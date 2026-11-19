"""Build an original-Z7 SD module host experiment in a new private directory.

SPDX-License-Identifier: MIT. Independent emulator-only research. No update
container, card staging, installation clearance or physical camera operation.
"""
import argparse
import binascii
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'z7-firmware-extensions/src'))
from z30_extensions.assembly import assemble, constant, jump
from z30_extensions.container import extract_eg, Z7_CONTAINER_SHA256
from z30_extensions.plan import Plan
from z30_extensions.platform import z7_380 as platform

COMPONENT = ROOT / 'z7-native-modules'
STATE, STATE_BYTES, MAGIC = 0xa9700000, 256, 0x5a37484d
CURSOR, HEAP_SITE, AUTOOP_BINDING = 0xa18fd738, 0x101e3da0, 0xa1822db0
HEAP_EXPECTED = bytes.fromhex('504933480860bde8104005e7')
ZIG = ROOT / '.private/toolchain/zig-x86_64-windows-0.15.2/zig.exe'
PRESET = 'sd-module-host-emulator-only'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def compile_host(base, zig=ZIG):
    """Fixed-address, BSS-free host; all writable state is explicitly reserved."""
    temporary = ROOT / '.private/tmp'
    temporary.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment['ZIG_GLOBAL_CACHE_DIR'] = str(ROOT / '.private/toolchain/zig-cache')
    environment['ZIG_LOCAL_CACHE_DIR'] = str(ROOT / '.private/tmp/zig-cache')
    with tempfile.TemporaryDirectory(prefix='z7-module-host-', dir=temporary) as directory:
        folder = Path(directory)
        objects = []
        for index, source in enumerate(('module.c', 'z7_380.c')):
            obj = folder / f'{index}.o'
            subprocess.run([str(zig), 'cc', '-target', 'thumb-freestanding-eabi', '-mcpu=cortex_a9',
                '-mfloat-abi=soft', '-Os', '-ffreestanding', '-fno-builtin', '-fno-unwind-tables',
                '-fno-asynchronous-unwind-tables', '-fno-stack-protector', '-Wall', '-Wextra', '-Werror',
                '-I', str(COMPONENT / 'sdk'), '-I', str(COMPONENT / 'host'),
                '-c', str(COMPONENT / 'host' / source), '-o', str(obj)], check=True, env=environment)
            objects.append(str(obj))
        linker = folder / 'host.ld'
        linker.write_text(f'''ENTRY(z7_autoop_init)
SECTIONS {{
 . = {base};
 .host : {{ *(.text .text.*) *(.rodata .rodata.*) *(.data .data.*) }}
 .bss (NOLOAD) : {{ *(.bss .bss.*) *(COMMON) }}
 /DISCARD/ : {{ *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) }}
}}
ASSERT(SIZEOF(.bss) == 0, "Host must not contain unreserved BSS");
''', encoding='utf-8')
        elf = folder / 'host.elf'
        subprocess.run([str(zig), 'ld.lld', '-T', str(linker), '--no-undefined',
                        *objects, '-o', str(elf)], check=True, env=environment)
        data = elf.read_bytes()
    shoff = struct.unpack_from('<I', data, 32)[0]
    stride, count = struct.unpack_from('<HH', data, 46)
    if stride != 40:
        raise ValueError('Unexpected host ELF')
    sections = [struct.unpack_from('<10I', data, shoff + i * stride) for i in range(count)]
    allocated = [s for s in sections if s[2] & 2 and s[5]]
    if len(allocated) != 1 or allocated[0][1] != 1 or allocated[0][3] != base:
        raise ValueError('Host must have exactly one allocated fixed-address image')
    section = allocated[0]
    code = data[section[4]:section[4] + section[5]]
    if not 0 < len(code) < 16384:
        raise ValueError('Unexpected host image size')
    symbols = {}
    for section in sections:
        if section[1] != 2:
            continue
        strings = sections[section[6]]
        names = data[strings[4]:strings[4] + strings[5]]
        for offset in range(section[4], section[4] + section[5], 16):
            name, value, _, _, _, index = struct.unpack_from('<IIIBBH', data, offset)
            label = names[name:].split(b'\0', 1)[0].decode()
            if label and index == 0:
                raise ValueError('Unresolved host symbol: ' + label)
            if label.startswith('z7_'):
                symbols[label] = value
    return code, symbols


