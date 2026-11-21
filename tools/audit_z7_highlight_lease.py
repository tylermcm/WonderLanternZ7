"""Execute compiled lease publication with explicit reader/writer interleavings.

SPDX-License-Identifier: MIT. This tests module publication, not native writer
serialization, allocation lifetime, physical scheduling, or camera recovery.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_R0
from audit_splash_image import NativePNG, STOCK_SHA, MEM, STACK, STOP
from audit_z7_highlight_submission import enter, returned
from build_z7_module import ROOT, HEADER, build
from build_z7_module_host import ZIG

CODE = MEM + 0x20000


def audit(stock, packet, metadata):
    if hashlib.sha256(stock).hexdigest() != STOCK_SHA:
        raise ValueError('Exact stock main required')
    f = NativePNG(stock)
    image = bytearray(packet[HEADER:HEADER + metadata['image_bytes']])
    for off in metadata['relocations']:
        struct.pack_into('<I', image, off, struct.unpack_from('<I', image, off)[0] + CODE)
    f.u.mem_write(CODE, bytes(image) + bytes(metadata['bss_bytes']))
    symbols = metadata['symbols']
    pub, inp, out = (CODE + symbols['z7_hl_' + n] for n in ('publication', 'input', 'output'))
    def word(p): return int.from_bytes(f.u.mem_read(p, 4), 'little')
    def write(p, v): f.u.mem_write(p, struct.pack('<I', v))
    def call(n): return f.call(CODE + symbols['z7_hl_' + n])
    checks = []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    check('initial-invalid-lease-readable-with-zero-serial', call('read') == 1 and bytes(f.u.mem_read(out, 252)) == bytes(252))
    first = struct.pack('<62I', *range(1, 63))
    f.u.mem_write(inp, first)
    check('publishes-entire-context-baseline-and-expected-parameters', call('publish') == 1 and call('read') == 1 and
          word(out) == 1 and bytes(f.u.mem_read(out + 4, 248)) == first)
    write(pub, word(pub) | 1)
    before = bytes(f.u.mem_read(pub, 260))
    f.u.mem_write(out, b'\xa5' * 252)
    check('busy-reader-writer-return-without-partial-output-or-mutation', call('read') == call('publish') == 0 and
          bytes(f.u.mem_read(out, 252)) == b'\xa5' * 252 and bytes(f.u.mem_read(pub, 260)) == before)
    write(pub, 0xfffffffe)
    second = struct.pack('<62I', *range(101, 163))
    f.u.mem_write(inp, second)
    check('sequence-wrap-retains-monotonic-serial-and-whole-record', call('publish') == 1 and word(pub) == 0 and
          call('read') == 1 and word(out) == 2 and bytes(f.u.mem_read(out + 4, 248)) == second)

    # Stop after a record load, execute the actual publisher on another stack,
    # then resume. Repeated sequence models wrap; serial must detect the tear.
    pending = [False]
    def observe(u, access, address, size, value, context): pending[0] = True
    def pause(u, address, size, context):
        if pending[0]:
            pending[0] = False
            u.emu_stop()
    hook = f.u.hook_add(UC_HOOK_MEM_READ, observe, begin=pub + 12, end=pub + 15)
    code_hook = f.u.hook_add(UC_HOOK_CODE, pause)
    f.u.ctl_remove_cache(CODE, CODE + len(image))
    guards = enter(f, CODE + symbols['z7_hl_read'], (), STACK)
    context = f.u.context_save()
    prior_sequence = word(pub)
    check('reader-pauses-mid-record-before-interleaved-writer', f.u.reg_read(UC_ARM_REG_PC) != STOP)
    f.u.hook_del(hook); f.u.hook_del(code_hook)
    f.u.ctl_remove_cache(CODE, CODE + len(image))
    third = struct.pack('<62I', *range(201, 263))
    f.u.mem_write(inp, third)
    writer_guards = enter(f, CODE + symbols['z7_hl_publish'], (), STACK - 0x10000)
    check('interleaved-publisher-preserves-independent-stack', returned(f, STACK - 0x10000, writer_guards) and
          f.u.reg_read(UC_ARM_REG_R0) == 1)
    write(pub, prior_sequence)
    f.u.context_restore(context)
    f.u.emu_start(f.u.reg_read(UC_ARM_REG_PC) | 1, STOP, timeout=10000000, count=10000000)
    check('serial-rejects-torn-record-even-when-sequence-repeats', returned(f, STACK, guards) and
          f.u.reg_read(UC_ARM_REG_R0) == 1 and word(out) == 3 and bytes(f.u.mem_read(out + 4, 248)) == third)
    write(pub + 4, 0xfffffffe)
    check('last-serial-publishes-and-remains-readable', call('publish') == 1 and call('read') == 1 and word(out) == 0xffffffff)
    record_before = bytes(f.u.mem_read(pub + 12, 248))
    f.u.mem_write(out, b'\xa5' * 252)
    check('serial-exhaustion-halts-without-recycling-or-partial-output', call('publish') == 0 and word(pub + 8) == 1 and
          call('read') == 0 and call('publish') == 0 and word(pub + 4) == 0xffffffff and
          bytes(f.u.mem_read(pub + 12, 248)) == record_before and bytes(f.u.mem_read(out, 252)) == b'\xa5' * 252)
    return dict(passed=True, checks=checks, compiled_thumb_publication_executed=True,
                explicit_interleaving_and_repeated_sequence_supplied=True,
                native_consumer_serialization_or_camera_timing_proven=False, camera_card_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); out = a.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists(): p.error('Choose a new private output directory')
    packet, metadata = build(ROOT / 'z7-native-modules/examples/highlight_lease_probe.c', zig=ZIG)
    result = audit(a.stock_main.read_bytes(), packet, metadata)
    result['probe_sha256'] = hashlib.sha256(packet).hexdigest()
    result['source_sha256'] = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
        'tools/audit_z7_highlight_lease.py', 'z7-native-modules/examples/highlight_lease_probe.c',
        'z7-native-modules/plugins/highlight_lease.h')}
    out.mkdir(parents=True)
    (out / 'probe.BIN').write_bytes(packet)
    (out / 'probe.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8', newline='\n')
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__': main()
