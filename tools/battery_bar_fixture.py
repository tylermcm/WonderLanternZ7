# SPDX-License-Identifier: MIT
"""Explicit incoming battery-bar inputs for private original-Z7 QEMU tests.

At the original typed-cache conversion compare, supply the two already-read
inputs. Original conversion, stores, GUI rendering, percentage getter and module
callbacks execute. No RAM object, percentage, framebuffer or return is supplied.
This is not an EX MCU model or physical battery-telemetry validation.
"""
import struct

POINT = 0x10368572
SNAPSHOTS = (0xa201d4d0, 0xa201d80c)


class BatteryBarFixture:
    def __init__(self, instruction):
        if instruction != bytes.fromhex('022a'):
            raise ValueError('Unexpected native battery-bar compare instruction')
        self.bar = None
        self.events = []
        self.stops = 0

    def select(self, bar):
        if bar not in (0, 1):
            raise ValueError('Fixture supports native adapter or full-battery bar only')
        self.bar = bar
        self.events.append(dict(operation='select', bar=bar))

    def apply(self, registers):
        if self.bar is None:
            raise RuntimeError('Battery-bar fixture has not been selected')
        if len(registers) not in (68, 168, 200, 328):
            raise ValueError('Unsupported ARM register layout')
        words = struct.unpack_from('<16I', registers)
        if words[15] != POINT:
            raise ValueError('Unexpected battery input boundary')
        self.stops += 1
        if self.stops > 2048:
            raise RuntimeError('Battery input observation budget exceeded')
        if words[6] not in SNAPSHOTS:
            self.events.append(dict(operation='unowned-target', target=hex(words[6])))
            return False
        # Native kind1/level4 -> bar1. Native kind2 -> adapter bar0.
        kind, level = (1, 4) if self.bar else (2, 0)
        struct.pack_into('<2I', registers, 4, level, kind)
        self.events.append(dict(operation='inputs', target=hex(words[6]),
                                original_kind=words[2], original_level=words[1],
                                supplied_kind=kind, supplied_level=level, bar=self.bar))
        return True


def battery_bar_remote(parent, fixture):
    """Compose with the persistent ModuleFileRemote service/stop serialization."""
    class BatteryBarRemote(parent):
        battery_bar_enabled = False

        def enable_battery_bar(self, bar):
            fixture.select(bar)
            if not self.fixture_enabled:
                raise RuntimeError('Battery input fixture requires persistent file-service observation')
            if not self.battery_bar_enabled:
                if self.plain(f'Z1,{POINT:x},2') != 'OK':
                    raise RuntimeError('Cannot observe native battery input conversion')
                self.battery_bar_enabled = True

        def service_fixture_packet(self, packet):
            if self.battery_bar_enabled:
                thread = packet.split('thread:')[1].split(';')[0]
                if self.plain('Hg' + thread) != 'OK':
                    raise RuntimeError('Cannot select battery conversion CPU')
                registers = bytearray.fromhex(self.plain('g'))
                if len(registers) < 68:
                    raise RuntimeError('Short battery input register packet')
                if struct.unpack_from('<I', registers, 60)[0] == POINT:
                    if fixture.apply(registers) and self.plain('G' + registers.hex()) != 'OK':
                        raise RuntimeError('Cannot supply incoming battery-bar inputs')
                    if self.plain(f'z1,{POINT:x},2') != 'OK' or self.plain('Hc' + thread) != 'OK':
                        raise RuntimeError('Cannot step original battery conversion compare')
                    stepped = self.plain('s')
                    if not stepped.startswith('T05') or self.plain('Hc-1') != 'OK':
                        raise RuntimeError('Unexpected battery conversion step result')
                    if self.plain(f'Z1,{POINT:x},2') != 'OK':
                        raise RuntimeError('Cannot restore battery conversion observation')
                    if self.fixture_stop_requested:
                        return stepped
                    self.send('c')
                    return None
            return super().service_fixture_packet(packet)
    return BatteryBarRemote
