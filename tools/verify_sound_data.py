"""Compare the real Z7 sound-data fallback with the native displaced prologue.

The original LDR R5 loads 0xA188D190; the resumed ADDS R5,#0x10 advances it
to the table at 0xA188D1A0.  Compare immediately after that native ADDS, so
literal reconstruction, argument registers, stack and flags are checked against
stock instructions.  Private firmware remains local; no guest is started.
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
    UC_ARM_REG_CPSR,
)
from z30_extensions.features.sound_layout_z7 import OWNED_AUDIO_KIND

BASE, SITE, CHECKPOINT = 0x10020000, 0x1006BFE6, 0x1006BFF2
AUDIO, ANCHOR, MAGIC = 0xA21AB994, 0xA1833548, 0x5A33534E
REGS = (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
        UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
        UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11)


def execute(image, scenario, complete):
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_A15)
    u.mem_map(BASE, (len(image) + 4095) & ~4095)
    u.mem_write(BASE, image)
    u.mem_map(0x50000000, 0x3000)
    u.mem_map(0xA1833000, 0x1000)
    u.mem_map(0xA21AB000, 0x1000)
    u.mem_write(AUDIO + 28, bytes([scenario['mode']]))
    u.mem_write(AUDIO + 32, struct.pack('<I', complete if scenario['owned'] else 0))
    if scenario['state']:
        u.mem_write(ANCHOR + 16, struct.pack('<I', 0x50000400))
        u.mem_write(0x50000400 + 56, struct.pack('<I', MAGIC))
        # LENGTH remains zero: an allocated state with no loaded WAV.
    for index, reg in enumerate(REGS):
        u.reg_write(reg, 0x70000000 + index * 0x100)
    u.reg_write(UC_ARM_REG_R0, 0x50000100)
    u.reg_write(UC_ARM_REG_SP, 0x50002000)
    u.reg_write(UC_ARM_REG_LR, 0x50002F01)
    observation = {'checkpoint_reached': False}

    def hook(emulator, address, size, unused):
        if address == CHECKPOINT:
            sp = emulator.reg_read(UC_ARM_REG_SP)
            observation.update(
                checkpoint_reached=True,
                registers=[emulator.reg_read(reg) for reg in REGS],
                nzcv=emulator.reg_read(UC_ARM_REG_CPSR) & 0xF0000000,
                sp=sp,
                lr=emulator.reg_read(UC_ARM_REG_LR),
                saved_stack=bytes(emulator.mem_read(sp + 24, 16)).hex(),
            )
            emulator.emu_stop()

    u.hook_add(UC_HOOK_CODE, hook)
    try:
        u.emu_start(SITE | 1, 0, count=250)
    except Exception as error:
        observation['error'] = str(error)
    return observation


def verify(stock, image, complete):
    if stock[SITE - BASE:SITE - BASE + 12] != bytes.fromhex(
            '70b5134c0646144d86b01035'):
        raise ValueError('Stock data prologue is not the expected Z7 C 3.80 input')
    if struct.unpack_from('<I', stock, 0x1006C040 - BASE)[0] != 0xA188D190:
        raise ValueError('Unexpected stock R5 literal')
    cases = []
    for scenario in (
        dict(name='default-off', mode=0, owned=False, state=False),
        dict(name='other-audio-callback', mode=OWNED_AUDIO_KIND, owned=False, state=False),
        dict(name='owned-callback-no-state', mode=OWNED_AUDIO_KIND, owned=True, state=False),
        dict(name='owned-callback-empty-state', mode=OWNED_AUDIO_KIND, owned=True, state=True),
    ):
        native = execute(stock, scenario, complete)
        candidate = execute(image, scenario, complete)
        checks = {key: candidate.get(key) == native.get(key) for key in (
            'registers', 'nzcv', 'sp', 'lr', 'saved_stack')}
        passed = native['checkpoint_reached'] and candidate['checkpoint_reached'] and all(checks.values())
        cases.append(dict(name=scenario['name'], passed=passed, checks=checks,
                          native=native, candidate=candidate))
    return dict(passed=all(case['passed'] for case in cases), cases=cases,
                scope='Actual fallback/helper instructions against stock through resumed ADDS R5,#0x10.',
                limitations='Local uninitialized scratch and caller-scratch R12 are excluded. No menu rendering, file I/O or audio playback.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    complete = int(report['features']['shutter_sound']['functions']['complete'], 16)
    result = verify(args.stock.read_bytes(), args.image.read_bytes(), complete)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(not result['passed'])
