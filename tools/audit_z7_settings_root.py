"""Compiled Custom Settings overview relocation contracts (MIT).

Native loader and owned callbacks execute. UI/file/property boundaries are
supplied; native-key/pixel coverage belongs to the separate QEMU probe.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1
from audit_z7_display_persistence import PersistenceFixture
from audit_z7_lcd_grid_persistence import NEW
from audit_z7_settings_files import PATHS
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output

ROOT_OBJECT, GRID, OWNED = 0xa18367a4, 0xa1836f8c, 0xa1833548


class RootFixture(PersistenceFixture):
    def hook(self, u, address, size, context):
        if address == 0x103fbb5c and u.reg_read(UC_ARM_REG_R1) == 45:
            self.entry_label = self.cstring(u.reg_read(UC_ARM_REG_R0))
            self.ret(0)
        elif address == 0x10404c42:
            self.open_request = (u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1))
            self.ret(1)
        elif address == 0x104025ec:
            self.back_request = u.reg_read(UC_ARM_REG_R0)
            self.ret(0)
        else:
            super().hook(u, address, size, context)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('host', 'module', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args(); out = require_private_output(a.output)
    h = json.loads((a.host / 'module-host.emulator.json').read_text())
    m = json.loads((a.module / 'module.json').read_text())
    raw = (a.host / 'module-host.emulator.main.bin').read_bytes()
    packet = (a.module / 'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == h['main_payload_sha256']
    assert hashlib.sha256(packet).hexdigest() == m['module_sha256']
    assert m['configuration']['settings_root_entry']
    checks = []

    def check(name, good):
        assert good, name
        checks.append(name)

    def fixture():
        f = RootFixture(raw, h, packet)
        f.file_paths = PATHS + NEW
        return f

    f = fixture()
    original = bytes(f.u.mem_read(ROOT_OBJECT, 44))
    original_words = struct.unpack('<11I', original)
    original_meta = struct.unpack('<7I', f.u.mem_read(original_words[10], 28))
    original_callbacks = bytes(f.u.mem_read(original_words[4], 32))
    original_controls = bytes(f.u.mem_read(original_meta[3], 8 * 28))
    original_maps = bytes(f.u.mem_read(original_meta[4], 8 * 4))
    original_events = bytes(f.u.mem_read(int.from_bytes(original_maps[:4], 'little'), 18 * 16))
    check('resident-load', f.call(h['symbols']['z7_module_load_once'], STATE) == 8)
    f.base = f.words()[12]; f.setword(40, 8)
    symbols = m['symbols']

    def call(name, *args):
        return f.call(f.base + symbols[name], *args)

    root = bytes(f.u.mem_read(ROOT_OBJECT, 44))
    w = struct.unpack('<11I', root)
    meta = struct.unpack('<7I', f.u.mem_read(w[10], 28))
    check('overview-object-only-callback-and-metadata-pointers-change',
          all(w[i] == original_words[i] for i in range(11) if i not in (4, 10)))
    check('all-eight-native-rows-preserved', bytes(f.u.mem_read(meta[3], 8 * 28)) == original_controls)
    check('all-eight-native-event-map-pointers-preserved', bytes(f.u.mem_read(meta[4], 32)) == original_maps)
    check('native-callbacks-except-constructor-preserved', bytes(f.u.mem_read(w[4] + 4, 28)) == original_callbacks[4:])
    check('eight-row-viewport-nine-total', meta[5] == 0x00080009)
    check('native-layout-and-geometry-preserved', all(meta[i] == original_meta[i] for i in (0, 1, 2, 6)))
    control = struct.unpack('<7I', f.u.mem_read(meta[3] + 8 * 28, 28))
    check('new-row-label-style-and-control', (control[0], control[4], control[6]) == (45, 0x1209, 0x7c00))
    events = struct.unpack('<72I', f.u.mem_read(f.read(meta[4] + 32), 18 * 16))
    old_events = struct.unpack('<72I', original_events)
    before_io = list(f.file_events)
    for i in range(18):
        row, old = events[i * 4:i * 4 + 4], old_events[i * 4:i * 4 + 4]
        if row[0] in (0x239, 0x252, 0x25f):
            check('activation-map-' + hex(row[0]), row[0] == old[0] and row[2] == old[2] and
                  row[1] == (f.base + symbols['sm_open']) | 1 and row[3] == 0x3a0)
            f.write(f.base + symbols['z7_settings_view'], 3)
            f.call(row[1], 0xdeadbeef)
            check('activation-resets-root-view-' + hex(row[0]), f.read(f.base + symbols['z7_settings_view']) == 0)
            check('activation-opens-owned-page-' + hex(row[0]), f.open_request == (2, 0))
        else:
            check('native-event-preserved-' + str(i), row == old)
    call('sm_root_enter', ROOT_OBJECT)
    check('plain-display-settings-label', f.entry_label == 'Display settings')
    check('entry-and-navigation-no-file-io', f.file_events == before_io)
    # The host commits the staged grid table at the first safe paint boundary.
    grid_meta = f.words()[32]
    check('grid-six-rows-only', f.read(grid_meta + 20) == 0x00060006)
    check('new-row-not-in-grid', b'Display settings' not in bytes(f.u.mem_read(f.base + symbols['names'], 6 * 16)))
    call('sm_back_event')
    check('root-back-uses-native-parent-stack', f.back_request == 0x3a1)
    # Re-run preflight against restored stock identity, varying only one input.
    for offset, value in ((0, 0), (4, 0), (12, 1), (36, 1), (16, 0), (40, 0)):
        f.u.mem_write(ROOT_OBJECT, original)
        f.write(ROOT_OBJECT + offset, value)
        before = bytes(f.u.mem_read(ROOT_OBJECT, 44))
        check('reject-conflicting-overview-' + str(offset), call('sm_prepare') == 0)
        check('rejection-preserves-overview-' + str(offset), bytes(f.u.mem_read(ROOT_OBJECT, 44)) == before)
    f.u.mem_write(ROOT_OBJECT, root)
    # Full failed initialization must publish neither the overview nor page zero.
    bad = fixture(); bad.write(ROOT_OBJECT + 12, 1)
    snapshots = {address: bytes(bad.u.mem_read(address, 44)) for address in (ROOT_OBJECT, GRID, OWNED)}
    check('occupied-overview-rejects-module-load', bad.call(h['symbols']['z7_module_load_once'], STATE) != 8)
    for address, snapshot in snapshots.items():
        check('failed-load-no-menu-publication-' + hex(address), bytes(bad.u.mem_read(address, 44)) == snapshot)
    result = dict(passed=True, checks=checks, count=len(checks), module_sha256=m['module_sha256'],
        main_sha256=h['main_payload_sha256'], scope=__doc__, camera_access=False,
        hardware_test_authorized=False)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(checks))))


if __name__ == '__main__':
    main()
