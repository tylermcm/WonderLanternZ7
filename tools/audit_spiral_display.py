"""Execute native-display spiral routing with supplied UI/graphics boundaries.

The LCD/EVF descriptors and registry entries below are synthetic fixtures, not
observations of physical EVF output. The original API call contract is checked.
"""
import argparse
import gc
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_CPSR
from audit_spiral_probe import SpiralFixture
from audit_splash_image import MEM
from build_spiral_lifecycle import validate_candidate


class DisplayFixture(SpiralFixture):
    def __init__(self, raw, report, stored=3, display=1, visible=1, scenario='normal'):
        super().__init__(raw, report['features']['spiral_probe'], stored)
        self.display, self.visible, self.case = display, visible, scenario
        self.lifecycle = report['features']['spiral_lifecycle']
        self.descriptor = MEM + 0x6000
        self.target = 6 if display == 4 else 5
        width, height = (1280, 960) if display == 4 else (720, 480)
        # Deliberately distinct synthetic surfaces ensure EVF never selects LCD.
        surface = 0xB0700000 if display == 4 else 0xB045F200
        self.u.mem_write(0xA1829E44, struct.pack('<I', display))
        self.u.mem_write(0xA18213A4, bytes.fromhex('efbeadde'))
        descriptor = bytearray(64)
        struct.pack_into('<I', descriptor, 8, width | height << 16)
        struct.pack_into('<I', descriptor, 0x24, surface)
        if scenario == 'null-pixels':
            struct.pack_into('<I', descriptor, 0x24, 0)
        if scenario == 'wrong-native-size':
            struct.pack_into('<I', descriptor, 8, 640 | 480 << 16)
        self.u.mem_write(self.descriptor, bytes(descriptor))
        entry = struct.pack('<IBxHH10x', surface, 15, width, height)
        self.u.mem_write(MEM + self.target * 20, entry)
        if scenario == 'missing':
            self.u.mem_write(MEM + self.target * 20, bytes(4))
        elif scenario == 'inactive':
            self.u.mem_write(MEM + self.target * 20 + 4, b'\xff')
        elif scenario == 'wrong-registry-size':
            self.u.mem_write(MEM + self.target * 20 + 6, struct.pack('<H', width-1))
        elif scenario == 'duplicate':
            self.u.mem_write(MEM + 7 * 20, entry)
        elif scenario == 'null-registry':
            self.u.mem_write(0xA180AD88, bytes(4))
        elif scenario == 'invalid-current':
            self.u.mem_write(0xA180AD84, b'\xff')

    def hook(self, u, address, size, context):
        if address == 0x10433B80:
            assert (u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1),
                    u.reg_read(UC_ARM_REG_R2)) == (1, self.display, 0)
            self.operations.append('native-ui-descriptor')
            self.ret(0 if self.case == 'null-descriptor' else self.descriptor)
        elif address == 0x103FB7DC:
            assert (u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)) == (self.display, 4)
            self.operations.append('visibility')
            self.ret(self.visible)
        elif address == 0x104146A8:
            index = u.reg_read(UC_ARM_REG_R0)
            self.operations.append(('select', index))
            if self.case == 'select-fails' and index == self.target:
                self.ret(0)
            else:
                self.current = index
                self.ret(1)
        elif address == 0x10431738:
            assert self.current == self.target
            assert (u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)) == (0, 0)
            prefix = 'evf_' if self.display == 4 else ''
            expected = struct.pack('<II', int(self.feature[prefix+'png'], 16),
                                   self.feature[prefix+'png_bytes']) + bytes(40)
            assert bytes(u.mem_read(u.reg_read(UC_ARM_REG_R2), 48)) == expected
            self.operations.append('draw-evf' if self.display == 4 else 'draw-lcd')
            self.ret(0)
        elif address == 0x103FA97C:
            assert u.reg_read(UC_ARM_REG_R0) == 10000
            self.operations.append('original-wait')
            self.ret(0)
        elif address == 0x10295822:
            assert (u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)) == (0x51512000, 0x51513000)
            self.operations.append('original-paint')
            self.ret(0x71A2B3C4)
        else:
            super().hook(u, address, size, context)


def audit(raw, report):
    assert report['preset'] == 'grid-spiral-display-lifecycle-emulator-only'
    checks = []
    for stored in (0, 1, 2, 3, 4, 5, 6, 0xFFFFFFFF):
        for display, visible in ((1, 1), (4, 1), (1, 0), (4, 0), (0, 1), (2, 1), (7, 1)):
            f = DisplayFixture(raw, report, stored, display, visible)
            accepted = stored == 3 and display in (1, 4)
            drawn = accepted and visible != 0
            expected = ['visibility'] if accepted else []
            if drawn:
                expected += ['lock', 'native-ui-descriptor', 'query', ('select', f.target),
                             'draw-evf' if display == 4 else 'draw-lcd', ('select', 2), 'unlock']
            returned = f.call(int(f.lifecycle['helper'], 16))
            checks.append(dict(name=f'active-display-value-{stored}-{display}-{visible}',
                               passed=returned == int(drawn) and f.operations == expected and f.current == 2))
            f.operations.clear()
            f.u.reg_write(UC_ARM_REG_CPSR, 0xB8000033)
            returned = f.call(0x103FCC44, 0x51512000, 0x51513000)
            flags = f.u.reg_read(UC_ARM_REG_CPSR) & 0xF8000000
            checks.append(dict(name=f'paint-return-stack-flags-{stored}-{display}-{visible}',
                passed=returned == 0x71A2B3C4 and flags == 0x78000000
                       and f.operations == ['original-wait', 'original-paint'] + expected
                       and bytes(f.u.mem_read(0xA18213A4, 4)) == bytes(4) and f.current == 2))
            del f
            gc.collect()
    for display in (1, 4):
        for scenario in ('null-descriptor', 'null-pixels', 'wrong-native-size', 'missing',
                         'inactive', 'wrong-registry-size', 'duplicate', 'null-registry',
                         'invalid-current', 'select-fails'):
            f = DisplayFixture(raw, report, display=display, scenario=scenario)
            returned = f.call(int(f.feature['draw'], 16))
            checks.append(dict(name=f'refusal-display-{display}-{scenario}',
                passed=returned == 0 and not any(str(op).startswith('draw-') for op in f.operations)
                       and f.operations[0] == 'lock' and f.operations[-1] == 'unlock'
                       and f.current == 2))
            del f
            gc.collect()
    return dict(schema=1, checks=checks, all_passed=all(c['passed'] for c in checks),
                main_payload_sha256=report['main_payload_sha256'], camera_access=False,
                card_access=False, supplied_ui_graphics_boundaries=True,
                return_stack_callee_registers_and_nzcvq_checked=True, scope=__doc__.strip())


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--stock', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    main, metadata = args.build/'spiral.emulator.main.bin', args.build/'spiral.emulator.json'
    validate_candidate(main, metadata, args.stock)
    result = audit(main.read_bytes(), json.loads(metadata.read_text()))
    args.output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(checks=len(result['checks']), all_passed=result['all_passed'])))
    raise SystemExit(not result['all_passed'])
