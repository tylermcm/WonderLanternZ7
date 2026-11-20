"""Execute the compiled resident highlight owner with original native transport.

SPDX-License-Identifier: MIT. Consumer bracketing/context epochs are supplied
explicitly, not installed hooks. Kernel queue/event state and palette supplied.
Native conversion, builder, queue wrappers, dispatch, copy and completion execute.
"""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_R0
from audit_splash_image import MEM, STACK, STOCK_SHA
from audit_z7_highlight_submission import SubmissionFixture, enter, returned
from audit_z7_highlight_converter import request
from audit_z7_display_parameters import COMPLETION, STATE_POINTER
from build_z7_module import ROOT, HEADER, build
from build_z7_module_host import ZIG

CODE, GUI, STATE = MEM + 0x20000, MEM + 0x1000, MEM + 0x4000


class OwnerFixture(SubmissionFixture):
    def __init__(self, raw, packet, metadata, selector=0, queue_result=0):
        super().__init__(raw)
        image = bytearray(packet[HEADER:HEADER + metadata['image_bytes']])
        for off in metadata['relocations']:
            struct.pack_into('<I', image, off, struct.unpack_from('<I', image, off)[0] + CODE)
        self.u.mem_write(CODE, bytes(image) + bytes(metadata['bss_bytes']))
        self.symbols = metadata['symbols']
        self.owner = CODE + self.symbols['z7_hr']
        self.payload = self.owner + 28
        self.pause_send = False
        self.queue_result = queue_result
        self.write(STATE_POINTER, STATE)
        self.u.mem_write(STATE, b'\xc3' * 256)
        self.u.mem_write(0xa180a568, bytes([selector]))
        self.u.mem_write(0xa1d68e54, b'\1')

    def hook(self, u, address, size, context):
        if address == 0x100363cc and self.pause_send:
            u.emu_stop()
            return
        super().hook(u, address, size, context)
        if address == 0x100363cc:
            self.ret(self.queue_result)

    def call_owner(self, name, *args):
        return self.call(CODE + self.symbols['z7_hr_' + name], *args)

    def consume(self, epoch):
        action = self.call_owner('begin', self.owner, epoch)
        if action == 1:
            result = self.call(0x10239840, self.owner)
        elif action == 2:
            result = self.call(COMPLETION, self.owner, 0)
        else:
            raise AssertionError('Expected current or cancelled owned consumption')
        return action, result


