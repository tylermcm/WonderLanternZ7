"""Execute native highlight request-cache getters/writers and a torn-read schedule.

SPDX-License-Identifier: MIT. Original getter, bank arithmetic, writer and memcpy
execute. Incoming bank indices/requests/palette and task schedule are supplied.
No producer hook, writer closure, physical lifetime or installation is proven.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn import UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_CPSR
from audit_splash_image import BASE, MEM, STOCK_SHA, STOP
from audit_z7_highlight_converter import ConverterFixture, request
from audit_z7_highlight_submission import enter, returned
from build_z7_module_host import ROOT

GETTER, WRITER = 0x10434cee, 0x104348e4
INDEX, CACHE, STRIDE = 0xa180f274, 0xa1f18fc0, 0xe84
REQUEST_OFFSET, PEAKING_OFFSET = 0x58, 0x40
CALLER_STACK = 0xa251f000


class CacheFixture(ConverterFixture):
    def __init__(self, raw):
        super().__init__(raw)
        self.u.mem_map(0xa1f19000, 0x4000)
        self.u.mem_map(0xa2510000, 0x10000)
        self.writes = []
        self.watch = self.copied = 0
        self.pause_copy = False
        self.u.hook_add(UC_HOOK_MEM_WRITE, self.on_write)

    def on_write(self, u, access, address, size, value, context):
        if CACHE <= address < CACHE + 3 * STRIDE:
            self.writes.append((address, size))
        if self.watch <= address < self.watch + 36:
            self.copied += size

    def hook(self, u, address, size, context):
        if self.pause_copy and 0 < self.copied < 36:
            self.pause_copy = False
            u.emu_stop()
            return
        # Update-only writer must not acquire the submission mutex or submit a
        # display packet. These are boundaries, not replacements for the writer.
        if address in (0x103542d2, 0x101641fa, 0x1034ff1e, 0x10348494):
            raise AssertionError('Unexpected submission/lock in cache-only audit')
        super().hook(u, address, size, context)

    def indices(self, lcd, hdmi, evf):
        for output, bank in ((1, lcd), (2, hdmi), (4, evf)):
            self.u.mem_write(INDEX + output, bytes([bank]))

    def base(self, bank): return CACHE + bank * STRIDE
    def data(self, bank): return bytes(self.u.mem_read(self.base(bank) + REQUEST_OFFSET, 36))
    def put(self, output, data):
        self.u.mem_write(MEM + 0x1000, data)
        return self.call(WRITER, output, 0, MEM + 0x1000, 0)


def audit(raw):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA:
        raise ValueError('Exact original-Z7 C3.80 stock MAIN required')
    checks = []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)

    # Bind constants to the actual native bank arithmetic literal pool.
    check('native-bank-index-and-cache-base-literals',
          struct.unpack_from('<2I', raw, 0x10433f5c - BASE) == (INDEX, CACHE))
    f = CacheFixture(raw)
    for bank in range(3):
        f.u.mem_write(f.base(bank), b'\xa5' * STRIDE)
    f.indices(0, 1, 2)
    for output, bank in ((1,0), (2,1), (4,2)):
        pointer = f.base(bank) + REQUEST_OFFSET
        check(f'output{output}-getter-selects-native-bank-request36', f.call(GETTER, output, 0, 0) == pointer)
        for nonzero in (1,2,4,0xffffffff):
            check(f'output{output}-getter-rejects-nonzero-kind{nonzero}', f.call(GETTER, output, nonzero, 0) == 0)
        for pattern in (0,1,2):
            before = [bytes(f.u.mem_read(f.base(b), STRIDE)) for b in range(3)]
            data = request(output, pattern, 213)
            f.writes.clear(); f.put(output, data)
            expected = bytearray(before[bank]); expected[REQUEST_OFFSET:REQUEST_OFFSET+36] = data
            if pattern: struct.pack_into('<I', expected, PEAKING_OFFSET, 0)
            check(f'output{output}-pattern{pattern}-native-writer-copies-exact36-and-conditionally-clears-peaking',
                  bytes(f.u.mem_read(f.base(bank), STRIDE)) == bytes(expected) and f.data(bank) == data)
            check(f'output{output}-pattern{pattern}-other-banks-unchanged',
                  all(bytes(f.u.mem_read(f.base(b), STRIDE)) == before[b] for b in range(3) if b != bank))

    for mask in range(8):
        for pattern in (0,2):
            for bank in range(3): f.u.mem_write(f.base(bank), b'\x6b' * STRIDE)
            data = request(4,pattern,191); f.put(mask,data)
            expected = []
            for output,bank in ((1,0),(2,1),(4,2)):
                block=bytearray(b'\x6b'*STRIDE)
                if mask & output:
                    block[REQUEST_OFFSET:REQUEST_OFFSET+36]=data
                    if pattern: struct.pack_into('<I',block,PEAKING_OFFSET,0)
                expected.append(bytes(block))
            check(f'writer-mask{mask}-pattern{pattern}-updates-only-selected-output-banks',
                  all(bytes(f.u.mem_read(f.base(b),STRIDE))==expected[b] for b in range(3)))
    for kind in (1,2,0xffffffff):
        before=bytes(f.u.mem_read(CACHE,3*STRIDE))
        f.call(WRITER,7,kind,MEM+0x1000,0)
        check(f'writer-nonzero-kind{kind}-does-not-modify-cache',bytes(f.u.mem_read(CACHE,3*STRIDE))==before)
    check('getter-output-zero-is-not-a-validating-api',f.call(GETTER,0,0,0)==REQUEST_OFFSET)

    # Output-to-bank selection is mutable. Pointer caching across this change
    # would read the wrong native request even without a concurrent copy.
    first = f.call(GETTER, 4, 0, 0)
    f.indices(2, 1, 0)
    check('output-bank-change-is-reflected-by-original-getter', first != f.call(GETTER, 4, 0, 0) == f.base(0)+REQUEST_OFFSET)
    f.indices(1, 1, 1)
    check('outputs-may-alias-same-supplied-native-bank', len({f.call(GETTER, output, 0, 0) for output in (1,2,4)}) == 1)
    data = request(4, 2, 180); f.put(4, data)
    check('aliased-outputs-observe-native-write-to-common-bank', all(bytes(f.u.mem_read(f.call(GETTER, output, 0, 0),36)) == data for output in (1,2,4)))

    # A paused native memcpy makes two equal reader snapshots insufficient:
    # both can observe the same incomplete record while its writer is stopped.
    f.indices(0, 1, 2)
    old = request(4, 1, 248); new = request(4, 2, 180)
    f.put(4, old)
    f.u.mem_write(MEM + 0x1000, new)
    f.watch = f.base(2) + REQUEST_OFFSET
    f.copied = 0; f.pause_copy = True
    guards = enter(f, WRITER, (4,0,MEM+0x1000,0), CALLER_STACK)
    check('native-cache-writer-can-be-paused-between-request-stores', 0 < f.copied < 36 and not returned(f,CALLER_STACK,guards))
    context = f.u.context_save()
    pointer = f.call(GETTER,4,0,0)
    a = bytes(f.u.mem_read(pointer,36)); b = bytes(f.u.mem_read(pointer,36))
    check('two-equal-cache-reads-can-still-be-torn', a == b and a != old and a != new)
    torn_bytes = f.copied
    f.u.context_restore(context)
    # memcpy executes ARM code; resume in the saved instruction-set state.
    pc = f.u.reg_read(UC_ARM_REG_PC)
    thumb = (f.u.reg_read(UC_ARM_REG_CPSR) >> 5) & 1
    f.u.emu_start(pc | thumb, STOP, timeout=10000000, count=10000000)
    check('paused-native-cache-writer-resumes-with-original-stack-and-complete-request', returned(f,CALLER_STACK,guards) and f.data(2) == new)
    return dict(passed=True, checks=checks, stock_main_sha256=STOCK_SHA,
                original_getter_writer_and_memcpy_execute=True, request_bytes=36,
                cache_bank_stride=STRIDE, request_offset=REQUEST_OFFSET,
                native_copy_stores_before_reader_schedule=torn_bytes,
                equal_double_read_proves_coherence=False,
                native_writer_exclusion_or_producer_publication_required=True,
                incoming_bank_mapping_requests_palette_and_task_schedule_supplied=True,
                all_native_writers_indirect_callers_or_physical_lifetime_proven=False,
                automatic_no_native_update_handoff_implemented=False,camera_card_access=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists(): p.error('Choose a new private output file')
    result=audit(a.stock_main.read_bytes())
    names=('tools/audit_z7_highlight_native_cache.py','tools/audit_z7_highlight_converter.py',
           'tools/audit_z7_highlight_submission.py','tools/audit_splash_image.py','tools/audit_z7_display_parameters.py')
    result['source_sha256']={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),torn_after_bytes=result['native_copy_stores_before_reader_schedule'])))


if __name__=='__main__':main()
