"""Bind original-Z7 information-app entry, selection and native DISP admission.

SPDX-License-Identifier: MIT. Native registry/getters, cycle/key handlers and
the manager's selection prefix execute. Property, admission, parent requests
and rendering services are supplied. No app initialization or pixels claimed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC
from audit_splash_image import NativePNG, STOCK_SHA, MEM, STACK, STOP
from build_z7_module_host import ROOT

APP, TABLE, STATE = 0xa182d16c, 0xa20207bc, 0xa1829af4
SNAPSHOT, INFO = 0xa201d4d0, 0xa20210c0
CALLBACK = MEM + 0x60000


class InformationFixture(NativePNG):
    def __init__(self, raw, fail_allocation=0):
        super().__init__(raw, fail_allocation=fail_allocation)
        self.u.mem_map(0xa2010000, 0x20000)
        self.properties = {0x138d: 0, 0x2f15: 4, 0x2f16: 4,
                           0x2f17: 4, 0x2f18: 4}
        self.display, self.monitor = 1, 1
        self.gates = {0x2a: 1, 2: 0}
        self.events, self.stores, self.stop_at = [], [], None
        self.store_result = 1
        self.results = {address: 0 for address in (
            0x103ebe0c, 0x103ebe3c, 0x10297654, 0x103ebed8,
            0x10297a2e, 0x10297a16, 0x1040a4ae, 0x10371100,
            0x10333e1a, 0x10301214, 0x10406282, 0x104063ea,
            0x10406248, 0x1037105e, 0x103244f6, 0x103fa7ba,
            0x103fad9c, 0x1030236a)}
        self.results[0x102c7426] = 1

    def hook(self, u, address, size, context):
        if address == self.stop_at:
            u.emu_stop()
        elif address == 0x104065a4:
            key = u.reg_read(UC_ARM_REG_R0)
            if key not in self.properties:
                raise AssertionError('Unspecified property boundary: ' + hex(key))
            self.ret(self.properties[key])
        elif address == 0x104065b0:
            key, value = u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)
            self.stores.append([key, value])
            if self.store_result:
                self.properties[key] = value
            self.ret(self.store_result)
        elif address == 0x103fef80:
            self.ret(self.display)
        elif address == 0x103fec18:
            self.ret(self.monitor)
        elif address == 0x103ea09e:
            self.ret(self.gates.get(u.reg_read(UC_ARM_REG_R0), 0))
        elif address in self.results:
            self.ret(self.results[address])
        elif address == CALLBACK:
            self.events.append([u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)])
            self.ret(0)
        else:
            super().hook(u, address, size, context)

    def prefix(self, function, stop, argument):
        # Explicit non-returning prefix boundary; not a completed app switch.
        self.stop_at = stop
        self.u.reg_write(UC_ARM_REG_R0, argument)
        self.u.reg_write(UC_ARM_REG_SP, STACK)
        self.u.reg_write(UC_ARM_REG_LR, STOP | 1)
        self.u.emu_start(function | 1, STOP, timeout=1000000, count=10000)
        self.stop_at = None
        if self.u.reg_read(UC_ARM_REG_PC) != stop:
            raise AssertionError('Native selection prefix did not reach its boundary')


def audit(raw):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA:
        raise ValueError('Exact original-Z7 stock MAIN required')
    f = InformationFixture(raw)
    checks, selections, admissions = [], [], []

    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good:
            raise AssertionError(name)

    check('original-information-getter', f.call(0x102fd528) == APP)
    check('original-information-key-slot', int.from_bytes(f.u.mem_read(APP + 0x14, 4), 'little') == 0x102fd647)
    check('original-information-update-slot', int.from_bytes(f.u.mem_read(APP + 0x1c, 4), 'little') == 0x102fda09)
    f.prefix(0x1030cf74, 0x1030d00a, CALLBACK | 1)
    check('original-registry-index13-binds-information-descriptor',
          int.from_bytes(f.u.mem_read(TABLE + 13 * 4, 4), 'little') == APP)
    check('original-registry-index15-is-distinct',
          int.from_bytes(f.u.mem_read(TABLE + 15 * 4, 4), 'little') == 0xa182cf00)
    for descriptor, index in ((0xa1829af8, 0), (APP, 13)):
        f.call(0x10376440, descriptor, CALLBACK | 1, index)
        check('native-parent-registration-' + str(index),
              struct.unpack('<2I', f.u.mem_read(descriptor, 8)) == (CALLBACK | 1, index))
    for success in (1, 0):
        f.properties[0x2f15], f.store_result = 3, success
        f.u.mem_write(SNAPSHOT + 0x18a, b'\3')
        f.events, f.stores = [], []
        returned = f.call(0x1037061c)
        check('native-page4-entry-request-store-result-' + str(success),
              returned == 2 and f.events == [[4, 0x108000]] and f.stores == [[0x2f15, 4]] and
              f.u.mem_read(SNAPSHOT + 0x18a, 1) == b'\4')
        check('native-entry-property-result-' + str(success), f.properties[0x2f15] == (4 if success else 3))
    # Selection includes output/movie rejection, but stops before app startup.
    for request in (0x108000, 0x100000):
        for movie in (0, 1):
            for display in (1, 4):
                for page in (0, 4):
                    f.properties = {0x138d: movie, **{key: page for key in range(0x2f15, 0x2f19)}}
                    f.display = display
                    f.u.mem_write(STATE, b'\0')
                    f.prefix(0x1030d1aa, 0x1030d33e, request)
                    selected = f.u.mem_read(STATE, 1)[0]
                    expected = 13 if not movie and display == 1 and request == 0x108000 else 0
                    check(f'native-selection-{request:x}-movie{movie}-display{display}-page{page}', selected == expected)
                    selections.append(dict(request=hex(request), movie=movie, display=display,
                                           page=page, selected_application=selected))
    scenarios = [('admitted', {}, {}, 0, True),
                 ('first-filter', {0x103ebe0c: 1}, {}, 0, False),
                 ('second-filter', {0x103ebe3c: 1}, {}, 0, False),
                 ('final-filter', {0x103ebed8: 1}, {}, 0, False),
                 ('secondary-gate', {}, {0x2a: 0, 2: 1}, 0, False),
                 ('fallback-gate', {0x102c7426: 0}, {0x2a: 0, 2: 0}, 0, False),
                 ('first-exclusion', {0x10297a2e: 1}, {}, 0, False),
                 ('second-exclusion', {0x10297a16: 1}, {}, 0, False),
                 ('snapshot-state2', {}, {}, 2, False),
                 ('snapshot-state5', {}, {}, 5, False)]
    for name, services, gates, state, admitted in scenarios:
        f = InformationFixture(raw)
        f.call(0x10376440, APP, CALLBACK | 1, 13)
        f.results.update(services)
        if gates:
            f.gates = gates
        incoming = bytearray(256)
        incoming[0x2d] = state
        f.u.mem_write(INFO, bytes(incoming))
        f.call(0x102fd646, 0x29)
        check(name + '-original-info-disp-admission',
              f.events == ([[4, 0x100000]] if admitted else []) and
              f.stores == ([[0x2f15, 0]] if admitted else []))
        check(name + '-info-snapshot-read-only', bytes(f.u.mem_read(INFO, len(incoming))) == incoming)
        admissions.append(dict(name=name, admitted=admitted, requests=f.events, stores=f.stores))
    return dict(passed=True, checks=checks, selections=selections, admissions=admissions,
                stock_main_sha256=STOCK_SHA, application_index=13, descriptor=hex(APP),
                key='0x102FD647', update='0x102FDA09', manager_state=hex(STATE), registry=hex(TABLE),
                entry_request='command4/payload108000', return_request='command4/payload100000',
                native_entry_checks_property_write_success=False,
                manager_prefix_boundary='0x1030D33E before final app work/initialization',
                supplied_boundaries=['Property reads/writes and parent request callback',
                                     'Named admission/gate/monitor/output results',
                                     'Incoming GUI snapshots and drawing/refresh sinks'],
                application_initialization_or_pixels_verified=False,
                custom_information_choice_implemented=False, camera_access=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock-main', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists():
        parser.error('Choose a new private output')
    result = audit(args.stock_main.read_bytes())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']),
                         selections=len(result['selections']), admissions=len(result['admissions']))))


if __name__ == '__main__':
    main()
