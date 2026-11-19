"""Original-Z7 DISP property selector and snapshot-to-property setter contract.

SPDX-License-Identifier: MIT. Native instructions execute; display-kind query,
property storage and incoming mode/output are supplied boundaries. No key hook.
"""
import argparse
import hashlib
import json
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1
from audit_splash_image import NativePNG, STOCK_SHA
from build_z7_module_host import ROOT


class DispSelector(NativePNG):
    def __init__(self, raw):
        super().__init__(raw)
        self.u.mem_map(0xa2010000, 0x20000)
        self.movie = 0
        self.display = 1
        self.stores = []
        self.cycle = False
        self.exposure = 0
        self.eligibility = 0
        self.information_calls = []

    def hook(self, u, address, size, context):
        if address == 0x104065a4:
            key = u.reg_read(UC_ARM_REG_R0)
            if self.cycle and key == 0x102c: self.ret(self.exposure)
            elif key == 0x138d: self.ret(self.movie)
            else: raise AssertionError('Unexpected selector property')
        elif address == 0x103fef80:
            self.ret(self.display)
        elif address == 0x104065b0:
            self.stores.append([u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)])
            self.ret(0)
        elif self.cycle and address == 0x103ebb42:
            self.ret(self.eligibility)
        elif self.cycle and address in (0x1030d50c, 0x103eb7c4):
            self.information_calls.append(hex(address)); self.ret(0)
        else:
            super().hook(u, address, size, context)


def audit(raw):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA: raise ValueError('Exact stock required')
    f = DispSelector(raw)
    checks = []
    for movie in (0, 1):
        for display in (1, 4):
            f.movie, f.display = movie, display
            expected = (0x2f17 if display == 1 else 0x2f18) if movie else (0x2f15 if display == 1 else 0x2f16)
            selected = f.call(0x103673ac)
            checks.append(dict(name=f'select-movie-{movie}-display-{display}', passed=selected == expected,
                               property=hex(selected)))
            if selected != expected: raise AssertionError(checks[-1])
            for mode in range(5):
                start = 0xa201d4d0 + 0x180
                f.u.mem_write(start, b'\xa5' * 32); f.stores.clear()
                f.call(0x103673de, mode)
                actual = bytes(f.u.mem_read(start, 32))
                desired = bytearray(b'\xa5' * 32); desired[10] = mode
                passed = actual == bytes(desired) and f.stores == [[expected, mode]]
                checks.append(dict(name=f'set-movie-{movie}-display-{display}-mode-{mode}', passed=passed))
                if not passed: raise AssertionError(checks[-1])
    f.cycle = True
    for movie in (0, 1):
        for display in (1, 4):
            for exposure in (0, 1):
                for eligibility in (0, 1):
                    for mode in range(5):
                        f.movie, f.display, f.exposure, f.eligibility = movie, display, exposure, eligibility
                        f.u.mem_write(0xa201d4d0 + 0x18a, bytes([mode])); f.stores.clear(); f.information_calls.clear()
                        next_mode = (mode + 1) % 5
                        if next_mode == 2 and not movie and (not exposure or eligibility): next_mode = 3
                        if next_mode == 4 and (movie or display == 4): next_mode = 0
                        expected_return = 2 if next_mode == 4 else 0x100
                        returned = f.call(0x1037061c)
                        actual_mode = bytes(f.u.mem_read(0xa201d4d0 + 0x18a, 1))[0]
                        passed = returned == expected_return and actual_mode == next_mode and len(f.stores) == 1 and f.stores[0][1] == next_mode and bool(f.information_calls) == (next_mode == 4)
                        checks.append(dict(name=f'cycle-{movie}-{display}-{exposure}-{eligibility}-{mode}', passed=passed,
                                           resulting_mode=actual_mode, returned=returned))
                        if not passed: raise AssertionError(checks[-1])
    return dict(passed=True, checks=checks, source_sha256=STOCK_SHA,
                photo_lcd_property='0x2f15', photo_alternate_output_property='0x2f16',
                movie_lcd_property='0x2f17', movie_alternate_output_property='0x2f18',
                snapshot_mode_offset='0x18a', selector='0x103673ac', setter='0x103673de',
                native_cycle='0x1037061c', information_app_transition_completed=False,
                supplied_boundaries=['Property138D/102C values', 'Native display-kind result', 'Property setter storage', 'Native eligibility result', 'Information-app transition calls'],
                key_callback_identified=False, physical_persistence_verified=False, camera_access=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, default=ROOT / '.private/builds/20261021-laptop-01/stock-main.bin')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists(): parser.error('Choose a new private output')
    result = audit(args.stock.read_bytes())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__': main()
