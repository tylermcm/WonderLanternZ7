"""Audit optional update registration and the displaced native entry prefix.

SPDX-License-Identifier: MIT. Compiled host/modules execute. Native comparison
is a supplied return boundary here; complete widget layout and pixels are not.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R12, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_CPSR
from audit_splash_image import ARGUMENTS, SAVED, STACK, STOP, STOCK_SHA
from audit_z7_module_host import HostFixture
from build_z7_module_host import ROOT, STATE


class UpdateFixture(HostFixture):
    prefix = False
    def hook(self, u, address, size, context):
        if self.prefix and address == 0x103690c0:
            self.native_calls += 1
            self.native_input = tuple(u.reg_read(r) for r in (*ARGUMENTS, *SAVED, UC_ARM_REG_R12, UC_ARM_REG_SP))
            self.native_flags = u.reg_read(UC_ARM_REG_CPSR) & 0xf8000000
            self.ret(0x12345678)
        elif self.prefix and address == 0x1036b116:
            self.continuation = tuple(u.reg_read(r) for r in (*ARGUMENTS, *SAVED, UC_ARM_REG_R12, UC_ARM_REG_SP))
            self.saved_stack = bytes(u.mem_read(STACK - 24, 24))
            u.emu_stop()
        else:
            super().hook(u, address, size, context)


def audit(raw, report, stock, directory):
    if hashlib.sha256(raw).hexdigest() != report['main_payload_sha256'] or hashlib.sha256(stock).hexdigest() != STOCK_SHA:
        raise ValueError('Fingerprint mismatch')
    checks = []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    def load(name):
        f = UpdateFixture(raw, report, (directory / (name + '.BIN')).read_bytes())
        meta = json.loads((directory / (name + '.json')).read_text())
        status = f.call(report['symbols']['z7_module_load_once'], STATE)
        return f, meta, status
    good, module, status = load('update-success')
    base = good.words()[12]; symbols = module['symbols']
    def word(f, name): return int.from_bytes(f.u.mem_read(base + symbols[name], 4), 'little')
    check('update-only-module-publishes-after-success', status == 8 and good.words()[23] == 1 and good.words()[37] == 1)
    check('six-owned-code-registration-contracts-pass', word(good, 'z7_update_probe_mask') == 63)
    check('initializer-does-not-invoke-update', word(good, 'z7_update_probe_calls') == 0)
    good.call(report['symbols']['z7_display_before_update'])
    check('published-update-invokes-owned-code', word(good, 'z7_update_probe_calls') == 1)
    check('post-init-registration-rejected', good.call(base + symbols['z7_update_probe_late_register']) == 0)
    for name, offset, value in [('not-ready', 92, 0), ('no-image', 48, 0), ('unregistered', 148, 0), ('bad-guard', 240, 0), ('bad-magic', 32, 0)]:
        saved = good.words()[offset // 4]; before = word(good, 'z7_update_probe_calls')
        good.setword(offset, value); good.call(report['symbols']['z7_display_before_update']); good.setword(offset, saved)
        check(name + '-does-not-invoke-update', word(good, 'z7_update_probe_calls') == before)
    failed, _, status = load('update-failure')
    check('failed-init-clears-update-and-display-publication', status == 7 and failed.words()[36:38] == (0, 0) and failed.words()[23] == 0 and not failed.live)
    failed.call(report['symbols']['z7_display_before_update'])
    check('failed-update-path-returns-without-released-code', not failed.words()[36])
    def prefix(f, flags):
        f.prefix = True; f.native_calls = 0; f.continuation = None
        for i, reg in enumerate((*ARGUMENTS, *SAVED, UC_ARM_REG_R12)): f.u.reg_write(reg, 0x43210000 + i)
        f.u.reg_write(UC_ARM_REG_SP, STACK); f.u.reg_write(UC_ARM_REG_LR, STOP | 1)
        f.u.reg_write(UC_ARM_REG_CPSR, (f.u.reg_read(UC_ARM_REG_CPSR) & ~0xf8000000) | flags)
        f.u.emu_start(0x1036b10d, 0, timeout=10000000, count=100000)
        return f.native_input, f.native_flags, f.continuation, f.saved_stack
    for flags in (0, 0x28000000, 0x50000000, 0xf8000000):
        original = UpdateFixture(stock, report, b'')
        absent = UpdateFixture(raw, report, b'')
        expected = prefix(original, flags)
        check(f'no-module-displaced-prefix-register-stack-flags-{flags:x}', prefix(absent, flags) == expected and absent.native_calls == 1)
        before = word(good, 'z7_update_probe_calls')
        check(f'owned-update-prefix-preserves-native-input-{flags:x}', prefix(good, flags) == expected and good.native_calls == 1)
        check(f'owned-update-bridge-invokes-callback-once-{flags:x}', word(good, 'z7_update_probe_calls') == before + 1)
    return dict(passed=True, checks=checks, main_sha256=report['main_payload_sha256'],
        supplied_boundaries=['Loader kernel/filesystem/heap services', 'Native initial snapshot comparison return'],
        native_entry_prefix_executes=True, full_widget_pipeline=False, actual_pixels=False, camera_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True); p.add_argument('--modules', type=Path, required=True)
    p.add_argument('--stock', type=Path, default=ROOT / '.private/builds/20261021-laptop-01/stock-main.bin')
    p.add_argument('--output', type=Path, required=True); a = p.parse_args()
    output = a.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists(): p.error('Choose a new private output')
    result = audit((a.build / 'module-host.emulator.main.bin').read_bytes(), json.loads((a.build / 'module-host.emulator.json').read_text()), a.stock.read_bytes(), a.modules)
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__': main()
