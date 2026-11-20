"""Identify original-Z7 readouts through native formatter routes.

SPDX-License-Identifier: MIT. Original updater/helper and string-copy instructions
execute with supplied snapshot/control data. Text/glyph drawing sinks are
supplied. Raw observed text stays in private output; no pixels/hardware proof.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from itertools import product

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3
from audit_splash_image import NativePNG, STOCK_SHA
from build_z7_module_host import ROOT


class IdentityFixture(NativePNG):
    def __init__(self, raw):
        super().__init__(raw)
        self.u.mem_map(0xa2010000, 0x20000)
        self.text = []
        for widget in (10, 11, 15):
            descriptor = int.from_bytes(self.u.mem_read(0x1064d610 + widget * 4, 4), 'little')
            controls = int.from_bytes(self.u.mem_read(descriptor + 44, 4), 'little')
            count = self.u.mem_read(descriptor + 40, 1)[0]
            if not 2 <= count <= 32: raise AssertionError('Native control count')
            for row in range(count): self.u.mem_write(controls + row * 48, b'\0\0')
            self.u.mem_write(controls + 49, b'\1')

    def hook(self, u, address, size, context):
        if address == 0x102f32ae:
            font, widget, control, pointer = [u.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)]
            text = bytes(u.mem_read(pointer, 40)).split(b'\0')[0].decode('ascii')
            self.text.append(dict(font=font, widget=widget, control=control, text=text))
            self.ret(0)
        elif address == 0x102f309a: self.ret(0)
        else: super().hook(u, address, size, context)


def audit(raw):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA: raise ValueError('Exact original-Z7 stock MAIN required')
    f = IdentityFixture(raw); cases = []
    for name, function, offset, value, fmt, expected in (
            ('shutter-time', 0x102f378c, 0x1c, 0, 0, (10, 'Time')),
            ('shutter-bulb', 0x102f378c, 0x1c, 1, 0, (10, 'Bulb')),
            ('aperture', 0x102f3836, 0x20, 36, 0, (11, '4.2')),
            ('iso-label-and-value', 0x102f3b5a, 0x165, 0, 0, (15, 'ISO')),
            ('shutter-full-warning', 0x102f378c, 0x1c, 0, 16, (10, 'Full')),
            ('shutter-card-warning', 0x102f378c, 0x1c, 0, 26, (10, 'Card')),
            ('shutter-error-warning', 0x102f378c, 0x1c, 0, 27, (10, 'Err')),
            ('shutter-second-error-warning', 0x102f378c, 0x1c, 0, 28, (10, 'Err'))):
        f.u.mem_write(0xa201d4d0, bytes(0x33c)); f.u.mem_write(0xa18237b8, bytes(7))
        f.u.mem_write(0xa201d4d0 + offset, struct.pack('<I', value)); f.u.mem_write(0xa18237b8, bytes([fmt]))
        f.text = []; f.call(function)
        if not any((v['widget'], v['text']) == expected for v in f.text): raise AssertionError((name, f.text))
        cases.append(dict(name=name, passed=True, function=hex(function), native_format=fmt, observed=f.text))
    visibility_cases = []
    descriptor = int.from_bytes(f.u.mem_read(0x1064d610 + 15 * 4, 4), 'little')
    controls = int.from_bytes(f.u.mem_read(descriptor + 44, 4), 'little')
    for mode, normal, alternate, secondary in product((0, 1, 2, 3, 4, 0xffffffff), range(2), range(2), range(2)):
        f.u.mem_write(0xa201d4d0, bytes(0x33c))
        for offset, value in ((4, normal), (0x3c, alternate), (0x24c, secondary), (0x250, mode)):
            f.u.mem_write(0xa201d4d0 + offset, struct.pack('<I', value))
        selected = alternate if mode == 1 else secondary if mode == 3 else normal
        if f.call(0x102f2586, 15) != selected: raise AssertionError('Native ISO phase selector')
        for row in (1, 2):
            f.u.mem_write(controls + row * 48, b'\0\0\1')
            f.call(0x102f2656, 15, row)
            visible = f.u.mem_read(controls + row * 48 + 1, 1)[0]
            if visible != selected: raise AssertionError('Native ISO subcontrol visibility')
            visibility_cases.append(dict(mode=mode, normal=normal, alternate=alternate, secondary=secondary,
                row=row, native_visible=visible, passed=True))
    return dict(passed=True, cases=cases, iso_visibility_cases=visibility_cases, stock_main_sha256=STOCK_SHA,
        identified_widgets=dict(shutter=10, aperture=11, iso=15),
        warnings_share_shutter_widget_and_control=True,
        native_iso_phase_selector_and_visibility_helper_execute=True,
        supplied_boundaries=['Snapshot and control visibility', 'Text/glyph drawing sinks'],
        camera_access=False, pixel_validation=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(); output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists(): p.error('Choose a new private output')
    result = audit(args.stock_main.read_bytes()); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, cases=len(result['cases']), iso_visibility_cases=len(result['iso_visibility_cases']))))


if __name__ == '__main__': main()
