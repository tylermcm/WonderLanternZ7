# SPDX-License-Identifier: GPL-2.0-or-later
"""Explicit module + write-only trigger-log file HLE for assisted QEMU only.

No SD/XQD controller or native filesystem implementation is modeled. Only the
module file and A:\\Z7TRIG.DAT receive supplied results; other requests pass
through to the original dispatch. The log's bytes are captured in memory.
"""
import struct
from module_file_fixture import ModuleFileFixture, FD

LOG_PATH = b'A:\\Z7TRIG.DAT'
LOG_FD = 0x6f300000


class TriggerFileFixture:
    def __init__(self, packet, size):
        self.module = ModuleFileFixture(packet)
        self.events = self.module.events
        self.size = size
        self.files = []          # every completed log write, oldest first
        self.handle = None
        self.finished = False    # keep observing for the worker's log writes

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

    def request(self, remote, pointer):
        data = remote.memory(pointer, 168)
        words = struct.unpack('<42I', data)
        operation = data[0x9c]
        if operation in (5, 13, 16):
            p = words[4]
            if not (0x10020000 <= p < 0x12000000 or 0xa1800000 <= p < 0xc0000000):
                return None
            path = remote.memory(p, 32).split(b'\0', 1)[0]
            if path != LOG_PATH:
                return self.module.request(remote, pointer)
            if operation != 13 or words[6] != 0 or self.handle is not None:
                raise AssertionError('Trigger log must only be created, one handle at a time')
            self.handle = bytearray()
            self.events.append(dict(component='trigger', operation='create'))
            return LOG_FD
        if words[7] != LOG_FD:
            if operation == 9 and words[7] == FD:
                raise AssertionError('The module diagnostic file is immutable')
            return self.module.request(remote, pointer)
        if self.handle is None:
            raise AssertionError('Stale trigger log handle')
        if operation == 6:
            self.files.append(bytes(self.handle))
            self.handle = None
            self.events.append(dict(component='trigger', operation='close'))
            return 0
        if operation != 9:
            raise AssertionError('Unexpected trigger log operation')
        buffer, capacity, actual = words[10:13]
        if buffer % 64 or capacity != self.size:
            raise AssertionError('Unexpected trigger log buffer or size')
        self.handle += remote.memory(buffer, capacity)
        remote.write_memory(actual, struct.pack('<I', capacity))
        self.events.append(dict(component='trigger', operation='write', bytes=capacity))
        return 0


class FieldFileFixture:
    """Module file + read-only SHUTTER1.WAV + write-only trigger log, for the
    combined field-test module. One shared module-file fixture."""
    def __init__(self, packet, wav, size):
        from sound_file_fixture import SoundFileFixture
        self.sound = SoundFileFixture(packet, wav)
        self.trigger = TriggerFileFixture(packet, size)
        self.trigger.module = self.sound.module
        self.module = self.sound.module
        self.events = self.module.events
        self.trigger.events = self.events
        self.finished = False

    files = property(lambda self: self.trigger.files)
    handle = property(lambda self: self.trigger.handle)
    packet = property(lambda self: self.module.packet)
    position = property(lambda self: self.module.position)
    opened = property(lambda self: self.module.opened)
    closed = property(lambda self: self.module.closed)
    module_finished = property(lambda self: self.module.finished)

    def request(self, remote, pointer):
        data = remote.memory(pointer, 168)
        words = struct.unpack('<42I', data)
        operation = data[0x9c]
        if operation in (5, 13, 16):
            p = words[4]
            if 0x10020000 <= p < 0x12000000 or 0xa1800000 <= p < 0xc0000000:
                if remote.memory(p, 32).split(b'\0', 1)[0] == LOG_PATH:
                    return self.trigger.request(remote, pointer)
        elif words[7] == LOG_FD:
            return self.trigger.request(remote, pointer)
        return self.sound.request(remote, pointer)
