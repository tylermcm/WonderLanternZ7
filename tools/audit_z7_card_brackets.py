"""Execute the original Z7 card-readout updater and shared bracket path.

SPDX-License-Identifier: MIT. Native visibility query and control flow execute;
GUI style/glyph updates and count-text helpers are supplied call boundaries.
This identifies why descriptor masks alone do not establish a clean display.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3
from audit_splash_image import NativePNG, STOCK_SHA, MEM
from build_z7_module_host import ROOT


class CardBrackets(NativePNG):
    def __init__(self, raw):
        super().__init__(raw)
        self.u.mem_map(0xa2010000, 0x20000)
        self.events = []
        self.execute_gui_wrappers = False

    def hook(self, u, address, size, context):
        if address in (0x102f2b8c, 0x102f2f80, 0x102f3cd8, 0x102f3eae):
            args = [u.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)]
            self.events.append(dict(function=hex(address), arguments=args))
            if self.execute_gui_wrappers and address in (0x102f2b8c, 0x102f2f80):
                return  # Original style/glyph wrapper, geometry copy and visibility setters execute.
            self.ret(1)
        elif self.execute_gui_wrappers and address in (0x103fb340, 0x103fb360):
            self.ret(1)  # Image payload/style application, not visibility or geometry.
        else:
            super().hook(u, address, size, context)


def audit(raw):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA:
        raise ValueError('Requires exact original Z7 C 3.80 MAIN')
    f = CardBrackets(raw)
    checks = []
    for visible in (0, 1):
        for output in (0, 1, 2):
            for excluded in (0, 1):
                for i in range(15): f.u.mem_write(0xa1824684 + i * 48 + 1, bytes([visible if i == 0 else 0]))
                f.u.mem_write(0xa18237ba, b'\0')
                f.u.mem_write(0xa18237c6, bytes([output]))
                f.u.mem_write(0xa201d4d0 + 0x40, b'\0')
                f.u.mem_write(0xa201d4d0 + 0x192, bytes([excluded]))
                f.events.clear()
                gate = f.call(0x102f2f1e, 16)
                f.call(0x102f3f8a)
                glyphs = [e['arguments'] for e in f.events if e['function'] == '0x102f2f80']
                expected = [] if excluded else (
                    [[16, 4, 0x50e, 0x2f6], [16, 2, 0x50f, 0x2f6]] if output == 2 else
                    [[16, 4, 0x121b, 1], [16, 2, 0x121d, 1]] +
                    ([[16, 3, 0x121c, 0], [16, 1, 0x121e, 0]] if output == 0 else []))
                passed = gate == visible and glyphs == expected
                checks.append(dict(name=f'visibility-{visible}-output-{output}-native-exclusion-{excluded}',
                                   passed=passed, native_visibility=gate, glyph_updates=glyphs))
                if not passed: raise AssertionError(checks[-1])
    f.execute_gui_wrappers = True
    for output in (0, 1, 2):
        for excluded in (0, 1):
            for i in range(15):
                object_pointer = MEM + 0x10000 + i * 512
                f.u.mem_write(object_pointer, bytes(284))
                f.u.mem_write(object_pointer + 4, struct.pack('<H', 4))
                f.u.mem_write(object_pointer + 0x48, struct.pack('<I', MEM + 0x20000))
                f.u.mem_write(0xa1824684 + i * 48 + 1, b'\0')
                f.u.mem_write(0xa1824684 + i * 48 + 36, struct.pack('<I', object_pointer))
            f.u.mem_write(0xa18237c6, bytes([output]))
            f.u.mem_write(0xa201d4d0 + 0x192, bytes([excluded]))
            f.call(0x102f3f8a)
            actual = [i for i in range(15) if int.from_bytes(f.u.mem_read(MEM + 0x10000 + i * 512 + 40, 4), 'little')]
            expected = [] if excluded else ([1, 2, 3, 4] if output == 0 else [2, 4])
            passed = actual == expected
            checks.append(dict(name=f'native-wrapper-output-{output}-exclusion-{excluded}', passed=passed,
                               objects_made_visible=actual, supplied_inactive_controls=True))
            if not passed: raise AssertionError(checks[-1])
    return dict(passed=True, checks=checks, source_sha256=STOCK_SHA,
        native_updater='0x102f3f8a', shared_brackets='0x102f7e24', widget=16,
        controls='0xa1824684', native_visibility_query='0x102f2f1e',
        inactive_controls_still_reach_bracket_updates=True,
        supplied_boundaries=['GUI style/glyph setters in control-flow cases; image/style payload application in native-wrapper cases',
                             'Native count-text helpers', 'Incoming output/snapshot/control bytes and synthetic GUI objects'],
        actual_pixels_verified=False, clean_display_implemented=False, camera_access=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, default=ROOT / '.private/builds/20261021-laptop-01/stock-main.bin')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists():
        parser.error('Choose a new private evidence path')
    result = audit(args.stock.read_bytes())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']), inactive_visibility_still_updates_brackets=True)))


if __name__ == '__main__':
    main()
