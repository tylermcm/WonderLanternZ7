"""Prepare a PRIVATE offline Z7 installation review; never access a camera/card.

The native probes execute selected stock instructions with mocked file I/O and
runtime state. They do not execute the flash writer or establish update/recovery.
"""
import argparse
import binascii
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'z7-firmware-extensions/src'))
from z30_extensions.build import build, PRESETS
from z30_extensions.container import (
    Z7_CONTAINER_SHA256, Z7_CONTAINER_SIZE, Z7_ZERO_ANCHOR,
    _load_samples, decode_body,
)
from z30_extensions.platform.z7_380 import BASE, SCATTER, StockImage


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def inspect_container(raw):
    if len(raw) != Z7_CONTAINER_SIZE or sha256(raw) != Z7_CONTAINER_SHA256:
        raise ValueError('Expected the untouched original Z7 C 3.80 container')
    body = decode_body(raw[32:], _load_samples(
        'z30_extensions.platform', 'z7_380_zero_samples.json'), Z7_ZERO_ANCHOR)
    if body[:32] != b' ' * 32 or struct.unpack_from('>4I', body, 32) != (4, 176, 0, 0):
        raise ValueError('Unexpected Z7 module directory')
    if body[-14:] != bytes(14) or binascii.crc_hqx(body[:-16], 0) != int.from_bytes(body[-16:-14], 'big'):
        raise ValueError('Invalid package CRC or trailer')
    cursor, modules, main = 176, [], None
    for index in range(4):
        name, offset, size, reserved0, reserved1 = struct.unpack_from('>16s4I', body, 48 + index * 32)
        name = name.rstrip(b'\0').decode('ascii')
        if (offset != cursor or size < 2 or offset + size > len(body) - 16
                or reserved0 or reserved1 or name in {entry['name'] for entry in modules}):
            raise ValueError('Invalid module bounds, name or reserved fields')
        module = body[offset:offset + size]
        if binascii.crc_hqx(module, 0):
            raise ValueError('Invalid module CRC')
        modules.append(dict(name=name, offset=offset, size=size, crc_zero=True, sha256=sha256(module)))
        if name == 'eg1610_038000.bi':
            main = StockImage(module).data
        cursor += size
    if cursor != len(body) - 16 or main is None:
        raise ValueError('Incomplete container coverage or missing EG')
    return main, dict(modules=modules, package_crc_ok=True, trailer_zero=True)


def storage_descriptor(stock):
    image = StockImage(stock)
    # Stock functions 0x10091F10 and 0x10091EFE select these initialized tables.
    entry = image.words(0xA1880B00 + 2 * 28, 7)
    if entry != (2, 0, 0, 0, 0, 2, 0):
        raise ValueError('Unexpected EG storage selector')
    descriptor = image.words(0xA18806A8 + 12 + entry[5] * 44, 11)
    if descriptor != (BASE, 0, 0x2940000, 0x2940000, 0, 0, 0, 0, 0, 0, 1):
        raise ValueError('Unexpected EG storage descriptor')
    return descriptor[2]


def machine(stock):
    from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_PROT_READ, UC_PROT_EXEC
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    rom_size = (len(stock) + 4095) & ~4095
    u.mem_map(BASE, rom_size)
    u.mem_write(BASE, stock)
    u.mem_protect(BASE, rom_size, UC_PROT_READ | UC_PROT_EXEC)
    u.mem_map(0xA1800000, 0x110000)
    u.mem_map(0xA2500000, 0x100000)
    u.mem_map(0x20000000, 0x40000)
    source, destination, size, _ = SCATTER
    u.mem_write(destination, stock[source - BASE:source - BASE + size])
    return u


