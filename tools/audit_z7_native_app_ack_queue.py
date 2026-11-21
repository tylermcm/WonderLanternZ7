"""Original Z7 task acknowledgements through native message pool and handler (MIT).

Native registration, device callback, packet encoding, pool initialization/copy/list management,
send wrappers, acknowledgement handler and program manager execute. Kernel queue
send, explicit dequeue/handler selection, locks/event-set and task completion
timing are supplied. No native task scheduling or full device dispatch proof.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2
from audit_splash_image import STOCK_SHA, MEM, STACK
from audit_z7_native_app_task_signals import NativeTaskSignals, WAKE
from audit_z7_native_app_transition import CONTROL, REQUEST
from audit_z7_native_touch_driver import PROGRAMS, GETTERS, OBJECT, ACTIVE

POOL, NODES, BUFFERS = 0xa181971c, 0xa1f954f8, 0xa1f95678
MUTEX, QUEUE = 0xa1f95ef8, MEM + 0xa3000


class AckQueue(NativeTaskSignals):
    kernel_result = 0

    def __init__(self, raw):
        super().__init__(raw)
        self.queued = []
        self.pool_depth = self.program_depth = 0
        self.copies = []
        self.u.mem_map(0xa1f90000, 0x10000)
        self.write(OBJECT + 0x20, QUEUE)
        self.write(OBJECT + 0x134, ACTIVE)
        # Original initializer builds all32 fixed nodes and68-byte buffers.
        self.call(0x100905d0)

    def hook(self, u, address, size, context):
        arg = u.reg_read(UC_ARM_REG_R0)
        if address == 0x1015b74e:
            assert arg == MUTEX
            self.ret(0)
            return
        if address in (0x1015b752, 0x1015b756):
            assert arg == MUTEX
            self.pool_depth += 1 if address == 0x1015b752 else -1
            assert self.pool_depth in (0, 1)
            self.ret(0)
            return
        if address in (0x1015b746, 0x1015b74a):
            self.program_depth += 1 if address == 0x1015b746 else -1
            assert self.program_depth in (0, 1)
            self.ret(0)
            return
        if address == 0x10170ad4 and BUFFERS <= arg < BUFFERS + 32 * 68:
            self.copies.append((arg, u.reg_read(UC_ARM_REG_R1), u.reg_read(UC_ARM_REG_R2)))
        if address == 0x100363cc:
            pointer = u.reg_read(UC_ARM_REG_R1)
            assert arg == QUEUE and BUFFERS <= pointer < BUFFERS + 32 * 68 and (pointer - BUFFERS) % 68 == 0 and u.reg_read(UC_ARM_REG_R2) == 2
            assert self.pool_depth == 0
            self.queued.append((pointer, bytes(u.mem_read(pointer, 68))))
            self.ret(0)
            return
        super().hook(u, address, size, context)


def audit(raw):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA:
        raise ValueError('Requires exact original Z7 C3.80 MAIN')
    f = AckQueue(raw)
    checks = []

    def check(name, good):
        assert good, name
        checks.append(name)

    check('original-device-ack-callback-and-state-handler', f.read(OBJECT + 0xd4) == 0x10058b2b and f.read(ACTIVE + 0x10) == 0x10090647)
    f.call(0x1008fc98, f.read(OBJECT + 0xd4))
    objects = [f.call(getter) for getter in GETTERS]
    for index, obj in enumerate(objects):
        check(f'program{index}-native-ack-registration', f.read(obj + 0x2c) == 0x10058b2b and f.read(obj + 0x34) == index)
    f.write(CONTROL, 1)
    f.write(CONTROL + 4, 1)
    check('native-pool-initializer-creates32-fixed-node-buffer-pairs',
          all(f.read(NODES + 12 * i + 8) == BUFFERS + 68 * i for i in range(32)))

    def deliver(kind, value, target):
        f.queued.clear()
        before = len(f.copies)
        if kind == 4:
            f.u.mem_write(REQUEST, struct.pack('<2I', target, value))
            f.call(0x10058b2a, kind, REQUEST)
        else:
            # This is the native callback dispatcher used by the task loop.
            f.call(0x1020b9f8, objects[target], kind, target)
        check(f'target{target}-kind{kind}-pool-copy-before-send', len(f.queued) == 1 and
              len(f.copies) == before + 1 and f.copies[-1][0] == f.queued[0][0] and f.copies[-1][2] == 68)
        pointer, packet = f.queued[0]
        expected = bytearray(68)
        struct.pack_into('<I', expected, 4, 2)
        struct.pack_into('<I', expected, 8, pointer)
        struct.pack_into('<I', expected, 16, 0x1000000 + kind - 1)
        struct.pack_into('<I', expected, 28, kind)
        struct.pack_into('<I', expected, 32, target)
        if kind == 4:
            struct.pack_into('<I', expected, 36, value)
        check(f'target{target}-kind{kind}-exact-native-message', packet == bytes(expected))
        f.u.mem_write(REQUEST, bytes([0xee]) * 8)
        f.u.mem_write(STACK - 0x800, bytes([0xdd]) * 0x800)
        check(f'target{target}-kind{kind}-packet-survives-sender-stack', bytes(f.u.mem_read(pointer, 68)) == packet)
        check(f'target{target}-kind{kind}-send-does-not-complete-transition',
              f.read(PROGRAMS + 8) == {4:2, 3:3, 2:1}[kind])
        # Dequeue and selection of the existing state handler are explicit
        # fixture boundaries; the handler and program-manager bodies execute.
        payload = pointer + 32 if kind == 4 else f.read(pointer + 32)
        f.call(f.read(ACTIVE + 0x10), ACTIVE, f.read(pointer + 28), payload)
        check(f'target{target}-kind{kind}-locks-released', f.pool_depth == f.program_depth == 0)
        f.call(0x100905e6, pointer)
        check(f'target{target}-kind{kind}-native-pool-recycle',
              [f.read(POOL + o) for o in (0x10, 0x14)] == [POOL + 0x10] * 2 and f.pool_depth == 0)

    for target in range(5):
        current = (target - 1) % 5
        f.u.mem_write(PROGRAMS, bytes([current, 5, 0, 0]))
        f.write(PROGRAMS + 8, 2)
        f.kernel_events.clear()
        deliver(4, 0x2468, target)
        check(f'target{target}-request-waits-for-stop-ack', f.read(PROGRAMS + 8) == 3 and f.kernel_events == [(WAKE, 1)])
        deliver(3, 0, current)
        check(f'target{target}-stop-ack-starts-target', f.read(PROGRAMS + 8) == 1 and f.kernel_events[-1] == (objects[target] + 0x20, 1))
        deliver(2, 0, target)
        check(f'target{target}-start-ack-idles-and-selects-target', f.read(PROGRAMS + 8) == 2 and
              bytes(f.u.mem_read(PROGRAMS, 2)) == bytes([target, 5]) and f.call(0x1008fdc0) == objects[target])
    root = Path(__file__).resolve().parent.parent
    names = ('audit_z7_native_app_ack_queue.py', 'audit_z7_native_app_task_signals.py', 'audit_z7_native_app_transition.py',
             'audit_z7_native_touch_driver.py', 'audit_z7_native_touch_queue.py', 'audit_splash_image.py')
    return dict(schema=1, passed=True, checks=len(checks), check_names=checks, stock_main_sha256=STOCK_SHA,
                native_programs=5, request_ack_packets=15, message_bytes=68, native_pool_nodes=32,
                native_registration_encoding_pool_copy_send_wrappers_state_handler_manager_and_recycle_execute=True,
                supplied_boundaries=['initial native device/program state and opaque handles', 'mapped fixed pool backing memory', 'kernel event-set and queue-send',
                                     'kernel mutex initialization/locks', 'dequeue and state-handler selection', 'task acknowledgement timing'],
                limits=['No actual device queue consumer, native task poll, scheduler or task lifetime proof',
                        'No allocation exhaustion, queue-send failure or producer concurrency coverage',
                        'No camera boot, real kernel handle, flash or recovery clearance'],
                installation_candidate=False,
                source_sha256={'tools/'+name:hashlib.sha256((root/'tools'/name).read_bytes()).hexdigest() for name in names})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--main', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Output must not already exist')
    result = audit(args.main.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('check_names', 'source_sha256')}))


if __name__ == '__main__':
    main()
