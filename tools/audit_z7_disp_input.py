"""Original-Z7 shooting-key dispatcher and native DISP admission paths.

SPDX-License-Identifier: MIT. Original dispatch/admission instructions execute;
incoming state and named native service results are explicit fixture boundaries.
No key callback or camera firmware is modified.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1
from audit_splash_image import NativePNG, STOCK_SHA
from build_z7_module_host import ROOT

SERVICES = {
    0x103eb032: 0, 0x103ea626: 0, 0x103fec18: 1, 0x102f6676: 0,
    0x10401d22: 0, 0x104065a4: 0, 0x1041af4c: 1, 0x103fef66: 0,
    0x103ea09e: 0, 0x102c7426: 1, 0x10297a2e: 0, 0x10297a16: 0,
    0x1037061c: 0x100, 0x103ea7b6: 0, 0x1036763c: 0,
    0x10370a90: 0, 0x103ebe0c: 0, 0x103ebe3c: 0, 0x10297654: 0,
    0x103ebed8: 0, 0x1036dc8c: 0, 0x10406282: 0, 0x104063ea: 0,
    0x10406248: 0, 0x103240aa: 0,
}


class DispInput(NativePNG):
    def __init__(self, raw):
        super().__init__(raw)
        self.u.mem_map(0xa2010000, 0x20000)
        self.results = dict(SERVICES)
        self.gates = {0x2a: 1, 2: 0}
        self.events = []

    def hook(self, u, address, size, context):
        if address in self.results:
            r0, r1 = u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)
            self.events.append(dict(function=hex(address), arguments=[r0, r1]))
            self.ret(self.gates.get(r0, 0) if address == 0x103ea09e else self.results[address])
        else:
            super().hook(u, address, size, context)


def audit(raw):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA: raise ValueError('Exact stock required')
    offset = 0x11e9c214 + 0xa1829b0c - 0xa1800000 - 0x10020000
    if struct.unpack_from('<I', raw, offset)[0] != 0x1030da57: raise AssertionError('Native callback binding')
    scenarios = [('admitted', {}, {}, 0, 0, 0x100, True)]
    scenarios += [(f'snapshot-state-{state}', {}, {}, state, 0, 0, False) for state in (2, 5, 11)]
    scenarios += [('native-mode-block', {0x10401d22: 1}, {}, 0, 0, 0, False),
                  ('native-first-exclusion', {0x10297a2e: 1}, {}, 0, 0, 0, False),
                  ('native-second-exclusion', {0x10297a16: 1}, {}, 0, 0, 0, False),
                  ('secondary-gate-block', {}, {0x2a: 0, 2: 1}, 0, 0, 0, False),
                  ('fallback-admission-block', {0x102c7426: 0}, {0x2a: 0, 2: 0}, 0, 0, 0, False),
                  ('fallback-admission-permits', {}, {0x2a: 0, 2: 0}, 0, 0, 0x100, True),
                  ('native-special-monitor-return', {0x103fec18: 3, 0x1041af4c: 0}, {}, 0, 0, 0, False),
                  ('native-special-monitor-busy', {0x103fec18: 3, 0x103fef66: 1}, {}, 0, 0, 0, False),
                  ('native-snapshot-no-cycle', {}, {}, 0, 1, 0x100, False)]
    checks = []
    for name, overrides, gates, state, skip_cycle, expected_return, advances in scenarios:
        f = DispInput(raw); f.results.update(overrides)
        if gates: f.gates = gates
        f.u.mem_write(0xa201d4d0, bytes([state]))
        f.u.mem_write(0xa201d4d0 + 0x192, bytes([skip_cycle]))
        returned = f.call(0x1030d7ac, 0x29, 0, 0, 0)
        actual = any(e['function'] == '0x1037061c' for e in f.events)
        passed = returned == expected_return and actual == advances
        checks.append(dict(name=name, passed=passed, returned=returned, native_cycle_called=actual))
        if not passed: raise AssertionError(checks[-1])
    f = DispInput(raw); f.call(0x1030d7ac, 0x28, 0, 0, 0)
    passed = any(e['function'] == '0x1036763c' for e in f.events) and not any(e['function'] == '0x1037061c' for e in f.events)
    checks.append(dict(name='z7ii-key-28-is-a-different-z7-handler', passed=passed))
    if not passed: raise AssertionError(checks[-1])
    for name, overrides, advances in (
        ('outer-admitted', {}, True),
        ('outer-first-admission-block', {0x10370a90: 1}, False),
        ('outer-first-key-filter-block', {0x103ebe0c: 1}, False),
        ('outer-second-key-filter-block', {0x103ebe3c: 1}, False),
        ('outer-final-key-filter-block', {0x103ebed8: 1}, False),
        ('outer-retains-inner-native-exclusion', {0x10297a16: 1}, False),
    ):
        f = DispInput(raw); f.results.update(overrides)
        f.call(0x1030da56, 0x29, 0, 0, 0)
        actual = any(e['function'] == '0x1037061c' for e in f.events)
        passed = actual == advances
        checks.append(dict(name=name, passed=passed, native_cycle_called=actual))
        if not passed: raise AssertionError(checks[-1])
    return dict(passed=True, checks=checks, source_sha256=STOCK_SHA,
                shooting_key_callback_slot='0xa1829b0c', shooting_key_callback='0x1030da57',
                internal_dispatcher='0x1030d7ac', disp_key='0x29', native_admission='0x103673f6',
                native_page_cycle='0x1037061c', original_key_callback_unchanged=True,
                supplied_boundaries=['Native service return values', 'Incoming snapshot bytes'],
                native_key_injection_observed=False, camera_access=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, default=ROOT / '.private/builds/20261021-laptop-01/stock-main.bin')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists(): parser.error('Choose a new private output')
    result = audit(args.stock.read_bytes()); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__': main()
