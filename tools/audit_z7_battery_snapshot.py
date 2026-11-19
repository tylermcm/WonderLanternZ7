"""Inspect the original Z7's native locked battery-menu snapshot contract.

SPDX-License-Identifier: MIT. Original getter and ARM memcpy instructions run;
mutex services and snapshot producer data are supplied. No percentage overlay,
hardware battery telemetry or camera access is established by this experiment.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_SP, UC_ARM_REG_LR
from audit_splash_image import NativePNG, MEM, STACK, STOP, STOCK_SHA
from build_z7_module_host import ROOT

SOURCE, MUTEX, SIZE = 0xa235aee4, 0xa235ae4c, 56


class BatterySnapshot(NativePNG):
    def __init__(self, raw):
        super().__init__(raw)
        self.u.mem_map(0xa2350000, 0x10000)
        self.held = False
        self.events = []
        self.menu_trace = False
        self.formatted = None

    def hook(self, u, address, size, context):
        if self.menu_trace and address in (0x104cdf88, 0x103faebe):
            self.ret(MEM + 0xc000)
        elif self.menu_trace and address == 0x101709a8:
            pointer = u.reg_read(UC_ARM_REG_R1)
            self.formatted = (bytes(u.mem_read(pointer, 5)), u.reg_read(UC_ARM_REG_R2))
            u.emu_stop()
        elif address in (0x10170944, 0x1017093e):
            if u.reg_read(UC_ARM_REG_R0) != MUTEX:
                raise AssertionError('Unexpected snapshot mutex')
            if address == 0x10170944:
                if self.held:
                    raise AssertionError('Recursive snapshot lock')
                self.events.append('lock')
                self.held = True
            else:
                if not self.held:
                    raise AssertionError('Unowned snapshot unlock')
                self.events.append('unlock')
                self.held = False
            self.ret(1)
        elif address == 0x10170a1c:
            if not self.held or u.reg_read(UC_ARM_REG_R1) != SOURCE or u.reg_read(UC_ARM_REG_R2) != SIZE:
                raise AssertionError('Wrong native snapshot copy contract')
            self.events.append('native-arm-memcpy')
            # Execute original ARM memcpy, including its state transition.
        else:
            super().hook(u, address, size, context)


def audit(raw):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA:
        raise ValueError('Requires exact original Z7 C 3.80 MAIN')
    fixture = BatterySnapshot(raw)
    checks = []
    for percent in (0, 1, 50, 99, 100, 101, 255, 0xffffffff):
        for alignment in (0, 4, 8):
            destination = MEM + 0x8000 + alignment
            body = bytearray((i * 37 + 11) & 255 for i in range(SIZE))
            struct.pack_into('<I', body, 24, percent)
            source = bytes(body) + bytes([0x6d]) * 16
            fixture.u.mem_write(SOURCE, source)
            fixture.u.mem_write(destination - 16, bytes([0xa5]) * (SIZE + 32))
            fixture.events.clear()
            fixture.call(0x10437684, destination)
            actual = bytes(fixture.u.mem_read(destination - 16, SIZE + 32))
            passed = (actual == bytes([0xa5]) * 16 + bytes(body) + bytes([0xa5]) * 16 and
                      bytes(fixture.u.mem_read(SOURCE, len(source))) == source and
                      fixture.events == ['lock', 'native-arm-memcpy', 'unlock'] and not fixture.held)
            checks.append(dict(name=f'locked-native-copy-{percent}-{alignment}', passed=passed))
            if not passed:
                raise AssertionError(checks[-1]['name'])
    # Stop at the original menu's first formatting call. This is a prefix trace,
    # not a completed constructor or an emulated GUI-object lifetime.
    fixture.menu_trace = True
    for percent in (0, 1, 50, 99, 100, 101, 255, 0xffffffff):
        fixture.u.mem_write(SOURCE + 24, struct.pack('<I', percent))
        fixture.u.mem_write(MEM + 0xb00c, struct.pack('<I', MEM + 0xc000))
        fixture.u.reg_write(UC_ARM_REG_R0, MEM + 0xb000)
        fixture.u.reg_write(UC_ARM_REG_SP, STACK)
        fixture.u.reg_write(UC_ARM_REG_LR, STOP | 1)
        fixture.formatted = None
        fixture.u.emu_start(0x104c4aa3, STOP, timeout=10000000, count=1000000)
        passed = fixture.formatted == (b'%d%%\0', percent)
        checks.append(dict(name=f'native-menu-formats-snapshot-word-{percent}', passed=passed))
        if not passed:
            raise AssertionError(checks[-1]['name'])
    return dict(passed=True, checks=checks, source_sha256=STOCK_SHA, snapshot_bytes=SIZE,
        percentage_word_offset=24, supplied_boundaries=['Mutex services', 'Snapshot producer bytes',
            'Menu object lookup/hide calls; constructor trace stops at first formatter'],
        sentinel_semantics_verified=False, telemetry_verified=False, overlay_implemented=False,
        camera_access=False, card_access=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, default=ROOT / '.private/builds/20261021-laptop-01/stock-main.bin')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists():
        parser.error('Choose a new private evidence path')
    result = audit(args.stock.read_bytes())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']), native_copy_bytes=SIZE)))


if __name__ == '__main__':
    main()
