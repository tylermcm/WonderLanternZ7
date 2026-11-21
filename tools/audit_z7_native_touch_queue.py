"""Execute original Z7 touch producer and synchronous ring copy (MIT).

The producer, ring index/count, zeroing, memcpy and metadata copies are stock
instructions. OS locks, wake, time, profile data and queue admission are supplied.
This is not native task scheduling, driver registration or consumer lifetime.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2
from audit_splash_image import NativePNG, STOCK_SHA, MEM, STACK

STATE, RING, STRIDE = 0xa1821314, 0xa200fe24, 0x154
LOCK, PACKET = 0xa200e76c, MEM + 0x10000


class TouchQueue(NativePNG):
    def __init__(self, raw):
        super().__init__(raw)
        self.native_call_timeout_us = 0
        self.u.mem_map(0xa2000000, 0x30000)
        self.u.mem_map(0xa1f90000, 0x10000)
        self.events = []
        self.depth = 0
        self.admission = 1

    def hook(self, u, address, size, context):
        arg = u.reg_read(UC_ARM_REG_R0)
        if address in (0x101641fa, 0x101641dc):
            assert arg == LOCK
            self.depth += 1 if address == 0x101641fa else -1
            assert self.depth in (0, 1)
            self.events.append(('lock' if address == 0x101641fa else 'unlock', arg))
            self.ret(0)
            return
        if address in (0x1040772e, 0x103e8ed6):
            self.events.append(('service', address))
            self.ret(0)
            return
        if address == 0x101f50cc:
            self.events.append(('clock', arg))
            u.mem_write(arg, bytes(8))
            self.ret(0)
            return
        if address == 0x101ea092:
            assert self.depth == 1
            self.events.append(('admission', arg))
            self.ret(self.admission)
            return
        if address == 0x10170a1c:
            # Observe, but execute the actual stock memory-copy implementation.
            self.events.append(('copy', arg, u.reg_read(UC_ARM_REG_R1),
                                u.reg_read(UC_ARM_REG_R2)))
        super().hook(u, address, size, context)


def audit(raw):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA:
        raise ValueError('Requires exact original Z7 C3.80 MAIN')
    f = TouchQueue(raw)
    checks = 0
    for index, kind, pressed in itertools.product(range(16), range(1, 9), (0, 1)):
        f.u.mem_write(STATE, bytes(0x34))
        f.u.mem_write(STATE, bytes([index, index]))
        if kind != 1 or not pressed:
            f.u.mem_write(STATE + 8, struct.pack('<I', 1))
        guard = b'\xa5' * 16
        f.u.mem_write(RING - 16, guard + bytes([0xcc]) * (16 * STRIDE) + guard)
        packet = bytearray((i * 17 + index) & 255 for i in range(60))
        packet[8:10] = bytes([pressed, kind])
        f.u.mem_write(PACKET, bytes(packet))
        f.events.clear()
        assert f.call(0x103319d8, PACKET) == 1
        assert f.depth == 0
        checks += 2
        expected = bytearray(packet)
        struct.pack_into('<I', expected, 0, 1)
        entry = RING + index * STRIDE
        assert bytes(f.u.mem_read(entry, STRIDE)) == bytes(expected) + bytes(STRIDE - 60)
        assert bytes(f.u.mem_read(PACKET, 60)) == bytes(packet)
        assert bytes(f.u.mem_read(STATE, 2)) == bytes([(index + 1) & 15, index])
        assert f.call(0x1033332e) == 1
        checks += 4
        copies = [e for e in f.events if e[0] == 'copy' and e[2] == PACKET]
        assert copies == [('copy', entry, PACKET, 60)]
        assert sum(e[0] == 'lock' for e in f.events) == 2
        assert sum(e[0] == 'unlock' for e in f.events) == 2
        checks += 3
        # Destroy caller data and its complete producer stack after return.
        f.u.mem_write(PACKET, bytes([0xee]) * 60)
        f.u.mem_write(STACK - 0x200, bytes([0xdd]) * 0x200)
        assert bytes(f.u.mem_read(entry, STRIDE)) == bytes(expected) + bytes(STRIDE - 60)
        assert bytes(f.u.mem_read(RING - 16, 16)) == guard
        assert bytes(f.u.mem_read(RING + 16 * STRIDE, 16)) == guard
        for other in range(16):
            if other != index:
                assert bytes(f.u.mem_read(RING + other * STRIDE, STRIDE)) == bytes([0xcc]) * STRIDE
        checks += 4
    for index in range(16):
        f.admission = 0
        f.u.mem_write(STATE, bytes(0x34))
        f.u.mem_write(STATE, bytes([index, index]))
        f.u.mem_write(STATE + 8, struct.pack('<I', 1))
        f.u.mem_write(RING, bytes([0xcc]) * (16 * STRIDE))
        packet = bytearray(range(60))
        packet[8:10] = b'\x01\x02'
        f.u.mem_write(PACKET, bytes(packet))
        f.events.clear()
        # Native failure synthesizes cancellation entries and still returns1.
        assert f.call(0x103319d8, PACKET) == 1
        assert f.depth == 0
        assert bytes(f.u.mem_read(PACKET, 60)) == bytes(packet)
        assert bytes(f.u.mem_read(STATE, 2)) == bytes([index, index])
        assert f.call(0x1033332e) == 0
        checks += 5
        cancellation = bytearray(STRIDE)
        struct.pack_into('<I', cancellation, 0, 1)
        cancellation[9] = 9
        f.u.mem_write(PACKET, bytes([0xee]) * 60)
        f.u.mem_write(STACK - 0x200, bytes([0xdd]) * 0x200)
        for other in range(16):
            expected = cancellation if other in (index, (index - 1) & 15) else bytes([0xcc]) * STRIDE
            assert bytes(f.u.mem_read(RING + other * STRIDE, STRIDE)) == bytes(expected)
        assert len([e for e in f.events if e[0] == 'admission']) == 1
        checks += 2
    f.admission = 1
    for blocked in (False, True):
        f.u.mem_write(STATE, bytes(0x34))
        if blocked:
            f.u.mem_write(STATE + 0xc, struct.pack('<I', 1))
        original_ring = bytes([0xcc]) * (16 * STRIDE)
        f.u.mem_write(RING, original_ring)
        packet = bytearray(range(60))
        packet[8:10] = bytes([1, 1 if blocked else 2])
        f.u.mem_write(PACKET, bytes(packet))
        f.events.clear()
        assert f.call(0x103319d8, PACKET) == 0
        assert f.depth == 0
        assert bytes(f.u.mem_read(RING, 16 * STRIDE)) == original_ring
        assert bytes(f.u.mem_read(PACKET, 60)) == bytes(packet)
        assert not any(e[0] in ('copy', 'admission') for e in f.events)
        checks += 5
    return {
        'schema': 1, 'passed': True, 'checks': checks,
        'stock_main_sha256': STOCK_SHA, 'empty_ring_indices': 16,
        'admitted_packet_cases': 256,
        'failed_queue_admission_cases': 16, 'native_filter_rejections': 2,
        'scope': 'Original touch producer 103319D8 and native memcpy; kinds1..8 with press/release in each empty ring index and supplied active state; exact 60-byte copy, entry clearing, ready marker, wrap/count, caller/stack independence and ABI preservation',
        'supplied_boundaries': ['OS locks', 'wake services', 'time',
                                'auxiliary profile data', 'queue admission result'],
        'failed_admission_returns1_and_copies_two_cancellation_entries': True,
        'limits': ['No full/nonempty ring or kinds outside1..8 coverage',
                   'No native consumer, concurrency or task lifetime proof',
                   'No driver registration, physical touch, boot, flash or recovery proof'],
        'installation_candidate': False,
        'source_sha256': {
            str(p.relative_to(Path(__file__).resolve().parent.parent)).replace('\\', '/'):
                hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__).resolve(),
                      Path(__file__).resolve().with_name('audit_splash_image.py'))
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--main', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Output must not already exist')
    result = audit(args.main.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
