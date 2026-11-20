"""Compiled original-Z7 readout mask ownership and settings integration.

SPDX-License-Identifier: MIT. Native loader, settings setters and native
mask interpreter execute. Incoming GUI state is supplied;
font/label drawing is supplied. No actual pixels, camera or card are verified.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2
from audit_z7_battery_percent import AutomaticFixture
from build_z7_module_host import ROOT, STATE

TABLE, SNAPSHOT, OBJECT = 0x1064d610, 0xa201d4d0, 0xa1833548
WIDGETS, FORMATS = (10, 11, 15), (0, 1, 5)


class ReadoutFixture(AutomaticFixture):
    def __init__(self, *args):
        super().__init__(*args)
        self.readout_dispatches = []
        self.hud_redraws = []
        for i in range(15):
            self.u.mem_write(0xa2019e78 + (230 + i) * 12, struct.pack('<3I', 0, 0xa2910000 + i * 64, 0))

    def hook(self, u, address, size, context):
        if address in (0x102f27a8, 0x102f2ada):
            self.readout_dispatches.append((address, u.reg_read(UC_ARM_REG_R0))); self.ret(0)
        elif address == 0x103faee0:
            self.hud_redraws.append((u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1))); self.ret(1)
        elif address == 0x103fbb5c and 230 <= u.reg_read(UC_ARM_REG_R1) < 245:
            text, slot = self.cstring(u.reg_read(UC_ARM_REG_R0)), u.reg_read(UC_ARM_REG_R1)
            record = 0xa2019e78 + slot * 12
            pointer = int.from_bytes(u.mem_read(record + 4, 4), 'little')
            u.mem_write(pointer, text.encode() + b'\0')
            u.mem_write(record, struct.pack('<I', len(text)))
            u.mem_write(record + 8, struct.pack('<I', u.reg_read(UC_ARM_REG_R2)))
            self.ret(0)
        elif address in (0x103faebe, 0x103fac5a, 0x103faec6):
            self.ret(0)
        else: super().hook(u, address, size, context)


def audit(raw, host, packet, module):
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Host/module fingerprint mismatch')
    f = ReadoutFixture(raw, host, packet)
    if f.call(host['symbols']['z7_module_load_once'], STATE) != 8: raise AssertionError('Module load')
    base = f.words()[12]; symbols = module['symbols']; checks = []
    def read(p): return int.from_bytes(f.u.mem_read(p, 4), 'little')
    def write(p, v): f.u.mem_write(p, struct.pack('<I', v))
    def word(name): return read(base + symbols[name])
    def setword(name, value): write(base + symbols[name], value)
    def call(name, *args): return f.call(base + symbols[name], *args)
    def before(): f.call(host['symbols']['z7_display_before_update'])
    def master():
        f.u.mem_write(OBJECT + 22, struct.pack('<2H', 0, 0)); call('sm_activate')
    model = base + symbols['z7_menu_settings']
    def info(preset, bits):
        for group in range(3):
            if call('z7_settings_information', model, preset, group, bool(bits & (1 << group))) != 1:
                raise AssertionError('Settings setter')
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    descriptors = [read(TABLE + i * 4) for i in range(61)]
    for i in WIDGETS:
        # Mixed baseline checks that ON does not synthesize native permissions.
        f.u.mem_write(descriptors[i] + 4, struct.pack('<9I', *([0xa5faffff ^ (i << 20)] * 9)))
        f.u.mem_write(read(descriptors[i] + 44), b'\1')
    original = [bytes(f.u.mem_read(p + 4, 36)) for p in descriptors]
    def masks(): return [bytes(f.u.mem_read(p + 4, 36)) for p in descriptors]
    def expected(bits, special=0):
        result = list(original)
        for index, i in enumerate(WIDGETS):
            words = list(struct.unpack('<9I', result[i]))
            if not bits & (1 << index) and not special & (1 << index):
                for bank in (0, 3): words[bank] &= ~0x909
            result[i] = struct.pack('<9I', *words)
        return result
    write(0xa181f91c, 0xa2c41000)
    f.u.mem_write(0xa2c41000, struct.pack('<4I', 4, 1, 0, 0xa2c42000))
    f.u.mem_write(0xa18237c6, b'\0'); f.u.mem_write(SNAPSHOT + 0x40, b'\0')
    f.u.mem_write(SNAPSHOT + 0x18a, b'\0'); f.u.mem_write(0xa18237b8, bytes(7))
    before(); check('default-off-does-not-edit-any-native-mask', masks() == original and not word('z7_readout_active'))
    master(); before()
    check('actual-native-master-action-activates-with-native-on-permissions', word('z7_readout_active') == 1 and masks() == original)
    check('all-on-master-does-not-dispatch-unchanged-native-groups', not f.readout_dispatches)
    for preset in range(4):
        setword('z7_readout_preset', preset)
        for bits in range(8):
            info(preset, bits)
            current = bytes(f.u.mem_read(SNAPSHOT, 0x33c)); before()
            check(f'preset-{preset}-information-{bits}-edits-only-six-owned-photo-words', masks() == expected(bits))
            check(f'preset-{preset}-information-{bits}-preserves-live-snapshot', bytes(f.u.mem_read(SNAPSHOT, 0x33c)) == current)
    check('no-permission-update-or-drawing-helper-is-called-by-policy', not f.readout_dispatches and not f.hud_redraws)
    prior = bytes(f.u.mem_read(0xa201d80c, 0x33c)); before()
    check('unchanged-pass-does-not-invalidate-previous-snapshot-again', bytes(f.u.mem_read(0xa201d80c, 0x33c)) == prior)
    info(3, 0); before()
    check('original-invalidator-complements-current-snapshot', bytes(f.u.mem_read(0xa201d80c, 0x33c)) == bytes(v ^ 255 for v in f.u.mem_read(SNAPSHOT, 0x33c)))
    previous = bytes(f.u.mem_read(0xa201d80c, 0x33c))
    f.call(host['symbols']['z7_display_before_paint'])
    check('paint-path-does-not-run-readout-policy', bytes(f.u.mem_read(0xa201d80c, 0x33c)) == previous)
    info(3, 0); before()
    for special in range(8):
        for i, offset in enumerate(FORMATS): f.u.mem_write(0xa18237b8 + offset, bytes([7 if special & (1 << i) else 0]))
        before(); check('special-native-formats-restore-complete-groups-' + str(special), masks() == expected(0, special))
    for warning in (16, 26, 27, 28):
        f.u.mem_write(0xa18237b8, bytes(7)); f.u.mem_write(0xa18237b8, bytes([warning])); before()
        check('identified-shutter-warning-retains-native-mask-' + str(warning), masks() == expected(0, 1) and f.call(0x102f2690, 10) == 0)
    f.u.mem_write(0xa18237b8, bytes(7)); before()
    for page in (0, 3):
        f.u.mem_write(SNAPSHOT + 0x18a, bytes([page]))
        for state in (0, 1):
            f.u.mem_write(SNAPSHOT + 0x338, struct.pack('<H', state))
            for operation in (0, 1, 3):
                f.u.mem_write(SNAPSHOT + 0x193, bytes([operation]))
                check(f'native-mask-interpreter-sees-suppression-page{page}-bank{state}-operation{operation}',
                    all(f.call(0x102f2690, widget) == 1 for widget in WIDGETS))
    f.u.mem_write(SNAPSHOT + 0x193, b'\0'); f.u.mem_write(SNAPSHOT + 0x338, bytes(2))
    for name, address, value in [('movie', SNAPSHOT + 0x40, b'\1'), ('alternate-output', 0xa18237c6, b'\2'),
            ('menu', 0xa2c41008, b'\1\0\0\0'), ('native-information-page', SNAPSHOT + 0x18a, b'\4')]:
        f.u.mem_write(address, value); before()
        check(name + '-restores-all-native-words', masks() == original and not word('z7_readout_active'))
        f.u.mem_write(address, bytes(len(value))); before()
        check(name + '-return-reacquires-eligible-native-mask', masks() == expected(0) and word('z7_readout_active') == 1)
    setword('z7_readout_preset', 4); before()
    check('invalid-preset-restores-native-words', masks() == original and not word('z7_readout_active'))
    setword('z7_readout_preset', 3); before()
    flags = read(model); write(model, flags | 4); before()
    check('invalid-settings-model-restores-native-words', masks() == original and not word('z7_readout_active'))
    write(model, flags); before()
    check('valid-model-return-reacquires-restored-native-baseline', masks() == expected(0) and word('z7_readout_active') == 1)
    foreign = descriptors[15] + 16; write(foreign, 0x12345678); before()
    check('foreign-word-preserved-and-other-owned-words-restored', read(foreign) == 0x12345678 and not word('z7_readout_active') and word('z7_readout_conflicts') == 1)
    stopped = masks(); before()
    check('foreign-word-conflict-latches-until-master-toggle', masks() == stopped)
    master(); before(); write(foreign, struct.unpack_from('<I', original[15], 12)[0]); master(); before()
    check('explicit-master-toggle-rearms-after-foreign-word-conflict', masks() == expected(0) and word('z7_readout_active') == 1)
    write(TABLE + 15 * 4, 0x100); before()
    check('foreign-binding-preserves-abandoned-mask-and-restores-other-groups', not word('z7_readout_active') and word('readout_pending') != 0 and masks()[10:12] == original[10:12])
    master(); before(); write(TABLE + 15 * 4, descriptors[15]); before()
    check('binding-return-finishes-owned-restoration-while-master-off', masks() == original and word('readout_pending') == 0)
    master(); before(); write(TABLE + 15 * 4, 0x100); before()
    write(descriptors[15] + 4, 0xdeadbeef); master(); before()
    write(TABLE + 15 * 4, descriptors[15]); before()
    check('binding-return-preserves-foreign-write-to-abandoned-mask', read(descriptors[15] + 4) == 0xdeadbeef and word('readout_pending') == 0)
    write(descriptors[15] + 4, struct.unpack_from('<I', original[15], 0)[0])
    master(); before()
    paint_binding = 0x1064c67c + 15 * 4; native_paint = read(paint_binding)
    write(paint_binding, 0x100); before()
    check('foreign-updater-binding-restores-owned-masks-without-dispatch', masks() == original and not f.readout_dispatches)
    master(); before(); write(paint_binding, native_paint); before()
    check('foreign-updater-return-with-master-off-keeps-native-state', masks() == original)
    # Invalid final binding must reject before touching either earlier group.
    write(TABLE + 15 * 4, 0x100); master(); before()
    check('invalid-final-binding-rejects-before-any-mask-store', masks() == original and not word('z7_readout_active'))
    write(TABLE + 15 * 4, descriptors[15]); before(); master(); before()
    check('master-disable-restores-exact-original-mask-state', masks() == original and not word('z7_readout_active'))
    denied = struct.unpack_from('<I', original[10])[0] & ~1
    write(descriptors[10] + 4, denied); info(3, 7); master(); before()
    check('enabled-readout-never-synthesizes-missing-native-photo-permission', read(descriptors[10] + 4) == denied and f.call(0x102f2690, 10) == 1)
    master(); before()
    check('disable-preserves-new-native-denied-permission-baseline', read(descriptors[10] + 4) == denied)
    check('policy-never-directly-dispatches-or-dirties-gui-objects', not f.readout_dispatches and not f.hud_redraws)
    return dict(passed=True, checks=checks, module_sha256=module['module_sha256'], main_sha256=host['main_payload_sha256'],
        native_mask_interpreter_executes=True, native_snapshot_invalidator_used=True,
        supplied_boundaries=['Loader services', 'GUI pool/page/output/control state', 'Prohibited direct dispatch and drawing calls are trapped',
            'Native menu label and drawing services'], preset_selection_diagnostic=True, native_disp_routing=False, actual_pixels=False, camera_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True); p.add_argument('--module', type=Path, required=True)
    p.add_argument('--legacy-build', type=Path, help='Optional exact older 20-byte API host rejection check')
    p.add_argument('--output', type=Path, required=True); args = p.parse_args(); output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists(): p.error('Choose a new private output')
    result = audit((args.build / 'module-host.emulator.main.bin').read_bytes(), json.loads((args.build / 'module-host.emulator.json').read_text()),
        (args.module / 'Z7APP.BIN').read_bytes(), json.loads((args.module / 'module.json').read_text()))
    if args.legacy_build:
        old = (args.legacy_build / 'module-host.emulator.main.bin').read_bytes()
        report = json.loads((args.legacy_build / 'module-host.emulator.json').read_text())
        if hashlib.sha256(old).hexdigest() != report['main_payload_sha256']: raise ValueError('Legacy fingerprint mismatch')
        fixture = ReadoutFixture(old, report, (args.module / 'Z7APP.BIN').read_bytes())
        regions = [(OBJECT, 44), (0xa1836f8c, 44)]
        regions += [(int.from_bytes(fixture.u.mem_read(TABLE + i * 4, 4), 'little'), 48) for i in range(61)]
        before = [bytes(fixture.u.mem_read(p, n)) for p, n in regions]
        status = fixture.call(report['symbols']['z7_module_load_once'], STATE)
        passed = status == 7 and before == [bytes(fixture.u.mem_read(p, n)) for p, n in regions] and not fixture.live
        if not passed: raise AssertionError('Older API must reject before native stores')
        result['checks'].append(dict(name='older-20-byte-api-rejects-before-native-stores-and-frees-module', passed=True))
        result['legacy_main_sha256'] = report['main_payload_sha256']
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__': main()
