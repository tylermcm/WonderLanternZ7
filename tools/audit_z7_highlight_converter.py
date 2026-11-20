"""Execute the original-Z7 highlight request-to-parameter converter.

SPDX-License-Identifier: MIT. Palette contents and incoming request buffers are
supplied. Native converter, enumeration tables and palette getter execute.
No producer hook, graphics submission, pixels or physical output is established.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1
from audit_splash_image import BASE, MEM, STOCK_SHA
from audit_z7_display_parameters import ParametersFixture
from build_z7_module_host import ROOT

CONVERTER, PALETTE_GETTER = 0x1034fe22, 0x10435aca
LEVELS = (255, 248, 235, 224, 213, 202, 191, 180)


class ConverterFixture(ParametersFixture):
    def __init__(self, raw):
        super().__init__(raw)
        self.u.mem_map(0xa1f18000, 0x1000)
        self.palette_gets = []

    def hook(self, u, address, size, context):
        if address == PALETTE_GETTER:
            self.palette_gets.append((u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)))
        super().hook(u, address, size, context)


def request(output, pattern, threshold):
    data = bytearray(36)
    struct.pack_into('<I', data, 0, int(pattern != 0))
    struct.pack_into('<8H', data, 6, 255, threshold, 13 if output == 4 else 15, 5, 255, threshold, 15, 5)
    struct.pack_into('<2I', data, 24, 4, 4)
    data[32] = data[33] = pattern - 1 if pattern else 2
    return bytes(data)


def audit(raw):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA:
        raise ValueError('Exact private original-Z7 C3.80 stock main required')
    f = ConverterFixture(raw)
    checks = []

    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good:
            raise AssertionError(name)

    def table(address, index):
        return raw[address - BASE + index]

    src, dst, palette_address = MEM + 0x1000, MEM + 0x2000, MEM + 0x8000
    f.u.mem_write(0xa1f18fac, struct.pack('<I', palette_address))
    cases = [(output, 0, 248, 0) for output in (1, 2, 4)] + [
        (output, pattern, threshold, palette_case)
        for palette_case in (0, 1) for output in (1, 2, 4)
        for pattern in (1, 2) for threshold in LEVELS]
    for output, pattern, threshold, palette_case in cases:
        palette = [(((i * 37 + palette_case * 91) & 255) << 24) | (0x123400 + i) for i in range(256)]
        f.u.mem_write(palette_address, struct.pack('<256I', *palette))
        incoming = request(output, pattern, threshold)
        f.u.mem_write(src - 16, b'\xc3' * 16 + incoming + b'\xe7' * 16)
        f.u.mem_write(dst - 16, b'\xa5' * 132)
        expected = bytearray(b'\xa5' * 100)
        struct.pack_into('<I', expected, 0, int(pattern != 0))
        if pattern:
            expected[4] = table(0x106311c4, 0)
            expected[12] = expected[52] = table(0x106311c0, 0)
            struct.pack_into('<I', expected, 88, 0)
            expected[96] = {1: 0, 2: 1, 4: 2}[output]
            expected[97:99] = bytes([4, 4])
            expected[99] = table(0x106311ac, pattern - 1)
            for enable_offset, index_offset, color_offset, color_index in (
                    (16, 26, 28, 13 if output == 4 else 15), (32, 42, 44, 5),
                    (56, 66, 68, 15), (72, 82, 84, 5)):
                struct.pack_into('<I', expected, enable_offset, 1)
                struct.pack_into('<H', expected, index_offset, color_index)
                expected[color_offset] = palette[color_index] >> 24
            struct.pack_into('<2H', expected, 8, 65535, threshold * 256)
            struct.pack_into('<2H', expected, 48, 65535, threshold * 256)
        before_gets = len(f.palette_gets)
        f.call(CONVERTER, dst, src, output)
        name = f'output{output}-pattern{pattern}-threshold{threshold}-palette{palette_case}'
        check(name + '-exact-parameter-writes-and-destination-padding',
              bytes(f.u.mem_read(dst - 16, 132)) == b'\xa5' * 16 + bytes(expected) + b'\xa5' * 16)
        check(name + '-input-preserved-and-original-palette-getter-used',
              bytes(f.u.mem_read(src - 16, 68)) == b'\xc3' * 16 + incoming + b'\xe7' * 16 and
              f.palette_gets[before_gets:] == ([(1, 0), (1, 0)] if pattern else []))
    return dict(passed=True, checks=checks, stock_main_sha256=STOCK_SHA, native_converter=hex(CONVERTER),
                native_palette_getter=hex(PALETTE_GETTER), request_bytes=36, parameter_bytes=100,
                cases=len(cases), output_flags=[1, 2, 4], thresholds=list(LEVELS), enabled_patterns=[1, 2],
                native_converter_enum_tables_and_palette_getter_execute=True,
                disabled_converter_changes_only_enable_word=True, palette_contents_supplied=True,
                physical_output_flag_mapping_verified=False, frame_producer_bound=False,
                graphics_submission=False, actual_pixels=False, module_installed=False, camera_or_card_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists():
        p.error('Choose a new private output')
    result = audit(a.stock_main.read_bytes())
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']), cases=result['cases'])))


if __name__ == '__main__':
    main()
