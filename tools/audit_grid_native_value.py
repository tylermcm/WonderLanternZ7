"""Audit the existing-scalar grid experiment with original Z7 instructions.

Fresh instances carry only synthetic internal flash bytes. Native scalar reads,
raw writes, startup validation, main journal and worker instructions execute.
OS/event/flash, UI-service/widget and viewport boundaries are supplied. This
does not verify physical storage, all property consumers or camera recovery.
"""
import argparse
import gc
import json
from pathlib import Path
import struct

from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_PC, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_CPSR
from audit_splash_image import STACK, STOP, ARGUMENTS, SAVED
from trace_settings_storage import SettingsFixture, MEM, GRID_VALUE, SCHEMA
from audit_grid_geometry import GridFixture, DESCRIPTOR
from build_grid_firmware import validate_candidate

WORKER_STATE, EVENT = 0xA18BCDC8, 0xA2390144


class PowerCut(Exception):
    pass


class NativeValueGrid(SettingsFixture):
    def __init__(self, image, journal=None, failure=None):
        super().__init__(image, journal=journal, failure=failure)
        self.u.mem_map(0xA1910000, 0x6F0000)  # Remaining native scalar BSS, zero supplied.
        self.labels, self.rows, self.marks, self.setters = [], [], [], []
        self.events, self.secondary = [], []
        self.worker, self.waits, self.worker_finished = False, 0, False
        self.program_count, self.cut_after = 0, None
        self.viewport = (0, 0, 720, 480)
        self.viewport_type, self.geometry_notifications = 1, []
        for address in (0x104065B0, 0x103FBB5C, 0x103FCF0E, 0x103FB344,
                        0x10405F00, 0x10402BC2, 0x10404CD8, 0x10437190,
                        0x10377010, 0x103EA09E, 0x101F447A, 0x10170BEE, 0x103EA7B6):
            self.u.hook_add(UC_HOOK_CODE, self.extra_hook, begin=address, end=address)
        self.u.hook_add(UC_HOOK_CODE, self.secondary_save, begin=0x101AEA60, end=0x101AEA60)

    def hook(self, u, address, size, context):
        r0, r1, r2 = (u.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2))
        if address == 0x10170BE8 and r0 == EVENT:
            self.events.append(r1)
            self.ret(0)
        elif address == 0x10170BF6 and r0 == EVENT and self.worker:
            self.waits += 1
            if self.waits == 1:
                if not self.events or r1 != 0x1733:
                    raise AssertionError('Unexpected settings-worker event wait')
                u.mem_write(r2, struct.pack('<I', self.events.pop(0)))
                self.ret(1)
            else:
                self.worker_finished = True
                u.emu_stop()
        else:
            super().hook(u, address, size, context)
            if address == 0x101AE3F0:
                self.program_count += 1
                if self.cut_after == self.program_count:
                    raise PowerCut('Cut after supplied whole-program boundary')

    def secondary_save(self, u, address, size, context):
        record = u.reg_read(UC_ARM_REG_R0)
        if record not in (0x10, 0xD, 0xE, 7):
            raise AssertionError('Unexpected secondary dataset save')
        self.secondary.append(record)
        self.ret(1)

    def extra_hook(self, u, address, size, context):
        r0, r1, r2 = (u.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2))
        if address == 0x104065B0:
            if r0 != 0x102D or r1 not in range(6):
                raise AssertionError('Unexpected UI bridge input')
            self.setters.append(r1)
            # Supply UI service dispatch, then run the real native raw setter.
            u.reg_write(UC_ARM_REG_R2, MEM + 0x800)
            u.reg_write(UC_ARM_REG_PC, 0x100704FB)
        elif address == 0x103FBB5C:
            text = bytes(u.mem_read(r0, 32)).split(b'\0')[0].decode('ascii')
            self.labels.append((r1, text))
            self.ret(0)
        elif address == 0x103FCF0E:
            self.ret(MEM + 0x10000 + r2 * 64)
        elif address == 0x103FB344:
            self.rows.append(r1)
            self.ret(0)
        elif address in (0x10402BC2, 0x10404CD8):
            if address == 0x10404CD8:
                self.marks.append((r1, r2))
            self.ret(0)
        elif address == 0x10405F00:
            self.ret(0)
        elif address == 0x10437190:
            for offset in (8, 0x14):
                u.mem_write(r0 + offset, struct.pack('<4h', *self.viewport))
            u.mem_write(r0 + 0x28, bytes([self.viewport_type]))
            self.ret(0)
        elif address == 0x103EA7B6:
            if (r0, r1) != (0x33, 0):
                raise AssertionError('Unexpected grid geometry notification')
            self.geometry_notifications.append(bytes(u.mem_read(DESCRIPTOR, 32)))
            self.ret(0)
        elif address == 0x10377010:
            self.ret(1)
        elif address == 0x103EA09E:
            if r0 not in (0x2B, 0x6E):
                raise AssertionError('Unexpected native visibility gate')
            self.ret(0)
        elif address == 0x101F447A:
            if r0 not in (0x11, 0x28):
                raise AssertionError('Unexpected startup secondary read')
            self.ret(0)
        elif address == 0x10170BEE:
            if r0 != EVENT:
                raise AssertionError('Unexpected worker clear')
            self.ret(0)

    def initialize(self):
        self.call(0x10091CAC)
        self.call(0x100709CA)

    def set_raw(self, value):
        return self.call(0x100704FA, 0x102D, value, MEM + 0x800)

    def scalar(self, key, destination):
        # Every indexed scalar read is a short bounded leaf path. Avoid a host
        # timer thread per emu_start on Windows while retaining instruction,
        # return-PC, stack and all callee-saved register checks.
        u = self.u
        for reg, value in zip(ARGUMENTS, (key, destination, 0, 0)):
            u.reg_write(reg, value)
        guards = {reg: 0x51510000 + i for i, reg in enumerate(SAVED)}
        for reg, value in guards.items():
            u.reg_write(reg, value)
        u.reg_write(UC_ARM_REG_SP, STACK)
        u.reg_write(UC_ARM_REG_LR, STOP | 1)
        u.emu_start(0x10070235, STOP, count=2000)
        if (u.reg_read(UC_ARM_REG_PC) != STOP or u.reg_read(UC_ARM_REG_SP) != STACK
                or any(u.reg_read(reg) != value for reg, value in guards.items())):
            raise AssertionError('Indexed scalar read exceeded its instruction/ABI contract')
        self.scalar_flags = u.reg_read(UC_ARM_REG_CPSR) & 0xF8000000
        return u.reg_read(UC_ARM_REG_R0)

    def payloads(self):
        return [bytes(self.u.mem_read(self.word(SCHEMA + i * 12), self.word(SCHEMA + i * 12 + 4)))
                for i in range(89)]

    def save_worker(self, enabled=True):
        if not enabled:
            self.call(0x10117642)
        self.u.mem_write(WORKER_STATE + 4, struct.pack('<I', 0x10117851))
        self.u.mem_write(WORKER_STATE + 12, struct.pack('<I', 1))
        self.call(0x10117860)
        self.worker = True
        self.u.reg_write(UC_ARM_REG_SP, STACK)
        self.u.emu_start(0x1011774D, STOP, timeout=10000000, count=10000000)
        if not self.worker_finished:
            raise AssertionError('Native settings worker failed to complete one event')