def build_image(container, zig=ZIG):
    if sha(container) != Z7_CONTAINER_SHA256:
        raise ValueError('Requires exact original Z7 C 3.80 container')
    plan = Plan(extract_eg(container), platform)
    # Original AUTOOP callback binding and original APPIDLE task descriptor.
    if plan.image.words(AUTOOP_BINDING, 1) != (0x102697f5,):
        raise ValueError('Unexpected original AUTOOP callback')
    descriptor = plan.image.read(0x11f9a92c, 28)
    if struct.unpack_from('<4I', descriptor) != (1, 28, 8192, 0) or descriptor[16:24] != b'APPIDLE\0':
        raise ValueError('Unexpected native task descriptor')
    if plan.image.words(0x101e3ee4, 1) != (CURSOR,) or plan.image.words(0x101e3e70, 1) != (STATE,):
        raise ValueError('Unexpected native workspace')
    code, symbols = compile_host(plan.address, zig)
    host_address = plan.alloc(code)
    cold_address = plan.alloc(bytes(160))
    # Preserve original initializer's stack unwind and tail continuation. R0
    # still reports the original workspace base; only the monotonic cursor moves.
    cold = f'''push {{r2,r3}}; mrs r2,apsr; push {{r2,r3}};
        {constant('r0', STATE)} mov r2,r0; movs r3,#0; movs r1,#64;
        clear: str r3,[r2],#4; subs r1,#1; bne clear;
        {constant('r2', STATE + 240)} {constant('r3', 0xa5a5a5a5)}
        str r3,[r2]; str r3,[r2,#4]; str r3,[r2,#8]; str r3,[r2,#12];
        {constant('r2', STATE + 32)} {constant('r3', MAGIC)} str r3,[r2];
        dmb sy; pop {{r2,r3}}; msr APSR_nzcvq,r2; pop {{r2,r3}};
        {constant('r1', CURSOR)} {constant('r0', STATE + STATE_BYTES)} str r0,[r1];
        {constant('r0', STATE)} pop.w {{r4,lr}};
        .balign 4; ldr.w pc,[pc,#0]; .word {0x101e3bb9};
    '''
    plan.put(cold_address, assemble(cold, cold_address, 160))
    plan.edit(HEAP_SITE, jump(HEAP_SITE, cold_address, 12),
              'Reserve isolated module host state before native workspace allocations', expected=HEAP_EXPECTED)
    plan.edit(AUTOOP_BINDING, struct.pack('<I', symbols['z7_autoop_init']),
              'Call original AUTOOP initializer before scheduling the isolated module loader',
              expected=struct.pack('<I', 0x102697f5))
    output, report = plan.finish()
    report.update(preset=PRESET, emulator_only=True, candidate_cleared=False,
        container_sha256=Z7_CONTAINER_SHA256, main_payload_size=len(output) - 2,
        main_payload_sha256=sha(output[:-2]), host_address=hex(host_address),
        host_bytes=len(code), host_sha256=sha(code), symbols=symbols,
        state=hex(STATE), state_bytes=STATE_BYTES, cold=hex(cold_address),
        module_path='A:\\Z7APP.BIN', module_target='0x03800007',
        source_files={str(p.relative_to(ROOT)).replace('\\', '/'): sha(p.read_bytes())
                      for p in sorted([*(COMPONENT / 'host').glob('*'), *(COMPONENT / 'sdk').glob('*')]) if p.is_file()})
    report['limitations'] += ['Boot, filesystem, cache and task contracts need scoped validation; no hardware clearance.',
                             'Separate stock-based no-feature probe; does not include the installed grid trial.']
    return output, report


def validate_candidate(path, report_path, stock_path, zig=ZIG):
    expected, report = build_image(Path(stock_path).read_bytes(), zig)
    actual = json.loads(Path(report_path).read_text(encoding='utf-8'))
    if (Path(path).read_bytes() != expected[:-2] or actual != report or binascii.crc_hqx(expected, 0)):
        raise ValueError('Module host candidate or report differs from independent rebuild')
    return dict(modified=True, independently_rebuilt=True, sha256=sha(expected[:-2]),
                size=len(expected)-2, preset=PRESET, camera_verified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / '.private/stock/Z_7_0380.bin')
    parser.add_argument('--zig', type=Path, default=ZIG)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists():
        parser.error('Choose a new output directory under .private')
    eg, report = build_image(args.source.read_bytes(), args.zig.resolve())
    repeated, second = build_image(args.source.read_bytes(), args.zig.resolve())
    if eg != repeated or report != second or binascii.crc_hqx(eg, 0):
        raise RuntimeError('Host build is not deterministic or CRC failed')
    output.mkdir(parents=True)
    (output / 'module-host.emulator.eg.bin').write_bytes(eg)
    (output / 'module-host.emulator.main.bin').write_bytes(eg[:-2])
    (output / 'module-host.emulator.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(main_bytes=len(eg)-2, main_sha256=sha(eg[:-2]),
                         host_bytes=report['host_bytes'], symbols=report['symbols'],
                         reproducible=True, eg_crc_zero=True, emulator_only=True)))


if __name__ == '__main__':
    main()
