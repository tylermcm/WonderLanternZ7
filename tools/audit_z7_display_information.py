"""Execute full display module five-choice routing and native Info key exit.

SPDX-License-Identifier: MIT. Property, parent request and app publication are
supplied boundaries. Actual native setters/key admission execute; no pixels or
complete application initialization are claimed by this instruction fixture.
"""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1
from audit_z7_focal_overlay import FocalOverlayFixture
from audit_z7_information_native import APP, TABLE, INFO, SNAPSHOT
from build_z7_module_host import ROOT, STATE


class DisplayInformationFixture(FocalOverlayFixture):
    def __init__(self, *args):
        super().__init__(*args)
        self.requests = []
        self.monitor = 1
        for address in (0x1040a4ae, 0x10371100, 0x10333e1a, 0x10301214,
                        0x10406282, 0x104063ea, 0x10406248, 0x1037105e,
                        0x103244f6, 0x103fa7ba, 0x103fad9c, 0x1030236a):
            self.results.setdefault(address, 0)
        self.write(TABLE, 0xa1829af8)
        self.write(TABLE + 13 * 4, APP)
        self.write(APP, 0x1030d511)
        self.write(APP + 4, 13)
        self.u.mem_write(INFO, bytes(256))
        self.u.mem_write(0xa1829af4, b'\0')

    def hook(self, u, address, size, context):
        if address == 0x1030d510:
            self.requests.append((u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)))
            self.ret(0)
        elif address == 0x103fec18:
            self.ret(self.monitor)
        elif address == 0x103ea09e and u.reg_read(UC_ARM_REG_R0) in (0x2a, 2):
            # HistogramFixture supplies other gate IDs for its painter. Native
            # DISP eligibility must use the CycleFixture's independently set gates.
            self.ret(self.gates.get(u.reg_read(UC_ARM_REG_R0), 0))
        else:
            super().hook(u, address, size, context)


