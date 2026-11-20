"""Execute compiled original-Z7 transition ledger and native page/request APIs.

SPDX-License-Identifier: MIT. Manager app publication/initialization and property
services are supplied. No rendered pixels, overlay cleanup or camera acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1
from audit_z7_information_host import InformationHostFixture
from audit_z7_information_native import APP, TABLE, SNAPSHOT, INFO
from build_z7_module_host import ROOT, STATE


class TransitionFixture(InformationHostFixture):
    def __init__(self, *args):
        super().__init__(*args)
        self.store_plan = []
        self.parent_return = 0
        self.forbidden_writes = []

    def hook(self, u, address, size, context):
        if address == 0x1030d510:
            self.events.append([u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)])
            self.ret(self.parent_return)
        elif address == 0x104065b0 and self.store_plan:
            key, value = u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)
            result, publish = self.store_plan.pop(0)
            self.stores.append([key, value])
            if publish:
                self.properties[key] = value
            self.ret(result)
        else:
            super().hook(u, address, size, context)


def audit(raw, host, packet, module):
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Host/module fingerprint mismatch')
    checks, fixtures = [], []

    def check(name, condition):
        checks.append(dict(name=name, passed=bool(condition)))
        if not condition:
            raise AssertionError(name)

    def setup(page=0):
        f = TransitionFixture(raw, host, packet)
        check('module-load-' + str(len(fixtures)), f.call(host['symbols']['z7_module_load_once'], STATE) == 8)
        f.base = f.words()[12]
        f.operation = f.base + module['symbols']['z7_information_operation']
        f.ledger = f.base + module['symbols']['z7_information_ledger']
        check('init-does-not-request-or-store-' + str(len(fixtures)), not any(isinstance(e, list) and e[0] == 4 for e in f.events) and not f.stores)
        f.events.clear()
        f.prefix(0x1030cf74, 0x1030d00a, 0x1030d511)
        f.call(0x10376440, 0xa1829af8, 0x1030d511, 0)
        f.call(0x10376440, APP, 0x1030d511, 13)
        f.u.mem_write(0xa1829af4, b'\0')
        f.properties[0x2f15] = page
        f.u.mem_write(SNAPSHOT + 0x18a, bytes([page]))
        f.u.mem_write(INFO, bytes(256))
        f.forbidden_writes.clear()
        fixtures.append(f)
        return f

    def ledger(f):
        return struct.unpack('<5I', f.u.mem_read(f.ledger, 20))

    def op(f, operation=0, saved=0, released=1):
        before = (bytes(f.u.mem_read(0xa1829af4, 1)), bytes(f.u.mem_read(TABLE, 24 * 4)))
        result = f.call(f.operation, operation, saved, released)
        after = (bytes(f.u.mem_read(0xa1829af4, 1)), bytes(f.u.mem_read(TABLE, 24 * 4)))
        if before != after:
            f.forbidden_writes.append((before, after))
        return result

    def native_app(f, index, page):
        # Explicit fixture boundary: actual manager/app initialization does not
        # execute here. Native production helper never writes these addresses.
        f.u.mem_write(0xa1829af4, bytes([index]))
        f.u.mem_write(SNAPSHOT + 0x18a, bytes([page]))
        f.properties[0x2f15] = page

    for saved in range(4):
        f = setup(saved)
        check(f'entry-{saved}-request-only-after-page4', op(f, saved=saved) == 2 and
              f.events == [[4, 0x108000]] and f.properties[0x2f15] == 4 and
              bytes(f.u.mem_read(SNAPSHOT + 0x18a, 1)) == b'\4' and ledger(f)[:3] == (1, saved, saved))
        check(f'entry-{saved}-delayed-request-not-completed', op(f, 1) == 0 and ledger(f)[0] == 1)
        before = (list(f.events), list(f.stores), ledger(f))
        check(f'entry-{saved}-duplicate-keeps-ledger', op(f, saved=0) == 0 and
              before == (f.events, f.stores, ledger(f)))
        native_app(f, 13, 4)
        check(f'entry-{saved}-observed-app13', op(f, 1) == 0 and ledger(f)[0] == 2)
        check(f'entry-{saved}-exit-admission-recorded', op(f, 2) == 1 and ledger(f)[0] == 3)
        check(f'entry-{saved}-duplicate-exit-no-change', op(f, 2) == 0 and ledger(f)[0] == 3)
        f.events.clear(); f.stores.clear()
        f.call(0x102fd646, 0x29)
        check(f'entry-{saved}-original-native-exit-executes', f.events == [[4, 0x100000]] and
              f.properties[0x2f15] == 0 and f.stores == [[0x2f15, 0]])
        before = list(f.stores)
        check(f'entry-{saved}-partial-native-exit-retains-ledger', op(f, 1) == 0 and
              ledger(f)[0] == 3 and f.stores == before)
        # Native manager return/app startup supplies the shooting snapshot.
        native_app(f, 0, 0)
        check(f'entry-{saved}-restores-original-user-page', op(f, 1) == 1 and ledger(f)[0] == 0 and
              f.properties[0x2f15] == saved and f.u.mem_read(SNAPSHOT + 0x18a, 1) == bytes([saved]) and
              ledger(f)[1] == saved)
        before = list(f.stores)
        check(f'entry-{saved}-idle-does-not-repeat-restore', op(f, 1) == 0 and f.stores == before)

    f = setup(0)
    check('custom-applied-page0-keeps-user-page3', op(f, saved=3) == 2 and ledger(f)[1:3] == (3, 0))
    native_app(f, 13, 4); op(f, 1); op(f, 2)
    native_app(f, 0, 0)
    check('intermediate-return0-never-resaved-as-baseline', op(f, 1) == 1 and
          ledger(f)[1] == 3 and f.properties[0x2f15] == 3)
    f = setup(3)
    native_app(f, 13, 4)
    check('unowned-information-app-never-records-exit', op(f, 2) == 0 and ledger(f) == (0,) * 5 and
          not f.events and not f.stores)
    f = setup(3); op(f, saved=1); native_app(f, 13, 4); op(f, 1)
    native_app(f, 0, 0); f.display = 4; before = list(f.stores)
    check('alternate-output-defers-return-restore', op(f, 1) == 0 and ledger(f)[0] == 2 and f.stores == before)
    f.display = 1
    check('eligible-output-restores-original-ledger', op(f, 1) == 1 and f.properties[0x2f15] == 1)
    for address in (APP + 0x14, APP + 0x18, TABLE + 13 * 4):
        f = setup(3); op(f, saved=1); native_app(f, 13, 4)
        f.u.mem_write(address, bytes(4)); before = list(f.stores)
        check('foreign-active-binding-' + hex(address) + '-rejects-exit', op(f, 2) == 0 and f.stores == before)
        check('foreign-active-binding-' + hex(address) + '-blocks-observation', op(f, 1) == 0 and
              ledger(f)[0] == 5 and f.stores == before and bytes(f.u.mem_read(address, 4)) == bytes(4))

    for name, change, saved, released in (
        ('unreleased-overlays', None, 3, 0), ('invalid-saved', None, 4, 1),
        ('foreign-app', (0xa1829af4, b'\15'), 3, 1),
        ('foreign-shooting-registry', (TABLE, bytes(4)), 3, 1),
        ('foreign-information-registry', (TABLE + 13 * 4, bytes(4)), 3, 1),
        ('foreign-key', (0xa1829b0c, bytes(4)), 3, 1),
        ('foreign-event', (0xa1829b10, bytes(4)), 3, 1),
        ('foreign-information-key', (APP + 0x14, bytes(4)), 3, 1),
        ('foreign-information-event', (APP + 0x18, bytes(4)), 3, 1),
        ('missing-parent', (0xa1829af8, bytes(4)), 3, 1),
        ('even-parent', (0xa1829af8, struct.pack('<I', 0x1030d510)), 3, 1),
        ('ram-parent', (0xa1829af8, struct.pack('<I', 0xa1820001)), 3, 1)):
        f = setup(3)
        if change:
            f.u.mem_write(*change)
        check(name + '-no-native-mutation', op(f, saved=saved, released=released) == 0 and
              not f.events and not f.stores and ledger(f) == (0,) * 5 and f.properties[0x2f15] == 3)
        if change:
            check(name + '-foreign-bytes-preserved', bytes(f.u.mem_read(change[0], len(change[1]))) == change[1])

    for name, configure in (
        ('movie', lambda f: f.properties.update({0x138d: 1})),
        ('alternate-output', lambda f: setattr(f, 'display', 4)),
        ('snapshot-property-disagreement', lambda f: f.properties.update({0x2f15: 2})),
        ('native-information-already-selected', lambda f: native_app(f, 0, 4))):
        f = setup(3); configure(f)
        check(name + '-rejects-without-write', op(f, saved=3) == 0 and not f.events and not f.stores)

    for plan in ([(0, False), (1, True)], [(0, True), (1, True)], [(1, False), (1, True)]):
        f = setup(3); f.store_plan = list(plan)
        check('failed-publish-' + str(plan) + '-rolls-back-before-request', op(f, saved=1) == 0 and
              not f.events and f.properties[0x2f15] == 3 and ledger(f)[0] == 0 and
              f.u.mem_read(SNAPSHOT + 0x18a, 1) == b'\3')
    f = setup(3); f.store_plan = [(0, False), (0, False)]
    check('failed-rollback-retains-recovery-ledger', op(f, saved=1) == 0 and ledger(f)[0] == 4 and not f.events)
    check('rollback-retries-original-entry-page', op(f, 1) == 1 and ledger(f)[0] == 0 and
          f.properties[0x2f15] == 3 and f.u.mem_read(SNAPSHOT + 0x18a, 1) == b'\3')
    f = setup(3); f.store_plan = [(0, False), (0, False)]
    op(f, saved=1); native_app(f, 0, 2); before = list(f.stores)
    check('foreign-during-recovery-is-preserved', op(f, 1) == 0 and ledger(f)[0] == 5 and
          f.properties[0x2f15] == 2 and f.stores == before)
    f = setup(3); op(f, saved=1); native_app(f, 13, 4); op(f, 1)
    native_app(f, 0, 0); f.store_plan = [(0, False)]
    check('failed-return-restoration-keeps-original-ledger', op(f, 1) == 0 and ledger(f)[0] == 4 and
          ledger(f)[1] == 1 and f.properties[0x2f15] == 0)
    check('return-restoration-retries-saved-user-page', op(f, 1) == 1 and f.properties[0x2f15] == 1)
    for foreign in (1, 2, 3):
        f = setup(3); op(f, saved=1); native_app(f, 13, 4); op(f, 1)
        native_app(f, 0, foreign); before = list(f.stores)
        check('foreign-return-page-' + str(foreign) + '-never-overwritten', op(f, 1) == 0 and
              ledger(f)[0] == 5 and f.properties[0x2f15] == foreign and f.stores == before)
    f = setup(3); f.parent_return = 0xffffffff
    check('parent-return-is-not-transition-success', op(f, saved=1) == 2 and ledger(f)[0] == 1 and
          op(f, 1) == 0 and ledger(f)[0] == 1)
    native_app(f, 2, 0); before = list(f.stores)
    check('unrelated-app-delays-without-writes', op(f, 1) == 0 and f.stores == before and ledger(f)[1] == 1)
    native_app(f, 0, 0)
    check('rejected-entry-native-return-restores-baseline', op(f, 1) == 1 and f.properties[0x2f15] == 1)
    f = setup(3); op(f, saved=1); native_app(f, 13, 4); op(f, 1)
    f.store_plan = [(0, False)]
    check('settings-exit-failed-publish-does-not-request', op(f, 3) == 0 and ledger(f)[0] == 6 and
          f.events == [[4, 0x108000]] and f.properties[0x2f15] == 4)
    check('settings-exit-can-retry-verified-property', op(f, 3) == 1 and ledger(f)[0] == 7 and
          f.events[-1:] == [[4, 0x100000]] and f.properties[0x2f15] == 0)
    before = (list(f.events), list(f.stores))
    check('settings-exit-pending-does-not-repeat', op(f, 1) == 0 and op(f, 3) == 0 and
          ledger(f)[0] == 7 and (f.events, f.stores) == before)
    native_app(f, 0, 4, )
    f.properties[0x2f15] = 0
    check('manager-switch-before-snapshot-return-remains-pending', op(f, 1) == 0 and ledger(f)[0] == 7)
    native_app(f, 0, 0)
    check('settings-exit-restores-original-page', op(f, 1) == 1 and f.properties[0x2f15] == 1)
    for state in (2, 5):
        f = setup(3); op(f, saved=1); native_app(f, 13, 4); op(f, 1)
        f.u.mem_write(INFO + 0x2d, bytes([state])); before = (list(f.events), list(f.stores))
        check('settings-exit-defers-native-state-' + str(state), op(f, 3) == 0 and ledger(f)[0] == 2 and
              (f.events, f.stores) == before)
    f = setup(3); op(f, saved=1); native_app(f, 13, 4); op(f, 1)
    f.store_plan = [(0, True)]
    check('failed-settings-exit-can-have-published-property0', op(f, 3) == 0 and ledger(f)[0] == 6 and
          f.properties[0x2f15] == 0 and f.events == [[4, 0x108000]])
    native_app(f, 13, 0)
    check('settings-exit-retries-after-native-snapshot-follows-owned-property0', op(f, 1) == 0 and
          ledger(f)[0] == 6 and op(f, 3) == 1 and f.events[-1:] == [[4, 0x100000]])
    native_app(f, 0, 0)
    check('partial-settings-exit-restores-original-user-page', op(f, 1) == 1 and f.properties[0x2f15] == 1)
    check('application-and-registry-unchanged-across-all-helper-calls', all(not f.forbidden_writes for f in fixtures))
    return dict(passed=True, checks=checks, main_sha256=host['main_payload_sha256'],
                module_sha256=module['module_sha256'], native_setter_getter_request_and_exit_execute=True,
                supplied_boundaries=['Incoming app/registry/snapshots', 'Property services and parent request sink',
                                     'Native manager publication and application initialization', 'Loader/kernel/heap/filesystem'],
                overlay_release_verified=False, custom_five_choice_routing_implemented=False,
                actual_pixels=False, camera_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--module', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if not a.output.resolve().is_relative_to(ROOT / '.private') or a.output.exists():
        p.error('Choose a new private output')
    result = audit((a.build / 'module-host.emulator.main.bin').read_bytes(),
                   json.loads((a.build / 'module-host.emulator.json').read_text(encoding='utf-8')),
                   (a.module / 'Z7APP.BIN').read_bytes(),
                   json.loads((a.module / 'module.json').read_text(encoding='utf-8')))
    a.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__':
    main()