def audit(raw, packet, metadata):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA:
        raise ValueError('Exact original-Z7 C3.80 stock main required')
    checks = []

    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good:
            raise AssertionError(name)

    for output, selector in ((1, 0), (4, 1)):
        for enabled in (0, 1):
            f = OwnerFixture(raw, packet, metadata, selector)
            f.u.mem_write(GUI, request(output, enabled, 248))
            label = f'output{output}-enabled{enabled}'
            check(label + '-owned-submit-returns-without-native-event-wait', f.call_owner('submit', GUI, output, 17) == 1 and
                  len(f.queued) == 1 and not f.event_operations)
            payload = bytes(f.u.mem_read(f.payload, 104))
            descriptor = bytes(f.u.mem_read(f.owner, 28))
            check(label + '-separate-zero-ack-payload-and-owned-context', f.queued[0]['payload'] == f.payload and
                  f.queued[0]['packet'] == f.owner and f.queued[0]['context'] == f.owner and f.read(f.payload + 100) == 0 and
                  f.read(f.payload) == enabled and (enabled or payload == bytes(104)))
            check(label + '-busy-rejects-resubmission-without-mutation', f.call_owner('submit', GUI, output, 18) == 0 and
                  bytes(f.u.mem_read(f.payload, 104)) == payload and bytes(f.u.mem_read(f.owner, 28)) == descriptor)
            check(label + '-foreign-packet-delegates-without-claiming', f.call_owner('begin', GUI, 17) == 0)
            check(label + '-original-consumer-applies-and-calls-owned-completion', f.consume(17) == (1, 1) and
                  f.native_completions == [(f.owner, 0)] and bytes(f.u.mem_read(STATE + 0x28, 100)) == payload[:100] and
                  f.read(f.payload + 100) == 1)
            check(label + '-callback-alone-cannot-release-or-reenter', f.call_owner('reap') == 0 and
                  f.call_owner('begin', f.owner, 17) == 3 and f.call_owner('submit', GUI, output, 18) == 0)
            f.call_owner('end')
            check(label + '-dispatcher-return-permits-single-acknowledged-reap', f.call_owner('reap') == 2 and f.call_owner('reap') == 0)
            check(label + '-next-request-clears-old-ack', f.call_owner('submit', GUI, output, 18) == 1 and f.read(f.payload + 100) == 0)
            del f
            gc.collect()

        f = OwnerFixture(raw, packet, metadata, selector)
        f.u.mem_write(GUI, request(output, 1, 248))
        f.call_owner('submit', GUI, output, 17)
        before = bytes(f.u.mem_read(STATE, 256))
        check(f'output{output}-changed-context-cancels-through-original-completion', f.consume(18)[0] == 2 and
              not f.native_handler_entries and f.native_completions == [(f.owner, 0)] and
              bytes(f.u.mem_read(STATE, 256)) == before and f.read(f.payload + 100) == 0)
        f.call_owner('end')
        check(f'output{output}-cancelled-reap-distinguished-from-application', f.call_owner('reap') == 1)
        del f
        gc.collect()

    for queue_result in (0, 0x80000002):
        f = OwnerFixture(raw, packet, metadata, queue_result=queue_result)
        f.u.mem_write(GUI, request(1, 1, 248))
        f.call_owner('submit', GUI, 1, 17)
        check(f'queue-result{queue_result:x}-no-completion-never-releases-storage', all(f.call_owner('reap') == 0 for _ in range(8)) and
              f.call_owner('submit', GUI, 1, 18) == 0 and len(f.queued) == 1)
        check(f'queue-result{queue_result:x}-late-consumer-can-still-apply-retained-request', f.consume(17) == (1, 1))
        f.call_owner('end')
        check(f'queue-result{queue_result:x}-only-observed-consumption-permits-release', f.call_owner('reap') == 2)
        del f
        gc.collect()

    f = OwnerFixture(raw, packet, metadata)
    f.u.mem_write(GUI, request(1, 1, 248))
    f.call_owner('submit', GUI, 1, 17)
    callback = f.read(f.owner + 12)
    f.call(callback, 0x42062007, f.owner)  # Wrong command, before consumption.
    f.call_owner('end')
    check('foreign-command-completion-cannot-release-pending-storage', f.call_owner('reap') == 0)
    check('owned-packet-claims-once', f.call_owner('begin', f.owner, 17) == 1)
    f.call_owner('end')
    check('consumer-return-without-completion-remains-parked', f.call_owner('reap') == 0)
    f.call(callback, 0x42062007, f.owner)
    f.call_owner('end')
    check('foreign-command-completion-cannot-release-consuming-storage', f.call_owner('reap') == 0)
    f.call(COMPLETION, f.owner, 0)
    f.call_owner('end')
    check('explicit-original-cancel-completion-retires-without-false-ack', f.call_owner('reap') == 1)
    check('idle-owned-address-is-not-an-ordinary-packet', f.call_owner('begin', f.owner, 17) == 3)
    del f
    gc.collect()

    for field in (12, 16, 20, 24):
        f = OwnerFixture(raw, packet, metadata)
        f.u.mem_write(GUI, request(1, 1, 248))
        f.call_owner('submit', GUI, 1, 17)
        f.write(f.owner + field, f.read(f.owner + field) ^ 4)
        check(f'corrupt-owned-descriptor-field{field}-does-not-delegate-or-release',
              f.call_owner('begin', f.owner, 17) == 3 and f.call_owner('reap') == 0 and not f.native_completions)
        del f
        gc.collect()

    f = OwnerFixture(raw, packet, metadata)
    f.u.mem_write(GUI, request(1, 1, 248))
    f.pause_send = True
    guards = enter(f, CODE + f.symbols['z7_hr_submit'], (GUI, 1, 17), STACK)
    check('early-consumer-submitter-paused-at-kernel-queue', f.u.reg_read(UC_ARM_REG_PC) == 0x100363cc)
    context = f.u.context_save()
    # Independent consumer stack: never overwrite the suspended submitter stack.
    def other(name, *args):
        saved = enter(f, CODE + f.symbols['z7_hr_' + name], args, STACK - 0x10000)
        if not returned(f, STACK - 0x10000, saved):
            raise AssertionError('Consumer owner ABI not preserved')
        return f.u.reg_read(UC_ARM_REG_R0)
    check('early-consumer-claims-published-owned-request', other('begin', f.owner, 17) == 1)
    saved = enter(f, 0x10239840, (f.owner,), STACK - 0x10000)
    check('early-consumer-original-dispatch-returns-and-acks', returned(f, STACK - 0x10000, saved) and f.read(f.payload + 100) == 1)
    other('end')
    check('early-consumer-retired-storage-still-waits-for-submit-return', other('reap') == 0)
    f.u.context_restore(context)
    f.pause_send = False
    from audit_splash_image import STOP
    f.u.emu_start(f.u.reg_read(UC_ARM_REG_PC) | 1, STOP, timeout=10000000, count=10000000)
    check('early-submitter-resumes-with-original-stack-and-registers', returned(f, STACK, guards) and f.u.reg_read(UC_ARM_REG_R0) == 1)
    check('early-completion-reaps-only-after-both-native-calls-return', f.call_owner('reap') == 2)
    check('invalid-output-and-null-input-do-not-submit', f.call_owner('submit', GUI, 2, 18) == 0 and
          f.call_owner('submit', 0, 1, 18) == 0 and len(f.queued) == 1)
    del f
    gc.collect()
    for output, selector in ((1, 0), (4, 1)):
        for enabled in (0, 1):
            f = OwnerFixture(raw, packet, metadata, selector)
            f.u.mem_write(GUI, request(output, enabled, 213))
            label = f'deferred-output{output}-enabled{enabled}'
            check(label + '-queues-zero-payload-without-converter-or-palette-access',
                  f.call_owner('defer', output, 17) == 1 and len(f.queued) == 1 and
                  bytes(f.u.mem_read(f.payload, 104)) == bytes(104) and not f.palette_gets)
            check(label + '-cannot-convert-unclaimed-queued-storage',
                  f.call_owner('convert', GUI, 17) == 0 and bytes(f.u.mem_read(f.payload, 104)) == bytes(104))
            check(label + '-consumer-claims-current-request', f.call_owner('begin', f.owner, 17) == 1)
            # Palette changes AFTER queueing. Conversion must use this new
            # native pointer/content, not a worker-time converted packet.
            f.write(0xa1f18fac, MEM + 0x9000)
            f.u.mem_write(MEM + 0x9000, struct.pack('<256I', *[((255 - i) << 24) | i for i in range(256)]))
            f.u.mem_write(MEM + 0xa000, bytes(100))
            f.call(0x1034fe22, MEM + 0xa000, GUI, output)
            expected = bytes(f.u.mem_read(MEM + 0xa000, 100))
            check(label + '-claimed-conversion-uses-current-native-palette-and-zero-padding',
                  f.call_owner('convert', GUI, 17) == 1 and bytes(f.u.mem_read(f.payload, 100)) == expected and f.read(f.payload + 100) == 0)
            check(label + '-stale-epoch-cannot-reconvert-claimed-storage',
                  f.call_owner('convert', GUI, 18) == 0 and bytes(f.u.mem_read(f.payload, 100)) == expected)
            check(label + '-original-consumer-copies-and-completes-converted-owned-payload',
                  f.call(0x10239840, f.owner) == 1 and f.read(f.payload + 100) == 1 and
                  bytes(f.u.mem_read(STATE + 0x28, 100)) == expected)
            completed = bytes(f.u.mem_read(f.payload, 104))
            check(label + '-completed-payload-is-no-longer-convertible',
                  f.call_owner('convert', GUI, 17) == 0 and bytes(f.u.mem_read(f.payload, 104)) == completed)
            f.call_owner('end')
            check(label + '-reaps-only-after-native-return', f.call_owner('reap') == 2)
            check(label + '-next-deferred-request-clears-prior-ack',
                  f.call_owner('defer', output, 18) == 1 and bytes(f.u.mem_read(f.payload, 104)) == bytes(104))
            check(label + '-changed-epoch-cancels-before-conversion',
                  f.call_owner('begin', f.owner, 19) == 2 and f.call_owner('convert', GUI, 19) == 0)
            check(label + '-cancelled-claim-cannot-be-revived-with-its-old-epoch',
                  f.call_owner('convert', GUI, 18) == 0 and bytes(f.u.mem_read(f.payload, 104)) == bytes(104))
            f.call(COMPLETION, f.owner, 0)
            f.call_owner('end')
            check(label + '-native-cancellation-reaps-without-false-application', f.call_owner('reap') == 1)
            del f
            gc.collect()
    return dict(passed=True, checks=checks, stock_main_sha256=STOCK_SHA,
                compiled_owner_native_converter_builder_submit_consumer_completion_execute=True,
                deferred_submission_and_claimed_dispatch_time_conversion_verified=True,
                kernel_queue_palette_service_and_consumer_bracketing_supplied=True,
                queue_failure_semantics_proven=False, lost_request_timeout_release=False,
                hook_installed=False, preference_connected=False, actual_warning_pixels=False,
                physical_camera_or_card_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists():
        p.error('Choose a new private output directory')
    out.mkdir(parents=True)
    packet, metadata = build(ROOT / 'z7-native-modules/examples/highlight_request_probe.c', zig=ZIG)
    (out / 'probe.BIN').write_bytes(packet)
    (out / 'probe.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8', newline='\n')
    result = audit(a.stock_main.read_bytes(), packet, metadata)
    result['probe_sha256'] = hashlib.sha256(packet).hexdigest()
    result['source_sha256'] = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
        'z7-native-modules/plugins/highlight_request.h',
        'z7-native-modules/examples/highlight_request_probe.c',
        'tools/audit_z7_highlight_request.py')}
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']), probe_sha256=result['probe_sha256'])))


if __name__ == '__main__':
    main()
