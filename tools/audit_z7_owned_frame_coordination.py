"""Exercise native primary frames versus owned parameter cleanup on API64.

SPDX-License-Identifier: MIT. Explicit two-stack schedules and modeled native
services/MMIO; no physical scheduling proof. Foreign parameter writers remain
uncoordinated and generation exhaustion has no feature shutdown implementation.
"""
import argparse
import gc
import hashlib
import json
from pathlib import Path

from unicorn.arm_const import UC_ARM_REG_PC
from audit_splash_image import STOCK_SHA, STOP
from audit_z7_gate_interleaving import InterleavingFixture
from audit_z7_highlight_submission import enter, returned
from audit_z7_highlight_host import observed_call
from audit_z7_highlight_frame_gate import SOURCE_APPLY
from audit_z7_highlight_plane import FRAME_APPLY
from audit_z7_cached_frame import CACHED
from audit_z7_parameters import NATIVE, CALLER_STACK
from audit_z7_frame_permission import FRAME
from build_z7_module_host import ROOT, STATE, CURSOR


class CoordinatedFixture(InterleavingFixture):
    pause_copy = False
    def hook(self, u, address, size, context):
        if self.pause_copy and address == 0x1023e226:
            self.pause_copy = False; self.copy_paused = True; u.emu_stop(); return
        super().hook(u, address, size, context)


