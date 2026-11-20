"""Compiled focal overlay ownership, formatting and transition contracts.

SPDX-License-Identifier: MIT. Native allocation/initialization, property reads
and object visibility/dirty helpers execute. Incoming GUI/lens state, labels,
font/list/paint, render submit and presentation remain supplied boundaries.
No framebuffer pixels or physical lens/output behavior are established.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import time

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC
from audit_splash_image import ARGUMENTS, SAVED, STACK, STOP
from audit_z7_histogram_component import HistogramFixture
from audit_z7_battery_display import SLOTS
from build_z7_module_host import ROOT, STATE

LABEL = 0xa2019e78 + 298 * 12
TYPE, VALUE = 0xa24e2600, 0xa24e25a8


class FocalOverlayFixture(HistogramFixture):
    def __init__(self, *args):
        super().__init__(*args)
        self.u.mem_map(0xa24e0000, 0x10000)
        self.write(LABEL, 0); self.write(LABEL + 4, 0xa2c40100); self.write(LABEL + 8, 0)
        self.write(TYPE, 1); self.write(VALUE, 245)
        self.write(0xa1821370 + 0x24, 1)
        self.write(0xa1829af8, 0x1030d511)
        self.write(0xa1829b0c, 0x1030da57); self.write(0xa1829b10, 0x1030dd1f)
        self.active_histogram = True
        self.focal_gets = []
        self.focal_paint_active = False
        self.longest_call_seconds = 0
        self.focal_object_global = self.focal_renderer = 0
        self.focal_fail_submit = False
    def call(self, address, *args):
        # The larger module CRC plus per-instruction lifecycle checks can
        # exceed the shared fixture's10s wall budget. Retain its10M instruction
        # cap and all original stack/callee-save guards; allow30s wall time.
        u = self.u
        for reg in ARGUMENTS: u.reg_write(reg, 0)
        for reg, value in zip(ARGUMENTS, args): u.reg_write(reg, value)
        guards = {reg: 0x51510000 + i for i, reg in enumerate(SAVED)}
        for reg, value in guards.items(): u.reg_write(reg, value)
        u.reg_write(UC_ARM_REG_SP, STACK); u.reg_write(UC_ARM_REG_LR, STOP | 1)
        started = time.monotonic()
        u.emu_start(address | 1, STOP, timeout=30000000, count=10000000)
        self.longest_call_seconds = max(self.longest_call_seconds, time.monotonic() - started)
        if u.reg_read(UC_ARM_REG_PC) != STOP or u.reg_read(UC_ARM_REG_SP) != STACK:
            raise ValueError(f'Incomplete native call:pc={u.reg_read(UC_ARM_REG_PC):08x},sp={u.reg_read(UC_ARM_REG_SP):08x}')
        if any(u.reg_read(reg) != value for reg, value in guards.items()):
            raise ValueError('Native call changed a callee-saved register')
        return u.reg_read(UC_ARM_REG_R0)
    def hook(self, u, address, size, context):
        if self.focal_paint_active and address in (0x103fe85e, 0x104065a4, 0x103673ac, 0x103fa770, 0x103ecf90):
            raise AssertionError('Focal painter re-entered a property or GUI wait service')
        if address == 0x103fbb5c and u.reg_read(UC_ARM_REG_R1) == 298:
            text = self.cstring(u.reg_read(UC_ARM_REG_R0))
            if len(text) > 15:
                raise AssertionError('Focal string exceeds owned buffer')
            pointer = self.read(LABEL + 4)
            u.mem_write(pointer, text.encode() + b'\0')
            self.write(LABEL, len(text)); self.write(LABEL + 8, u.reg_read(UC_ARM_REG_R2))
            self.labels.append((text, 298)); self.ret(0)
        elif address == 0x103fe85e:
            self.focal_gets.append(u.reg_read(UC_ARM_REG_R0))
            # Execute original property wrapper and typed read.
        elif address == 0x102f2042:
            self.submits += 1
            if self.focal_fail_submit:
                self.ret(0); return
            if not self.focal_renderer or not self.read(self.focal_object_global):
                raise AssertionError('Missing focal object for supplied render dispatch')
            u.reg_write(UC_ARM_REG_R0, self.read(self.focal_object_global))
            for reg in (UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3): u.reg_write(reg, 0)
            u.reg_write(UC_ARM_REG_PC, self.focal_renderer)
        else:
            super().hook(u, address, size, context)


def audit(raw, host, packet, module):
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Fingerprint mismatch')
    symbols = module['symbols']; checks = []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good:
            raise AssertionError(name)
    def load():
        f = FocalOverlayFixture(raw, host, packet)
        if f.call(host['symbols']['z7_module_load_once'], STATE) != 8:
            raise AssertionError('Module load')
        at = f.words()[12]
        f.focal_object_global, f.focal_renderer = at + symbols['z7_focal_object'], at + symbols['focal_painter']
        return f, at
    def word(f, base, name): return f.read(base + symbols['z7_focal_' + name])
    def before(f): f.call(host['symbols']['z7_display_before_update'])
    def after(f):
        # Incoming state at the after-GUI boundary includes the native delta
        # snapshot synchronization; no completed framebuffer is supplied.
        f.u.mem_write(0xa201d80c, bytes(f.u.mem_read(0xa201d4d0, 0x33c)))
        f.call(host['symbols']['z7_display_after_gui_update'])
    def info(f, base, group, on): f.call(base + symbols['z7_settings_information'], base + symbols['z7_menu_settings'], 0, group, on)
    def enable(f, base):
        model = base + symbols['z7_menu_settings']
        f.call(base + symbols['z7_settings_component'], model, 0, 1, 0)
        f.call(base + symbols['z7_settings_component'], model, 0, 2, 0)
        info(f, base, 7, 1)
        f.call(base + symbols['z7_settings_flag'], model, 0, 1)
        before(f)
    def paint(f, base):
        f.paint_calls.clear()
        f.focal_paint_active = True
        try:
            return f.call(base + symbols['focal_painter'], word(f, base, 'object'), 0, 0, 0)
        finally:
            f.focal_paint_active = False
    f, base = load()
    check('init-does-not-create-focal-object-or-label', not word(f, base, 'object') and not f.labels and not f.list_calls)
    check('composed-after-gui-callback-registered', f.words()[41] == 1 and f.words()[40] == base + symbols['focal_combined_after_gui'])
    enable(f, base)
    masks = [bytes(f.u.mem_read(f.read(0x1064d610 + i * 4) + 4, 36)) for i in range(61)]
    vr = f.read(0x1064d610 + 50 * 4)
    vr_controls = bytes(f.u.mem_read(f.read(vr + 44), 3 * 48))
    after(f)
    obj = word(f, base, 'object')
    check('fractional-live-value-creates-independent-owned-text', bool(obj) and f.labels == [('24.5mm', 298)] and f.read(SLOTS + 1198 * 4) == obj)
    check('battery-slot-and-label-remain-separate', not f.read(SLOTS + 1199 * 4) and not f.read(0xa2019e78 + 299 * 12))
    check('one-native-registration-and-present', f.list_calls == [(0xa201e3b4, obj)] and f.presents == 1)
    paint(f, base)
    check('painter-clears-own-window-and-calls-native-text-only', [p[0] for p in f.paint_calls] == [0x10433912, 0x10384968])
    shape = struct.unpack('<24I', f.paint_calls[0][1])
    check('transparent-clear-scoped-to-dedicated-window', shape[4:6] == (110 | (194 << 16), 220 | (218 << 16)) and shape[13:15] == (2, 0))
    check('focal-never-edits-native-descriptors-or-vr-controls', masks == [bytes(f.u.mem_read(f.read(0x1064d610 + i * 4) + 4, 36)) for i in range(61)] and
          vr_controls == bytes(f.u.mem_read(f.read(vr + 44), 3 * 48)))
    old_gets, old_submits = len(f.focal_gets), f.submits
    f.now += 99; after(f)
    check('sub100ms-callback-does-not-resample-or-submit', len(f.focal_gets) == old_gets and f.submits == old_submits)
    f.now += 1; after(f)
    check('unchanged-value-resamples-without-label-or-render-churn', len(f.focal_gets) == old_gets + 3 and f.submits == old_submits and len(f.labels) == 1)
    for value, text in ((240, '24mm'), (1, '0.1mm'), (40000, '4000mm'), (4294967294, '429496729.4mm')):
        f.write(VALUE, value); f.now += 100; after(f)
        check('native-label-format-' + str(value), f.labels[-1] == (text, 298) and word(f, base, 'object') == obj and len(f.list_calls) == 1)
    painted = word(f, base, 'paints')
    info(f, base, 6, 0); before(f); f.now += 100; after(f)
    check('other-off-repaints-unchanged-independent-focal-text', word(f, base, 'object') == obj and f.read(obj + 40) == 1 and word(f, base, 'paints') > painted)
    info(f, base, 7, 0); before(f); paint(f, base)
    check('focal-off-retires-text-without-native-vr-control-stores', [p[0] for p in f.paint_calls] == [0x10433912] and not f.read(obj + 40) and
          vr_controls == bytes(f.u.mem_read(f.read(vr + 44), 3 * 48)))
    info(f, base, 7, 1); f.write(VALUE, 245); before(f); f.now += 100; after(f)
    check('reenable-reuses-object-and-samples-immediately', word(f, base, 'object') == obj and f.labels[-1] == ('24.5mm', 298) and f.read(obj + 40) == 1)
    for kind, value in ((0, 245), (2, 245), (4, 245), (255, 245), (1, 0), (3, 0xffffffff)):
        f.write(TYPE, kind); f.write(VALUE, value); f.now += 100; after(f); paint(f, base)
        check(f'invalid-kind{kind}-value{value}-clears-without-text', not f.read(obj + 40) and [p[0] for p in f.paint_calls] == [0x10433912])
        f.write(TYPE, 1); f.write(VALUE, 245); f.now += 100; after(f)
    for name, mutate in (
        ('movie', lambda f: f.u.mem_write(0xa201d510, b'\1')),
        ('evf', lambda f: f.u.mem_write(0xa18237c6, b'\2')),
        ('rotation', lambda f: f.u.mem_write(0xa201d808, b'\1\0')),
        ('af-state', lambda f: f.u.mem_write(0xa201d4d0, b'\1')),
        ('alternate-operation', lambda f: f.u.mem_write(0xa201d663, b'\1')),
        ('menu', lambda f: f.write(0xa2c41008, 1)),
        ('foreign-slot', lambda f: f.write(SLOTS + 1198 * 4, 0xa2c45000)),
        ('foreign-label', lambda f: (f.write(LABEL, 2), f.u.mem_write(0xa2c40100, b'AF\0'))),
        ('full-pool', lambda f: f.u.mem_write(f.read(0xa181c77c), struct.pack('<1200I', *([1] * 1200)))),
    ):
        bad, at = load(); enable(bad, at); mutate(bad); before(bad); after(bad)
        check(name + '-rejects-new-focal-registration-and-sampling', not word(bad, at, 'object') and not bad.labels and not bad.focal_gets)
    f.write(SLOTS + 1198 * 4, 0); before(f); f.now += 100; after(f)
    check('detached-object-is-forgotten-before-reallocation', word(f, base, 'object') != obj and len(f.list_calls) == 2)
    f.paint_calls.clear(); f.call(base + symbols['focal_painter'], obj, 0, 0, 0)
    check('detached-old-object-cannot-paint', not f.paint_calls)
    # Supply each current logical preset, while using the compiled setters for
    # independent per-preset choices. Native key cycling has separate coverage.
    for preset in range(4):
        for group, on in ((6, 1 - preset % 2), (7, preset % 2)):
            f.call(base + symbols['z7_settings_information'], base + symbols['z7_menu_settings'], preset, group, on)
        f.write(base + symbols['z7_readout_preset'], preset)
        before(f); f.now += 100; after(f); paint(f, base)
        check(f'incoming-preset-{preset}-independent-focal-choice', f.read(word(f, base, 'object') + 40) == preset % 2)
    for name, set_busy, clear_busy in (
        ('pending', lambda: setattr(f, 'pending', 1), lambda: setattr(f, 'pending', 0)),
        ('render-busy', lambda: f.write(0xa1821370 + 0x34, 1), lambda: f.write(0xa1821370 + 0x34, 0)),
    ):
        count, submitted = len(f.focal_gets), f.submits
        set_busy(); f.write(VALUE, 240); f.now += 100; after(f)
        check(name + '-does-not-query-or-submit', len(f.focal_gets) == count and f.submits == submitted)
        clear_busy(); after(f)
        check(name + '-recovers-on-current-lens-value', word(f, base, 'tenths') == 240)
    painted = word(f, base, 'paints')
    f.u.mem_write(0xa201d4d0 + 8, b'\1'); before(f); f.now += 100; after(f)
    check('native-hud-snapshot-delta-repaints-unchanged-label', word(f, base, 'paints') > painted)
    painted, presented = word(f, base, 'paints'), f.presents
    f.focal_fail_submit = True; f.write(VALUE, 245); f.now += 100; after(f)
    check('failed-submit-retains-repaint-request-without-present', word(f, base, 'paints') == painted and f.presents == presented)
    f.focal_fail_submit = False; f.now += 100; after(f)
    check('unchanged-label-retries-retained-repaint-request', word(f, base, 'paints') > painted and f.presents == presented + 1)
    return dict(passed=True, checks=checks, module_sha256=module['module_sha256'], owned_slot=1198, label_slot=298,
        independent_of_other_and_vr=True, native_allocation_and_initialization_execute=True,
        native_call_wall_budget_seconds=30, native_call_instruction_cap=10000000,
        stack_and_callee_save_guards_checked=True, longest_primary_fixture_call_seconds=f.longest_call_seconds,
        native_source_getter_executes=True, actual_pixels=False, evf_or_rotated_layout_implemented=False,
        supplied_boundaries=['Incoming GUI/lens state', 'Labels/font/list/paint', 'Render submit/presentation', 'Loader/kernel'], camera_access=False)


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
