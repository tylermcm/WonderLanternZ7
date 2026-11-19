"""Compiled native-key diagnostic ownership, delegation and master-setting audit.

SPDX-License-Identifier: MIT. Original key callback outcome is supplied here;
its original admission/cycling instructions have separate native input audits.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3
from audit_z7_battery_percent import AutomaticFixture
from build_z7_module_host import ROOT, STATE


class KeyFixture(AutomaticFixture):
    next_mode = None
    def __init__(self, *args):
        super().__init__(*args)
        self.keys = []
        self.u.mem_write(0xa181f91c, struct.pack('<I', 0xa2c41000))
        self.u.mem_write(0xa2c41000, struct.pack('<4I', 4, 4, 0, 0xa2c42000))

    def hook(self, u, address, size, context):
        if address == 0x1030da56:
            self.keys.append([u.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)])
            if self.next_mode is not None: self.u.mem_write(0xa201d4d0 + 0x18a, bytes([self.next_mode]))
            self.ret(0x12345678)
        else:
            super().hook(u, address, size, context)


def audit(raw, host, packet, module):
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Fingerprint mismatch')
    checks = []
    def check(name, passed):
        checks.append(dict(name=name, passed=bool(passed)))
        if not passed: raise AssertionError(name)
    def fixture():
        f = KeyFixture(raw, host, packet)
        if f.call(host['symbols']['z7_module_load_once'], STATE) != 8: raise AssertionError('load')
        return f, f.words()[12]
    def word(f, base, name): return int.from_bytes(f.u.mem_read(base + module['symbols'][name], 4), 'little')
    def setting(f, base, value): f.u.mem_write(base + module['symbols']['z7_disp_key_enabled'], struct.pack('<I', value))
    f, base = fixture()
    check('owned-key-callback-published-after-success', int.from_bytes(f.u.mem_read(0xa1829b0c, 4), 'little') == (base + module['symbols']['clean_key']) | 1)
    f.call(host['symbols']['z7_display_before_paint'])
    check('default-off-primes-no-clean-masks', not word(f, base, 'z7_clean_active'))
    for name, key, enabled, new_mode, excluded in (
        ('off', 0x29, 0, 1, None), ('eligible', 0x29, 1, 1, None),
        ('native-blocked', 0x29, 1, None, None), ('other-key', 0x28, 1, 1, None),
        ('unknown-setting', 0x29, 2, 1, None), ('evf', 0x29, 1, 1, 'evf'),
        ('movie', 0x29, 1, 1, 'movie'), ('menu', 0x29, 1, 1, 'menu')):
        g, loaded = fixture(); setting(g, loaded, enabled); g.next_mode = new_mode
        g.u.mem_write(0xa201d4d0 + 0x18a, b'\0')
        if excluded == 'evf': g.u.mem_write(0xa18237c6, b'\2')
        if excluded == 'movie': g.u.mem_write(0xa201d510, b'\1')
        if excluded == 'menu': g.u.mem_write(0xa2c41008, struct.pack('<I', 1))
        returned = g.call(loaded + module['symbols']['clean_key'], key, 0x11, 0x22, 0x33)
        check(name + '-delegates-all-native-arguments-and-result', returned == 0x12345678 and g.keys == [[key, 0x11, 0x22, 0x33]])
        check(name + '-accepts-only-native-admitted-photo-lcd-change', word(g, loaded, 'z7_disp_key_accepted') == int(name == 'eligible'))
    setting(f, base, 1); f.call(host['symbols']['z7_display_before_paint'])
    check('master-on-primes-simplified-masks-before-key', word(f, base, 'z7_clean_active') == 1)
    setting(f, base, 0); f.call(host['symbols']['z7_display_before_paint'])
    check('master-off-restores-owned-masks', not word(f, base, 'z7_clean_active'))
    for name, address in [('foreign-key', 0xa1829b0c), ('grid-preflight', 0xa1836f8c)]:
        g = KeyFixture(raw, host, packet); g.u.mem_write(address, bytes(4))
        initial = bytes(g.u.mem_read(0xa1829b0c, 4))
        check(name + '-failure-never-publishes-key-callback', g.call(host['symbols']['z7_module_load_once'], STATE) == 7 and
              bytes(g.u.mem_read(0xa1829b0c, 4)) == initial and not g.live)
    return dict(passed=True, checks=checks, module_sha256=module['module_sha256'], main_sha256=host['main_payload_sha256'],
                supplied_boundaries=['Native key callback outcome', 'GUI/page/output state', 'Loader services'],
                native_key_admission_executed=False, camera_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True); p.add_argument('--module', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); args = p.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists(): p.error('Choose a new private output')
    r = audit((args.build / 'module-host.emulator.main.bin').read_bytes(), json.loads((args.build / 'module-host.emulator.json').read_text()),
              (args.module / 'Z7APP.BIN').read_bytes(), json.loads((args.module / 'module.json').read_text()))
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(r, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(r['checks']))))


if __name__ == '__main__': main()
