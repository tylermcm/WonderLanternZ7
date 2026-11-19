"""Automatic native battery module policy, ownership and retirement audit.

SPDX-License-Identifier: MIT. Real compiled module/host and native pool, snapshot,
zeroing, label-dispatch and HUD initializer instructions execute. Incoming GUI,
telemetry, font, list and pixel services remain explicit supplied boundaries.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2
from audit_z7_battery_display import NativeBatteryDisplayFixture, POOL, SLOTS, LABEL
from build_z7_module_host import ROOT, STATE

ICON, CONTROL = 0xa1fa08ec, 0xa1824a14


class AutomaticFixture(NativeBatteryDisplayFixture):
    def __init__(self, *args):
        super().__init__(*args)
        self.getter_calls = self.font_invalidations = 0
        self.u.mem_write(0xa181f91c, bytes(4))
        self.u.mem_write(0xa18237c6, b'\0')
        self.u.mem_write(CONTROL + 1, b'\1')
        self.u.mem_write(CONTROL + 36, struct.pack('<I', ICON))
        self.u.mem_write(ICON, bytes(284))
        for offset, value in ((4, 4), (8, 0x1120), (12, 0), (16, 2 | (396 << 16)), (20, 62 | (428 << 16)),
                              (40, 1), (52, 2), (56, 0xffffffff), (72, 0xa201e3b4), (76, 0x10384969)):
            self.u.mem_write(ICON + offset, struct.pack('<I', value))

    def hook(self, u, address, size, context):
        if address == 0x10437684:
            self.getter_calls += 1
            super().hook(u, address, size, context)
        elif address == 0x103fbb5c:
            p, index = u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)
            value = self.cstring(p)
            if index != 299 or len(value) > 7: raise AssertionError('Unexpected overlay label write')
            self.u.mem_write(0xa2c40000, value.encode() + b'\0')
            self.u.mem_write(LABEL, struct.pack('<I', len(value)))
            self.u.mem_write(LABEL + 8, struct.pack('<I', u.reg_read(UC_ARM_REG_R2)))
            self.labels.append((value, index))
            self.ret(0)
        elif address == 0x104e983a:
            self.font_invalidations += 1
            self.ret(0)
        else:
            super().hook(u, address, size, context)


def audit(raw, host, packet, module):
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Host/module fingerprint mismatch')
    if not module['configuration']['battery_percent_enabled']: raise ValueError('Audit requires enabled module')
    checks = []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    def load():
        f = AutomaticFixture(raw, host, packet)
        if f.call(host['symbols']['z7_module_load_once'], STATE) != 8: raise AssertionError('Module load failed')
        return f, f.words()[12]
    def word(f, base, name): return int.from_bytes(f.u.mem_read(base + module['symbols']['z7_battery_' + name], 4), 'little')
    def setword(f, base, name, value): f.u.mem_write(base + module['symbols']['z7_battery_' + name], struct.pack('<I', value))
    def before(f): f.call(host['symbols']['z7_display_before_paint'])
    def after(f): f.call(host['symbols']['z7_display_after_paint'])
    def paint(f, base): return f.call(base + module['symbols']['painter'], word(f, base, 'object'), 0, 0, 0)
    f, base = load()
    check('init-publishes-no-gui-object-or-label', not f.labels and not f.list_calls and word(f, base, 'object') == 0)
    before(f); after(f)
    object_pointer = word(f, base, 'object')
    check('eligible-native-battery-creates-one-owned-text', object_pointer and f.labels == [('63%', 299)] and len(f.list_calls) == 1 and f.getter_calls == 1)
    check('native-sample-and-object-published', word(f, base, 'percent') == 63 and word(f, base, 'samples') == 1)
    check('compact-original-lcd-hud-font-selected', int.from_bytes(f.u.mem_read(LABEL + 8, 4), 'little') == 100)
    paint(f, base)
    check('native-painter-uses-frame-clear-silhouette-and-text', [p[0] for p in f.paint_calls] == [0x10433912] * 5 + [0x10384968])
    f.u.mem_write(ICON + 52, struct.pack('<2I', 0x1000, 0x31a)); f.paint_calls.clear(); paint(f, base)
    outline = struct.unpack('<24I', f.paint_calls[1][1]); text = struct.unpack('<24I', f.paint_calls[-1][1])
    check('native-warning-palette-preserved-for-frame-and-text', outline[13:15] == text[13:15] == (0x1000, 0x31a))
    f.getter_calls = 0
    for _ in range(15): before(f)
    check('fifteen-following-paint-passes-do-not-resample', f.getter_calls == 0)
    before(f)
    check('sixteenth-following-pass-resamples-once', f.getter_calls == 1)
    f.u.mem_write(0xa235aefc, struct.pack('<I', 100))
    for _ in range(16): before(f)
    after(f)
    check('changed-sample-updates-label-and-invalidates-font', f.labels[-1] == ('100%', 299) and f.font_invalidations >= 1 and len(f.list_calls) == 1)
    setword(f, base, 'enabled', 0); before(f)
    f.paint_calls.clear(); paint(f, base)
    check('disabled-overlay-clears-and-restores-stock-icon', [p[0] for p in f.paint_calls] == [0x10433912, 0x10384968] and
          bytes(f.u.mem_read(object_pointer + 40, 4)) == bytes(4) and bytes(f.u.mem_read(ICON + 40, 4)) == struct.pack('<I', 1))
    count = f.getter_calls
    for _ in range(32): before(f); after(f)
    check('disabled-feature-does-no-sampling-or-new-registration', f.getter_calls == count and len(f.list_calls) == 1)
    setword(f, base, 'enabled', 1); before(f); after(f)
    check('reenable-samples-immediately-and-reuses-object', f.getter_calls == count + 1 and word(f, base, 'object') == object_pointer and len(f.list_calls) == 1)
    f.u.mem_write(0xa235aefc, struct.pack('<I', 101))
    for _ in range(16): before(f)
    paint(f, base)
    count = f.getter_calls
    for _ in range(15): before(f); after(f)
    check('invalid-samples-retire-and-remain-rate-limited', f.getter_calls == count and bytes(f.u.mem_read(object_pointer + 40, 4)) == bytes(4))
    f.u.mem_write(0xa235aefc, struct.pack('<I', 50)); before(f); after(f)
    check('valid-data-recovers-at-next-scheduled-sample', word(f, base, 'percent') == 50 and f.labels[-1] == ('50%', 299))
    f.u.mem_write(0xa2c40000, b'AF\0'); f.u.mem_write(LABEL, struct.pack('<I', 2))
    old_labels = list(f.labels); before(f); paint(f, base); after(f)
    check('foreign-label-is-never-overwritten-or-drawn', f.labels == old_labels and bytes(f.u.mem_read(0xa2c40000, 3)) == b'AF\0' and
          bytes(f.u.mem_read(object_pointer + 40, 4)) == bytes(4))
    for case in ('disabled', 'unknown-setting', 'evf', 'movie', 'menu', 'no-icon', 'hidden-icon', 'foreign-painter', 'alternate-layout', 'bar-fallback', 'foreign-slot', 'foreign-label', 'full-global-pool', 'plug-glyph', 'foreign-image-kind', 'background-glyph', 'font-too-large', 'font-out-of-range'):
        bad, loaded = load()
        if case == 'disabled': setword(bad, loaded, 'enabled', 0)
        if case == 'unknown-setting': setword(bad, loaded, 'enabled', 2)
        if case == 'evf': bad.u.mem_write(0xa18237c6, b'\2')
        if case == 'movie': bad.u.mem_write(0xa201d510, b'\1')
        if case == 'menu':
            bad.u.mem_write(0xa181f91c, struct.pack('<I', 0xa2c41000)); bad.u.mem_write(0xa2c41008, struct.pack('<I', 1))
        if case == 'no-icon': bad.u.mem_write(CONTROL + 1, b'\0')
        if case == 'hidden-icon': bad.u.mem_write(ICON + 40, bytes(4))
        if case == 'foreign-painter': bad.u.mem_write(ICON + 76, struct.pack('<I', 0x100202b5))
        if case == 'alternate-layout': bad.u.mem_write(ICON + 16, struct.pack('<I', 658 | (396 << 16)))
        if case == 'plug-glyph': bad.u.mem_write(ICON + 8, struct.pack('<I', 0x112a))
        if case == 'foreign-image-kind': bad.u.mem_write(ICON + 12, struct.pack('<I', 2))
        if case == 'background-glyph': bad.u.mem_write(ICON + 8, struct.pack('<I', 0x1121))
        if case == 'font-too-large': bad.u.mem_write(0xa182380e, b'\0')
        if case == 'font-out-of-range': bad.u.mem_write(0xa182380e, b'\xff')
        if case == 'bar-fallback': bad.u.mem_write(0xa18b4de8, struct.pack('<I', 1))
        if case == 'foreign-slot': bad.u.mem_write(SLOTS + 1199 * 4, struct.pack('<I', ICON))
        if case == 'foreign-label': bad.u.mem_write(LABEL, struct.pack('<I', 5))
        if case == 'full-global-pool':
            flags = int.from_bytes(bad.u.mem_read(0xa181c77c, 4), 'little'); bad.u.mem_write(flags, struct.pack('<1200I', *([1] * 1200)))
        before(bad); after(bad)
        check(case + '-publishes-no-overlay-or-label', word(bad, loaded, 'object') == 0 and not bad.labels and not bad.list_calls)
    rebuilt, loaded = load(); before(rebuilt); after(rebuilt)
    old = word(rebuilt, loaded, 'object')
    rebuilt.u.mem_write(SLOTS + 1199 * 4, bytes(4)); before(rebuilt); after(rebuilt)
    check('gui-slot-rebuild-recreates-with-fresh-ownership', word(rebuilt, loaded, 'object') not in (0, old) and len(rebuilt.list_calls) == 2)
    rebuilt.paint_calls.clear(); rebuilt.call(loaded + module['symbols']['painter'], old, 0, 0, 0)
    check('stale-native-callback-never-draws-detached-object', not rebuilt.paint_calls)
    reset, loaded = load(); before(reset); after(reset)
    reset.u.mem_write(SLOTS + 1199 * 4, bytes(4)); reset.u.mem_write(LABEL, bytes(4)); reset.u.mem_write(0xa2c40000, b'\0')
    before(reset); after(reset)
    check('gui-rebuild-reclaims-only-empty-reset-label', len(reset.list_calls) == 2 and reset.labels == [('63%', 299), ('63%', 299)])
    stolen, loaded = load(); before(stolen); after(stolen); before(stolen)
    stolen.u.mem_write(0xa2c40000, b'AF\0'); stolen.u.mem_write(LABEL, struct.pack('<I', 2)); stolen.paint_calls.clear()
    paint(stolen, loaded)
    check('label-change-between-prepaint-and-painter-cannot-draw-foreign-text',
          not any(p[0] == 0x10384968 and int.from_bytes(p[1][:4], 'little') == 0x7a40 for p in stolen.paint_calls))
    font, loaded = load(); before(font); after(font)
    font.u.mem_write(LABEL + 8, struct.pack('<I', 0)); font.paint_calls.clear(); before(font); paint(font, loaded); after(font)
    check('foreign-font-change-retires-without-overwriting-label', int.from_bytes(font.u.mem_read(LABEL + 8, 4), 'little') == 0 and
          not any(p[0] == 0x10384968 and int.from_bytes(p[1][:4], 'little') == 0x7a40 for p in font.paint_calls))
    return dict(passed=True, checks=checks, module_sha256=module['module_sha256'], main_sha256=host['main_payload_sha256'],
        sampling_interval_gui_passes=16, supplied_boundaries=['GUI/control instance and transitions', 'Native incoming telemetry and mutex',
            'Font/label/list/pixel services', 'File/kernel/heap'], physical_camera=False, visual_validation=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True); parser.add_argument('--module', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--disabled-module', type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists(): parser.error('Choose a new private evidence path')
    host = json.loads((args.build / 'module-host.emulator.json').read_text()); module = json.loads((args.module / 'module.json').read_text())
    result = audit((args.build / 'module-host.emulator.main.bin').read_bytes(), host, (args.module / 'Z7APP.BIN').read_bytes(), module)
    if args.disabled_module:
        off = json.loads((args.disabled_module / 'module.json').read_text()); packet = (args.disabled_module / 'Z7APP.BIN').read_bytes()
        if off['configuration']['battery_percent_enabled'] or hashlib.sha256(packet).hexdigest() != off['module_sha256']:
            raise ValueError('Requires fingerprinted disabled configuration')
        f = AutomaticFixture((args.build / 'module-host.emulator.main.bin').read_bytes(), host, packet)
        status = f.call(host['symbols']['z7_module_load_once'], STATE)
        for _ in range(32):
            f.call(host['symbols']['z7_display_before_paint']); f.call(host['symbols']['z7_display_after_paint'])
        good = status == 8 and not f.labels and not f.list_calls and not f.getter_calls
        result['checks'].append(dict(name='disabled-sd-package-admitted-without-sampling-or-drawing', passed=good))
        if not good: raise AssertionError('Disabled SD configuration did work')
        result['disabled_module_sha256'] = off['module_sha256']
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__': main()
