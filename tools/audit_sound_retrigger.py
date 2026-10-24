"""Audit an EXISTING private image for notification-only sound retriggering.

This probe deliberately supplies callback notifications without an independently
identified photo transaction. It is not a live-view/sensor emulator and cannot
identify the real callback cadence. The owner's no-photo playback report supplies
the hardware failure evidence; this probe exposes admission/restart mechanics.
Exit 1 means the required notification-only rejection is absent, not a fixed image.
No firmware is generated or staged.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from verify_sound_shot import ShotFixture
from verify_sound_playback import STATE, BUSY, ENABLED, PENDING
from z30_extensions.features.sound_layout_z7 import SWITCH_INDEX, SWITCH_OFFSET


class AuditFixture(ShotFixture):
    def __init__(self, *args, **kwargs):
        self.stop_requests = 0
        super().__init__(*args, **kwargs)

    def hook(self, u, address, size, context):
        if address == 0x101BFC1C:
            self.stop_requests += 1
            self.ret(1)  # Controlled stop acceptance, no device/driver execution.
        elif address == 0x10404C42:
            self.ret(0)  # Controlled native page navigation on Enabled OFF.
        else:
            super().hook(u, address, size, context)

    def notification(self):
        result = self.run_path('dispatch0')
        if result['error'] or not result['reached']:
            raise AssertionError(result)

    def disable(self):
        page = STATE + SWITCH_OFFSET
        self.word(page, SWITCH_INDEX << 16)
        self.u.mem_write(page + 22, struct.pack('<2H', 0, 0))
        self.call(self.f['action'], (page, 0x239))


def audit(stock, image, report):
    sequential = AuditFixture(stock, image, report, enabled=1)
    for _ in range(3):
        sequential.notification()
        sequential.completion(0x04180022, 0)
        sequential.completion(0x04180023, 0)

    overlap = AuditFixture(stock, image, report, enabled=1)
    overlap.notification()
    overlap.completion(0x04180022, 0)
    overlap.notification()
    pending = overlap.words(STATE + PENDING, 1)[0]
    overlap.call(overlap.f['labels'])
    busy_heading = overlap.labels.get(40)
    before_finish = len(overlap.jobs)
    overlap.completion(0x04180023, 0)
    after_finish = len(overlap.jobs)

    # Exercise the compiled UI OFF action while another notification is pending.
    overlap.completion(0x04180022, 0)
    overlap.notification()
    overlap.disable()
    disabled = overlap.words(STATE + ENABLED, 1)[0] == 0
    cleared = overlap.words(STATE + PENDING, 1)[0] == 0
    overlap.completion(0x04180023, 0)
    for _ in range(3):
        overlap.notification()
    no_restart_after_off = len(overlap.jobs) == after_finish
    idle_after_finish = overlap.words(STATE + BUSY, 1)[0] == 0

    disabled_initially = AuditFixture(stock, image, report, enabled=0)
    for _ in range(3):
        disabled_initially.notification()

    observations = dict(
        supplied_photo_transactions=0,
        sequential_notifications=3,
        sequential_queue_requests=len(sequential.jobs),
        overlap_pending=pending,
        overlap_heading=busy_heading,
        overlap_queue_requests_before_finish=before_finish,
        overlap_queue_requests_after_finish=after_finish,
        controlled_stop_requests=overlap.stop_requests,
        compiled_off_clears_enabled=disabled,
        compiled_off_clears_pending=cleared,
        no_new_queue_after_off=no_restart_after_off,
        idle_after_synthetic_finish=idle_after_finish,
        initially_disabled_queue_requests=len(disabled_initially.jobs),
    )
    requirements = [
        dict(name='notifications-without-independent-photo-must-not-queue',
             passed=len(sequential.jobs) == 0),
        dict(name='notification-overlap-must-not-restart-without-photo',
             passed=after_finish == before_finish),
        dict(name='compiled-off-clears-pending-and-blocks-future-queue',
             passed=disabled and cleared and no_restart_after_off and idle_after_finish),
        dict(name='initially-off-blocks-notifications', passed=not disabled_initially.jobs),
    ]
    return dict(
        schema=1,
        audit_only=True,
        passed=all(item['passed'] for item in requirements),
        main_sha256=hashlib.sha256(image).hexdigest(),
        observations=observations,
        requirements=requirements,
        scope='Existing compiled native dispatcher, custom trigger/completion, UI OFF action, labels and original property getter.',
        limitations=[
            'Synthetic controller notifications; no independently identified shutter transaction, real live-view frames or sensor exposure.',
            'Started/finished packets and successful stop result are supplied unit inputs, not observed hardware completion behavior.',
            'Property RAM, native callback, allocator, queue, controller helper/semaphore and UI boundaries are controlled by the fixture.',
            'OFF blocks future admission in this sequence; it does not synchronously cancel the currently playing audio.',
            'No installation acceptance, real timing/reentrancy, physical audio or recovery assurance.',
        ],
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.stock.read_bytes(), args.image.read_bytes(),
                   json.loads(args.report.read_text(encoding='utf-8')))
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    raise SystemExit(not result['passed'])
