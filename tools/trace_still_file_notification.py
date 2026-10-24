"""Trace a stock Z7 still-file finalization notification without file/device I/O.

This is a backward-tracing anchor, NOT a proposed shutter hook. A finalized file
is not necessarily one new exposure; multi-format output, replay, cardless use,
burst timing and failure behavior need independent evidence. No firmware is built.
"""
import argparse
import hashlib
import json
from pathlib import Path

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1

from verify_sound_playback import Fixture, STACK
from z30_extensions.platform.z7_380 import MAIN_PAYLOAD_SHA256

SUCCESS = 0x04390080


class StillFileFixture(Fixture):
    CALLBACK = 0x500FF300

    def __init__(self, *args, finalize_result=SUCCESS, flush_result=SUCCESS, **kwargs):
        self.finalize_result = finalize_result
        self.flush_result = flush_result
        self.notifications, self.file_boundaries = [], []
        super().__init__(*args, **kwargs)

    def hook(self, u, address, size, context):
        if address == self.CALLBACK:
            event = u.reg_read(UC_ARM_REG_R0)
            packet = u.reg_read(UC_ARM_REG_R1)
            self.notifications.append(dict(event=hex(event), packet=list(self.words(packet, 3))))
            self.ret(1)
        elif address in (0x103F7B98, 0x103F7E32, 0x103F7A4C, 0x1031F0EE, 0x103F7EFC):
            self.file_boundaries.append(hex(address))
            result = {0x103F7E32: self.finalize_result,
                      0x103F7EFC: self.flush_result}.get(address, 0)
            self.ret(result)  # No real file/slot operations are executed.
        else:
            super().hook(u, address, size, context)


def trace(stock, report):
    if hashlib.sha256(stock).hexdigest() != MAIN_PAYLOAD_SHA256:
        raise ValueError('Requires the original Z7 C 3.80 MAIN payload')
    checks, scenarios = [], []
    for name, kind, prior_result, finalize_result, flush_result in (
        ('kind0-success', 0, 0, SUCCESS, SUCCESS),
        ('kind1-success', 1, 0, SUCCESS, SUCCESS),
        ('kind3-success', 3, 0, SUCCESS, SUCCESS),
        ('prior-failure', 0, 3, SUCCESS, SUCCESS),
        ('finalize-failure', 0, 0, 0, SUCCESS),
        ('flush-failure', 0, 0, SUCCESS, 0),
    ):
        f = StillFileFixture(stock, stock, report, finalize_result=finalize_result,
                             flush_result=flush_result)
        # Execute the original callback-registration wrapper and packed-ID helper.
        registered = f.call(0x1035FF54, (f.CALLBACK | 1,))
        record = f.call(0x10309884, (0, 100, 1, kind))
        f.word(STACK, prior_result)  # Fifth argument at the original entry SP.
        result = f.call(0x1026FADC, (0x50060000, record, 4096, 0))
        should_notify = prior_result == 0 and finalize_result == flush_result == SUCCESS
        expected = [dict(event='0x41e0002', packet=[record, int(kind != 3), 0])] if should_notify else []
        checks.append(dict(name=name + '-original-registered-dispatch-result',
                           passed=registered == 0 and f.notifications == expected))
        checks.append(dict(name=name + '-return-matches-notification-admission',
                           passed=result == (0 if should_notify else 3)))
        scenarios.append(dict(name=name, record_id=hex(record), return_value=result,
                              notifications=f.notifications, controlled_file_boundaries=f.file_boundaries))

    f = StillFileFixture(stock, stock, report)
    records = [f.call(0x10309884, fields) for fields in
               ((0, 100, 1, 0), (0, 100, 1, 1), (0, 100, 2, 0), (1, 100, 1, 0))]
    equivalence = [f.call(0x103099A0, (records[0], other)) for other in records[1:]]
    checks.append(dict(name='native-record-comparison-ignores-kind-but-distinguishes-number-and-slot',
                       passed=equivalence == [1, 0, 0]))
    checks.append(dict(name='native-record-field-getters-match-constructor',
                       passed=[f.call(address, (records[1],)) for address in
                               (0x103098B6, 0x103098BC, 0x103098C8, 0x103098CE)] == [0, 100, 1, 1]))
    return dict(
        schema=1, audit_only=True, stock_main_sha256=hashlib.sha256(stock).hexdigest(),
        evidence_checks_passed=all(c['passed'] for c in checks), checks=checks,
        scenarios=scenarios,
        native_record_comparison=dict(input_fields=['slot', 'group', 'number', 'kind'],
                                      same_group_number_different_kind=equivalence[0],
                                      different_number=equivalence[1], different_slot=equivalence[2]),
        candidate_cleared=False, per_photo_trigger_identified=False,
        scope='Original stock finalization wrapper, callback registration/dispatch, packed record constructor/getters/comparison execute in Unicorn.',
        limitations=[
            'File handles, operation results and record fields are supplied unit inputs; file/device operations are controlled boundaries.',
            'Numeric kind values are not identified here as JPEG/NEF or other formats.',
            'File-finalization notification can follow the exposure; actual latency/cadence and per-photo cardinality are unmeasured.',
            'No proof of correct behavior for multi-format/duplicate/replayed files, bursts, cancellation, cardless capture or card removal.',
            'No sensor exposure, physical audio, installation acceptance or recovery evidence; no new firmware or hook generated.',
        ])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = trace(args.stock.read_bytes(), json.loads(args.report.read_text(encoding='utf-8')))
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    raise SystemExit(not result['evidence_checks_passed'])
