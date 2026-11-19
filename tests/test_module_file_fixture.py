"""Ownership, bounds and pass-through checks for the explicit QEMU file HLE."""
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from module_file_fixture import ModuleFileFixture, FD


class Memory:
    def __init__(self):
        self.data = {}

    def write_memory(self, pointer, data):
        self.data.update((pointer + i, byte) for i, byte in enumerate(data))

    def memory(self, pointer, length):
        return bytes(self.data.get(pointer + i, 0) for i in range(length))


class ModuleFileFixtureTests(unittest.TestCase):
    def setUp(self):
        self.memory = Memory()
        self.fixture = ModuleFileFixture(bytes(i % 256 for i in range(800)))
        self.path = 0xa1801000
        self.message = 0xa1802000
        self.buffer = 0xa1803000
        self.actual = 0xa1804000
        self.stat = 0xa1805000
        self.memory.write_memory(self.path, b'A:\\Z7APP.BIN\0')
        self.memory.write_memory(self.buffer, b'\xa5' * 640)

    def request(self, opcode, **fields):
        words = [0] * 42
        for index, value in fields.items():
            words[int(index)] = value
        data = bytearray(struct.pack('<42I', *words))
        data[0x9c] = opcode
        self.memory.write_memory(self.message, data)
        return self.fixture.request(self.memory, self.message)

    def opened(self):
        self.assertEqual(self.request(5, **{'4': self.path}), FD)
        self.assertEqual(self.request(16, **{'4': self.path, '21': self.stat}), 0)
        self.assertEqual(struct.unpack('<Q', self.memory.memory(self.stat + 0x218, 8))[0], 800)

    def test_exact_payload_and_padding_across_two_native_reads(self):
        self.opened()
        self.assertEqual(self.request(8, **{'7': FD, '10': self.buffer, '11': 512, '12': self.actual}), 0)
        self.assertEqual(self.memory.memory(self.buffer, 512), self.fixture.packet[:512])
        self.assertEqual(self.memory.memory(self.buffer + 512, 128), b'\xa5' * 128)
        self.assertEqual(struct.unpack('<I', self.memory.memory(self.actual, 4))[0], 512)
        self.memory.write_memory(self.buffer, b'\xa5' * 640)
        self.assertEqual(self.request(8, **{'7': FD, '10': self.buffer, '11': 289, '12': self.actual}), 0)
        self.assertEqual(self.memory.memory(self.buffer, 288), self.fixture.packet[512:])
        self.assertEqual(self.memory.memory(self.buffer + 288, 352), b'\xa5' * 352)
        self.assertEqual(struct.unpack('<I', self.memory.memory(self.actual, 4))[0], 288)
        self.assertEqual(self.fixture.position, 800)

    def test_fixture_retires_only_after_original_post_close_stat(self):
        self.opened()
        self.assertEqual(self.request(6, **{'7': FD}), 0)
        self.assertFalse(self.fixture.finished)
        self.assertEqual(self.request(16, **{'4': self.path, '21': self.stat}), 0)
        self.assertTrue(self.fixture.finished)
        with self.assertRaises(AssertionError):
            self.request(6, **{'7': FD})

    def test_unrelated_requests_and_handles_are_passed_through(self):
        self.memory.write_memory(self.path, b'A:\\NIKON001.DSC\0')
        self.assertIsNone(self.request(5, **{'4': self.path}))
        self.assertIsNone(self.request(8, **{'7': 7}))
        self.assertIsNone(self.request(9, **{'7': FD}))
        self.assertFalse(self.fixture.opened)
        self.assertEqual(self.fixture.events, [])

    def test_owned_read_bounds_alignment_and_write_open_rejected(self):
        with self.assertRaises(AssertionError):
            self.request(5, **{'4': self.path, '5': 1})
        self.opened()
        for capacity, buffer in ((0, self.buffer), (514, self.buffer), (1, self.buffer + 1)):
            with self.assertRaises(AssertionError):
                self.request(8, **{'7': FD, '10': buffer, '11': capacity, '12': self.actual})

    def test_only_bounded_nonempty_module_files_are_accepted(self):
        for data in (b'', bytes((1 << 20) + 1)):
            with self.assertRaises(ValueError):
                ModuleFileFixture(data)


if __name__ == '__main__':
    unittest.main()
