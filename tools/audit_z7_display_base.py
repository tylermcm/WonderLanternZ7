"""Compiled original-Z7 native base-page ownership and rollback contracts.

SPDX-License-Identifier: MIT. Original selector/setter instructions execute;
property reads/storage, incoming GUI state and loader services are supplied.
No pixels, real property persistence, physical card or camera are established.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1
from audit_z7_disp_cycle import CycleFixture
from audit_z7_display_readouts import SNAPSHOT, TABLE
from build_z7_module_host import ROOT, STATE


class BaseFixture(CycleFixture):
    def __init__(self, *args):
        super().__init__(*args)
        self.properties = {0x138d: 0, 0x2f15: 0}
        self.display = 1
        self.setter_results = []
        self.native_setter_entries = []
        self.viewport = (0, 0, 720, 480)

    def hook(self, u, address, size, context):
        if address == 0x104065a4:
            self.ret(self.properties.get(u.reg_read(UC_ARM_REG_R0), 0))
        elif address == 0x104065b0:
            key, value = u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)
            self.property_writes.append((key, value))
            result, store = self.setter_results.pop(0) if self.setter_results else (1, True)
            if store: self.properties[key] = value
            self.ret(result)
        elif address == 0x103fef80: self.ret(self.display)
        elif address == 0x10437190:
            pointer = u.reg_read(UC_ARM_REG_R0)
            for offset in (8, 0x14): u.mem_write(pointer + offset, struct.pack('<4h', *self.viewport))
            u.mem_write(pointer + 0x28, b'\1'); self.ret(0)
        elif address == 0x103673de:
            self.native_setter_entries.append(u.reg_read(UC_ARM_REG_R0))
        else: super().hook(u, address, size, context)


def audit(raw, host, packet, module):
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Fingerprint mismatch')
    checks = []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    symbols = module['symbols']
    def load(native=0, horizon=1):
        f = BaseFixture(raw, host, packet)
        if f.call(host['symbols']['z7_module_load_once'], STATE) != 8: raise AssertionError('Module load')
        base = f.words()[12]
        f.properties[0x2f15] = native
        f.u.mem_write(SNAPSHOT + 0x18a, bytes([native]))
        f.call(base + symbols['z7_settings_component'], base + symbols['z7_menu_settings'], 0, 2, horizon)
        return f, base
    def word(f, base, name): return int.from_bytes(f.u.mem_read(base + symbols[name], 4), 'little')
    def master(f, base, enabled): f.call(base + symbols['z7_settings_flag'], base + symbols['z7_menu_settings'], 0, enabled)
    def before(f): f.call(host['symbols']['z7_display_before_update'])
    def page(f): return f.u.mem_read(SNAPSHOT + 0x18a, 1)[0]
    def masks(f):
        return [bytes(f.u.mem_read(int.from_bytes(f.u.mem_read(TABLE + i * 4, 4), 'little') + 4, 36)) for i in range(61)]
    for native in range(4):
        for horizon in range(2):
            f, base = load(native, horizon)
            original = masks(f)
            before(f)
            check(f'disabled-native-{native}-{horizon}-does-not-claim-page', not word(f, base, 'z7_base_active') and not f.property_writes)
            master(f, base, 1)
            snapshot = bytearray(f.u.mem_read(SNAPSHOT, 0x33c))
            desired = 3 if horizon else 0
            snapshot[0x18a] = desired
            before(f)
            check(f'native-{native}-horizon-{horizon}-selects-original-base',
                word(f, base, 'z7_base_active') == 1 and word(f, base, 'z7_base_saved') == native and
                word(f, base, 'z7_base_applied') == desired and f.properties[0x2f15] == desired and
                bytes(f.u.mem_read(SNAPSHOT, 0x33c)) == snapshot and
                f.native_setter_entries == ([desired] if native != desired else []))
            stores = len(f.property_writes)
            before(f)
            check(f'unchanged-base-{native}-{horizon}-does-not-repeat-property-store', len(f.property_writes) == stores)
            master(f, base, 0); before(f)
            check(f'disable-restores-native-{native}-{horizon}-page-and-all-masks',
                page(f) == native and f.properties[0x2f15] == native and masks(f) == original and
                not word(f, base, 'z7_base_active') and not word(f, base, 'z7_readout_active'))
    f, base = load()
    master(f, base, 1)
    for components in range(16):
        for bit in range(4):
            f.call(base + symbols['z7_settings_component'], base + symbols['z7_menu_settings'], 0, bit, bool(components & (1 << bit)))
        before(f)
        expected = 3 if components & 4 else 0
        check(f'component-combination-{components}-uses-native-horizon-base', page(f) == expected and f.properties[0x2f15] == expected)
    for foreign_snapshot in (False, True):
        f, base = load(); master(f, base, 1); before(f)
        if not foreign_snapshot: f.properties[0x2f15] = 2
        f.u.mem_write(SNAPSHOT + 0x18a, b'\2')
        before(f)
        check('foreign-' + ('snapshot' if foreign_snapshot else 'property') + '-preserved-and-policy-suspended',
            page(f) == 2 and f.properties[0x2f15] == (0 if foreign_snapshot else 2) and
            word(f, base, 'z7_base_conflicts') == 1 and not word(f, base, 'z7_base_active') and not word(f, base, 'z7_readout_active'))
        f.properties[0x2f15] = 0; f.u.mem_write(SNAPSHOT + 0x18a, b'\0')
        before(f)
        check('foreign-conflict-latched-' + str(foreign_snapshot), page(f) == 0 and not word(f, base, 'z7_base_active'))
        master(f, base, 0); before(f); master(f, base, 1); before(f)
        check('master-off-clears-conflict-' + str(foreign_snapshot), page(f) == 3 and word(f, base, 'z7_base_active') == 1)
    for kind in ('menu', 'movie', 'output', 'selector-movie', 'selector-output'):
        f, base = load(); master(f, base, 1); before(f)
        f.u.mem_write(SNAPSHOT + 0x18a, b'\1')
        if kind == 'menu': f.u.mem_write(0xa2c41008, struct.pack('<I', 1))
        if kind == 'movie': f.u.mem_write(SNAPSHOT + 0x40, b'\1')
        if kind == 'output': f.u.mem_write(0xa18237c6, b'\2')
        if kind == 'selector-movie': f.properties[0x138d] = 1
        if kind == 'selector-output': f.display = 4
        setters = len(f.native_setter_entries)
        before(f)
        check(kind + '-restores-only-saved-photo-lcd-property', f.properties[0x2f15] == 0 and page(f) == 1 and
            len(f.native_setter_entries) == setters and not word(f, base, 'z7_base_active'))
    for result in ((0, False), (1, False), (0, True)):
        f, base = load(); master(f, base, 1)
        f.setter_results = [result]
        before(f)
        check('apply-failure-rolls-back-native-snapshot-' + str(result), page(f) == 0 and f.properties[0x2f15] == 0 and
            word(f, base, 'z7_base_errors') == 1 and not word(f, base, 'z7_base_active') and not word(f, base, 'z7_readout_active'))
    f, base = load(); master(f, base, 1); before(f)
    master(f, base, 0); f.setter_results = [(0, False)]
    before(f)
    check('failed-restore-retains-conditional-ownership-and-rolls-back-snapshot',
        page(f) == 3 and f.properties[0x2f15] == 3 and word(f, base, 'z7_base_active') == 1 and not word(f, base, 'z7_readout_active'))
    before(f)
    check('next-update-retries-pending-native-restore', page(f) == 0 and f.properties[0x2f15] == 0 and not word(f, base, 'z7_base_active'))
    f, base = load(); master(f, base, 1); before(f)
    f.u.mem_write(0xa18237c6, b'\2'); f.u.mem_write(SNAPSHOT + 0x18a, b'\1')
    setters = len(f.native_setter_entries); f.setter_results = [(0, False)]
    before(f)
    check('inactive-output-failed-restore-preserves-shared-snapshot', page(f) == 1 and f.properties[0x2f15] == 3 and
        word(f, base, 'z7_base_active') == 1 and len(f.native_setter_entries) == setters)
    before(f)
    check('inactive-output-retries-only-photo-lcd-property', page(f) == 1 and f.properties[0x2f15] == 0 and
        not word(f, base, 'z7_base_active') and len(f.native_setter_entries) == setters)
    f, base = load(); f.properties[0x2f15] = 0xffffffff; master(f, base, 1); original = masks(f); before(f)
    check('invalid-property-does-not-claim-or-filter-native-groups', not word(f, base, 'z7_base_active') and masks(f) == original and not f.property_writes)
    return dict(passed=True, checks=checks, main_sha256=host['main_payload_sha256'], module_sha256=module['module_sha256'],
        original_selector_and_setter_execute=True, conditional_property_restore=True,
        supplied_boundaries=['Loader/kernel/filesystem/heap', 'Incoming GUI/pool/page/output state', 'Property read/storage and display-kind service results'],
        actual_pixels=False, camera_access=False, remaining_components_bound=False, information_app_bound=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True); p.add_argument('--module', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--legacy-build', type=Path)
    a = p.parse_args(); output = a.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists(): p.error('Choose a new private output')
    result = audit((a.build / 'module-host.emulator.main.bin').read_bytes(), json.loads((a.build / 'module-host.emulator.json').read_text()),
        (a.module / 'Z7APP.BIN').read_bytes(), json.loads((a.module / 'module.json').read_text()))
    if a.legacy_build:
        raw = (a.legacy_build / 'module-host.emulator.main.bin').read_bytes()
        host = json.loads((a.legacy_build / 'module-host.emulator.json').read_text())
        if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256']: raise ValueError('Legacy fingerprint')
        f = BaseFixture(raw, host, (a.module / 'Z7APP.BIN').read_bytes())
        original = bytes(f.u.mem_read(SNAPSHOT, 0x33c))
        original_masks = [bytes(f.u.mem_read(int.from_bytes(f.u.mem_read(TABLE + i * 4, 4), 'little'), 48)) for i in range(61)]
        status = f.call(host['symbols']['z7_module_load_once'], STATE)
        passed = (status == 7 and not f.live and not f.property_writes and bytes(f.u.mem_read(SNAPSHOT, 0x33c)) == original and
            original_masks == [bytes(f.u.mem_read(int.from_bytes(f.u.mem_read(TABLE + i * 4, 4), 'little'), 48)) for i in range(61)])
        if not passed: raise AssertionError('Older host rejection before native stores')
        result['checks'].append(dict(name='older-24-byte-host-rejects-before-native-stores', passed=True))
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__': main()
