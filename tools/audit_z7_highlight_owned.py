"""Execute full-profile owned apply/restore/disable and native-update ownership.

SPDX-License-Identifier: MIT. Native packet/queue/conversion/copy/ack/completion
execute with supplied kernel/filesystem/UI/palette and explicit task handoff.
Frame flags remain native; no pixels, immediate frame cleanup or hardware proof.
"""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_PC
from audit_splash_image import STOCK_SHA, MEM, STACK, STOP
from audit_z7_parameters import ParameterProfileFixture, NATIVE, PACKET, PAYLOAD, PALETTE, CALLER_STACK
from audit_z7_highlight_submission import enter, returned
from audit_z7_highlight_converter import request
from audit_z7_settings_files import PATHS
from audit_z7_settings_storage import record
from build_z7_module_host import ROOT, STATE


class OwnedFixture(ParameterProfileFixture):
    pause_send = False

    def __init__(self, raw, host, packet, module):
        configured = (1, 15, 9, 0, 4, 8, 255, 0, 0, 255)
        super().__init__(raw, host, packet, {PATHS[0]: record(configured, 1)})
        self.u.mem_map(NATIVE + 0x5000, 0x1000)
        self.module = module

    def hook(self, u, address, size, context):
        if address == 0x100363cc and u.reg_read(UC_ARM_REG_R0) == 0x12300001 and self.pause_send:
            self.waiting_packet = u.reg_read(UC_ARM_REG_R1)
            u.emu_stop(); return
        super().hook(u, address, size, context)

    def address(self, name): return self.base + self.module['symbols'][name]
    def value(self, name): return self.read(self.address(name))
    def owned(self, name): return self.value('z7_highlight_owned_' + name)
    def lease(self, offset=12): return self.read(self.address('z7_highlight_lease') + offset)
    def worker(self): self.call(self.report['symbols']['z7_module_worker_tick'])
    def gui(self):
        self.u.mem_write(0xa201d80c, bytes(self.u.mem_read(0xa201d4d0, 0x33c)))
        self.call(self.report['symbols']['z7_display_after_gui_update'])
    def load(self):
        status = self.call(self.report['symbols']['z7_module_load_once'], STATE)
        self.base = self.words()[12]; self.setword(40, status)
        if status != 8: raise AssertionError(('Module initialization', status))
        self.focal_object_global = self.address('z7_focal_object')
        self.focal_renderer = self.address('focal_painter')
    def convert(self, pattern=1, threshold=248):
        self.u.mem_write(NATIVE + 0x2300, request(1, pattern, threshold))
        self.u.mem_write(NATIVE + 0x2400, bytes(100))
        self.call(0x1034fe22, NATIVE + 0x2400, NATIVE + 0x2300, 1)
        return bytes(self.u.mem_read(NATIVE + 0x2400, 100))
    def native(self, parameters):
        self.u.mem_write(PAYLOAD, parameters + bytes(4))
        self.u.mem_write(PACKET, struct.pack('<7I', 0, 0, 0, 0, 0x42060007, PAYLOAD, 0))
        result = self.call(0x10239840, PACKET)
        if result != 1 or self.read(PAYLOAD + 100) != 1: raise AssertionError('Native parameter copy/completion')
    def parameters(self): return bytes(self.u.mem_read(NATIVE + 0x28, 100))
    def toggle(self):
        self.write(self.address('z7_settings_view'), 1); self.write(self.address('z7_settings_preset'), 0)
        self.u.mem_write(0xa1833548 + 22, struct.pack('<2H', 5, 0))
        self.call(self.address('sm_activate'))
    def dispatch(self): return self.call(0x10239840, self.queued[-1])


