"""Execute no-frame restoration in the qualified native parameter consumer.

SPDX-License-Identifier: MIT. Original driver writes emulated MMIO; kernel/FS/
UI/surfaces/colors/native engine descriptors and explicit scheduling supplied.
No physical plane application, allocation pin, pixels or camera/card proof.
"""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import struct

from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_R0
from audit_z7_highlight_plane import PlaneFixture, MMIO
from audit_z7_highlight_owned import OwnedFixture
from audit_z7_frame_permission import FRAME
from audit_z7_highlight_frame_gate import SOURCE_APPLY, FRAME_APPLY, GATE
from audit_z7_parameters import NATIVE
from audit_splash_image import STOCK_SHA, STACK, STOP
from audit_z7_highlight_submission import enter, returned
from build_z7_module_host import ROOT


class CleanupFixture(PlaneFixture):
    def __init__(self, *args):
        self.frame_calls = 0
        self.cleanup_running = False
        self.reject_disable = False
        self.stuck_control = None
        super().__init__(*args)
        self.engine = NATIVE + 0x2800
        self.write(self.engine, 0x141); self.write(self.engine + 4, 0)
        self.write(0xa180a578, self.engine)

    def hook(self, u, address, size, context):
        if not self.cleanup_running:
            # Module CRC/init does not use frame/plane boundaries. Keep the
            # original ownership fixture's hooks during that expensive phase.
            OwnedFixture.hook(self, u, address, size, context); return
        if self.stuck_control is not None:
            u.mem_write(MMIO + 0x430, struct.pack('<I', self.stuck_control)); self.stuck_control = None
        if address in (SOURCE_APPLY, FRAME_APPLY): self.frame_calls += 1
        super().hook(u, address, size, context)

    def mmio_write(self, u, access, address, size, value, context):
        super().mmio_write(u, access, address, size, value, context)
        if self.reject_disable and address == MMIO + 0x430 and not value & 1:
            self.stuck_control = self.read(address) | 1  # Supplied stuck hardware bit.

    def counter(self, name): return self.value('z7_highlight_cleanup_' + name)
    def load(self):
        OwnedFixture.load(self)
        self.cleanup_running = True
    def control(self): return self.read(MMIO + 0x430)
    def start(self, enabled, permission):
        self.load()
        baseline = self.convert(2, 213) if enabled else bytes(100)
        self.native(baseline)
        self.call(self.report['symbols']['z7_display_before_update']); self.gui(); self.worker(); self.dispatch(); self.worker()
        self.write(FRAME + 0x34, permission)
        if self.call(SOURCE_APPLY, 0, FRAME) != 1 or not self.control() & 1: raise AssertionError('Initial owned plane')
        return baseline


class AdmittedOwnedFixture(OwnedFixture):
    """Original ownership model plus admitted engine; no plane hook overhead."""
    def __init__(self, *args):
        super().__init__(*args)
        self.write(NATIVE + 0x2800, 0x141); self.write(NATIVE + 0x2804, 0)
        self.write(0xa180a578, NATIVE + 0x2800)


