"""Execute API56 consumption-time permission, including native deferred replay.

SPDX-License-Identifier: MIT. Native source/frame/gate/conversion execute.
Kernel/FS/UI/context/surface/color/plane boundaries and interleavings supplied.
No actual warning pixels, physical frame fence, camera/card or recovery proof.
"""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R12, UC_ARM_REG_LR, UC_ARM_REG_SP, UC_ARM_REG_CPSR
from audit_splash_image import NativePNG, MEM, STOCK_SHA, SAVED
from audit_z7_parameters import ParameterHostFixture, NATIVE
from audit_z7_module_host import HostFixture
from audit_z7_highlight_owned import OwnedFixture
from audit_z7_highlight_frame_gate import SOURCE_APPLY, FRAME_APPLY, GATE, STATE as OLD_STATE
from build_z7_module import ROOT, build
from build_z7_module_host import STATE, CURSOR, ZIG

FRAME = NATIVE + 0x3000


class FrameHostFixture(ParameterHostFixture):
    def __init__(self, *args):
        self.bridge_samples = []
        super().__init__(*args)

    def hook(self, u, address, size, context):
        if address in (0x1023bab0, 0x1023bab8):
            registers = (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
                         *SAVED, UC_ARM_REG_R12, UC_ARM_REG_LR, UC_ARM_REG_SP)
            self.bridge_samples.append((address, tuple(u.reg_read(r) for r in registers), u.reg_read(UC_ARM_REG_CPSR) & 0xf8000000))
        super().hook(u, address, size, context)


class FrameProfileFixture(OwnedFixture):
    def __init__(self, *args):
        super().__init__(*args)
        for address in (0xa1d5f000, 0xa1d69000, 0xa1d6a000, 0x20140000):
            # Parent profiles already map some pages. Consult mapped regions,
            # rather than catching and hiding unrelated mapping failures.
            if not any(start <= address <= end for start, end, _ in self.u.mem_regions()):
                self.u.mem_map(address, 0x1000)
        self.hardware = []
        self.write(0xa1d6ab80, 0x12300003)
        self.write(0xa180a578, MEM + 0x9000); self.write(MEM + 0x9000, 0x142)
        self.u.mem_write(MEM + 0x6000, struct.pack('<4H', 0x1000, 0x8000, 0xe000, 0))
        self.u.mem_write(0xa1d69351, b'\3')

    def hook(self, u, address, size, context):
        if address == FRAME_APPLY:
            return  # Execute original body instead of epoch fixture's sink.
        if address in (0x10170944, 0x1017093e) and u.reg_read(UC_ARM_REG_R0) == 0xa1d6ab80:
            # Keep the original highlight mutex wrapper; bypass only the
            # unrelated composed histogram fixture's mutex identity model.
            NativePNG.hook(self, u, address, size, context); return
        if address in (0x100361e8, 0x100364dc):
            if u.reg_read(UC_ARM_REG_R0) != 0x12300003: raise AssertionError('Unexpected mutex')
            self.ret(0); return
        if address in (0x10241a0e, 0x1023b7f6, 0x1024147e, 0x1024354e, 0x10243d82):
            args = tuple(u.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2))
            self.hardware.append((address, args))
            self.ret(1 if address == 0x1023b7f6 else MEM + 0x6000 if address == 0x10243d82 else 0)
            return
        super().hook(u, address, size, context)

    def plane(self): return [args[2] for address, args in self.hardware if address == 0x10241a0e]


