"""Execute compiled ARM module host with original Z7 filesystem/task wrappers.

SPDX-License-Identifier: MIT. Kernel task creation/start, allocator and the
filesystem request dispatcher are modeled boundaries. Native wrappers, CRC,
relocations, cache-maintenance instructions and module initialization execute.
No real card, camera, flash writer or complete firmware boot is exercised.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_PC, UC_ARM_REG_CPSR
from audit_splash_image import NativePNG, MEM, STOCK_SHA
from build_z7_module import pack_module, seal
from build_z7_module_host import ROOT, STATE, STATE_BYTES, MAGIC, CURSOR, HEAP_SITE, PRESET, DISPLAY_PRESET


class HostFixture(NativePNG):
    def __init__(self, raw, report, packet, case='success'):
        super().__init__(raw, fail_allocation={'alloc-raw': 1, 'alloc-body': 2}.get(case, 0))
        # CRC over larger linked modules plus Python instruction hooks can
        # exceed10s. Keep the10M instruction limit and original ABI guards;
        # extend only this host fixture's wall budget. Direct PNG audits retain
        # their existing10s budget.
        self.native_call_timeout_us = 30000000
        self.report, self.packet, self.case = report, packet, case
        self.u.mem_map(STATE - 4096, 12288)
        self.u.mem_map(0xa2900000, 0x100000)
        # Explicit cached-memory table fixture, not a claim about runtime MMU.
        self.u.mem_write(0xa29dbf18, struct.pack('<4I', 0, 0, 0, 0xffffffff))
        self.u.mem_write(STATE, bytes(report.get('state_bytes', STATE_BYTES)))
        self.setword(32, MAGIC)
        self.setword(72, 0xffffffff)
        for off in range(240, 256, 4):
            self.setword(off, 0xa5a5a5a5)
        if report.get('state_bytes', 0) >= 272:
            for off in (264, 268):
                self.setword(off, 0xa5a5a5a5)
        if report.get('state_bytes', 0) >= 288:
            for off in (280, 284):
                self.setword(off, 0xa5a5a5a5)
        if report.get('state_bytes', 0) >= 304:
            for off in (296, 300):
                self.setword(off, 0xa5a5a5a5)
        if report.get('state_bytes', 0) >= 324:
            for off in (316, 320):
                self.setword(off, 0xa5a5a5a5)
        if report.get('state_bytes', 0) >= 336:
            for off in (328, 332):
                self.setword(off, 0xa5a5a5a5)
        if report.get('native_cache_copy_hooks'):
            for off in (352, 356):
                self.setword(off, 0xa5a5a5a5)
        if report.get('graphics_queue_hooks'):
            for off in (376,380):
                self.setword(off,0xa5a5a5a5)
        if report.get('navigation_hooks'):
            for off in (396,400):
                self.setword(off,0xa5a5a5a5)
        if report.get('touch_hooks'):
            for off in (416,420):
                self.setword(off,0xa5a5a5a5)
        self.position = 0
        self.events, self.cache = [], []
        self.open_count = self.close_count = self.read_count = self.create_count = self.start_count = 0
        self.original_calls = 0
        self.result_seen = False
        self.heap_flags = 0xf8000000
        self.heap_observation = None
        self.cache_pcs = {}
        decoder = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        decoder.skipdata = True
        address = int(report['host_address'], 16)
        for insn in decoder.disasm(raw[address - 0x10020000:address - 0x10020000 + report['host_bytes']], address):
            if insn.mnemonic in ('mcr', 'dsb', 'isb'):
                self.cache_pcs[insn.address] = insn.op_str if insn.mnemonic == 'mcr' else insn.mnemonic

    def setword(self, offset, value):
        self.u.mem_write(STATE + offset, struct.pack('<I', value))

    def words(self):
        return struct.unpack('<64I', self.u.mem_read(STATE, STATE_BYTES))

    def cstring(self, p):
        return bytes(self.u.mem_read(p, 64)).split(b'\0', 1)[0].decode('ascii')

    def hook(self, u, address, size, unused):
        if address == 0x1027beae:
            message = u.reg_read(UC_ARM_REG_R0)
            words = struct.unpack('<42I', u.mem_read(message, 168))
            op = bytes(u.mem_read(message + 0x9c, 1))[0]
            result = 0
            if op == 5:
                self.open_count += 1
                self.events.append(('open', self.cstring(words[4]), words[5], words[6]))
                if self.case == 'missing' or (self.case == 'delayed-card' and self.open_count < 3):
                    result = 0x80000010
                else:
                    result = 7
            elif op == 16:
                pointer = words[0x54 // 4]
                length = len(self.packet)
                if self.case == 'bad-size':
                    length = (1 << 20) + 1
                if self.case == 'size-high':
                    length |= 1 << 32
                if self.case == 'grown-file':
                    length -= 1
                u.mem_write(pointer + 0x218, struct.pack('<Q', length))
                self.events.append(('stat', length))
            elif op == 8:
                self.read_count += 1
                fd, pointer, capacity, actual = words[7], words[10], words[11], words[12]
                if fd != 7 or not 1 <= capacity <= 513 or pointer % 64:
                    raise AssertionError('Wrong native read signature or staging alignment')
                count = min(capacity, len(self.packet) - self.position)
                if self.case == 'short-read':
                    count = max(0, count - 1)
                if count:
                    u.mem_write(pointer, self.packet[self.position:self.position + count])
                u.mem_write(actual, struct.pack('<I', count))
                self.events.append(('read', capacity, count, pointer))
                self.position += count
                if self.case == 'read-error':
                    result = 0x80000041
            elif op == 6:
                self.close_count += 1
                self.events.append(('close', words[7]))
                if self.case == 'close-error':
                    result = 0x80000041
            else:
                raise AssertionError(f'Unexpected filesystem operation {op}')
            self.ret(result)
        elif address == 0x10035fdc:
            p = u.reg_read(UC_ARM_REG_R0)
            values = struct.unpack('<14I', u.mem_read(p, 56))
            self.create_count += 1
            self.events.append(('create', values, bytes(u.mem_read(p + 48, 8)).hex()))
            self.ret(0xfffffffb if self.case == 'task-create-error' else 0x01000102)
        elif address == 0x10035e6c:
            self.events.append(('task-flags', u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)))
            self.ret(0)
        elif address == 0x10036440:
            self.start_count += 1
            self.events.append(('start', u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)))
            self.ret(0xfffffffb if self.case == 'task-start-error' else 0)
        elif address == 0x102697f4:
            # Separate supplied AUTOOP boundary; full native boot is not claimed.
            self.original_calls += 1
            self.ret(0x12343800)
        elif address == 0x1017089c:
            self.events.append(('workspace-mutex', u.reg_read(UC_ARM_REG_R0)))
            self.ret(1)
        elif address == 0x101e3bb8:
            self.heap_observation = dict(r0=u.reg_read(UC_ARM_REG_R0), r1=u.reg_read(UC_ARM_REG_R1),
                r2=u.reg_read(UC_ARM_REG_R2), r3=u.reg_read(UC_ARM_REG_R3), flags=u.reg_read(UC_ARM_REG_CPSR) & 0xf8000000)
            self.events.append(('workspace-continuation', u.reg_read(UC_ARM_REG_R0)))
            self.ret(u.reg_read(UC_ARM_REG_R0))
        elif address == HEAP_SITE:
            u.reg_write(UC_ARM_REG_CPSR, (u.reg_read(UC_ARM_REG_CPSR) & ~0xf8000000) | self.heap_flags)
            u.reg_write(UC_ARM_REG_R2, 0x22334455)
            u.reg_write(UC_ARM_REG_R3, 0x66778899)
        elif address == 0x1017081e:
            delay = u.reg_read(UC_ARM_REG_R0)
            self.events.append(('delay', delay))
            if delay == 1000 and self.result_seen:
                # Stop at the worker's first deliberate resident park boundary.
                u.emu_stop()
            else:
                self.ret(0)
        else:
            if address == (self.report['symbols']['z7_module_result'] & ~1):
                self.result_seen = True
            if address == 0x101e9f9a:
                self.cache.append(('native-invalidate-line', u.reg_read(UC_ARM_REG_R2)))
            if address in self.cache_pcs:
                self.cache.append(('publish', address, self.cache_pcs[address]))
            super().hook(u, address, size, unused)


def audit(raw, report, stock, packet):
    if hashlib.sha256(stock).hexdigest() != STOCK_SHA:
        raise ValueError('Requires exact original Z7 C 3.80 MAIN')
    if report['preset'] not in (PRESET, DISPLAY_PRESET) or hashlib.sha256(raw).hexdigest() != report['main_payload_sha256']:
        raise ValueError('Candidate fingerprint or identity mismatch')
    checks, scenarios = [], []
    def check(name, condition):
        checks.append(dict(name=name, passed=bool(condition)))
        if not condition:
            raise AssertionError(name)
    def fixture(case='success', data=packet):
        return HostFixture(raw, report, data, case)
    def run(case, expected, data=packet):
        f = fixture(case, data)
        result = f.call(report['symbols']['z7_module_load_once'], STATE)
        check(case + '-result', result == expected)
        check(case + '-file-path-read-only', all(e[1:] == ('A:\\Z7APP.BIN', 0, 0)
              for e in f.events if e[0] == 'open'))
        check(case + '-guard-preserved', f.words()[60:] == (0xa5a5a5a5,) * 4)
        if expected != 8:
            check(case + '-no-retained-image', not f.words()[12] and not f.words()[13] and not f.live)
        else:
            check(case + '-single-retained-allocation', len(f.live) == 1 and f.words()[13] in f.live)
            check(case + '-compiled-c-module-initialized',
                  bytes(f.u.mem_read(f.words()[12] + 128, 4)) == struct.pack('<I', 0x5a703801))
            published = [e[2].replace(' ', '') for e in f.cache if e[0] == 'publish']
            check(case + '-cache-publish-executed',
                  sum('c7,c11' in op for op in published) == (f.words()[14] + 63) // 64 and
                  len(published) >= 4 and published[-4] == 'dsb' and
                  'c7,c5' in published[-3] and published[-2:] == ['dsb', 'isb'])
            before = list(f.events)
            check(case + '-reload-rejected', f.call(report['symbols']['z7_module_load_once'], STATE) == 10 and f.events == before)
        scenarios.append(dict(case=case, status=result, reads=f.read_count, opens=f.open_count,
            closes=f.close_count, allocations=f.allocations, frees=f.frees,
            events=f.events, cache=f.cache, state=list(f.words())))
        return f

    good = run('success', 8)
    check('success-closes-before-module-call', good.close_count == 1)
    # Largest native read request: full 512-byte last block + EOF byte. This
    # executes the native invalidator's extra cache-line iteration.
    large_image = bytearray(896)
    large_image[:128] = packet[64:192]
    struct.pack_into('<I', large_image, 68, 896)
    large = pack_module(large_image, 4, 0, (68, 72, *range(128, 184, 4)))
    f = fixture(data=large)
    check('513-byte-final-read-and-native-cache-padding', f.call(report['symbols']['z7_module_load_once'], STATE) == 8
          and [e[1] for e in f.events if e[0] == 'read'] == [512, 513])
    check('large-probe-bss-initialized', bytes(f.u.mem_read(f.words()[12] + 896, 4)) == struct.pack('<I', 0x5a703801))
    buffers = {e[3] for e in f.events if e[0] == 'read'}
    invalidated = [e[1] for e in f.cache if e[0] == 'native-invalidate-line']
    check('native-invalidation-stays-inside-owned-640-byte-stack-array', len(buffers) == 1 and
          all(next(iter(buffers)) <= p < next(iter(buffers)) + 640 for p in invalidated) and
          next(iter(buffers)) + 576 in invalidated)
    # Additional chunked image preserves probe literals while moving BSS.
    bigger = bytearray(768)
    bigger[:128] = packet[64:192]
    struct.pack_into('<I', bigger, 68, 768)
    split = pack_module(bigger, 4, 0, (68, 72))
    f = fixture(data=split)
    check('multiple-chunks-plus-final-tail', f.call(report['symbols']['z7_module_load_once'], STATE) == 8
          and [e[1] for e in f.events if e[0] == 'read'] == [512, len(split) - 512 + 1])

    for case, expected in (('missing', 1), ('bad-size', 2), ('size-high', 2),
                           ('alloc-raw', 3), ('alloc-body', 3), ('short-read', 4),
                           ('read-error', 4), ('close-error', 5), ('grown-file', 4)):
        f = run(case, expected)
        check(case + '-close-count', f.close_count == (0 if case == 'missing' else 1))
        if case == 'close-error':
            before = list(f.events)
            check('failed-close-is-not-retried', f.call(report['symbols']['z7_module_load_once'], STATE) == 5 and f.events == before)
    corrupt = bytearray(packet)
    corrupt[64] ^= 1
    run('bad-crc', 6, bytes(corrupt))
    foreign = bytearray(packet)
    struct.pack_into('<I', foreign, 8, 0x01700072)
    run('wrong-model', 6, seal(foreign))
    failing = pack_module(b'\x01\x20\x70\x47' + bytes(60), 0, 0)
    run('init-error', 7, failing)

    f = fixture()
    f.setword(240, 0)
    check('invalid-state-no-filesystem-or-allocation', f.call(report['symbols']['z7_module_load_once'], STATE) == 11 and not f.events and not f.allocations)
    for case in ('success', 'task-create-error', 'task-start-error'):
        f = fixture(case)
        check(case + '-original-autoop-result-preserved', f.call(report['symbols']['z7_autoop_init']) == 0x12343800)
        check(case + '-single-task-created', f.create_count == 1)
        created = next(e for e in f.events if e[0] == 'create')
        values = created[1]
        check(case + '-native-task-descriptor', values[0] == STATE and values[2] == 0x10170741 and
              values[3] == 28 and values[4] == 8192 and values[11] == 1 and
              created[2] == b'Z7MOD\0\0\0'.hex())
        check(case + '-native-task-start-contract', f.start_count == (0 if case == 'task-create-error' else 1))
        check(case + '-full-width-kernel-task-id', f.words()[0] == (0xfffffffb if case == 'task-create-error' else 0x01000102) and
              (case == 'task-create-error' or ('start', 0x01000102, STATE) in f.events))
        check(case + '-boot-status', f.words()[9] == (2 if case == 'success' else 1) and
              f.words()[10] == (0 if case == 'success' else 9))
        f.call(report['symbols']['z7_autoop_init'])
        check(case + '-boot-scheduling-once-original-forwarded-every-time', f.create_count == 1 and f.original_calls == 2)
    f = fixture()
    check('patched-workspace-original-unwind', f.call(0x101e3d94) == STATE)
    check('workspace-reservation-and-state-guards', int.from_bytes(f.u.mem_read(CURSOR, 4), 'little') == STATE + STATE_BYTES and
          f.words()[8] == MAGIC and f.words()[60:] == (0xa5a5a5a5,) * 4 and not any(f.words()[:8]))
    check('workspace-hook-preserves-native-continuation-registers-and-flags', f.heap_observation ==
          dict(r0=STATE, r1=CURSOR, r2=0x22334455, r3=0x66778899, flags=0xf8000000))

    # Worker task runs to its resident park, without pretending to return.
    from unicorn.arm_const import UC_ARM_REG_SP, UC_ARM_REG_LR
    for case, expected_attempts, expected_status in (('missing', 100, 1), ('delayed-card', 3, 8)):
        f = fixture(case)
        f.u.reg_write(UC_ARM_REG_R0, STATE)
        f.u.reg_write(UC_ARM_REG_SP, 0x503f0000)
        f.u.reg_write(UC_ARM_REG_LR, 0x503ff001)
        f.u.emu_start(report['symbols']['z7_module_worker'], 0, timeout=10000000, count=10000000)
        check(case + '-worker-bounded-and-parked', f.result_seen and f.words()[17] == expected_attempts and
              f.words()[10] == expected_status and f.events[-1] == ('delay', 1000))
        check(case + '-retry-delay-count', sum(e == ('delay', 100) for e in f.events) == expected_attempts - 1)

    return dict(checks=checks, scenarios=scenarios, passed=all(c['passed'] for c in checks),
        scope='Compiled Thumb host and C module with original Z7 wrappers; kernel/filesystem/heap boundaries modeled',
        limitations=['No complete firmware boot, real card or physical cache-coherence validation',
                     'No physical camera, firmware installation or recovery verification'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--module', type=Path, required=True)
    parser.add_argument('--stock', type=Path, default=ROOT / '.private/builds/20261021-laptop-01/stock-main.bin')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists():
        parser.error('Choose a new private evidence path')
    raw = (args.build / 'module-host.emulator.main.bin').read_bytes()
    report = json.loads((args.build / 'module-host.emulator.json').read_text(encoding='utf-8'))
    result = audit(raw, report, args.stock.read_bytes(), args.module.read_bytes())
    result.update(main_sha256=hashlib.sha256(raw).hexdigest(), module_sha256=hashlib.sha256(args.module.read_bytes()).hexdigest())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(passed=result['passed'], checks=len(result['checks']), output=str(output))))


if __name__ == '__main__':
    main()
