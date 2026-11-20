"""Compiled six-group original-Z7 masks, native interpreter and ownership.

SPDX-License-Identifier: MIT. Native loader, model setters, mask interpreter
and invalidator execute. Incoming GUI/property state is supplied. No pixels,
actual DISP input, physical card or camera operation are established.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from audit_z7_display_base import BaseFixture
from audit_z7_display_readouts import TABLE, SNAPSHOT
from build_z7_module_host import ROOT, STATE

WIDGETS = (10, 11, 15, 5, 51, 2)


def audit(raw, host, packet, module):
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Fingerprint mismatch')
    if module['information_groups'] != dict(shutter=10, aperture=11, iso=15, shooting=5, release=51, focus=2):
        raise ValueError('Six-group diagnostic required')
    symbols = module['symbols']; checks = []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    def load():
        f = BaseFixture(raw, host, packet)
        if f.call(host['symbols']['z7_module_load_once'], STATE) != 8: raise AssertionError('Load')
        base = f.words()[12]
        # Isolate information filtering from the independently native base-page
        # setter; its intentional horizon snapshot change is not a mask write.
        for preset in range(4):
            f.call(base + symbols['z7_settings_component'], base + symbols['z7_menu_settings'], preset, 2, 0)
        desc = [int.from_bytes(f.u.mem_read(TABLE + i * 4, 4), 'little') for i in range(61)]
        for i in WIDGETS:
            f.u.mem_write(desc[i] + 4, struct.pack('<9I', *([0xa5faffff ^ (i << 20)] * 9)))
            f.u.mem_write(int.from_bytes(f.u.mem_read(desc[i] + 44, 4), 'little'), b'\1')
        return f, base, desc
    def masks(f, desc): return [bytes(f.u.mem_read(p + 4, 36)) for p in desc]
    def call(name, *args): return f.call(base + symbols[name], *args)
    def word(name): return int.from_bytes(f.u.mem_read(base + symbols[name], 4), 'little')
    def setword(name, v): f.u.mem_write(base + symbols[name], struct.pack('<I', v))
    def before(): f.call(host['symbols']['z7_display_before_update'])
    def master(on): call('z7_settings_flag', base + symbols['z7_menu_settings'], 0, on)
    def information(preset, bits):
        for group in range(6):
            if call('z7_settings_information', base + symbols['z7_menu_settings'], preset, group, bool(bits & (1 << group))) != 1:
                raise AssertionError('Model setter')
    def expected(bits, special=0):
        result = list(original)
        for index, i in enumerate(WIDGETS):
            words = list(struct.unpack('<9I', result[i]))
            if not bits & (1 << index) and not special & (1 << index):
                for bank in (0, 3): words[bank] &= ~0x909
            result[i] = struct.pack('<9I', *words)
        return result
    f, base, desc = load(); original = masks(f, desc)
    before(); check('default-off-preserves-all-61-descriptors', masks(f, desc) == original and not word('z7_readout_active'))
    master(1)
    for preset in range(4):
        setword('z7_readout_preset', preset)
        for bits in range(64):
            information(preset, bits); snapshot = bytes(f.u.mem_read(SNAPSHOT, 0x33c)); before()
            check(f'preset{preset}-groups{bits}-only-owned-lcd-photo-bits', masks(f, desc) == expected(bits))
            check(f'preset{preset}-groups{bits}-snapshot-preserved', bytes(f.u.mem_read(SNAPSHOT, 0x33c)) == snapshot)
    information(3, 0); before()
    for index, offset in enumerate((0, 1, 5)):
        for fmt in range(1, 29):
            f.u.mem_write(0xa18237b8, bytes(7)); f.u.mem_write(0xa18237b8 + offset, bytes([fmt])); before()
            check(f'exposure-format-{index}-{fmt}-preserves-warning-and-filters-ordinary-groups', masks(f, desc) == expected(0, 1 << index))
    f.u.mem_write(0xa18237b8, bytes(7)); before()
    for page in (0, 3):
        for bank in (0, 1):
            for operation in (0, 1, 3):
                f.u.mem_write(SNAPSHOT + 0x18a, bytes([page])); f.u.mem_write(SNAPSHOT + 0x338, struct.pack('<H', bank))
                f.u.mem_write(SNAPSHOT + 0x193, bytes([operation]))
                check(f'native-excludes-six-groups-page{page}-bank{bank}-operation{operation}', all(f.call(0x102f2690, i) == 1 for i in WIDGETS))
    f.u.mem_write(SNAPSHOT + 0x18a, b'\0'); f.u.mem_write(SNAPSHOT + 0x338, bytes(2)); f.u.mem_write(SNAPSHOT + 0x193, b'\0')
    master(0); before(); check('master-off-restores-all-12-owned-words', masks(f, desc) == original and not word('readout_pending'))
    # Each new group must independently follow conditional restoration rules.
    for widget in WIDGETS[3:]:
        for kind in ('foreign-word', 'descriptor', 'updater'):
            f, base, desc = load(); original = masks(f, desc); information(0, 0); master(1); before()
            index = WIDGETS.index(widget)
            address = desc[widget] + 16 if kind == 'foreign-word' else (TABLE if kind == 'descriptor' else 0x1064c67c) + widget * 4
            saved = bytes(f.u.mem_read(address, 4)); f.u.mem_write(address, struct.pack('<I', 0x12345678 if kind == 'foreign-word' else 0x100))
            before()
            check(f'{widget}-{kind}-deactivates-and-latches', not word('z7_readout_active') and word('readout_blocked'))
            check(f'{widget}-{kind}-preserves-foreign-value', int.from_bytes(f.u.mem_read(address, 4), 'little') == (0x12345678 if kind == 'foreign-word' else 0x100))
            if kind == 'descriptor':
                check(f'{widget}-abandoned-two-word-ownership-pending', word('readout_pending') == 3 << (index * 2))
            if kind != 'foreign-word': f.u.mem_write(address, saved)
            master(0); before()
            retained = list(original)
            if kind == 'foreign-word':
                words = list(struct.unpack('<9I', retained[widget])); words[3] = 0x12345678
                retained[widget] = struct.pack('<9I', *words)
            check(f'{widget}-{kind}-disabled-cleanup-restores-only-owned-native-words', masks(f, desc) == retained)
    check('no-direct-dispatch-or-object-drawing', not f.readout_dispatches and not f.hud_redraws)
    return dict(passed=True, checks=checks, module_sha256=module['module_sha256'], main_sha256=host['main_payload_sha256'],
        widgets=list(WIDGETS), masks_only=True, native_mask_interpreter_executes=True, preset_selection_supplied=True,
        supplied_boundaries=['Loader', 'GUI/property/snapshot state', 'Native label/drawing sinks'], actual_pixels=False, camera_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True); p.add_argument('--module', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(); output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists(): p.error('Choose a new private output')
    result = audit((args.build / 'module-host.emulator.main.bin').read_bytes(), json.loads((args.build / 'module-host.emulator.json').read_text()),
        (args.module / 'Z7APP.BIN').read_bytes(), json.loads((args.module / 'module.json').read_text()))
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__': main()
