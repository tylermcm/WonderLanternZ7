"""Native DISP admission and compiled preset-cycle registration checks.

SPDX-License-Identifier: MIT. Original handlers/fallback execute. Named service
results and GUI input state are supplied. No pixels or physical camera proof.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R12, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_CPSR
from audit_splash_image import ARGUMENTS, SAVED, STACK, STOP, STOCK_SHA
from audit_z7_disp_input import SERVICES
from audit_z7_display_readouts import ReadoutFixture, TABLE, SNAPSHOT
from build_z7_module_host import ROOT, STATE


class CycleFixture(ReadoutFixture):
    def __init__(self, *args):
        super().__init__(*args)
        self.results = {p: v for p, v in SERVICES.items() if p != 0x1037061c}
        self.gates = {0x2a: 1, 2: 0}; self.cycle_entries = 0; self.property_writes = []
        self.prefix = False
        self.u.mem_write(0xa181f91c, struct.pack('<I', 0xa2c41000))
        self.u.mem_write(0xa2c41000, struct.pack('<4I', 4, 1, 0, 0xa2c42000))
        self.u.mem_write(SNAPSHOT, bytes(0x33c))
        self.u.mem_write(0xa18237c6, b'\0'); self.u.mem_write(0xa18237b8, bytes(7))

    def hook(self, u, address, size, context):
        if self.prefix and address == 0x10370626:
            self.continuation = tuple(u.reg_read(r) for r in (*ARGUMENTS, *SAVED, UC_ARM_REG_R12, UC_ARM_REG_SP))
            self.saved_stack = bytes(u.mem_read(STACK - 16, 16))
            self.flags = u.reg_read(UC_ARM_REG_CPSR) & 0xf8000000
            u.emu_stop()
        elif address in self.results:
            key = u.reg_read(UC_ARM_REG_R0)
            self.ret(self.gates.get(key, 0) if address == 0x103ea09e else self.results[address])
        elif address == 0x1037061c: self.cycle_entries += 1
        elif address == 0x104065b0:
            self.property_writes.append((u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1))); self.ret(1)
        elif address == 0x103fef80: self.ret(1)
        else: super().hook(u, address, size, context)


def audit(raw, host, packet, module, diagnostics, stock):
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Fingerprint mismatch')
    if hashlib.sha256(stock).hexdigest() != STOCK_SHA: raise ValueError('Exact stock required')
    checks = []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    def load(data=packet):
        f = CycleFixture(raw, host, data)
        status = f.call(host['symbols']['z7_module_load_once'], STATE)
        return f, f.words()[12], status
    f, base, status = load(); symbols = module['symbols']
    def word(g, loaded, name): return int.from_bytes(g.u.mem_read(loaded + symbols[name], 4), 'little')
    def master(g, loaded, value): return g.call(loaded + symbols['z7_settings_flag'], loaded + symbols['z7_menu_settings'], 0, value)
    check('preset-module-publishes-cycle-after-success', status == 8 and f.words()[39] == 1)
    check('outer-key-binding-remains-original', int.from_bytes(f.u.mem_read(0xa1829b0c, 4), 'little') == 0x1030da57)
    f.call(0x1030da56, 0x29)
    check('disabled-delegates-to-original-cycle', f.cycle_entries == 1 and len(f.property_writes) == 1 and not word(f, base, 'z7_preset_cycles'))
    f.u.mem_write(SNAPSHOT + 0x18a, b'\0'); master(f, base, 1)
    entries = f.cycle_entries; f.call(0x1030da56, 0x28)
    check('different-native-key-does-not-call-cycle-or-select-preset', f.cycle_entries == entries and not word(f, base, 'z7_preset_cycles') and not word(f, base, 'z7_readout_preset'))
    for expected in (1, 2, 3, 0):
        writes = len(f.property_writes); f.call(0x1030da56, 0x29)
        check(f'admitted-disp-advances-preset-{expected}', word(f, base, 'z7_readout_preset') == expected and len(f.property_writes) == writes and f.u.mem_read(SNAPSHOT + 0x18a, 1) == b'\0')
        f.call(host['symbols']['z7_display_before_update'])
        bits = int.from_bytes(f.u.mem_read(base + symbols['z7_menu_settings'] + 24 + expected * 4, 4), 'little')
        check(f'preset-{expected}-readout-mask', all(bool(int.from_bytes(f.u.mem_read(int.from_bytes(f.u.mem_read(TABLE + widget * 4, 4), 'little') + 4, 4), 'little') & 1) == bool(bits & (1 << i)) for i, widget in enumerate((10, 11, 15))))
    scenarios = [('outer-admission', {0x10370a90: 1}, {}, 0, 0), ('outer-first-filter', {0x103ebe0c: 1}, {}, 0, 0),
        ('outer-second-filter', {0x103ebe3c: 1}, {}, 0, 0), ('outer-final-filter', {0x103ebed8: 1}, {}, 0, 0),
        ('inner-mode', {0x10401d22: 1}, {}, 0, 0), ('inner-first-exclusion', {0x10297a2e: 1}, {}, 0, 0),
        ('inner-second-exclusion', {0x10297a16: 1}, {}, 0, 0), ('secondary-gate', {}, {0x2a: 0, 2: 1}, 0, 0),
        ('fallback-block', {0x102c7426: 0}, {0x2a: 0, 2: 0}, 0, 0), ('state2', {}, {}, 2, 0),
        ('state5', {}, {}, 5, 0), ('state11', {}, {}, 11, 0), ('skip-cycle', {}, {}, 0, 1)]
    for name, overrides, gates, state, skip in scenarios:
        g, loaded, status = load(); master(g, loaded, 1); g.results.update(overrides)
        if gates: g.gates = gates
        g.u.mem_write(SNAPSHOT, bytes([state])); g.u.mem_write(SNAPSHOT + 0x192, bytes([skip]))
        g.call(0x1030da56, 0x29)
        check(name + '-blocks-custom-cycle', not g.cycle_entries and not word(g, loaded, 'z7_readout_preset') and not word(g, loaded, 'z7_preset_cycles'))
    for name, address, value in [('movie', SNAPSHOT + 0x40, b'\1'), ('output', 0xa18237c6, b'\2'), ('menu', 0xa2c41008, struct.pack('<I', 1)),
            ('unbound-information', 0, struct.pack('<I', 31))]:
        g, loaded, status = load(); master(g, loaded, 1)
        if name == 'unbound-information': address = loaded + symbols['z7_menu_settings'] + 4
        g.u.mem_write(address, value); g.call(0x1030da56, 0x29)
        check(name + '-delegates-without-custom-advance', not word(g, loaded, 'z7_readout_preset') and not word(g, loaded, 'z7_preset_cycles') and bool(g.property_writes))
    for page in (0, 2): check('disable-choice-' + str(page), f.call(base + symbols['z7_settings_page'], base + symbols['z7_menu_settings'], page, 0) == 1)
    for expected in (1, 3, 1):
        f.call(0x1030da56, 0x29); check('skip-disabled-to-' + str(expected), word(f, base, 'z7_readout_preset') == expected)
    probe = json.loads((diagnostics / 'cycle-success.json').read_text()); ps = probe['symbols']
    g, loaded, status = load((diagnostics / 'cycle-success.BIN').read_bytes())
    read = lambda name: int.from_bytes(g.u.mem_read(loaded + ps[name], 4), 'little')
    check('owned-cycle-registration-contracts', status == 8 and read('z7_cycle_probe_mask') == 63 and g.words()[39] == 1)
    check('init-does-not-call-cycle', not read('z7_cycle_probe_calls'))
    check('late-registration-rejected', g.call(loaded + ps['z7_cycle_probe_late_register']) == 0)
    for value in (0, 1, 2, 3, 0x100, 0x101, 0xffffffff):
        g.u.mem_write(loaded + ps['z7_cycle_probe_result'], struct.pack('<I', value))
        check('validate-cycle-result-' + hex(value), g.call(host['symbols']['z7_display_disp_cycle']) == (value if value in (2, 0x100) else 0))
    for name, off in [('not-ready', 92), ('no-image', 48), ('unregistered', 156), ('bad-guard', 240)]:
        saved = int.from_bytes(g.u.mem_read(STATE + off, 4), 'little'); before = read('z7_cycle_probe_calls')
        g.setword(off, 0); check(name + '-cycle-not-called', g.call(host['symbols']['z7_display_disp_cycle']) == 0 and read('z7_cycle_probe_calls') == before); g.setword(off, saved)
    g, loaded, status = load((diagnostics / 'cycle-failure.BIN').read_bytes())
    check('failed-init-clears-cycle-and-frees-image', status == 7 and g.words()[38:40] == (0, 0) and not g.live and g.call(host['symbols']['z7_display_disp_cycle']) == 0)
    g, loaded, status = load((diagnostics / 'cycle-success.BIN').read_bytes())
    check('consumed-bridge-returns-native-update-result', g.call(0x1037061c) == 0x100 and not g.property_writes)
    def prefix(g, flags):
        g.prefix = True; g.continuation = None
        for i, reg in enumerate((*ARGUMENTS, *SAVED, UC_ARM_REG_R12)): g.u.reg_write(reg, 0x43210000 + i)
        g.u.reg_write(UC_ARM_REG_SP, STACK); g.u.reg_write(UC_ARM_REG_LR, STOP | 1)
        g.u.reg_write(UC_ARM_REG_CPSR, (g.u.reg_read(UC_ARM_REG_CPSR) & ~0xf8000000) | flags)
        g.u.emu_start(0x1037061d, 0, timeout=10000000, count=100000)
        return g.continuation, g.flags, g.saved_stack
    for flags in (0, 0x28000000, 0x50000000, 0xf8000000):
        original = CycleFixture(stock, host, b''); absent = CycleFixture(raw, host, b'')
        expected = prefix(original, flags)
        check('absent-cycle-prefix-preserves-registers-stack-flags-' + hex(flags), prefix(absent, flags) == expected)
        g, loaded, status = load((diagnostics / 'cycle-success.BIN').read_bytes())
        for result in (0, 1, 0x101):
            g.u.mem_write(loaded + ps['z7_cycle_probe_result'], struct.pack('<I', result))
            check('delegated-cycle-prefix-' + hex(flags) + '-' + hex(result), prefix(g, flags) == expected)
    return dict(passed=True, checks=checks, main_sha256=host['main_payload_sha256'], module_sha256=module['module_sha256'],
        original_outer_and_inner_admission_execute=True, original_fallback_cycle_executes=True,
        supplied_boundaries=['Loader/kernel/filesystem/heap', 'Incoming GUI/pool/page/output state', 'Named native admission service returns', 'Native property setter result'],
        actual_pixels=False, camera_access=False, information_app_bound=False, native_base_components_bound=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True); p.add_argument('--module', type=Path, required=True)
    p.add_argument('--diagnostics', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--stock', type=Path, default=ROOT / '.private/builds/20261021-laptop-01/stock-main.bin')
    p.add_argument('--legacy-build', type=Path, help='Optional older 24-byte host rejection check')
    a = p.parse_args(); output = a.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists(): p.error('Choose a new private output')
    r = audit((a.build / 'module-host.emulator.main.bin').read_bytes(), json.loads((a.build / 'module-host.emulator.json').read_text()), (a.module / 'Z7APP.BIN').read_bytes(), json.loads((a.module / 'module.json').read_text()), a.diagnostics, a.stock.read_bytes())
    if a.legacy_build:
        old = (a.legacy_build / 'module-host.emulator.main.bin').read_bytes()
        meta = json.loads((a.legacy_build / 'module-host.emulator.json').read_text())
        if hashlib.sha256(old).hexdigest() != meta['main_payload_sha256']: raise ValueError('Legacy host fingerprint')
        f = CycleFixture(old, meta, (a.module / 'Z7APP.BIN').read_bytes())
        regions = [(0xa1833548, 44), (0xa1836f8c, 44), (0xa1829b0c, 4)]
        regions += [(int.from_bytes(f.u.mem_read(TABLE + i * 4, 4), 'little'), 48) for i in range(61)]
        before = [bytes(f.u.mem_read(p, n)) for p, n in regions]
        status = f.call(meta['symbols']['z7_module_load_once'], STATE)
        passed = status == 7 and before == [bytes(f.u.mem_read(p, n)) for p, n in regions] and not f.live
        if not passed: raise AssertionError('Older host rejection before native stores')
        r['checks'].append(dict(name='older-24-byte-api-rejects-before-native-stores', passed=True))
        r['legacy_main_sha256'] = meta['main_payload_sha256']
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(r, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(r['checks']))))


if __name__ == '__main__': main()
