"""Native Z7 LCD grid suppression, native rebuild and preset edit contracts.

SPDX-License-Identifier: MIT. Original geometry builder and compiled callbacks
execute. Incoming saved grid/crop, viewport, property and GUI state are supplied.
No physical storage, output scanout or camera operation is established.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_PC

from audit_z7_display_base import BaseFixture
from audit_z7_display_readouts import SNAPSHOT
from build_z7_module_host import ROOT, STATE

DESCRIPTOR, GRID_RAW = 0xa2020c2c, 0xa24f182c


class GridVisibilityFixture(BaseFixture):
    def __init__(self, raw, host, packet):
        super().__init__(raw, host, packet)
        self.grid_scalar = host['symbols']['z7_display_scalar']
        self.grid_available = 1; self.grid_excluded = {0x2b: 0, 0x6e: 0}
        self.scalar_only = False

    def hook(self, u, address, size, context):
        if self.scalar_only and address in (0x104065a4, 0x104065b0, 0x103673ac):
            raise AssertionError('Scalar callback re-entered a native property service')
        if address == 0x104065a4 and u.reg_read(UC_ARM_REG_R0) == 0x102d:
            # The saved native scalar input is supplied. Run the real host/
            # module scalar callback, then return to original1037723E code.
            u.reg_write(UC_ARM_REG_R1, int.from_bytes(u.mem_read(GRID_RAW, 4), 'little'))
            u.reg_write(UC_ARM_REG_PC, self.grid_scalar | 1)
        elif address == 0x10377010: self.ret(self.grid_available)
        elif address == 0x103ea09e and u.reg_read(UC_ARM_REG_R0) in self.grid_excluded:
            self.ret(self.grid_excluded[u.reg_read(UC_ARM_REG_R0)])
        else: super().hook(u, address, size, context)


def audit(raw, host, packet, module):
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Fingerprint mismatch')
    f = GridVisibilityFixture(raw, host, packet)
    f.u.mem_map(0xa24f0000, 0x10000)  # Supplied native saved-grid scalar region.
    if f.call(host['symbols']['z7_module_load_once'], STATE) != 8: raise AssertionError('Module load')
    base = f.words()[12]; symbols = module['symbols']; model = base + symbols['z7_menu_settings']
    checks = []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    def word(p): return int.from_bytes(f.u.mem_read(p, 4), 'little')
    def before(): f.call(host['symbols']['z7_display_before_update'])
    def grid(value):
        if f.call(base + symbols['z7_settings_component'], model, 0, 0, value) != 1: raise AssertionError('Compiled grid setter')
    def master(value): f.call(base + symbols['z7_settings_flag'], model, 0, value)
    def geometry(mode):
        f.call(0x10376da0, mode)
        return bytes(f.u.mem_read(DESCRIPTOR, 32))
    original_tables = bytes(f.u.mem_read(base + symbols['tables'], 384))
    master(1); before()
    for viewport in ((0, 0, 720, 480), (20, 40, 700, 440)):
        f.viewport = viewport
        for mode in range(3):
            for style in range(6):
                f.u.mem_write(GRID_RAW, struct.pack('<I', style))
                f.properties[0x402] = (0, 2, 8)[mode]
                grid(1); before(); ordinary = geometry(mode)
                stores = list(f.property_writes)
                snapshot = bytes(f.u.mem_read(SNAPSHOT, 0x33c))
                f.u.mem_write(SNAPSHOT + 0x33c, snapshot)
                grid(0); before(); hidden = geometry(mode)
                check(f'grid-off-{viewport}-{mode}-{style}-uses-native-visibility-without-geometry-or-setting-writes',
                    f.call(0x1037723e) == 0 and hidden == ordinary and
                    word(GRID_RAW) == style and f.property_writes == stores and
                    bytes(f.u.mem_read(SNAPSHOT, 0x33c)) == snapshot)
                check(f'grid-edit-{viewport}-{mode}-{style}-invalidates-native-layout-on-same-page',
                    bytes(f.u.mem_read(SNAPSHOT + 0x33c, 0x33c)) == bytes(value ^ 255 for value in snapshot))
                grid(1); before(); restored = geometry(mode)
                check(f'grid-on-{viewport}-{mode}-{style}-rebuilds-identical-native-descriptor', restored == ordinary and word(GRID_RAW) == style)
    check('component-edits-preserve-all-owned-style-tables', bytes(f.u.mem_read(base + symbols['tables'], 384)) == original_tables)
    f.u.mem_write(GRID_RAW, struct.pack('<I', 1)); grid(0); before()
    seed = bytes((i * 17 + 3) & 255 for i in range(32))
    f.u.mem_write(DESCRIPTOR, seed)
    f.call(base + symbols['grid_geometry'], DESCRIPTOR)
    check('grid-component-does-not-change-native-geometry-fields', bytes(f.u.mem_read(DESCRIPTOR, 32)) == seed)
    for enabled in range(2):
        grid(enabled); before()
        for style in range(6):
            f.u.mem_write(GRID_RAW, struct.pack('<I', style))
            for available in range(2):
                for first in range(2):
                    for second in range(2):
                        f.grid_available = available; f.grid_excluded = {0x2b: first, 0x6e: second}
                        check(f'native-visibility-{enabled}-{style}-{available}-{first}-{second}',
                            f.call(0x1037723e) == int(enabled and style and available and not first and not second))
    f.grid_available = 1; f.grid_excluded = {0x2b: 0, 0x6e: 0}
    f.u.mem_write(GRID_RAW, struct.pack('<I', 1)); grid(0); before()
    f.scalar_only = True
    try:
        for key in (0, 1, 0x102c, 0x102d, 0x138d, 0x2f15, 0xffffffff):
            for value in (0, 1, 2, 3, 4, 5, 0xffffffff):
                check(f'scalar-callback-only-edits-grid-key-{key}-{value}',
                    f.call(host['symbols']['z7_display_scalar'], key, value) == (0 if key == 0x102d else value))
    finally: f.scalar_only = False
    for name in ('movie', 'output', 'menu', 'master-off', 'foreign-property', 'foreign-snapshot', 'invalid-model', 'information-enabled'):
        snapshot = bytes(f.u.mem_read(SNAPSHOT, 0x33c)); flags = word(model); pages = word(model + 4)
        property_value = f.properties[0x2f15]
        if name == 'movie': f.u.mem_write(SNAPSHOT + 0x40, b'\1')
        if name == 'output': f.u.mem_write(0xa18237c6, b'\2')
        if name == 'menu': f.u.mem_write(0xa2c41008, struct.pack('<I', 1))
        if name == 'master-off': master(0)
        if name == 'foreign-property': f.properties[0x2f15] = 2
        if name == 'foreign-snapshot': f.u.mem_write(SNAPSHOT + 0x18a, b'\2')
        if name == 'invalid-model': f.u.mem_write(model, struct.pack('<I', 0x80000001))
        if name == 'information-enabled': f.call(base + symbols['z7_settings_page'], model, 4, 1)
        if name == 'foreign-property': before()  # GUI ownership validation precedes rendering.
        f.u.mem_write(DESCRIPTOR, seed); f.call(base + symbols['grid_geometry'], DESCRIPTOR)
        check(name + '-retains-native-grid-descriptor', bytes(f.u.mem_read(DESCRIPTOR, 32)) == seed)
        check(name + '-native-scalar-retains-grid-outside-custom-owner',
            f.call(host['symbols']['z7_display_scalar'], 0x102d, 1) == 1)
        f.u.mem_write(SNAPSHOT, snapshot); f.u.mem_write(model, struct.pack('<2I', flags, pages))
        f.u.mem_write(0xa18237c6, b'\0'); f.u.mem_write(0xa2c41008, bytes(4)); f.properties[0x2f15] = property_value
        if name == 'foreign-property':
            master(0); before(); master(1); before()
        check(name + '-eligible-return-resumes-custom-grid-policy',
            f.call(host['symbols']['z7_display_scalar'], 0x102d, 1) == 0)
    foreign = DESCRIPTOR + 0x100
    f.u.mem_write(foreign, seed); f.call(base + symbols['grid_geometry'], foreign)
    check('foreign-descriptor-pointer-remains-unchanged', bytes(f.u.mem_read(foreign, 32)) == seed)
    snapshot = bytes(f.u.mem_read(SNAPSHOT, 0x33c)); f.u.mem_write(SNAPSHOT + 0x33c, snapshot)
    master(0); before()
    check('master-off-on-same-native-page-invalidates-grid-retirement',
        bytes(f.u.mem_read(SNAPSHOT + 0x33c, 0x33c)) == bytes(value ^ 255 for value in snapshot))
    retired = geometry(0)
    check('master-off-rebuilds-native-counts-without-changing-saved-style',
        struct.unpack_from('<H', retired, 10)[0] == 3 and struct.unpack_from('<H', retired, 22)[0] == 3 and word(GRID_RAW) == 1)
    return dict(passed=True, checks=checks, main_sha256=host['main_payload_sha256'], module_sha256=module['module_sha256'],
        original_geometry_calls=109, original_geometry_builder_executes=True, native_invalidator_executes=True,
        lcd_descriptor=hex(DESCRIPTOR), native_visibility='0x1037723E', geometry_fields_changed_by_suppression=False,
        native_grid_setting_written=False, scalar_callback_reenters_property_service=False,
        supplied_boundaries=['Incoming saved grid/crop and GUI state', 'Viewport/property service results', 'Native visibility eligibility/exclusion service results', 'Loader/kernel/filesystem/heap'],
        actual_pixels=False, camera_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True); p.add_argument('--module', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); output = a.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists(): p.error('Choose a new private output')
    result = audit((a.build / 'module-host.emulator.main.bin').read_bytes(), json.loads((a.build / 'module-host.emulator.json').read_text()),
        (a.module / 'Z7APP.BIN').read_bytes(), json.loads((a.module / 'module.json').read_text()))
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']), native_geometry_calls=result['original_geometry_calls'])))


if __name__ == '__main__': main()
