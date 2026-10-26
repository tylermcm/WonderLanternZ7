"""Execute compiled grid selection, page entry and native geometry instructions.

UI widgets/property storage and viewport are controlled boundaries. This is not
display, startup-concurrency, image-file or physical-camera verification.
"""
import argparse
import gc
import json
from pathlib import Path
import struct

from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                              UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_SP,
                              UC_ARM_REG_LR, UC_ARM_REG_PC)
from audit_splash_image import STACK, STOP
from audit_grid_geometry import GridFixture, DESCRIPTOR
from build_grid_firmware import validate_candidate
from z30_extensions.features.grid_z7 import STATE, MAGIC, THIRDS_ID, CURSOR, HEAP_SITE


class PatchedGrid(GridFixture):
    def __init__(self, raw, viewport, crop, choice, magic=MAGIC, enabled=0):
        super().__init__(raw, viewport, crop)
        self.u.mem_map(STATE, 4096)
        self.u.mem_write(STATE, struct.pack('<2I', magic, choice) + bytes([0x5A]) * 56)
        self.enabled, self.labels, self.selections, self.rows, self.setters = enabled, [], [], [], []
        self.current_marks = []

    def hook(self, u, address, size, context):
        if address in (0x10170944, 0x1017093E):
            # Only the workspace allocator's OS mutex boundary is supplied.
            self.ret(0)
        elif address == 0x101E3BB8:
            self.ret(u.reg_read(UC_ARM_REG_R0))
        elif address == 0x104065A4 and u.reg_read(UC_ARM_REG_R0) == 0x102D:
            self.ret(self.enabled)
        elif address == 0x104065B0:
            key, value = u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)
            if key != 0x102D or value not in (0, 1):
                raise AssertionError('Nonboolean grid-property write')
            self.enabled = value
            self.setters.append((key, value))
            self.ret(1)
        elif address == 0x10405F00:
            self.ret(0)
        elif address in (0x10402BC2, 0x10404CD8):
            self.selections.append(u.reg_read(UC_ARM_REG_R1))
            if address == 0x10404CD8:
                self.current_marks.append((u.reg_read(UC_ARM_REG_R1), u.reg_read(UC_ARM_REG_R2)))
            self.ret(0)
        elif address == 0x103FBB5C:
            text = bytes(u.mem_read(u.reg_read(UC_ARM_REG_R0), 32)).split(b'\0')[0].decode('ascii')
            self.labels.append((u.reg_read(UC_ARM_REG_R1), text))
            self.ret(0)
        elif address == 0x103FCF0E:
            self.ret(0x50070000 + u.reg_read(UC_ARM_REG_R2) * 64)
        elif address == 0x103FB344:
            self.rows.append(u.reg_read(UC_ARM_REG_R1))
            self.ret(0)
        else:
            super().hook(u, address, size, context)


