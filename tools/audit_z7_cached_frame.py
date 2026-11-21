"""Execute cached primary metadata/state filtering and native driver effects.

SPDX-License-Identifier: MIT. Kernel/FS/UI/surfaces/colors/native descriptors,
MMIO storage and explicit scheduling supplied. No lane/fence/allocation proof.
"""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import struct

from audit_splash_image import MEM, STOCK_SHA
from audit_z7_parameters import ParameterHostFixture, NATIVE
from audit_z7_highlight_host import observed_call
from audit_z7_highlight_cleanup import CleanupFixture
from audit_z7_frame_permission import FRAME
from audit_z7_highlight_frame_gate import SOURCE_APPLY, STATE as DISPLAY_STATE
from audit_z7_module_host import HostFixture
from build_z7_module import ROOT, build
from build_z7_module_host import STATE, CURSOR, ZIG

CACHED = 0x1023d794


def audit(raw, host, packet, module, old_raw, old_host, old_packet, old_module, probe, metadata, failed, failed_metadata):
    checks = []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    f = ParameterHostFixture(raw, host, probe, metadata)
    f.write(STATE - 4, 0xc3c3c3c3); f.write(STATE + 304, 0xc3c3c3c3)
    check('api60-cold-reserves320-for304-preserving-neighbors-and-every-prefix-guard',
          f.call(0x101e3d94) == STATE and f.read(CURSOR) == STATE + 320 and
          all(f.read(STATE + o) == 0xa5a5a5a5 for o in (240, 244, 248, 252, 264, 268, 280, 284, 296, 300)) and
          f.read(STATE - 4) == f.read(STATE + 304) == 0xc3c3c3c3)
    check('api60-cold-preserves-native-continuation-and-allocator-alignment',
          f.heap_observation == dict(r0=STATE, r1=CURSOR, r2=0x22334455, r3=0x66778899, flags=0xf8000000) and
          [f.call(0x101e3dac, n) for n in (1, 63, 64, 65)] == [STATE + n for n in (320, 384, 448, 512)])
    del f; gc.collect()
    f = ParameterHostFixture(raw, host, probe, metadata)
    check('cached-registration-rejects-prerequisite-null-even-data-foreign-duplicate',
          f.load() == 8 and f.read(f.address('z7_cf_mask')) == 127)
    check('cached-registration-is-init-only', f.call(f.address('z7_cf_late')) == 0)
    address = host['symbols']['z7_cached_frame_permission']
    def calls(): return f.read(f.address('z7_cf_calls'))
    for fields in (0, FRAME + 4):
        for native in (0, 1):
            for decision in (0, 1, 2, 3):
                f.write(f.address('z7_cf_decision'), decision); before = calls()
                check(f'fields{fields:x}-native{native}-decision{decision}-contract',
                      f.call(address, fields, native) == (1 if decision == 1 else 0 if decision == 2 else native) and
                      calls() == before + 1 and f.read(f.address('z7_cf_fields')) == fields and f.read(f.address('z7_cf_native')) == native)
    for name, fields, native in (('unaligned', FRAME + 5, 1), ('outside-camera', MEM, 1),
                                  ('short-range', 0xc0000000 - 0x30, 1), ('native-inhibit', FRAME + 4, 2)):
        before = calls()
        check(name + '-delegates-without-module-entry', f.call(address, fields, native) == native and calls() == before)
    for off in (264, 268, 280, 284, 296, 300):
        f.write(STATE + off, 0); before = calls()
        check(f'guard{off}-delegates', f.call(address, 0, 1) == 1 and calls() == before)
        f.write(STATE + off, 0xa5a5a5a5)
    f.write(STATE + 292, 1); before = calls()
    check('cached-callback-reentry-delegates', f.call(address, FRAME + 4, 1) == 1 and calls() == before)
    f.write(STATE + 292, 0)
    original_callback = f.read(STATE + 288)
    for pointer in (original_callback & ~1, 0x10239841):
        f.write(STATE + 288, pointer); before = calls()
        check(f'corrupted-callback{pointer:x}-delegates', f.call(address, 0, 1) == 1 and calls() == before)
    f.write(STATE + 288, original_callback)
    f.write(f.address('z7_cf_decision'), 0)
    f.write(DISPLAY_STATE + 0x28, 0)  # Disable plane for native fallback comparison.
    for fields in (0, FRAME + 4):
        for flags in (0, 0x58000000, 0xa0000000):
            state = bytes(f.u.mem_read(DISPLAY_STATE, 0x2000))
            globals_ = bytes(f.u.mem_read(0xa1d5f500, 0x100))
            f.write(STATE + 288, 0)
            expected = observed_call(f, CACHED, (fields, 1), flags)
            f.u.mem_write(DISPLAY_STATE, state); f.u.mem_write(0xa1d5f500, globals_)
            f.write(STATE + 288, original_callback)
            actual = observed_call(f, CACHED, (fields, 1), flags)
            check(f'fields{fields:x}-flags{flags:x}-native-results-registers-and-nzcvq-preserved', actual == expected)
    del f; gc.collect()
    f = ParameterHostFixture(raw, host, failed, failed_metadata)
    check('failed-init-clears-cached-and-all-prior-callbacks-before-free', f.load() == 7 and not f.live and
          all(f.read(STATE + off) == 0 for off in (256, 260, 272, 276, 288, 292)))
    del f; gc.collect()

    # Reproduce the old bypass on the exact accepted API56 pair. Scheduling
    # here is sequential: this establishes a path gap, not physical concurrency.
    f = CleanupFixture(old_raw, old_host, old_packet, old_module); f.start(True, 0)
    f.toggle(); f.call(SOURCE_APPLY, 0, FRAME)
    check('old-api56-primary-off-filter-clears-register-enable', f.control() & 1 == 0)
    f.write(FRAME + 0x34, 1)
    check('old-api56-cached-metadata-bypasses-filter-and-reenables-old-owned-parameters',
          f.call(CACHED, FRAME + 4, 1) == 1 and f.control() & 1 == 1)
    del f; gc.collect()

    f = CleanupFixture(raw, host, packet, module); baseline = f.start(True, 0)
    record = f.address('z7_highlight_native_frame')
    original = bytes(f.u.mem_read(FRAME, 0x4b8))
    f.toggle(); calls_before = f.frame_calls
    check('cached-null-refresh-inhibits-off-without-primary-frame-gui-or-worker',
          f.call(CACHED, 0, 1) == 1 and f.control() & 1 == 0 and f.frame_calls == calls_before and f.read(record + 52) == 0)
    f.write(FRAME + 0x34, 1)
    check('cached-fresh-native-one-cannot-reenable-off-owned-parameters',
          f.call(CACHED, FRAME + 4, 1) == 1 and f.control() & 1 == 0 and f.read(NATIVE + 0x20) == 0)
    check('cached-native-input-record-keeps-original-one-after-null-recheck', f.read(record + 52) == 1)
    f.gui(); f.worker(); f.dispatch(); f.worker()
    check('cleanup-restores-enabled-native-baseline-using-cached-original-one', f.parameters() == baseline and f.lease() == 0 and f.control() & 1 == 1)
    f.toggle(); f.gui(); f.worker(); f.dispatch(); f.worker()
    f.write(FRAME + 0x34, 0); f.call(SOURCE_APPLY, 0, FRAME)
    check('cached-null-refresh-on-does-not-replace-original-zero-with-filtered-one',
          f.call(CACHED, 0, 1) == 1 and f.control() & 1 == 1 and f.read(record + 52) == 0)
    f.toggle(); f.gui(); f.worker(); f.dispatch(); f.worker()
    check('off-cleanup-after-cached-null-keeps-enabled-native-baseline-hidden', f.parameters() == baseline and f.lease() == 0 and f.control() & 1 == 0)
    f.toggle(); f.gui(); f.worker(); f.dispatch(); f.worker(); f.call(SOURCE_APPLY, 0, FRAME)
    f.write(0xa2c41008, 1)
    check('cached-refresh-rechecks-live-menu-before-gui-or-worker', f.call(CACHED, 0, 1) == 1 and f.control() & 1 == 0)
    f.write(0xa2c41008, 0); f.call(SOURCE_APPLY, 0, FRAME)
    f.write(0xa24e1e00, 1)
    check('cached-refresh-rechecks-live-movie-before-gui-or-worker', f.call(CACHED, 0, 1) == 1 and f.control() & 1 == 0)
    f.write(0xa24e1e00, 0); f.write(FRAME + 0x34, 2)
    check('cached-native-nonboolean-inhibit-remains-native', f.call(CACHED, FRAME + 4, 1) == 1 and f.read(NATIVE + 0x20) == 2 and f.control() & 1 == 0)
    f.write(FRAME + 0x34, 0)
    check('cached-filter-does-not-mutate-input-frame', bytes(f.u.mem_read(FRAME, 0x4b8)) == original)
    del f; gc.collect()

    f = CleanupFixture(raw, host, packet, module); f.start(True, 0)
    record = f.address('z7_highlight_native_frame'); latest = f.convert(2, 202)
    f.native(latest)
    check('same-context-native-update-retains-original-frame-policy-for-null-refresh',
          f.read(record + 60) == 1 and f.read(record + 52) == 0 and f.control() & 1 == 0)
    check('null-refresh-can-present-updated-owned-parameters-with-known-original-policy',
          f.call(CACHED, 0, 1) == 1 and f.control() & 1 == 1 and f.read(record + 52) == 0)
    f.toggle(); f.gui(); f.worker(); f.dispatch(); f.worker()
    check('no-frame-off-after-native-update-and-null-refresh-restores-latest-baseline-hidden',
          f.parameters() == latest and f.lease() == 0 and f.control() & 1 == 0)
    f.toggle(); f.gui(); f.worker(); f.dispatch(); f.worker()
    f.write(FRAME + 0x34, 2); f.call(SOURCE_APPLY, 0, FRAME)
    latest = f.convert(2, 191); f.native(latest)
    check('native-inhibit-survives-parameter-update-and-null-cached-refresh',
          f.read(record + 52) == 2 and f.call(CACHED, 0, 1) == 1 and f.control() & 1 == 0)
    f.toggle(); f.gui(); f.worker(); f.dispatch(); f.worker()
    check('off-restoration-retains-explicit-native-inhibit-and-latest-baseline',
          f.parameters() == latest and f.lease() == 0 and f.read(NATIVE + 0x20) == 2 and f.control() & 1 == 0)
    del f; gc.collect()

    f = CleanupFixture(raw, host, packet, module); f.load()
    baseline = f.convert(2, 213); f.native(baseline)
    f.call(host['symbols']['z7_display_before_update']); f.gui(); f.worker(); f.dispatch(); f.worker()
    check('null-refresh-without-known-original-frame-policy-cannot-create-untracked-owned-plane',
          f.call(CACHED, 0, 1) == 1 and f.control() & 1 == 0 and f.value('z7_highlight_frame_enabled') == 0)
    f.write(FRAME + 0x34, 1)
    check('fresh-cached-metadata-can-establish-original-policy-without-primary-frame',
          f.call(CACHED, FRAME + 4, 1) == 1 and f.control() & 1 == 1)
    f.toggle(); f.gui(); f.worker(); f.dispatch(); f.worker()
    check('no-frame-off-after-first-cached-presentation-restores-native-baseline-one',
          f.parameters() == baseline and f.lease() == 0 and f.control() & 1 == 1)
    del f; gc.collect()
    f = HostFixture(old_raw, old_host, packet)
    menu = bytes(f.u.mem_read(0xa1833548, 44))
    check('api56-host-rejects-api60-profile-before-native-menu-preparation',
          f.call(old_host['symbols']['z7_module_load_once'], STATE) == 7 and not f.live and bytes(f.u.mem_read(0xa1833548, 44)) == menu)
    return dict(passed=True, checks=checks, host_sha256=host['main_payload_sha256'], module_sha256=module['module_sha256'],
                old_api56_cached_path_gap_reproduced=True, native_cached_metadata_and_null_refresh_execute=True,
                actual_native_driver_register_effects_verified=True, original_cached_permission_not_replaced_by_filtered_value=True,
                native_frame_parameter_serialization_allocation_lifetime_or_physical_pixels_proven=False,
                kernel_filesystem_ui_surfaces_colors_engine_descriptors_mmio_and_scheduling_supplied=True,
                camera_card_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True); p.add_argument('--module', type=Path, required=True)
    p.add_argument('--legacy-build', type=Path, required=True); p.add_argument('--legacy-module', type=Path, required=True)
    p.add_argument('--stock-main', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); out = a.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists(): p.error('Choose a new private output directory')
    if hashlib.sha256(a.stock_main.read_bytes()).hexdigest() != STOCK_SHA: p.error('Exact stock main required')
    def inputs(folder, module=False):
        r = json.loads((folder / ('module.json' if module else 'module-host.emulator.json')).read_text(encoding='utf-8'))
        b = (folder / ('Z7APP.BIN' if module else 'module-host.emulator.main.bin')).read_bytes()
        if hashlib.sha256(b).hexdigest() != r['module_sha256' if module else 'main_payload_sha256']: raise ValueError('Fingerprint mismatch')
        return b, r
    raw, host = inputs(a.build); packet, module = inputs(a.module, True)
    old_raw, old_host = inputs(a.legacy_build); old_packet, old_module = inputs(a.legacy_module, True)
    if not host.get('cached_frame_permission_hooks') or module['api_minimum_bytes'] != 60: p.error('Explicit API60 pair required')
    source = ROOT / 'z7-native-modules/examples/cached_frame_host_probe.c'
    probe, metadata = build(source, zig=ZIG); out.mkdir(parents=True)
    failed_source = out / 'failed.c'
    failed_source.write_text('#define Z7_CACHED_INIT_FAIL 1\n#include "' + source.as_posix() + '"\n', encoding='utf-8', newline='\n')
    failed, failed_metadata = build(failed_source, zig=ZIG)
    result = audit(raw, host, packet, module, old_raw, old_host, old_packet, old_module, probe, metadata, failed, failed_metadata)
    result['source_sha256'] = {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in (
        'tools/audit_z7_cached_frame.py', 'tools/build_z7_module_host.py', 'tools/build_z7_display_module.py',
        'tools/audit_z7_module_host.py', 'z7-native-modules/sdk/cached_frame_permission.h',
        'z7-native-modules/examples/cached_frame_host_probe.c', 'z7-native-modules/host/z7_380.c',
        'z7-native-modules/host/z7_380.h', 'z7-native-modules/examples/display_highlight_owned_policy.h',
        'z7-native-modules/plugins/combined_display.c')}
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__': main()