def audit(raw, host, packet, module):
    checks = []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    f = CleanupFixture(raw, host, packet, module)
    baseline = f.start(False, 0)
    record = f.address('z7_highlight_native_frame')
    check('captures-original-native-zero-separately-from-filtered-one', f.read(record + 52) == 0 and f.read(NATIVE + 0x20) == 1 and f.read(record + 60) == 1)
    calls = f.frame_calls; before = bytes(f.u.mem_read(FRAME, 0x4b8))
    f.toggle(); f.gui(); count = len(f.programs); f.worker()
    check('worker-queues-cleanup-without-calling-frame-or-plane-driver', f.frame_calls == calls and len(f.programs) == count and f.control() & 1 == 1)
    f.dispatch()
    check('off-consumer-restores-disabled-baseline-and-clears-plane-without-frame',
          f.frame_calls == calls and f.parameters() == baseline and f.control() & 1 == 0 and f.read(NATIVE + 0x20) == 0 and
          f.read(NATIVE + 0x1c) == 0 and f.lease() == 0 and f.counter('done') == 1 and bytes(f.u.mem_read(FRAME, 0x4b8)) == before)
    f.worker(); count = len(f.programs); f.worker()
    check('settled-off-does-not-repeat-plane-cleanup', len(f.programs) == count)
    f.toggle(); f.gui(); f.worker(); f.dispatch(); f.worker(); f.call(SOURCE_APPLY, 0, FRAME)
    f.write(NATIVE + 0x1c, 0)  # Deliberately stale native bookkeeping.
    calls = f.frame_calls; f.toggle(); f.gui(); f.worker(); f.dispatch(); f.worker()
    check('register-qualified-disable-fallback-clears-plane-despite-stale-inactive-bookkeeping',
          f.frame_calls == calls and f.control() & 1 == 0 and f.lease() == 0 and f.parameters() == baseline)

    # Native enabled baseline with original frame permission0 must stay hidden,
    # even though the module's consumed permission had been forced to1.
    f.toggle(); f.gui()
    enabled_baseline = f.convert(2, 213); f.native(enabled_baseline); f.worker()
    f.write(FRAME + 0x34, 0); f.call(SOURCE_APPLY, 0, FRAME)
    calls = f.frame_calls; f.toggle(); f.gui(); f.worker(); f.dispatch(); f.worker()
    check('enabled-native-baseline-with-original-zero-is-restored-but-not-rendered',
          f.frame_calls == calls and f.parameters() == enabled_baseline and f.control() & 1 == 0 and f.read(NATIVE + 0x20) == 0 and f.lease() == 0)

    f.toggle(); f.gui(); f.worker(); f.dispatch(); f.worker()
    f.write(FRAME + 0x34, 1); f.call(SOURCE_APPLY, 0, FRAME)
    calls = f.frame_calls; owned_threshold = f.read(MMIO + 0x434)
    f.toggle(); f.gui(); f.worker(); f.dispatch(); f.worker()
    check('enabled-native-baseline-with-original-one-reprograms-native-plane-without-frame',
          f.frame_calls == calls and f.parameters() == enabled_baseline and f.control() & 1 == 1 and f.read(NATIVE + 0x20) == 1 and
          f.read(MMIO + 0x434) != owned_threshold and f.lease() == 0)

    # After a meaningful format0 frame, format4 is a native bypass. Cleanup
    # retains the prior meaningful format rather than calling a no-op gate4.
    f.toggle(); f.gui(); f.worker(); f.dispatch(); f.worker(); f.call(SOURCE_APPLY, 0, FRAME)
    f.u.mem_write(FRAME + 5, b'\4')
    # Exercise the actual consumption callback and original gate4 separately;
    # the remaining native format4 frame-render path is outside this fixture.
    f.call(host['symbols']['z7_primary_frame_permission'], FRAME, 1); f.call(GATE, 4)
    check('format4-bypass-does-not-replace-last-meaningful-frame-format', f.read(record + 56) == 0)
    calls = f.frame_calls; f.toggle(); f.gui(); f.worker(); f.dispatch(); f.worker()
    check('no-frame-restoration-after-format4-still-programs-native-baseline',
          f.frame_calls == calls and f.lease() == 0 and f.parameters() == enabled_baseline and f.control() & 1 == 1)
    f.u.mem_write(FRAME + 5, b'\0')

    # A movie/output departure has no photo baseline restoration in that new
    # context. It disables the owned plane and keeps the original baseline.
    f.toggle(); f.gui(); f.worker(); f.dispatch(); f.worker(); f.call(SOURCE_APPLY, 0, FRAME)
    calls = f.frame_calls; f.write(0xa24e1e00, 1); f.gui(); f.worker(); f.dispatch(); f.worker()
    check('mode-exit-consumer-disables-owned-plane-without-frame-and-keeps-baseline',
          f.frame_calls == calls and f.control() & 1 == 0 and f.read(NATIVE + 0x28) == 0 and f.lease() == 1 and f.lease(28) == 1)
    f.toggle(); f.gui(); f.write(0xa24e1e00, 0); f.gui(); f.worker(); f.dispatch(); f.worker()
    check('return-off-restores-original-native-permission-and-baseline-without-frame',
          f.frame_calls == calls and f.parameters() == enabled_baseline and f.control() & 1 == 1 and f.lease() == 0)

    f.toggle(); f.gui(); f.worker(); f.dispatch(); f.worker(); f.call(SOURCE_APPLY, 0, FRAME)
    calls = f.frame_calls; f.toggle(); f.gui(); f.worker()  # Pending old restore.
    f.write(0xa24e1e00, 1); newer = f.convert(2, 202); releases = f.counter('native_releases')
    f.native(newer)
    check('incoming-native-update-quiesces-old-owned-plane-before-foreign-copy',
          f.frame_calls == calls and f.control() & 1 == 0 and f.parameters() == newer and f.lease() == 0 and f.counter('native_releases') == releases + 1)
    programs = len(f.programs)
    check('queued-old-restore-cannot-clobber-new-native-parameters-or-plane',
          f.dispatch() == 0 and f.parameters() == newer and len(f.programs) == programs)
    f.worker(); f.write(0xa24e1e00, 0); f.gui()
    f.toggle(); f.gui(); f.worker(); f.dispatch(); f.worker(); f.call(SOURCE_APPLY, 0, FRAME)
    check('new-native-generation-can-capture-fresh-original-frame-input', f.read(record + 60) == 1 and f.control() & 1 == 1)
    # A menu can invalidate the live epoch before GUI publication. Worker
    # restoration operates only in the native consumer and invokes no frame.
    calls = f.frame_calls; f.write(0xa2c41008, 1); f.worker(); f.dispatch(); f.worker()
    check('menu-entry-without-gui-or-frame-restores-native-baseline',
          f.frame_calls == calls and f.lease() == 0 and f.parameters() == newer and f.control() & 1 == 1)
    f.write(0xa2c41008, 0); f.gui(); f.worker(); f.dispatch(); f.worker(); f.call(SOURCE_APPLY, 0, FRAME)
    calls = f.frame_calls; f.write(0xa181c764, 2); f.u.mem_write(0xa180a568, b'\1'); f.worker(); f.dispatch(); f.worker()
    check('output-exit-without-gui-or-frame-disables-photo-owned-plane', f.frame_calls == calls and f.control() & 1 == 0 and f.lease(28) == 1)
    del f; gc.collect()

    f = CleanupFixture(raw, host, packet, module); baseline = f.start(True, 0)
    record = f.address('z7_highlight_native_frame')
    f.toggle(); f.gui(); f.worker()
    replacement = NATIVE + 0x2900
    f.write(replacement, 0x142); f.write(replacement + 4, 0x4000); f.write(0xa180a578, replacement)
    programs = len(f.programs); parameters = f.parameters(); old_control = f.control()
    check('changed-engine-cancels-cleanup-before-copy-and-never-touches-either-bank',
          f.dispatch() == 0 and f.parameters() == parameters and len(f.programs) == programs and f.control() == old_control and
          f.read(MMIO + 0x4430) == 0 and f.owned('parked') == 1)
    del f; gc.collect()

    f = CleanupFixture(raw, host, packet, module); f.start(True, 0)
    record = f.address('z7_highlight_native_frame'); sequence = f.read(record)
    f.write(record, sequence | 1); f.toggle(); f.gui(); f.worker()
    parameters = f.parameters(); programs = len(f.programs)
    check('busy-native-frame-publication-cancels-cleanup-without-partial-restore',
          f.dispatch() == 0 and f.parameters() == parameters and len(f.programs) == programs and f.owned('parked') == 1)
    # Direct compiled publication tests do not assert a native scheduler model.
    # A failed bounded read cannot expose a partial original-permission record.
    output, source = NATIVE + 0x2a00, NATIVE + 0x2b00
    reader, writer = f.address('highlight_frame_native_read'), f.address('highlight_frame_native_publish')
    f.u.mem_write(output, b'\xa5' * 52)
    check('busy-frame-reader-preserves-entire-output', f.call(reader, output) == 0 and bytes(f.u.mem_read(output, 52)) == b'\xa5' * 52)
    f.write(record, sequence)  # End the explicit injected busy-writer condition.
    # Interrupt a reader after one record word, execute the real publisher on
    # a separate stack, and model a repeated32-bit sequence. Serial must reject
    # the mixed old/new record and retry to a complete new snapshot.
    pending = [False]
    def observe(u, access, address, size, value, context): pending[0] = True
    def pause(u, address, size, context):
        if pending[0]: pending[0] = False; u.emu_stop()
    hook = f.u.hook_add(UC_HOOK_MEM_READ, observe, begin=record + 12, end=record + 15)
    code_hook = f.u.hook_add(UC_HOOK_CODE, pause)
    f.u.ctl_remove_cache(f.base, f.base + module['image_bytes'])
    guards = enter(f, reader, (output,), STACK); saved = f.u.context_save(); prior_sequence = f.read(record)
    check('reader-reaches-explicit-mid-record-interleaving', f.u.reg_read(UC_ARM_REG_PC) != STOP)
    f.u.hook_del(hook); f.u.hook_del(code_hook); f.u.ctl_remove_cache(f.base, f.base + module['image_bytes'])
    changed = struct.pack('<13I', *range(101, 114)); f.u.mem_write(source, changed)
    writer_guards = enter(f, writer, (source,), STACK - 0x10000)
    check('compiled-frame-publisher-preserves-independent-stack', returned(f, STACK - 0x10000, writer_guards) and f.u.reg_read(UC_ARM_REG_R0) == 1)
    f.write(record, prior_sequence); f.u.context_restore(saved)
    f.u.emu_start(f.u.reg_read(UC_ARM_REG_PC) | 1, STOP, timeout=10000000, count=10000000)
    check('frame-serial-rejects-torn-record-even-if-sequence-repeats', returned(f, STACK, guards) and
          f.u.reg_read(UC_ARM_REG_R0) == 1 and bytes(f.u.mem_read(output, 52)) == changed)
    f.write(record, 0xfffffffe); f.write(record + 4, 0xfffffffe)
    check('frame-sequence-wrap-retains-readable-last-serial', f.call(writer, source) == 1 and f.read(record) == 0 and
          f.read(record + 4) == 0xffffffff and f.call(reader, output) == 1 and bytes(f.u.mem_read(output, 52)) == changed)
    f.u.mem_write(output, b'\xa5' * 52)
    check('frame-serial-exhaustion-halts-without-recycling-or-partial-output', f.call(writer, source) == 0 and f.read(record + 8) == 1 and
          f.read(record + 4) == 0xffffffff and f.call(reader, output) == 0 and bytes(f.u.mem_read(output, 52)) == b'\xa5' * 52)
    del f; gc.collect()

    f = CleanupFixture(raw, host, packet, module); f.load()
    baseline = f.convert(2, 213); f.native(baseline)
    f.write(f.engine, 0)  # Unknown engine before first owned application.
    f.call(host['symbols']['z7_display_before_update']); f.gui(); f.worker()
    check('unknown-engine-cancels-initial-application-before-native-parameter-copy',
          f.dispatch() == 0 and f.parameters() == baseline and not f.programs and f.lease() == 0 and f.owned('parked') == 1)
    generation = f.value('z7_highlight_native_parameter_generation')
    newer = f.convert(2, 202); f.native(newer)
    check('unknown-engine-delegates-incoming-native-payload-without-conversion-or-plane-control',
          f.parameters() == newer and not f.programs and f.lease() == 0 and f.value('z7_highlight_native_parameter_generation') == generation + 1)
    del f; gc.collect()

    f = CleanupFixture(raw, host, packet, module); baseline = f.start(True, 0)
    f.reject_disable = True; calls = f.frame_calls; before_done = f.counter('done')
    f.toggle(); f.gui(); f.worker(); f.dispatch()
    check('failed-register-readback-parks-without-claiming-successful-plane-restoration',
          f.frame_calls == calls and f.parameters() == baseline and f.control() & 1 == 1 and f.counter('done') == before_done and
          f.counter('failed') == 1 and f.owned('parked') == 1 and f.lease() == 1)
    del f; gc.collect()
    return dict(passed=True, checks=checks, host_sha256=host['main_payload_sha256'], module_sha256=module['module_sha256'],
                consumer_no_frame_restore_disable_and_native_update_quiescence_connected=True,
                actual_native_driver_mmio_register_effects_verified=True, original_native_permission_preserved=True,
                native_writer_context_engine_lifetime_serialization_assumed=True,
                kernel_filesystem_ui_surfaces_colors_engine_descriptors_and_scheduling_supplied=True,
                physical_display_pixels_allocation_pin_camera_or_card_verified=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True); p.add_argument('--module', type=Path, required=True)
    p.add_argument('--stock-main', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--owned-regression', action='store_true', help='Also execute all36 existing owned checks with admitted engine fixture')
    a = p.parse_args(); out = a.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists(): p.error('Choose a new private output file')
    if hashlib.sha256(a.stock_main.read_bytes()).hexdigest() != STOCK_SHA: p.error('Exact stock main required')
    host = json.loads((a.build / 'module-host.emulator.json').read_text(encoding='utf-8'))
    module = json.loads((a.module / 'module.json').read_text(encoding='utf-8'))
    raw, packet = (a.build / 'module-host.emulator.main.bin').read_bytes(), (a.module / 'Z7APP.BIN').read_bytes()
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        p.error('Exact host/module required')
    admitted = module.get('kind') in ('original-Z7-display-highlight-cleanup-diagnostic', 'original-Z7-display-highlight-cached-diagnostic',
                                    'original-Z7-display-highlight-coordinated-diagnostic')
    if (not host.get('frame_permission_hooks') or not admitted or
        module['api_minimum_bytes'] > host.get('api_bytes', 0) or
        (module['api_minimum_bytes'] >= 60 and not host.get('cached_frame_permission_hooks')) or
        (module['api_minimum_bytes'] == 64 and not host.get('owned_frame_coordination_hooks'))):
        p.error('Explicit compatible cleanup profile and host required')
    result = audit(raw, host, packet, module)
    if a.owned_regression:
        import audit_z7_highlight_owned as owned
        previous = owned.OwnedFixture
        try:
            owned.OwnedFixture = AdmittedOwnedFixture
            result['owned_regression_checks'] = owned.audit(raw, host, packet, module)['checks']
        finally:
            owned.OwnedFixture = previous
    result['source_sha256'] = {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in (
        'tools/audit_z7_highlight_cleanup.py', 'tools/audit_z7_highlight_owned.py', 'z7-native-modules/examples/display_highlight_cleanup_policy.h',
        'z7-native-modules/examples/display_highlight_owned_policy.h', 'z7-native-modules/examples/display_highlight_context_policy.h')}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']), owned_regression_checks=len(result.get('owned_regression_checks', [])))))


if __name__ == '__main__': main()
