"""Supplied-bin boundary ownership and immutable-buffer tests; no guest/device."""
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from histogram_sample_fixture import HistogramSampleFixture, DIAGNOSTIC_BINS, GETTER, sample_remote, histogram_scanout_box


class FakeRemote:
    def __init__(self): self.writes = []; self.cleared = True
    def memory(self, address, length): return bytes(length) if self.cleared else b'\xa5' * length
    def write_memory(self, address, data): self.writes.append((address, bytes(data)))


class HistogramSampleTests(unittest.TestCase):
    def fixture(self): return HistogramSampleFixture(0xa2900000, 4096, 6144, 4096)
    def registers(self, destination=0xa2901000, caller=0xa2900021):
        data = bytearray(68); struct.pack_into('<I', data, 0, destination); struct.pack_into('<I', data, 56, caller)
        return data
    def test_exact_owned_caller_buffer_writes_only1024_bytes(self):
        f = self.fixture(); r = FakeRemote(); self.assertEqual(f.request(r, self.registers()), 1)
        self.assertEqual(r.writes, [(0xa2901000, struct.pack('<256I', *DIAGNOSTIC_BINS))])
        self.assertFalse(f.events[-1]['native_event_completed'])
    def test_native_or_non_thumb_callers_pass_through_without_writes(self):
        for caller in (0x104070b1, 0xa28fffff, 0xa2901001, 0xa2900020):
            f = self.fixture(); r = FakeRemote(); self.assertIsNone(f.request(r, self.registers(caller=caller)))
            self.assertFalse(r.writes)
    def test_owned_caller_wrong_buffer_rejected_without_write(self):
        f = self.fixture(); r = FakeRemote()
        with self.assertRaises(AssertionError): f.request(r, self.registers(destination=0xa2901040))
        self.assertFalse(r.writes)
    def test_stale_buffer_rejected_without_write(self):
        f = self.fixture(); r = FakeRemote(); r.cleared = False
        with self.assertRaises(AssertionError): f.request(r, self.registers())
        self.assertFalse(r.writes)
    def test_invalid_bounds_alignment_and_bin_counts_rejected(self):
        for args in [(0xa2900001, 4096, 6144, 4096), (0xa2900000, 6144, 4096, 4096),
                     (0xa2900000, 4096, 6144, 4097), (0xa2900000, 4096, 4608, 4096),
                     (0xbffff000, 4096, 6144, 4096)]:
            with self.assertRaises(ValueError): HistogramSampleFixture(*args)
        for bins in ([0] * 255, [0] * 257, [-1] * 256, [1 << 32] * 256):
            with self.assertRaises(ValueError): HistogramSampleFixture(0xa2900000, 4096, 6144, 4096, bins)
    def test_input_samples_are_frozen(self):
        bins = list(DIAGNOSTIC_BINS); f = HistogramSampleFixture(0xa2900000, 4096, 6144, 4096, bins)
        bins[0] = 999; r = FakeRemote(); f.request(r, self.registers())
        self.assertEqual(struct.unpack_from('<I', r.writes[0][1])[0], DIAGNOSTIC_BINS[0])


class ProtocolRemote(FakeRemote):
    def __init__(self, length=68, caller=0xa2900021):
        super().__init__(); self.commands = []; self.sent = []; self.responses = ['T05thread:p01.01;', 'complete']
        self.registers = bytearray(length)
        for i in range(16): struct.pack_into('<I', self.registers, 4 * i, 0x12340000 + i)
        struct.pack_into('<I', self.registers, 0, 0xa2901000)
        struct.pack_into('<I', self.registers, 56, caller)
        struct.pack_into('<I', self.registers, 60, GETTER)
        struct.pack_into('<I', self.registers, 164 if length == 168 else 64, 0xa0000013)
        self.updated = None
    def receive(self): return self.responses.pop(0)
    def send(self, command): self.sent.append(command)
    def plain(self, command):
        self.commands.append(command)
        if command == 'g': return self.registers.hex()
        if command.startswith('G'): self.updated = bytearray.fromhex(command[1:])
        if command == 's': return 'T05thread:p01.01;'
        return 'OK'
    def refresh_fixture_breakpoint(self): self.commands.append('base-refresh')