def probe_header(stock, module, capacity, *, reported_size=None, extended_version=0):
    from unicorn import UC_HOOK_CODE
    from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                                  UC_ARM_REG_R3, UC_ARM_REG_PC, UC_ARM_REG_SP, UC_ARM_REG_LR)
    u = machine(stock)

    def word(address, value):
        u.mem_write(address, struct.pack('<I', value))

    word(0xA25565B4, BASE)  # current module marker, from the pinned stock image
    word(0xA25565C0, capacity)
    word(0xA18D1A84, 0x20010000)  # ordinary scratch buffer
    word(0x20000218, len(module) if reported_size is None else reported_size)
    word(0x20020000, 0x20020100)
    offset, calls = 0, []

    def ret(value):
        u.reg_write(UC_ARM_REG_R0, value)
        u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR))

    def hook(uc, address, size, context):
        nonlocal offset
        if address == 0x102D86E6:  # seek in an immutable in-memory file
            if uc.reg_read(UC_ARM_REG_R2) != 0:
                raise AssertionError('Unexpected seek origin')
            offset = uc.reg_read(UC_ARM_REG_R1)
            calls.append('seek')
            ret(1)
        elif address == 0x102D86D8:  # read; no filesystem/device implementation
            destination, count = uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2)
            if count > 64:
                raise AssertionError('Header probe read beyond its scope')
            data = module[offset:offset + count]
            if data:
                uc.mem_write(destination, data)
            word(uc.reg_read(UC_ARM_REG_R3), len(data))
            offset += len(data)
            calls.append('read')
            ret(0x04390080)
        elif address == 0x10205784:
            # The pinned current image has a NUL marker at 0x10. Its ctype
            # classification is zero. No general character table is modelled.
            if stock[0x10:0x14] != bytes(4) or module[0x10:0x14] != bytes(4):
                raise ValueError('Unsupported header marker for the ctype fixture')
            ret(0x20020000)
        elif address == 0x101C9A2C:
            if uc.reg_read(UC_ARM_REG_R0) != 0x111:
                raise AssertionError('Unexpected runtime property query')
            ret(extended_version)
        elif address == 0x10170A80:
            count = uc.reg_read(UC_ARM_REG_R1)
            if count > 64:
                raise AssertionError('Unexpected clear length')
            uc.mem_write(uc.reg_read(UC_ARM_REG_R0), bytes(count))
            ret(0)
        elif address == 0x10170AD4:
            destination, source, count = (uc.reg_read(reg) for reg in
                                         (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2))
            if count > 64:
                raise AssertionError('Unexpected copy length')
            uc.mem_write(destination, bytes(uc.mem_read(source, count)))
            ret(destination)

    u.hook_add(UC_HOOK_CODE, hook)
    u.reg_write(UC_ARM_REG_SP, 0x2003E000)
    u.reg_write(UC_ARM_REG_LR, 0x2003F001)
    u.reg_write(UC_ARM_REG_R0, 0x20000000)
    u.reg_write(UC_ARM_REG_R1, 1)
    u.emu_start(0x101B5F37, 0x2003F000, count=100000)
    if u.reg_read(UC_ARM_REG_PC) != 0x2003F000:
        raise AssertionError('Native header probe did not return within its bound')
    return dict(result=u.reg_read(UC_ARM_REG_R0), mocked_file_operations=calls)


def probe_filename(stock, filename):
    """Execute the stock single-name matching loop; directory I/O is excluded."""
    from unicorn import UC_HOOK_CODE
    from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R6, UC_ARM_REG_R8,
                                  UC_ARM_REG_PC, UC_ARM_REG_LR)
    u = machine(stock)
    pattern = StockImage(stock).read(0x11BABB64, 13)
    if pattern != b'EG1610??.BIN\0':
        raise ValueError('Unexpected native EG filename pattern')
    u.mem_write(0x20000000, pattern)
    u.mem_write(0x20000100, filename.encode('ascii') + b'\0')
    u.reg_write(UC_ARM_REG_R8, 0x20000000)
    u.reg_write(UC_ARM_REG_R6, 0x20000100)
    matched = None

    def hook(uc, address, size, context):
        nonlocal matched
        if address in (0x101B6C8E, 0x101B6CC0):
            matched = address == 0x101B6CC0
            uc.emu_stop()
        elif address == 0x101C1F94:
            value = uc.reg_read(UC_ARM_REG_R0)
            uc.reg_write(UC_ARM_REG_R0, value - 32 if 97 <= value <= 122 else value)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    u.hook_add(UC_HOOK_CODE, hook)
    u.emu_start(0x101B6CA1, 0x2003F000, count=10000)
    if matched is None:
        raise AssertionError('Native filename loop did not finish within its bound')
    return matched


def require_private_output(path):
    path = path.resolve()
    private = (ROOT / '.private').resolve()
    if not path.is_relative_to(private) or path == private:
        raise ValueError('Review output must be a new subdirectory of this lab .private/')
    if path.exists():
        raise ValueError('Review output already exists; use a new directory')
    return path


