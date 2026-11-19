"""Build experimental original-Z7 Thumb modules; never builds Nikon firmware.

SPDX-License-Identifier: MIT
Derived from JKWTCN/z7ii-extensions tools/module.py at
50a22b24c50619cffa646dac386e8334659f475a (MIT, copyright 2026 JKWTCN).
Independent Z7 format, bounded ELF parsing and validation are local changes.
See z7-native-modules/LICENSE and NOTICE.md.
"""
import argparse
import binascii
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SDK = ROOT / 'z7-native-modules' / 'sdk'
MAGIC, ABI, TARGET = b'Z7M1', 1, 0x03800007
HEADER, MAX_FILE, MAX_MEMORY = 64, 1 << 20, 4 << 20


def seal(data):
    data = bytearray(data)
    if len(data) < HEADER:
        raise ValueError('Truncated module header')
    data[32:36] = bytes(4)
    struct.pack_into('<I', data, 32, binascii.crc32(data))
    return bytes(data)


def pack_module(image, bss_size, entry_offset, relocations=()):
    """Package linked Thumb bytes; pointer words hold image-relative offsets."""
    image = bytes(image)
    relocs = list(relocations)
    if not image or len(image) % 64 or len(image) > MAX_FILE - HEADER:
        raise ValueError('Image must be nonempty, bounded, and aligned to 64 bytes')
    if not 0 <= bss_size <= MAX_MEMORY - len(image):
        raise ValueError('Image and BSS exceed the memory limit')
    if entry_offset < 0 or entry_offset % 2 or entry_offset >= len(image):
        raise ValueError('Invalid Thumb entry offset')
    if relocs != sorted(set(relocs)):
        raise ValueError('Relocations must be strictly increasing and unique')
    for off in relocs:
        if off < 0 or off % 4 or off > len(image) - 4:
            raise ValueError('Unaligned or out-of-bounds relocation')
        if struct.unpack_from('<I', image, off)[0] >= len(image) + bss_size:
            raise ValueError('Absolute pointer outside module')
    size = HEADER + len(image) + 4 * len(relocs)
    if size > MAX_FILE:
        raise ValueError('Module exceeds the file limit')
    header = struct.pack('<4s15I', MAGIC, ABI, TARGET, size, len(image),
                         bss_size, entry_offset, len(relocs), 0, *([0] * 7))
    return seal(header + image + b''.join(struct.pack('<I', off) for off in relocs))


