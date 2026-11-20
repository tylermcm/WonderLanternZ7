"""Bind original-Z7 OpenVG exports and native sampler-control bit generation.

SPDX-License-Identifier: MIT. Executes bounded original instruction prefixes;
image descriptors, quality inputs and context fields are supplied. No complete
image creation, hardware texture-origin meaning or framebuffer pixels claimed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_CPSR
from audit_splash_image import NativePNG, STOCK_SHA, MEM, STACK, STOP
from build_z7_module_host import ROOT

EXPORTS = {
    'vgCreateImage': (0xa1801048, 0x10450b36), 'vgCopyImage': (0xa1801080, 0x10450c4c),
    'vgDrawImage': (0xa1801088, 0x10450c86), 'vgSetPixels': (0xa1801090, 0x10450cbc),
    'vgWritePixels': (0xa1801098, 0x10450d00), 'vgGetPixels': (0xa18010a0, 0x10450df4),
    'vgReadPixels': (0xa18010a8, 0x10450e3c), 'vgCopyPixels': (0xa18010b0, 0x10450da4),
    'vgCreateImageStandardDataDMP': (0xa18011b0, 0x104514e8),
    'vgCreateImageDataDMP': (0xa1801178, 0x104514b6),
    'vgCreateImageBufferPointerDMPX': (0xa18011e0, 0x104516c6),
    'vgCreateImageMultiBufferPointerDMPX': (0xa18011d8, 0x10451684),
}


class ControlsFixture(NativePNG):
    stop_at = None

    def hook(self, u, address, size, context):
        if address == self.stop_at:
            u.emu_stop()
        else:
            super().hook(u, address, size, context)

    def prefix(self, begin, end, registers, flags=0):
        self.stop_at = end
        self.u.reg_write(UC_ARM_REG_SP, STACK)
        self.u.reg_write(UC_ARM_REG_LR, STOP | 1)
        self.u.reg_write(UC_ARM_REG_CPSR, (self.u.reg_read(UC_ARM_REG_CPSR) & ~0xf8000000) | flags)
        for register, value in registers.items():
            self.u.reg_write(register, value)
        self.u.emu_start(begin | 1, STOP, timeout=1000000, count=1000)
        self.stop_at = None
        if self.u.reg_read(UC_ARM_REG_PC) != end:
            raise AssertionError('Original prefix did not reach its explicit boundary')


def audit(raw):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA:
        raise ValueError('Exact original-Z7 C3.80 stock MAIN required')
    f = ControlsFixture(raw)
    checks, cases = [], []

    def check(name, condition):
        checks.append(dict(name=name, passed=bool(condition)))
        if not condition:
            raise AssertionError(name)

    for name, (slot, address) in EXPORTS.items():
        text, function = struct.unpack('<2I', f.u.mem_read(slot, 8))
        check('original-named-export-' + name, function == address | 1 and
              bytes(f.u.mem_read(text, len(name) + 1)) == name.encode() + b'\0')
    descriptor, state = MEM + 0x1000, MEM + 0x2000
    for quality in range(1, 8):
        for kind in (1, 3, 4, 0x4003):
            before = b'\xa5' * 0xb4
            f.u.mem_write(descriptor, before)
            f.u.mem_write(STACK, struct.pack('<7I', quality, kind, 0, 8, 8, 6, 0))
            f.prefix(0x1047e814, 0x1047e844, {
                UC_ARM_REG_R0: descriptor, UC_ARM_REG_R1: 0, UC_ARM_REG_R2: 8, UC_ARM_REG_R3: 6})
            expected = bytearray(before)
            struct.pack_into('<I', expected, 0x0c, 0)
            struct.pack_into('<I', expected, 0x18, 0)
            struct.pack_into('<I', expected, 0x24, quality)
            struct.pack_into('<2H', expected, 0x34, 8, 6)
            struct.pack_into('<H', expected, 0x48, kind)
            check('native-image-initializer-quality-' + str(quality) + '-kind-' + hex(kind),
                  bytes(f.u.mem_read(descriptor, len(before))) == expected and f.u.reg_read(UC_ARM_REG_SP) == STACK - 32)
    for pixel_format in (0, 12):
        for quality in (1, 4):
            for context_value in (0, 1, 2, 4):
                for kind in (3, 4):
                    for flags in (0, 0xf8000000):
                        f.u.mem_write(descriptor, bytes(0xb4))
                        f.u.mem_write(descriptor + 0x1c, struct.pack('<I', pixel_format))
                        f.u.mem_write(descriptor + 0x24, struct.pack('<I', quality))
                        f.u.mem_write(descriptor + 0x48, struct.pack('<H', kind))
                        f.u.mem_write(state, bytes(0xb0))
                        f.u.mem_write(state + 0xa0, struct.pack('<I', context_value))
                        before = (bytes(f.u.mem_read(descriptor, 0xb4)), bytes(f.u.mem_read(state, 0xb0)))
                        f.prefix(0x104b92ea, 0x104b9318, {
                            UC_ARM_REG_R5: 0xdeadbeef, UC_ARM_REG_R6: state, UC_ARM_REG_R7: descriptor}, flags)
                        actual = f.u.reg_read(UC_ARM_REG_R5)
                        expected = (0x20 if pixel_format == 12 else 0) | (6 if quality & 4 and context_value == 4 else 0) | (1 if kind == 4 else 0)
                        case = dict(format=pixel_format, quality=quality, context_value=context_value,
                                    kind=kind, incoming_flags=hex(flags), sampler_flags=actual)
                        cases.append(case)
                        check('native-sampler-flags-' + '-'.join(str(x) for x in case.values()), actual == expected and
                              before == (bytes(f.u.mem_read(descriptor, 0xb4)), bytes(f.u.mem_read(state, 0xb0))) and
                              f.u.reg_read(UC_ARM_REG_SP) == STACK)
    return dict(passed=True, checks=checks, stock_main_sha256=STOCK_SHA, exports={name:hex(value[1]) for name,value in EXPORTS.items()},
                sampler_cases=cases, native_quality_store_prefix=['0x1047e814', '0x1047e844'],
                native_sampler_control_prefix=['0x104b92ea', '0x104b9318'],
                quality_dependent_sampler_mask='0x6', descriptor_kind4_sampler_mask='0x1',
                texture_origin_hardware_meaning_established=False, native_pixels=False,
                supplied_boundaries=['Descriptor format/quality/kind', 'Context comparison value', 'Incoming ARM flags and stack arguments'],
                camera_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if not a.output.resolve().is_relative_to(ROOT / '.private') or a.output.exists():
        p.error('Choose a new private output')
    result = audit(a.stock_main.read_bytes())
    a.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']), sampler_cases=len(result['sampler_cases']))))


if __name__ == '__main__':
    main()
