"""Original-Z7 histogram painter geometry and native scale getter.

SPDX-License-Identifier: MIT. Original painter, rectangle adapter, native memcpy
and state getter execute. Incoming bins/GUI rectangles and low-level rectangle
draw/barrier services are supplied. This is primitive geometry, not actual pixels.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1
from audit_splash_image import NativePNG, STOCK_SHA, MEM
from build_z7_module_host import ROOT

CONTROL, STATE, BINS, OBJECT = 0xa18273d4, 0xa201d308, 0xa201df88, MEM + 0x10000


class PainterFixture(NativePNG):
    def __init__(self, raw):
        super().__init__(raw)
        self.u.mem_map(0xa2010000, 0x20000)
        self.rectangles, self.barriers = [], []

    def hook(self, u, address, size, context):
        if address == 0x103fa470:
            rectangle = struct.unpack('<4h', u.mem_read(u.reg_read(UC_ARM_REG_R0), 8))
            self.rectangles.append(dict(rectangle=rectangle, palette=u.reg_read(UC_ARM_REG_R1)))
            self.ret(1)
        elif address == 0x103fcb46:
            self.barriers.append(u.reg_read(UC_ARM_REG_R0)); self.ret(1)
        else: super().hook(u, address, size, context)


def audit(raw):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA: raise ValueError('Exact original-Z7 stock required')
    checks, scenarios = [], []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    f = PainterFixture(raw)
    def write(address, value): f.u.mem_write(address, struct.pack('<I', value))
    for scale in (0, 1, 37, 100, 0xffffffff):
        write(STATE + 0x34, scale)
        check(f'original-gate3-reads-histogram-scale-{scale}', f.call(0x103ea09e, 3) == scale)
    for name, bins, scale, visible in [
        ('uniform', [100] * 256, 100, 1), ('empty', [0] * 256, 100, 1),
        ('low', [1] * 256, 100, 1), ('clipped', [200] * 256, 100, 1),
        ('hidden', [100] * 256, 100, 0)]:
        write(STATE + 0x34, scale); write(OBJECT + 0x28, visible)
        f.u.mem_write(0xa18237c6, b'\0')
        f.u.mem_write(CONTROL + 10, struct.pack('<4h', 20, 30, 216, 130))
        f.u.mem_write(BINS, struct.pack('<256I', *bins))
        f.rectangles.clear(); f.barriers.clear()
        check(name + '-native-painter-returns', f.call(0x102f1544, OBJECT, 0, 0, 0) == 1)
        bars = [r['rectangle'] for r in f.rectangles if r['palette'] == 1]
        check(name + '-no-negative-or-outside-rectangles', all(20 <= x1 <= x2 <= 216 and 30 <= y1 <= y2 <= 130
              for x1, y1, x2, y2 in (r['rectangle'] for r in f.rectangles)))
        check(name + '-bar-visibility', bool(bars) == bool(visible and any(bins)))
        if bars:
            expected_height = min(100, 100 * bins[0] // scale)
            check(name + '-native-bin-height-and-clipping', all(y2 - y1 == expected_height and x2 - x1 == 2 for x1, y1, x2, y2 in bars))
        check(name + '-native-source-not-modified', bytes(f.u.mem_read(BINS, 1024)) == struct.pack('<256I', *bins))
        scenarios.append(dict(name=name, visible=bool(visible), scale=scale, rectangles=f.rectangles.copy(), barriers=f.barriers.copy()))
    return dict(passed=True, checks=checks, scenarios=scenarios, stock_main_sha256=STOCK_SHA,
        native_painter='0x102F1544', native_scale_getter='0x103EA09E key3',
        native_rectangle_adapter='0x102F14C2', supplied_boundaries=['Bins and GUI object/rectangle',
        'Low-level rectangle draw103FA470', 'Native display barrier103FCB46'],
        actual_pixels=False, successful_statistics_producer=False, camera_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock', type=Path, default=ROOT / '.private/builds/20261021-laptop-01/stock-main.bin')
    p.add_argument('--output', type=Path, required=True); a = p.parse_args(); output = a.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists(): p.error('Choose a new private output')
    result = audit(a.stock.read_bytes()); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']), scenarios=len(result['scenarios']))))


if __name__ == '__main__': main()
