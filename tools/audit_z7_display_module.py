"""Execute the compiled Z7 grid/histogram module through its real host API.

SPDX-License-Identifier: MIT. Native geometry/scalar/setter instructions execute;
file, kernel, heap, viewport, UI bridge and flash boundaries are explicit fixtures.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
from itertools import product
from unicorn.arm_const import UC_ARM_REG_R0

from audit_z7_module_host import HostFixture
from audit_grid_native_value import NativeValueGrid
from audit_grid_geometry import GridFixture, DESCRIPTOR
from audit_splash_image import MEM, STOCK_SHA
from trace_settings_storage import GRID_VALUE
from build_z7_module_host import ROOT, STATE, DISPLAY_PRESET

OBJECT, HISTOGRAM = 0xa1836f8c, 0xa1827404


class HistogramFixture(HostFixture):
    """Execute native visibility code; supply individual camera-context gates."""
    def __init__(self, *args):
        super().__init__(*args)
        self.u.mem_map(0xa2010000, 0x20000)
        self.u.mem_map(0xa2360000, 0x10000)
        self.excluded = self.blocked = 0
        self.exposure = 1
        self.histogram_available = False
        self.histogram_bins = [0] * 256
        self.histogram_requests = 0

    def hook(self, u, address, size, context):
        if address in (0x1017095a, 0x1017093e) and u.reg_read(UC_ARM_REG_R0) == 0xa2363384:
            self.ret(1)
        elif address == 0x104070ac:
            pointer = u.reg_read(UC_ARM_REG_R0)
            if pointer != 0xa201f6d8:
                raise AssertionError('Unexpected native histogram destination')
            self.histogram_requests += 1
            if self.histogram_available:
                u.mem_write(pointer, struct.pack('<256I', *self.histogram_bins))
            self.ret(int(self.histogram_available))
        elif address == 0x104065a4:
            key = u.reg_read(UC_ARM_REG_R0)
            if key not in (0x102c, 0x138d):
                raise AssertionError('Unexpected histogram property')
            self.ret(self.exposure if key == 0x102c else 0)
        elif address == 0x103ea09e:
            if u.reg_read(UC_ARM_REG_R0) != 12:
                raise AssertionError('Unexpected output exclusion')
            self.ret(self.excluded)
        elif address in (0x103709aa, 0x103ebb42):
            self.ret(self.blocked)
        elif address in (0x10369248, 0x10369214):
            self.ret(0)
        else:
            super().hook(u, address, size, context)


def audit(raw, host, stock, bundle, failures):
    if host['preset'] != DISPLAY_PRESET or hashlib.sha256(raw).hexdigest() != host['main_payload_sha256']:
        raise ValueError('Display host identity mismatch')
    if hashlib.sha256(stock).hexdigest() != STOCK_SHA:
        raise ValueError('Requires exact original Z7 MAIN')
    packet = (bundle / 'Z7APP.BIN').read_bytes()
    module = json.loads((bundle / 'module.json').read_text())
    if hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Display module fingerprint mismatch')
    checks = []
    def check(name, passed):
        checks.append(dict(name=name, passed=bool(passed)))
        if not passed:
            raise AssertionError(name)
    f = HostFixture(raw, host, packet)
    if module['kind'] == 'original-Z7-combined-display-module':
        # This audit isolates grid behavior with a supplied inactive battery GUI.
        f.u.mem_map(0xa2010000, 0x20000)
        f.u.mem_write(0xa18237d0, bytes(4))
    native_meta = bytes(f.u.mem_read(OBJECT + 40, 4))
    native_callbacks = bytes(f.u.mem_read(OBJECT + 16, 4))
    check('module-init-and-both-staged-registrations', f.call(host['symbols']['z7_module_load_once'], STATE) == 8 and
          f.words()[22:24] == (1, 1) and f.words()[34:36] == (1, 0))
    check('init-does-not-publish-native-menu-pointers', bytes(f.u.mem_read(OBJECT + 40, 4)) == native_meta and
          bytes(f.u.mem_read(OBJECT + 16, 4)) == native_callbacks)
    if module['kind'] == 'original-Z7-combined-display-module':
        check('combined-publishes-all-six-owned-display-services', all(f.words()[26:32]))
        for name, address in (('battery-preflight', 0x1064d610 + 18 * 4), ('grid-preflight', OBJECT)):
            bad = HostFixture(raw, host, packet)
            bad.u.mem_write(address, bytes(4))
            check(name + '-fails-before-any-native-publication',
                  bad.call(host['symbols']['z7_module_load_once'], STATE) == 7 and not bad.live and
                  bad.words()[19:36] == (0,) * 17 and
                  bytes(bad.u.mem_read(OBJECT + 40, 4)) == native_meta and
                  bytes(bad.u.mem_read(OBJECT + 16, 4)) == native_callbacks and
                  struct.unpack('<9I', bad.u.mem_read(HISTOGRAM + 4, 36)) == (0x444,) * 6 + (0x440,) * 3)
    # A supplied native page-list shape lets the GUI-owned bridge prove deferral.
    listing, records = 0xa2908000, 0xa2909000
    f.u.mem_write(0xa181f91c, struct.pack('<I', listing))
    f.u.mem_write(listing, struct.pack('<4I', 16, 1, 1, records))
    f.u.mem_write(records, struct.pack('<I', OBJECT))
    f.call(host['symbols']['z7_display_before_paint'])
    check('grid-active-defers-publication', f.words()[35] == 0 and bytes(f.u.mem_read(OBJECT + 40, 4)) == native_meta)
    f.u.mem_write(records, struct.pack('<I', 0xa1837bec))
    f.call(host['symbols']['z7_display_before_paint'])
    check('inactive-grid-commits-on-gui-bridge', f.words()[35] == 1 and
          int.from_bytes(f.u.mem_read(OBJECT + 40, 4), 'little') == f.words()[32] and
          int.from_bytes(f.u.mem_read(OBJECT + 16, 4), 'little') == f.words()[33])
    check('histogram-masks-expanded-exactly', struct.unpack('<9I', f.u.mem_read(HISTOGRAM + 4, 36)) == (0xccc,) * 9)
    for state in range(256):
        check('dual-histogram-gate-' + str(state), f.call(host['symbols']['z7_display_histogram_gate'], state) == int(state in (2, 3)))
    h = HistogramFixture(raw, host, packet)
    check('native-histogram-fixture-loads-module', h.call(host['symbols']['z7_module_load_once'], STATE) == 8)
    control = int.from_bytes(h.u.mem_read(HISTOGRAM + 44, 4), 'little')
    for mode, kind, auxiliary, excluded, exposure, blocked in product(range(4), range(4), range(2), range(2), range(2), range(2)):
        h.u.mem_write(0xa201d4d0 + 0x18a, bytes([mode]))
        h.u.mem_write(0xa201d308 + 0x10, bytes([kind]))
        h.u.mem_write(0xa201f698 + 0x1f, bytes([auxiliary]))
        h.excluded, h.exposure, h.blocked = excluded, exposure, blocked
        h.u.mem_write(control, bytes(2))
        h.call(0x1036d57c)
        visible = not auxiliary and mode in (2, 3) and not excluded and kind == 1 and exposure and not blocked
        dirty = not auxiliary and mode in (2, 3) and not excluded and kind != 2
        check(f'native-histogram-context-{mode}-{kind}-{auxiliary}-{excluded}-{exposure}-{blocked}',
              bytes(h.u.mem_read(control, 2)) == bytes([int(dirty), int(visible)]))
    # Trace the original context producer and its snapshot copy too. Only the
    # statistics service and mutex are supplied; never force its output context.
    h.u.mem_write(0xa181c988, bytes(2))  # Supplied unextended viewport capability.
    h.exposure, h.blocked, h.excluded = 1, 0, 0
    for mode, viewport_flag, available in product(range(4), range(2), range(2)):
        h.u.mem_write(0xa201d4d0 + 0x18a, bytes([mode]))
        h.u.mem_write(0xa201d4d0 + 0x40, b'\0')
        h.u.mem_write(0xa2367974, bytes(0x420))
        h.u.mem_write(0xa2367974 + 0x28, bytes([viewport_flag]))
        h.histogram_available = bool(available)
        h.histogram_bins = [i % 13 for i in range(256)]
        h.histogram_requests = 0
        h.u.mem_write(0xa201d318, b'\x09')
        h.call(0x10370696)
        expected = mode in (2, 3) and not viewport_flag and available
        check(f'native-histogram-producer-{mode}-{viewport_flag}-{available}',
              bytes(h.u.mem_read(0xa201d318, 1)) == bytes([int(expected)]) and
              h.histogram_requests == int(mode in (2, 3) and not viewport_flag))
        if expected:
            check(f'native-histogram-producer-copies-bins-{mode}',
                  bytes(h.u.mem_read(0xa201df88, 1024)) == struct.pack('<256I', *h.histogram_bins) and
                  int.from_bytes(h.u.mem_read(0xa201d33c, 4), 'little') == 12)
    for kind in ('failed-init', 'foreign-controls', 'foreign-callback'):
        bad = HostFixture(raw, host, (failures / (kind + '.BIN')).read_bytes())
        check(kind + '-rejects-and-frees-module', bad.call(host['symbols']['z7_module_load_once'], STATE) == 7 and not bad.live)
        check(kind + '-clears-all-pending-hooks-and-menu', bad.words()[19:36] == (0,) * 17)
        check(kind + '-preserves-native-menu-and-histogram', bytes(bad.u.mem_read(OBJECT + 40, 4)) == native_meta and
              bytes(bad.u.mem_read(OBJECT + 16, 4)) == native_callbacks and
              struct.unpack('<9I', bad.u.mem_read(HISTOGRAM + 4, 36)) == (0x444,) * 6 + (0x440,) * 3)

    base, memory_size = f.words()[12], f.words()[14]
    loaded_memory = bytes(f.u.mem_read(base, memory_size))
    loaded_state = bytes(f.u.mem_read(STATE, 256))
    def native_fixture():
        a = NativeValueGrid(raw)
        a.initialize()
        a.u.mem_map(STATE, 4096)
        a.u.mem_write(STATE, loaded_state)
        a.u.mem_write(base, loaded_memory)
        a.u.mem_write(OBJECT + 40, struct.pack('<I', f.words()[32]))
        a.u.mem_write(OBJECT + 16, struct.pack('<I', f.words()[33]))
        return a
    a = native_fixture()
    symbols = module['symbols']
    layouts = [('fourths', 1, 0x1901, '4x4 grid'), ('thirds', 2, 0x7a30, '3x3 grid'),
               ('golden', 3, 0x7a31, 'Golden ratio'), ('center', 4, 0x7a32, 'Center cross'),
               ('dense', 5, 0x7a33, '6x6 grid'), ('off', 0, 0x1902, 'Off')]
    meta = struct.unpack('<7I', a.u.mem_read(f.words()[32], 28))
    dispatch = struct.unpack('<6I', a.u.mem_read(meta[4], 24))
    for row, (name, value, control, label) in enumerate(layouts):
        if name == 'off':
            function = 0x104f5593
        else:
            activation = [fn for event, fn, _, _ in struct.iter_unpack('<4I', a.u.mem_read(dispatch[row], 272)) if event == 0x239]
            check(name + '-activation-is-owned-module-code', activation == [base + symbols[name]])
            function = activation[0]
        a.call(function)
        check(name + '-stores-native-scalar', a.word(GRID_VALUE) == value)
        a.labels.clear(); a.rows.clear(); a.marks.clear()
        a.u.mem_write(OBJECT + 36, struct.pack('<I', MEM + 0x10000))
        a.call(base + symbols['grid_enter'], OBJECT)
        check(name + '-six-labels-and-native-selection', a.labels == [(39 + i, entry[3]) for i, entry in enumerate(layouts)] and
              a.rows == list(range(39, 45)) and a.marks == [(control, 1)])
        check(name + '-original-native-visibility', a.call(0x1037723e) == int(value != 0))
    check('menu-selection-performs-no-flash-programming', not a.operations)
    # Sample every original indexed property once with the extended grid value.
    b = NativeValueGrid(stock)
    b.initialize()
    a.set_raw(3); b.set_raw(3)
    keys = []
    for group in range(72):
        pointer = 0x114d8d9c + group * 28
        if b.word(pointer):
            _, count = struct.unpack('<HH', b.u.mem_read(pointer + 12, 4))
            if count > 256:
                raise ValueError('Unexpected native property catalogue')
            keys.extend((group << 8) | i for i in range(count))
    keys += [0, 0xffff, 0xffffffff]
    unchanged = flags = True
    for key in keys:
        ar, br = a.scalar(key, MEM), b.scalar(key, MEM)
        unchanged &= ar == br and a.word(MEM) == (1 if key == 0x102d and br == 1 else b.word(MEM))
        flags &= a.scalar_flags == b.scalar_flags
    check('all-native-scalars-change-only-owned-grid-value', unchanged)
    check('native-scalar-nzcvq-preserved', flags)
    check('normalization-never-rewrites-persistent-value', a.word(GRID_VALUE) == 3)

    geometry_calls = 0
    for viewport in ((0, 0, 720, 480), (20, 40, 700, 440), (0, 0, 640, 426)):
        a.viewport = viewport
        reference = GridFixture(stock, viewport, 0)
        for mode in range(3):
            for crop in (0, 1, 2, 4, 8):
                reference.crop = crop
                a.call(0x100704fa, 0x402, crop, MEM + 0x800)
                for stored in (0, 1, 2, 3, 4, 5, 6, 0xffffffff):
                    a.set_raw(stored)
                    a.call(0x10376da0, mode)
                    actual = struct.unpack('<hhIHHhhIHHHHBBH', a.u.mem_read(DESCRIPTOR, 32))
                    expected = reference.geometry(mode, {2: 2, 3: 2, 4: 1, 5: 5}.get(stored, 3))
                    geometry_calls += 2
                    if stored != 3:
                        good = actual == expected
                    else:
                        good = all(actual[i] == expected[i] for i in (0, 2, 4, 6, 7, 9, 10, 11, 12, 13, 14))
                        for origin, interval, span in ((1, 3, 7), (5, 8, 2)):
                            offset = actual[origin] - (expected[origin] - expected[interval])
                            good &= abs(offset - expected[span] * ((3 - math.sqrt(5)) / 2)) < 1
                            good &= 2 * offset + actual[interval] == expected[span]
                    check(f'geometry-{viewport}-{mode}-{crop}-{stored}', good)
        for stored in range(6):
            a.set_raw(stored)
            a.viewport_type = 1
            a.call(0x10376da0, 0)
            expected = bytes(a.u.mem_read(DESCRIPTOR, 32))
            a.viewport_type = 0
            a.call(0x10376da0, 0)
            check(f'native-notification-sees-final-layout-{viewport}-{stored}', a.geometry_notifications[-1] == expected)
            a.viewport_type = 1
            geometry_calls += 2
    check('immutable-module-count-tables', bytes(a.u.mem_read(base + symbols['tables'], 384)) ==
          loaded_memory[symbols['tables']:symbols['tables'] + 384])
    return dict(passed=True, checks=checks, geometry_calls=geometry_calls,
        indexed_scalar_keys=len(keys), module_sha256=module['module_sha256'],
        main_sha256=host['main_payload_sha256'], supplied_boundaries=['File dispatch', 'Kernel', 'Heap',
            'Viewport/crop', 'UI services bridged to original raw setter', 'Storage/OS fixtures'],
        camera_access=False, card_access=False, physical_persistence_verified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--module', type=Path, required=True)
    parser.add_argument('--failures', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--stock', type=Path, default=ROOT / '.private/builds/20261021-laptop-01/stock-main.bin')
    args = parser.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists():
        parser.error('Choose a new private evidence path')
    raw = (args.build / 'module-host.emulator.main.bin').read_bytes()
    host = json.loads((args.build / 'module-host.emulator.json').read_text())
    result = audit(raw, host, args.stock.read_bytes(), args.module, args.failures)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(passed=True, checks=len(result['checks']), geometry_calls=result['geometry_calls'])))


if __name__ == '__main__':
    main()
