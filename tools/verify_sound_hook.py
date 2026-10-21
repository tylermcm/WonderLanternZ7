"""Execute the real Z7 config call window with a controlled native-parser boundary.

Checks the default-off fallback preserves the original parser's return value,
arguments, callee-saved R4 and SP, and presents an aligned stack to the parser.
"""
import argparse
import json
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import (UC_CPU_ARM_CORTEX_A15, UC_ARM_REG_R0,
                              UC_ARM_REG_R1, UC_ARM_REG_R4, UC_ARM_REG_SP,
                              UC_ARM_REG_LR, UC_ARM_REG_PC)

BASE, SITE, PARSER, CONTINUATION = 0x10020000, 0x1006BD54, 0x1006B794, 0x1006BD58


def verify(image):
    cases = []
    for returned in (0, 1, 0x12345678):
        u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_A15)
        u.mem_map(BASE, (len(image) + 4095) & ~4095)
        u.mem_write(BASE, image)
        u.mem_map(0xA21AB000, 4096)  # Default-off audio service state, all zero.
        u.mem_map(0x50000000, 0x2000)
        initial_sp, argument, saved_r4 = 0x50001000, 0x50000100, 0xCAFEBABE
        u.reg_write(UC_ARM_REG_SP, initial_sp)
        u.reg_write(UC_ARM_REG_R0, argument)
        u.reg_write(UC_ARM_REG_R1, 0x87654321)
        u.reg_write(UC_ARM_REG_R4, saved_r4)
        observation = {'parser_return': returned, 'calls': 0, 'returned': False}

        def hook(emulator, address, size, unused):
            if address == PARSER:
                observation['calls'] += 1
                observation['parser_sp'] = hex(emulator.reg_read(UC_ARM_REG_SP))
                observation['parser_stack_aligned'] = emulator.reg_read(UC_ARM_REG_SP) % 8 == 0
                observation['arguments_preserved'] = (
                    emulator.reg_read(UC_ARM_REG_R0) == argument and
                    emulator.reg_read(UC_ARM_REG_R1) == 0x87654321)
                emulator.reg_write(UC_ARM_REG_R0, returned)
                emulator.reg_write(UC_ARM_REG_PC, emulator.reg_read(UC_ARM_REG_LR))
            elif address == CONTINUATION:
                observation['returned'] = True
                observation['actual_r0'] = hex(emulator.reg_read(UC_ARM_REG_R0))
                observation['return_preserved'] = emulator.reg_read(UC_ARM_REG_R0) == returned
                observation['stack_restored'] = emulator.reg_read(UC_ARM_REG_SP) == initial_sp
                observation['r4_preserved'] = emulator.reg_read(UC_ARM_REG_R4) == saved_r4
                emulator.emu_stop()

        u.hook_add(UC_HOOK_CODE, hook)
        u.emu_start(SITE | 1, 0, count=200)
        observation['passed'] = observation['calls'] == 1 and all(observation.get(key) for key in (
            'returned', 'parser_stack_aligned', 'arguments_preserved', 'return_preserved',
            'stack_restored', 'r4_preserved'))
        cases.append(observation)
    return {'passed': all(case['passed'] for case in cases), 'cases': cases,
            'scope': 'Real Z7 callsite/trampoline/config fallback; parser return controlled at native entry.',
            'limitations': 'Synthetic RAM and default-off branch; not audio playback or camera acceptance.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.image.read_bytes())
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(not result['passed'])