def audit(raw, host, packet, module):
    checks = []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    def lane(f): return f.read(STATE + 308), f.read(STATE + 312)
    for label, entry, args in (('source', SOURCE_APPLY, (0, FRAME)),
                               ('cached-fresh', CACHED, (FRAME + 4, 1)),
                               ('cached-null', CACHED, (0, 1))):
        f = CoordinatedFixture(raw, host, packet, module)
        if label == 'source':
            f.write(STATE - 4, 0xc3c3c3c3); f.write(STATE + 324, 0xc3c3c3c3)
            check('cold-reserves384-for324-with-neighbor-and-all-guard-integrity',
                  f.call(0x101e3d94) == STATE and f.read(CURSOR) == STATE + 384 and
                  f.read(STATE - 4) == f.read(STATE + 324) == 0xc3c3c3c3 and
                  all(f.read(STATE + off) == 0xa5a5a5a5 for off in
                      (240, 244, 248, 252, 264, 268, 280, 284, 296, 300, 316, 320)))
            del f; gc.collect(); f = CoordinatedFixture(raw, host, packet, module)
        f.load(); baseline = bytes(100); f.native(baseline)
        check(label + '-module-enables-coordination-only-with-idle-published-lane',
              f.read(STATE + 304) == 1 and lane(f)[0] & 3 == 0 and lane(f)[1] == 0)
        f.call(host['symbols']['z7_display_before_update']); f.gui(); f.worker(); f.dispatch(); f.worker()
        f.write(FRAME + 0x34, 0)
        if label == 'cached-null':
            check(label + '-first-frame-establishes-original-frame-policy', f.call(SOURCE_APPLY, 0, FRAME) == 1)
            f.write(NATIVE + 0x24, 1)
        f.pause_driver = True; f.driver_paused = False
        guards = enter(f, entry, args, CALLER_STACK); suspended = f.u.context_save()
        held = lane(f); before = f.parameters(); done = f.counter('done'); cancelled = f.owned('cancelled')
        check(label + '-pauses-at-real-enable-with-frame-lane-held', f.driver_paused and held[0] & 3 == 1 and held[1] != 0)
        f.toggle(); f.gui(); f.worker()
        check(label + '-busy-off-cancels-with-normal-owned-completion',
              f.dispatch() == 0 and f.owned('cancelled') == cancelled + 1 and
              f.read(f.address('z7_highlight_owned_request') + 128) == 0)
        check(label + '-busy-cancellation-does-not-copy-release-or-report-cleanup',
              f.parameters() == before and f.lease() == 1 and f.counter('done') == done and lane(f) == held)
        f.u.context_restore(suspended)
        f.u.emu_start(f.u.reg_read(UC_ARM_REG_PC) | 1, STOP, timeout=10000000, count=10000000)
        check(label + '-old-frame-finishes-with-original-stack-and-releases-only-its-token',
              returned(f, CALLER_STACK, guards) and lane(f)[0] & 3 == 0 and lane(f)[1] == 0 and f.control() & 1 == 1)
        f.worker()
        check(label + '-retry-restores-baseline-and-clears-real-enable',
              f.dispatch() == 1 and f.counter('done') == done + 1 and f.parameters() == baseline and
              f.lease() == 0 and f.control() & 1 == 0 and lane(f)[0] & 3 == 0 and lane(f)[1] == 0)
        f.worker()
        check(label + '-settled-off-frame-cannot-resurrect-owned-plane',
              f.call(entry, *args) == 1 and f.control() & 1 == 0 and f.parameters() == baseline and f.lease() == 0)
        del f; gc.collect()

    f = CoordinatedFixture(raw, host, packet, module); baseline = f.start(False, 0)
    f.toggle(); f.gui(); f.worker(); f.pause_copy = True; f.copy_paused = False
    guards = enter(f, 0x10239840, (f.queued[-1],), CALLER_STACK); suspended = f.u.context_save()
    held = lane(f); before = f.parameters(); control = f.control(); programs = len(f.programs)
    check('owned-cleanup-pauses-before-real-native-copy-with-parameter-lane-held',
          f.copy_paused and held[0] & 3 == 2 and held[1] == f.queued[-1])
    frame_before = bytes(f.u.mem_read(FRAME, 0x4b8))
    for label, entry, args in (('primary', FRAME_APPLY, (FRAME, 0)),
                               ('cached-fresh', CACHED, (FRAME + 4, 1)),
                               ('cached-null', CACHED, (0, 1))):
        for flags in (0, 0xa8000000, 0x50000000):
            result, volatile, actual_flags = observed_call(f, entry, args, flags)
            check(label + f'-busy-native-zero-preserves-flags{flags:x}-and-input',
                  result == 0 and actual_flags == flags and f.parameters() == before and f.control() == control and
                  lane(f) == held and len(f.programs) == programs and bytes(f.u.mem_read(FRAME, 0x4b8)) == frame_before)
    f.u.context_restore(suspended)
    f.u.emu_start(f.u.reg_read(UC_ARM_REG_PC) | 1, STOP, timeout=10000000, count=10000000)
    check('resumed-owned-consumer-completes-native-copy-cleanup-and-lane-release',
          returned(f, CALLER_STACK, guards) and f.parameters() == baseline and f.control() & 1 == 0 and
          f.lease() == 0 and lane(f)[0] & 3 == 0 and lane(f)[1] == 0)
    return dict(passed=True, checks=checks, host_sha256=host['main_payload_sha256'], module_sha256=module['module_sha256'],
                owned_off_cleanup_stale_frame_schedule_prevented=True, native_frame_rejected_while_owned_copy_active=True,
                foreign_native_parameter_requests_coordinated=False, lane_exhaustion_shutdown_implemented=False,
                physical_scheduler_engine_lifetime_pixels_or_installation_proven=False, camera_card_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True); p.add_argument('--module', type=Path, required=True)
    p.add_argument('--stock-main', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); out = a.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists(): p.error('Choose a new private output file')
    if hashlib.sha256(a.stock_main.read_bytes()).hexdigest() != STOCK_SHA: p.error('Exact stock main required')
    host = json.loads((a.build / 'module-host.emulator.json').read_text(encoding='utf-8'))
    module = json.loads((a.module / 'module.json').read_text(encoding='utf-8'))
    raw, packet = (a.build / 'module-host.emulator.main.bin').read_bytes(), (a.module / 'Z7APP.BIN').read_bytes()
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        p.error('Exact host/module fingerprints required')
    if not host.get('owned_frame_coordination_hooks') or module['api_minimum_bytes'] != 64: p.error('Explicit API64 pair required')
    result = audit(raw, host, packet, module)
    names = {*host['source_files'], *module['source_inputs_sha256'],
             'tools/audit_z7_owned_frame_coordination.py', 'tools/build_z7_module_host.py',
             'tools/build_z7_display_module.py', 'tools/audit_z7_module_host.py'}
    result['source_sha256'] = {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in sorted(names)}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__': main()
