"""Execute native warning-plane programming below the API56 permission gate.

SPDX-License-Identifier: MIT. Actual converter/consumer/frame/gate/driver and
configuration validator instructions execute. MMIO storage, hardware colors,
surface checks, kernel/FS/UI/context and explicit task scheduling are supplied.
Register programming is not physical application, image processing or pixels.
"""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import struct

from unicorn import UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2
from audit_splash_image import NativePNG, STOCK_SHA, MEM
from audit_z7_frame_permission import FrameProfileFixture, FRAME
from audit_z7_highlight_frame_gate import SOURCE_APPLY, FRAME_APPLY, GATE
from audit_z7_parameters import NATIVE
from build_z7_module_host import ROOT

DRIVER, VALIDATOR, READBACK = 0x10241a0e, 0x10258ef8, 0x10241c2e
MMIO = 0x20140000


class PlaneFixture(FrameProfileFixture):
    def __init__(self, *args):
        super().__init__(*args)
        self.u.mem_map(MMIO + 0x1000, 0x5000)
        self.programs, self.register_writes = [], []
        self.u.hook_add(UC_HOOK_MEM_WRITE, self.mmio_write, begin=MMIO, end=MMIO + 0x5fff)

    def mmio_write(self, u, access, address, size, value, context):
        self.register_writes.append((address, size, value))

    def hook(self, u, address, size, context):
        if address == DRIVER:
            engine, config, enabled = (u.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2))
            self.programs.append((engine, enabled, bytes(u.mem_read(config, 60)) if config else None))
            NativePNG.hook(self, u, address, size, context)
            return  # Execute the real native driver instead of the old sink.
        super().hook(u, address, size, context)


