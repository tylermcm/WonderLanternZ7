# SPDX-License-Identifier: GPL-2.0-or-later
"""Read-only module-file HLE at one original Z7 filesystem dispatch boundary.

This is an explicit diagnostic fixture, not an emulated SD/XQD controller.
All native wrappers, kernel scheduling, heap allocation and cache instructions
outside the intercepted dispatch remain guest code. Unrelated requests execute
their original dispatch instructions. No guest code bytes are modified.
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'z7-qemu/tools'))
from rsp import Remote

DISPATCH = 0x1027beae
FD = 0x6f000007


class ModuleFileFixture:
    def __init__(self, packet):
        self.packet = bytes(packet)
        if not 0 < len(self.packet) <= 1 << 20:
            raise ValueError('Module fixture file must be nonempty and at most 1 MiB')
        self.position = 0
        self.opened = self.closed = self.finished = False
        self.events = []

    def request(self, remote, pointer):
        data = remote.memory(pointer, 168)
        words = struct.unpack('<42I', data)
        operation = data[0x9c]
        if operation in (5, 16):
            path_pointer = words[4]
            if not (0x10020000 <= path_pointer < 0x12000000 or 0xa1800000 <= path_pointer < 0xc0000000):
                return None
            path = remote.memory(path_pointer, 32).split(b'\0', 1)[0]
            if path != b'A:\\Z7APP.BIN':
                return None
            if operation == 5:
                if self.opened or words[5:7] != (0, 0):
                    raise AssertionError('Unexpected module fixture open or write flags')
                self.opened = True
                self.events.append(dict(operation='open', read_only=True))
                return FD
            if not self.opened:
                raise AssertionError('Module stat before open')
            destination = words[0x54 // 4] + 0x218
            remote.write_memory(destination, struct.pack('<Q', len(self.packet)))
            self.events.append(dict(operation='stat', bytes=len(self.packet), after_close=self.closed))
            if self.closed:
                self.finished = True
            return 0
        if operation not in (6, 8) or words[7] != FD:
            return None
        if not self.opened or self.closed:
            raise AssertionError('Read/close without owned open module file')
        if operation == 6:
            self.closed = True
            self.events.append(dict(operation='close'))
            return 0
        buffer, capacity, actual = words[10:13]
        if buffer % 64 or not 1 <= capacity <= 513:
            raise AssertionError('Unexpected module staging alignment/capacity')
        count = min(capacity, len(self.packet) - self.position)
        if count:
            remote.write_memory(buffer, self.packet[self.position:self.position + count])
        remote.write_memory(actual, struct.pack('<I', count))
        self.position += count
        self.events.append(dict(operation='read', capacity=capacity, actual=count))
        return 0


class ModuleFileRemote(Remote):
    def __init__(self, port, fixture):
        self.fixture = fixture
        self.fixture_enabled = True
        self.dispatch_stops = 0
        self.breakpoint_refreshes = []
        super().__init__(port)

    def plain(self, command):
        self.send(command)
        return super().receive()

    def refresh_fixture_breakpoint(self):
        if self.fixture_enabled:
            removed = self.plain(f'z1,{DISPATCH:x},2')
            installed = self.plain(f'Z1,{DISPATCH:x},2')
            self.breakpoint_refreshes.append(dict(removed=removed, installed=installed))
            if installed != 'OK':
                raise RuntimeError('Cannot install filesystem observation after negotiation: ' + repr(self.breakpoint_refreshes[-1]))

    def write_memory(self, pointer, data):
        for offset in range(0, len(data), 1024):
            part = data[offset:offset + 1024]
            if self.plain(f'M{pointer + offset:x},{len(part):x}:' + part.hex()) != 'OK':
                raise RuntimeError('Diagnostic module memory write failed')

    def receive(self):
        while True:
            packet = super().receive()
            if not self.fixture_enabled or not packet.startswith('T') or 'thread:' not in packet:
                return packet
            thread = packet.split('thread:')[1].split(';')[0]
            if self.plain('Hg' + thread) != 'OK':
                raise RuntimeError('Cannot select stopped diagnostic CPU')
            registers = bytearray.fromhex(self.plain('g'))
            if len(registers) < 68:
                raise RuntimeError('Unexpected diagnostic ARM register packet')
            pc = struct.unpack_from('<I', registers, 60)[0]
            if pc != DISPATCH:
                return packet
            self.dispatch_stops += 1
            if self.dispatch_stops > 4096:
                raise RuntimeError('Filesystem diagnostic exceeded its stop budget')
            pointer = struct.unpack_from('<I', registers)[0]
            result = self.fixture.request(self, pointer)
            if result is None:
                # Execute the first original dispatch instruction on this CPU,
                # then restore the observation point for subsequent calls.
                if self.plain(f'z1,{DISPATCH:x},2') != 'OK' or self.plain('Hc' + thread) != 'OK':
                    raise RuntimeError('Cannot step unrelated filesystem dispatch')
                step = self.plain('s')
                if not step.startswith('T05') or self.plain('Hc-1') != 'OK':
                    raise RuntimeError('Unexpected unrelated-dispatch step result')
                if self.plain(f'Z1,{DISPATCH:x},2') != 'OK':
                    raise RuntimeError('Cannot restore filesystem observation point')
            else:
                lr = struct.unpack_from('<I', registers, 56)[0]
                cpsr_offset = 64 if len(registers) == 68 else 164
                cpsr = struct.unpack_from('<I', registers, cpsr_offset)[0]
                struct.pack_into('<I', registers, 0, result)
                struct.pack_into('<I', registers, 60, lr & ~1)
                struct.pack_into('<I', registers, cpsr_offset, (cpsr & ~0x20) | (0x20 if lr & 1 else 0))
                if self.plain('G' + registers.hex()) != 'OK':
                    raise RuntimeError('Cannot return diagnostic filesystem result')
                if self.fixture.finished:
                    if self.plain(f'z1,{DISPATCH:x},2') != 'OK':
                        raise RuntimeError('Cannot retire diagnostic filesystem breakpoint')
                    self.fixture_enabled = False
            self.send('c')
