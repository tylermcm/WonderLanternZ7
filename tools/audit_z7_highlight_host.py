"""Execute optional API48 host bridges, native fallback and owned requests.

SPDX-License-Identifier: MIT. Exact original native logic executes with supplied
kernel/filesystem, surface checks, hardware plane/color and incoming context.
Diagnostic source eligibility/epoch are explicit inputs, not photo policy.
"""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R12, UC_ARM_REG_CPSR, UC_ARM_REG_SP
from audit_splash_image import MEM, STACK, STOCK_SHA, ARGUMENTS
from audit_z7_module_host import HostFixture
from audit_z7_highlight_frame_gate import FrameGateFixture, FRAME, STATE as DISPLAY_STATE
from audit_z7_highlight_converter import request
from build_z7_module import ROOT, build
from build_z7_module_host import STATE, ZIG

GUI = MEM + 0xb000  # Separate from DisplayService state and its deferred frame.

class HighlightHostFixture(HostFixture):
    def __init__(self, raw, report, packet, metadata, selector=0, immediate=True):
        super().__init__(raw, report, packet)
        self.metadata = metadata
        for address in (0xa1d5f000, 0xa1d68000, 0xa1d69000, 0xa1d6a000,
                        0xa1f13000, 0xa1f18000, 0x20140000):
            self.u.mem_map(address, 0x1000)
        self.hardware, self.queued, self.completions, self.handlers = [], [], [], []
        self.write(0xa1d6ab80, 0x12300003)
        self.write(0xa1d5f580, 0x12300001)
        self.write(0xa180a588, DISPLAY_STATE)
        self.write(0xa180a578, MEM + 0x9000)
        self.write(MEM + 0x9000, 0x142)
        self.u.mem_write(0xa180a568, bytes([selector]))
        self.u.mem_write(0xa1d68e54, b'\3')
        self.u.mem_write(0xa1d69351, bytes([3 if immediate else 0]))
        self.write(DISPLAY_STATE + 0x228, 1)
        self.write(DISPLAY_STATE + 0x24, 1)
        self.write(0xa1f18fac, MEM + 0x8000)
        self.u.mem_write(MEM + 0x8000, struct.pack('<256I', *[i << 24 for i in range(256)]))
        self.u.mem_write(MEM + 0x6000, struct.pack('<4H', 0x1000, 0x8000, 0xe000, 0))
        self.u.mem_write(MEM + 0x5000, request(1 if selector == 0 else 4, 1, 248))
        self.call(0x1034fe22, DISPLAY_STATE + 0x28, MEM + 0x5000, 1 if selector == 0 else 4)

    def write(self, address, value):
        self.u.mem_write(address, struct.pack('<I', value))

    def read(self, address):
        return int.from_bytes(self.u.mem_read(address, 4), 'little')

    def hook(self, u, address, size, context):
        if address == self.report['highlight_bridges']['highlight_source_original']:
            self.source_native_stack = u.reg_read(UC_ARM_REG_SP)
            self.source_native_scratch = bytes(u.mem_read(STACK - 0x1000, 0x1000))
        if address in (0x100361e8, 0x100364dc):
            if u.reg_read(UC_ARM_REG_R0) != 0x12300003:
                raise AssertionError('Unexpected mutex')
            self.ret(0)
            return
        if address == 0x100363cc:
            if u.reg_read(UC_ARM_REG_R0) != 0x12300001:
                raise AssertionError('Unexpected queue')
            self.queued.append(u.reg_read(UC_ARM_REG_R1))
            self.ret(0)
            return
        if address == 0x102396c0:
            self.completions.append(u.reg_read(UC_ARM_REG_R0))
        if address == 0x1023e214:
            self.handlers.append(u.reg_read(UC_ARM_REG_R0))
        if address in (0x10241a0e, 0x1023b7f6, 0x1024147e, 0x1024354e, 0x10243d82):
            args = [u.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2)]
            if address == 0x10241a0e:
                self.hardware.append(dict(operation='warning-plane', arguments=args,
                    configuration=list(u.mem_read(args[1], 60)) if args[1] else None))
                self.ret(0)
            elif address == 0x1023b7f6:
                self.hardware.append(dict(operation='surface-check', arguments=args))
                self.ret(1)
            elif address == 0x10243d82:
                self.hardware.append(dict(operation='hardware-color', arguments=args))
                self.ret(MEM + 0x6000)
            else:
                self.hardware.append(dict(operation=hex(address), arguments=args))
                self.ret(0)
            return
        super().hook(u, address, size, context)

    def load(self):
        result = self.call(self.report['symbols']['z7_module_load_once'], STATE)
        self.base = self.words()[12]
        return result

    def address(self, name):
        return self.base + self.metadata['symbols'][name]

    def value(self, name):
        return self.read(self.address('z7_hl_' + name))

    def set(self, name, value):
        self.write(self.address('z7_hl_' + name), value)

    def invoke(self, name, *args):
        return self.call(self.address('z7_hl_' + name), *args)


