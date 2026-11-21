"""Incoming register boundary safety without Nikon firmware or a camera."""
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from battery_bar_fixture import BatteryBarFixture, POINT, SNAPSHOTS, battery_bar_remote


def registers(length=168, target=SNAPSHOTS[0], pc=POINT):
    packet = bytearray(b'\x55' * length)
    struct.pack_into('<I', packet, 6 * 4, target)
    struct.pack_into('<I', packet, 15 * 4, pc)
    return packet


class BatteryInputTests(unittest.TestCase):
    def test_only_two_incoming_registers_change_in_supported_packets(self):
        for length in (68, 168, 200, 328):
            with self.subTest(length=length):
                fixture = BatteryBarFixture(bytes.fromhex('022a'))
                fixture.select(1)
                packet = registers(length)
                before = bytes(packet)
                self.assertTrue(fixture.apply(packet))
                self.assertEqual(struct.unpack_from('<2I', packet, 4), (4, 1))
                self.assertEqual(packet[:4], before[:4])
                self.assertEqual(packet[12:], before[12:])

    def test_adapter_uses_original_kind_two_input(self):
        fixture = BatteryBarFixture(bytes.fromhex('022a'))
        fixture.select(0)
        packet = registers()
        fixture.apply(packet)
        self.assertEqual(struct.unpack_from('<2I', packet, 4), (0, 2))

    def test_unowned_destination_is_observed_without_mutation(self):
        fixture = BatteryBarFixture(bytes.fromhex('022a'))
        fixture.select(1)
        packet = registers(target=0xa201c000)
        before = bytes(packet)
        self.assertFalse(fixture.apply(packet))
        self.assertEqual(packet, before)
        self.assertEqual(fixture.events[-1]['operation'], 'unowned-target')

    def test_unrecognized_boundary_or_selection_is_rejected(self):
        with self.assertRaises(ValueError): BatteryBarFixture(b'\0\0')
        fixture = BatteryBarFixture(bytes.fromhex('022a'))
        with self.assertRaises(RuntimeError): fixture.apply(registers())
        for bar in (2, 6, -1):
            with self.assertRaises(ValueError): fixture.select(bar)
        fixture.select(1)
        with self.assertRaises(ValueError): fixture.apply(registers(pc=POINT + 2))
        with self.assertRaises(ValueError): fixture.apply(registers(length=72))

    def test_remote_executes_original_compare_and_honors_serialized_stop(self):
        class Parent:
            fixture_enabled = True
            fixture_stop_requested = True
            def __init__(self): self.commands, self.sent = [], []
            def plain(self, command):
                self.commands.append(command)
                if command == 'g': return registers().hex()
                if command == 's': return 'T05thread:p01.01;'
                return 'OK'
            def send(self, command): self.sent.append(command)
            def service_fixture_packet(self, packet): return 'parent-stop'
        fixture = BatteryBarFixture(bytes.fromhex('022a'))
        remote = battery_bar_remote(Parent, fixture)()
        remote.enable_battery_bar(1)
        self.assertEqual(remote.service_fixture_packet('T05thread:p01.01;'), 'T05thread:p01.01;')
        self.assertIn('s', remote.commands)
        self.assertIn('Hcp01.01', remote.commands)
        self.assertIn('Hc-1', remote.commands)
        self.assertEqual(remote.sent, [])
        supplied = [c for c in remote.commands if c.startswith('G')]
        self.assertEqual(len(supplied), 1)
        self.assertEqual(struct.unpack_from('<2I', bytes.fromhex(supplied[0][1:]), 4), (4, 1))


if __name__ == '__main__': unittest.main()
