# SPDX-License-Identifier: GPL-2.0-or-later
"""Explicit module + two writable journal-file HLE for assisted QEMU only.

No SD/XQD controller or native filesystem implementation is modeled. Only the
owned names/handles below receive supplied results. Other requests pass through.
Synthetic record bytes remain host-memory data until the probe saves them privately.
"""
import struct
from module_file_fixture import ModuleFileFixture, FD

PATHS = (b'A:\\Z7CFG0.DAT', b'A:\\Z7CFG1.DAT')
FIRST_FD = 0x6f100000
NOT_FOUND = 0x80000010


class SettingsFileFixture:
    def __init__(self, packet, files=None):
        self.module = ModuleFileFixture(packet)
        self.events = self.module.events
        self.files = {slot: bytes(data) for slot, data in (files or {}).items()}
        if any(slot not in (0, 1) or len(data) > 4096 for slot, data in self.files.items()):
            raise ValueError('Only two bounded diagnostic journal slots are allowed')
        self.handles, self.issued = {}, set()
        self.next_fd = FIRST_FD
        self.finished = False

    @property
    def packet(self): return self.module.packet
    @property
    def position(self): return self.module.position
    @property
    def opened(self): return self.module.opened
    @property
    def closed(self): return self.module.closed
    @property
    def module_finished(self): return self.module.finished

    @staticmethod
    def ram(pointer, length):
        return 0xa1800000 <= pointer and length <= 0xc0000000 - pointer

    def request(self, remote, pointer):
        data = remote.memory(pointer, 168)
        words = struct.unpack('<42I', data)
        operation = data[0x9c]
        slot = None
        if operation in (5, 13, 16):
            p = words[4]
            if not (0x10020000 <= p < 0x12000000 or self.ram(p, 32)):
                return None
            path = remote.memory(p, 32).split(b'\0', 1)[0]
            if path in PATHS:
                slot = PATHS.index(path)
            else:
                return self.module.request(remote, pointer)
        if slot is not None:
            if self.finished or not self.module_finished:
                raise AssertionError('Settings access outside the persistent service lifetime')
            if operation == 16:
                raise AssertionError('Settings adapter must not borrow module stat storage')
            if operation == 5 and words[5:7] != (0, 0):
                raise AssertionError('Settings reads require read-only open')
            if operation == 13 and words[6] != 0:
                raise AssertionError('Unexpected native settings create mode')
            event = dict(component='settings', operation='open' if operation == 5 else 'create', slot=slot)
            self.events.append(event)
            if operation == 5 and slot not in self.files:
                event['missing'] = True
                return NOT_FOUND
            if len(self.issued) >= 256:
                raise RuntimeError('Settings file fixture exceeded its handle budget')
            fd = self.next_fd
            self.next_fd += 1
            self.issued.add(fd)
            self.handles[fd] = dict(slot=slot, position=0, writable=operation == 13)
            if operation == 13:
                self.files[slot] = b''
            event['fd'] = hex(fd)
            return fd
        fd = words[7]
        if fd not in self.issued:
            if operation == 9 and fd == FD:
                raise AssertionError('The module diagnostic file is immutable')
            return self.module.request(remote, pointer)
        if self.finished or fd not in self.handles:
            raise AssertionError('Stale/closed diagnostic journal handle')
        handle = self.handles[fd]
        slot = handle['slot']
        if operation == 6:
            del self.handles[fd]
            self.events.append(dict(component='settings', operation='close', slot=slot, fd=hex(fd)))
            return 0
        if operation not in (8, 9) or handle['writable'] != (operation == 9):
            raise AssertionError('Unexpected journal operation or handle permission')
        buffer, capacity, actual = words[10:13]
        if buffer % 64 or not self.ram(buffer, capacity) or actual % 4 or not self.ram(actual, 4) or capacity != (81 if operation == 8 else 80):
            raise AssertionError('Unexpected journal buffer, length or count pointer')
        if operation == 8:
            chunk = self.files[slot][handle['position']:handle['position'] + capacity]
            count = len(chunk)
            if count:
                remote.write_memory(buffer, chunk)
        else:
            if handle['position']:
                raise AssertionError('Expected one bounded journal write')
            count = capacity
            self.files[slot] = remote.memory(buffer, capacity)
        handle['position'] += count
        remote.write_memory(actual, struct.pack('<I', count))
        self.events.append(dict(component='settings', operation='read' if operation == 8 else 'write', slot=slot, bytes=count, fd=hex(fd)))
        return 0

    def retire(self):
        if not self.module_finished or self.handles:
            raise RuntimeError('Cannot retire settings service before files are closed')
        self.finished = True
