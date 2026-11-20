"""Execute original-Z7 highlight building, queueing and completion handoff.

SPDX-License-Identifier: MIT. Native GUI conversion, builder, queue wrappers,
consumer dispatch and completion callbacks execute. Only kernel queue/event
services and incoming palette/service state are supplied. A separate emulated
consumer stack is an explicit scheduling fixture, not a physical timing proof.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC
from audit_splash_image import NativePNG, MEM, STACK, STOP, ARGUMENTS, SAVED, STOCK_SHA
from audit_z7_display_parameters import COMPLETION, STATE_POINTER
from audit_z7_highlight_converter import ConverterFixture, request
from build_z7_module_host import ROOT

BUILDER, CALLER, QUEUE_HANDLE, EVENT_HANDLE = 0x1034efb0, 0x1034ff1e, 0x12300001, 0x12300002


class SubmissionFixture(ConverterFixture):
    def __init__(self, raw):
        super().__init__(raw)
        self.u.mem_map(0xa1d5f000, 0x1000)
        self.u.mem_map(0xa1f13000, 0x1000)
        self.write(0xa1d5f580, QUEUE_HANDLE)
        self.write(0xa1f1353c, EVENT_HANDLE)
        self.write(0xa1f18fac, MEM + 0x8000)
        self.u.mem_write(MEM + 0x8000, struct.pack('<256I', *[((i * 37 & 255) << 24) | i for i in range(256)]))
        self.queued, self.event_operations, self.native_completions = [], [], []
        self.event_bits, self.wait_pending = 0, None

    def write(self, address, value):
        self.u.mem_write(address, struct.pack('<I', value))

    def read(self, address):
        return int.from_bytes(self.u.mem_read(address, 4), 'little')

    def hook(self, u, address, size, context):
        if address == COMPLETION:
            self.native_completions.append((u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)))
            # Bypass only the older fixture's completion return. Execute the
            # original completion body and its original native callback.
            NativePNG.hook(self, u, address, size, context)
            return
        if address == 0x100363cc:  # Kernel queue send; original wrappers executed.
            handle, packet = u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)
            if handle != QUEUE_HANDLE:
                raise AssertionError('Wrong native display queue handle')
            self.queued.append(dict(packet=packet, command=self.read(packet + 16), payload=self.read(packet + 20),
                                    callback=self.read(packet + 12), context=self.read(packet + 24)))
            self.ret(0)
            return
        if address == 0x10035e94:  # Kernel event clear receives complemented mask.
            if u.reg_read(UC_ARM_REG_R0) != EVENT_HANDLE:
                raise AssertionError('Wrong clear event handle')
            keep = u.reg_read(UC_ARM_REG_R1)
            self.event_bits &= keep
            self.event_operations.append(('clear', (~keep) & 0xffffffff))
            self.ret(0)
            return
        if address == 0x10036334:
            if u.reg_read(UC_ARM_REG_R0) != EVENT_HANDLE:
                raise AssertionError('Wrong set event handle')
            bits = u.reg_read(UC_ARM_REG_R1)
            self.event_bits |= bits
            self.event_operations.append(('set', bits))
            self.ret(0)
            return
        if address == 0x10036504:
            handle, bits, mode, output = [u.reg_read(r) for r in ARGUMENTS]
            if handle != EVENT_HANDLE or mode != 0:
                raise AssertionError('Wrong native event wait contract')
            if self.event_bits & bits:
                self.write(output, self.event_bits & bits)
                self.event_operations.append(('wait-complete', bits))
                self.wait_pending = None
                self.ret(0)
            else:
                self.wait_pending = dict(bits=bits, output=output, stack=u.reg_read(UC_ARM_REG_SP), timeout=self.read(u.reg_read(UC_ARM_REG_SP)))
                self.event_operations.append(('wait-blocked', bits))
                u.emu_stop()
            return
        super().hook(u, address, size, context)


def enter(f, entry, arguments, stack):
    for r in ARGUMENTS:
        f.u.reg_write(r, 0)
    for r, value in zip(ARGUMENTS, arguments):
        f.u.reg_write(r, value)
    guards = {r: 0x51510000 + i for i, r in enumerate(SAVED)}
    for r, value in guards.items():
        f.u.reg_write(r, value)
    f.u.reg_write(UC_ARM_REG_SP, stack)
    f.u.reg_write(UC_ARM_REG_LR, STOP | 1)
    f.u.emu_start(entry | 1, STOP, timeout=10000000, count=10000000)
    return guards


def returned(f, stack, guards):
    return f.u.reg_read(UC_ARM_REG_PC) == STOP and f.u.reg_read(UC_ARM_REG_SP) == stack and all(f.u.reg_read(r) == v for r, v in guards.items())


def audit(raw):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA:
        raise ValueError('Exact private original-Z7 C3.80 main required')
    checks, observations = [], []

    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good:
            raise AssertionError(name)

    for bank in range(3):
        f = SubmissionFixture(raw)
        descriptor, payload = MEM + 0x2000, MEM + 0x3000
        callback = (0x10354343, 0x1035434d, 0x10354357)[bank]
        f.u.mem_write(descriptor - 16, b'\xa5' * 64)
        f.u.mem_write(STACK, struct.pack('<2I', callback, descriptor))
        result = f.call(BUILDER, 16, bank, 0, payload)
        expected = bytearray(b'\xa5' * 32)
        struct.pack_into('<4I', expected, 12, callback, 0x42060007 + bank * 0x1000, payload, 0)
        check(f'bank{bank}-builder-preserves-caller-stack-and-returns-descriptor', result == descriptor and bytes(f.u.mem_read(STACK, 8)) == struct.pack('<2I', callback, descriptor))
        check(f'bank{bank}-exact-command-payload-callback-and-descriptor-padding', bytes(f.u.mem_read(descriptor - 16, 64)) == b'\xa5' * 16 + bytes(expected) + b'\xa5' * 16)

    # DisplayService handles banks0/2. Bank1's42061007 selects the separate
    # native103490F4 submission path and is not forced through this consumer.
    for output, selector, event_bit, callback in ((1, 0, 0x20, 0x10354343), (4, 1, 0x80, 0x10354357)):
        for enabled in (False, True):
            f = SubmissionFixture(raw)
            src, state = MEM + 0x1000, MEM + 0x4000
            incoming = request(output, int(enabled), 248)
            f.u.mem_write(src, incoming)
            f.write(STATE_POINTER, state)
            f.u.mem_write(state, b'\xc3' * 256)
            f.u.mem_write(0xa180a568, bytes([selector]))
            f.u.mem_write(0xa1d68e54, b'\1')
            f.u.mem_write(STACK - 0x400, b'\xa5' * 0x400)
            guards = enter(f, CALLER, (output, 0, src), STACK)
            label = f'output{output}-enabled{int(enabled)}'
            check(label + '-caller-blocks-at-real-kernel-wait-after-queueing-once', len(f.queued) == 1 and f.wait_pending is not None and f.u.reg_read(UC_ARM_REG_PC) == 0x10036504)
            queued = f.queued[0]
            check(label + '-original-builder-selects-correct-command-and-native-callback', queued['command'] == 0x42060007 + selector * 0x2000 and queued['callback'] == callback and queued['context'] == 0 and f.wait_pending['bits'] == event_bit and f.wait_pending['timeout'] == 0xffffffff)
            frame = bytes(f.u.mem_read(queued['payload'], 100))
            check(label + '-converted-stack-payload-lives-until-completion', queued['payload'] < queued['packet'] < STACK and queued['payload'] + 100 == queued['packet'] and f.read(queued['payload']) == int(enabled))
            context = f.u.context_save()
            consumer_guards = enter(f, 0x10239840, (queued['packet'],), STACK - 0x10000)
            check(label + '-native-consumer-completion-callback-return-on-separate-stack', returned(f, STACK - 0x10000, consumer_guards) and f.u.reg_read(UC_ARM_REG_R0) == 1 and f.native_handler_entries == [queued['packet']] and f.native_completions == [(queued['packet'], 0)])
            check(label + '-exact-payload-publication-and-acknowledgement', bytes(f.u.mem_read(state + 0x28, 100)) == frame and f.read(state + 0x24) == f.read(queued['payload'] + 100) == 1)
            check(label + '-original-completion-callback-sets-matching-event', f.event_operations == [('clear', event_bit), ('wait-blocked', event_bit), ('set', event_bit)])
            f.u.context_restore(context)
            f.u.emu_start(f.u.reg_read(UC_ARM_REG_PC) | 1, STOP, timeout=10000000, count=10000000)
            check(label + '-original-caller-resumes-and-preserves-abi', returned(f, STACK, guards) and f.wait_pending is None and f.u.reg_read(UC_ARM_REG_R0) == 1 and f.event_operations[-1] == ('wait-complete', event_bit))
            check(label + '-original-gui-request-unchanged', bytes(f.u.mem_read(src, 36)) == incoming)
            observations.append(dict(output_flag=output, command=hex(queued['command']), callback=hex(callback), event_bit=event_bit, enabled=enabled))
    return dict(passed=True, checks=checks, observations=observations, stock_main_sha256=STOCK_SHA,
                native_builder_caller_converter_submit_wrappers_consumer_completion_callbacks_execute=True,
                logical_bank_commands=['0x42060007', '0x42061007', '0x42062007'],
                separate_native_consumer_stack=True, native_caller_wait_timeout='0xffffffff', kernel_queue_and_event_services_supplied=True,
                bank1_separate_submission_path_executed=False, physical_scheduler_or_pixels_verified=False,
                frame_producer_bound=False, module_installed=False, physical_camera_or_card_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists():
        p.error('Choose a new private output')
    result = audit(a.stock_main.read_bytes())
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__':
    main()
