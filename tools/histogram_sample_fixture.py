"""Explicit supplied-bin boundary for private original-Z7 rendering tests.

SPDX-License-Identifier: MIT. Only an exact owned module buffer/caller may get
supplied bins at104070AC. Other native callers run the original getter. This
does not emulate an ISP/statistics producer or complete any native event.
"""
import hashlib
import math
import struct

GETTER = 0x104070ac
DIAGNOSTIC_BINS = tuple(32 * (1 + i % 32) for i in range(256))


def histogram_scanout_box(rectangle, size):
    """Native720x480 RGBA bitmap rows run bottom-up; scanout is top-down.

    This is the bitmap convention already established by the native surface
    audit in GRID_SPIRAL_RESEARCH.md. CPU fill103FA1A0 uses exclusive endpoints.
    """
    x1, y1, x2, y2 = rectangle
    width, height = size
    if not (0 <= x1 < x2 <= 720 and 0 <= y1 < y2 <= 480 and width > 0 and height > 0):
        raise ValueError('Expected bounded native LCD rectangle and positive scanout size')
    return (math.floor(x1 * width / 720), math.floor((480 - y2) * height / 480),
            math.ceil(x2 * width / 720), math.ceil((480 - y1) * height / 480))


class HistogramSampleFixture:
    def __init__(self, base, image_bytes, memory_bytes, sample_offset, samples=DIAGNOSTIC_BINS):
        samples = tuple(samples)
        if (base % 64 or not 0xa1800000 <= base < 0xc0000000 or
            not 0 < image_bytes <= memory_bytes <= 0x400000 or base + memory_bytes > 0xc0000000 or
            sample_offset % 64 or not image_bytes <= sample_offset <= memory_bytes - 1024 or
            len(samples) != 256 or any(type(v) is not int or not 0 <= v <= 0xffffffff for v in samples)):
            raise ValueError('Expected one bounded owned histogram buffer and256 unsigned bins')
        self.base, self.image_bytes = base, image_bytes
        self.destination = base + sample_offset
        self.packet = struct.pack('<256I', *samples)
        self.sha256 = hashlib.sha256(self.packet).hexdigest()
        self.events = []

    def request(self, remote, registers):
        destination = struct.unpack_from('<I', registers, 0)[0]
        lr = struct.unpack_from('<I', registers, 56)[0]
        if not lr & 1 or not self.base <= (lr & ~1) < self.base + self.image_bytes:
            self.events.append(dict(operation='native-caller-pass-through', caller=hex(lr)))
            return None
        if destination != self.destination:
            raise AssertionError('Module getter did not use its exact owned sample buffer')
        if remote.memory(destination, 1024) != bytes(1024):
            raise AssertionError('Module did not clear its sample buffer')
        remote.write_memory(destination, self.packet)
        self.events.append(dict(operation='supplied-bins', caller=hex(lr), destination=hex(destination),
            bytes=1024, sample_sha256=self.sha256, native_event_completed=False, register_packet_bytes=len(registers)))
        return 1


def sample_remote(base_remote):
    """Wrap the existing filesystem remote without changing its service fixture."""
    class HistogramRemote(base_remote):
        histogram_fixture = None
        histogram_enabled = False
        histogram_pause_requested = False

        def enable_histogram_samples(self, fixture):
            if self.histogram_enabled: raise RuntimeError('Histogram boundary already active')
            self.histogram_fixture = fixture
            self.histogram_stops = 0
            if self.plain(f'Z1,{GETTER:x},2') != 'OK': raise RuntimeError('Cannot install supplied-bin boundary')
            self.histogram_enabled = True

        def disable_histogram_samples(self):
            if self.histogram_enabled and self.plain(f'z1,{GETTER:x},2') != 'OK':
                raise RuntimeError('Cannot remove supplied-bin boundary')
            self.histogram_enabled = False

        def refresh_fixture_breakpoint(self):
            super().refresh_fixture_breakpoint()
            if self.histogram_enabled:
                self.plain(f'z1,{GETTER:x},2')
                if self.plain(f'Z1,{GETTER:x},2') != 'OK': raise RuntimeError('Cannot restore supplied-bin observation')

        def receive(self):
            while True:
                packet = super().receive()
                if self.histogram_pause_requested or not self.histogram_enabled or not packet.startswith('T') or 'thread:' not in packet: return packet
                thread = packet.split('thread:')[1].split(';')[0]
                if self.plain('Hg' + thread) != 'OK': raise RuntimeError('Cannot select sample caller CPU')
                registers = bytearray.fromhex(self.plain('g'))
                if len(registers) < 68: raise RuntimeError('Unexpected ARM register packet')
                if struct.unpack_from('<I', registers, 60)[0] != GETTER: return packet
                self.histogram_stops += 1
                if self.histogram_stops > 256: raise RuntimeError('Supplied-bin stop budget exceeded')
                result = self.histogram_fixture.request(self, registers)
                if result is None:
                    if self.plain(f'z1,{GETTER:x},2') != 'OK' or self.plain('Hc' + thread) != 'OK':
                        raise RuntimeError('Cannot pass through a native sample caller')
                    stepped = self.plain('s')
                    if not stepped.startswith('T05') or self.plain('Hc-1') != 'OK':
                        raise RuntimeError('Unexpected sample pass-through step')
                    if self.plain(f'Z1,{GETTER:x},2') != 'OK': raise RuntimeError('Cannot restore sample boundary')
                else:
                    lr = struct.unpack_from('<I', registers, 56)[0]
                    # Legacy ARM g has FPA placeholders before CPSR. XML core
                    # packets put CPSR after r15, including extended VFP forms.
                    if len(registers) not in (68, 168, 200, 328): raise RuntimeError('Unsupported ARM register layout')
                    cpsr_offset = 164 if len(registers) == 168 else 64
                    cpsr = struct.unpack_from('<I', registers, cpsr_offset)[0]
                    struct.pack_into('<I', registers, 0, result)
                    struct.pack_into('<I', registers, 60, lr & ~1)
                    struct.pack_into('<I', registers, cpsr_offset, (cpsr & ~0x20) | 0x20)
                    if self.plain('G' + registers.hex()) != 'OK': raise RuntimeError('Cannot return supplied sample result')
                self.send('c')
    return HistogramRemote
