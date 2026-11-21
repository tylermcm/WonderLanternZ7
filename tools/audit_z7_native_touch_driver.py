"""Original Z7 touch registration, fanout and application-to-queue path (MIT).

Runs stock driver and dispatch instructions through the stock event producer.
Supplies locks, wake/time/admission services and active state/program selection.
No physical driver initialization, task scheduling or camera acceptance proof.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1
from audit_z7_native_touch_queue import TouchQueue, STATE, RING, STRIDE, PACKET
from audit_splash_image import STOCK_SHA, MEM

SLOTS, READY, DRIVER_LOCK = 0xa1f910ac, 0xa1815b90, 0xa1f91258
OBJECT, ACTIVE, PROGRAMS = 0xa1819748, 0xa181a1f0, 0xa1815c64
CALLBACKS = (MEM + 0x40001, MEM + 0x40011, MEM + 0x40021)
PATH = (0x10058b22, 0x1005d44e, 0x10090640, 0x1009003c,
        0x1008fdc0, 0x1020ba9a, 0x103319d8)
GETTERS = (0x102697b4, 0x1048b0e4, 0x105006e4, 0x10333378, 0x1026ab54)
HANDLERS = (0x10269ab3, 0x1048b3dd, 0x105009bd, 0x103339cf, 0x1026ad7b)


class TouchDriver(TouchQueue):
    def __init__(self, raw):
        super().__init__(raw)
        self.driver_depth = 0
        self.driver_events = []
        for callback in CALLBACKS:
            self.u.mem_write(callback & ~1, b'\x70\x47')

    def word(self, address, value):
        self.u.mem_write(address, struct.pack('<I', value))

    def read(self, address):
        return int.from_bytes(self.u.mem_read(address, 4), 'little')

    def hook(self, u, address, size, context):
        arg = u.reg_read(UC_ARM_REG_R0)
        if address in (0x10170944, 0x1017093e):
            assert arg == DRIVER_LOCK
            self.driver_depth += 1 if address == 0x10170944 else -1
            assert self.driver_depth in (0, 1)
            self.driver_events.append(('lock' if address == 0x10170944 else 'unlock', arg))
            self.ret(0)
            return
        if address in tuple(c & ~1 for c in CALLBACKS):
            assert self.driver_depth == 1
            self.driver_events.append(('callback', address | 1, arg, bytes(u.mem_read(arg, 60))))
            self.ret(0xdeadbeef)
            return
        if address in PATH or address | 1 in HANDLERS:
            assert self.driver_depth == 1
            self.driver_events.append(('native', address, arg))
        if address in (0x1015b746, 0x1015b74a, 0x10406474, 0x104064cc, 0x103661bc):
            assert self.driver_depth == 1
            self.driver_events.append(('service', address, arg, u.reg_read(UC_ARM_REG_R1)))
            if address == 0x104064cc:
                assert u.reg_read(UC_ARM_REG_R1) == 2
            self.ret(0x77 if address == 0x10406474 else 0)
            return
        super().hook(u, address, size, context)


def audit(raw):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA:
        raise ValueError('Requires exact original Z7 C3.80 MAIN')
    f = TouchDriver(raw)
    checks = []

    def check(name, good):
        assert good, name
        checks.append(name)

    f.word(READY, 0)
    for index in range(3):
        check(f'not-ready-registration-{index}', f.call(0x1020d3d4, index, CALLBACKS[index]) == 0xffffffff)
    check('not-ready-preserves-slots', bytes(f.u.mem_read(SLOTS, 12)) == bytes(12))
    f.word(READY, 1)
    for index in (3, 4, 0xffffffff):
        check(f'out-of-range-registration-{index}', f.call(0x1020d3d4, index, CALLBACKS[0]) == 0xffffffff)
    for index in range(3):
        check(f'register-slot-{index}', f.call(0x1015b85a, index, CALLBACKS[index]) == 0 and f.read(SLOTS + 4 * index) == CALLBACKS[index])
        check(f'occupied-slot-{index}-not-replaced', f.call(0x10407846, index, CALLBACKS[(index + 1) % 3]) == 0xffffffff and f.read(SLOTS + 4 * index) == CALLBACKS[index])
        check(f'clear-slot-{index}', f.call(0x1020d3d4, index, 0) == 0 and f.read(SLOTS + 4 * index) == 0)

    packet = bytes(range(60))
    f.u.mem_write(PACKET, packet)
    for mask in range(8):
        for index in range(3):
            check(f'mask{mask}-registration{index}', f.call(0x1020d3d4, index, CALLBACKS[index] if mask & (1 << index) else 0) == 0)
        f.driver_events.clear()
        check(f'mask{mask}-dispatch-return', f.call(0x1020c2d4, 0, PACKET) == 0)
        expected = [('lock', DRIVER_LOCK)] + [
            ('callback', CALLBACKS[i], PACKET, packet) for i in range(3) if mask & (1 << i)
        ] + [('unlock', DRIVER_LOCK)]
        check(f'mask{mask}-locked-synchronous-ordered-fanout', f.driver_events == expected and f.driver_depth == 0)
        check(f'mask{mask}-packet-preserved', bytes(f.u.mem_read(PACKET, 60)) == packet)
        for index in range(3):
            f.call(0x1020d3d4, index, 0)
    for kind in (1, 2, 0xffffffff):
        f.driver_events.clear()
        check(f'nonzero-kind{kind}-ignored', f.call(0x1020c2d4, kind, PACKET) == 0 and not f.driver_events)

    # Initialized native objects/handlers are read from the original RAM image.
    check('native-object-driver-callback', f.read(OBJECT + 0xd0) == 0x10058b23)
    check('native-active-state-handler', f.read(ACTIVE + 0xc) == 0x10090641)
    check('register-original-driver-callback', f.call(0x1020d3d4, 0, f.read(OBJECT + 0xd0)) == 0)
    f.word(OBJECT + 0x134, ACTIVE)
    f.word(PROGRAMS - 0x10, 1)
    for program, admitted in itertools.product(range(5), (False, True)):
        obj = f.call(GETTERS[program])
        check(f'program{program}-original-touch-handler', f.read(obj + 0x50) == HANDLERS[program])
        f.word(PROGRAMS + 0x10 + 12 * program, obj)
        f.u.mem_write(PROGRAMS, bytes([program]))
        f.u.mem_write(STATE, bytes(0x34))
        if not admitted:
            f.word(STATE + 0xc, 1)
        f.u.mem_write(RING, bytes(16 * STRIDE))
        event = bytearray(range(60))
        event[8:10] = b'\x01\x01'
        f.u.mem_write(PACKET, bytes(event))
        f.driver_events.clear()
        f.events.clear()
        check(f'program{program}-admitted{admitted}-fanout-return', f.call(0x1020c2d4, 0, PACKET) == 0)
        visited = [e[1] for e in f.driver_events if e[0] == 'native']
        check(f'program{program}-admitted{admitted}-complete-native-chain', visited == list(PATH[:-1]) + [HANDLERS[program] & ~1, PATH[-1]])
        check(f'program{program}-admitted{admitted}-producer-once-original-packet', [e[2] for e in f.driver_events if e[:2] == ('native', 0x103319d8)] == [PACKET])
        check(f'program{program}-admitted{admitted}-locks-returned', f.depth == f.driver_depth == 0)
        check(f'program{program}-admitted{admitted}-queue-count', f.call(0x1033332e) == int(admitted))
        expected = bytearray(event)
        struct.pack_into('<I', expected, 0, 1)
        check(f'program{program}-admitted{admitted}-queue-copy', bytes(f.u.mem_read(RING, STRIDE)) == (bytes(expected) + bytes(STRIDE - 60) if admitted else bytes(STRIDE)))
        check(f'program{program}-admitted{admitted}-wake-follows-producer-result', sum(e[:2] == ('service', 0x104064cc) for e in f.driver_events) == int(admitted))
        check(f'program{program}-admitted{admitted}-packet-preserved', bytes(f.u.mem_read(PACKET, 60)) == bytes(event))
    return {
        'schema': 1, 'passed': True, 'checks': len(checks), 'check_names': checks,
        'stock_main_sha256': STOCK_SHA, 'fanout_masks': 8, 'native_application_paths': 5,
        'application_admission_cases': 10,
        'scope': 'Native registration and both veneers, slot occupancy/clear/range/ready rejection, locked ordered three-slot fanout, original device/state/program dispatch through five original handlers into stock touch producer and queue',
        'supplied_boundaries': ['OS locks and wake/time services', 'queue admission',
                                'native active state/program selection', 'profile data',
                                'program3 maintenance service'],
        'limits': ['No physical driver initialization or event acquisition',
                   'No native task scheduling, consumer concurrency or lifetime proof',
                   'No installed module touch bridge, camera boot, installation or recovery proof'],
        'installation_candidate': False,
        'source_sha256': {
            str(p.relative_to(Path(__file__).resolve().parent.parent)).replace('\\', '/'):
                hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__).resolve(),
                      Path(__file__).resolve().with_name('audit_z7_native_touch_queue.py'),
                      Path(__file__).resolve().with_name('audit_splash_image.py'))
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--main', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Output must not already exist')
    result = audit(args.main.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'check_names'}))


if __name__ == '__main__':
    main()
