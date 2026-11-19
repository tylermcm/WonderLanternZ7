"""Audit the compiled battery text diagnostic's native object lifetime.

SPDX-License-Identifier: MIT. The native pool allocator, zeroing and text-object
initializer execute. Font measurement, label storage, paint/list services,
file/kernel/heap and the supplied GUI instance remain explicit boundaries.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1
from audit_z7_module_host import HostFixture
from build_z7_module_host import ROOT, STATE

POOL, SLOTS, LABEL = 0xa2c3ce18, 0xa2c37800, 0xa2019e78 + 299 * 12


class BatteryDisplayFixture(HostFixture):
    def __init__(self, raw, host, packet):
        super().__init__(raw, host, packet)
        self.u.mem_map(0xa1f90000, 0x70000)
        self.u.mem_map(0xa2010000, 0x20000)
        self.u.mem_map(0xa2c30000, 0x20000)
        self.u.mem_write(0xa18237d0, struct.pack('<I', 0xa201e388))
        self.u.mem_write(0xa201e3ac, struct.pack('<I', POOL))
        self.u.mem_write(POOL, struct.pack('<4H2I', 1340, 140, 1200, 0, SLOTS, 0))
        self.u.mem_write(LABEL, struct.pack('<3I', 0, 0xa2c40000, 0))
        self.labels, self.paint_calls, self.list_calls = [], [], []

    def hook(self, u, address, size, context):
        if address == 0x103fbb5c:
            self.labels.append((self.cstring(u.reg_read(UC_ARM_REG_R0)), u.reg_read(UC_ARM_REG_R1)))
            self.ret(0)
        elif address == 0x10487500:
            self.ret(1)
        elif address == 0x103faeba:
            self.list_calls.append((u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)))
            self.ret(1)
        elif address in (0x10433912, 0x10384968):
            p = u.reg_read(UC_ARM_REG_R0)
            self.paint_calls.append((address, bytes(u.mem_read(p, 96))))
            self.ret(1)
        else:
            super().hook(u, address, size, context)


def audit(raw, host, packet, module):
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Candidate or module identity mismatch')
    checks = []
    def check(name, passed):
        checks.append(dict(name=name, passed=bool(passed)))
        if not passed:
            raise AssertionError(name)
    def load():
        f = BatteryDisplayFixture(raw, host, packet)
        if f.call(host['symbols']['z7_module_load_once'], STATE) != 8:
            raise AssertionError('Diagnostic module did not initialize')
        return f, f.words()[12]
    symbols = module['symbols']
    def address(base, name):
        return base + symbols['z7_battery_trial_' + name]
    def word(f, base, name):
        return int.from_bytes(f.u.mem_read(address(base, name), 4), 'little')
    f, base = load()
    f.call(host['symbols']['z7_display_after_paint'])
    check('inactive-diagnostic-allocates-no-gui-object', word(f, base, 'object') == 0 and not f.list_calls)
    f.u.mem_write(address(base, 'phase'), struct.pack('<I', 1))
    f.call(host['symbols']['z7_display_after_paint'])
    object_pointer = word(f, base, 'object')
    check('original-native-pool-owns-regular-slot', object_pointer != 0 and int.from_bytes(f.u.mem_read(SLOTS + 1199 * 4, 4), 'little') == object_pointer)
    check('native-text-constructor-and-module-painter-installed', int.from_bytes(f.u.mem_read(object_pointer + 0x4c, 4), 'little') == base + symbols['painter'] and
          int.from_bytes(f.u.mem_read(object_pointer + 0x54, 4), 'little') == 0x10384955)
    check('one-label-and-one-native-list-registration', f.labels == [('63%', 299)] and f.list_calls == [(0xa201e3b4, object_pointer)])
    f.call(host['symbols']['z7_display_after_paint'])
    check('repeated-frame-does-not-allocate-or-append-again', len(f.list_calls) == 1)
    f.call(base + symbols['painter'], object_pointer, 0, 0, 0)
    rectangle = struct.unpack('<24I', f.paint_calls[0][1])
    check('visible-painter-clears-only-supplied-native-rectangle-before-text', [x[0] for x in f.paint_calls] == [0x10433912, 0x10384968] and
          rectangle[4:6] == (2 | (392 << 16), 78 | (436 << 16)) and rectangle[13:15] == (2, 0))
    f.u.mem_write(address(base, 'phase'), struct.pack('<I', 2))
    f.call(host['symbols']['z7_display_before_paint'])
    check('retirement-marks-owned-object-dirty-before-paint', int.from_bytes(f.u.mem_read(object_pointer + 0x44, 4), 'little') == 1)
    f.paint_calls.clear()
    f.call(base + symbols['painter'], object_pointer, 0, 0, 0)
    check('retirement-clears-and-skips-native-text-erase', word(f, base, 'phase') == 3 and [x[0] for x in f.paint_calls] == [0x10433912] and
          bytes(f.u.mem_read(object_pointer + 0x28, 4)) == bytes(4))
    f.u.mem_write(SLOTS + 1199 * 4, bytes(4))
    f.paint_calls.clear()
    f.call(base + symbols['painter'], object_pointer, 0, 0, 0)
    check('detached-object-is-never-painted', word(f, base, 'error') == 3 and not f.paint_calls)
    for case in ('foreign-slot', 'foreign-label', 'missing-label-buffer', 'full-global-pool', 'gui-not-ready'):
        bad, loaded = load()
        if case == 'foreign-slot': bad.u.mem_write(SLOTS + 1199 * 4, struct.pack('<I', 0xa1fa0000))
        if case == 'foreign-label': bad.u.mem_write(LABEL, struct.pack('<I', 3))
        if case == 'missing-label-buffer': bad.u.mem_write(LABEL + 4, bytes(4))
        if case == 'full-global-pool':
            availability = int.from_bytes(bad.u.mem_read(0xa181c77c, 4), 'little')
            bad.u.mem_write(availability, struct.pack('<1200I', *([1] * 1200)))
        if case == 'gui-not-ready': bad.u.mem_write(0xa201e3ac, bytes(4))
        bad.u.mem_write(address(loaded, 'phase'), struct.pack('<I', 1))
        bad.call(host['symbols']['z7_display_after_paint'])
        check(case + '-does-not-publish-an-object', word(bad, loaded, 'object') == 0 and not bad.list_calls and not bad.labels)
    return dict(passed=True, checks=checks, module_sha256=module['module_sha256'], main_sha256=host['main_payload_sha256'],
        supplied_boundaries=['GUI context/pool instance', 'Font measurement', 'Label storage', 'Paint and list services', 'File/kernel/heap'],
        visual_restoration_verified=False, telemetry_verified=False, camera_access=False)


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