def audit(raw, host, packet, module):
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Host/module fingerprints must match')
    checks = []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    f = OwnedFixture(raw, host, packet, module); f.load()
    baseline = f.convert(2, 213)
    f.native(baseline)  # Initial native parameters before first GUI publication.
    f.call(host['symbols']['z7_display_before_update']); f.gui()
    before_files = list(f.file_events)
    f.worker()
    r = f.address('z7_highlight_owned_request')
    check('full-worker-queues-owned-zero-payload-without-native-gui-wait', len(f.queued) == 1 and
          bytes(f.u.mem_read(r + 28, 104)) == bytes(104) and f.wait_pending is None and f.parameters() == baseline)
    f.u.mem_write(NATIVE + 0x5000, struct.pack('<256I', *[((255 - i) << 24) | i for i in range(256)]))
    f.write(0xa1f18fac, NATIVE + 0x5000)
    expected = f.convert()
    check('owned-consumer-converts-current-palette-and-native-handler-applies-and-acks',
          f.dispatch() == 1 and f.parameters() == expected and f.read(r + 128) == 1 and f.owned('applied') == 1)
    check('owned-lease-retains-exact-enabled-native-baseline', f.lease() == 1 and
          bytes(f.u.mem_read(f.address('z7_highlight_lease') + 60, 100)) == baseline)
    check('owned-dispatch-does-not-increment-native-update-generation', f.value('z7_highlight_native_parameter_generation') == 1)
    f.worker()
    check('settled-owned-application-reaps-without-repeated-queueing', len(f.queued) == 1 and f.read(r + 132) == 0 and f.file_events == before_files)
    f.toggle(); f.worker()
    check('checkbox-off-queues-restoration-without-touching-native-parameters-yet', len(f.queued) == 2 and f.parameters() == expected)
    f.gui()  # Changes publication epoch while restoration is pending.
    check('stale-cleanup-epoch-cancels-without-clobbering-owned-state', f.dispatch() == 0 and f.parameters() == expected and f.read(r + 128) == 0)
    f.worker()
    check('cleanup-retries-with-current-epoch-and-restores-exact-native-baseline', len(f.queued) == 3 and f.dispatch() == 1 and
          f.parameters() == baseline and f.lease() == 0 and f.owned('restored') == 1)
    f.worker()
    check('restored-off-state-never-resubmits', len(f.queued) == 3)
    f.toggle(); f.gui(); f.worker(); f.dispatch(); f.worker()
    check('reenabled-epoch-applies-again-without-native-source-packet', f.owned('applied') == 2 and f.parameters() == expected)
    f.toggle(); f.gui(); f.worker()
    pending = f.queued[-1]
    f.native(expected)  # Same bytes, newer native owner. Must invalidate restore.
    check('same-byte-native-update-invalidates-lease', f.lease() == 0 and f.value('z7_highlight_native_parameter_generation') == 2)
    check('pending-restore-cannot-overwrite-new-native-owner-even-with-equal-bytes', f.call(0x10239840, pending) == 0 and
          f.parameters() == expected and f.owned('restored') == 1)
    f.worker()
    count = len(f.queued); f.worker()
    check('native-owner-left-untouched-while-feature-off', len(f.queued) == count and f.parameters() == expected)
    f.toggle(); f.gui(); f.worker(); f.dispatch(); f.worker()
    f.write(0xa24e1e00, 1); f.gui(); f.worker()
    check('mode-exit-queues-disable-rather-than-photo-baseline-restore', f.dispatch() == 1 and f.read(NATIVE + 0x28) == 0 and
          f.lease(28) == 1 and f.owned('disabled') == 1)
    f.worker(); count = len(f.queued); f.worker()
    check('disabled-other-mode-holds-baseline-without-repeated-writes', len(f.queued) == count)
    f.toggle(); f.gui()  # Turn component off while outside the original context.
    f.write(0xa24e1e00, 0); f.gui(); f.worker()
    check('return-to-original-context-off-restores-baseline-and-relinquishes', f.dispatch() == 1 and
          f.parameters() == expected and f.lease() == 0 and f.owned('restored') == 2)
    f.worker(); f.toggle(); f.gui(); f.worker(); f.dispatch(); f.worker()
    f.write(0xa24e1e00, 1); f.gui(); f.worker()
    pending = f.queued[-1]
    native_movie = f.convert(2, 202)
    f.native(native_movie)
    check('new-native-movie-update-is-not-converted-and-relinquishes-lease', f.parameters() == native_movie and f.lease() == 0)
    check('queued-old-disable-cannot-clobber-new-native-movie-parameters', f.call(0x10239840, pending) == 0 and f.parameters() == native_movie)
    check('owned-stage-never-forces-frame-permission', bytes(f.u.mem_read(MEM + 0x10000, 0x4b8)) == bytes(0x4b8))

    # Deferred consumer may run before the worker's kernel send returns.
    del f
    gc.collect()
    g = OwnedFixture(raw, host, packet, module); g.load()
    disabled = bytes(4) + b'\xa5' * 96
    g.native(disabled)
    g.call(host['symbols']['z7_display_before_update']); g.gui()
    g.pause_send = True
    guards = enter(g, host['symbols']['z7_module_worker_tick'], (), CALLER_STACK)
    check('worker-pauses-at-real-queue-send-with-metadata-published', g.u.reg_read(UC_ARM_REG_PC) == 0x100363cc)
    context = g.u.context_save(); g.pause_send = False
    rr = g.address('z7_highlight_owned_request')
    check('early-owned-consumer-applies-with-correct-prepublished-metadata', g.call(0x10239840, g.waiting_packet) == 1 and
          g.owned('applied') == 1 and g.read(rr + 132) == 4 and g.read(rr + 148) == 0)
    check('disabled-native-baseline-is-normalized-without-reading-stale-fields',
          bytes(g.u.mem_read(g.address('z7_highlight_lease') + 60, 100)) == bytes(100))
    g.u.context_restore(context)
    g.u.emu_start(g.u.reg_read(UC_ARM_REG_PC) | 1, STOP, timeout=10000000, count=10000000)
    check('worker-resumes-with-original-stack-and-only-then-permits-reap', returned(g, CALLER_STACK, guards) and g.read(rr + 148) == 1)
    g.worker()
    check('early-consumption-reaps-after-both-returns-without-duplicate-submit', g.read(rr + 132) == 0 and len(g.queued) == 1)
    g.toggle(); g.gui(); g.worker()
    check('normalized-disabled-baseline-restores-to-disabled-zero-record', g.dispatch() == 1 and g.parameters() == bytes(100) and g.lease() == 0)
    # Incoming eligible native traffic is rewritten in place by the optional
    # callback. Its original baseline must supersede earlier owned state.
    g.worker(); g.toggle(); g.gui()
    latest_native = g.convert(2, 217)
    g.native(latest_native)
    latest_owned = g.convert()
    check('eligible-native-update-applies-conversion-and-captures-new-native-baseline',
          g.parameters() == latest_owned and g.lease() == 1 and
          bytes(g.u.mem_read(g.address('z7_highlight_lease') + 60, 100)) == latest_native)
    queued = len(g.queued)
    g.worker()
    check('settled-incoming-native-conversion-needs-no-owned-resubmission', len(g.queued) == queued)
    g.toggle(); g.gui(); g.worker()
    check('off-restores-latest-incoming-native-baseline', g.dispatch() == 1 and g.parameters() == latest_native and g.lease() == 0)
    g.worker(); g.toggle(); g.gui(); g.worker()
    # Open native menu after queueing and before consuming, without a GUI tick.
    g.write(0xa2c41008, 1)
    check('live-menu-entry-cancels-pending-apply-before-another-gui-publication',
          g.dispatch() == 0 and g.parameters() == latest_native and g.lease() == 0)
    g.worker(); g.gui()
    queued = len(g.queued); g.worker()
    check('menu-ineligible-publication-does-not-submit-owned-application', len(g.queued) == queued)
    g.write(0xa2c41008, 0); g.gui(); g.worker()
    check('leaving-menu-allows-current-application', g.dispatch() == 1 and g.parameters() == latest_owned)
    g.worker(); g.write(0xa2c41008, 1); g.worker()
    check('live-menu-entry-restores-baseline-before-another-gui-publication',
          g.dispatch() == 1 and g.parameters() == latest_native and g.lease() == 0)
    g.worker(); g.write(0xa2c41008, 0); g.gui(); g.worker(); g.dispatch(); g.worker()
    g.write(0xa181c764, 2); g.u.mem_write(0xa180a568, b'\1')
    g.worker()
    check('live-output-switch-queues-disable-for-current-selector',
          g.read(g.queued[-1] + 16) == 0x42062007 and g.dispatch() == 1 and g.read(NATIVE + 0x28) == 0 and g.lease(28) == 1)
    g.worker(); queued = len(g.queued); g.gui(); g.worker()
    check('evf-context-holds-disabled-photo-lease-without-repeated-writes', len(g.queued) == queued)
    g.write(0xa181c764, 1); g.u.mem_write(0xa180a568, b'\0'); g.gui(); g.worker()
    check('return-to-lcd-reapplies-with-original-native-baseline-retained',
          g.dispatch() == 1 and g.parameters() == latest_owned and
          bytes(g.u.mem_read(g.address('z7_highlight_lease') + 60, 100)) == latest_native)
    g.worker(); g.toggle(); g.gui(); g.worker()
    check('off-after-output-round-trip-restores-original-native-baseline',
          g.dispatch() == 1 and g.parameters() == latest_native and g.lease() == 0)
    return dict(passed=True, checks=checks, host_sha256=host['main_payload_sha256'], module_sha256=module['module_sha256'],
        full_profile_owned_worker_consumer_native_copy_ack_completion_execute=True,
        native_consumer_serialization_assumed=True, kernel_filesystem_ui_palette_and_explicit_interleavings_supplied=True,
        source_frame_permission_override=False, immediate_pending_cleanup=False, warning_pixels=False, camera_card_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True); p.add_argument('--module', type=Path, required=True)
    p.add_argument('--stock-main', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); out = a.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists(): p.error('Choose a new private output directory')
    if hashlib.sha256(a.stock_main.read_bytes()).hexdigest() != STOCK_SHA: p.error('Exact stock main required')
    host = json.loads((a.build / 'module-host.emulator.json').read_text()); module = json.loads((a.module / 'module.json').read_text())
    result = audit((a.build / 'module-host.emulator.main.bin').read_bytes(), host, (a.module / 'Z7APP.BIN').read_bytes(), module)
    result['source_sha256'] = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
        'tools/audit_z7_highlight_owned.py', 'z7-native-modules/examples/display_highlight_owned_policy.h',
        'z7-native-modules/plugins/highlight_lease.h', 'z7-native-modules/plugins/highlight_request.h')}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__': main()
