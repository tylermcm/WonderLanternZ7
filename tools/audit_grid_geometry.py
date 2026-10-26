"""Execute original Z7 grid geometry with controlled viewport/property inputs.

Independent research. Changes count fields in Unicorn memory only. No firmware
export, device access, drawing replacement or installation is performed.
"""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0
from audit_splash_image import NativePNG, STOCK_SHA

TABLE = 0x1064FD90
BUILDER = 0x10376DA0
DESCRIPTOR = 0xA2020C2C


class GridFixture(NativePNG):
    def __init__(self, raw, viewport, crop):
        super().__init__(raw)
        self.viewport, self.crop = viewport, crop
        self.u.mem_map(0xA2000000, 0x100000)

    def hook(self, u, address, size, context):
        if address == 0x104065A4:
            if u.reg_read(UC_ARM_REG_R0) != 0x402:
                raise AssertionError('Unexpected property read')
            self.ret(self.crop)
        elif address == 0x10437190:
            pointer = u.reg_read(UC_ARM_REG_R0)
            for offset in (8, 0x14):
                u.mem_write(pointer + offset, struct.pack('<4h', *self.viewport))
            u.mem_write(pointer + 0x28, b'\1')
            self.ret(0)
        else:
            super().hook(u, address, size, context)

    def geometry(self, mode, count):
        for record in range(3):
            for offset in (10, 22):
                self.u.mem_write(TABLE + record * 32 + offset,
                                 struct.pack('<H', count))
        self.call(BUILDER, mode)
        return struct.unpack('<hhIHHhhIHHHHBBH',
                             self.u.mem_read(DESCRIPTOR, 32))


def audit(raw):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA:
        raise ValueError('Requires pinned original Z7 C 3.80 MAIN without EG CRC')
    checks, examples = [], []
    def check(name, passed):
        checks.append(dict(name=name, passed=bool(passed)))
    check('six-original-count-fields-equal-three', all(
        struct.unpack_from('<H', raw, TABLE - 0x10020000 + record * 32 + offset)[0] == 3
        for record in range(3) for offset in (10, 22)))
    viewports = [(0, 0, 720, 480), (20, 40, 700, 440), (0, 0, 640, 426)]
    for viewport in viewports:
        left, top, right, bottom = viewport
        for mode in range(3):
            for crop in (0, 1, 2, 4, 8):
                fixture = GridFixture(raw, viewport, crop)
                stock = fixture.geometry(mode, 3)
                thirds = fixture.geometry(mode, 2)
                label = f'{viewport}-mode{mode}-crop{crop}'
                # NativePNG.call independently checks the return PC, stack and
                # all callee-saved registers on both original-builder executions.
                check(label + '-counts-and-third-spacing',
                      (stock[4], stock[9]) == (3, 3)
                      and (thirds[4], thirds[9]) == (2, 2)
                      and thirds[3] == (bottom - top) // 3
                      and thirds[8] == (right - left) // 3)
                check(label + '-preserves-extents-style-and-native-offsets',
                      all(stock[i] == thirds[i] for i in (0, 2, 6, 7, 10, 11, 12, 13, 14))
                      and thirds[1] - thirds[3] == stock[1] - stock[3]
                      and thirds[5] - thirds[8] == stock[5] - stock[8])
                if viewport == viewports[0] and crop == 0:
                    examples.append(dict(mode=mode, stock=list(stock), thirds=list(thirds)))
                del fixture
                gc.collect()
    return dict(schema=1, stock_main_sha256=STOCK_SHA,
                scope='Original Z7 geometry and soft-float instructions; supplied viewport and crop-property boundaries. No display, GPU or physical camera validation.',
                original_menu_page='0x153', original_property='0x102D',
                original_builder=hex(BUILDER), count_table=hex(TABLE),
                native_calls=90, checks=checks, examples=examples,
                camera_access=False, firmware_export=False,
                all_passed=all(item['passed'] for item in checks))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.stock.read_bytes())
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(checks=len(result['checks']), all_passed=result['all_passed'])))
    if not result['all_passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
