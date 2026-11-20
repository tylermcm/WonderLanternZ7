"""Original-Z7 histogram getter rejection and timeout-cleanup contracts.

SPDX-License-Identifier: MIT. Original wrapper/driver/zeroing instructions run.
Incoming driver state, mutex/event services and an unavailable event result are
supplied. No successful statistics producer or histogram pixels are established.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from itertools import product

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3
from audit_splash_image import NativePNG, STOCK_SHA, MEM
from build_z7_module_host import ROOT

DRIVER, REQUEST, EVENT, MUTEX = 0xa188d70c, 0xa188d6b0, 0xa2330840, 0xa233160c
BYTES = 1024


class HistogramGetter(NativePNG):
    def __init__(self, raw):
        super().__init__(raw)
        self.u.mem_map(0xa2330000, 0x10000)
        self.events = []; self.held = False; self.destination = 0

    def hook(self, u, address, size, context):
        if address == 0x10170bee:
            if (u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)) != (EVENT, 1):
                raise AssertionError('Unexpected native histogram event clear')
            self.events.append('event-clear'); self.ret(0)
        elif address == 0x10170c32:
            args = tuple(u.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3))
            if args != (EVENT, 1, 0, 100) or self.held: raise AssertionError('Unexpected histogram wait contract')
            self.events.append('event-unavailable'); self.ret(0)
        elif address in (0x10170944, 0x1017093e):
            if u.reg_read(UC_ARM_REG_R0) != MUTEX: raise AssertionError('Unexpected histogram mutex')
            if address == 0x10170944:
                if self.held: raise AssertionError('Recursive histogram lock')
                self.held = True; self.events.append('lock')
            else:
                if not self.held: raise AssertionError('Unowned histogram unlock')
                self.held = False; self.events.append('unlock')
            self.ret(1)
        elif address == 0x101709d4:
            if u.reg_read(UC_ARM_REG_R0) != self.destination or u.reg_read(UC_ARM_REG_R1) != BYTES:
                raise AssertionError('Unexpected histogram rejection zeroing')
            self.events.append('native-zero')  # Execute original instructions.
        elif address in (0x100a51d8, 0x100efac4):
            raise AssertionError('Unavailable event reached statistics conversion')
        else: super().hook(u, address, size, context)


def audit(raw):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA: raise ValueError('Exact original-Z7 stock required')
    f = HistogramGetter(raw); checks = []
    fast = {0, 3, 4, 5, *range(0x20, 0x26)}
    for state, mode, alignment in product((0, 1, 2, 3, 4, 7, 255), (0, 2, 3, 4, 5, 0x20, 0x25, 255), range(4)):
        f.destination = MEM + 0x8000 + alignment
        f.u.mem_write(DRIVER, bytes([1, state, mode]))
        f.u.mem_write(REQUEST, bytes(0x18))
        f.u.mem_write(f.destination - 16, b'\xa5' * (BYTES + 32))
        f.events.clear(); f.held = False
        result = f.call(0x104070ac, f.destination)
        entered = state == 2 and alignment == 0
        expected = b'\xa5' * 16 + (bytes(BYTES) if entered else b'\xa5' * BYTES) + b'\xa5' * 16
        events = ['event-clear'] + (['lock', 'unlock'] if mode in fast else []) + ['event-unavailable'] + (['lock', 'unlock'] if mode in fast else []) + ['native-zero'] if entered else []
        passed = (result == 0 and bytes(f.u.mem_read(f.destination - 16, BYTES + 32)) == expected and
            f.events == events and not f.held and bytes(f.u.mem_read(REQUEST + 0x10, 8)) == bytes(8) and
            bytes(f.u.mem_read(DRIVER, 3)) == bytes([1, state, mode]))
        checks.append(dict(driver_state=state, mode=mode, destination_alignment=alignment,
            entered_native_wait=entered, native_destination_zeroed=entered, passed=passed))
        if not passed: raise AssertionError(dict(case=checks[-1], actual_events=f.events, expected_events=events, return_value=result))
    return dict(passed=True, checks=checks, stock_main_sha256=STOCK_SHA,
        wrapper_chain=['0x104070AC', '0x10203C5E', '0x10148DA0', '0x101F8F20', '0x100A7382'],
        driver_state_required=2, destination_alignment_required=4, requested_bytes=BYTES,
        unavailable_event_return=0, native_wait_argument=100,
        early_rejection_preserves_destination=True, timeout_zeroes_exact_destination=True,
        timeout_clears_busy_and_pending_destination=True, original_zeroing_instructions_execute=True,
        supplied_boundaries=['Incoming driver state/mode', 'Mutex/event services', 'Unavailable event result0'],
        successful_statistics_producer_verified=False, pixel_validation=False, camera_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock', type=Path, default=ROOT / '.private/builds/20261021-laptop-01/stock-main.bin')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); output = a.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists(): p.error('Choose a new private output')
    result = audit(a.stock.read_bytes()); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']), timeout_zero_bytes=BYTES)))


if __name__ == '__main__': main()
