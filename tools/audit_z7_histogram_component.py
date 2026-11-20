"""Compiled original-Z7 histogram pass, native layout and cleanup contracts.

SPDX-License-Identifier: MIT. Native mask/layout/updater/visibility instructions
execute. One positive chain also executes the original histogram painter/scale
getter through supplied low-level rectangle services. Incoming GUI state, sample
producer, render submit and present services are supplied; failure injection uses
supplied painter returns. An unavailable-event case executes the real getter/
driver/zeroing chain. No successful hardware statistics or actual pixels proven.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_PC
from audit_z7_display_base import BaseFixture
from audit_z7_module_host import HostFixture
from audit_z7_histogram_getter import DRIVER, REQUEST, EVENT, MUTEX
from build_z7_module_host import ROOT, STATE

DESC, CONTROL, SNAPSHOT, PREVIOUS = 0xa1827404, 0xa18273d4, 0xa201d4d0, 0xa201d80c
OBJECT, BINS, CONTEXT = 0xa2c44000, 0xa201df88, 0xa201d308
MASKS = struct.pack('<9I', *([0x444] * 6 + [0x440] * 3))


class HistogramFixture(BaseFixture):
    active_histogram = False

    def __init__(self, *args):
        super().__init__(*args)
        self.u.mem_map(0xa2330000, 0x10000)
        self.samples = [1 + (i % 16) * 10 for i in range(256)]
        self.sample_kind = 'valid'
        self.pending, self.menu, self.blocked, self.exclude = 0, 0, 0, 0
        self.now = 1000
        self.ready = (0, 0)
        self.native_waits = self.gets = self.submits = self.presents = self.native_paints = 0
        self.layout_entries = []
        self.submit_mode = 'paint'
        self.change_after_sample = None
        self.module_base = 0
        self.execute_native_painter = False
        self.rectangles = []
        self.painter_entry = self.painter_return = 0
        self.inside_painter = False

    def read(self, address):
        return int.from_bytes(self.u.mem_read(address, 4), 'little')

    def write(self, address, value):
        self.u.mem_write(address, struct.pack('<I', value))

    def hook(self, u, address, size, context):
        if self.active_histogram:
            if address == self.painter_return: self.inside_painter = False
            if address == self.painter_entry:
                from unicorn.arm_const import UC_ARM_REG_LR
                self.inside_painter = True; self.painter_return = u.reg_read(UC_ARM_REG_LR) & ~1
            if self.inside_painter and address in (0x104065a4, 0x104065b0, 0x103673ac, 0x103fa770, 0x103ecf90):
                raise AssertionError('Painter re-entered property or display-wait service')
            if address in (0x10369248, 0x10369214, 0x102f27a8, 0x102f2ada, 0x102f5540):
                self.layout_entries.append((address, u.reg_read(UC_ARM_REG_R0)))
                HostFixture.hook(self, u, address, size, context)
                return  # Bypass readout fixture's supplied layout/dispatch.
            if address == 0x10437190:
                u.mem_write(u.reg_read(UC_ARM_REG_R0), bytes(0x420))
                u.mem_write(u.reg_read(UC_ARM_REG_R0) + 0x28, bytes(self.ready))
                self.ret(0); return
            if address in (0x103fa770, 0x103ecf90, 0x10301e12, 0x10401d22, 0x103709aa, 0x103ebb42):
                self.ret({0x103fa770: self.pending, 0x10301e12: self.menu,
                          0x10401d22: self.blocked}.get(address, 0)); return
            if address == 0x103ea09e:
                if self.execute_native_painter and u.reg_read(UC_ARM_REG_R0) == 3:
                    HostFixture.hook(self, u, address, size, context); return
                self.ret(self.exclude if u.reg_read(UC_ARM_REG_R0) == 12 else 0); return
            if self.execute_native_painter and address == 0x103fa470:
                self.rectangles.append((struct.unpack('<4h', u.mem_read(u.reg_read(UC_ARM_REG_R0), 8)), u.reg_read(UC_ARM_REG_R1)))
                self.ret(1); return
            if self.execute_native_painter and address == 0x103fcb46:
                self.ret(1); return
            if address == 0x103ffa2c:
                self.ret(self.now); return
            if address == 0x104070ac:
                self.gets += 1
                destination = u.reg_read(UC_ARM_REG_R0)
                if destination % 64 or bytes(u.mem_read(destination, 1024)) != bytes(1024):
                    raise AssertionError('Samples must be aligned and cleared before every getter')
                if self.sample_kind != 'native-unavailable':
                    if self.sample_kind == 'valid':
                        u.mem_write(destination, struct.pack('<256I', *self.samples))
                    if self.change_after_sample:
                        self.change_after_sample()
                    self.ret(int(self.sample_kind != 'failed')); return
            if address in (0x10170bee, 0x10170c32, 0x10170944, 0x1017093e):
                key = u.reg_read(UC_ARM_REG_R0)
                if address in (0x10170944, 0x1017093e):
                    if key != MUTEX: raise AssertionError('Histogram mutex identity')
                    self.ret(1)
                elif address == 0x10170bee:
                    if (key, u.reg_read(UC_ARM_REG_R1)) != (EVENT, 1): raise AssertionError('Event clear')
                    self.ret(0)
                else:
                    args = tuple(u.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3))
                    if args != (EVENT, 1, 0, 100): raise AssertionError('Native unavailable wait')
                    self.native_waits += 1; self.ret(0)
                return
            if address in (0x100a51d8, 0x100efac4):
                raise AssertionError('Unavailable event must not reach a producer')
            if address == 0x102f2042:
                self.submits += 1
                if bytes(u.mem_read(DESC + 4, 36)) != MASKS:
                    raise AssertionError('Temporary masks leaked into submit')
                if self.submit_mode == 'fail': self.ret(0)
                elif self.submit_mode == 'no-paint': self.ret(1)
                else:
                    # Supplied synchronous renderer consumes the installed
                    # module callback. Its native painter call is a boundary.
                    u.reg_write(UC_ARM_REG_R0, OBJECT)
                    if self.submit_mode == 'output-before-paint': self.write(0xa1821370 + 0x24, 4)
                    for reg in (UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3): u.reg_write(reg, 0)
                    u.reg_write(UC_ARM_REG_PC, self.read(OBJECT + 0x4c))
                return
            if address == 0x102f1544:
                self.native_paints += 1
                if self.execute_native_painter:
                    HostFixture.hook(self, u, address, size, context); return
                if self.submit_mode == 'replace-object': self.write(CONTROL + 36, OBJECT + 512)
                if self.submit_mode == 'change-page': u.mem_write(SNAPSHOT + 0x18a, b'\1')
                if self.submit_mode == 'change-output': self.write(0xa1821370 + 0x24, 4)
                self.ret(1); return
            if address == 0x102f11b6:
                self.presents += 1; self.ret(0); return
        super().hook(u, address, size, context)


def audit(raw, host, packet, module, legacy):
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Fingerprint mismatch')
    checks = []
    def check(name, value):
        checks.append(dict(name=name, passed=bool(value)))
        if not value: raise AssertionError(name)
    f = HistogramFixture(raw, host, packet)
    check('module-loads', f.call(host['symbols']['z7_module_load_once'], STATE) == 8)
    base, symbols = f.words()[12], module['symbols']
    f.painter_entry = (base + symbols['histogram_painter']) & ~1
    model = base + symbols['z7_menu_settings']
    def word(name): return f.read(base + symbols['z7_histogram_' + name])
    def component(bit, value): f.call(base + symbols['z7_settings_component'], model, 0, bit, value)
    check('stock-histogram-masks-retained-at-init', bytes(f.u.mem_read(DESC + 4, 36)) == MASKS)
    check('after-gui-registered', f.words()[41] == 1 and f.words()[40] == base + symbols['histogram_after_gui'])
    f.call(base + symbols['z7_settings_flag'], model, 0, 1)
    component(1, 1); component(2, 0)
    f.call(host['symbols']['z7_display_before_update'])
    f.properties[0x102c] = 1
    f.active_histogram = True
    def reset(page=0):
        f.display = 1; f.properties[0x138d] = 0; f.properties[0x2f15] = page; f.properties[0x102c] = 1
        f.u.mem_write(SNAPSHOT, bytes(0x33c)); f.u.mem_write(SNAPSHOT + 0x18a, bytes([page]))
        f.u.mem_write(PREVIOUS + 0x18a, bytes([page]))
        f.write(base + symbols['z7_base_applied'], page)
        f.u.mem_write(0xa201f698 + 0x1f, b'\0')
        # App object word0 is a message callback, not an inactive-context byte.
        f.write(0xa1829af8, 0x1030d511)
        f.write(0xa1829b0c, 0x1030da57); f.write(0xa1829b10, 0x1030dd1f)
        f.u.mem_write(0xa18237c6, b'\0'); f.write(0xa2c41008, 0)
        f.write(0xa1821370 + 0x30, 0); f.write(0xa1821370 + 0x34, 0)
        f.write(0xa1821370 + 0x24, 1)
        f.u.mem_write(DESC + 4, MASKS); f.write(DESC + 44, CONTROL)
        f.u.mem_write(CONTROL, bytes(3)); f.write(CONTROL + 36, OBJECT)
        f.u.mem_write(OBJECT, bytes(284)); f.write(OBJECT + 4, 4)
        f.write(OBJECT + 0x48, 0xa201e3b4); f.write(OBJECT + 0x4c, 0x10433913)
        f.u.mem_write(BINS, b'\xa5' * 1024); f.write(CONTEXT + 0x34, 0x12345678)
        f.u.mem_write(CONTEXT + 0x10, b'\0')
        f.sample_kind = 'valid'; f.submit_mode = 'paint'; f.change_after_sample = None
        f.pending = f.menu = f.blocked = f.exclude = 0; f.ready = (0, 0)
        f.layout_entries.clear()
    def update(): return f.call(base + symbols['histogram_update'])
    for page in (0, 3):
        reset(page)
        previous = f.presents
        result = update()
        check(f'page-{page}-supplied-samples-native-layout-draws', result == 15 and f.presents == previous + 1)
        check(f'page-{page}-all-native-masks-restored', bytes(f.u.mem_read(DESC + 4, 36)) == MASKS)
        check(f'page-{page}-native-updater-installed-and-retired-module-painter',
              any(address == 0x102f5540 for address, _ in f.layout_entries) and
              f.read(OBJECT + 0x4c) == 0x10433913 and f.read(OBJECT + 0x28) == 1)
        check(f'page-{page}-sample-copy-and-normalization', bytes(f.u.mem_read(BINS, 1024)) == struct.pack('<256I', *f.samples) and f.read(CONTEXT + 0x34) == max(f.samples))
    for name, samples in [('one', [1] + [0] * 255), ('uniform', [7] * 256),
                          ('outlier', [1] * 255 + [1000]), ('maximum', [0xffffffff] + [0] * 255),
                          ('maximum-total', [0xffffffff - 255] + [1] * 255)]:
        reset(); f.samples = samples
        f.write(BINS - 4, 0x12344321); f.write(BINS + 1024, 0x43211234)
        check(name + '-normalization-success', update() == 15)
        expected = min(max(samples), 4 * (sum(samples) // sum(v != 0 for v in samples)))
        check(name + '-integer-normalization-without-overflow', f.read(CONTEXT + 0x34) == expected)
        check(name + '-bin-copy-exact-and-bounded', bytes(f.u.mem_read(BINS, 1024)) == struct.pack('<256I', *samples) and
              f.read(BINS - 4) == 0x12344321 and f.read(BINS + 1024) == 0x43211234)
    f.samples = [1 + (i % 16) * 10 for i in range(256)]
    reset(); f.execute_native_painter = True
    check('compiled-pass-through-original-layout-painter-and-scale-getter', update() == 15)
    check('original-painter-emits-visible-bin-primitives', any(palette == 1 for _, palette in f.rectangles))
    check('original-painter-chain-restores-masks-and-optional-callback', bytes(f.u.mem_read(DESC + 4, 36)) == MASKS and f.read(OBJECT + 0x4c) == 0x10433913)
    f.execute_native_painter = False
    for name, mutate, expected in [
        ('component-off', lambda: component(1, 0), 0),
        ('previous-page', lambda: f.u.mem_write(PREVIOUS + 0x18a, b'\3'), 1),
        ('movie', lambda: f.u.mem_write(SNAPSHOT + 0x40, b'\1'), 0),
        ('menu', lambda: setattr(f, 'menu', 1), 2),
        ('update-blocked', lambda: setattr(f, 'blocked', 1), 2),
        ('widget-excluded', lambda: setattr(f, 'exclude', 1), 2),
        ('inactive-output', lambda: f.write(0xa1821370 + 0x24, 0), 2),
        ('evf-active', lambda: f.write(0xa1821370 + 0x24, 4), 2),
        ('mixed-outputs', lambda: f.write(0xa1821370 + 0x24, 3), 2),
        ('foreign-key-callback', lambda: f.write(0xa1829b0c, 0), 2),
        ('foreign-event-callback', lambda: f.write(0xa1829b10, 0), 2),
        ('pending-event', lambda: setattr(f, 'pending', 1), 3),
        ('render-busy', lambda: f.write(0xa1821370 + 0x34, 1), 3),
        ('foreign-masks', lambda: f.write(DESC + 4, 0), 4),
        ('foreign-control', lambda: f.write(DESC + 44, CONTROL + 48), 4),
        ('foreign-canvas', lambda: f.write(OBJECT + 0x48, 0), 4),
        ('dirty-control', lambda: f.u.mem_write(CONTROL, b'\1'), 5),
        ('visible-control', lambda: f.u.mem_write(CONTROL + 1, b'\1'), 5),
        ('foreign-painter', lambda: f.write(OBJECT + 0x4c, 0x10384969), 13),
        ('photo-ineligible', lambda: f.properties.update({0x102c: 0}), 6),
        ('readiness-28', lambda: setattr(f, 'ready', (1, 0)), 7),
        ('readiness-29', lambda: setattr(f, 'ready', (0, 1)), 7),
        ('getter-failed', lambda: setattr(f, 'sample_kind', 'failed'), 8),
        ('getter-empty', lambda: setattr(f, 'sample_kind', 'empty'), 9),
        ('total-overflow', lambda: setattr(f, 'samples', [0xffffffff] * 256), 10),
        ('page-changed-during-sampling', lambda: setattr(f, 'change_after_sample', lambda: f.u.mem_write(SNAPSHOT + 0x18a, b'\1')), 11),
        ('slot-changed-during-sampling', lambda: setattr(f, 'change_after_sample', lambda: f.write(CONTROL + 36, OBJECT + 512)), 11),
        ('output-changed-during-sampling', lambda: setattr(f, 'change_after_sample', lambda: f.write(0xa1821370 + 0x24, 4)), 11),
    ]:
        reset(); component(1, 1); f.samples = [1 + (i % 16) * 10 for i in range(256)]
        before_gets, before_submits, before_presents = f.gets, f.submits, f.presents
        mutate(); native_before = bytes(f.u.mem_read(BINS, 1024)); masks_before = bytes(f.u.mem_read(DESC + 4, 36))
        check(name + '-result', update() == expected)
        check(name + '-no-native-sample-or-mask-stores', bytes(f.u.mem_read(BINS, 1024)) == native_before and bytes(f.u.mem_read(DESC + 4, 36)) == masks_before and f.read(CONTEXT + 0x34) == 0x12345678)
        check(name + '-no-submit-or-present', f.submits == before_submits and f.presents == before_presents)
        if expected < 8 or expected == 13: check(name + '-does-not-sample', f.gets == before_gets)
    for mode in ('fail', 'no-paint', 'change-page', 'replace-object', 'change-output', 'output-before-paint'):
        reset(); f.submit_mode = mode; before = f.presents; paints_before = f.native_paints
        result = update()
        check(mode + '-submit-failure-or-change-not-presented', result == (11 if mode == 'replace-object' else 14) and f.presents == before)
        check(mode + '-module-painter-always-restored', f.read(OBJECT + 0x4c) == 0x10433913 and bytes(f.u.mem_read(DESC + 4, 36)) == MASKS)
        if mode != 'replace-object':
            check(mode + '-context-cleared-and-widget-hidden', f.u.mem_read(CONTEXT + 0x10, 1) == b'\0' and f.u.mem_read(CONTROL + 1, 1) == b'\0' and not f.read(OBJECT + 0x28))
        if mode in ('change-output', 'output-before-paint'):
            check(mode + '-no-placement-on-replacement-output', sum(address == 0x102f27a8 for address, _ in f.layout_entries) == 1)
        if mode == 'output-before-paint':
            check(mode + '-ram-guard-skips-native-painter', f.native_paints == paints_before)
    for retirement in ('component-off', 'master-off', 'foreign-painter', 'replacement-object'):
        reset(); component(1, 1)
        f.call(base + symbols['z7_settings_flag'], model, 0, 1)
        f.call(host['symbols']['z7_display_before_update']); reset()
        check(retirement + '-starts-from-drawn-owned-widget', update() == 15)
        component(1, 0)
        if retirement == 'master-off': f.call(base + symbols['z7_settings_flag'], model, 0, 0)
        if retirement == 'foreign-painter': f.write(OBJECT + 0x4c, 0x10384969)
        if retirement == 'replacement-object': f.write(CONTROL + 36, OBJECT + 512)
        f.call(host['symbols']['z7_display_before_update'])
        if retirement in ('component-off', 'master-off'):
            check(retirement + '-retires-through-native-hide-dirty-and-invalidation', not f.read(OBJECT + 0x28) and
                  f.read(OBJECT + 0x44) == 1 and not f.u.mem_read(CONTROL + 1, 1)[0])
        else:
            check(retirement + '-does-not-overwrite-foreign-object', f.read(OBJECT + 0x28) == 1 and
                  f.read(OBJECT + 0x4c) == (0x10384969 if retirement == 'foreign-painter' else 0x10433913))
    f.call(base + symbols['z7_settings_flag'], model, 0, 1); component(1, 1)
    f.call(host['symbols']['z7_display_before_update'])
    reset(); f.sample_kind = 'native-unavailable'; f.u.mem_write(DRIVER, b'\1\2\2'); f.u.mem_write(REQUEST, bytes(24))
    check('original-unavailable-event-fails-closed', update() == 8 and f.native_waits == 1)
    check('unavailable-event-keeps-native-bins-and-scale', bytes(f.u.mem_read(BINS, 1024)) == b'\xa5' * 1024 and f.read(CONTEXT + 0x34) == 0x12345678)
    reset(); f.sample_kind = 'failed'; before = f.gets
    f.call(host['symbols']['z7_display_after_gui_update']); f.now += 99
    f.call(host['symbols']['z7_display_after_gui_update'])
    check('cadence-skips-before-100-native-units', f.gets == before + 1)
    f.now += 1; f.call(host['symbols']['z7_display_after_gui_update'])
    check('failed-attempt-retries-at-completion-plus-100-native-units', f.gets == before + 2 and word('last_end') == f.now)
    f.now += 100; f.change_after_sample = lambda: setattr(f, 'now', f.now + 500)
    f.call(host['symbols']['z7_display_after_gui_update'])
    check('slow-failure-cadence-stamped-from-completion', word('last_end') == f.now)
    before = f.gets; f.change_after_sample = None; f.now += 99
    f.call(host['symbols']['z7_display_after_gui_update'])
    check('slow-failure-does-not-trigger-immediate-retry', f.gets == before)
    old_host = json.loads((legacy / 'module-host.emulator.json').read_text())
    old = HistogramFixture((legacy / 'module-host.emulator.main.bin').read_bytes(), old_host, packet)
    original_masks = bytes(old.u.mem_read(DESC + 4, 36))
    check('older-api28-rejected-before-native-mask-or-property-stores', old.call(old_host['symbols']['z7_module_load_once'], STATE) == 7 and not old.live and not old.property_writes and bytes(old.u.mem_read(DESC + 4, 36)) == original_masks)
    return dict(passed=True, checks=checks, main_sha256=host['main_payload_sha256'], module_sha256=module['module_sha256'],
        native_layout_and_updater_execute=True, native_unavailable_event_chain_executes=True,
        native_histogram_painter_and_scale_getter_execute=True,
        painter_property_or_display_wait_reentry=False,
        supplied_boundaries=['Loader/kernel/heap/property/GUI inputs', 'Successful/empty/failed sample data',
        'Synchronous render submit', 'Painter result in failure-injection cases',
        'Low-level rectangle/barrier services in native painter case', 'Present request'],
        successful_native_statistics_producer=False, actual_pixels=False, camera_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True); p.add_argument('--module', type=Path, required=True)
    p.add_argument('--legacy-build', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); output = a.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists(): p.error('Choose a new private output')
    result = audit((a.build / 'module-host.emulator.main.bin').read_bytes(), json.loads((a.build / 'module-host.emulator.json').read_text()),
        (a.module / 'Z7APP.BIN').read_bytes(), json.loads((a.module / 'module.json').read_text()), a.legacy_build)
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__': main()
