"""Filesystem stop handling must preserve a requested diagnostic pause."""
from pathlib import Path
import struct
import sys
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from module_file_fixture import ModuleFileRemote, DISPATCH


class Fixture:
    finished = False
    def __init__(self, result): self.result, self.requests = result, []
    def request(self, remote, pointer): self.requests.append(pointer); return self.result


class RemoteFixture(ModuleFileRemote):
    def __init__(self, result, stop):
        self.fixture = Fixture(result)
        self.fixture_enabled, self.fixture_stop_requested = True, stop
        self.fixture_transaction = threading.Lock()
        self.dispatch_stops, self.commands, self.sent = 0, [], []
        words = [0x11220000 + i for i in range(17)]
        words[0], words[14], words[15], words[16] = 0xa2001000, 0x10450001, DISPATCH, 0x60000000
        self.original = struct.pack('<17I', *words)
        self.register_bytes = self.original
        class Socket:
            def sendall(_, value):
                if not self.fixture_transaction.locked(): raise AssertionError('Unserialized interrupt')
                self.sent.append(value)
        self.sock = Socket()

    def plain(self, command):
        self.commands.append(command)
        if command == 'g': return self.register_bytes.hex()
        if command.startswith('G'):
            self.register_bytes = bytes.fromhex(command[1:]); return 'OK'
        if command == 's': return 'T05thread:1;'
        return 'OK'

    def send(self, command): self.sent.append(command)


class ModuleFileRemoteTests(unittest.TestCase):
    def test_owned_dispatch_completes_but_does_not_resume_requested_stop(self):
        remote = RemoteFixture(0x80000010, True)
        packet = 'T05thread:1;'
        self.assertEqual(remote.service_fixture_packet(packet), packet)
        self.assertEqual(remote.sent, [])
        words = list(struct.unpack('<17I', remote.original))
        words[0], words[15], words[16] = 0x80000010, 0x10450000, 0x60000020
        self.assertEqual(remote.register_bytes, struct.pack('<17I', *words))
        self.assertEqual(remote.fixture.requests, [0xa2001000])

    def test_unrelated_dispatch_steps_original_instruction_and_stays_paused(self):
        remote = RemoteFixture(None, True)
        self.assertEqual(remote.service_fixture_packet('T05thread:1;'), 'T05thread:1;')
        self.assertEqual(remote.register_bytes, remote.original)
        self.assertEqual(remote.commands[-5:], [f'z1,{DISPATCH:x},2', 'Hc1', 's', 'Hc-1', f'Z1,{DISPATCH:x},2'])
        self.assertEqual(remote.sent, [])

    def test_without_pause_intent_the_fixture_keeps_guest_running(self):
        remote = RemoteFixture(0, False)
        self.assertIsNone(remote.service_fixture_packet('T05thread:1;'))
        self.assertEqual(remote.sent, ['c'])

    def test_interrupt_is_serialized_and_records_pause_intent(self):
        remote = RemoteFixture(0, False)
        remote.request_fixture_stop()
        self.assertTrue(remote.fixture_stop_requested)
        self.assertEqual(remote.sent, [b'\x03'])

    def test_original_read_only_fixture_still_retires_automatically(self):
        remote = RemoteFixture(0, False)
        remote.fixture.finished = True
        self.assertIsNone(remote.service_fixture_packet('T05thread:1;'))
        self.assertFalse(remote.fixture_enabled)
        self.assertEqual(remote.commands[-1], f'z1,{DISPATCH:x},2')
        self.assertEqual(remote.sent, ['c'])

    def test_non_filesystem_stop_is_returned_without_advancing_guest(self):
        remote = RemoteFixture(0, True)
        words = list(struct.unpack('<17I', remote.register_bytes)); words[15] = 0x100531bc
        remote.register_bytes = struct.pack('<17I', *words)
        self.assertEqual(remote.service_fixture_packet('T02thread:1;'), 'T02thread:1;')
        self.assertEqual(remote.fixture.requests, [])
        self.assertEqual(remote.sent, [])


if __name__ == '__main__': unittest.main()
