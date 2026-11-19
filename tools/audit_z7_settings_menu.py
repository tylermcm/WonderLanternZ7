"""Compiled page-zero native-menu binding and setting action audit.

SPDX-License-Identifier: MIT. Original page getter and compiled owned callbacks
execute; label storage, focus/header services and loader I/O are supplied.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2
from audit_z7_module_host import HostFixture
from build_z7_module_host import ROOT, STATE

OBJECT, REGISTRY = 0xa1833548, 0xa2019e78


class MenuFixture(HostFixture):
    def __init__(self, *args):
        super().__init__(*args)
        self.u.mem_map(0xa2000000, 0x10000); self.u.mem_map(0xa2010000, 0x20000)
        self.u.mem_write(0xa200da5c + 2 * 4, struct.pack('<I', OBJECT))
        for i in range(15): self.u.mem_write(REGISTRY + (230 + i) * 12, struct.pack('<3I', 0, 0xa2910000 + i * 64, 0))
        self.labels = []
        self.back_requests = []
        self.redraws = []
        self.opens, self.property_writes = [], []

    def hook(self, u, address, size, context):
        if address == 0x103fbb5c:
            text, slot = self.cstring(u.reg_read(UC_ARM_REG_R0)), u.reg_read(UC_ARM_REG_R1)
            if not 230 <= slot < 245 or len(text) > 50: raise AssertionError('Unexpected settings label')
            record = REGISTRY + slot * 12
            buffer = int.from_bytes(u.mem_read(record + 4, 4), 'little')
            u.mem_write(buffer, text.encode() + b'\0'); u.mem_write(record, struct.pack('<I', len(text)))
            u.mem_write(record + 8, struct.pack('<I', u.reg_read(UC_ARM_REG_R2)))
            self.labels.append((slot, text)); self.ret(0)
        elif address == 0x103faebe:
            self.ret(0)
        elif address == 0x10402bc2:
            pointer, control = u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)
            if pointer != OBJECT or not 0x7b10 <= control <= 0x7b16: raise AssertionError('Unexpected focus')
            u.mem_write(pointer + 22, struct.pack('<2H', 0, control - 0x7b10)); self.ret(0)
        elif address == 0x104025ec:
            self.back_requests.append(u.reg_read(UC_ARM_REG_R0)); self.ret(0)
        elif address == 0x103fac5a:
            self.redraws.append([u.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2)])
            self.ret(1)
        elif address == 0x103faec6:
            self.ret(1)
        elif address == 0x10404c42:
            self.opens.append([u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)]); self.ret(1)
        elif address == 0x104065b0:
            self.property_writes.append([u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)]); self.ret(1)
        else:
            super().hook(u, address, size, context)


def audit(raw, host, packet, module):
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Fingerprint mismatch')
    checks = []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    f = MenuFixture(raw, host, packet)
    check('page-zero-published-only-after-success', f.call(host['symbols']['z7_module_load_once'], STATE) == 8 and bytes(f.u.mem_read(OBJECT, 4)) == struct.pack('<I', 2))
    base = f.words()[12]
    def call(name, *args): return f.call(base + module['symbols'][name], *args)
    def model(): return list(struct.unpack('<10I', f.u.mem_read(base + module['symbols']['z7_menu_settings'], 40)))
    def word(name): return int.from_bytes(f.u.mem_read(base + module['symbols'][name], 4), 'little')
    def action(row): f.u.mem_write(OBJECT + 22, struct.pack('<2H', 0, row)); call('sm_activate', 0xdeadbeef)
    check('menu-global-battery-default-matches-renderer-disabled-state', word('z7_battery_enabled') == 0)
    check('native-page-getter-resolves-zero-and-retains-stock-leaf', f.call(0x103fccc2, 2, 0) == OBJECT and f.call(0x103fccc2, 2, 42) == OBJECT + 42 * 44)
    check('native-page-getter-still-rejects-unknown-class', f.call(0x103fccc2, 7, 0) == 0)
    call('sm_render', OBJECT)
    check('seven-root-labels-and-independent-off-status', len(f.labels) == 15 and (230, 'Display settings') in f.labels and (238, 'OFF') in f.labels and (244, 'OFF') in f.labels)
    action(0); check('native-root-action-toggles-only-master', model()[0] == 1 and model()[1] == 15)
    action(1); check('standard-subview-opens-without-native-page-replacement', word('z7_settings_view') == 1 and (230, 'Standard') in f.labels)
    action(0); check('preset-page-disable-is-independent', model()[1] == 14)
    action(2); check('grid-component-toggle-retains-other-presets', model()[2:6] == [0, 0, 5, 10])
    action(1); action(0); check('information-subview-toggles-shutter-independently', word('z7_settings_view') == 2 and model()[6:10] == [126, 7, 0, 127])
    action(6); action(1); check('extra-subview-toggles-focal-independently', word('z7_settings_view') == 3 and model()[6] == 254)
    call('sm_back_event', 0xdeadbeef); check('extra-back-restores-information-view', word('z7_settings_view') == 2)
    call('sm_back_event', 0xdeadbeef); check('information-back-restores-preset-view', word('z7_settings_view') == 1)
    action(6); check('native-reset-retains-page-enable-and-master', model() == [1, 14, 1, 0, 5, 10, 127, 7, 0, 127])
    call('sm_back_event', 0xdeadbeef); action(6); action(5)
    check('battery-and-native-information-page-switches-independent', model()[0:2] == [3, 30])
    check('native-battery-choice-publishes-to-automatic-renderer', word('z7_battery_enabled') == 1)
    action(6); check('native-battery-disable-preserves-other-settings', model()[0:2] == [1, 30] and word('z7_battery_enabled') == 0)
    action(6)
    f.u.mem_write(base + module['symbols']['z7_menu_settings'] + 4, struct.pack('<I', 16)); action(5)
    check('native-action-cannot-disable-last-page', model()[1] == 16)
    check('native-actions-request-original-queued-redraw', f.redraws and all(row == [0x103fa771, 3, 7] for row in f.redraws))
    call('sm_back_event', 0xdeadbeef)
    check('root-back-uses-original-history-transition', f.back_requests == [0x3a1])
    events = base + module['symbols']['sm_events']
    back_rows = [struct.unpack('<4I', f.u.mem_read(events + i * 16, 16)) for i in range(14)]
    check('back-event-destination-remains-neutral-through-view-changes', all(row[3] == 0x3a0 for row in back_rows if row[0] in (0x238, 0x253)))
    text_object = 0xa291c000
    f.u.mem_write(text_object, bytes(100)); f.u.mem_write(text_object + 12, struct.pack('<I', 1))
    check('original-setter-rejects-direct-resource-to-dynamic-font-change', f.call(0x103fb340, text_object, 230, 2) == 0 and
          bytes(f.u.mem_read(text_object + 12, 4)) == struct.pack('<I', 1))
    for old_kind in (0, 1, 2, 3, 6):
        f.u.mem_write(text_object, bytes(100)); f.u.mem_write(text_object + 12, struct.pack('<I', old_kind))
        call('sm_bind_text', text_object, 230)
        check(f'owned-text-kind-{old_kind}-uses-supported-native-bridge',
              bytes(f.u.mem_read(text_object + 8, 8)) == struct.pack('<2I', 230, 2) and
              bytes(f.u.mem_read(text_object + 68, 4)) == struct.pack('<I', 1))
    if 'sm_open' in module['symbols']:
        meta = base + module['symbols']['metadata']; row_maps = base + module['symbols']['maps']
        check('entry-profile-retains-six-grid-options-and-adds-seventh-row', bytes(f.u.mem_read(meta + 20, 4)) == struct.pack('<I', 0x00070007))
        for row in range(7):
            pointer = int.from_bytes(f.u.mem_read(row_maps + row * 4, 4), 'little')
            records = [struct.unpack('<4I', f.u.mem_read(pointer + i * 16, 16)) for i in range(17)]
            active = [record for record in records if record[0] in (0x239, 0x25f)]
            check(f'entry-profile-owned-row-{row}-activation-and-routing', len(active) == 2 and all(
                record[1] & 1 and base <= (record[1] & ~1) < base + module['image_bytes'] and record[3] == (0x3a0 if row == 6 else 0x3a1) for record in active))
        for name, value in [('fourths', 1), ('thirds', 2), ('golden', 3), ('center', 4), ('dense', 5), ('off_owned', 0)]:
            call(name); check('entry-profile-retains-native-grid-choice-' + name, f.property_writes[-1] == [0x102d, value])
        f.u.mem_write(base + module['symbols']['z7_settings_view'], struct.pack('<I', 2)); call('sm_open')
        check('native-entry-opens-settings-root-with-original-page-api', f.opens == [[2, 0]] and word('z7_settings_view') == 0)
    prior = list(f.labels); record = REGISTRY + 230 * 12; f.u.mem_write(record, struct.pack('<I', 1))
    call('sm_render', OBJECT); check('foreign-label-is-never-overwritten', f.labels == prior and bytes(f.u.mem_read(record, 4)) == struct.pack('<I', 1))
    previous = model(); f.u.mem_write(OBJECT + 40, bytes(4)); action(0)
    check('detached-page-callback-cannot-change-model', model() == previous)
    for name, address in [('occupied-page-zero', OBJECT), ('grid-preflight-failure', 0xa1836f8c)]:
        g = MenuFixture(raw, host, packet); g.u.mem_write(address, struct.pack('<I', 0xdeadbeef))
        original = bytes(g.u.mem_read(OBJECT, 44))
        check(name + '-preserves-native-page-and-cleans-module', g.call(host['symbols']['z7_module_load_once'], STATE) == 7 and bytes(g.u.mem_read(OBJECT, 44)) == original and not g.live)
    return dict(passed=True, checks=checks, module_sha256=module['module_sha256'], main_sha256=host['main_payload_sha256'],
                supplied_boundaries=['Label storage', 'Native focus/header services',
                    'Native queued/component drawing, page opening and property storage', 'File/kernel/heap'],
                actual_menu_pixels=False, card_io=False, camera_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True); p.add_argument('--module', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); args = p.parse_args(); output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists(): p.error('Choose a new private output')
    r = audit((args.build / 'module-host.emulator.main.bin').read_bytes(), json.loads((args.build / 'module-host.emulator.json').read_text()),
              (args.module / 'Z7APP.BIN').read_bytes(), json.loads((args.module / 'module.json').read_text()))
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(r, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(r['checks']))))


if __name__ == '__main__': main()
