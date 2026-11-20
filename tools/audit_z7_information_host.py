"""Execute compiled information registration, admitted-key bridge and wrapper.

SPDX-License-Identifier: MIT. Original key/admission and displaced instructions
execute. Loader, named native services and the information-update body are
supplied. This is ABI/ownership validation, not panel pixels or custom DISP.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R12, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_CPSR
from audit_splash_image import ARGUMENTS, SAVED, STACK, STOP, STOCK_SHA
from audit_z7_information_native import InformationFixture, APP, TABLE, INFO, CALLBACK
from audit_z7_module_host import HostFixture
from build_z7_module_host import ROOT, STATE

REGISTERS = (*ARGUMENTS, *SAVED, UC_ARM_REG_R12, UC_ARM_REG_LR, UC_ARM_REG_SP)


class InformationHostFixture(HostFixture, InformationFixture):
    observing = False

    def hook(self, u, address, size, context):
        if self.observing:
            if address in (0x102fd7e6, 0x102fd7e8, 0x102fd9b4):
                self.continuations.append((address, tuple(u.reg_read(r) for r in REGISTERS),
                                           u.reg_read(UC_ARM_REG_CPSR) & 0xf8000000))
            if address == 0x102fda08:
                self.native_updates.append(tuple(u.reg_read(r) for r in REGISTERS))
                for r, value in ((UC_ARM_REG_R1, 0x11335577), (UC_ARM_REG_R2, 0x22446688),
                                 (UC_ARM_REG_R3, 0x33557799), (UC_ARM_REG_R12, 0x446688aa)):
                    u.reg_write(r, value)
                u.reg_write(UC_ARM_REG_CPSR, (u.reg_read(UC_ARM_REG_CPSR) & ~0xf8000000) | 0x58000000)
                self.ret(0x31415926)
                return
        super().hook(u, address, size, context)

    def invoke(self, address, key=0x29, flags=0):
        self.observing = True
        self.continuations, self.native_updates, self.events, self.stores = [], [], [], []
        for index, r in enumerate((*ARGUMENTS, *SAVED, UC_ARM_REG_R12)):
            self.u.reg_write(r, 0x43210000 + index)
        self.u.reg_write(UC_ARM_REG_R0, key)
        self.u.reg_write(UC_ARM_REG_SP, STACK)
        self.u.reg_write(UC_ARM_REG_LR, STOP | 1)
        self.u.reg_write(UC_ARM_REG_CPSR, (self.u.reg_read(UC_ARM_REG_CPSR) & ~0xf8000000) | flags)
        self.u.emu_start(address | 1, STOP, timeout=10000000, count=100000)
        self.observing = False
        if self.u.reg_read(UC_ARM_REG_PC) != STOP or self.u.reg_read(UC_ARM_REG_SP) != STACK:
            raise AssertionError('Information bridge changed its caller stack/return')
        return tuple(self.u.reg_read(r) for r in REGISTERS), self.u.reg_read(UC_ARM_REG_CPSR) & 0xf8000000


def audit(raw, report, stock, directory, legacy):
    if hashlib.sha256(raw).hexdigest() != report['main_payload_sha256'] or hashlib.sha256(stock).hexdigest() != STOCK_SHA:
        raise ValueError('Fingerprint mismatch')
    checks = []

    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good:
            raise AssertionError(name)

    def context(f):
        f.u.mem_write(0xa1829af4, b'\15')
        f.u.mem_write(TABLE + 13 * 4, struct.pack('<I', APP))
        f.u.mem_write(INFO, bytes(256))
        f.call(0x10376440, APP, CALLBACK | 1, 13)

    def load(name='information-success', host=report, image=raw, foreign=None):
        f = InformationHostFixture(image, host, (directory / (name + '.BIN')).read_bytes())
        if foreign:
            f.u.mem_write(foreign, bytes(4))
        status = f.call(host['symbols']['z7_module_load_once'], STATE)
        f.probe_base = f.words()[12]
        context(f)
        return f, status

    module = json.loads((directory / 'information-success.json').read_text(encoding='utf-8'))
    f, status = load()
    base, symbols = f.words()[12], module['symbols']

    def value(g, name):
        return int.from_bytes(g.u.mem_read(g.probe_base + symbols[name], 4), 'little')

    def configure(g, name, v):
        g.u.mem_write(g.probe_base + symbols[name], struct.pack('<I', v))

    check('api40-information-only-module-loaded', status == 8 and value(f, 'z7_info_probe_api_bytes') == 40 and f.words()[23] == 1)
    check('both-registration-contracts', value(f, 'z7_info_probe_cycle_mask') == 63 and value(f, 'z7_info_probe_update_mask') == 63)
    check('init-does-not-call-information-hooks', not value(f, 'z7_info_probe_cycles') and not value(f, 'z7_info_probe_updates'))
    check('native-information-key-event-slots-unchanged',
          int.from_bytes(f.u.mem_read(APP + 0x14, 4), 'little') == 0x102fd647 and
          int.from_bytes(f.u.mem_read(APP + 0x18, 4), 'little') == 0x102fdaef)
    check('native-information-update-body-unchanged', raw[0x102fda08-0x10020000:0x102fdaee-0x10020000] == stock[0x102fda08-0x10020000:0x102fdaee-0x10020000])
    check('late-cycle-registration-rejected', f.call(base + symbols['z7_info_probe_late_cycle']) == 0)
    check('late-update-registration-rejected', f.call(base + symbols['z7_info_probe_late_update']) == 0)
    for result in (0, 1, 2, 0x100, 0x101, 0xffffffff):
        configure(f, 'z7_info_probe_result', result)
        check('validate-owned-cycle-result-' + hex(result),
              f.call(report['symbols']['z7_display_information_cycle']) == (result if result in (2, 0x100) else 0))
    configure(f, 'z7_info_probe_result', 0)
    for flags in (0, 0x28000000, 0x50000000, 0xf8000000):
        for busy, monitor in ((0, 1), (1, 1), (0, 3)):
            original = InformationHostFixture(stock, report, b'')
            absent = InformationHostFixture(raw, report, b'')
            for g in (original, absent, f):
                context(g)
                g.results[0x1040a4ae] = busy
                g.monitor = monitor
            expected = original.invoke(0x102fd646, flags=flags)
            check(f'absent-key-{flags:x}-{busy}-{monitor}-whole-native-abi', absent.invoke(0x102fd646, flags=flags) == expected)
            before = value(f, 'z7_info_probe_cycles')
            check(f'delegated-key-{flags:x}-{busy}-{monitor}-whole-native-abi', f.invoke(0x102fd646, flags=flags) == expected)
            check(f'delegated-key-{flags:x}-{busy}-{monitor}-exact-native-continuations', f.continuations == original.continuations == absent.continuations)
            check(f'delegated-key-{flags:x}-{busy}-{monitor}-once', value(f, 'z7_info_probe_cycles') == before + 1)
    for result in (2, 0x100):
        configure(f, 'z7_info_probe_result', result)
        f.invoke(0x102fd646)
        check('consumed-key-' + hex(result) + '-skips-native-exit', not f.events and not f.stores and
              [c[0] for c in f.continuations] == [0x102fd9b4])
    configure(f, 'z7_info_probe_result', 0x100)
    for name, gates, fallback in (('secondary-gate', {0x2a: 0, 2: 1}, 1),
                                   ('fallback-gate', {0x2a: 0, 2: 0}, 0)):
        f.gates, f.results[0x102c7426] = gates, fallback
        before = value(f, 'z7_info_probe_cycles')
        f.invoke(0x102fd646)
        check(name + '-native-admission-blocks-owned-cycle', value(f, 'z7_info_probe_cycles') == before and not f.events)
    f.gates, f.results[0x102c7426] = {0x2a: 1, 2: 0}, 1
    for name, address, incoming in (
        ('first-filter', 0x103ebe0c, None), ('second-filter', 0x103ebe3c, None),
        ('final-filter', 0x103ebed8, None), ('first-exclusion', 0x10297a2e, None),
        ('second-exclusion', 0x10297a16, None), ('state2', None, 2), ('state5', None, 5)):
        saved = f.results.get(address)
        if address:
            f.results[address] = 1
        if incoming is not None:
            f.u.mem_write(INFO + 0x2d, bytes([incoming]))
        before = value(f, 'z7_info_probe_cycles')
        f.invoke(0x102fd646)
        check(name + '-native-admission-blocks-owned-cycle', value(f, 'z7_info_probe_cycles') == before and not f.events)
        if address:
            f.results[address] = saved
        f.u.mem_write(INFO + 0x2d, b'\0')
    wrapper = report['symbols']['z7_information_update_bridge']
    for flags in (0, 0x28000000, 0x50000000, 0xf8000000):
        original = InformationHostFixture(stock, report, b'')
        absent = InformationHostFixture(raw, report, b'')
        for g in (original, absent, f):
            context(g)
        expected = original.invoke(0x102fda08, key=0x1234, flags=flags)
        check(f'absent-update-{flags:x}-original-result-abi', absent.invoke(wrapper, key=0x1234, flags=flags) == expected)
        before = value(f, 'z7_info_probe_updates')
        check(f'owned-update-{flags:x}-original-result-abi', f.invoke(wrapper, key=0x1234, flags=flags) == expected)
        check(f'owned-update-{flags:x}-original-entry-registers', f.native_updates == original.native_updates == absent.native_updates)
        check(f'owned-update-{flags:x}-once', value(f, 'z7_info_probe_updates') == before + 1)
    configure(f, 'z7_info_probe_cycle_dispatch', report['symbols']['z7_display_information_cycle'])
    configure(f, 'z7_info_probe_recurse_cycle', 1)
    before = value(f, 'z7_info_probe_cycles')
    f.call(report['symbols']['z7_display_information_cycle'])
    check('nested-cycle-suppressed-and-guard-released', value(f, 'z7_info_probe_cycles') == before + 1 and f.words()[47] == 0)
    configure(f, 'z7_info_probe_recurse_update', 1)
    before = value(f, 'z7_info_probe_updates')
    f.invoke(wrapper)
    check('nested-update-keeps-native-body-and-suppresses-module-reentry',
          len(f.native_updates) == 2 and value(f, 'z7_info_probe_updates') == before + 1 and f.words()[48] == 0)
    configure(f, 'z7_info_probe_leave', 1)
    f.invoke(wrapper)
    check('callback-leaving-app-skips-stale-native-update', not f.native_updates and f.u.mem_read(0xa1829af4, 1) == b'\0' and f.words()[48] == 0)
    configure(f, 'z7_info_probe_leave', 0)
    for name, offset, replacement in (('not-ready', 92, 0), ('no-image', 48, 0), ('bad-guard', 240, 0),
                                      ('cycle-running', 188, 1), ('update-running', 192, 1)):
        context(f)
        saved, before = f.words()[offset // 4], value(f, 'z7_info_probe_cycles')
        f.setword(offset, replacement)
        f.call(report['symbols']['z7_display_information_cycle'])
        updates = value(f, 'z7_info_probe_updates')
        f.invoke(wrapper)
        f.setword(offset, saved)
        check(name + '-skips-owned-cycle', value(f, 'z7_info_probe_cycles') == before)
        check(name + '-update-delegates-unchanged', value(f, 'z7_info_probe_updates') == updates and len(f.native_updates) == 1)
    for name, address, data in (
        ('foreign-key', APP + 0x14, bytes(4)), ('foreign-event', APP + 0x18, bytes(4)),
        ('foreign-update', APP + 0x1c, bytes(4)), ('other-app', 0xa1829af4, b'\0'),
        ('foreign-registry', TABLE + 13 * 4, bytes(4))):
        context(f)
        saved = bytes(f.u.mem_read(address, len(data)))
        f.u.mem_write(address, data)
        cycles, updates = value(f, 'z7_info_probe_cycles'), value(f, 'z7_info_probe_updates')
        f.call(report['symbols']['z7_display_information_cycle'])
        f.invoke(wrapper)
        check(name + '-skips-owned-callbacks-and-delegates-native-update',
              value(f, 'z7_info_probe_cycles') == cycles and value(f, 'z7_info_probe_updates') == updates and len(f.native_updates) == 1)
        check(name + '-foreign-state-not-overwritten', bytes(f.u.mem_read(address, len(data))) == data)
        f.u.mem_write(address, saved)
    for name, foreign in (('information-failure', None), ('information-success', APP + 0x14),
                           ('information-success', APP + 0x18), ('information-success', APP + 0x1c)):
        failed, status = load(name, foreign=foreign)
        check(name + '-failure-' + str(foreign) + '-clears-publication',
              status == 7 and failed.words()[43:49] == (0,) * 6 and not failed.words()[23] and not failed.live)
    old = json.loads((legacy / 'module-host.emulator.json').read_text(encoding='utf-8'))
    failed, status = load(host=old, image=(legacy / 'module-host.emulator.main.bin').read_bytes())
    check('legacy-api32-rejects-api40-module', status == 7 and not failed.live)
    return dict(passed=True, checks=checks, api_bytes=40, state_bytes=256,
                main_sha256=report['main_payload_sha256'], original_key_admission_executes=True,
                delegated_prefix_register_stack_lr_flags_verified=True,
                supplied_boundaries=['Loader/kernel/filesystem/heap', 'Incoming app/registry/snapshot state',
                                     'Named native key service returns and parent request sink',
                                     'Original information-update body return/register/flag sink'],
                custom_information_page_implemented=False, actual_pixels=False, camera_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--modules', type=Path, required=True)
    p.add_argument('--legacy-build', type=Path, required=True)
    p.add_argument('--stock-main', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    output = a.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists():
        p.error('Choose a new private output')
    result = audit((a.build / 'module-host.emulator.main.bin').read_bytes(),
                   json.loads((a.build / 'module-host.emulator.json').read_text(encoding='utf-8')),
                   a.stock_main.read_bytes(), a.modules, a.legacy_build)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__':
    main()
