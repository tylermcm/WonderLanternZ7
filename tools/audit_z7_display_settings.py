"""Compiled ARM settings-model and independent wire-format verification.

SPDX-License-Identifier: MIT. No camera addresses, native GUI or card writes are
used by the model. Its diagnostic loads through the actual compiled SD host;
file/kernel/heap services remain supplied by the instruction fixture.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import zlib
from audit_z7_module_host import HostFixture
from build_z7_module_host import ROOT, STATE
from audit_splash_image import MEM

DEFAULT = [0, 15, 1, 0, 5, 10, 127, 7, 0, 127]


def wire(model):
    words = [0x3143375a, 1, 0x03800007, 0] + list(model) + [0, 0]
    packet = bytearray(struct.pack('<16I', *words))
    struct.pack_into('<I', packet, 12, zlib.crc32(packet))
    return bytes(packet)


def reseal(packet):
    packet = bytearray(packet); packet[12:16] = bytes(4)
    struct.pack_into('<I', packet, 12, zlib.crc32(packet))
    return bytes(packet)


def audit(raw, host, packet, module):
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Host/module fingerprint mismatch')
    f = HostFixture(raw, host, packet)
    if f.call(host['symbols']['z7_module_load_once'], STATE) != 8: raise AssertionError('load')
    base = f.words()[12]
    address = lambda name: base + module['symbols']['z7_settings_' + name]
    def model(): return list(struct.unpack('<10I', f.u.mem_read(address('model'), 40)))
    def put(values): f.u.mem_write(address('model'), struct.pack('<10I', *values))
    def call(op, a=0, b=0, c=0): return f.call(address('operation'), op, a, b, c)
    checks = []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    check('native-initializer-loads-complete-disabled-default-model', model() == DEFAULT)
    before = bytes(f.u.mem_read(base, module['image_bytes'] + module['bss_bytes']))
    check('independent-default-wire-vector', call(1, 64) == 1 and bytes(f.u.mem_read(address('output'), 64)) == wire(DEFAULT))
    after = bytes(f.u.mem_read(base, len(before)))
    permitted = address('output') - base
    check('encode-changes-only-owned-64-byte-output', before[:permitted] == after[:permitted] and before[permitted + 64:] == after[permitted + 64:])
    invalid_model = [0xa5a5a5a5] * 10
    reference = wire(DEFAULT)
    for bit in range(512):
        bad = bytearray(reference); bad[bit // 8] ^= 1 << (bit % 8)
        f.u.mem_write(address('input'), bytes(bad)); put(invalid_model)
        check(f'wire-single-bit-damage-{bit}-preserves-output', call(2, 64) == 0 and model() == invalid_model)
    invalid_fields = [(0, 0), (4, 0), (4, 2), (8, 0x01700008), (16, 4), (20, 0), (20, 32), (56, 1), (60, 1)]
    invalid_fields += [(24 + i * 4, 16) for i in range(4)] + [(40 + i * 4, 256) for i in range(4)]
    for offset, value in invalid_fields:
        bad = bytearray(reference); struct.pack_into('<I', bad, offset, value)
        f.u.mem_write(address('input'), reseal(bad)); put(invalid_model)
        check(f'sealed-invalid-field-{offset}-{value}-preserves-output', call(2, 64) == 0 and model() == invalid_model)
    for size in (0, 1, 63, 65, 0xffffffff):
        f.u.mem_write(address('input'), reference); put(invalid_model)
        check(f'wrong-decode-length-{size}', call(2, size) == 0 and model() == invalid_model)
        put(DEFAULT); f.u.mem_write(address('output'), b'\xa5' * 64)
        check(f'wrong-encode-length-{size}', call(1, size) == 0 and bytes(f.u.mem_read(address('output'), 64)) == b'\xa5' * 64)
    rng = random.Random(0x03800007)
    for i in range(64):
        values = [rng.randrange(4), rng.randrange(1, 32)] + [rng.randrange(16) for _ in range(4)] + [rng.randrange(256) for _ in range(4)]
        f.u.mem_write(address('input'), wire(values)); put(invalid_model)
        check(f'independent-wire-decode-{i}', call(2, 64) == 1 and model() == values)
        check(f'independent-wire-reencode-{i}', call(1, 64) == 1 and bytes(f.u.mem_read(address('output'), 64)) == wire(values))
    for pages in range(1, 32):
        values = list(DEFAULT); values[1] = pages
        for current in range(5):
            put(values)
            expected = next((current + step) % 5 for step in range(1, 6) if pages & (1 << ((current + step) % 5)))
            check(f'page-cycle-enabled-{pages}-from-{current}', call(5, current) == expected and model() == values)
        for page in range(5):
            for enabled in (0, 1):
                put(values); proposed = pages | (1 << page) if enabled else pages & ~(1 << page)
                expected = list(values); expected[1] = proposed or pages
                check(f'page-enable-{pages}-{page}-{enabled}', call(3, page, enabled) == bool(proposed) and model() == expected)
    for operation, limit in ((6, 8), (7, 4)):
        for page in range(4):
            for bit in range(limit):
                for enabled in (0, 1):
                    values = [3, 16, 15, 15, 15, 15, 255, 255, 255, 255]
                    put(values); expected = list(values)
                    index = (6 if operation == 6 else 2) + page
                    expected[index] = expected[index] | (1 << bit) if enabled else expected[index] & ~(1 << bit)
                    check(f'isolated-setting-{operation}-{page}-{bit}-{enabled}', call(operation, page, bit, enabled) == 1 and model() == expected)
    for page in range(4):
        values = [3, 16, 15, 15, 15, 15, 255, 255, 255, 255]; put(values)
        expected = list(values); expected[2 + page] = DEFAULT[2 + page]; expected[6 + page] = DEFAULT[6 + page]
        check(f'preset-reset-{page}-preserves-master-battery-and-page-enables', call(4, page) == 1 and model() == expected)
    for flag in (0, 1):
        for enabled in (0, 1):
            values = list(DEFAULT); put(values); expected = list(values); expected[0] = enabled << flag
            check(f'independent-global-flag-{flag}-{enabled}', call(8, flag, enabled) == 1 and model() == expected)
    for op, a, b, c in ((3, 5, 1, 0), (3, 0, 2, 0), (4, 4, 0, 0), (6, 4, 0, 1), (6, 0, 8, 1),
                         (7, 0, 4, 1), (7, 0, 0, 2), (8, 2, 1, 0), (8, 0, 2, 0)):
        put(DEFAULT); check(f'invalid-edit-{op}-{a}-{b}-{c}', call(op, a, b, c) == 0 and model() == DEFAULT)
    put(DEFAULT); check('invalid-current-page-rejected', call(5, 5) == 0xffffffff and model() == DEFAULT)
    put(invalid_model); f.u.mem_write(address('output'), b'\xa5' * 64)
    check('invalid-model-encode-preserves-output', call(1, 64) == 0 and bytes(f.u.mem_read(address('output'), 64)) == b'\xa5' * 64)
    # Call public C entrypoints directly for their pointer/buffer contracts.
    native = lambda name, *args: f.call(base + module['symbols']['z7_settings_' + name], *args)
    scratch = MEM + 0x90000
    put(DEFAULT); f.u.mem_write(scratch, b'\xa5' * 96)
    check('unaligned-wire-output-retains-both-canaries', native('encode', address('model'), scratch + 3, 64) == 1 and
          bytes(f.u.mem_read(scratch, 96)) == b'\xa5' * 3 + reference + b'\xa5' * 29)
    put(invalid_model)
    check('unaligned-wire-input-decodes', native('decode', scratch + 3, 64, address('model')) == 1 and model() == DEFAULT)
    f.u.mem_write(scratch, struct.pack('<10I', *DEFAULT) + b'\xa5' * 56)
    check('overlapping-model-and-wire-encode-stages-before-write', native('encode', scratch, scratch, 64) == 1 and
          bytes(f.u.mem_read(scratch, 96)) == reference + b'\xa5' * 32)
    check('overlapping-wire-and-model-decode-stages-before-write', native('decode', scratch, 64, scratch) == 1 and
          bytes(f.u.mem_read(scratch, 96)) == struct.pack('<10I', *DEFAULT) + reference[40:] + b'\xa5' * 32)
    for name, arguments, expected in (
        ('valid', [0], 0), ('encode', [0, scratch, 64], 0), ('encode', [address('model'), 0, 64], 0),
        ('decode', [0, 64, address('model')], 0), ('decode', [address('input'), 64, 0], 0),
        ('next', [0, 0], 0xffffffff), ('page', [0, 0, 1], 0), ('reset', [0, 0], 0)):
        check('null-pointer-' + name + '-' + str(arguments), native(name, *arguments) == expected)
    return dict(passed=True, checks=checks, module_sha256=module['module_sha256'], main_sha256=host['main_payload_sha256'],
                wire_bytes=64, defaults_wire_sha256=hashlib.sha256(reference).hexdigest(), model_only=True,
                menu_binding=False, card_read_or_write=False, camera_access=False, supplied_boundaries=['File/kernel/heap for diagnostic module loading'])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True); p.add_argument('--module', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); args = p.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists(): p.error('Choose a new private output')
    r = audit((args.build / 'module-host.emulator.main.bin').read_bytes(), json.loads((args.build / 'module-host.emulator.json').read_text()),
              (args.module / 'Z7APP.BIN').read_bytes(), json.loads((args.module / 'module.json').read_text()))
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(r, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(r['checks']))))


if __name__ == '__main__': main()
