"""Run the automatic paint hook with supplied UI/visibility/draw boundaries."""
import argparse
import gc
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1
from audit_spiral_probe import SpiralFixture, audit as audit_draw
from build_spiral_lifecycle import validate_candidate


class LifecycleFixture(SpiralFixture):
    def __init__(self, raw, report, stored=3, display=1, visible=1):
        super().__init__(raw, report['features']['spiral_probe'], stored)
        self.lifecycle = report['features']['spiral_lifecycle']
        self.visible = visible
        self.u.mem_write(0xA1829E44, struct.pack('<I', display))
        self.u.mem_write(0xA18213A4, bytes.fromhex('efbeadde'))

    def hook(self, u, address, size, context):
        if address == 0x103FB7DC:
            assert (u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)) == (1, 4)
            self.operations.append('visibility')
            self.ret(self.visible)
        elif address == int(self.feature['draw'], 16):
            self.operations.append('spiral')
            self.ret(1)
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
    checks = audit_draw(raw, report)['checks']
    for stored in (0, 1, 2, 3, 4, 5, 6, 0xFFFFFFFF):
        for display, visible in ((1, 1), (1, 0), (0, 1), (2, 1), (4, 1)):
            f = LifecycleFixture(raw, report, stored, display, visible)
            drawn = stored == 3 and display == 1 and visible != 0
            expected = (['visibility'] if stored == 3 and display == 1 else [])
            if drawn:
                expected += ['spiral']
            returned = f.call(int(f.lifecycle['helper'], 16))
            checks.append(dict(name=f'gate-value-{stored}-display-{display}-visible-{visible}',
                               passed=returned == int(drawn) and f.operations == expected))
            f.operations.clear()
            returned = f.call(0x103FCC44, 0x51512000, 0x51513000)
            checks.append(dict(name=f'original-paint-before-overlay-{stored}-{display}-{visible}',
                passed=returned == 0x71A2B3C4
                       and f.operations == ['original-wait', 'original-paint'] + expected
                       and bytes(f.u.mem_read(0xA18213A4, 4)) == bytes(4)))
            del f
            gc.collect()
    return dict(schema=1, checks=checks, all_passed=all(c['passed'] for c in checks),
                main_payload_sha256=report['main_payload_sha256'], camera_access=False,
                card_access=False, supplied_ui_graphics_boundaries=True,
                scope=__doc__.strip(), return_stack_callee_registers_checked=True)


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