def audit(stock, image, report):
    checks = []
    def check(name, condition):
        checks.append(dict(name=name, passed=bool(condition)))
    funcs = {k: int(v, 16) for k, v in report['features']['grid']['functions'].items()}
    expanded = report['preset'] == 'grid-layouts-emulator-only'
    layouts = report['features']['grid'].get('layouts', [
        dict(function='fourths', stored_value=1, control_id=0x1901, label='4x4 grid'),
        dict(function='thirds', stored_value=2, control_id=0x7A30, label='3x3 grid'),
        dict(function='off', stored_value=0, control_id=0x1902, label='Off')])
    normalized = (2, 3, 4, 5) if expanded else (2,)
    stored_cases = (0, 1, 2, 3, 4, 5, 6, 0xFFFFFFFF) if expanded else (0, 1, 2, 3, 0xFFFFFFFF)
    check('no-custom-workspace-or-journal-feature', report['features']['grid']['state_bytes'] == 0
          and 'settings' not in report['features'])
    for address, size in ((0x101E3DA0, 12), (0x10070A16, 14), (0x101AEBAE, 12),
                          (0x101AEC44, 12), (0x100709CA, 10)):
        off = address - 0x10020000
        check('stock-heap-or-journal-entry-' + hex(address), image[off:off+size] == stock[off:off+size])
    a, b = NativeValueGrid(image), NativeValueGrid(stock)
    a.initialize(); b.initialize()
    keys = []
    for group in range(72):
        address = 0x114D8D9C + group * 28
        if b.word(address):
            _, count = struct.unpack('<HH', b.u.mem_read(address + 12, 4))
            if count > 256:
                raise AssertionError('Unexpected native scalar group bound')
            keys.extend((group << 8) | low for low in range(count))
    keys += [0xFFFF, 0x4800]
    for stored in stored_cases:
        a.set_raw(stored); b.set_raw(stored)
        same, flags_same = True, True
        for key in keys:
            ar, br = a.scalar(key, MEM), b.scalar(key, MEM)
            av, bv = a.word(MEM), b.word(MEM)
            same &= ar == br and av == (1 if key == 0x102D and stored in normalized else bv)
            flags_same &= a.scalar_flags == b.scalar_flags
        check('native-getter-differential-stored-' + str(stored), same)
        check('native-getter-preserves-original-nzcvq-' + str(stored), flags_same)
        check('getter-never-modifies-stored-scalar-' + str(stored), a.word(GRID_VALUE) == stored)
        check('full-native-UI-get-chain-stored-' + str(stored),
              a.call(0x104065A4, 0x102D) == (1 if stored in normalized else stored))
        check('native-visibility-predicate-stored-' + str(stored),
              a.call(0x1037723E) == int(stored in (1, *normalized)))
    b.set_raw(2)
    check('stock-visibility-treats-new-value-as-off', b.call(0x1037723E) == 0)
    b.u.mem_write(0xA1836F8C + 36, struct.pack('<I', MEM + 0x10000))
    b.call(0x104EFA6A, 0xA1836F8C)
    check('stock-grid-menu-treats-new-value-as-off', b.marks == [(0x1902, 1)])
    del b
    gc.collect()
    for layout in layouts[:-1]:
        name, stored, control = (layout[k] for k in ('function', 'stored_value', 'control_id'))
        a.call(funcs[name])
        check('compiled-choice-stores-native-value-' + name, a.word(GRID_VALUE) == stored)
        a.labels.clear(); a.rows.clear(); a.marks.clear()
        a.u.mem_write(0xA1836F8C + 36, struct.pack('<I', MEM + 0x10000))
        a.call(funcs['enter'], 0xA1836F8C)
        check('compiled-menu-current-marker-' + name, a.marks == [(control, 1)]
              and a.labels == [(39 + i, layout['label']) for i, layout in enumerate(layouts)]
              and a.rows == list(range(39, 39 + len(layouts))))
    check('UI-selection-does-not-program-flash', not a.operations)
    a.call(funcs['thirds'])
    a.u.mem_write(0xA20A6D48, bytes([0x5A]) * 0x384)
    a.call(0x100B9E6C, 0xA20A6D48, 0x102D, 2)
    check('native-packed-snapshot-can-store-third-value-in-one-byte',
          bytes(a.u.mem_read(0xA20A6D48, 0x384))
          == bytes([0x5A]) * 0x29C + b'\2' + bytes([0x5A]) * (0x384 - 0x29D))
    if expanded:
        for stored in (0, 1, 3, 4, 5):
            a.u.mem_write(0xA20A6D48, bytes([0x5A]) * 0x384)
            a.call(0x100B9E6C, 0xA20A6D48, 0x102D, stored)
            check(f'packed-snapshot-stores-only-layout-byte-{stored}',
                  bytes(a.u.mem_read(0xA20A6D48, 0x384)) == bytes([0x5A]) * 0x29C
                  + bytes([stored]) + bytes([0x5A]) * (0x384 - 0x29D))
    before = a.payloads()
    a.save_worker()
    check('native-event-request-and-worker-save-main', a.worker_finished
          and a.word(WORKER_STATE + 12) == 0 and a.operations
          and a.secondary == [0x10, 0xD, 0xE, 7])
    saved = a.journal()
    del a
    gc.collect()
    for choice, stored in [('fourths', 1), ('off', 0)] + (
            [(layout['function'], layout['stored_value']) for layout in layouts[2:-1]] if expanded else []):
        a = NativeValueGrid(image, saved)
        a.initialize(); a.call(0x10117594)
        a.call(0x104F5592 if choice == 'off' else funcs[choice])
        a.save_worker()
        changed = a.journal()
        total_programs = a.program_count
        del a
        gc.collect()
        a = NativeValueGrid(image, changed)
        a.initialize(); a.call(0x10117594)
        check(choice + '-also-persists-in-fresh-native-startup', a.word(GRID_VALUE) == stored)
        check(choice + '-preserves-all-unrelated-native-records',
              all(payload == before[i] for i, payload in enumerate(a.payloads()) if i != 49))
        if expanded and stored > 2:
            check(choice + '-fresh-native-visibility-on', a.call(0x1037723E) == 1)
            a.u.mem_write(0xA1836F8C + 36, struct.pack('<I', MEM + 0x10000))
            a.call(funcs['enter'], 0xA1836F8C)
            check(choice + '-fresh-native-layout-menu',
                  a.marks == [(next(layout['control_id'] for layout in layouts
                                   if layout['stored_value'] == stored), 1)])
        del a
        gc.collect()
        if expanded and stored > 2:
            a = NativeValueGrid(stock, changed)
            a.initialize(); a.call(0x10117594)
            check(choice + '-stock-loads-scalar-without-writing',
                  a.word(GRID_VALUE) == stored and not a.operations
                  and a.word(WORKER_STATE) == 1 and a.call(0x1037723E) == 0)
            a.u.mem_write(0xA1836F8C + 36, struct.pack('<I', MEM + 0x10000))
            a.call(0x104EFA6A, 0xA1836F8C)
            check(choice + '-stock-menu-treats-as-off', a.marks == [(0x1902, 1)])
            del a
            gc.collect()
    for cut in sorted({1, total_programs}):
        a = NativeValueGrid(image, saved)
        a.initialize(); a.call(0x10117594); a.call(funcs['fourths'])
        a.cut_after = cut
        interrupted = False
        try:
            a.save_worker()
        except PowerCut:
            interrupted = True
        interrupted_banks = a.journal()
        check(f'program-cut-{cut}-is-reached', interrupted)
        del a
        gc.collect()
        a = NativeValueGrid(image, interrupted_banks)
        a.initialize(); a.call(0x10117594)
        check(f'program-cut-{cut}-loads-valid-old-or-new-grid', a.word(WORKER_STATE) == 1
              and a.word(GRID_VALUE) in (1, 2))
        check(f'program-cut-{cut}-preserves-unrelated-records',
              all(payload == before[i] for i, payload in enumerate(a.payloads()) if i != 49))
        del a
        gc.collect()
    a = NativeValueGrid(image, saved, failure='program')
    a.initialize(); a.call(0x10117594); a.call(funcs['fourths']); a.save_worker()
    failed = a.journal()
    del a
    gc.collect()
    a = NativeValueGrid(image, failed)
    a.initialize(); a.call(0x10117594)
    check('supplied-program-failure-preserves-previous-valid-store',
          a.word(WORKER_STATE) == 1 and a.word(GRID_VALUE) == 2 and a.payloads() == before)
    del a
    gc.collect()
    # New CPU/RAM instances carry only the two stored flash-bank byte strings.
    for raw in (image, stock):
        a = NativeValueGrid(raw, saved)
        a.initialize()
        a.call(0x10117594)
        label = 'patched' if raw is image else 'stock'
        check(label + '-fresh-native-startup-loads-original-schema-and-value',
              a.word(GRID_VALUE) == 2 and a.word(WORKER_STATE) == 1)
        check(label + '-fresh-native-startup-preserves-all-89-records', a.payloads() == before)
        check(label + '-fresh-startup-does-not-write', not a.operations)
        if raw is image:
            check('fresh-patched-native-visibility-on', a.call(0x1037723E) == 1)
        else:
            check('fresh-stock-native-visibility-off', a.call(0x1037723E) == 0)
        del a
        gc.collect()
    a = NativeValueGrid(image, saved)
    a.initialize(); a.call(0x10117594)
    a.call(0x104F5592)
    check('native-off-stores-zero-and-hides', a.word(GRID_VALUE) == 0 and a.call(0x1037723E) == 0)
    a.call(funcs['thirds']); a.call(0x100709CA)
    check('native-default-reset-restores-grid-off', a.word(GRID_VALUE) == 0)
    a.call(funcs['thirds']); a.save_worker(enabled=False)
    check('native-save-disable-policy-is-preserved', not a.operations and a.word(WORKER_STATE + 12) == 0)
    del a
    gc.collect()
    geometry_calls = 0
    for viewport in ((0, 0, 720, 480), (20, 40, 700, 440), (0, 0, 640, 426)):
        ref = GridFixture(stock, viewport, 0)
        a = NativeValueGrid(image); a.initialize(); a.viewport = viewport
        for mode in range(3):
            for crop in ((0, 1, 2, 4, 8) if expanded else (0,)):
                ref.crop = crop
                a.call(0x100704FA, 0x402, crop, MEM + 0x800)
                for stored in stored_cases:
                    a.set_raw(stored)
                    a.call(0x10376DA0, mode)
                    actual = struct.unpack('<hhIHHhhIHHHHBBH', a.u.mem_read(DESCRIPTOR, 32))
                    count = {2: 2, 3: 2, 4: 1, 5: 5}.get(stored, 3) if expanded else (2 if stored == 2 else 3)
                    expected = ref.geometry(mode, count)
                    geometry_calls += 2
                    same = actual == expected
                    if expanded and stored == 3:
                        # Independent geometric oracle: exact phi fractions,
                        # allowing <1px Q16 rounding, while preserving Nikon's
                        # crop offsets, line extents, counts and styling.
                        same = all(actual[i] == expected[i] for i in (0, 2, 4, 6, 7, 9, 10, 11, 12, 13, 14))
                        for origin, interval, span in ((1, 3, 7), (5, 8, 2)):
                            base = expected[origin] - expected[interval]
                            first = actual[origin] - base
                            exact = expected[span] * ((3 - 5 ** .5) / 2)
                            same &= abs(first - exact) < 1
                            same &= 2 * first + actual[interval] == expected[span]
                    check(f'geometry-{viewport}-{mode}-crop{crop}-{stored}', same)
        if expanded:
            # Exercise the other displaced native tail branch. The original
            # event must see the finished golden descriptor, not the temporary
            # thirds geometry that was used to compute Nikon's crop offsets.
            for stored in range(6):
                a.set_raw(stored)
                a.viewport_type = 1
                a.call(0x10376DA0, 0)
                expected = bytes(a.u.mem_read(DESCRIPTOR, 32))
                a.viewport_type = 0
                a.call(0x10376DA0, 0)
                geometry_calls += 2
                check(f'viewport-notification-{viewport}-{stored}',
                      a.geometry_notifications[-1] == expected
                      and bytes(a.u.mem_read(DESCRIPTOR, 32)) == expected)
        del a, ref
        gc.collect()
    return dict(schema=1, scope=__doc__.strip(), main_payload_sha256=report['main_payload_sha256'],
                checks=checks, geometry_calls=geometry_calls, scalar_differential_calls=len(keys)*len(stored_cases)*2,
                indexed_native_property_keys=len(keys)-2,
                all_passed=all(c['passed'] for c in checks), native_records=89,
                custom_journal_hooks=False, supplied_boundaries=['OS locks/events', 'in-memory flash erase/program',
                    'secondary datasets during worker/startup', 'UI bridge to original raw setter and widgets',
                    'viewport and visibility gates'], camera_access=False, card_access=False,
                full_camera_shutdown=False, physical_durability=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--stock', type=Path, required=True)
    p.add_argument('--container', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    binary, report_path = [args.build / ('grid.emulator.' + ext) for ext in ('main.bin', 'json')]
    validate_candidate(binary, report_path, args.container)
    report = json.loads(report_path.read_text())
    if report['preset'] not in ('grid-native-value-emulator-only', 'grid-layouts-emulator-only'):
        p.error('Requires native-value experiment')
    result = audit(args.stock.read_bytes(), binary.read_bytes(), report)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(checks=len(result['checks']), all_passed=result['all_passed'])))
    if not result['all_passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
