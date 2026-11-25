# SPDX-License-Identifier: GPL-2.0-or-later
"""Explicit module + read-only shutter WAV file HLE for assisted QEMU only.

No SD/XQD controller or native filesystem implementation is modeled. Only the
module file and A:\\SHUTTER1.WAV receive supplied results; other requests pass
through to the original dispatch. Nothing is ever written or created.
"""
import struct
from module_file_fixture import ModuleFileFixture, FD

WAV_PATH = b'A:\\SHUTTER1.WAV'
WAV_FD = 0x6f200000
WAV_CAPACITY = 48000 * 4 + 4096 + 1
NOT_FOUND = 0x80000010


class SoundFileFixture:
    def __init__(self, packet, wav=None):
        self.module = ModuleFileFixture(packet)
        self.events = self.module.events
        self.wav = None if wav is None else bytes(wav)
        self.wav_open = self.wav_closed = False
        self.wav_position = 0
        self.finished = False  # Keep the observation point for the module's WAV read.

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
            if path != WAV_PATH:
                return self.module.request(remote, pointer)
            if operation != 5 or words[5:7] != (0, 0):
                raise AssertionError('Shutter WAV must only be opened read-only')
            if not self.module_finished or self.wav_open:
                raise AssertionError('WAV open outside module init or repeated')
            event = dict(component='sound', operation='open')
            self.events.append(event)
            if self.wav is None:
                event['missing'] = True
                return NOT_FOUND
            self.wav_open = True
            return WAV_FD
        if words[7] != WAV_FD:
            if operation == 9 and words[7] == FD:
                raise AssertionError('The module diagnostic file is immutable')
            return self.module.request(remote, pointer)
        if not self.wav_open or self.wav_closed:
            raise AssertionError('Stale shutter WAV handle')
        if operation == 6:
            self.wav_closed = True
            self.events.append(dict(component='sound', operation='close'))
            return 0
        if operation != 8:
            raise AssertionError('Unexpected shutter WAV operation')
        buffer, capacity, actual = words[10:13]
        if buffer % 64 or capacity != WAV_CAPACITY:
            raise AssertionError('Unexpected shutter WAV buffer or capacity')
        chunk = self.wav[self.wav_position:self.wav_position + capacity]
        if chunk:
            remote.write_memory(buffer, chunk)
        self.wav_position += len(chunk)
        remote.write_memory(actual, struct.pack('<I', len(chunk)))
        self.events.append(dict(component='sound', operation='read', capacity=capacity, actual=len(chunk)))
        return 0