def from_elf(data):
    """Accept bounded linked ELF32 ARM, with retained relocation records."""
    def region(offset, size):
        if offset < 0 or size < 0 or offset + size > len(data):
            raise ValueError('ELF range outside input')
        return data[offset:offset + size]

    region(0, 52)
    if data[:7] != b'\x7fELF\x01\x01\x01' or struct.unpack_from('<HHI', data, 16) != (2, 40, 1):
        raise ValueError('Expected linked little-endian ELF32 ARM')
    entry, _, shoff = struct.unpack_from('<III', data, 24)
    shsize, count = struct.unpack_from('<HH', data, 46)
    if shsize != 40 or not count:
        raise ValueError('Unexpected section format')
    region(shoff, count * 40)
    sections = [struct.unpack_from('<10I', data, shoff + i * 40) for i in range(count)]
    for section in sections:
        if section[1] != 8:
            region(section[4], section[5])
    symbols = {}
    for section in sections:
        if section[1] != 2:
            continue
        if section[6] >= count or section[9] != 16 or section[5] % 16:
            raise ValueError('Invalid symbol table')
        strings = sections[section[6]]
        if strings[1] != 3:
            raise ValueError('Invalid symbol string table')
        names = region(strings[4], strings[5])
        for off in range(section[4], section[4] + section[5], 16):
            name, value, _, _, _, index = struct.unpack_from('<IIIBBH', data, off)
            end = names.find(b'\0', name)
            if end < 0:
                raise ValueError('Invalid symbol name')
            try:
                label = names[name:end].decode('utf-8')
            except UnicodeDecodeError as error:
                raise ValueError('Invalid symbol encoding') from error
            if index == 0 and label:
                raise ValueError('Undefined module symbol: ' + label)
            if index >= count and index != 0xfff1:
                raise ValueError('Invalid symbol section')
            if label in ('__image_end', '__memory_end', 'z7_main') and label in symbols and symbols[label] != value:
                raise ValueError('Conflicting module symbol: ' + label)
            if label and not label.startswith('$'):
                symbols[label] = value
    if not {'__image_end', '__memory_end', 'z7_main'} <= symbols.keys():
        raise ValueError('Missing linker bounds or z7_main')
    image_size, memory_size = symbols['__image_end'], symbols['__memory_end']
    if not 0 < image_size <= MAX_FILE - HEADER or image_size % 64 or not image_size <= memory_size <= MAX_MEMORY:
        raise ValueError('Invalid module image or BSS bounds')
    if not entry & 1 or entry != symbols['z7_main'] or entry & ~1 >= image_size:
        raise ValueError('Invalid module Thumb entry')
    image = bytearray(image_size)
    occupied = []
    for _, kind, flags, addr, off, size, *_ in sections:
        if not flags & 2 or not size:
            continue
        if kind == 8:
            if addr < image_size or addr + size > memory_size:
                raise ValueError('BSS outside module memory')
            continue
        if addr + size > image_size or any(addr < end and start < addr + size for start, end in occupied):
            raise ValueError('Allocated sections overlap or exceed image')
        occupied.append((addr, addr + size))
        image[addr:addr + size] = region(off, size)
    relocations = []
    # Linker-resolved relative references; absolute module pointers need rebasing.
    relative = {0, 3, 10, 25, 26, 28, 29, 30, 42, 45, 46, 49, 50, 51}
    for section in sections:
        if section[1] == 4:
            raise ValueError('RELA relocation tables are unsupported')
        if section[1] != 9:
            continue
        if section[7] >= count or section[6] >= count or sections[section[6]][1] != 2 or section[9] != 8 or section[5] % 8:
            raise ValueError('Invalid relocation table')
        if not sections[section[7]][2] & 2:
            continue
        target = sections[section[7]]
        for off in range(section[4], section[4] + section[5], 8):
            address, info = struct.unpack_from('<II', data, off)
            if not target[3] <= address < target[3] + target[5] or info >> 8 >= sections[section[6]][5] // 16:
                raise ValueError('Relocation outside target or symbol table')
            kind = info & 255
            if kind == 2:
                relocations.append(address)
            elif kind not in relative:
                raise ValueError(f'Unsupported ARM relocation {kind} at {address:#x}')
    relocations.sort()
    packed = pack_module(image, memory_size - image_size, entry & ~1, relocations)
    return packed, dict(target=TARGET, image_bytes=image_size, bss_bytes=memory_size - image_size,
                        entry_offset=entry & ~1, relocations=relocations, symbols=symbols)


def build(source, clang='clang', linker=None, zig=None):
    linker = linker or ('ld.lld.exe' if os.name == 'nt' else 'ld.lld')
    temporary_root = ROOT / '.private/tmp'
    temporary_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='z7-native-module-', dir=temporary_root) as folder:
        obj, elf = Path(folder) / 'module.o', Path(folder) / 'module.elf'
        environment = os.environ.copy()
        if zig:
            environment['ZIG_GLOBAL_CACHE_DIR'] = str(ROOT / '.private/toolchain/zig-cache')
            environment['ZIG_LOCAL_CACHE_DIR'] = str(ROOT / '.private/tmp/zig-cache')
        compiler = ([str(zig), 'cc', '-target', 'thumb-freestanding-eabi', '-mcpu=cortex_a9']
                    if zig else [clang, '--target=arm-none-eabi', '-mcpu=cortex-a9', '-mthumb'])
        subprocess.run(compiler + [
                        '-mfloat-abi=soft', '-Os', '-fPIC', '-fvisibility=hidden',
                        '-ffreestanding', '-fno-builtin', '-fno-unwind-tables',
                        '-fno-asynchronous-unwind-tables', '-fno-stack-protector',
                        '-Wall', '-Wextra', '-Werror', '-I', str(SDK),
                        '-c', str(source), '-o', str(obj)], check=True, env=environment)
        link = ([str(zig), 'ld.lld', '-T', str(SDK / 'module.ld'), '--emit-relocs', '--no-undefined']
                if zig else [linker, '-T', str(SDK / 'module.ld'), '--emit-relocs', '--no-undefined'])
        subprocess.run(link + [str(obj), '-o', str(elf)], check=True, env=environment)
        return from_elf(elf.read_bytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--clang', default='clang')
    parser.add_argument('--linker')
    parser.add_argument('--zig', type=Path, help='Use a private Zig/Clang cross-compiler')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output must not already exist')
    module, report = build(args.source, args.clang, args.linker, args.zig)
    with args.output.open('xb') as handle:
        handle.write(module)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
