"""Execute the compiled spiral helper with supplied native graphics boundaries.

Checks gating, native lock/select/draw/restore order, descriptors and ABI. Native
graphics API implementations are separately exercised in the QEMU drawing probe.
"""
import argparse
import gc
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2
from audit_splash_image import NativePNG, MEM
from build_spiral_probe import validate_candidate


class SpiralFixture(NativePNG):
    def __init__(self, raw, feature, stored=3, scenario='normal'):
        super().__init__(raw)
        self.feature, self.scenario, self.operations = feature, scenario, []
        self.current = self.original = 2
        self.u.mem_map(0xA2400000, 0x100000)
        self.u.mem_write(0xA24F182C, struct.pack('<I', stored))
        self.u.mem_write(0xA180AD84, struct.pack('<3I', 12, MEM, 0))
        records = bytearray(33 * 20)
        for index in range(33):
            records[index * 20 + 4] = 0xFF
        struct.pack_into('<IBxHH', records, 2 * 20, 0xB0000000, 12, 720, 480)
        struct.pack_into('<IBxHH', records, 5 * 20, 0xB045F200, 15, 720, 480)
        if scenario == 'missing':
            struct.pack_into('<I', records, 5 * 20, 0)
        elif scenario == 'duplicate':
            records[6 * 20:7 * 20] = records[5 * 20:6 * 20]
        elif scenario == 'wrong-size':
            struct.pack_into('<H', records, 5 * 20 + 6, 640)
        elif scenario == 'inactive':
            records[5 * 20 + 4] = 0xFF
        elif scenario == 'null-registry':
            self.u.mem_write(0xA180AD84 + 4, bytes(4))
        elif scenario == 'invalid-current':
            self.u.mem_write(0xA180AD84, b'\xff')
        self.u.mem_write(MEM, bytes(records))

    def hook(self, u, address, size, context):
        if address in (0x10413FF4, 0x10413FFA):
            self.operations.append('lock' if address == 0x10413FF4 else 'unlock')
            self.ret(0)
        elif address == 0x10414756:
            self.operations.append('query')
            self.ret(self.current)
        elif address == 0x104146A8:
            index = u.reg_read(UC_ARM_REG_R0)
            self.operations.append(('select', index))
            if self.scenario == 'select-fails' and index == 5:
                self.ret(0)
            else:
                self.current = index
                self.ret(1)
        elif address == 0x10431738:
            self.operations.append('draw')
            if self.current != 5 or u.reg_read(UC_ARM_REG_R0) or u.reg_read(UC_ARM_REG_R1):
                raise AssertionError('PNG draw did not use the selected UI surface at origin')
            descriptor = bytes(u.mem_read(u.reg_read(UC_ARM_REG_R2), 48))
            expected = struct.pack('<II', int(self.feature['png'], 16), self.feature['png_bytes']) + bytes(40)
            if descriptor != expected:
                raise AssertionError('PNG descriptor differs from immutable asset contract')
            self.ret(0)
        else:
            super().hook(u, address, size, context)


def audit(raw, report):
    feature = report['features']['spiral_probe']
    function = int(feature['draw'], 16)
    checks = []
    for stored in (0, 1, 2, 3, 4, 5, 6, 0xFFFFFFFF):
        f = SpiralFixture(raw, feature, stored)
        returned = f.call(function)
        expected = ['lock', 'query', ('select', 5), 'draw', ('select', 2), 'unlock'] if stored == 3 else []
        checks.append(dict(name='stored-value-gate-and-call-order-' + str(stored),
                           passed=returned == int(stored == 3) and f.operations == expected and f.current == 2))
        del f
        gc.collect()
    for scenario in ('missing', 'duplicate', 'wrong-size', 'inactive', 'null-registry', 'invalid-current', 'select-fails'):
        f = SpiralFixture(raw, feature, scenario=scenario)
        returned = f.call(function)
        checks.append(dict(name='safe-refusal-' + scenario, passed=returned == 0
            and f.operations[0] == 'lock' and f.operations[-1] == 'unlock'
            and 'draw' not in f.operations and f.current == f.original))
        del f
        gc.collect()
    return dict(schema=1, main_payload_sha256=report['main_payload_sha256'],
        checks=checks, all_passed=all(check['passed'] for check in checks),
        scope=__doc__.strip(), native_graphics_boundaries_supplied=True,
        return_pc_stack_callee_registers_checked=True, camera_access=False, card_access=False)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--stock', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    main = args.build / 'spiral.emulator.main.bin'
    metadata = args.build / 'spiral.emulator.json'
    validate_candidate(main, metadata, args.stock)
    result = audit(main.read_bytes(), json.loads(metadata.read_text()))
    args.output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(checks=len(result['checks']), all_passed=result['all_passed'])))
    raise SystemExit(not result['all_passed'])
