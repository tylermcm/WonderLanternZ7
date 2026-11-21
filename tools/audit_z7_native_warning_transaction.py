"""Execute API72 warning-gate/parameter transactions under supplied schedules.

SPDX-License-Identifier: MIT. Native code and register writes execute; kernel,
colors/surfaces, task schedules, engine/context and MMIO storage are supplied.
No physical wait-graph, indirect native caller/writer closure or pixels proof.
"""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_R0
from audit_splash_image import STOCK_SHA, STACK, STOP, MEM
from audit_z7_owned_frame_coordination import CoordinatedFixture
from audit_z7_highlight_cleanup import CleanupFixture
from audit_z7_highlight_submission import enter, returned
from audit_z7_highlight_frame_gate import SOURCE_APPLY, FRAME_APPLY
from audit_z7_cached_frame import CACHED
from audit_z7_parameters import NATIVE, CALLER_STACK, PACKET, PAYLOAD
from audit_z7_frame_permission import FRAME
from build_z7_module_host import ROOT, STATE
from z30_extensions.assembly import assemble, constant, invoke


class TransactionFixture(CoordinatedFixture):
    pause_delay = pause_completion = pause_mutex = pause_postgate = False
    def __init__(self, *args):
        super().__init__(*args); self.u.mem_map(NATIVE + 0x6000, 0x2000)
    def hook(self, u, address, size, context):
        if not self.cleanup_running:
            CleanupFixture.hook(self, u, address, size, context); return
        if self.pause_delay and address == 0x1017081e and u.reg_read(UC_ARM_REG_R0) == 1:
            self.pause_delay = False; self.delay_paused = True; u.emu_stop(); return
        if self.pause_completion and address == 0x102396c8:
            self.pause_completion = False; self.completion_paused = True; u.emu_stop(); return
        if self.pause_mutex and address == 0x10170944 and u.reg_read(UC_ARM_REG_R0) == 0xa1d6ab80:
            self.pause_mutex = False; self.mutex_paused = True; u.emu_stop(); return
        if self.pause_postgate and address == 0x1023babc:
            self.pause_postgate = False; self.postgate_paused = True; u.emu_stop(); return
        super().hook(u, address, size, context)