def audit(stock, image, report):
    checks = []
    def check(name, passed):
        checks.append(dict(name=name, passed=bool(passed)))
    functions = {key: int(value, 16) for key, value in report['features']['grid']['functions'].items()}
    persistent = 'settings' in report['features']
    cold = PatchedGrid(image, (0, 0, 720, 480), 0, 1)
    cold.u.mem_write(STACK, struct.pack('<2I', 0x12345678, STOP | 1))
    cold.u.reg_write(UC_ARM_REG_SP, STACK)
    cold.u.reg_write(UC_ARM_REG_R2, 0x22334455)
    cold.u.reg_write(UC_ARM_REG_R3, 0x66778899)
    cold.u.emu_start(HEAP_SITE | 1, STOP, count=10000 if persistent else 1000)
    check('cold-hook-defaults-fourths-and-reserves-exactly-64-bytes',
          (bytes(cold.u.mem_read(STATE, 8)) == struct.pack('<2I', MAGIC, 0)
           if persistent else bytes(cold.u.mem_read(STATE, 64)) == struct.pack('<I', MAGIC) + bytes(60))
          and struct.unpack('<I', cold.u.mem_read(CURSOR, 4))[0] == STATE + report['features']['grid']['state_bytes'])
    checks[-1]['name'] = 'cold-hook-defaults-fourths-and-reserves-reported-owned-bytes'
    check('cold-hook-replays-original-caller-stack-contract',
          cold.u.reg_read(UC_ARM_REG_PC) == STOP
          and cold.u.reg_read(UC_ARM_REG_SP) == STACK + 8
          and cold.u.reg_read(UC_ARM_REG_R0) == STATE
          and cold.u.reg_read(UC_ARM_REG_R4) == 0x12345678
          and cold.u.reg_read(UC_ARM_REG_R2) == 0x22334455
          and cold.u.reg_read(UC_ARM_REG_R3) == 0x66778899)
    owned_bytes = report['features']['grid']['state_bytes']
    reserved = bytes(cold.u.mem_read(STATE, owned_bytes))
    first = cold.call(0x101E3DAC, 1)
    second = cold.call(0x101E3DAC, 65)
    storage = cold.call(0x101E3DAC, 0x380000)
    check('original-workspace-allocator-starts-after-owned-reservation',
          (first, second, storage) == (STATE + owned_bytes,
                                      STATE + owned_bytes + 64,
                                      STATE + owned_bytes + 192))
    check('original-workspace-allocator-preserves-owned-state-and-aligns',
          bytes(cold.u.mem_read(STATE, owned_bytes)) == reserved
          and struct.unpack('<I', cold.u.mem_read(CURSOR, 4))[0]
          == STATE + owned_bytes + 192 + 0x380000
          and all(address % 64 == 0 for address in (first, second, storage)))
    del cold
    gc.collect()
    geometry_calls = 0
    for viewport in ((0, 0, 720, 480), (20, 40, 700, 440), (0, 0, 640, 426)):
        for mode in range(3):
            for crop in (0, 1, 2, 4, 8):
                original = GridFixture(stock, viewport, crop)
                stock_geometry = original.geometry(mode, 3)
                thirds_geometry = original.geometry(mode, 2)
                geometry_calls += 2
                del original
                gc.collect()
                for choice, magic, reference in ((0, MAGIC, stock_geometry), (1, MAGIC, thirds_geometry),
                                                 (42, MAGIC, stock_geometry), (1, 0, stock_geometry)):
                    fixture = PatchedGrid(image, viewport, crop, choice, magic)
                    before = bytes(fixture.u.mem_read(STATE, 64))
                    result = fixture.geometry(mode, 3)
                    geometry_calls += 1
                    check(f'geometry-{viewport}-mode{mode}-crop{crop}-choice{choice}-magic{magic}',
                          result == reference and bytes(fixture.u.mem_read(STATE, 64)) == before)
                    # Unicorn hooks retain Python callbacks. Collect each
                    # fixture cycle promptly rather than accumulating ROMs.
                    del fixture
                    gc.collect()
    for enabled, choice, expected in ((0, 0, 0x1902), (0, 1, 0x1902),
                                      (1, 0, 0x1901), (1, 1, THIRDS_ID), (1, 42, 0x1901)):
        fixture = PatchedGrid(image, (0, 0, 720, 480), 0, choice, enabled=enabled)
        # A collection pointer exercises all three existing native row widgets.
        fixture.u.mem_write(0xA1836F8C + 36, struct.pack('<I', 0x50060000))
        fixture.call(functions['enter'], 0xA1836F8C)
        check(f'page-enabled{enabled}-choice{choice}',
              fixture.selections[-1] == expected
              and fixture.current_marks == [(expected, 1)]
              and fixture.labels == [(39, '4x4 grid'), (40, '3x3 grid'), (41, 'Off')]
              and fixture.rows == [39, 40, 41])
        del fixture
        gc.collect()
    for entry, initial, expected in (('thirds', 0, 1), ('fourths', 1, 0)):
        fixture = PatchedGrid(image, (0, 0, 720, 480), 0, initial)
        fixture.call(functions[entry])
        check(entry + '-keeps-native-property-boolean-and-state-owned',
              fixture.setters == [(0x102D, 1)]
              and struct.unpack('<2I', fixture.u.mem_read(STATE, 8)) == (MAGIC, expected)
              and (fixture.u.mem_read(STATE + 8, 4) == struct.pack('<I', 1)
                   and fixture.u.mem_read(STATE + 32, 4) == struct.pack('<I', 0x5A5A5A5B)
                   if persistent else bytes(fixture.u.mem_read(STATE + 8, 56)) == bytes([0x5A]) * 56))
        del fixture
        gc.collect()
    fixture = PatchedGrid(image, (0, 0, 720, 480), 0, 1, enabled=1)
    fixture.call(0x104F5592)
    check('native-off-preserves-third-choice', fixture.enabled == 0
          and struct.unpack('<I', fixture.u.mem_read(STATE + 4, 4))[0] == 1)
    return dict(schema=1, scope=__doc__.strip(), checks=checks, geometry_calls=geometry_calls,
                all_passed=all(check['passed'] for check in checks), camera_access=False,
                main_payload_sha256=report['main_payload_sha256'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--container', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    main_path, report_path = (args.build / ('grid.emulator.' + ext) for ext in ('main.bin', 'json'))
    validate_candidate(main_path, report_path, args.container)
    result = audit(args.stock.read_bytes(), main_path.read_bytes(), json.loads(report_path.read_text()))
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(checks=len(result['checks']), all_passed=result['all_passed'])))
    if not result['all_passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