def audit(raw, host, packet, module, fixture_class=None):
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Host/module fingerprint mismatch')
    checks = []
    symbols = module['symbols']
    fixture_class = fixture_class or DisplayInformationFixture

    def check(name, condition):
        checks.append(dict(name=name, passed=bool(condition)))
        if not condition:
            raise AssertionError(name)

    def load(native=3):
        # Retire unreachable emulator/hook cycles before allocating another
        # complete firmware fixture. Existing live fixtures remain referenced.
        gc.collect()
        f = fixture_class(raw, host, packet)
        check('full-module-load-' + str(len(checks)), f.call(host['symbols']['z7_module_load_once'], STATE) == 8)
        f.base = f.words()[12]
        f.model = f.base + symbols['z7_menu_settings']
        f.focal_object_global, f.focal_renderer = f.base + symbols['z7_focal_object'], f.base + symbols['focal_painter']
        f.properties[0x2f15] = native
        f.u.mem_write(SNAPSHOT + 0x18a, bytes([native]))
        for preset in range(4):
            for bit in (1, 2):
                setting(f, 'component', preset, bit, 0)
        setting(f, 'page', 4, 1)
        return f

    def setting(f, name, *args):
        result = f.call(f.base + symbols['z7_settings_' + name], f.model, *args)
        if result != 1:
            raise AssertionError('Settings ' + name + ': ' + str(args))

    def word(f, name):
        return f.read(f.base + symbols[name])

    def ledger(f):
        return struct.unpack('<5I', f.u.mem_read(f.base + symbols['z7_information_ledger'], 20))

    def before(f):
        f.call(host['symbols']['z7_display_before_update'])

    def after(f):
        f.u.mem_write(0xa201d80c, bytes(f.u.mem_read(SNAPSHOT, 0x33c)))
        f.call(host['symbols']['z7_display_after_gui_update'])

    def info_before(f):
        f.call(host['symbols']['z7_display_before_information_update'])

    def native_app(f, app, page, property=None):
        f.u.mem_write(0xa1829af4, bytes([app]))
        f.u.mem_write(SNAPSHOT + 0x18a, bytes([page]))
        f.properties[0x2f15] = page if property is None else property

    def masks(f):
        return [bytes(f.u.mem_read(f.read(0x1064d610 + i * 4) + 4, 36)) for i in range(61)]

    def enter(f):
        for unused in range(4):
            f.call(0x1030da56, 0x29)
            if word(f, 'z7_information_pending'):
                break
            before(f)
        before(f); after(f)
        check('entry-requests-native-app13-' + str(len(checks)), f.requests[-1:] == [(4, 0x108000)] and ledger(f)[0] == 1)
        native_app(f, 13, 4); info_before(f)

    f = load()
    check('api40-information-and-full-existing-hooks-published', f.words()[39] == f.words()[41] == f.words()[44] == f.words()[46] == 1)
    original = masks(f)
    setting(f, 'flag', 0, 1); before(f)
    check('enabling-information-keeps-preset0-and-user-page3', word(f, 'z7_base_saved') == 3 and
          word(f, 'z7_base_active') == 1 and f.properties[0x2f15] == 0)
    for expected in (1, 2, 3):
        f.call(0x1030da56, 0x29); before(f)
        check('actual-admitted-shooting-key-to-' + str(expected), word(f, 'z7_readout_preset') == expected and not f.requests)
    f.call(0x1030da56, 0x29)
    check('fifth-choice-is-deferred-until-component-release', word(f, 'z7_information_pending') == 1 and not f.requests and word(f, 'z7_readout_preset') == 3)
    before(f)
    check('entry-releases-all-native-masks-and-base', masks(f) == original and not word(f, 'z7_base_active') and
          not word(f, 'z7_readout_active') and f.properties[0x2f15] == 3)
    after(f)
    check('entry-preserves-baseline-and-observes-asynchronous-manager', f.requests == [(4, 0x108000)] and
          ledger(f)[:3] == (1, 3, 3) and word(f, 'z7_readout_preset') == 3)
    native_app(f, 13, 4); info_before(f)
    check('logical-information-only-after-native-app-observed', word(f, 'z7_readout_preset') == 4 and ledger(f)[0] == 2 and masks(f) == original)
    requests = list(f.requests); cycles = word(f, 'z7_preset_cycles')
    for state in (2, 5):
        f.u.mem_write(INFO + 0x2d, bytes([state])); f.call(0x102fd646, 0x29)
        check('native-information-state-' + str(state) + '-blocks-custom-exit', f.requests == requests and
              word(f, 'z7_preset_cycles') == cycles and ledger(f)[0] == 2)
    f.u.mem_write(INFO + 0x2d, b'\0')
    f.call(0x102fd646, 0x29)
    check('original-admitted-information-key-exits-to-preset0', f.requests[-1:] == [(4, 0x100000)] and
          ledger(f)[0] == 3 and word(f, 'z7_information_target') == 0 and f.properties[0x2f15] == 0)
    info_before(f)
    check('property-cleared-before-app-switch-remains-pending', ledger(f)[0] == 3 and word(f, 'z7_readout_preset') == 4)
    native_app(f, 0, 0); before(f)
    check('native-return-restores-user-baseline-before-reacquiring-preset0', ledger(f)[0] == 0 and
          word(f, 'z7_readout_preset') == 0 and word(f, 'z7_base_saved') == 3 and word(f, 'z7_base_active') == 1)
    setting(f, 'flag', 0, 0); before(f)
    check('master-off-restores-original-page3-and-all61-masks', f.properties[0x2f15] == 3 and
          f.u.mem_read(SNAPSHOT + 0x18a, 1) == b'\3' and masks(f) == original)

    f = load(); original = masks(f)
    for preset in range(4):
        setting(f, 'page', preset, 0)
    setting(f, 'flag', 0, 1); before(f); after(f)
    check('information-only-config-reselects-and-enters', f.requests == [(4, 0x108000)] and masks(f) == original)
    native_app(f, 13, 4); info_before(f); before_requests = list(f.requests)
    f.call(0x102fd646, 0x29)
    check('information-only-native-disp-keeps-page-without-exit', word(f, 'z7_readout_preset') == 4 and f.requests == before_requests and f.properties[0x2f15] == 4)
    setting(f, 'flag', 0, 0); info_before(f)
    check('master-off-native-info-uses-verified-native-return-request', ledger(f)[0] == 7 and f.requests[-1:] == [(4, 0x100000)] and f.properties[0x2f15] == 0)
    before_requests = list(f.requests); info_before(f)
    check('delayed-settings-return-never-repeats-request', f.requests == before_requests and ledger(f)[0] == 7)
    native_app(f, 0, 0); before(f)
    check('information-only-master-off-restores-original-user-page', f.properties[0x2f15] == 3 and ledger(f)[0] == 0 and masks(f) == original and not word(f, 'z7_base_active'))

    f = load(); setting(f, 'flag', 0, 1); before(f); enter(f)
    setting(f, 'page', 4, 0); info_before(f)
    check('disabled-current-information-requests-native-return', f.requests[-1:] == [(4, 0x100000)] and ledger(f)[0] == 7)
    native_app(f, 0, 0); before(f)
    check('disabled-current-information-reselects-preset0', word(f, 'z7_readout_preset') == 0 and word(f, 'z7_base_saved') == 3)
    check('native-key-event-bindings-remain-original', f.read(0xa1829b0c) == 0x1030da57 and f.read(APP + 0x14) == 0x102fd647 and f.read(APP + 0x18) == 0x102fdaef)

    f = load(); original = masks(f)
    setting(f, 'information', 0, 7, 1); setting(f, 'flag', 0, 1); before(f); after(f)
    focal = word(f, 'z7_focal_object')
    check('focal-overlay-draws-with-information-choice-enabled', focal != 0 and word(f, 'z7_focal_paints') > 0 and
          word(f, 'z7_focal_presents') > 0)
    for preset in (1, 2, 3, 4):
        f.call(0x1030da56, 0x29)
        # Deliberately postpone native painting until the information choice.
        before(f)
    after(f)
    check('pending-retired-focal-painter-blocks-information-entry', word(f, 'focal_retire') == 1 and
          word(f, 'z7_information_pending') == 1 and not f.requests and masks(f) == original)
    f.call(f.base + symbols['focal_painter'], focal, 0, 0, 0)
    check('compiled-focal-painter-completes-own-retirement', word(f, 'focal_retire') == 0 and f.read(focal + 0x28) == 0)
    for state in (2, 5, 11):
        f.u.mem_write(SNAPSHOT, bytes([state])); after(f)
        check('deferred-entry-rechecks-native-state-' + str(state), not f.requests and word(f, 'z7_information_pending') == 1)
    f.u.mem_write(SNAPSHOT, b'\0')
    f.gates = {0x2a: 0, 2: 1}; after(f)
    check('deferred-entry-rechecks-native-secondary-gate', not f.requests and word(f, 'z7_information_pending') == 1)
    f.gates = {0x2a: 1, 2: 0}
    after(f)
    check('information-entry-follows-actual-owned-painter-retirement', f.requests == [(4, 0x108000)] and ledger(f)[0] == 1)

    f = load(); original = masks(f); setting(f, 'flag', 0, 1); before(f)
    for unused in range(4):
        f.call(0x1030da56, 0x29); before(f)
    f.setter_results = [(0, False), (1, True)]
    after(f)
    check('failed-entry-publication-rolls-back-without-request', not f.requests and ledger(f)[0] == 0 and
          f.properties[0x2f15] == 3 and masks(f) == original and word(f, 'z7_information_errors') == 1)
    before(f); after(f)
    check('failed-entry-does-not-loop-on-subsequent-gui-updates', not f.requests and word(f, 'z7_information_errors') == 1)
    setting(f, 'flag', 0, 0); before(f)
    check('master-off-acknowledges-failed-entry-with-baseline-intact', not word(f, 'z7_information_suspended') and
          f.properties[0x2f15] == 3 and masks(f) == original)

    f = load(); setting(f, 'flag', 0, 1); before(f)
    for unused in range(4):
        f.call(0x1030da56, 0x29); before(f)
    f.setter_results = [(0, False), (0, False)]; after(f)
    check('partial-entry-retains-recovery-and-fault', ledger(f)[0] == 4 and not f.requests and word(f, 'z7_information_errors') == 1)
    before(f)
    check('recovered-entry-failure-keeps-components-suspended', ledger(f)[0] == 0 and
          word(f, 'z7_information_suspended') == 1 and not word(f, 'z7_base_active') and not f.requests)

    f = load(); setting(f, 'flag', 0, 1); before(f); enter(f)
    setting(f, 'flag', 0, 0); requests = list(f.requests)
    f.write(0xa2c41008, 1); info_before(f)
    check('settings-exit-defers-until-native-menu-leaves', f.requests == requests and ledger(f)[0] == 2)
    f.write(0xa2c41008, 0)
    for state in (2, 5):
        f.u.mem_write(INFO + 0x2d, bytes([state])); info_before(f)
        check('settings-exit-defers-info-state-' + str(state), f.requests == requests and f.properties[0x2f15] == 4)
    f.u.mem_write(INFO + 0x2d, b'\0'); f.monitor = 3; info_before(f)
    check('settings-exit-defers-special-monitor-route', f.requests == requests and ledger(f)[0] == 2)
    f.monitor = 1; info_before(f)
    check('settings-exit-requests-once-after-native-gates-clear', f.requests == requests + [(4, 0x100000)] and ledger(f)[0] == 7)
    f = load(); setting(f, 'flag', 0, 1); before(f)
    for unused in range(3):
        f.call(0x1030da56, 0x29); before(f)
    f.call(0x1030da56, 0x29)
    mask_address = f.read(0x1064d610 + 10 * 4) + 4
    foreign = f.read(mask_address) ^ 0x80000000
    f.write(mask_address, foreign); before(f); after(f)
    check('foreign-mask-during-retirement-prevents-information-entry', not f.requests and
          f.read(mask_address) == foreign and word(f, 'z7_information_errors') == 1 and
          not word(f, 'z7_information_pending'))
    setting(f, 'flag', 0, 0); before(f)
    check('master-off-preserves-foreign-mask-without-transition', not f.requests and f.read(mask_address) == foreign)
    legacy = ROOT / '.private/builds/20261119-display-host-07'
    old = json.loads((legacy / 'module-host.emulator.json').read_text(encoding='utf-8'))
    f = fixture_class((legacy / 'module-host.emulator.main.bin').read_bytes(), old, packet)
    check('api32-host-rejects-full-information-profile-before-native-menu-preparation',
          f.call(old['symbols']['z7_module_load_once'], STATE) == 7 and not f.live and not f.labels and not f.words()[23])
    return dict(passed=True, checks=checks, main_sha256=host['main_payload_sha256'], module_sha256=module['module_sha256'],
                full_focal_other_histogram_profile=True, native_key_admission_and_exit_execute=True,
                supplied_boundaries=['Incoming GUI/lens/native application state', 'Property and parent request services',
                                     'Native manager/app initialization', 'Loader/filesystem/heap', 'Render and presentation services'],
                actual_pixels=False, camera_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--module', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--persistence-transport', action='store_true', help='Supply separate journal files for the API44 persistent profile')
    a = p.parse_args()
    if not a.output.resolve().is_relative_to(ROOT / '.private') or a.output.exists():
        p.error('Choose a new private output')
    fixture_class = None
    if a.persistence_transport:
        from audit_z7_display_persistence import PersistenceFixture
        fixture_class = PersistenceFixture
    result = audit((a.build / 'module-host.emulator.main.bin').read_bytes(),
                   json.loads((a.build / 'module-host.emulator.json').read_text(encoding='utf-8')),
                   (a.module / 'Z7APP.BIN').read_bytes(), json.loads((a.module / 'module.json').read_text(encoding='utf-8')), fixture_class)
    result['separate_settings_files_transport'] = bool(a.persistence_transport)
    a.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__':
    main()
