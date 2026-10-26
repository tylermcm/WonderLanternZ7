"""Execute stock Z7 PNG metadata and pixel paths with synthetic images.

Independent research fixture: no firmware generation, file/device I/O,
GPU drawing or startup hook. Only allocator/free boundaries are supplied;
the resource getter, wrappers, libpng/zlib and memory helpers execute.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import (
    UC_CPU_ARM_CORTEX_A15, UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
    UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
    UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
    UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC,
)

BASE = 0x10020000
STOCK_SHA = 'e6df1764323fb1c287159dd3ce1c84ac93c72b96ba6eb09c070295c093fecbff'
MEM, HEAP, STACK, STOP = 0x50000000, 0x50100000, 0x503F0000, 0x503FF000
TABLE = 0x10D0B7C0
ARGUMENTS = (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)
SAVED = (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
         UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11)


def synthetic_png(width, height, channels):
    def chunk(kind, data):
        return (struct.pack('>I', len(data)) + kind + data
                + struct.pack('>I', zlib.crc32(kind + data) & 0xFFFFFFFF))
    pixels = bytes(value for y in range(height) for x in range(width)
                   for value in ((255 if (x // 8 + y // 8) % 2 else 20, 40, 180)
                                 + ((160,) if channels == 4 else ())))
    stride = width * channels
    scan = b''.join(b'\0' + pixels[y * stride:(y + 1) * stride] for y in range(height))
    header = struct.pack('>IIBBBBB', width, height, 8, 6 if channels == 4 else 2, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header)
            + chunk(b'IDAT', zlib.compress(scan)) + chunk(b'IEND', b''))


class NativePNG:
    def __init__(self, raw, fail_allocation=0):
        self.u = u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_A15)
        u.mem_map(BASE, (len(raw) + 4095) & ~4095)
        u.mem_write(BASE, raw)
        u.mem_map(0xA1800000, 0x110000)
        u.mem_write(0xA1800000, raw[0x11E9C214 - BASE:0x11E9C214 - BASE + 0x101200])
        u.mem_map(MEM, 0x400000)
        self.cursor = HEAP
        self.live, self.allocations = {}, []
        self.attempts = self.frees = 0
        self.fail_allocation = fail_allocation
        u.hook_add(UC_HOOK_CODE, self.hook)

    def ret(self, value):
        self.u.reg_write(UC_ARM_REG_R0, value)
        self.u.reg_write(UC_ARM_REG_PC, self.u.reg_read(UC_ARM_REG_LR))

    def hook(self, u, address, size, context):
        if address == 0x1016FE38:
            self.attempts += 1
            if self.attempts == self.fail_allocation:
                self.ret(0)
                return
            length = u.reg_read(UC_ARM_REG_R0)
            if not 0 < length <= 0x100000 or self.cursor + length >= 0x50200000:
                raise ValueError('Unexpected metadata allocation size')
            result = self.cursor
            self.cursor += (length + 7) & ~7
            self.live[result] = length
            self.allocations.append(length)
            self.ret(result)
        elif address == 0x1016FE4A:
            pointer = u.reg_read(UC_ARM_REG_R0)
            if pointer:
                if pointer not in self.live:
                    raise ValueError('Invalid or duplicate free')
                del self.live[pointer]
                self.frees += 1
            self.ret(0)
        elif address == 0x10239398:
            raise ValueError('Native PNG error/assert callback reached; fixture stopped')

    def call(self, address, *args):
        u = self.u
        for reg in ARGUMENTS:
            u.reg_write(reg, 0)
        for reg, value in zip(ARGUMENTS, args):
            u.reg_write(reg, value)
        guards = {reg: 0x51510000 + index for index, reg in enumerate(SAVED)}
        for reg, value in guards.items():
            u.reg_write(reg, value)
        u.reg_write(UC_ARM_REG_SP, STACK)
        u.reg_write(UC_ARM_REG_LR, STOP | 1)
        u.emu_start(address | 1, STOP, timeout=10000000, count=10000000)
        if u.reg_read(UC_ARM_REG_PC) != STOP or u.reg_read(UC_ARM_REG_SP) != STACK:
            raise ValueError('Native call did not return with its original stack')
        if any(u.reg_read(reg) != value for reg, value in guards.items()):
            raise ValueError('Native call changed a callee-saved register')
        return u.reg_read(UC_ARM_REG_R0)


def audit(raw):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA:
        raise ValueError('Requires original Z7 C 3.80 MAIN, excluding the EG CRC')
    scenarios, checks = [], [dict(name='exact-stock-main', passed=True)]
    for name, width, height, channels, failure, index, mode, stock_table in (
        ('native-stock-entry-zero', 36, 72, 0, 0, 0, 0, True),
        ('synthetic-rgb', 32, 24, 3, 0, 0, 0, False),
        ('synthetic-rgba', 32, 24, 4, 0, 0, 0, False),
        ('synthetic-logo-sized-rgb', 320, 120, 3, 0, 0, 0, False),
        ('upper-index-clamps-to-first', 32, 24, 3, 0, 1, 0, False),
        ('unsupported-wrapper-mode', 32, 24, 3, 0, 0, 1, False),
        ('first-allocation-fails', 32, 24, 3, 1, 0, 0, False),
        ('second-allocation-fails', 32, 24, 3, 2, 0, 0, False),
        ('third-allocation-fails', 32, 24, 3, 3, 0, 0, False),
    ):
        f = NativePNG(raw, failure)
        asset = None if stock_table else synthetic_png(width, height, channels)
        if asset:
            f.u.mem_write(MEM + 0x10000, asset)
            f.u.mem_write(MEM, struct.pack('<5I', 0, len(asset), 0, 0, MEM + 0x10000))
        # The table registration and bound are explicit unit inputs, not a claim
        # about spare native IDs or a permanently patched global resource table.
        f.call(0x104BD2EA, TABLE if stock_table else MEM)
        f.call(0x104BD21C, 0, 1)
        obj, output = MEM + 0x100, MEM + 0x200
        f.u.mem_write(obj, struct.pack('<4I', 0, 0, index, mode))
        result = f.call(0x104E98A8, obj, output)
        dimensions = list(struct.unpack('<HH', f.u.mem_read(output, 4)))
        expected_success = not failure and mode == 0
        checks.extend([
            dict(name=name + '-native-result', passed=result == int(expected_success)),
            dict(name=name + '-dimensions', passed=dimensions == ([width, height] if expected_success else [0, 0])),
            dict(name=name + '-heap-clean', passed=not f.live),
        ])
        scenarios.append(dict(name=name, input_size=[width, height],
                              synthetic_png_bytes=len(asset) if asset else None,
                              native_dimensions=dimensions, native_result=result,
                              allocation_attempts=f.attempts,
                              allocation_sizes=f.allocations, frees=f.frees,
                              live_allocations=len(f.live), abi_preserved=True))
    pixel_scenarios = []
    for width, height, channels in ((32, 24, 3), (32, 24, 4), (320, 120, 3)):
        f = NativePNG(raw)
        asset = synthetic_png(width, height, channels)
        data, context, metadata, slot = (MEM + value for value in (0x10000, 0x200, 0x300, 0x400))
        destination = 0x50200010
        expected = bytes(value for y in range(height) for x in range(width)
                         for value in (255 if (x // 8 + y // 8) % 2 else 20, 40, 180,
                                       160 if channels == 4 else 255))
        f.u.mem_write(data, asset)
        f.call(0x104313D0, context)
        # Fifth AAPCS argument selects tight native rows. The metadata path
        # derives dimensions, channel count, byte count and stride from the PNG.
        f.u.mem_write(STACK, struct.pack('<I', 1))
        f.call(0x10431278, data, len(asset), context, metadata)
        fields = struct.unpack('<10I', f.u.mem_read(metadata, 40))
        f.u.mem_write(destination - 16, b'\xA5' * (len(expected) + 32))
        f.u.mem_write(slot, struct.pack('<I', destination))
        result = f.call(0x104311F4, context, metadata, slot)
        actual = bytes(f.u.mem_read(destination, len(expected)))
        guards = (bytes(f.u.mem_read(destination - 16, 16)) == b'\xA5' * 16
                  and bytes(f.u.mem_read(destination + len(expected), 16)) == b'\xA5' * 16)
        prefix = f'pixel-{width}x{height}-{channels}'
        checks.extend([
            dict(name=prefix + '-native-format', passed=fields[:2] == (width, height)
                 and fields[7:] == (4, width * height * 4, width * 4)),
            dict(name=prefix + '-native-success', passed=result == 1),
            dict(name=prefix + '-exact-rgba', passed=actual == expected),
            dict(name=prefix + '-buffer-guards', passed=guards),
            dict(name=prefix + '-heap-clean', passed=not f.live),
        ])
        pixel_scenarios.append(dict(input_size=[width, height], input_channels=channels,
            synthetic_png_bytes=len(asset), decoded_bytes=len(actual),
            native_row_stride=fields[9], native_channels=fields[7],
            exact_rgba_pixels=actual == expected,
            alpha_preserved_or_filled=actual[3::4] == expected[3::4],
            output_sha256=hashlib.sha256(actual).hexdigest(),
            buffer_guards_intact=guards, live_allocations=len(f.live), abi_preserved=True))
    pixels_verified = all(c['passed'] for c in checks if c['name'].startswith('pixel-'))
    return dict(schema=1, audit_only=True, stock_main_sha256=STOCK_SHA,
                evidence_checks_passed=all(c['passed'] for c in checks), checks=checks,
                scenarios=scenarios, pixel_scenarios=pixel_scenarios,
                native_interfaces=dict(resource_table=hex(TABLE),
                    table_registration='0x104BD2EA', table_bound='0x104BD21C',
                    descriptor_getter='0x104BD2F6', size_wrapper='0x104E98A8',
                    png_header_path='0x104310B4', png_context='0x104313D0',
                    png_format='0x10431278', png_pixels='0x104311F4'),
                scope='Original stock image resource getter, wrappers, libpng/zlib pixel decoding and memory helpers execute in Unicorn.',
                limitations=[
                    'Heap allocation/free are controlled, single-threaded boundaries; real allocator ownership/concurrency is unverified.',
                    'Resource table registration/bound are supplied unit inputs; no spare image ID or safe global table replacement established.',
                    'RGB/RGBA 8-bit non-interlaced synthetic images tested; palette, other depths, malformed/truncated inputs and decoder failure cleanup are unverified.',
                    'Exact decoded RGBA bytes verified in unit RAM; alpha blending and GPU/LCD drawing are unverified.',
                    'Upper-bound normalization tested; negative/untrusted image IDs are not cleared for use.',
                    'No power-on notification, once-per-boot behavior, dismissal, LCD/EVF switching or wake timing established.',
                    'No new firmware image, camera/card access, update acceptance or recovery evidence.',
                ], pixel_decode_verified=pixels_verified, startup_hook_identified=False,
                firmware_built=False, candidate_cleared=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Use a new output path to preserve earlier evidence')
    result = audit(args.stock.read_bytes())
    with args.output.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(evidence_checks=len(result['checks']),
                          passed=result['evidence_checks_passed'],
                          pixel_decode_verified=result['pixel_decode_verified'], candidate_cleared=False)))
    raise SystemExit(not result['evidence_checks_passed'])