def audit(raw, host, packet, module, probe, metadata, failed, failed_metadata, legacy):
    checks = []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    f = FrameHostFixture(raw, host, probe, metadata)
    f.write(STATE - 4, 0xc3c3c3c3); f.write(STATE + 288, 0xc3c3c3c3)
    check('api56-cold-clears288-and-reserves320-aligned-bytes', f.call(0x101e3d94) == STATE and f.read(CURSOR) == STATE + 320 and
          all(f.read(STATE + o) == 0xa5a5a5a5 for o in (240, 244, 248, 252, 264, 268, 280, 284)) and
          f.read(STATE - 4) == f.read(STATE + 288) == 0xc3c3c3c3)
    check('api56-cold-preserves-original-continuation-registers-and-flags', f.heap_observation ==
          dict(r0=STATE, r1=CURSOR, r2=0x22334455, r3=0x66778899, flags=0xf8000000))
    check('api56-native-workspace-allocator-remains64-aligned',
          [f.call(0x101e3dac, n) for n in (1, 63, 64, 65)] == [STATE + n for n in (320, 384, 448, 512)])
    # Cold initialization precedes z7_module_boot, which initializes retained_fd.
    # Use the usual prepared-loader fixture for independent registration tests.
    del f; gc.collect()
    f = FrameHostFixture(raw, host, probe, metadata)
    check('api56-register-rejects-prerequisite-null-even-data-foreign-and-duplicate', f.load() == 8 and f.read(f.address('z7_fp_mask')) == 127)
    check('frame-registration-is-init-only', f.call(f.address('z7_fp_late')) == 0)
    filter_address = host['symbols']['z7_primary_frame_permission']
    def calls(): return f.read(f.address('z7_fp_calls'))
    for native in (0, 1):
        for decision in (0, 1, 2, 3, 0xffffffff):
            f.write(f.address('z7_fp_decision'), decision)
            before = calls()
            check(f'native{native}-decision{decision}-bounded-filter-result-and-arguments',
                  f.call(filter_address, FRAME, native) == (1 if decision == 1 else 0 if decision == 2 else native) and calls() == before + 1 and
                  f.read(f.address('z7_fp_frame')) == FRAME and f.read(f.address('z7_fp_native')) == native)
    for name, pointer, permission in (('null', 0, 0), ('unaligned', FRAME + 1, 1), ('outside-camera', MEM, 1),
                                      ('truncated-camera-range', 0xc0000000 - 0x34, 1), ('native-inhibit', FRAME, 2)):
        before = calls()
        check(name + '-delegates-without-callback', f.call(filter_address, pointer, permission) == permission and calls() == before)
    for offset in (264, 268, 280, 284):
        f.write(STATE + offset, 0); before = calls()
        check(f'guard{offset}-delegates-without-callback', f.call(filter_address, FRAME, 1) == 1 and calls() == before)
        f.write(STATE + offset, 0xa5a5a5a5)
    f.u.mem_write(FRAME, b'\1'); before = calls()
    check('unsupported-frame-kind-delegates', f.call(filter_address, FRAME, 1) == 1 and calls() == before)
    f.u.mem_write(FRAME, b'\0'); f.write(STATE + 276, 1); before = calls()
    check('callback-reentry-delegates-without-recursion', f.call(filter_address, FRAME, 1) == 1 and calls() == before)
    f.write(STATE + 276, 0)
    # Execute actual primary-frame entry: callee saves/stack are checked by call.
    # Observe both sides of the inserted bridge to verify live volatile regs and
    # NZCVQ, apart from native overwritten r0/r1, retain their original contract.
    f.write(f.address('z7_fp_decision'), 1)
    incoming = bytes(f.u.mem_read(FRAME, 0x4b8))
    f.write(OLD_STATE + 0x24, 1)
    check('primary-frame-entry-executes-consumption-bridge-and-enables-native-plane',
          f.call(FRAME_APPLY, FRAME, 1) == 1 and f.read(OLD_STATE + 0x20) == f.read(OLD_STATE + 0x1c) == 1 and
          bytes(f.u.mem_read(FRAME, 0x4b8)) == incoming)
    before, after = f.bridge_samples[-2:]
    check('inserted-bridge-preserves-live-registers-stack-and-nzcvq',
          before[0] == 0x1023bab0 and after[0] == 0x1023bab8 and
          before[1][2:] == after[1][2:] and before[2] == after[2] and
          after[1][0] == incoming[5] and after[1][1] == OLD_STATE)
    # No callback / corrupted callback must leave the native frame behavior.
    callback = f.read(STATE + 272); f.write(STATE + 272, callback & ~1); before = calls()
    check('corrupted-resident-callback-delegates', f.call(filter_address, FRAME, 1) == 1 and calls() == before)
    f.write(STATE + 272, callback)
    del f; gc.collect()
    f = ParameterHostFixture(raw, host, failed, failed_metadata)
    check('failed-init-clears-frame-and-parameter-pointers-before-free', f.load() == 7 and not f.live and
          all(f.read(STATE + o) == 0 for o in (256, 260, 272, 276)))
    del f; gc.collect()

    f = FrameProfileFixture(raw, host, packet, module); f.load()
    baseline = f.convert(2, 213); f.native(baseline)
    f.call(host['symbols']['z7_display_before_update']); f.gui(); f.worker(); f.dispatch(); f.worker()
    expected = f.parameters()
    original = bytes(f.u.mem_read(FRAME, 0x4b8))
    check('full-profile-consumption-enables-only-settled-owned-parameters',
          f.call(SOURCE_APPLY, 0, FRAME) == 1 and f.read(NATIVE + 0x1c) == f.read(NATIVE + 0x20) == 1 and
          f.plane()[-1] == 1 and bytes(f.u.mem_read(FRAME, 0x4b8)) == original)
    f.u.mem_write(0xa1d69351, b'\0'); f.hardware.clear()
    check('deferred-source-copy-keeps-native-permission-without-programming-plane',
          f.call(SOURCE_APPLY, 0, FRAME) == 1 and bytes(f.u.mem_read(NATIVE + 0x50c, 0x4b8)) == original and
          bytes(f.u.mem_read(NATIVE + 0x508, 1)) == b'\1' and not f.plane())
    check('forced-deferred-replay-enables-from-current-lease-without-mutating-copy',
          f.call(FRAME_APPLY, NATIVE + 0x50c, 1) == 1 and f.read(NATIVE + 0x20) == 1 and
          bytes(f.u.mem_read(NATIVE + 0x50c, 0x4b8)) == original)
    f.toggle()  # No GUI publication or worker tick before replay.
    f.hardware.clear()
    check('checkbox-off-immediately-inhibits-old-pending-replay-before-gui-and-worker',
          f.call(FRAME_APPLY, NATIVE + 0x50c, 1) == 1 and f.read(NATIVE + 0x20) == f.read(NATIVE + 0x1c) == 0 and
          f.plane() == [0] and f.parameters() == expected and bytes(f.u.mem_read(NATIVE + 0x50c, 0x4b8)) == original)
    # A native1 frame also must not render stale owned parameters while Off.
    f.write(FRAME + 0x34, 1)
    check('off-inhibits-native-one-while-owned-parameters-await-restoration',
          f.call(FRAME_APPLY, FRAME, 1) == 1 and f.read(NATIVE + 0x20) == 0 and f.read(FRAME + 0x34) == 1)
    f.gui(); f.worker(); f.dispatch(); f.worker()
    check('after-restoration-native-one-and-original-baseline-are-delegated',
          f.parameters() == baseline and f.call(FRAME_APPLY, FRAME, 1) == 1 and f.read(NATIVE + 0x1c) == 1)
    f.toggle(); f.gui(); f.worker(); f.dispatch(); f.worker()
    for name, address, value, byte in (('menu', 0xa2c41008, 1, False), ('movie', 0xa24e1e00, 1, False),
                                       ('output', 0xa181c764, 2, False), ('preset-cycle', f.address('z7_preset_cycles'), 999, False)):
        prior = bytes(f.u.mem_read(address, 1 if byte else 4))
        f.u.mem_write(address, bytes([value]) if byte else struct.pack('<I', value))
        check(name + '-change-inhibits-replay-before-gui-or-worker', f.call(FRAME_APPLY, FRAME, 1) == 1 and f.read(NATIVE + 0x20) == 0)
        f.u.mem_write(address, prior)
    check('return-to-current-context-enables-without-mutating-native-frame',
          f.call(FRAME_APPLY, FRAME, 1) == 1 and f.read(NATIVE + 0x20) == 1 and f.read(FRAME + 0x34) == 1)
    prior_palette = f.read(0xa1f18fac)
    f.write(0xa1f18fac, NATIVE + 0x5000)
    check('palette-change-inhibits-unreconverted-owned-parameters',
          f.call(FRAME_APPLY, FRAME, 1) == 1 and f.read(NATIVE + 0x20) == 0)
    f.write(0xa1f18fac, prior_palette)
    lease = f.address('z7_highlight_lease'); sequence = f.read(lease)
    f.write(lease, sequence | 1)
    check('busy-lease-publication-inhibits-instead-of-rendering-unverified-owned-parameters',
          f.call(FRAME_APPLY, FRAME, 1) == 1 and f.read(NATIVE + 0x20) == 0)
    f.write(lease, sequence); f.write(lease + 8, 1)
    check('halted-lease-publication-inhibits-unverified-owned-parameters',
          f.call(FRAME_APPLY, FRAME, 1) == 1 and f.read(NATIVE + 0x20) == 0)
    del f; gc.collect()
    old = json.loads((legacy / 'module-host.emulator.json').read_text(encoding='utf-8'))
    old_raw = (legacy / 'module-host.emulator.main.bin').read_bytes()
    if old.get('api_bytes') != 52 or hashlib.sha256(old_raw).hexdigest() != old['main_payload_sha256']:
        raise ValueError('Exact API52 legacy host required')
    f = HostFixture(old_raw, old, packet)
    menu = bytes(f.u.mem_read(0xa1833548, 44))
    check('api52-host-rejects-frame-profile-before-native-menu-preparation',
          f.call(old['symbols']['z7_module_load_once'], STATE) == 7 and not f.live and
          bytes(f.u.mem_read(0xa1833548, 44)) == menu)
    return dict(passed=True, checks=checks, host_sha256=host['main_payload_sha256'], module_sha256=module['module_sha256'],
                consumed_permission_only=True, caller_and_pending_frame_data_unchanged=True,
                immediate_stale_pending_replay_inhibition=True, native_context_writer_serialization_assumed=True,
                physical_pixels_frame_fence_camera_or_card_verified=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True); p.add_argument('--module', type=Path, required=True)
    p.add_argument('--legacy-build', type=Path, required=True)
    p.add_argument('--stock-main', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); out = a.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists(): p.error('Choose a new private output directory')
    if hashlib.sha256(a.stock_main.read_bytes()).hexdigest() != STOCK_SHA: p.error('Exact stock main required')
    host = json.loads((a.build / 'module-host.emulator.json').read_text(encoding='utf-8'))
    module = json.loads((a.module / 'module.json').read_text(encoding='utf-8'))
    raw, packet = (a.build / 'module-host.emulator.main.bin').read_bytes(), (a.module / 'Z7APP.BIN').read_bytes()
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        p.error('Host/module fingerprints differ')
    if not host.get('frame_permission_hooks') or module['api_minimum_bytes'] != 56: p.error('Explicit API56 host and profile required')
    source = ROOT / 'z7-native-modules/examples/frame_permission_host_probe.c'
    probe, metadata = build(source, zig=ZIG)
    out.mkdir(parents=True)
    failed_source = out / 'failed.c'
    failed_source.write_text('#define Z7_FRAME_INIT_FAIL 1\n#include "' + source.as_posix() + '"\n', encoding='utf-8', newline='\n')
    failed, failed_metadata = build(failed_source, zig=ZIG)
    result = audit(raw, host, packet, module, probe, metadata, failed, failed_metadata, a.legacy_build)
    result['source_sha256'] = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
        'tools/audit_z7_frame_permission.py', 'tools/build_z7_module_host.py', 'tools/build_z7_display_module.py',
        'tools/audit_z7_module_host.py', 'z7-native-modules/host/z7_380.c', 'z7-native-modules/host/z7_380.h',
        'z7-native-modules/sdk/frame_permission.h', 'z7-native-modules/examples/frame_permission_host_probe.c',
        'z7-native-modules/examples/display_highlight_owned_policy.h', 'z7-native-modules/plugins/combined_display.c')}
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__': main()