class HistogramProtocolTests(unittest.TestCase):
    def test_owned_return_preserves_other_registers_flags_and_thumb(self):
        for length in (68, 168, 200, 328):
            remote = sample_remote(ProtocolRemote)(length)
            remote.enable_histogram_samples(HistogramSampleFixture(0xa2900000, 4096, 6144, 4096))
            before = bytes(remote.registers)
            self.assertEqual(remote.receive(), 'complete')
            updated = remote.updated
            self.assertEqual(struct.unpack_from('<I', updated, 0)[0], 1)
            self.assertEqual(struct.unpack_from('<I', updated, 60)[0], 0xa2900020)
            cpsr = 164 if length == 168 else 64
            self.assertEqual(struct.unpack_from('<I', updated, cpsr)[0], 0xa0000033)
            for i in range(len(before)):
                if i not in set(range(4)) | set(range(60, 64)) | set(range(cpsr, cpsr + 4)):
                    self.assertEqual(updated[i], before[i])
            self.assertEqual(remote.sent, ['c']); self.assertEqual(len(remote.writes), 1)
    def test_native_caller_steps_original_then_restores_all_cpu_resume(self):
        remote = sample_remote(ProtocolRemote)(caller=0x10203c61)
        remote.enable_histogram_samples(HistogramSampleFixture(0xa2900000, 4096, 6144, 4096))
        self.assertEqual(remote.receive(), 'complete')
        self.assertFalse(remote.writes); self.assertIsNone(remote.updated)
        self.assertIn('Hcp01.01', remote.commands); self.assertIn('Hc-1', remote.commands)
        self.assertIn('s', remote.commands); self.assertEqual(remote.sent, ['c'])
    def test_refresh_and_disable_preserve_base_fixture_and_remove_boundary(self):
        remote = sample_remote(ProtocolRemote)()
        remote.enable_histogram_samples(HistogramSampleFixture(0xa2900000, 4096, 6144, 4096))
        remote.refresh_fixture_breakpoint(); remote.disable_histogram_samples()
        self.assertIn('base-refresh', remote.commands)
        self.assertEqual(remote.commands[-1], f'z1,{GETTER:x},2')
        self.assertFalse(remote.histogram_enabled)
    def test_requested_pause_returns_queued_getter_stop_without_resuming(self):
        remote = sample_remote(ProtocolRemote)()
        remote.enable_histogram_samples(HistogramSampleFixture(0xa2900000, 4096, 6144, 4096))
        remote.histogram_pause_requested = True
        self.assertEqual(remote.receive(), 'T05thread:p01.01;')
        self.assertFalse(remote.sent); self.assertFalse(remote.writes); self.assertIsNone(remote.updated)
        remote.histogram_pause_requested = False
        remote.responses.insert(0, 'T05thread:p01.01;')
        self.assertEqual(remote.receive(), 'complete')
        self.assertEqual(remote.sent, ['c']); self.assertEqual(len(remote.writes), 1)


class NativeHistogramCoordinates(unittest.TestCase):
    def test_native_bottom_up_rectangle_maps_into_scanout(self):
        self.assertEqual(histogram_scanout_box((475, 269, 675, 370), (1024, 682)), (675, 156, 960, 300))
        self.assertEqual(histogram_scanout_box((0, 0, 720, 480), (1024, 682)), (0, 0, 1024, 682))
        self.assertEqual(histogram_scanout_box((0, 470, 10, 480), (720, 480)), (0, 0, 10, 10))
    def test_unidentified_or_empty_rectangles_rejected(self):
        for rect in ((-1, 0, 20, 30), (0, 0, 721, 480), (0, 0, 20, 481), (20, 30, 20, 40)):
            with self.assertRaises(ValueError): histogram_scanout_box(rect, (1024, 682))


if __name__ == '__main__': unittest.main()
