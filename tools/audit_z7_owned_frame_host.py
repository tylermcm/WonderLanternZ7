"""Check API64 init, guards, native-frame token lifetime and failed activation.

SPDX-License-Identifier: MIT. Calls compiled host ownership helpers; the full
native frame/driver schedules are covered separately. No hardware clearance.
"""
import argparse
import hashlib
import json
from pathlib import Path

from audit_z7_parameters import ParameterHostFixture
from audit_splash_image import STOCK_SHA
from build_z7_module import ROOT, build
from build_z7_module_host import STATE, ZIG


def audit(raw, host, probe, metadata, failed, failed_metadata):
    checks = []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    f = ParameterHostFixture(raw, host, probe, metadata)
    check('enable-requires-callbacks-and-is-single-init-only-operation', f.load() == 8 and
          f.read(f.address('z7_of_mask')) == 15 and f.read(STATE + 304) == 1 and f.call(f.address('z7_of_late')) == 0)
    start, end = host['symbols']['z7_owned_frame_enter'], host['symbols']['z7_owned_frame_leave']
    owned = host['symbols']['z7_owned_parameter_enter']
    owner = 0xa251f000
    token = f.call(start, owner)
    check('frame-helper-admits-and-rejects-nested-owner', token & 3 == 1 and f.call(start, owner) == 0xffffffff and f.read(STATE + 312) == owner)
    f.call(end, owner + 8, token); f.call(end, owner, token + 4)
    check('wrong-token-or-owner-does-not-release-frame',
          f.read(STATE + 308) == token and f.read(STATE + 312) == owner)
    f.call(end, owner, token)
    next_token = f.call(start, owner)
    f.call(end, owner, token)
    check('late-release-cannot-open-later-frame-at-same-stack-address', next_token != token and f.read(STATE + 308) == next_token)
    f.call(end, owner, next_token)
    for off in (316, 320):
        before = f.read(STATE + 308)
        f.write(STATE + off, 0)
        check(f'corrupt-new-guard{off}-disables-helper-admission-and-callback-activation',
              f.call(start, owner) == 0 and f.call(owned, f.read(STATE + 212)) == 0 and
              f.call(f.address('z7_of_late')) == 0 and f.read(STATE + 308) == before)
        f.write(STATE + off, 0xa5a5a5a5)
    # Foreign descriptors never acquire this diagnostic's owned-only lane.
    check('foreign-packet-helper-preserves-native-path-without-lane-claim',
          f.call(owned, 0xa2502000) == 0 and f.read(STATE + 308) & 3 == 0)
    f.write(STATE + 308, 0xfffffffc)
    check('generation-exhaustion-refuses-frame-admission-without-wrap', f.call(start, owner) == 0xffffffff and
          f.read(STATE + 308) == 0xfffffffc and f.read(STATE + 312) == 0)

    f = ParameterHostFixture(raw, host, failed, failed_metadata)
    check('failed-init-after-activation-releases-module-and-clears-activation-and-callbacks',
          f.load() == 7 and f.read(STATE + 304) == 0 and f.read(STATE + 48) == f.read(STATE + 52) == 0 and
          all(f.read(STATE + off) == 0 for off in (212, 216, 220, 224, 228, 256, 272, 288)) and
          f.read(STATE + 308) & 3 == 0 and f.read(STATE + 312) == 0)
    f = ParameterHostFixture(raw, host, probe, metadata)
    token = f.call(start, owner)
    check('preactivation-frame-is-tracked-before-module-load', token & 3 == 1 and f.read(STATE + 304) == 0)
    check('activation-fails-without-resetting-older-inflight-frame-token', f.load() == 7 and f.read(STATE + 304) == 0 and
          f.read(STATE + 308) == token and f.read(STATE + 312) == owner)
    f.call(end, owner, token)
    f.position = 0  # Supplied filesystem: a new open starts at file offset0.
    check('activation-can-retry-after-prior-frame-retires', f.load() == 8 and f.read(STATE + 304) == 1 and
          f.read(STATE + 308) & 3 == 0 and f.read(STATE + 312) == 0)
    return dict(passed=True, checks=checks, native_host_ownership_helpers_execute=True,
                foreign_parameter_serialization_or_exhaustion_shutdown_implemented=False, camera_card_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True); p.add_argument('--stock-main', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); out = a.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists(): p.error('Choose a new private output directory')
    if hashlib.sha256(a.stock_main.read_bytes()).hexdigest() != STOCK_SHA: p.error('Exact stock main required')
    host = json.loads((a.build / 'module-host.emulator.json').read_text(encoding='utf-8'))
    raw = (a.build / 'module-host.emulator.main.bin').read_bytes()
    if not host.get('owned_frame_coordination_hooks') or hashlib.sha256(raw).hexdigest() != host['main_payload_sha256']:
        p.error('Exact API64 host required')
    source = ROOT / 'z7-native-modules/examples/owned_frame_host_probe.c'
    packet, metadata = build(source, zig=ZIG)
    out.mkdir(parents=True)
    failed_source = out / 'failed.c'
    failed_source.write_text('#define Z7_OWNED_COORD_INIT_FAIL 1\n#include "' + source.as_posix() + '"\n', encoding='utf-8', newline='\n')
    failed, failed_metadata = build(failed_source, zig=ZIG)
    result = audit(raw, host, packet, metadata, failed, failed_metadata)
    result.update(host_sha256=host['main_payload_sha256'], probe_sha256=hashlib.sha256(packet).hexdigest(),
                  failed_probe_sha256=hashlib.sha256(failed).hexdigest())
    result['source_sha256'] = {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in (
        'tools/audit_z7_owned_frame_host.py', 'z7-native-modules/examples/owned_frame_host_probe.c',
        'z7-native-modules/host/z7_380.c', 'z7-native-modules/host/z7_380.h', 'z7-native-modules/host/highlight_lane.h',
        'z7-native-modules/sdk/owned_frame_coordination.h', 'tools/audit_z7_module_host.py')}
    for name, value in (('probe.BIN', packet), ('failed.BIN', failed)): (out / name).write_bytes(value)
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__': main()
