# SPDX-License-Identifier: MIT
"""Execute the exact native bar converter with scoped incoming input fixture.

Original instructions, source cache and canary destination execute in Unicorn;
no GUI, physical telemetry, camera installation or recovery claim.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R6, UC_ARM_REG_R8, UC_ARM_REG_PC
from battery_bar_fixture import BatteryBarFixture, POINT, SNAPSHOTS
from build_z7_module_host import ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists():
        parser.error('Choose a new private evidence file')
    raw = (args.build/'module-host.emulator.main.bin').read_bytes()
    host = json.loads((args.build/'module-host.emulator.json').read_text())
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256']:
        raise ValueError('Host fingerprint mismatch')
    checks = []
    for selected, expected in ((None, 6), (1, 1), (0, 0)):
        u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        u.mem_map(0x10368000, 0x1000)
        u.mem_write(0x10368000, raw[0x10368000-0x10020000:0x10369000-0x10020000])
        u.mem_map(0xa201d000, 0x1000)
        u.mem_write(0xa201d000, b'\x55'*0x1000)
        u.mem_map(0x20000000, 0x1000)
        u.reg_write(UC_ARM_REG_R6, SNAPSHOTS[0] + 0x90)
        u.reg_write(UC_ARM_REG_R8, 0x20000000)
        fixture = BatteryBarFixture(bytes(u.mem_read(POINT, 2)))
        if selected is not None: fixture.select(selected)
        def hook(cpu, address, size, context):
            if address == POINT and selected is not None:
                packet = bytearray(68)
                for reg, index in ((UC_ARM_REG_R0, 0), (UC_ARM_REG_R1, 1), (UC_ARM_REG_R2, 2), (UC_ARM_REG_R6, 6), (UC_ARM_REG_PC, 15)):
                    struct.pack_into('<I', packet, index*4, cpu.reg_read(reg))
                assert fixture.apply(packet)
                cpu.reg_write(UC_ARM_REG_R1, struct.unpack_from('<I', packet, 4)[0])
                cpu.reg_write(UC_ARM_REG_R2, struct.unpack_from('<I', packet, 8)[0])
        u.hook_add(UC_HOOK_CODE, hook)
        u.emu_start(0x10368565, 0x103685ae, timeout=1000000, count=100)
        expected_memory = bytearray(b'\x55'*0x1000)
        expected_memory[SNAPSHOTS[0]-0xa201d000+0x1aa] = expected
        assert bytes(u.mem_read(0xa201d000, 0x1000)) == expected_memory
        assert bytes(u.mem_read(0x20000000, 0x1000)) == bytes(0x1000)
        checks.append(dict(selected=selected, native_bar=expected, single_destination_byte_only=True,
                           source_cache_unchanged=True))
    result = dict(passed=True, checks=checks, main_sha256=host['main_payload_sha256'],
                  original_converter_executes=True, native_gui_or_pixels=False, physical_telemetry=False,
                  source_sha256={name:hashlib.sha256((ROOT/'tools'/name).read_bytes()).hexdigest()
                                 for name in ('battery_bar_fixture.py', 'audit_z7_battery_bar.py')})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, native_conversions=len(checks))))


if __name__ == '__main__': main()
