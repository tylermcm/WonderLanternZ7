"""Execute original primary-frame warning permission and deferred-copy gates.

SPDX-License-Identifier: MIT. Incoming frame/service/palette state, selected
surface checks and hardware palette/plane programming are supplied. Original
source routing, frame application and warning gate instructions execute.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2
from audit_splash_image import MEM, STOCK_SHA
from audit_z7_highlight_converter import ConverterFixture, request
from build_z7_module_host import ROOT

SOURCE_APPLY, FRAME_APPLY, GATE = 0x1034866e, 0x1023b9d0, 0x1023b76e
STATE, FRAME, ENGINE = MEM + 0x1000, MEM + 0x10000, MEM + 0x4000


class FrameGateFixture(ConverterFixture):
    def __init__(self, raw, selector=0, permission=0, enabled=1, service=3, immediate=True):
        super().__init__(raw)
        self.u.mem_map(0xa1d5f000, 0x1000)
        self.u.mem_map(0xa1d69000, 0x1000)
        self.u.mem_map(0xa1d6a000, 0x1000)
        self.u.mem_write(0xa1d6ab80, struct.pack('<I', 0x12300003))
        self.u.mem_map(0x20140000, 0x1000)
        self.hardware, self.frame_calls, self.gate_calls = [], [], []
        self.write(0xa180a588, STATE)
        self.write(0xa180a578, ENGINE)
        self.write(ENGINE, 0x142)
        self.write(ENGINE + 4, 0)
        self.u.mem_write(0xa180a568, bytes([selector]))
        self.u.mem_write(0xa1d68e54, bytes([service]))
        self.u.mem_write(0xa1d69351, bytes([3 if immediate else 0]))
        self.write(STATE + 0x228, 1)
        self.write(STATE + 0x24, 1)
        self.write(0xa1f18fac, MEM + 0x8000)
        self.u.mem_write(MEM + 0x8000, struct.pack('<256I', *[i << 24 for i in range(256)]))
        self.u.mem_write(MEM + 0x6000, struct.pack('<4H', 0x1000, 0x8000, 0xe000, 0))
        self.u.mem_write(MEM + 0x5000, request(1 if selector == 0 else 4, enabled, 248))
        self.call(0x1034fe22, STATE + 0x28, MEM + 0x5000, 1 if selector == 0 else 4)
        self.write(FRAME + 0x34, permission)

    def write(self, address, value):
        self.u.mem_write(address, struct.pack('<I', value))

    def read(self, address):
        return int.from_bytes(self.u.mem_read(address, 4), 'little')

    def hook(self, u, address, size, context):
        if address in (0x100361e8, 0x100364dc):
            if u.reg_read(UC_ARM_REG_R0) != 0x12300003:
                raise AssertionError('Unexpected native mutex handle')
            self.ret(0)
            return
        if address == FRAME_APPLY:
            self.frame_calls.append((u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)))
        if address == GATE:
            self.gate_calls.append(u.reg_read(UC_ARM_REG_R0))
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


def audit(raw):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA:
        raise ValueError('Exact private original-Z7 C3.80 stock main required')
    checks, cases = [], []

    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good:
            raise AssertionError(name)

    for selector in (0, 1):
        for previous in (0, 1):
            for permission in (0, 1):
                for enabled in (0, 1):
                    f = FrameGateFixture(raw, selector, permission, enabled)
                    f.write(STATE + 0x1c, previous)
                    incoming = bytes(f.u.mem_read(FRAME, 0x4b8))
                    result = f.call(SOURCE_APPLY, selector * 2, FRAME)
                    label = f'selector{selector}-previous{previous}-frame{permission}-parameters{enabled}'
                    active = permission & enabled
                    expected = [1] if active else [0] if previous else []
                    check(label + '-native-route-and-frame-permission-publication', result == 1 and f.frame_calls == [(FRAME, 0)] and f.read(STATE + 0x20) == permission)
                    check(label + '-warning-plane-requires-both-enables-and-cleans-up-previous-state', f.read(STATE + 0x1c) == active and
                          [h['arguments'][2] for h in f.hardware if h['operation'] == 'warning-plane'] == expected and f.read(STATE + 0x24) == 0)
                    check(label + '-native-source-frame-unchanged', bytes(f.u.mem_read(FRAME, 0x4b8)) == incoming)
                    cases.append(dict(selector=selector, previous=previous, permission=permission, enabled=enabled, hardware=f.hardware))
        f = FrameGateFixture(raw, selector, 1, 1, immediate=False)
        f.u.mem_write(FRAME + 0x200, bytes((i * 37 + 5) & 255 for i in range(0x2b8)))
        incoming = bytes(f.u.mem_read(FRAME, 0x4b8))
        check(f'selector{selector}-deferred-frame-is-copied-without-plane-programming', f.call(SOURCE_APPLY, selector * 2, FRAME) == 1 and
              bytes(f.u.mem_read(STATE + 0x50c, 0x4b8)) == incoming and f.u.mem_read(STATE + 0x508, 1) == b'\1' and not f.hardware)
        f.write(FRAME + 0x34, 0)  # Model caller restoration after native source copy.
        check(f'selector{selector}-caller-restoration-does-not-change-pending-permission', f.read(STATE + 0x50c + 0x34) == 1 and f.read(STATE + 0x20) == 0)
        check(f'selector{selector}-native-forced-replay-consumes-the-pending-permission', f.call(FRAME_APPLY, STATE + 0x50c, 1) == 1 and
              f.read(STATE + 0x20) == f.read(STATE + 0x1c) == 1 and [h['arguments'][2] for h in f.hardware if h['operation'] == 'warning-plane'] == [1])
        for name in ('wrong-output', 'not-ready', 'inactive-service', 'unsupported-source'):
            f = FrameGateFixture(raw, selector, 1, 1)
            if name == 'wrong-output': f.u.mem_write(0xa180a568, bytes([1 - selector]))
            if name == 'not-ready': f.write(STATE + 0x228, 0)
            if name == 'inactive-service': f.u.mem_write(0xa1d68e54, b'\1')
            if name == 'unsupported-source': f.u.mem_write(FRAME, b'\5')
            result = f.call(SOURCE_APPLY, selector * 2, FRAME)
            check(f'selector{selector}-' + name + '-never-publishes-frame-permission-or-programs-plane',
                  result == (0 if name in ('wrong-output', 'unsupported-source') else 1) and not f.hardware and f.read(STATE + 0x20) == f.read(STATE + 0x1c) == 0)
        f = FrameGateFixture(raw, selector, 1, 1, service=4)
        check(f'selector{selector}-native-service4-also-applies-frame-permission', f.call(SOURCE_APPLY, selector * 2, FRAME) == 1 and f.read(STATE + 0x1c) == 1)
        f = FrameGateFixture(raw, selector, 2, 1)
        f.write(STATE + 0x1c, 1)
        check(f'selector{selector}-nonboolean-frame-permission-does-not-enable-warning-plane', f.call(SOURCE_APPLY, selector * 2, FRAME) == 1 and
              f.read(STATE + 0x20) == 2 and f.read(STATE + 0x1c) == 0 and [h['arguments'][2] for h in f.hardware if h['operation'] == 'warning-plane'] == [0])
    return dict(passed=True, checks=checks, cases=cases, stock_main_sha256=STOCK_SHA,
                native_source_route_frame_apply_warning_gate_execute=True, per_frame_permission_offset=0x34,
                native_state_permission_offset=0x20, native_global_parameter_offset=0x28,
                supplied_boundaries=['Incoming frame/service/MMIO/palette state', 'Selected surface checks', 'Hardware color and warning-plane programming', 'Kernel mutex lock/release'],
                deferred_frame_copy_bytes=0x4b8, deferred_frame_offset=0x50c, deferred_frame_ready_offset=0x508,
                caller_restoration_does_not_cancel_deferred_copy=True, image_template_offset_bound=False, producer_hook_installed=False, actual_warning_pixels=False,
                physical_camera_or_card_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists():
        p.error('Choose a new private output')
    result = audit(a.stock_main.read_bytes())
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__':
    main()