def audit(raw, host, packet, module):
    checks = []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    f = PlaneFixture(raw, host, packet, module); f.load()
    baseline = f.convert(2, 213); f.native(baseline)
    f.call(host['symbols']['z7_display_before_update']); f.gui(); f.worker(); f.dispatch(); f.worker()
    engine = f.read(0xa180a578)
    # Both bank offsets are supplied inputs. This does not identify the physical
    # LCD/EVF assignment or claim either descriptor is a real live camera object.
    banks = []
    for offset, identity in ((0, 0x141), (0x4000, 0x142)):
        f.write(engine, identity); f.write(engine + 4, offset)
        f.write(NATIVE + 0x1c, 0); f.write(NATIVE + 0x24, 1)
        f.write(MMIO + offset + 0x430, 0xa5a50000)
        f.register_writes.clear(); f.programs.clear()
        original = bytes(f.u.mem_read(FRAME, 0x4b8))
        check(f'bank{offset:x}-full-profile-reaches-real-native-plane-driver',
              f.call(SOURCE_APPLY, 0, FRAME) == 1 and len(f.programs) == 1 and f.programs[0][:2] == (engine, 1) and
              f.read(MMIO + offset + 0x430) & 1 == 1 and f.read(NATIVE + 0x1c) == 1 and f.read(NATIVE + 0x24) == 0 and
              bytes(f.u.mem_read(FRAME, 0x4b8)) == original)
        config = f.programs[0][2]
        scratch = NATIVE + 0x2600
        f.u.mem_write(scratch, config)
        check(f'bank{offset:x}-native-transformed-config-passes-original-validator', f.call(VALIDATOR, scratch) == 1)
        # Independent field-to-register checks from the actual transformed60B
        # configuration; do not substitute a synthetic raster for real pixels.
        half = lambda n: int.from_bytes(config[n:n + 2], 'little')
        word = lambda n: int.from_bytes(config[n:n + 4], 'little')
        expected = {
            0x430: 1 | ((config[0] & 3) << 8),
            0x434: (half(2) | 0xff) | (half(4) << 16),
            0x43c: config[6], 0x450: config[28],
            0x45c: half(34) | ((255 - config[36]) << 16),
            0x464: half(42) | ((255 - config[44]) << 16),
            0x468: config[46] | (config[47] << 8) | (int(bool(word(48))) << 16),
            0x470: config[56] | (config[57] << 8),
            0x478: config[59],
        }
        check(f'bank{offset:x}-actual-register-fields-match-native-transformed-config',
              all(f.read(MMIO + offset + field) == value for field, value in expected.items()))
        writes = list(f.register_writes)
        check(f'bank{offset:x}-programming-writes-only-selected-plane-and-native-shared-aux-register',
              all(size == 4 and (MMIO + offset + 0x430 <= address <= MMIO + offset + 0x478 or
                                address in (MMIO + 0x46c, MMIO + 0x446c)) for address, size, _ in writes))
        f.u.mem_write(scratch + 0x100, b'\xa5' * 64)
        f.write(scratch + 0x200, 0xcccccccc)
        check(f'bank{offset:x}-native-readback-observes-enable-and-mode',
              f.call(READBACK, engine, scratch + 0x100, scratch + 0x200) == 0 and
              f.read(scratch + 0x200) == 1 and bytes(f.u.mem_read(scratch + 0x100, 1)) == config[:1])
        # A no-frame control call: original gate disables with permission0.
        # This is a proven control primitive, not yet module cleanup ownership.
        before = bytes(f.u.mem_read(MMIO, 0x6000)); control = f.read(MMIO + offset + 0x430)
        f.write(NATIVE + 0x20, 0); f.register_writes.clear(); f.programs.clear()
        check(f'bank{offset:x}-original-gate-tears-down-without-source-or-frame-application',
              f.call(GATE, 0) == 1 and f.programs == [(engine, 0, None)] and f.read(NATIVE + 0x1c) == 0 and
              f.read(MMIO + offset + 0x430) == control & ~1)
        after = bytearray(before)
        struct.pack_into('<I', after, offset + 0x430, control & ~1)
        check(f'bank{offset:x}-no-frame-disable-preserves-all-other-register-bits-and-banks',
              bytes(f.u.mem_read(MMIO, 0x6000)) == after and f.register_writes == [(MMIO + offset + 0x430, 4, control & ~1)])
        f.register_writes.clear(); f.programs.clear()
        check(f'bank{offset:x}-already-disabled-gate-never-programs-driver-again',
              f.call(GATE, 0) == 1 and not f.programs and not f.register_writes)
        banks.append(dict(offset=offset, supplied_engine_identity=identity, transformed_config_sha256=hashlib.sha256(config).hexdigest()))

    f.write(engine, 0x141); f.write(engine + 4, 0)
    f.u.mem_write(0xa1d69351, b'\0')
    check('deferred-source-keeps-native-permission-in-pending-copy', f.call(SOURCE_APPLY, 0, FRAME) == 1 and f.read(NATIVE + 0x50c + 0x34) == 0)
    check('forced-replay-programs-real-plane-using-current-lease',
          f.call(FRAME_APPLY, NATIVE + 0x50c, 1) == 1 and f.read(MMIO + 0x430) & 1 == 1)
    pending = bytes(f.u.mem_read(NATIVE + 0x50c, 0x4b8))
    f.toggle(); f.register_writes.clear()
    check('off-before-gui-worker-replay-clears-real-register-enable',
          f.call(FRAME_APPLY, NATIVE + 0x50c, 1) == 1 and f.read(MMIO + 0x430) & 1 == 0 and f.read(NATIVE + 0x1c) == 0 and
          bytes(f.u.mem_read(NATIVE + 0x50c, 0x4b8)) == pending)

    # Driver status0 is also returned for a rejected configuration, without any
    # MMIO programming. Consequently gate result/state alone cannot prove that
    # a newly requested plane was programmed or rendered.
    scratch = NATIVE + 0x2600
    invalid = bytearray(60); struct.pack_into('<2H', invalid, 2, 0, 1)
    f.u.mem_write(scratch, bytes(invalid)); f.register_writes.clear()
    check('native-validator-rejects-reversed-threshold-range', f.call(VALIDATOR, scratch) == 0)
    check('driver-returns-normal-status-for-rejected-config-without-register-writes',
          f.call(DRIVER, engine, scratch, 1) == 0 and not f.register_writes)
    check('null-config-enable-is-a-native-noop-with-normal-status', f.call(DRIVER, engine, 0, 1) == 0 and not f.register_writes)
    # The same rejection can propagate through a nominally successful upper
    # gate: its active/dirty bookkeeping does not read back hardware enable.
    f.write(NATIVE + 0x30, 0x01000000)  # First native group upper0/lower256.
    f.write(NATIVE + 0x20, 1); f.write(NATIVE + 0x1c, 0); f.write(NATIVE + 0x24, 1)
    f.write(MMIO + 0x430, 0); f.register_writes.clear()
    check('successful-gate-bookkeeping-does-not-prove-plane-was-programmed',
          f.call(GATE, 0) == 1 and f.read(NATIVE + 0x1c) == 1 and f.read(NATIVE + 0x24) == 0 and
          f.read(MMIO + 0x430) == 0 and not f.register_writes)
    # Format4 explicitly bypasses the gate and cannot prove release.
    f.write(NATIVE + 0x1c, 1); f.write(NATIVE + 0x20, 0); f.write(MMIO + 0x430, 0x101)
    f.register_writes.clear()
    check('format4-gate-bypasses-teardown-and-preserves-active-plane',
          f.call(GATE, 4) == 1 and f.read(NATIVE + 0x1c) == 1 and f.read(MMIO + 0x430) == 0x101 and not f.register_writes)
    del f; gc.collect()
    return dict(passed=True, checks=checks, banks=banks, host_sha256=host['main_payload_sha256'], module_sha256=module['module_sha256'],
                original_native_plane_programming_validator_and_readback_execute=True,
                no_frame_native_teardown_primitive_verified=True, module_no_frame_teardown_connected=False,
                mmio_storage_and_kernel_filesystem_ui_surface_colors_supplied=True,
                physical_driver_application_image_processing_warning_pixels_camera_card_verified=False)


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
    if not host.get('frame_permission_hooks') or module['api_minimum_bytes'] != 56: p.error('Explicit API56 pair required')
    result = audit(raw, host, packet, module)
    result['source_sha256'] = {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in (
        'tools/audit_z7_highlight_plane.py', 'tools/audit_z7_frame_permission.py',
        'z7-native-modules/examples/display_highlight_owned_policy.h')}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__': main()
