"""Trace the existing sound hook through the ORIGINAL Z7 callback consumer.

Unlike verify_sound_shot.py, the callback body is executed, not replaced by a
return stub. Controller notifications and native classification RAM are still
supplied unit inputs. This does not identify those states as real idle/photo
states or establish a valid physical shutter trigger. No firmware is built.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_PC

from verify_sound_shot import ShotFixture, CALLBACK, OBJECT
from verify_sound_playback import Fixture, STATE
from z30_extensions.platform.z7_380 import MAIN_PAYLOAD_SHA256

CONSUMER = 0x1014708C
CAPTURE_STATE = 0xA18B7B90
WORKER_QUEUE = 0x1013C4A2


class NativeConsumerFixture(ShotFixture):
    def __init__(self, *args, **kwargs):
        self.consumer_entries = 0
        self.native_work = []
        self.native_returns = 0
        super().__init__(*args, **kwargs)
        self.u.mem_map(0xA2300000, 0x100000)

    def hook(self, u, address, size, context):
        if address == CALLBACK:
            self.consumer_entries += 1
            # Only replace the trampoline's destination. Execute the original
            # registered callback, retaining its caller's actual LR/stack.
            u.reg_write(UC_ARM_REG_PC, CONSUMER | 1)
        elif address in (0x101641FA, 0x101641DC):
            self.ret(1)  # Native synchronization boundaries are controlled.
        elif address == WORKER_QUEUE:
            callback, packet, size_bytes = (u.reg_read(r) for r in
                (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2))
            self.native_work.append(dict(callback=hex(callback), bytes=size_bytes,
                                         packet=list(self.words(packet, size_bytes // 4))
                                         if packet and size_bytes else []))
            self.ret(1)  # Record scheduling; do not run another firmware task.
        else:
            if address == 0x100726AE:
                self.native_returns += 1
            super().hook(u, address, size, context)

    def configure_classification(self, state_1a, state_1f):
        # These are deliberately numeric scenarios, not inferred mode names.
        self.u.mem_write(CAPTURE_STATE + 5, b'\0')
        self.u.mem_write(CAPTURE_STATE + 0x1F, bytes([state_1f]))
        self.word(CAPTURE_STATE + 0x18, 0)
        # +0x1A aliases the high half of +0x18; restore it after clearing word.
        self.u.mem_write(CAPTURE_STATE + 0x1A, bytes([state_1a]))

    def snapshot(self):
        return dict(consumer_entries=self.consumer_entries,
                    native_work=self.native_work,
                    native_return_visits=self.native_returns,
                    custom_audio_requests=len(self.jobs),
                    custom_status=self.words(STATE + 116, 1)[0])


class ReleaseRequestFixture(Fixture):
    """Execute the stock AutoRelease request API and its zero-count worker.

    Validation helpers are supplied explicitly. A release-request notification
    does not by itself establish that a sensor exposure happened.
    """
    CALLBACK = 0x500FF200
    PACKET = 0x50004000

    def __init__(self, *args, **kwargs):
        self.scheduled, self.notifications, self.release_requests = [], [], []
        super().__init__(*args, **kwargs)
        self.u.mem_map(0xA2300000, 0x100000)

    def hook(self, u, address, size, context):
        r0, r1, r2 = (u.reg_read(r) for r in
            (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2))
        if address == 0x1005F7FC:
            self.scheduled.append(dict(worker=hex(r0), bytes=r2,
                                       packet=list(self.words(r1, r2 // 4))))
            self.ret(1)
        elif address == self.CALLBACK:
            self.notifications.append(dict(event=hex(r0), packet=list(self.words(r1, 2))))
            self.ret(1)
        elif address in (0x100F6FFA, 0x102012F0, 0x100624F4, 0x1006253E):
            self.ret(0)  # Controlled validation/context helpers, not sensor state.
        elif address == 0x100F6F88:
            self.ret(0x1F)  # Select the worker's main validation branch.
        elif address == 0x10061FAA:
            self.release_requests.append(list(self.words(r0, 2)))
            self.ret(1)  # Record release control admission, never drive hardware.
        else:
            super().hook(u, address, size, context)


def trace(stock, image, report):
    if hashlib.sha256(stock).hexdigest() != MAIN_PAYLOAD_SHA256:
        raise ValueError('Requires the original Z7 C 3.80 MAIN payload')
    checks, scenarios = [], []
    registered = struct.unpack_from('<I', stock, 0x10147E20 - 0x10020000)[0]
    checks.append(dict(name='stock-registration-literal-identifies-consumer',
                       passed=registered == CONSUMER | 1))
    setter = NativeConsumerFixture(stock, stock, report)
    setter.word(OBJECT + 0x44, 0)
    setter.call(0x100752DE, (registered,))
    checks.append(dict(name='original-setter-populates-dispatcher-callback-slot',
                       passed=setter.words(OBJECT + 0x44, 1)[0] == registered))
    for state_1a, state_1f in ((0, 0), (1, 0), (3, 0), (0, 2), (1, 2), (3, 2)):
        runs = []
        for payload in (stock, image):
            fixture = NativeConsumerFixture(stock, payload, report, enabled=1)
            fixture.configure_classification(state_1a, state_1f)
            result = fixture.run_path('dispatch0')
            if result['error'] or not result['reached']:
                raise AssertionError(result)
            runs.append(fixture.snapshot())
        before, after = runs
        name = f'state1a-{state_1a}-state1f-{state_1f}'
        scenarios.append(dict(name=name, stock=before, patched=after))
        checks.append(dict(name=name + '-original-consumer-executes-and-returns',
                           passed=before['consumer_entries'] == after['consumer_entries'] == 1
                           and before['native_return_visits'] == after['native_return_visits'] == 1))
        checks.append(dict(name=name + '-native-scheduling-preserved',
                           passed=before['native_work'] == after['native_work']))
        checks.append(dict(name=name + '-patch-queues-regardless-of-native-classification',
                           passed=before['custom_audio_requests'] == 0
                           and after['custom_audio_requests'] == 1))
        if state_1f == 0 and state_1a in (1, 3):
            checks.append(dict(name=name + '-native-rejects-but-patch-queues',
                               passed=not after['native_work'] and after['custom_audio_requests'] == 1))
    release = ReleaseRequestFixture(stock, stock, report)
    for offset in (0, 4, 8):
        release.word(release.PACKET + offset, 0)
    request_return = release.call(0x10203D40, (release.PACKET, release.CALLBACK | 1))
    release.call(0x102029BC, (release.PACKET,))
    release_result = dict(request_return=request_return, scheduled=release.scheduled,
                          notifications=release.notifications,
                          release_control_requests=release.release_requests)
    checks.append(dict(name='stock-zero-count-release-request-schedules-worker',
                       passed=request_return == 0 and len(release.scheduled) == 1
                       and release.scheduled[0]['worker'] == '0x10202a79'))
    checks.append(dict(name='stock-zero-count-notification-without-release-control',
                       passed=release.notifications == [dict(event='0x4100034', packet=[0, 0])]
                       and not release.release_requests))
    return dict(
        schema=1, audit_only=True, evidence_checks_passed=all(c['passed'] for c in checks),
        candidate_cleared=False, main_sha256=hashlib.sha256(image).hexdigest(),
        registered_consumer=hex(registered),
        scenarios=scenarios, release_request_probe=release_result, checks=checks,
        scope='Original Z7 dispatcher and registered consumer 0x1014708C execute in stock and existing patched MAIN images; custom admission and original property getter execute.',
        limitations=[
            'Numeric classification scenarios supplied in RAM; their runtime mode meanings are not established.',
            'Native locks, worker scheduling, allocator, audio queue, controller helper and semaphore remain controlled boundaries.',
            'No photo/sensor transaction or live-view frame cadence is generated or measured.',
            'Release API/zero-count worker use controlled context/validation helpers; request notification is not per-photo exposure evidence.',
            'Passing evidence checks confirm the admission defect, not candidate safety or a corrected shutter trigger.',
        ])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = trace(args.stock.read_bytes(), args.image.read_bytes(),
                   json.loads(args.report.read_text(encoding='utf-8')))
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    raise SystemExit(not result['evidence_checks_passed'])
