"""Test new layout journals with the earlier owner-tested three-choice image.

Native settings instructions run with the existing supplied OS/flash/UI
boundaries. This verifies selected loader/setting compatibility, not physical
rollback, updater programming, shutdown timing or emergency camera recovery.
"""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import struct

from audit_grid_native_value import NativeValueGrid
from trace_settings_storage import GRID_VALUE, MEM
from build_grid_firmware import validate_candidate


def audit(image, report, previous, previous_report):
    checks = []
    new_funcs = {k: int(v, 16) for k, v in report['features']['grid']['functions'].items()}
    old_funcs = {k: int(v, 16) for k, v in previous_report['features']['grid']['functions'].items()}
    def check(name, passed):
        checks.append(dict(name=name, passed=bool(passed)))
    for choice, value in (('golden', 3), ('center', 4), ('dense', 5)):
        f = NativeValueGrid(image)
        f.initialize(); f.call(new_funcs[choice])
        payloads = f.payloads()
        f.save_worker()
        banks = f.journal()
        del f
        gc.collect()
        f = NativeValueGrid(previous, banks)
        f.initialize(); f.call(0x10117594)
        check(choice + '-previous-native-loader-restores-value-and-all-records',
              f.word(GRID_VALUE) == value and f.payloads() == payloads)
        check(choice + '-previous-startup-does-not-write-storage', not f.operations)
        check(choice + '-previous-native-grid-visibility-is-off', f.call(0x1037723E) == 0)
        f.u.mem_write(0xA1836F8C + 36, struct.pack('<I', MEM + 0x10000))
        f.call(old_funcs['enter'], 0xA1836F8C)
        check(choice + '-previous-menu-focuses-off', f.marks == [(0x1902, 1)])
        f.call(old_funcs['thirds']); f.save_worker()
        restored = f.journal()
        del f
        gc.collect()
        f = NativeValueGrid(previous, restored)
        f.initialize(); f.call(0x10117594)
        check(choice + '-previous-can-save-and-reload-3x3-again',
              f.word(GRID_VALUE) == 2 and f.call(0x1037723E) == 1)
        check(choice + '-previous-preserves-unrelated-records-after-reselection',
              all(p == payloads[i] for i, p in enumerate(f.payloads()) if i != 49))
        del f
        gc.collect()
    return dict(schema=1, scope=__doc__.strip(),
        main_payload_sha256=hashlib.sha256(image).hexdigest(),
        previous_main_payload_sha256=hashlib.sha256(previous).hexdigest(),
        checks=checks, all_passed=all(c['passed'] for c in checks),
        camera_access=False, card_access=False, physical_rollback_verified=False,
        emergency_recovery_verified=False)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--previous-build', type=Path, required=True)
    p.add_argument('--container', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    reports = []
    images = []
    for directory, preset in ((args.build, 'grid-layouts-emulator-only'),
                              (args.previous_build, 'grid-native-value-emulator-only')):
        main, metadata = directory/'grid.emulator.main.bin', directory/'grid.emulator.json'
        validate_candidate(main, metadata, args.container)
        report = json.loads(metadata.read_text())
        if report['preset'] != preset:
            p.error('Wrong candidate or previous-build identity')
        reports.append(report); images.append(main.read_bytes())
    result = audit(images[0], reports[0], images[1], reports[1])
    args.output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(checks=len(result['checks']), all_passed=result['all_passed'])))
    raise SystemExit(not result['all_passed'])
