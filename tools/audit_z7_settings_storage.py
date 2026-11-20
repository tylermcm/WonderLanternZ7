"""Execute the ARM settings journal against an independent byte-format model.

SPDX-License-Identifier: MIT. Storage transport is explicitly in-memory. Native
card, cache, close/flush, task concurrency and physical durability are not tested.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib

from audit_splash_image import MEM
from audit_z7_module_host import HostFixture
from build_z7_module_host import ROOT, STATE

DEFAULTS = (0, 15, 1, 0, 5, 10, 127, 7, 0, 127)
LOADED, DEFAULTED, IO_FAILED, AMBIGUOUS, INVALID, SAVED, UNCHANGED, VERIFY_FAILED = range(8)


def payload(settings):
    data = bytearray(struct.pack('<16I', 0x3143375a, 1, 0x03800007, 0, *settings, 0, 0))
    struct.pack_into('<I', data, 12, zlib.crc32(data))
    return bytes(data)


def seal(data):
    data = bytearray(data)
    data[12:16] = bytes(4)
    struct.pack_into('<I', data, 12, zlib.crc32(data))
    return bytes(data)


def record(settings, generation):
    return seal(struct.pack('<4I', 0x314a375a, 1, generation, 0) + payload(settings))


def valid(data):
    if len(data) != 80 or data[:8] != b'Z7J1\1\0\0\0' or seal(data) != data:
        return False
    p = data[16:]
    if p[:12] != b'Z7C1\1\0\0\0\7\0\x80\3' or seal(p) != p or p[56:] != bytes(8):
        return False
    values = struct.unpack_from('<10I', p, 16)
    return not values[0] & ~3 and 0 < values[1] <= 31 and all(v <= 15 for v in values[2:6]) and all(v <= 255 for v in values[6:])


def audit(raw, host, packet, module):
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Exact host/module required')
    f = HostFixture(raw, host, packet)
    if f.call(host['symbols']['z7_module_load_once'], STATE) != 8:
        raise AssertionError('Storage diagnostic failed initialization')
    base, symbols = f.words()[12], module['symbols']
    checks = []

    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good:
            raise AssertionError(name)

    def ptr(name):
        return base + symbols['z7_storage_probe_' + name]

    def read(name, size=4):
        return bytes(f.u.mem_read(ptr(name), size))

    def number(name):
        return int.from_bytes(read(name), 'little')

    def setnumber(name, value):
        f.u.mem_write(ptr(name), struct.pack('<I', value))

    def invoke(name, *args):
        return f.call(base + symbols[name], *args)

    def reset(settings=DEFAULTS):
        f.u.mem_write(base + module['image_bytes'], bytes(module['bss_bytes']))
        f.u.mem_write(ptr('status'), struct.pack('<2I', 1, 1))
        f.u.mem_write(ptr('model'), struct.pack('<10I', *settings))
        f.u.mem_write(ptr('output'), b'\xa5' * 40)
        f.u.mem_write(ptr('record'), b'\xcd' * 80)
        setnumber('write_prefix', 80)

    def install(slot, data):
        assert len(data) == 80
        f.u.mem_write(ptr('slots') + slot * 80, data)
        f.u.mem_write(ptr('status') + slot * 4, bytes(4))

    def info():
        return struct.unpack('<4I', read('info', 16))

    def load():
        return invoke('z7_storage_probe_load')

    def save():
        return invoke('z7_storage_probe_save')

    reset()
    check('missing-slots-load-defaults-without-writing', load() == DEFAULTED and read('output', 40) == struct.pack('<10I', *DEFAULTS) and not number('writes') and info() == (0, 0, 2, 0))
    check('initial-save-writes-slot0-generation0', save() == SAVED and info() == (1, 0, 0, 0) and read('slots', 80) == record(DEFAULTS, 0))
    before = read('slots', 160)
    check('same-settings-save-is-write-free', save() == UNCHANGED and number('writes') == 1 and read('slots', 160) == before)
    edited = (3, 31, 15, 2, 4, 8, 255, 0, 5, 128)
    f.u.mem_write(ptr('model'), struct.pack('<10I', *edited))
    check('changed-settings-alternate-to-slot1', save() == SAVED and info() == (3, 0, 1, 1) and number('last_slot') == 1 and read('slots', 80) == before[:80])
    check('changed-record-matches-independent-format', read('slots', 160)[80:] == record(edited, 1))
    check('restart-load-selects-newest-valid-payload', load() == LOADED and read('output', 40) == struct.pack('<10I', *edited))

    for generation in (0, 1, 0x7fffffff, 0x80000000, 0xfffffffe, 0xffffffff):
        reset(edited)
        check('encode-generation-' + hex(generation), invoke('z7_storage_record_encode', ptr('model'), generation, ptr('record'), 80) == 1 and read('record', 80) == record(edited, generation))
        check('decode-generation-' + hex(generation), invoke('z7_storage_record_decode', ptr('record'), 80, ptr('output'), ptr('generation')) == 1 and number('generation') == generation and read('output', 40) == struct.pack('<10I', *edited))
    for bit in range(640):
        reset()
        damaged = bytearray(record(edited, 29))
        damaged[bit // 8] ^= 1 << (bit % 8)
        f.u.mem_write(ptr('record'), bytes(damaged))
        setnumber('generation', 0x55aa55aa)
        check('single-bit-damage-' + str(bit) + '-rejects-before-publication', invoke('z7_storage_record_decode', ptr('record'), 80, ptr('output'), ptr('generation')) == 0 and read('output', 40) == b'\xa5' * 40 and number('generation') == 0x55aa55aa)
    for offset, value in ((0, 0), (4, 2), (16, 0), (20, 2), (24, 0x03800072), (32, 4), (36, 0), (36, 32), (40, 16), (56, 256), (72, 1), (76, 1)):
        reset()
        damaged = bytearray(record(DEFAULTS, 1))
        struct.pack_into('<I', damaged, offset, value)
        if offset >= 16:
            damaged[16:] = seal(damaged[16:])
        damaged = seal(damaged)
        f.u.mem_write(ptr('record'), damaged)
        check('resealed-invalid-field-' + str(offset) + '-' + str(value), not valid(damaged) and invoke('z7_storage_record_decode', ptr('record'), 80, ptr('output'), ptr('generation')) == 0 and read('output', 40) == b'\xa5' * 40)
    for size in (0, 1, 64, 79, 81, 128, 0xffffffff):
        reset()
        install(0, record(DEFAULTS, 0))
        f.u.mem_write(ptr('record'), record(DEFAULTS, 0))
        check('wrong-record-length-' + str(size), invoke('z7_storage_record_decode', ptr('record'), size, ptr('output'), ptr('generation')) == 0 and invoke('z7_storage_record_encode', ptr('model'), 0, ptr('record'), size) == 0 and read('record', 80) == record(DEFAULTS, 0))

    for a, b, expected in ((0, 1, 1), (1, 0, 0), (0xffffffff, 0, 1), (0, 0xffffffff, 0), (0xfffffffe, 1, 1), (0x7fffffff, 0x80000000, 1)):
        reset()
        install(0, record(DEFAULTS, a)); install(1, record(edited, b))
        check('serial-order-' + hex(a) + '-' + hex(b), load() == LOADED and info()[2] == expected and read('output', 40) == struct.pack('<10I', *(edited if expected else DEFAULTS)))
    for a, b in ((0, 0x80000000), (0x80000000, 0), (41, 41)):
        reset(edited)
        install(0, record(DEFAULTS, a)); install(1, record(edited, b))
        before = read('slots', 160)
        check('ambiguous-order-load-preserves-model-' + hex(a) + '-' + hex(b), load() == AMBIGUOUS and read('output', 40) == b'\xa5' * 40)
        check('ambiguous-order-save-does-not-write-' + hex(a) + '-' + hex(b), save() == AMBIGUOUS and not number('writes') and read('slots', 160) == before)
    reset()
    install(0, record(DEFAULTS, 9)); install(1, record(DEFAULTS, 9))
    check('identical-tied-slots-accepted', load() == LOADED and info() == (3, 0, 0, 9) and save() == UNCHANGED)
    reset(edited); install(0, record(DEFAULTS, 0xffffffff))
    check('save-wraps-generation-and-reloads', save() == SAVED and info()[3] == 0 and load() == LOADED and info()[2] == 1 and read('output', 40) == struct.pack('<10I', *edited))

    for active in (0, 1):
        old = record(DEFAULTS, 9)
        target = active ^ 1
        for prefix in range(81):
            for reported_result in (0, 2):
                reset(edited); install(active, old); install(target, b'\xcc' * 80)
                setnumber('write_prefix', prefix); setnumber('write_result', reported_result)
                expected = IO_FAILED if reported_result else SAVED if prefix == 80 else VERIFY_FAILED
                tag = f'slot{active}-prefix{prefix}-status{reported_result}'
                check(tag + '-save-result', save() == expected and number('writes') == 1 and number('last_slot') == target)
                check(tag + '-previous-valid-slot-untouched', read('slots', 160)[active * 80:(active + 1) * 80] == old)
                check(tag + '-restart-selects-valid-record', load() == LOADED and read('output', 40) == struct.pack('<10I', *(edited if prefix == 80 else DEFAULTS)))
    # A previous unsuccessful close can leave a fully written newer record.
    reset(edited); install(0, record(DEFAULTS, 5)); setnumber('write_result', 2)
    check('uncertain-commit-reports-failure', save() == IO_FAILED and info()[2:] == (0, 5))
    setnumber('write_result', 0)
    check('rescan-recognizes-uncertain-commit-without-rewriting', save() == UNCHANGED and number('writes') == 1 and info()[2:] == (1, 6))
    for read_error in (1, 2, 3):
        reset(edited); install(0, record(DEFAULTS, 12)); setnumber('read_error', read_error)
        expected = VERIFY_FAILED if read_error == 3 else IO_FAILED
        check('read-error-' + str(read_error) + '-save-fails-closed', save() == expected and number('writes') == int(read_error == 3) and read('slots', 80) == record(DEFAULTS, 12))
    for active in (0, 1):
        for prefix in range(81):
            reset(edited)
            older = record((1, *DEFAULTS[1:]), 7)
            prior = record(DEFAULTS, 8)
            install(active, prior); install(active ^ 1, older)
            setnumber('write_prefix', prefix)
            mixed = record(edited, 9)[:prefix] + older[prefix:]
            expected_result = SAVED if mixed == record(edited, 9) else VERIFY_FAILED
            expected_model = struct.pack('<10I', *DEFAULTS)
            if valid(mixed) and struct.unpack_from('<I', mixed, 8)[0] > 8:
                expected_model = mixed[32:72]
            tag = f'older-slot{active ^ 1}-prefix{prefix}'
            check(tag + '-readback-status', save() == expected_result)
            check(tag + '-restart-reference', load() == LOADED and read('output', 40) == expected_model and read('slots', 160)[active * 80:(active + 1) * 80] == prior)
    for status in (2, 4, 0xffffffff):
        reset(edited); install(0, record(DEFAULTS, 12))
        f.u.mem_write(ptr('status') + 4, struct.pack('<I', status))
        check('unknown-slot-status-' + str(status) + '-loads-known-valid', load() == LOADED and info() == (1, 2, 0, 12))
        check('unknown-slot-status-' + str(status) + '-blocks-save', save() == IO_FAILED and not number('writes'))
    reset(); f.u.mem_write(ptr('status'), struct.pack('<2I', 2, 1))
    check('unavailable-is-not-absent-or-default-reset', load() == IO_FAILED and read('output', 40) == b'\xa5' * 40 and save() == IO_FAILED and not number('writes'))
    reset(edited); install(0, record(DEFAULTS, 12)); f.u.mem_write(ptr('status') + 4, struct.pack('<I', 3))
    check('wrong-length-slot-is-invalid-not-io-unavailable', load() == LOADED and info() == (1, 0, 0, 12) and save() == SAVED and read('slots', 80) == record(DEFAULTS, 12))
    reset(); f.u.mem_write(ptr('status'), struct.pack('<2I', 3, 3))
    check('both-known-invalid-lengths-use-defaults', load() == DEFAULTED and info() == (0, 0, 2, 0) and not number('writes'))
    reset(); setnumber('mutate_on_read', 1)
    check('save-stages-coherent-input-before-io-callbacks', save() == SAVED and read('slots', 80) == record(DEFAULTS, 0) and number('model') == 3)
    reset((4, *DEFAULTS[1:]))
    check('invalid-model-save-performs-no-io', save() == INVALID and not number('reads') and not number('writes'))
    # Caller-owned capacity supports overlap; output generation stays separate.
    scratch = MEM + 0x20000
    f.u.mem_write(scratch, struct.pack('<10I', *edited) + bytes(80))
    check('encode-overlapping-settings-and-record', invoke('z7_storage_record_encode', scratch, 7, scratch, 80) == 1 and bytes(f.u.mem_read(scratch, 80)) == record(edited, 7))
    check('decode-overlapping-record-and-settings', invoke('z7_storage_record_decode', scratch, 80, scratch + 16, ptr('generation')) == 1 and bytes(f.u.mem_read(scratch + 16, 40)) == struct.pack('<10I', *edited) and number('generation') == 7)
    reset()
    table = base + symbols['storage_io']
    for name, function, args, expected in (
        ('load-null-io', 'z7_storage_load', (0, ptr('output'), ptr('info')), INVALID),
        ('load-null-output', 'z7_storage_load', (table, 0, ptr('info')), INVALID),
        ('load-null-info', 'z7_storage_load', (table, ptr('output'), 0), INVALID),
        ('save-null-io', 'z7_storage_save', (0, ptr('model'), ptr('info')), INVALID),
        ('save-null-model', 'z7_storage_save', (table, 0, ptr('info')), INVALID),
        ('save-null-info', 'z7_storage_save', (table, ptr('model'), 0), INVALID),
        ('encode-null-model', 'z7_storage_record_encode', (0, 0, ptr('record'), 80), 0),
        ('encode-null-output', 'z7_storage_record_encode', (ptr('model'), 0, 0, 80), 0),
        ('decode-null-input', 'z7_storage_record_decode', (0, 80, ptr('output'), ptr('generation')), 0),
        ('decode-null-output', 'z7_storage_record_decode', (ptr('record'), 80, 0, ptr('generation')), 0),
        ('decode-null-generation', 'z7_storage_record_decode', (ptr('record'), 80, ptr('output'), 0), 0)):
        prior = bytes(f.u.mem_read(base + module['image_bytes'], module['bss_bytes']))
        check(name + '-preserves-output-and-performs-no-io', invoke(function, *args) == expected and bytes(f.u.mem_read(base + module['image_bytes'], module['bss_bytes'])) == prior)
    for read_callback, write_callback in ((0, 0), (0, base + symbols['storage_write']), (base + symbols['storage_read'], 0)):
        f.u.mem_write(scratch, struct.pack('<3I', 0, read_callback, write_callback))
        check('missing-io-callbacks-' + str(bool(read_callback)) + '-' + str(bool(write_callback)), invoke('z7_storage_save', scratch, ptr('model'), ptr('info')) == INVALID and not number('reads') and not number('writes'))
    check('host-guards-preserved-through-policy-tests', f.words()[60:] == (0xa5a5a5a5,) * 4)
    return dict(passed=True, checks=checks, main_sha256=host['main_payload_sha256'], module_sha256=module['module_sha256'],
                record_bytes=80, settings_payload_bytes=64, single_bit_corruptions=640, interrupted_prefixes_per_slot=81,
                native_arm_policy_executes=True, independent_python_wire_reference=True,
                supplied_storage_transport=True, native_file_io_implemented=False, worker_integration=False,
                physical_cache_or_durability_verified=False, camera_access=False, physical_card_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--module', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists():
        p.error('Choose a new private output')
    result = audit((a.build / 'module-host.emulator.main.bin').read_bytes(), json.loads((a.build / 'module-host.emulator.json').read_text(encoding='utf-8')),
                   (a.module / 'Z7APP.BIN').read_bytes(), json.loads((a.module / 'module.json').read_text(encoding='utf-8')))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__':
    main()