def audit(raw, host, packet, module):
    checks = []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    def lane(f): return f.read(STATE + 308), f.read(STATE + 312)
    def resume(f, ctx):
        f.u.context_restore(ctx)
        f.u.emu_start(f.u.reg_read(UC_ARM_REG_PC) | 1, STOP, timeout=10000000, count=10000000)
    def prepare(f, data, descriptor=PACKET, payload=PAYLOAD, callback=0):
        f.u.mem_write(payload, data + bytes(4))
        f.u.mem_write(descriptor, struct.pack('<7I', 0, 0, 0, callback, 0x42060007, payload, 0))
    def available(f):
        api = f.read(f.address('native_warning_api'))
        return f.call(f.read(api + 68))

    for label, entry, args in (('source', SOURCE_APPLY, (0, FRAME)),
                               ('cached-fresh', CACHED, (FRAME + 4, 1)),
                               ('cached-null', CACHED, (0, 1))):
        f = TransactionFixture(raw, host, packet, module); f.load(); baseline = bytes(100); f.native(baseline)
        check(label + '-activates-both-protocols-and-owned-feature-status',
              f.read(STATE + 304) == f.read(STATE + 324) == available(f) == 1)
        f.call(host['symbols']['z7_display_before_update']); f.gui(); f.worker(); f.dispatch(); f.worker()
        f.write(FRAME + 0x34, 0)
        if label == 'cached-null': f.call(SOURCE_APPLY, 0, FRAME); f.write(NATIVE + 0x24, 1)
        f.pause_driver = True; f.driver_paused = False
        frame_guards = enter(f, entry, args, CALLER_STACK); frame_ctx = f.u.context_save()
        held = lane(f); before = f.parameters()
        check(label + '-native-gate-holds-frame-token-at-real-enable-driver', f.driver_paused and held[0] & 3 == 1)
        f.toggle(); f.gui()
        if label == 'source':
            cancelled = f.owned('cancelled'); f.worker()
            check('owned-cleanup-cancels-without-releasing-active-native-gate',
                  f.dispatch() == 0 and f.owned('cancelled') == cancelled + 1 and lane(f) == held and f.lease() == 1)
        prepare(f, baseline)
        f.pause_delay = True; f.delay_paused = False
        foreign_guards = enter(f, 0x10239840, (PACKET,), STACK); foreign_ctx = f.u.context_save()
        check(label + '-foreign-request-yields-without-copy-ack-or-lease-release',
              f.delay_paused and f.parameters() == before and f.read(PAYLOAD + 100) == 0 and f.lease() == 1 and lane(f) == held)
        resume(f, frame_ctx)
        check(label + '-earlier-frame-finishes-before-waiting-request',
              returned(f, CALLER_STACK, frame_guards) and f.control() & 1 == 1 and lane(f)[0] & 3 == 0)
        resume(f, foreign_ctx)
        check(label + '-foreign-consumer-copies-acks-quiesces-and-retires',
              returned(f, STACK, foreign_guards) and f.u.reg_read(UC_ARM_REG_R0) == 1 and
              f.parameters() == baseline and f.read(PAYLOAD + 100) == 1 and f.lease() == 0 and
              f.control() & 1 == 0 and lane(f)[0] & 3 == 0 and lane(f)[1] == 0)
        check(label + '-next-frame-cannot-resurrect-off-plane', f.call(entry, *args) == 1 and f.control() & 1 == 0)
        del f; gc.collect()

    f = TransactionFixture(raw, host, packet, module); baseline = f.start(False, 0)
    f.toggle(); f.gui(); prepare(f, baseline)
    f.pause_copy = True; f.copy_paused = False
    guards = enter(f, 0x10239840, (PACKET,), CALLER_STACK); ctx = f.u.context_save()
    held = lane(f); before = f.parameters(); permission = f.read(NATIVE + 0x20); programs = len(f.programs)
    check('foreign-copy-pauses-with-bridge-local-parameter-token', f.copy_paused and held[0] & 3 == 2 and
          f.read(held[1]) == held[0] and f.read(held[1] + 4) == PACKET)
    for label, entry, args in (('primary', FRAME_APPLY, (FRAME, 0)), ('cached-fresh', CACHED, (FRAME + 4, 1)), ('cached-null', CACHED, (0, 1))):
        check(label + '-busy-warning-gate-does-not-store-permission-or-program-plane',
              f.call(entry, *args) == 0 and f.parameters() == before and f.read(NATIVE + 0x20) == permission and
              lane(f) == held and len(f.programs) == programs)
    resume(f, ctx)
    check('foreign-copy-resumes-to-ack-and-release', returned(f, CALLER_STACK, guards) and f.parameters() == baseline and
          f.read(PAYLOAD + 100) == 1 and lane(f)[0] & 3 == 0 and lane(f)[1] == 0)

    # Actual callback thunk reenters native frame and parameter dispatch. The
    # supplied callback code records both native results and preserves its ABI.
    callback, results = MEM + 0x18000, NATIVE + 0x6800
    other_packet, other_payload = NATIVE + 0x6000, NATIVE + 0x6100
    prepare(f, baseline, other_packet, other_payload)
    code = f'''push.w {{r4-r8,lr}}; {constant('r4', results)}
        {constant('r0', FRAME)} movs r1,#0; {invoke(FRAME_APPLY)} str r0,[r4];
        {constant('r0', other_packet)} {invoke(0x10239840)} str r0,[r4,#4];
        pop.w {{r4-r8,pc}};'''
    f.u.mem_write(callback, assemble(code, callback, 192))
    prepare(f, baseline, callback=callback | 1)
    check('foreign-completion-callback-can-reenter-frame-and-parameter-consumer',
          f.call(0x10239840, PACKET) == 1 and f.read(results) == f.read(results + 4) == 1 and
          f.read(other_payload + 100) == 1 and lane(f)[0] & 3 == 0 and lane(f)[1] == 0)

    f.pause_mutex = True; f.mutex_paused = False
    mutex_guards = enter(f, SOURCE_APPLY, (0, FRAME), CALLER_STACK); mutex_ctx = f.u.context_save()
    check('earlier-native-frame-mutex-boundary-does-not-hold-warning-lane',
          f.mutex_paused and lane(f)[0] & 3 == 0 and lane(f)[1] == 0)
    f.native(baseline)
    check('foreign-consumer-completes-while-earlier-frame-is-paused-at-mutex',
          f.read(PAYLOAD + 100) == 1 and f.parameters() == baseline and lane(f)[0] & 3 == 0)
    resume(f, mutex_ctx)
    check('frame-resumes-after-mutex-boundary-without-stale-owned-enable',
          returned(f, CALLER_STACK, mutex_guards) and f.control() & 1 == 0)

    f.toggle(); f.gui(); f.worker(); f.dispatch(); f.worker()
    f.pause_postgate = True; f.postgate_paused = False
    post_guards = enter(f, SOURCE_APPLY, (0, FRAME), CALLER_STACK); post_ctx = f.u.context_save()
    check('postgate-native-frame-releases-warning-lane-before-remaining-render-work',
          f.postgate_paused and f.control() & 1 == 1 and lane(f)[0] & 3 == 0)
    f.toggle(); f.gui(); f.native(baseline)
    check('foreign-update-quiesces-plane-while-prior-frame-is-past-gate', f.control() & 1 == 0 and f.lease() == 0)
    resume(f, post_ctx)
    check('postgate-old-frame-tail-does-not-resurrect-disabled-warning-plane',
          returned(f, CALLER_STACK, post_guards) and f.control() & 1 == 0 and f.parameters() == baseline)

    # Retired local slot cannot release a later consumer while the original
    # completion/dispatcher is still unwinding on its independent stack.
    prepare(f, baseline); f.pause_completion = True; f.completion_paused = False
    old_guards = enter(f, 0x10239840, (PACKET,), CALLER_STACK); old_ctx = f.u.context_save()
    check('foreign-token-is-retired-before-original-completion-callback', f.completion_paused and lane(f)[0] & 3 == 0 and lane(f)[1] == 0)
    prepare(f, baseline, other_packet, other_payload); f.pause_copy = True; f.copy_paused = False
    new_guards = enter(f, 0x10239840, (other_packet,), STACK); new_ctx = f.u.context_save(); held = lane(f)
    check('second-consumer-can-own-lane-before-first-completion-returns', f.copy_paused and held[0] & 3 == 2)
    resume(f, old_ctx)
    check('late-first-consumer-return-cannot-release-second-token', returned(f, CALLER_STACK, old_guards) and lane(f) == held)
    resume(f, new_ctx)
    check('second-consumer-still-completes-with-own-token', returned(f, STACK, new_guards) and lane(f)[0] & 3 == 0 and lane(f)[1] == 0)

    # Exhaustion disables OWNED eligibility but must not freeze native updates.
    f.toggle(); f.gui(); f.worker(); f.dispatch(); f.worker(); f.call(SOURCE_APPLY, 0, FRAME)
    check('owned-feature-reapplies-before-exhaustion', f.lease() == 1 and f.control() & 1 == 1)
    f.write(STATE + 308, 0xfffffff0)
    check('near-exhaustion-status-drains-owned-feature', available(f) == 0 and f.call(SOURCE_APPLY, 0, FRAME) == 1 and f.control() & 1 == 0)
    f.worker(); f.dispatch(); f.worker()
    check('near-exhaustion-worker-restores-native-baseline', f.lease() == 0 and f.parameters() == baseline and f.control() & 1 == 0)
    f.write(STATE + 308, 0xfffffffc)
    for n in range(3):
        prepare(f, baseline, callback=callback | 1)
        check(f'terminal-native-frame-foreign-completion-reentry-{n}-continues-without-counter-wrap',
              f.call(SOURCE_APPLY, 0, FRAME) == 1 and f.call(0x10239840, PACKET) == 1 and
              f.read(results) == f.read(results + 4) == 1 and lane(f) == (0xfffffffc, 0) and available(f) == 0 and f.lease() == 0)
    return dict(passed=True, checks=checks, host_sha256=host['main_payload_sha256'], module_sha256=module['module_sha256'],
                supplied_foreign_stale_frame_schedules_prevented=True, native_completion_reentry_and_retired_slot_verified=True,
                supplied_generation_exhaustion_drains_owned_and_preserves_native_updates=True,
                physical_wait_graph_indirect_writer_caller_closure_pixels_or_installation_proven=False, camera_card_access=False)


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
    if (not host.get('native_warning_transaction_hooks') or module['api_minimum_bytes'] not in (72,80) or
            module['api_minimum_bytes'] > host.get('api_bytes',0) or
            (module['api_minimum_bytes']==80 and not host.get('native_cache_copy_hooks')) or
            hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']):
        p.error('Exact compatible API72/80 host and module required')
    result = audit(raw, host, packet, module)
    names = {*host['source_files'], *module['source_inputs_sha256'],
             'tools/audit_z7_native_warning_transaction.py', 'tools/build_z7_module_host.py', 'tools/build_z7_display_module.py',
             'tools/audit_z7_module_host.py', 'tools/audit_z7_owned_frame_coordination.py', 'tools/audit_z7_highlight_cleanup.py'}
    result['source_sha256'] = {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in sorted(names)}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__': main()
