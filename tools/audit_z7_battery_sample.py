"""Execute the compiled direct-percentage sample policy through its real host.

SPDX-License-Identifier: MIT. Original native snapshot getter and ARM memcpy
execute; incoming telemetry, mutex and loader services are supplied boundaries.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2
from audit_z7_module_host import HostFixture
from build_z7_module_host import ROOT, STATE


class SampleFixture(HostFixture):
    def __init__(self, raw, host, packet, percent=63, kind=1, initialized=1, fallback=0, transition=False):
        super().__init__(raw, host, packet)
        self.u.mem_map(0xa2350000, 0x10000)
        snapshot = [initialized, kind, 0, 0, 0, 0, percent] + [0] * 7
        self.u.mem_write(0xa235aee4, struct.pack('<14I', *snapshot))
        self.u.mem_write(0xa18b4de8, struct.pack('<I', fallback))
        self.sample_events = []
        self.sample_locked = False
        self.transition = transition

    def hook(self, u, address, size, context):
        if address in (0x10170944, 0x1017093e) and u.reg_read(UC_ARM_REG_R0) == 0xa235ae4c:
            if address == 0x10170944:
                if self.sample_locked: raise AssertionError('Recursive snapshot lock')
                self.sample_locked = True
                self.sample_events.append('lock')
            else:
                if not self.sample_locked: raise AssertionError('Unowned snapshot unlock')
                self.sample_locked = False
                self.sample_events.append('unlock')
            self.ret(1)
        elif address == 0x10170a1c and u.reg_read(UC_ARM_REG_R1) == 0xa235aee4:
            if not self.sample_locked or u.reg_read(UC_ARM_REG_R2) != 56:
                raise AssertionError('Wrong original snapshot copy contract')
            self.sample_events.append('native-copy')
            if self.transition:
                u.mem_write(0xa18b4de8, struct.pack('<I', 1))
            # Execute the original ARM memcpy.
        else:
            super().hook(u, address, size, context)


def audit(raw, host, packet, module):
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Host or module identity mismatch')
    scenarios = [(f'valid-{p}', dict(percent=p), True) for p in (0, 1, 9, 10, 63, 99, 100)]
    scenarios += [(f'kind-{k}', dict(kind=k), True) for k in range(2, 7)]
    scenarios += [(f'invalid-percent-{p}', dict(percent=p), False) for p in (101, 255, 0xffffffff)]
    scenarios += [(f'uninitialized-{i}', dict(initialized=i), False) for i in (0, 2, 0xffffffff)]
    scenarios += [(f'unknown-kind-{k}', dict(kind=k), False) for k in (0, 7, 255)]
    scenarios += [('bar-fallback-before-query', dict(fallback=1), False),
                  ('bar-fallback-during-query', dict(transition=True), False)]
    checks = []
    for name, arguments, valid in scenarios:
        f = SampleFixture(raw, host, packet, **arguments)
        status = f.call(host['symbols']['z7_module_load_once'], STATE)
        base = f.words()[12]
        word = lambda key: int.from_bytes(f.u.mem_read(base + module['symbols'][key], 4), 'little')
        success = (status == 8 and word('z7_battery_sample_valid') == int(valid) and
                   word('z7_battery_sample_percent') == (arguments.get('percent', 63) if valid else 0xffffffff) and
                   not f.sample_locked and f.sample_events == ([] if arguments.get('fallback') else ['lock', 'native-copy', 'unlock']))
        checks.append(dict(name=name, passed=bool(success)))
        if not success: raise AssertionError(name)
    return dict(passed=True, checks=checks, main_sha256=host['main_payload_sha256'], module_sha256=module['module_sha256'],
        supplied_boundaries=['Incoming telemetry bytes', 'Mutex services', 'Fallback transition during query', 'File/kernel/heap'],
        sample_only=True, visibility_or_cadence_implemented=False, telemetry_verified=False, camera_access=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--module', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists(): parser.error('Choose a new private evidence path')
    host = json.loads((args.build / 'module-host.emulator.json').read_text())
    module = json.loads((args.module / 'module.json').read_text())
    result = audit((args.build / 'module-host.emulator.main.bin').read_bytes(), host, (args.module / 'Z7APP.BIN').read_bytes(), module)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__': main()
