"""Reproduce a stale in-flight native frame after no-frame Off cleanup.

SPDX-License-Identifier: MIT. This supplies an explicit two-stack schedule; it
does NOT prove that physical native tasks can take this schedule. Actual native
gate/consumer/driver instructions and emulated MMIO effects execute. A successful
reproduction is evidence against an unqualified ordering guarantee, not safety.
"""
import argparse
import hashlib
import json
from pathlib import Path

from unicorn.arm_const import UC_ARM_REG_R2, UC_ARM_REG_PC
from audit_z7_highlight_cleanup import CleanupFixture
from audit_z7_highlight_submission import enter, returned
from audit_z7_highlight_frame_gate import SOURCE_APPLY
from audit_z7_highlight_plane import DRIVER
from audit_z7_parameters import NATIVE, CALLER_STACK
from audit_z7_frame_permission import FRAME
from audit_splash_image import STOCK_SHA, STOP
from build_z7_module_host import ROOT


class InterleavingFixture(CleanupFixture):
    pause_driver = False

    def hook(self, u, address, size, context):
        if self.pause_driver and address == DRIVER and u.reg_read(UC_ARM_REG_R2) == 1:
            self.pause_driver = False
            self.driver_paused = True
            u.emu_stop()
            return
        super().hook(u, address, size, context)


def audit(raw, host, packet, module):
    checks = []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    f = InterleavingFixture(raw, host, packet, module); f.load()
    baseline = bytes(100)
    f.native(baseline)
    f.call(host['symbols']['z7_display_before_update']); f.gui(); f.worker(); f.dispatch(); f.worker()
    f.write(FRAME + 0x34, 0)
    f.pause_driver = True; f.driver_paused = False
    guards = enter(f, SOURCE_APPLY, (0, FRAME), CALLER_STACK)
    suspended = f.u.context_save()
    check('frame-pauses-at-real-enable-driver-after-eligibility-and-conversion',
          f.driver_paused and f.u.reg_read(UC_ARM_REG_PC) == DRIVER and f.control() & 1 == 0 and f.lease() == 1)
    f.toggle(); f.gui(); f.worker()
    check('off-restoration-consumer-acknowledges-while-earlier-frame-is-suspended', f.dispatch() == 1)
    check('cleanup-reports-success-restores-baseline-and-releases-lease',
          f.counter('done') == 1 and f.parameters() == baseline and f.lease() == 0 and f.control() & 1 == 0)
    f.u.context_restore(suspended)
    f.u.emu_start(f.u.reg_read(UC_ARM_REG_PC) | 1, STOP, timeout=10000000, count=10000000)
    check('resumed-old-frame-returns-with-original-stack-and-callee-registers', returned(f, CALLER_STACK, guards))
    check('resumed-old-frame-reenables-plane-after-successful-off-cleanup',
          f.control() & 1 == 1 and f.read(NATIVE + 0x1c) == 1 and f.parameters() == baseline and f.lease() == 0)
    return dict(passed=True, checks=checks, host_sha256=host['main_payload_sha256'], module_sha256=module['module_sha256'],
                stale_inflight_frame_after_cleanup_reproduced=True,
                frame_parameter_ordering_safe_under_supplied_interleaving=False,
                actual_native_gate_consumer_driver_and_register_writes_execute=True,
                separate_frame_and_consumer_stacks_and_schedule_supplied=True,
                physical_schedule_reachability_shared_locks_or_pixels_proven=False,
                camera_card_access=False)


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
    if not host.get('cached_frame_permission_hooks') or module['api_minimum_bytes'] != 60: p.error('Explicit API60 pair required')
    result = audit(raw, host, packet, module)
    result['source_sha256'] = {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in (
        'tools/audit_z7_gate_interleaving.py', 'tools/audit_z7_highlight_cleanup.py',
        'z7-native-modules/examples/display_highlight_cleanup_policy.h',
        'z7-native-modules/examples/display_highlight_owned_policy.h')}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(reproduced=True, checks=len(result['checks']), ordering_safe=False)))


if __name__ == '__main__': main()
