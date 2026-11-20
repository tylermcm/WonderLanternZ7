"""Execute API52 filtering and native caller/parameter/completion handoff.

SPDX-License-Identifier: MIT. Native source/packet logic and module callbacks
execute with supplied kernel/filesystem/UI/palette and explicit task scheduling.
No physical output, source flag override, owned request or restoration claimed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_PC
from audit_splash_image import NativePNG, STOCK_SHA, MEM, STACK, STOP, ARGUMENTS
from audit_z7_highlight_host import HighlightHostFixture
from audit_z7_highlight_epoch import EpochProfileFixture, NATIVE
from audit_z7_highlight_submission import enter, returned
from audit_z7_highlight_converter import request
from audit_z7_settings_files import PATHS
from audit_z7_settings_storage import record
from audit_z7_display_persistence import PersistenceFixture
from build_z7_module import ROOT, build
from build_z7_module_host import STATE, CURSOR, ZIG

PACKET, PAYLOAD, PALETTE = NATIVE + 0x2000, NATIVE + 0x2100, NATIVE + 0x4000
CALLER_STACK = 0xa251f000


class ParameterHostFixture(HighlightHostFixture):
    def __init__(self, raw, report, packet, metadata):
        super().__init__(raw, report, packet, metadata)
        self.u.mem_map(0xa24e1000, 0x1000)
        self.u.mem_map(NATIVE, 0x5000)
        self.write(0xa24e1e00, 0)

    def hook(self, u, address, size, context):
        if address in (0x10170944, 0x1017093e) and u.reg_read(UC_ARM_REG_R0) == 0xa29dbf0c:
            self.ret(1)  # Supplied workspace lock; allocator arithmetic executes.
            return
        super().hook(u, address, size, context)


def host_audit(raw, host, packet, metadata, failed, failed_metadata, check):
    f = ParameterHostFixture(raw, host, packet, metadata)
    f.write(STATE - 4, 0xc3c3c3c3)
    f.write(STATE + 272, 0xc3c3c3c3)
    check('api52-native-workspace-hook-reserves320-aligned-bytes-for272-byte-state', f.call(0x101e3d94) == STATE and f.read(CURSOR) == STATE + 320)
    check('api52-cold-state-prefix-and-tail-guards-and-neighbors', f.words()[60:] == (0xa5a5a5a5,) * 4 and
          f.read(STATE + 264) == f.read(STATE + 268) == 0xa5a5a5a5 and
          f.read(STATE - 4) == f.read(STATE + 272) == 0xc3c3c3c3 and f.read(STATE + 256) == f.read(STATE + 260) == 0)
    check('api52-cold-continuation-preserves-original-volatile-state', f.heap_observation ==
          dict(r0=STATE, r1=CURSOR, r2=0x22334455, r3=0x66778899, flags=0xf8000000))
    starts = [f.call(0x101e3dac, size) for size in (1, 63, 64, 65)]
    check('original-native-allocator-keeps-every-following-workspace-allocation64-byte-aligned',
          starts == [STATE + n for n in (320, 384, 448, 512)] and all(p % 64 == 0 for p in starts) and f.read(CURSOR) == STATE + 640)
    f = ParameterHostFixture(raw, host, packet, metadata)
    check('api52-init-registration-checks-prerequisite-null-even-bss-foreign-duplicate', f.load() == 8 and f.read(f.address('z7_ph_mask')) == 127)
    check('api52-late-registration-rejected', f.call(f.address('z7_ph_late')) == 0)

    def calls(): return f.read(f.address('z7_ph_calls'))
    def reset():
        f.write(0xa24e1e00, 0)
        f.u.mem_write(0xa180a568, b'\0')
        f.u.mem_write(0xa1d68e54, b'\3')
        f.u.mem_write(PAYLOAD - 16, b'\xa5' * 136)
        f.write(PAYLOAD, 0)
        f.u.mem_write(PACKET, struct.pack('<7I', 0x11111111, 0x22222222, 0x33333333, 0, 0x42060007, PAYLOAD, 0))
    for selector, command, phase in ((0, 0x42060007, 3), (1, 0x42062007, 3),
                                     (0, 0x42060007, 4), (1, 0x42062007, 4)):
        reset()
        f.u.mem_write(0xa180a568, bytes([selector]))
        f.u.mem_write(0xa1d68e54, bytes([phase]))
        f.write(PACKET + 16, command)
        before, count = bytes(f.u.mem_read(PACKET, 28)), calls()
        check(f'api52-selector{selector}-phase{phase}-callback-precedes-real-native-copy-and-ack', f.call(0x10239840, PACKET) == 1 and
              calls() == count + 1 and f.read(f.address('z7_ph_command')) == command and
              f.read(PAYLOAD) == f.read(MEM + 0x1000 + 0x28) == f.read(PAYLOAD + 100) == 1)
        check(f'api52-selector{selector}-phase{phase}-descriptor-and-source-padding-preserved', bytes(f.u.mem_read(PACKET, 28)) == before and
              bytes(f.u.mem_read(PAYLOAD - 16, 16)) == b'\xa5' * 16 and bytes(f.u.mem_read(PAYLOAD + 104, 16)) == b'\xa5' * 16)
    cases = (
        ('bank1', PACKET + 16, 0x42061007, False), ('other-command', PACKET + 16, 0x42060008, False),
        ('wrong-selector', 0xa180a568, 1, True), ('invalid-selector', 0xa180a568, 2, True),
        ('movie', 0xa24e1e00, 1, False), ('unknown-mode', 0xa24e1e00, 2, False),
        ('service0', 0xa1d68e54, 0, True), ('service1', 0xa1d68e54, 1, True),
        ('service2', 0xa1d68e54, 2, True), ('service5', 0xa1d68e54, 5, True),
        ('unaligned-payload', PACKET + 20, PAYLOAD + 1, False), ('null-payload', PACKET + 20, 0, False),
        ('noncamera-payload', PACKET + 20, MEM + 0x1000, False),
        ('missing-ack-bounds', PACKET + 20, 0xc0000000 - 100, False), ('invalid-enable', PAYLOAD, 2, False),
        ('reentrant-claim', STATE + 260, 1, False))
    for name, address, value, byte in cases:
        reset()
        if byte: f.u.mem_write(address, bytes([value]))
        else: f.write(address, value)
        count, before = calls(), bytes(f.u.mem_read(PAYLOAD, 104))
        notices = f.read(f.address('z7_ph_notices'))
        notice = name in ('movie', 'unknown-mode', 'service1', 'service2')
        check(name + '-exposes-no-writable-data-and-delegates-payload-unchanged',
              f.call(host['symbols']['z7_highlight_consumer_enter'], PACKET) == 0 and calls() == count + int(notice) and
              f.read(f.address('z7_ph_notices')) == notices + int(notice) and bytes(f.u.mem_read(PAYLOAD, 104)) == before)
        f.write(STATE + 260, 0)
    for name, pointer in (('null-packet', 0), ('unaligned-packet', PACKET + 1), ('noncamera-packet', MEM + 0x1000)):
        reset(); count = calls()
        check(name + '-does-not-enter-parameter-callback', f.call(host['symbols']['z7_highlight_consumer_enter'], pointer) == 0 and calls() == count)
    reset(); count = calls()
    check('registered-owned-descriptor-never-enters-foreign-parameter-callback',
          f.call(host['symbols']['z7_highlight_consumer_enter'], f.address('descriptor')) == 3 and calls() == count)
    reset(); count = calls()
    f.write(f.address('z7_ph_recurse'), 1); f.write(f.address('z7_ph_packet'), PACKET)
    check('parameter-callback-reentry-delegates-native-without-recursive-module-call', f.call(0x10239840, PACKET) == 1 and calls() == count + 1)
    for offset in (264, 268):
        reset(); count = calls(); f.write(STATE + offset, 0)
        check(f'extended-guard{offset}-rejects-parameter-dispatch', f.call(host['symbols']['z7_highlight_consumer_enter'], PACKET) == 0 and calls() == count)
        f.write(STATE + offset, 0xa5a5a5a5)
    f = ParameterHostFixture(raw, host, failed, failed_metadata)
    check('failed-init-clears-prefix-and-parameter-pointers-before-free', f.load() == 7 and not f.live and
          f.words()[53:60] == (0,) * 7 and f.read(STATE + 256) == f.read(STATE + 260) == 0)


class ParameterProfileFixture(EpochProfileFixture):
    def __init__(self, raw, host, packet, files):
        super().__init__(raw, host, packet, files)
        for address in (0xa1d5f000, 0xa1f13000, 0xa1f18000, NATIVE + 0x4000, 0xa2510000):
            self.u.mem_map(address, 0x10000 if address == 0xa2510000 else 0x1000)
        self.write(0xa1d5f580, 0x12300001)
        self.write(0xa1f1353c, 0x12300002)
        self.write(0xa1f18fac, PALETTE)
        self.u.mem_write(PALETTE, struct.pack('<256I', *[i << 24 for i in range(256)]))
        self.queued, self.bits, self.wait_pending = [], 0, None
        self.parameter_startup = []

    def hook(self, u, address, size, context):
        if address in (0x10170bee, 0x10170be8, 0x10170c72) and u.reg_read(UC_ARM_REG_R0) == 0xa1f1353c:
            # Bypass the composed histogram fixture's unrelated event model.
            # Execute these ORIGINAL native wrappers down to supplied kernels.
            NativePNG.hook(self, u, address, size, context)
            return
        if address == 0x100363cc and u.reg_read(UC_ARM_REG_R0) == 0x12300001:
            self.queued.append(u.reg_read(UC_ARM_REG_R1)); self.ret(0); return
        if address == 0x10035e94 and u.reg_read(UC_ARM_REG_R0) == 0x12300002:
            self.bits &= u.reg_read(UC_ARM_REG_R1); self.ret(0); return
        if address == 0x10036334 and u.reg_read(UC_ARM_REG_R0) == 0x12300002:
            self.bits |= u.reg_read(UC_ARM_REG_R1); self.ret(0); return
        if address == 0x10036504 and u.reg_read(UC_ARM_REG_R0) == 0x12300002:
            _, bits, mode, output = (u.reg_read(r) for r in ARGUMENTS)
            if mode != 0: raise AssertionError('Unexpected native wait mode')
            if self.bits & bits:
                self.write(output, self.bits & bits); self.wait_pending = None; self.ret(0)
            else:
                self.wait_pending = (bits, self.read(u.reg_read(UC_ARM_REG_SP)))
                u.emu_stop()
            return
        if address == 0x1027beae and hasattr(self, 'parameter_startup'):
            p = u.reg_read(UC_ARM_REG_R0)
            if bytes(u.mem_read(p + 0x9c, 1)) == b'\5' and self.words()[19]:
                path = self.cstring(int.from_bytes(u.mem_read(p + 16, 4), 'little'))
                if path in PATHS: self.parameter_startup.append(bool(self.read(STATE + 256)))
        super().hook(u, address, size, context)


def profile_audit(raw, host, packet, module, check):
    configured = (1, 15, 9, 0, 4, 8, 255, 0, 0, 255)
    f = ParameterProfileFixture(raw, host, packet, {PATHS[0]: record(configured, 1)})
    status = f.call(host['symbols']['z7_module_load_once'], STATE)
    f.base = f.words()[12]; f.setword(40, status)
    symbols = module['symbols']
    def addr(name): return f.base + symbols[name]
    def value(name): return f.read(addr('z7_highlight_parameter_' + name))
    f.focal_object_global = addr('z7_focal_object'); f.focal_renderer = addr('focal_painter')
    check('api52-full-profile-registers-parameter-callback-before-settings-io', status == 8 and f.parameter_startup == [True, True])
    f.call(host['symbols']['z7_display_before_update'])
    f.u.mem_write(0xa201d80c, bytes(f.u.mem_read(0xa201d4d0, 0x33c)))
    f.call(host['symbols']['z7_display_after_gui_update'])
    check('parameter-profile-publishes-current-photo-epoch', f.read(addr('z7_highlight_gui_epoch')) == 1)
    expected_request, expected = NATIVE + 0x2300, NATIVE + 0x2400
    f.u.mem_write(expected_request, request(1, 1, 248)); f.u.mem_write(expected, bytes(100))
    f.call(0x1034fe22, expected, expected_request, 1)
    converted = bytes(f.u.mem_read(expected, 100))
    gui = NATIVE + 0x2500
    for enabled in (0, 1):
        incoming = request(1, 2 if enabled else 0, 213 if enabled else 248)
        f.u.mem_write(gui, incoming)
        guards = enter(f, 0x1034ff1e, (1, 0, gui), CALLER_STACK)
        label = f'native-input-enabled{enabled}'
        check(label + '-caller-queues-and-blocks-at-kernel-event-wait', f.u.reg_read(UC_ARM_REG_PC) == 0x10036504 and
              len(f.queued) == enabled + 1 and f.wait_pending == (0x20, 0xffffffff))
        descriptor = f.queued[-1]; payload = f.read(descriptor + 20)
        before = bytes(f.u.mem_read(descriptor, 28))
        initial = bytes(f.u.mem_read(payload, 100))
        check(label + '-original-conversion-differs-from-feature-request', initial != converted and
              f.read(payload) == enabled and payload + 100 == descriptor and (enabled or initial == bytes(100)))
        context = f.u.context_save()
        f.call(0x10239840, descriptor)
        check(label + '-actual-hook-converts-before-native-copy-and-ack', value('count') == enabled + 1 and value('epoch') == 1 and value('input_enabled') == enabled and
              bytes(f.u.mem_read(payload, 100)) == converted and bytes(f.u.mem_read(NATIVE + 0x28, 100)) == converted and f.read(payload + 100) == 1)
        check(label + '-descriptor-callback-source-context-preserved-except-original-overlap-ack',
              bytes(f.u.mem_read(descriptor + 4, 24)) == before[4:] and f.bits == 0x20)
        f.u.context_restore(context)
        f.u.emu_start(f.u.reg_read(UC_ARM_REG_PC) | 1, STOP, timeout=10000000, count=10000000)
        check(label + '-caller-completes-with-original-stack-callee-registers-and-gui-request', returned(f, CALLER_STACK, guards) and
              f.u.reg_read(UC_ARM_REG_R0) == 1 and f.wait_pending is None and bytes(f.u.mem_read(gui, 36)) == incoming)
    # Full-profile exclusions: actual native consumer still copies the original
    # caller payload and acknowledges it; the module leaves it byte-identical.
    for name, location, bad in (('menu', 0xa2c41008, 1), ('mode', 0xa24e1e00, 1),
                               ('palette', 0xa1f18fac, 0), ('odd-settings', addr('z7_settings_revision'), 1)):
        old = f.read(location); f.write(location, bad)
        original = converted if name == 'menu' else bytes(100)
        f.u.mem_write(PAYLOAD, original + bytes(4)); f.u.mem_write(PACKET, struct.pack('<7I', 0, 0, 0, 0, 0x42060007, PAYLOAD, 0))
        count = value('count')
        generation = f.read(addr('z7_highlight_native_parameter_generation'))
        check(name + '-preserves-native-payload-completion-and-invalidates-prior-ownership', f.call(0x10239840, PACKET) == 1 and
              bytes(f.u.mem_read(PAYLOAD, 100)) == original and f.read(PAYLOAD + 100) == 1 and value('count') == count and
              f.read(addr('z7_highlight_native_parameter_generation')) == generation + 1 and value('epoch') == 0)
        f.write(location, old)
    f.write(addr('z7_settings_view'), 1); f.write(addr('z7_settings_preset'), 0)
    f.u.mem_write(0xa1833548 + 22, struct.pack('<2H', 5, 0)); f.call(addr('sm_activate'))
    f.u.mem_write(0xa201d80c, bytes(f.u.mem_read(0xa201d4d0, 0x33c)))
    f.call(host['symbols']['z7_display_after_gui_update'])
    f.u.mem_write(PAYLOAD, bytes(104)); f.u.mem_write(PACKET, struct.pack('<7I', 0, 0, 0, 0, 0x42060007, PAYLOAD, 0))
    count = value('count')
    check('actual-menu-checkbox-off-delegates-native-parameters-after-republication', f.call(0x10239840, PACKET) == 1 and
          bytes(f.u.mem_read(PAYLOAD, 100)) == bytes(100) and f.read(PAYLOAD + 100) == 1 and value('count') == count)
    f.write(addr('z7_highlight_native_parameter_generation'), 0xffffffff)
    f.u.mem_write(PAYLOAD, bytes(104))
    check('native-update-generation-exhaustion-never-recycles-ownership-identity', f.call(0x10239840, PACKET) == 1 and
          f.read(addr('z7_highlight_native_parameter_generation')) == 0xffffffff and value('epoch') == 0 and value('count') == count)
    check('parameter-milestone-does-not-write-frame-permission', bytes(f.u.mem_read(MEM + 0x10000, 0x4b8)) == bytes(0x4b8))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True); p.add_argument('--module', type=Path, required=True)
    p.add_argument('--legacy-build', type=Path, required=True, help='API48 host for early rejection')
    p.add_argument('--runtime-reference', type=Path, help='Previously regression-tested host; require only cold-window differences')
    p.add_argument('--stock-main', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); out = a.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists(): p.error('Choose a new private output directory')
    if not all((a.legacy_build / n).is_file() for n in ('module-host.emulator.json', 'module-host.emulator.main.bin')):
        p.error('--legacy-build must name a host bundle')
    if hashlib.sha256(a.stock_main.read_bytes()).hexdigest() != STOCK_SHA: p.error('Exact stock main required')
    raw = (a.build / 'module-host.emulator.main.bin').read_bytes(); host = json.loads((a.build / 'module-host.emulator.json').read_text())
    packet = (a.module / 'Z7APP.BIN').read_bytes(); module = json.loads((a.module / 'module.json').read_text())
    if not host.get('parameter_hooks') or host.get('api_bytes') != 52 or host.get('state_bytes') != 272 or host.get('workspace_reserved_bytes') != 320:
        p.error('API52 parameter host with aligned workspace reservation required')
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']: p.error('Artifact fingerprint mismatch')
    out.mkdir(parents=True)
    source = ROOT / 'z7-native-modules/examples/parameters_host_probe.c'
    probe, metadata = build(source, zig=ZIG)
    failed_source = out / 'failed.c'; failed_source.write_text('#define Z7_PARAMETER_INIT_FAIL 1\n#include "' + source.as_posix() + '"\n', encoding='utf-8', newline='\n')
    failed, failed_metadata = build(failed_source, zig=ZIG)
    for name, binary, report in (('probe', probe, metadata), ('failed', failed, failed_metadata)):
        (out / (name + '.BIN')).write_bytes(binary)
        (out / (name + '.json')).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    checks = []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    reference = None
    if a.runtime_reference:
        reference = json.loads((a.runtime_reference / 'module-host.emulator.json').read_text())
        reference_raw = (a.runtime_reference / 'module-host.emulator.main.bin').read_bytes()
        cold = int(host['cold'], 16)
        changes = [i for i, (x, y) in enumerate(zip(reference_raw, raw)) if x != y]
        check('regression-reference-runtime-and-all-noncold-bytes-identical',
              hashlib.sha256(reference_raw).hexdigest() == reference['main_payload_sha256'] and
              reference['host_sha256'] == host['host_sha256'] and reference['symbols'] == host['symbols'] and
              len(reference_raw) == len(raw) and changes and all(cold <= 0x10020000 + i < cold + 160 for i in changes))
    host_audit(raw, host, probe, metadata, failed, failed_metadata, check)
    profile_audit(raw, host, packet, module, check)
    legacy = json.loads((a.legacy_build / 'module-host.emulator.json').read_text())
    f = PersistenceFixture((a.legacy_build / 'module-host.emulator.main.bin').read_bytes(), legacy, packet)
    check('api48-host-rejects-parameter-profile-before-settings-or-menu-preparation',
          f.call(legacy['symbols']['z7_module_load_once'], STATE) == 7 and not f.live and
          not any(event[0] in ('open', 'create', 'write') for event in f.file_events) and bytes(f.u.mem_read(0xa1833548, 44)) == bytes(44))
    result = dict(passed=True, checks=checks, host_sha256=host['main_payload_sha256'], module_sha256=module['module_sha256'],
        actual_native_caller_converter_dispatch_copy_ack_completion_execute=True,
        kernel_filesystem_ui_palette_and_task_handoff_supplied=True, api_bytes=52, state_bytes=272, workspace_reserved_bytes=320,
        native_frame_permission_writes=False, owned_requests_and_restoration=False, warning_pixels=False, camera_card_access=False)
    if reference:
        result['runtime_reference_sha256'] = reference['main_payload_sha256']
        result['runtime_reference_delta_addresses'] = [hex(0x10020000 + i) for i in changes]
    names = ('tools/audit_z7_parameters.py', 'tools/build_z7_module_host.py', 'tools/audit_z7_module_host.py',
             'z7-native-modules/host/z7_380.c', 'z7-native-modules/host/z7_380.h', 'z7-native-modules/sdk/parameters.h',
             'z7-native-modules/examples/parameters_host_probe.c', 'z7-native-modules/examples/display_highlight_context_policy.h')
    result['source_sha256'] = {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in names}
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(checks))))


if __name__ == '__main__': main()