def observed_call(f, address, args, flags=0):
    f.u.reg_write(UC_ARM_REG_R12, 0x13579bdf)
    f.u.reg_write(UC_ARM_REG_CPSR, (f.u.reg_read(UC_ARM_REG_CPSR) & ~0xf8000000) | flags)
    result = f.call(address, *args)
    return result, tuple(f.u.reg_read(r) for r in (*ARGUMENTS, UC_ARM_REG_R12)), f.u.reg_read(UC_ARM_REG_CPSR) & 0xf8000000


def audit(raw, report, stock, packet, metadata, failed_packet, failed_metadata):
    if hashlib.sha256(raw).hexdigest() != report['main_payload_sha256'] or hashlib.sha256(stock).hexdigest() != STOCK_SHA:
        raise ValueError('Exact host and original stock fingerprints required')
    if not report.get('highlight_hooks') or report.get('api_bytes') != 48:
        raise ValueError('Explicit highlight-host build required')
    checks = []

    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good:
            raise AssertionError(name)

    for selector in (0, 1):
        for permission in (0, 1):
            for flags in (0, 0x58000000, 0xa0000000):
                f = HighlightHostFixture(raw, report, packet, metadata, selector)
                baseline = FrameGateFixture(stock, selector, permission, 1)
                # Match independent engine layout for hardware argument comparison.
                baseline.write(0xa180a578, MEM + 0x9000)
                baseline.write(MEM + 0x9000, 0x142)
                f.write(FRAME + 0x34, permission)
                actual = observed_call(f, 0x1034866e, (selector * 2, FRAME), flags)
                # Original transform leaves hardware-config padding unwritten.
                # Compare byte-exact output with identical incoming native
                # scratch bytes, including the bridge's returned-call residue.
                # Caller-owned registers/frame/state remain independent inputs.
                baseline.u.mem_write(STACK - 0x1000, f.source_native_scratch)
                expected = observed_call(baseline, 0x1034866e, (selector * 2, FRAME), flags)
                check(f'unregistered-source{selector}-permission{permission}-flags{flags:x}-exact-native-fallback',
                      actual == expected and f.source_native_stack == STACK and f.hardware == baseline.hardware and
                      bytes(f.u.mem_read(DISPLAY_STATE, 0x8c)) == bytes(baseline.u.mem_read(DISPLAY_STATE, 0x8c)))
                del f, baseline
                gc.collect()

    f = HighlightHostFixture(raw, report, packet, metadata)
    check('api48-module-registers-all-hooks-during-init', f.load() == 8 and f.value('api_bytes') == 48 and f.value('registration_mask') == 2047)
    check('every-callback-required-and-truncated-or-unaligned-ranges-rejected', f.value('invalid_callback_fields') == 4 and f.value('invalid_ranges') == 3)
    check('registration-does-not-run-source-or-consumer', f.value('source_calls') == f.value('consumer_calls') == 0)
    check('late-registration-rejected', f.invoke('late') == 0)
    f.set('source_enable', 0)
    baseline = FrameGateFixture(stock, 0, 0, 1)
    baseline.write(0xa180a578, MEM + 0x9000)
    baseline.write(MEM + 0x9000, 0x142)
    expected = observed_call(baseline, 0x1034866e, (0, FRAME), 0x58000000)
    actual = observed_call(f, 0x1034866e, (0, FRAME), 0x58000000)
    check('registered-noop-source-preserves-native-result-volatile-registers-and-flags', actual == expected)
    check('zero-token-still-pairs-source-callbacks', f.value('source_calls') == f.value('source_after') == 1 and f.value('token') == 0)
    del f, baseline
    gc.collect()

    for selector in (0, 1):
        for immediate in (False, True):
            f = HighlightHostFixture(raw, report, packet, metadata, selector, immediate)
            check(f'source{selector}-immediate{immediate}-module-loads', f.load() == 8)
            f.set('recurse_source', 1)
            incoming = bytes(f.u.mem_read(FRAME, 0x4b8))
            check(f'source{selector}-immediate{immediate}-native-result-and-caller-frame-restored',
                  f.call(0x1034866e, selector * 2, FRAME) == 1 and bytes(f.u.mem_read(FRAME, 0x4b8)) == incoming)
            check(f'source{selector}-immediate{immediate}-local-token-and-recursion-suppression',
                  f.value('source_calls') == f.value('source_after') == 1 and f.value('token') == 0xabc12345 and f.value('nested_source') == 0)
            check(f'source{selector}-immediate{immediate}-native-permission-path-executes',
                  (f.read(DISPLAY_STATE + 0x20) == f.read(DISPLAY_STATE + 0x1c) == 1) if immediate else
                  (f.read(DISPLAY_STATE + 0x50c + 0x34) == 1 and f.u.mem_read(DISPLAY_STATE + 0x508, 1) == b'\1' and not f.hardware))
            del f
            gc.collect()

    for output, selector in ((1, 0), (4, 1)):
        for stale in (False, True):
            f = HighlightHostFixture(raw, report, packet, metadata, selector)
            f.load()
            owner = f.address('z7_hr')
            f.u.mem_write(GUI, request(output, 1, 248))
            check(f'output{output}-stale{stale}-owned-submit', f.invoke('submit', GUI, output, 17) == 1 and f.queued == [owner])
            f.set('recurse_consumer', 1)
            if stale:
                f.set('epoch', 18)
            before = bytes(f.u.mem_read(DISPLAY_STATE, 0x8c))
            native_result = f.call(0x10239840, owner)
            check(f'output{output}-stale{stale}-actual-host-consumer-brackets-original-completion',
                  native_result == (0 if stale else 1) and f.completions == [owner] and
                  f.value('consumer_calls') == f.value('consumer_after') == 1 and f.value('nested_consumer') == 0)
            check(f'output{output}-stale{stale}-cancellation-versus-native-copy',
                  (not f.handlers and bytes(f.u.mem_read(DISPLAY_STATE, 0x8c)) == before) if stale else
                  (f.handlers == [owner] and bytes(f.u.mem_read(DISPLAY_STATE + 0x28, 100)) == bytes(f.u.mem_read(owner + 28, 100))))
            check(f'output{output}-stale{stale}-reap-after-bridge-return', f.invoke('reap') == (1 if stale else 2))
            check(f'output{output}-stale{stale}-idle-owned-address-parks-without-native-dispatch',
                  f.call(0x10239840, owner) == 0 and f.value('consumer_after') == 1 and f.completions == [owner])
            del f
            gc.collect()

    f = HighlightHostFixture(raw, report, packet, metadata)
    f.load()
    f.u.mem_write(GUI, request(1, 1, 248))
    f.invoke('submit', GUI, 1, 17)
    f.set('cycle_after', 1)
    f.set('next_request', GUI)
    owner = f.address('z7_hr')
    check('retirement-publication-allows-immediate-reap-submit-and-consume-before-old-host-return',
          f.call(0x10239840, owner) == 1 and f.value('reaped_after') == 2 and
          f.value('submitted_after') == f.value('consumed_after') == 1 and
          f.value('consumer_calls') == f.value('consumer_after') == 2 and f.queued == [owner, owner])
    check('overlapping-return-tail-does-not-overwrite-next-retirement', f.invoke('reap') == 2 and f.words()[59] == 0)
    del f
    gc.collect()

    foreign, payload = MEM + 0x2000, MEM + 0x3000
    for selector in (0, 1):
        for family in (0, 1):
            f = HighlightHostFixture(raw, report, packet, metadata, selector)
            f.load()
            baseline = HighlightHostFixture(stock, report, packet, metadata, selector)
            f.invoke('submit', MEM + 0x5000, 1 if selector == 0 else 4, 17)
            descriptor = struct.pack('<7I', 0, 0, 0, 0, 0x42060007 + family * 0x2000, payload, 0)
            for fixture in (f, baseline):
                fixture.u.mem_write(payload, bytes(range(100)) + bytes(4))
                fixture.u.mem_write(foreign, descriptor)
            expected = observed_call(baseline, 0x10239840, (foreign,), 0x58000000)
            actual = observed_call(f, 0x10239840, (foreign,), 0x58000000)
            check(f'foreign-selector{selector}-family{family}-exact-native-result-registers-flags-and-publication',
                  actual == expected and bytes(f.u.mem_read(DISPLAY_STATE, 0x8c)) == bytes(baseline.u.mem_read(DISPLAY_STATE, 0x8c)) and
                  f.handlers == baseline.handlers and f.completions == baseline.completions)
            check(f'foreign-selector{selector}-family{family}-never-calls-module-or-releases-owned-request',
                  f.value('consumer_calls') == f.value('consumer_after') == 0 and f.invoke('reap') == 0)
            del f, baseline
            gc.collect()

    for offset, bad in ((32, 0), (48, 0), (52, 0), (76, 1), (92, 0),
                        (208, 0xffffffff), (216, 0), (220, 0x102fd647),
                        (224, 0x102fd647), (228, 0x102fd647), (240, 0)):
        f = HighlightHostFixture(raw, report, packet, metadata)
        f.load()
        f.write(STATE + offset, bad)
        check(f'invalid-resident-state-offset{offset}-native-source-fallback-without-module-call',
              f.call(0x1034866e, 0, FRAME) == 1 and f.value('source_calls') == 0 and f.read(FRAME + 0x34) == 0)
        del f
        gc.collect()
    f = HighlightHostFixture(raw, report, failed_packet, failed_metadata)
    check('initializer-failure-clears-all-highlight-pointers-before-free', f.load() == 7 and
          f.words()[53:60] == (0,) * 7 and f.words()[23] == 0 and not f.live)
    check('failed-module-native-source-remains-usable', f.call(0x1034866e, 0, FRAME) == 1 and f.read(DISPLAY_STATE + 0x20) == 0)
    return dict(passed=True, checks=checks, host_sha256=report['main_payload_sha256'], stock_main_sha256=STOCK_SHA,
                unregistered_hardware_padding_comparison_uses_identical_native_entry_scratch_bytes=True,
                api_bytes=48, actual_source_and_consumer_bridges_installed_in_private_emulator_image=True,
                diagnostic_eligibility_epoch_kernel_filesystem_hardware_boundaries_supplied=True,
                full_profile_preference_connected=False, physical_output_photo_movie_context_bound=False,
                actual_warning_pixels=False, camera_card_access_staging_flash_or_push=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--stock-main', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists():
        p.error('Choose a new private output directory')
    out.mkdir(parents=True)
    source = ROOT / 'z7-native-modules/examples/highlight_host_probe.c'
    packet, metadata = build(source, zig=ZIG)
    failed_source = out / 'failed.c'
    failed_source.write_text('#define Z7_HL_FAIL 1\n#include "' + source.as_posix() + '"\n', encoding='utf-8', newline='\n')
    failed_packet, failed_metadata = build(failed_source, zig=ZIG)
    for label, binary, report in (('probe', packet, metadata), ('failed', failed_packet, failed_metadata)):
        (out / (label + '.BIN')).write_bytes(binary)
        (out / (label + '.json')).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    report = json.loads((a.build / 'module-host.emulator.json').read_text())
    result = audit((a.build / 'module-host.emulator.main.bin').read_bytes(), report,
                   a.stock_main.read_bytes(), packet, metadata, failed_packet, failed_metadata)
    result['source_sha256'] = {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in (
        'tools/audit_z7_highlight_host.py', 'tools/build_z7_module_host.py',
        'z7-native-modules/host/z7_380.c', 'z7-native-modules/host/z7_380.h',
        'z7-native-modules/sdk/highlight.h', 'z7-native-modules/plugins/highlight_request.h',
        'z7-native-modules/examples/highlight_host_probe.c')}
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__':
    main()
