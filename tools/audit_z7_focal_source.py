"""Execute the original focal producer/getter and compiled direct sampler.

SPDX-License-Identifier: MIT. Original property lookup/read, focal producer,
fraction/encoded conversions and PTP scaling execute. Incoming lens-query values,
property publication and loader services are supplied; no lens hardware or pixels.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2
from audit_z7_module_host import HostFixture
from build_z7_module_host import ROOT, STATE
from audit_splash_image import MEM

TYPE, VALUE, CONTEXT = 0xa24e2600, 0xa24e25a8, 0xa18d3e90


class FocalSourceFixture(HostFixture):
    def __init__(self, *args):
        super().__init__(*args)
        self.u.mem_map(0xa24e0000, 0x10000)
        self.gets, self.publications, self.queries = [], [], []
        self.query_values = {}
        self.producer = False
        self.transition = None
    def hook(self, u, address, size, context):
        if address == 0x103fe85e:
            key = u.reg_read(UC_ARM_REG_R0)
            self.gets.append(key)
            if self.transition and self.gets == [0x1c14, 0x1c01, 0x1c14]:
                u.mem_write(TYPE, struct.pack('<I', self.transition))
            # Execute the original wrapper, property lookup and typed read.
        elif self.producer and address == 0x1015ce8e:
            count, keys, values = [u.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2)]
            requested = struct.unpack('<' + 'I' * count, u.mem_read(keys, count * 4))
            self.queries.append(list(requested))
            for index, key in enumerate(requested):
                if key not in self.query_values:
                    raise AssertionError('Unexpected incoming lens query')
                u.mem_write(values + index * 4, struct.pack('<I', self.query_values[key]))
            self.ret(1)
        elif self.producer and address == 0x101645ec:
            key, value = u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)
            if key != 0x1c01:
                raise AssertionError('Unexpected native publication')
            self.publications.append([key, value])
            u.mem_write(VALUE, struct.pack('<I', value))
            self.ret(1)
        else:
            super().hook(u, address, size, context)


def audit(raw, host, packet, module):
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Fingerprint mismatch')
    f = FocalSourceFixture(raw, host, packet)
    checks, cases = [], []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good:
            raise AssertionError(name)
    def store(address, value):
        f.u.mem_write(address, struct.pack('<I', value))
    def word(address):
        return int.from_bytes(f.u.mem_read(address, 4), 'little')
    def sample(kind, value, transition=None):
        store(TYPE, kind)
        store(VALUE, value)
        f.gets, f.transition = [], transition
        f.call(base + module['symbols']['z7_focal_resample'])
        return word(base + module['symbols']['z7_focal_sample_valid']), word(base + module['symbols']['z7_focal_sample_tenths'])
    for key, address in ((0x1c01, VALUE), (0x1c14, TYPE)):
        check('original-key-admitted-' + hex(key), f.call(0x10070204, key, MEM) == 1)
        index = word(MEM)
        check('original-key-value-binding-' + hex(key), word(0x114d09ac + index * 16 + 8) == address)
    check('diagnostic-loads-through-host', f.call(host['symbols']['z7_module_load_once'], STATE) == 8)
    base = f.words()[12]
    for kind in (0, 1, 2, 3, 4, 255, 0xffffffff):
        for value in (0, 1, 60, 240, 245, 40000, 0xffffffff):
            actual = sample(kind, value)
            valid = kind in (1, 3) and value not in (0, 0xffffffff)
            check(f'compiled-type{kind}-value{value}', actual == (int(valid), value if valid else 0xffffffff))
            check(f'compiled-type{kind}-value{value}-read-only-properties', word(TYPE) == kind and word(VALUE) == value)
    for before, after in ((1, 3), (3, 1), (1, 2), (3, 4), (1, 255)):
        actual = sample(before, 245, after)
        check(f'type-transition-{before}-{after}-rejects-sample', actual == (0, 0xffffffff) and f.gets == [0x1c14, 0x1c01, 0x1c14])
    f.transition = None
    for kind in (0, 1, 2, 3, 4):
        for value in (240, 245):
            store(TYPE, kind)
            store(VALUE, value)
            # Native PTP also exposes type4; the electronic-lens feature keeps
            # its independently selected type1/3 policy instead of treating
            # every PTP-admitted state as live electronic-lens telemetry.
            expected = value * 10 if kind in (1, 3, 4) else 0
            check(f'original-ptp-type{kind}-value{value}-hundredths', f.call(0x1034231a) == expected)
    # Execute the native live producer using incoming lens-controller query data.
    # Its property publication boundary stores the original selected key only.
    for whole, fraction, expected in ((24, 0, 240), (24, 32768, 245), (70, 0, 700)):
        store(TYPE, 1)
        f.u.mem_write(CONTEXT + 6, b'\1')
        store(CONTEXT + 0x78, 0xffffffff)
        f.producer = True
        f.query_values = {0x309e: whole, 0x309d: fraction}
        f.publications, f.queries = [], []
        check(f'live-producer-fraction-{whole}-{fraction}-publishes', f.call(0x1016342e, MEM) == 1 and
              f.publications == [[0x1c01, expected]] and f.queries == [[0x309e, 0x309d]] and word(VALUE) == expected)
        check(f'live-producer-fraction-{whole}-{fraction}-stable-no-repeat', f.call(0x1016342e, MEM) == 0 and len(f.publications) == 1)
        f.producer = False
        check(f'compiled-sample-follows-native-fraction-{whole}-{fraction}', sample(1, expected) == (1, expected))
        cases.append(dict(kind=1, incoming_whole=whole, incoming_fraction=fraction, native_tenths=expected))
    for encoded in (0, 24, 48, 72, 96, 120, 144, 168, 192, 216, 240, 255, 256, 257):
        expected = f.call(0x10204fcc, encoded, MEM)
        store(TYPE, 3)
        f.u.mem_write(CONTEXT + 6, b'\3')
        store(CONTEXT + 0x78, 0xffffffff)
        f.producer, f.query_values = True, {0x601d: encoded}
        f.publications, f.queries = [], []
        check(f'live-producer-encoded-{encoded}-original-table-conversion', f.call(0x1016342e, MEM) == 1 and
              f.publications == [[0x1c01, expected]] and f.queries == [[0x601d]] and word(VALUE) == expected)
        f.producer = False
        cases.append(dict(kind=3, incoming_encoded=encoded, native_tenths=expected))
    for kind in (0, 2, 4):
        f.u.mem_write(CONTEXT + 6, bytes([kind]))
        store(CONTEXT + 0x78, 245)
        store(VALUE, 245)
        f.producer, f.publications = True, []
        check(f'original-invalid-type-{kind}-can-retain-stale-focal', f.call(0x1016342e, MEM) == 0 and not f.publications and word(VALUE) == 245)
        f.producer = False
        check(f'compiled-invalid-type-{kind}-hides-stale-focal', sample(kind, 245) == (0, 0xffffffff))
    return dict(passed=True, checks=checks, cases=cases, module_sha256=module['module_sha256'],
        native_getter='0x103FE85E', native_live_producer='0x1016342E', type_key='0x1c14', focal_key='0x1c01',
        units='tenths of mm; original PTP getter multiplies by10 for property5008',
        native_fractional_and_encoded_conversions_execute=True, compiled_sampler_executes=True,
        properties_and_snapshot_modified_by_module=False, sample_type_recheck_is_not_atomic_lens_identity=True,
        supplied_boundaries=['Incoming lens-controller query values', 'Native property publication', 'Loader/kernel/filesystem'],
        lens_hardware_verified=False, actual_pixels=False, overlay_implemented=False, camera_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--module', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists():
        p.error('Choose a new private output')
    result = audit((args.build / 'module-host.emulator.main.bin').read_bytes(),
        json.loads((args.build / 'module-host.emulator.json').read_text()), (args.module / 'Z7APP.BIN').read_bytes(),
        json.loads((args.module / 'module.json').read_text()))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']), producer_cases=len(result['cases']))))


if __name__ == '__main__':
    main()
