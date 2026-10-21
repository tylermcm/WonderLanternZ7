"""Compare the real Z7 route hook's stock fallback with native instructions.

The stock prologue displaced by this 12-byte hook ends after MOVW R9,#0x3A0.
The next instruction is BEQ at 0x1048B406.  Compare its input registers, N/Z,
stack and taken branch against an execution of the unmodified stock image.
All private candidate/stock bytes stay local.  No guest or hardware is started.
"""
import argparse
import json
import struct
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import (
    UC_CPU_ARM_CORTEX_A15, UC_ARM_REG_R0, UC_ARM_REG_R1,
    UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5,
    UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9,
    UC_ARM_REG_R10, UC_ARM_REG_R11, UC_ARM_REG_SP, UC_ARM_REG_LR,
    UC_ARM_REG_PC, UC_ARM_REG_CPSR,
)

BASE, SITE, BRANCH = 0x10020000, 0x1048B3FA, 0x1048B406
ANCHOR, MAGIC = 0xA1833548, 0x5A33534E
REGS = (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
        UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
        UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11)


def execute(image, scenario):
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_A15)
    u.mem_map(BASE, (len(image) + 4095) & ~4095)
    u.mem_write(BASE, image)
    u.mem_map(0x50000000, 0x3000)
    u.mem_map(0xA1833000, 0x1000)
    state = scenario['state']
    if state:
        u.mem_write(ANCHOR + 16, struct.pack('<I', state))
        u.mem_write(state + 56, struct.pack('<I', MAGIC))
    for index, reg in enumerate(REGS):
        u.reg_write(reg, 0x10203040 + index * 0x10101)
    u.reg_write(UC_ARM_REG_R0, scenario['page'])
    u.reg_write(UC_ARM_REG_R1, scenario['event'])
    u.reg_write(UC_ARM_REG_R7, scenario['r7'])
    u.reg_write(UC_ARM_REG_SP, 0x50002000)
    u.reg_write(UC_ARM_REG_LR, 0x50002F01)
    observation = {'checkpoint_reached': False}

    def hook(emulator, address, size, unused):
        if address == BRANCH:
            observation.update(
                checkpoint_reached=True,
                registers=[emulator.reg_read(reg) for reg in REGS],
                nz=emulator.reg_read(UC_ARM_REG_CPSR) & 0xC0000000,
                sp=emulator.reg_read(UC_ARM_REG_SP),
                lr=emulator.reg_read(UC_ARM_REG_LR),
                saved_stack=bytes(emulator.mem_read(
                    emulator.reg_read(UC_ARM_REG_SP), 32)).hex(),
            )
        elif observation['checkpoint_reached']:
            observation['branch_target'] = address
            emulator.emu_stop()

    u.hook_add(UC_HOOK_CODE, hook)
    try:
        u.emu_start(SITE | 1, 0, count=250)
    except Exception as error:
        observation['error'] = str(error)
    return observation


def verify(stock, image):
    if stock[SITE - BASE:SITE - BASE + 12] != bytes.fromhex(
            '2de9f04705000e4640f2a039'):
        raise ValueError('Stock route prologue is not the expected Z7 C 3.80 input')
    cases = []
    for scenario in (
        dict(name='absent-state-null-page', state=0, page=0, event=0x239, r7=0x10203040),
        dict(name='absent-state-stock-page', state=0, page=0x50000100, event=0x239, r7=0),
        dict(name='allocated-state-stock-page', state=0x50000400, page=0x50000100, event=0x23E, r7=0),
        dict(name='owned-root-navigation', state=0x50000400, page=0x50000440, event=0x261, r7=0),
        dict(name='owned-files-navigation', state=0x50000400, page=0x50037240, event=0x262, r7=0),
        dict(name='owned-switch-navigation', state=0x50000400, page=0x5003726C, event=0x262, r7=0),
    ):
        native = execute(stock, scenario)
        candidate = execute(image, scenario)
        checks = {key: candidate.get(key) == native.get(key) for key in (
            'registers', 'nz', 'sp', 'lr', 'saved_stack', 'branch_target')}
        passed = native['checkpoint_reached'] and candidate['checkpoint_reached'] and all(checks.values())
        cases.append(dict(name=scenario['name'], passed=passed, checks=checks,
                          native=native, candidate=candidate))
    return dict(passed=all(case['passed'] for case in cases), cases=cases,
                scope='Actual hook and helper instructions against stock prologue through native BEQ.',
                limitations='Compares N/Z consumed by BEQ; C/V are not consumed by that branch and R12 is caller scratch. No menu rendering, guest or hardware.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.stock.read_bytes(), args.image.read_bytes())
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(not result['passed'])
