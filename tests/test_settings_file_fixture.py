"""Persistent-file HLE ownership, byte boundaries and lifetime contracts."""
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from settings_file_fixture import SettingsFileFixture, PATHS, NOT_FOUND
from module_file_fixture import FD
from test_module_file_fixture import Memory


class SettingsFileFixtureTests(unittest.TestCase):
    def setUp(self):
        self.memory = Memory()
        self.fixture = SettingsFileFixture(bytes(i % 251 for i in range(800)))
        self.path, self.message, self.buffer, self.actual, self.stat = (0xa1801000, 0xa1802000, 0xa1803000, 0xa1804000, 0xa1805000)
        self.memory.write_memory(self.path, b'A:\\Z7APP.BIN\0')

    def request(self, opcode, **fields):
        words = [0] * 42
        for i, value in fields.items(): words[int(i)] = value
        data = bytearray(struct.pack('<42I', *words)); data[0x9c] = opcode
        self.memory.write_memory(self.message, data)
        return self.fixture.request(self.memory, self.message)

    def loaded(self):
        self.assertEqual(self.request(5, **{'4': self.path}), FD)
        self.assertEqual(self.request(16, **{'4': self.path, '21': self.stat}), 0)
        for capacity in (512, 289):
            self.assertEqual(self.request(8, **{'7': FD, '10': self.buffer, '11': capacity, '12': self.actual}), 0)
        self.assertEqual(self.request(6, **{'7': FD}), 0)
        self.assertEqual(self.request(16, **{'4': self.path, '21': self.stat}), 0)
        self.assertTrue(self.fixture.module_finished)
        self.assertFalse(self.fixture.finished)

    def path_for(self, slot): self.memory.write_memory(self.path, PATHS[slot] + b'\0')

    def test_settings_remain_available_after_module_retirement(self):
        self.loaded()
        for slot in (0, 1):
            self.path_for(slot)
            self.assertEqual(self.request(5, **{'4': self.path}), NOT_FOUND)
        self.assertFalse(self.fixture.handles)
        self.assertEqual(self.fixture.position, 800)
        self.assertEqual(self.fixture.packet, bytes(i % 251 for i in range(800)))

    def test_explicit_open_error_is_not_absence_and_preserves_unread_slots(self):
        self.loaded(); self.path_for(0)
        self.fixture.files = {0: b'old0', 1: b'old1'}
        self.fixture.fail_open = True
        self.assertEqual(self.request(5, **{'4': self.path}), 0x80000002)
        self.assertEqual(self.fixture.files, {0: b'old0', 1: b'old1'})
        self.assertFalse(self.fixture.handles)
        self.assertFalse(self.fixture.issued)
        self.fixture.fail_open = False
        fd = self.request(5, **{'4': self.path})
        self.assertIn(fd, self.fixture.handles)
        self.request(6, **{'7': fd})

    def test_explicit_create_failure_preserves_both_slots_and_allocates_no_handle(self):
        self.loaded(); self.path_for(0)
        self.fixture.files = {0: b'valid-old', 1: b'valid-peer'}
        self.fixture.fail_create = True
        self.assertEqual(self.request(13, **{'4': self.path}), 0x80000002)
        self.assertEqual(self.fixture.files, {0: b'valid-old', 1: b'valid-peer'})
        self.assertFalse(self.fixture.handles)
        self.assertFalse(self.fixture.issued)
        self.assertEqual(self.fixture.events[-1]['injected_error'], '0x80000002')
        self.fixture.fail_create = False
        fd = self.request(13, **{'4': self.path})
        self.assertIn(fd, self.fixture.handles)
        self.assertEqual(self.fixture.files, {0: b'', 1: b'valid-peer'})
        self.request(6, **{'7': fd})

    def test_exact_write_read_and_close_preserve_other_slot_and_padding(self):
        self.loaded()
        self.fixture.files[1] = b'old-peer'
        self.path_for(0)
        fd = self.request(13, **{'4': self.path})
        payload = bytes(range(80))
        self.memory.write_memory(self.buffer, payload + b'\xa5' * 112)
        self.assertEqual(self.request(9, **{'7': fd, '10': self.buffer, '11': 80, '12': self.actual}), 0)
        self.assertEqual(self.fixture.files, {0: payload, 1: b'old-peer'})
        self.assertEqual(self.request(6, **{'7': fd}), 0)
        read_fd = self.request(5, **{'4': self.path})
        self.assertNotEqual(fd, read_fd)
        self.memory.write_memory(self.buffer, b'\xa5' * 192)
        self.assertEqual(self.request(8, **{'7': read_fd, '10': self.buffer, '11': 81, '12': self.actual}), 0)
        self.assertEqual(self.memory.memory(self.buffer, 192), payload + b'\xa5' * 112)
        self.assertEqual(self.memory.memory(self.actual, 4), struct.pack('<I', 80))
        self.assertEqual(self.request(6, **{'7': read_fd}), 0)
        with self.assertRaises(AssertionError): self.request(6, **{'7': read_fd})

    def test_read_lengths_are_opaque_but_bounded_by_guest_capacity(self):
        self.loaded(); self.path_for(0)
        for size in (0, 79, 80, 81, 4096):
            self.fixture.files[0] = b'x' * size
            fd = self.request(5, **{'4': self.path})
            self.memory.write_memory(self.buffer, b'\xa5' * 192)
            self.assertEqual(self.request(8, **{'7': fd, '10': self.buffer, '11': 81, '12': self.actual}), 0)
            count = min(size, 81)
            self.assertEqual(self.memory.memory(self.buffer, 192), b'x' * count + b'\xa5' * (192 - count))
            self.assertEqual(self.memory.memory(self.actual, 4), struct.pack('<I', count))
            self.request(6, **{'7': fd})

    def test_permissions_lengths_and_ram_ranges_fail_before_changes(self):
        self.loaded(); self.path_for(0); self.fixture.files[0] = b'x' * 80
        fd = self.request(5, **{'4': self.path})
        with self.assertRaises(AssertionError): self.request(9, **{'7': fd, '10': self.buffer, '11': 80, '12': self.actual})
        for capacity, pointer, actual in ((80, self.buffer, self.actual), (82, self.buffer, self.actual), (81, self.buffer + 1, self.actual), (81, 0x10020000, self.actual), (81, self.buffer, self.actual + 1), (81, self.buffer, 0xc0000000)):
            with self.assertRaises(AssertionError): self.request(8, **{'7': fd, '10': pointer, '11': capacity, '12': actual})
        self.assertEqual(self.fixture.handles[fd]['position'], 0)
        self.assertEqual(self.fixture.files[0], b'x' * 80)

    def test_unrelated_paths_and_handles_pass_through_without_writes(self):
        self.loaded()
        self.memory.write_memory(self.path, b'A:\\NIKON001.DSC\0')
        before = dict(self.memory.data)
        self.assertIsNone(self.request(5, **{'4': self.path}))
        self.assertIsNone(self.request(8, **{'7': 7}))
        # Only request-message memory changes; no supplied response/payload stores.
        self.assertEqual({k: v for k, v in self.memory.data.items() if not self.message <= k < self.message + 168}, {k: v for k, v in before.items() if not self.message <= k < self.message + 168})
        self.assertEqual(self.fixture.files, {})

    def test_module_is_immutable_and_owned_stale_handles_are_not_reused(self):
        self.loaded()
        with self.assertRaises(AssertionError): self.request(9, **{'7': FD})
        self.path_for(0)
        with self.assertRaises(AssertionError): self.request(5, **{'4': self.path, '5': 1})
        with self.assertRaises(AssertionError): self.request(13, **{'4': self.path, '6': 1})
        with self.assertRaises(AssertionError): self.request(16, **{'4': self.path, '21': self.stat})

    def test_retirement_requires_all_owned_files_closed(self):
        with self.assertRaises(RuntimeError): self.fixture.retire()
        self.loaded(); self.path_for(0)
        fd = self.request(13, **{'4': self.path})
        with self.assertRaises(RuntimeError): self.fixture.retire()
        self.request(6, **{'7': fd}); self.fixture.retire()
        self.assertTrue(self.fixture.finished)
        with self.assertRaises(AssertionError): self.request(5, **{'4': self.path})

    def test_initial_files_are_limited_to_owned_slots_and_size(self):
        for files in ({2: b''}, {0: bytes(4097)}):
            with self.assertRaises(ValueError): SettingsFileFixture(b'module', files)


if __name__ == '__main__': unittest.main()
