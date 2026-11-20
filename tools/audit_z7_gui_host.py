"""Audit owned after-GUI registration and the original shooting-update wrapper.

SPDX-License-Identifier: MIT. Original callback instructions execute with named
native service returns supplied. This is an ABI/order test, not a widget, frame,
statistics producer, physical camera or recovery test.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R12, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_CPSR
from audit_splash_image import ARGUMENTS, SAVED, STACK, STOP, STOCK_SHA
from audit_z7_module_host import HostFixture
from build_z7_module_host import ROOT, STATE

SLOT = 0xa1829b14
ORIGINAL = 0x1030db42
END = 0x1030dd1e


class GuiFixture(HostFixture):
    observing = False

    def __init__(self, raw, report, packet):
        super().__init__(raw, report, packet)
        self.u.mem_map(0xa2010000, 0x20000)
        decoder = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        self.services = {int(i.op_str.lstrip('#'), 16) for i in decoder.disasm(
            raw[ORIGINAL - 0x10020000:END - 0x10020000], ORIGINAL) if i.mnemonic == 'bl'}

    def word(self, address):
        return int.from_bytes(self.u.mem_read(address, 4), 'little')

    def hook(self, u, address, size, context):
        if self.observing:
            if address == ORIGINAL:
                self.order.append('original-entry')
                self.entries.append(tuple(u.reg_read(r) for r in (*ARGUMENTS, *SAVED, UC_ARM_REG_R12)))
            if address == (self.report['symbols']['z7_display_after_gui_update'] & ~1):
                self.order.append('after-original-return')
            if self.words()[40] and address == (self.words()[40] & ~1):
                self.order.append('owned-callback')
            if address in self.services:
                key = u.reg_read(UC_ARM_REG_R0)
                result = 0
                if address == 0x10376418:
                    result = 1 if self.scenario == 'mode-transition' else 0
                elif address == 0x10301c3e:
                    result = int(self.scenario == 'app-transition')
                elif address == 0x104065a4 and key == 0x1f00:
                    result = int(self.scenario == 'app-transition')
                elif address == 0x102995b0:
                    result = int(self.scenario == 'pending-byte')
                elif address == 0x102995b8:
                    u.mem_write(key, struct.pack('<I', 7))
                    result = 1
                elif address in (0x103240aa, 0x103764b8):
                    self.order.append('native-gui-service' if address == 0x103240aa else 'native-app-transition')
                    result = 0x27183800
                # Explicit caller-clobbered service outputs, identical in both
                # images; no supplied success for statistics or actual drawing.
                for r, value in ((UC_ARM_REG_R1, 0x11335577), (UC_ARM_REG_R2, 0x22446688),
                                 (UC_ARM_REG_R3, 0x33557799), (UC_ARM_REG_R12, 0x446688aa)):
                    u.reg_write(r, value)
                self.ret(result)
                return
        super().hook(u, address, size, context)

    def update(self, address, flags=0, scenario='ordinary'):
        self.observing = True
        self.scenario, self.order, self.entries = scenario, [], []
        self.u.mem_write(0xa201d4d0, bytes([2 if scenario == 'snapshot-transition' else 0]))
        for i, reg in enumerate((*ARGUMENTS, *SAVED, UC_ARM_REG_R12)):
            self.u.reg_write(reg, 0x43210000 + i)
        self.u.reg_write(UC_ARM_REG_SP, STACK)
        self.u.reg_write(UC_ARM_REG_LR, STOP | 1)
        self.u.reg_write(UC_ARM_REG_CPSR, (self.u.reg_read(UC_ARM_REG_CPSR) & ~0xf8000000) | flags)
        self.u.emu_start(address | 1, STOP, timeout=10000000, count=100000)
        self.observing = False
        if self.u.reg_read(UC_ARM_REG_PC) != STOP or self.u.reg_read(UC_ARM_REG_SP) != STACK:
            raise AssertionError('GUI wrapper did not restore caller stack/return')
        return (tuple(self.u.reg_read(r) for r in (*ARGUMENTS, *SAVED, UC_ARM_REG_R12)),
                self.u.reg_read(UC_ARM_REG_CPSR) & 0xf8000000)


def audit(raw, report, stock, directory, legacy):
    if hashlib.sha256(raw).hexdigest() != report['main_payload_sha256'] or hashlib.sha256(stock).hexdigest() != STOCK_SHA:
        raise ValueError('Fingerprint mismatch')
    checks, scenarios = [], []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good:
            raise AssertionError(name)
    def load(name, image=raw, host=report, foreign=False):
        f = GuiFixture(image, host, (directory / (name + '.BIN')).read_bytes())
        meta = json.loads((directory / (name + '.json')).read_text())
        if foreign:
            f.u.mem_write(SLOT, struct.pack('<I', ORIGINAL | 1))
        status = f.call(host['symbols']['z7_module_load_once'], STATE)
        return f, meta, status
    good, module, status = load('gui-success')
    base, symbols = good.words()[12], module['symbols']
    def word(name):
        return good.word(base + symbols[name])
    bridge = report['symbols']['z7_gui_update_bridge']
    check('native-update-body-byte-identical', raw[ORIGINAL-0x10020000:END-0x10020000] == stock[ORIGINAL-0x10020000:END-0x10020000])
    check('native-key-event-slots-unchanged', good.word(SLOT-8) == 0x1030da57 and good.word(SLOT-4) == 0x1030dd1f)
    check('only-update-slot-uses-resident-wrapper', good.word(SLOT) == bridge)
    check('gui-only-success-publishes', status == 8 and good.words()[23] == 1 and good.words()[41:43] == (1, 0))
    check('six-owned-registration-contracts', word('z7_gui_probe_mask') == 63)
    check('init-does-not-call-gui', word('z7_gui_probe_calls') == 0)
    good.call(report['symbols']['z7_display_after_gui_update'])
    check('dispatcher-invokes-owned-code', word('z7_gui_probe_calls') == 1)
    check('late-registration-rejected', good.call(base + symbols['z7_gui_probe_late_register']) == 0)
    for name, offset, value in [('not-ready', 92, 0), ('no-image', 48, 0), ('unregistered', 164, 0),
                                ('running', 168, 1), ('bad-guard', 240, 0), ('bad-magic', 32, 0)]:
        saved, before = good.words()[offset // 4], word('z7_gui_probe_calls')
        good.setword(offset, value)
        good.call(report['symbols']['z7_display_after_gui_update'])
        good.setword(offset, saved)
        check(name + '-skips-callback', word('z7_gui_probe_calls') == before)
    good.u.mem_write(SLOT, struct.pack('<I', ORIGINAL | 1))
    before = word('z7_gui_probe_calls')
    good.call(report['symbols']['z7_display_after_gui_update'])
    check('foreign-slot-skips-callback', word('z7_gui_probe_calls') == before)
    good.u.mem_write(SLOT, struct.pack('<I', bridge))
    for scenario in ('ordinary', 'app-transition', 'mode-transition', 'snapshot-transition', 'pending-byte'):
        for flags in (0, 0x28000000, 0x50000000, 0xf8000000):
            original = GuiFixture(stock, report, b'')
            absent = GuiFixture(raw, report, b'')
            expected = original.update(ORIGINAL, flags, scenario)
            check(f'{scenario}-{flags:x}-absent-abi', absent.update(bridge, flags, scenario) == expected)
            before = word('z7_gui_probe_calls')
            check(f'{scenario}-{flags:x}-owned-abi', good.update(bridge, flags, scenario) == expected)
            check(f'{scenario}-{flags:x}-original-entry-registers', good.entries == original.entries)
            check(f'{scenario}-{flags:x}-callback-after-return', good.order == original.order + ['after-original-return', 'owned-callback'])
            check(f'{scenario}-{flags:x}-callback-once', word('z7_gui_probe_calls') == before + 1 and good.words()[42] == 0)
            scenarios.append(dict(scenario=scenario, incoming_flags=flags, order=good.order, final_flags=expected[1]))
    good.u.mem_write(base + symbols['z7_gui_probe_recurse'], struct.pack('<I', 1))
    before = word('z7_gui_probe_calls')
    good.update(bridge)
    check('nested-native-update-still-executes', good.order.count('original-entry') == 2 and good.order.count('native-gui-service') == 2)
    check('nested-module-callback-suppressed', word('z7_gui_probe_calls') == before + 1 and good.words()[42] == 0)
    for name, foreign in [('gui-failure', False), ('gui-success', True)]:
        f, _, status = load(name, foreign=foreign)
        check(name + ('-foreign' if foreign else '') + '-clears-failed-publication',
              status == 7 and f.words()[40:43] == (0, 0, 0) and not f.words()[23] and not f.live)
        f.call(report['symbols']['z7_display_after_gui_update'])
        check(name + ('-foreign' if foreign else '') + '-released-code-not-called', not f.words()[40])
    old = json.loads((legacy / 'module-host.emulator.json').read_text())
    f, _, status = load('gui-success', (legacy / 'module-host.emulator.main.bin').read_bytes(), old)
    check('legacy-api28-rejects-api32-module', status == 7 and not f.live and f.word(SLOT) == (ORIGINAL | 1))
    return dict(passed=True, checks=checks, scenarios=scenarios, main_sha256=report['main_payload_sha256'],
                api_bytes=32, state_bytes=256, supplied_boundaries=['Loader kernel/filesystem/heap',
                'Original shooting-update direct native service returns'], original_callback_instructions_execute=True,
                full_widget_pipeline=False, statistics_production=False, actual_pixels=False, camera_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--modules', type=Path, required=True)
    p.add_argument('--legacy-build', type=Path, required=True)
    p.add_argument('--stock', type=Path, default=ROOT / '.private/builds/20261021-laptop-01/stock-main.bin')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    output = a.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists():
        p.error('Choose a new private output')
    result = audit((a.build / 'module-host.emulator.main.bin').read_bytes(),
                   json.loads((a.build / 'module-host.emulator.json').read_text()), a.stock.read_bytes(), a.modules, a.legacy_build)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']), scenarios=len(result['scenarios']))))


if __name__ == '__main__':
    main()
