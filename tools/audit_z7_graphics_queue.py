"""Original Z7 rectangle producer, enqueue wrapper, dispatcher and completion.

SPDX-License-Identifier: MIT. Kernel queue/locks/events and rectangle renderer
are supplied. Two Unicorn CPUs model an explicit serialized task schedule, not
native task concurrency or pixels. No camera/card access or hook installation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2
from audit_splash_image import NativePNG, BASE, MEM, STOCK_SHA
from build_z7_module_host import ROOT

TASK, MODE, EVENT = 0xa1d75d34, 0xa180ad70, 0xa1d75e3c
PRODUCER, DISPATCH, RENDER, COMPLETE = 0x1042f5f6, 0x10372390, 0x1042f5a8, 0x1042eade
MESSAGE, PAYLOAD = MEM+0x60000, MEM+0x60100
TASK_DESCRIPTOR = MEM+0x60200


class GraphicsFixture(NativePNG):
    def __init__(self, raw, consumer=None):
        super().__init__(raw)
        self.u.mem_map(0xa1d75000, 0x1000)
        self.consumer = consumer
        self.rendered, self.queued, self.completions, self.events = [], [], [], []
        self.waits = 0
        self.registration = []

    def hook(self, u, address, size, context):
        r0, r1, r2 = (u.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2))
        if address == RENDER:
            self.rendered.append(bytes(u.mem_read(r0, 28)))
            self.ret(0)
        elif address == 0x101123b4:
            assert (r0, r1) == (TASK+0x20, TASK_DESCRIPTOR+0x10)
            self.registration.append(('queue-init', r0, r1))
            self.ret(0)
        elif address == 0x1017074a:
            assert r0 == TASK and r2 == TASK_DESCRIPTOR
            self.registration.append(('task-start', r0, r2))
            self.ret(0)
        elif address in (0x101641fa, 0x101641dc):
            assert r0 == TASK+0x30, 'Unexpected graphics lock'
            self.ret(0)
        elif address == 0x10112446:
            assert self.consumer is not None and r0 == TASK+0x20
            message = bytearray(u.mem_read(r1, 28))
            assert struct.unpack_from('<I', message, 8)[0] == r1, 'Native enqueue self link missing'
            payload = bytes(u.mem_read(struct.unpack_from('<I', message, 20)[0], 24))
            self.queued.append((bytes(message), payload))
            # Separate CPU avoids recursive execution of the producer CPU.
            # Producer stack remains live until this supplied task completes.
            struct.pack_into('<I', message, 20, PAYLOAD)
            self.consumer.u.mem_write(MESSAGE, bytes(message))
            self.consumer.u.mem_write(PAYLOAD, payload)
            self.consumer.call(DISPATCH, MESSAGE)
            assert self.consumer.completions[-1] == (0x42010062, 0), self.consumer.completions
            assert self.consumer.events[-1] == (EVENT, 1)
            u.mem_write(r1+24, bytes(self.consumer.u.mem_read(MESSAGE+24, 4)))
            self.ret(0)
        elif address == COMPLETE:
            self.completions.append((r0, r1))  # Original callback continues.
        elif address in (0x10170bee, 0x10170be8):
            assert (r0, r1) == (EVENT, 1)
            self.events.append((r0, r1))
            self.ret(0)
        elif address == 0x10170c72:
            assert (r0, r1) == (EVENT, 1) and self.consumer.completions
            self.waits += 1
            u.mem_write(r2, struct.pack('<I', 1))
            self.ret(0)
        else:
            super().hook(u, address, size, context)


def audit(raw):
    checks = []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    check('native-task-queue-and-dispatch-bindings',
          struct.unpack_from('<2I', raw, 0x103727b8-BASE) == (TASK+0x30, DISPATCH|1))
    check('native-rectangle-message-and-completion-bindings',
          struct.unpack_from('<3I', raw, 0x1042f794-BASE) == (0x42010014, COMPLETE|1, EVENT))
    registration = GraphicsFixture(raw)
    registration.u.mem_write(TASK, b'\xa5'*0x30)
    registration.call(0x101f2414, TASK, DISPATCH|1, TASK_DESCRIPTOR)
    check('original-registration-publishes-dispatch-at-task-plus-2c',
          bytes(registration.u.mem_read(TASK,0x30)) == b'\xa5'*0x2c+struct.pack('<I',DISPATCH|1) and
          registration.registration == [('queue-init',TASK+0x20,TASK_DESCRIPTOR+0x10),('task-start',TASK,TASK_DESCRIPTOR)])
    for mode in (0, 1, 2, 0xffff):
        for box in ((0,0,720,480), (110,194,110,24), (719,479,1,1)):
            consumer = GraphicsFixture(raw)
            producer = GraphicsFixture(raw, consumer)
            producer.u.mem_write(MODE, struct.pack('<H', mode))
            # Unused input words differ deliberately: queued payload normalizes
            # them to zero; direct rendering receives the original structure.
            shape = struct.pack('<6I4B', *box, 0x12345678, 0x87654321, 1, 2, 0xa5, 0x5a)
            producer.u.mem_write(PAYLOAD, shape)
            producer.call(PRODUCER, PAYLOAD)
            check(f'mode{mode}-box{box}-producer-input-unchanged', bytes(producer.u.mem_read(PAYLOAD,28)) == shape)
            if mode:
                expected = struct.pack('<6I4B', *box, 0, 0, 1, 2, 0, 0)
                check(f'mode{mode}-box{box}-native-queue-marshalling-dispatch-and-completion',
                      len(producer.queued) == 1 and not producer.rendered and consumer.rendered == [expected] and
                      consumer.completions == [(0x42010062,0)] and producer.waits == 1 and
                      struct.unpack_from('<I',producer.queued[0][0],16)[0] == 0x42010017 and
                      struct.unpack_from('<I',consumer.u.mem_read(MESSAGE+24,4))[0] == 0)
            else:
                check(f'mode{mode}-box{box}-native-direct-rendering-bypasses-queue',
                      producer.rendered == [shape] and not producer.queued and not consumer.rendered and producer.waits == 0)
    return dict(passed=True, checks=checks, stock_main_sha256=STOCK_SHA,
                original_producer_enqueue_wrapper_dispatcher_and_completion_execute=True,
                kernel_queue_locks_events_and_rectangle_renderer_supplied=True,
                schedule='Serialized producer enqueue, separate consumer CPU, completion, producer wait return',
                native_task_concurrency_graphics_slot_installation_or_pixels_proven=False,
                camera_card_access=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists(): p.error('Choose a new private output file')
    raw=a.stock_main.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=STOCK_SHA: p.error('Exact original Z7 C3.80 MAIN required')
    result=audit(raw)
    names=('tools/audit_z7_graphics_queue.py','tools/audit_splash_image.py','tools/build_z7_module_host.py')
    result['source_sha256']={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']))))


if __name__=='__main__': main()