def reviewed_candidate(directory, preset, raw, stock):
    """Admit the exact feature selection, including the independently built grid.

    This is review admission only. In particular a persistent grid review must
    never be mistaken for clearance of its experimental internal storage hooks.
    """
    if preset in ('grid', 'grid-persistent', 'grid-native'):
        from build_grid_firmware import build_image
        candidate = (directory / 'grid.emulator.eg.bin').read_bytes()
        rebuilt, report = build_image(raw, persistent=preset == 'grid-persistent',
                                     native_choice=preset == 'grid-native')
        recorded = json.loads((directory / 'grid.emulator.json').read_text(encoding='utf-8'))
        if recorded != report:
            raise ValueError('Grid report differs from independent rebuild')
        main = directory / 'grid.emulator.main.bin'
    elif preset in PRESETS:
        candidate = (directory / f'{preset}.eg.bin').read_bytes()
        rebuilt, report = build(stock, preset, model='z7')
        main = directory / f'{preset}.main.bin'
    else:
        raise ValueError('Unsupported review preset')
    if candidate != rebuilt or binascii.crc_hqx(candidate, 0):
        raise ValueError('Candidate differs from independent rebuild or has a bad CRC')
    if main.read_bytes() != candidate[:-2]:
        raise ValueError('MAIN must retain the entire candidate except the final CRC')
    return candidate, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / '.private/stock/Z_7_0380.bin')
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--preset', choices=PRESETS + ('grid', 'grid-persistent', 'grid-native'), default='full')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = require_private_output(args.output)
    raw = args.source.read_bytes()
    stock, container = inspect_container(raw)
    candidate, build_report = reviewed_candidate(args.build, args.preset, raw, stock)
    capacity = storage_descriptor(stock)
    checks = []

    def check(name, actual, expected):
        if actual != expected:
            raise AssertionError(f'{name}: expected {expected!r}, got {actual!r}')
        checks.append(dict(name=name, passed=True))

    for name, data in [('stock', stock), (args.preset, candidate)]:
        for extended in (0, 1):
            result = probe_header(stock, data, capacity, extended_version=extended)
            check(f'{name}_native_header_property_{extended}', result['result'], 1)
    check('native_header_rejects_oversize',
          probe_header(stock, stock, capacity, reported_size=capacity + 1)['result'], 11)
    check('native_header_rejects_short_version', probe_header(stock, stock[:40], capacity)['result'], 13)
    for filename, expected in [('EG161080.BIN', True), ('eg161080.bin', True),
                               ('EG16100380.BIN', False), ('EG162080.BIN', False),
                               ('EG161080.BIN.extra', False), ('EG1610.BIN', False)]:
        check('native_name_' + filename, probe_filename(stock, filename), expected)
    report = dict(schema=1, purpose='Offline review only; not hardware installation approval',
                  model='Original Nikon Z7', firmware='C 3.80', preset=args.preset,
                  features=list(build_report['features']),
                  internal_settings_format_changed='settings' in build_report['features'],
                  internal_setting_value_encoding_changed='grid_native' in build_report['features'],
                  installation_assessment=('GRID_NATIVE_FLASH_ASSESSMENT.md'
                      if 'grid_native' in build_report['features'] else
                      'GRID_FLASH_ASSESSMENT.md' if args.preset.startswith('grid') else 'FLASH_ASSESSMENT.md'),
                  installation_cleared=False,
                  stock_container_sha256=sha256(raw), container=container,
                  candidate=dict(filename='EG161080.BIN', size=len(candidate), sha256=sha256(candidate),
                                 main_sha256=sha256(candidate[:-2]), crc_zero=True, independently_rebuilt=True),
                  stock_eg=dict(size=len(stock), sha256=sha256(stock)),
                  storage_descriptor_bytes=capacity, below_descriptor_capacity=len(candidate) <= capacity,
                  native_checks=checks, physical_camera_tested=False, card_written=False,
                  limits=['Selected header and single-name instructions only; file I/O and runtime property mocked.',
                          'No directory enumeration, complete updater admission, erase/program/readback or real boot.',
                          'Same-version camera acceptance and emergency boot recovery remain unverified.',
                          'Stock copies are rollback inputs, not a proven recovery mechanism.',
                          'No full-container header digest was recomputed or validated.'])
    output.mkdir(parents=True, exist_ok=False)
    files = {'candidate/EG161080.BIN': candidate, 'stock-module/EG161080.BIN': stock,
             'stock-container/Z_7_0380.bin': raw}
    for name, data in files.items():
        path = output / name
        path.parent.mkdir(exist_ok=True)
        with path.open('xb') as handle:
            handle.write(data)
        if sha256(path.read_bytes()) != sha256(data):
            raise RuntimeError('Review bundle readback mismatch')
    (output / 'review.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    (output / 'READ-ME-FIRST.txt').write_text(
        'OFFLINE REVIEW ONLY. CAMERA INSTALLATION IS NOT YET VALIDATED.\n'
        'Read the project FLASH_ASSESSMENT.md before any card/camera write.\n'
        f"Read the exact-candidate assessment: {report['installation_assessment']}\n"
        'candidate/ contains the full independent modified EG module with its CRC.\n'
        'stock-module/ and stock-container/ are untouched inputs, kept separately.\n'
        'These stock files do not establish recovery after an inoperable boot.\n'
        'Do not place both stock and candidate EG files on the same card.\n'
        'This tool did not access a camera, card reader or removable drive.\n', encoding='utf-8')
    print(json.dumps(dict(output=str(output), native_checks=len(checks), private_files_verified=len(files),
                          candidate_sha256=sha256(candidate), camera_written=False), indent=2))


if __name__ == '__main__':
    main()
