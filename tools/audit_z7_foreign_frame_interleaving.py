"""Reproduce the FOREIGN parameter gap left by owned-only API64 coordination.

SPDX-License-Identifier: MIT. A supplied two-stack schedule executes original
consumer, frame/gate and register instructions. Successful reproduction is a
counterexample, not a safety or physical-schedule-reachability assertion.
"""
import argparse
import hashlib
import json
from pathlib import Path

from unicorn.arm_const import UC_ARM_REG_PC
from audit_splash_image import STOCK_SHA, STOP
from audit_z7_gate_interleaving import InterleavingFixture
from audit_z7_highlight_submission import enter, returned
from audit_z7_highlight_frame_gate import SOURCE_APPLY
from audit_z7_frame_permission import FRAME
from audit_z7_parameters import CALLER_STACK, NATIVE
from build_z7_module_host import ROOT, STATE


def audit(raw, host, packet, module):
    checks = []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    f = InterleavingFixture(raw, host, packet, module); f.load()
    baseline = bytes(100); f.native(baseline)
    f.call(host['symbols']['z7_display_before_update']); f.gui(); f.worker(); f.dispatch(); f.worker()
    f.write(FRAME + 0x34, 0); f.pause_driver = True; f.driver_paused = False
    guards = enter(f, SOURCE_APPLY, (0, FRAME), CALLER_STACK); saved = f.u.context_save()
    held = f.read(STATE + 308), f.read(STATE + 312)
    check('owned-frame-pauses-at-real-enable-while-holding-frame-token',
          f.driver_paused and held[0] & 3 == 1 and f.lease() == 1 and f.control() & 1 == 0)
    f.toggle(); f.gui()
    f.native(baseline)  # Original foreign descriptor, actual copy/ack/completion.
    check('foreign-native-update-completes-and-releases-old-owned-lease-during-frame',
          f.parameters() == baseline and f.lease() == 0 and f.control() & 1 == 0 and
          (f.read(STATE + 308), f.read(STATE + 312)) == held)
    f.u.context_restore(saved)
    f.u.emu_start(f.u.reg_read(UC_ARM_REG_PC) | 1, STOP, timeout=10000000, count=10000000)
    check('old-frame-retires-with-correct-stack-and-releases-frame-token',
          returned(f, CALLER_STACK, guards) and f.read(STATE + 308) & 3 == 0 and f.read(STATE + 312) == 0)
    check('old-frame-reenables-plane-after-foreign-disabled-parameters-and-lease-release',
          f.control() & 1 == 1 and f.read(NATIVE + 0x1c) == 1 and f.parameters() == baseline and f.lease() == 0)
    return dict(passed=True, checks=checks, stale_frame_after_foreign_update_reproduced=True,
                foreign_frame_parameter_ordering_safe=False, actual_native_copy_gate_driver_registers_execute=True,
                explicit_schedule_kernel_services_context_engine_and_mmio_supplied=True,
                physical_schedule_reachability_proven=False, camera_card_access=False,
                host_sha256=host['main_payload_sha256'], module_sha256=module['module_sha256'])


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
    if not host.get('owned_frame_coordination_hooks') or module['api_minimum_bytes'] != 64 or (
            hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']):
        p.error('Exact API64 host and module required')
    result = audit(raw, host, packet, module)
    names = {*host['source_files'], *module['source_inputs_sha256'],
             'tools/audit_z7_foreign_frame_interleaving.py', 'tools/audit_z7_gate_interleaving.py',
             'tools/audit_z7_highlight_cleanup.py', 'tools/audit_z7_highlight_plane.py',
             'tools/audit_z7_highlight_owned.py', 'tools/audit_z7_highlight_submission.py',
             'tools/build_z7_module_host.py', 'tools/audit_z7_module_host.py'}
    result['source_sha256'] = {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in sorted(names)}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(reproduced=True, checks=len(result['checks']), foreign_ordering_safe=False)))


if __name__ == '__main__': main()
