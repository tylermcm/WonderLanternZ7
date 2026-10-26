"""Instruction/ABI audit of the independent splash firmware, with mocked OS/GPU boundaries.

This tests the actual rebuilt instructions and state transitions, not display pixels.
QEMU presentation must be verified separately with the unmocked native renderer.
"""
import argparse
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R12, UC_ARM_REG_PC, UC_ARM_REG_SP, UC_ARM_REG_LR
from audit_splash_image import NativePNG, MEM, STACK, STOP, ARGUMENTS, SAVED
from build_splash_firmware import validate_candidate
from z30_extensions.assembly import assemble, constant
from z30_extensions.features.splash_z7 import STATE, CURSOR, MAGIC, GUARD, RENDER_SITE, FIRST_RENDER_CALLER


class Controller(NativePNG):
    def __init__(self, raw):
        super().__init__(raw)
        self.u.mem_map(STATE - 4096, 12288)
        self.u.mem_write(STATE - 16, b'\xCC' * 96)
        self.calls, self.draws, self.delay_result = [], [], 0
        self.forwarded = []
        self.u.mem_write(MEM + 0x800, struct.pack('<7I', 0, 0, 720, 480, 255, 0, 0))
        self.u.mem_write(MEM + 0x1000, assemble(
            'push {r4,lr};' + constant('r12', RENDER_SITE | 1)
            + 'blx r12; pop {r4,pc};', MEM + 0x1000, 64))

    def words(self):
        return struct.unpack('<16I', self.u.mem_read(STATE, 64))

    def setword(self, offset, value):
        self.u.mem_write(STATE + offset, struct.pack('<I', value))

    def hook(self, u, address, size, context):
        if address == 0x10431738:
            pointer = u.reg_read(ARGUMENTS[2])
            desc = struct.unpack('<16I', u.mem_read(pointer, 64))
            self.draws.append(dict(pointer=desc[0], size=desc[1], zero_tail=not any(desc[2:]),
                                   phase=self.words()[1], aligned=u.reg_read(UC_ARM_REG_SP) % 8 == 0))
            # Execute a real nested call through the patched renderer while busy.
            u.reg_write(UC_ARM_REG_PC, (MEM + 0x1000) | 1)
        elif address == RENDER_SITE + 10:
            sp = u.reg_read(UC_ARM_REG_SP)
            saved = struct.unpack('<3I', u.mem_read(sp + 68, 12))
            self.forwarded.append(dict(sp=sp, args=[u.reg_read(r) for r in ARGUMENTS],
                                       r12=u.reg_read(UC_ARM_REG_R12),
                                       r4=u.reg_read(SAVED[0]), r5=u.reg_read(SAVED[1]), saved=saved))
            u.reg_write(SAVED[0], saved[0])
            u.reg_write(SAVED[1], saved[1])
            u.reg_write(UC_ARM_REG_SP, sp + 80)
            u.reg_write(UC_ARM_REG_LR, saved[2])
            self.ret(0)
        elif address == 0x1017081E:
            self.calls.append((address, u.reg_read(ARGUMENTS[0]), self.words()[1]))
            self.ret(self.delay_result)
        elif address in {
            0x1017089C, 0x101E3BB8, 0x10273676, 0x10465240, 0x10401F26,
            0x10401F20, 0x10273686, 0x10297434, 0x103F9CE2, 0x103FA168,
            0x103F9C0A, 0x104066C8, 0x103FC352, 0x1040629C, 0x1033239A,
            0x102E37F2, 0x103332E8, 0x10465026, 0x10406474, 0x104064CC,
        }:
            self.calls.append((address, u.reg_read(ARGUMENTS[0]), self.words()[1]))
            self.ret(MEM + 0x200 if address == 0x10406474 else 0)
        else:
            super().hook(u, address, size, context)

    def render(self, caller=FIRST_RENDER_CALLER):
        u = self.u
        args = [MEM + 0x800, 0x1234, 0x5678, 0x9ABC]
        guards = {reg: 0x62620000 + i for i, reg in enumerate(SAVED)}
        for reg, value in zip(ARGUMENTS, args):
            u.reg_write(reg, value)
        for reg, value in guards.items():
            u.reg_write(reg, value)
        u.reg_write(UC_ARM_REG_R12, 0x12121212)
        u.reg_write(UC_ARM_REG_SP, STACK)
        u.reg_write(UC_ARM_REG_LR, caller)
        u.emu_start(RENDER_SITE | 1, caller & ~1, timeout=10000000, count=10000000)
        top = self.forwarded[-1]
        return (u.reg_read(UC_ARM_REG_PC) == caller & ~1
                and u.reg_read(UC_ARM_REG_SP) == STACK
                and all(u.reg_read(reg) == value for reg, value in guards.items())
                and top['sp'] == STACK - 80 and top['args'] == args
                and top['r4'] == args[0] and top['r5'] == 0
                and top['r12'] == 0x12121212
                and top['saved'] == (guards[SAVED[0]], guards[SAVED[1]], caller))


def audit(candidate, report_path, stock):
    identity = validate_candidate(candidate, report_path, stock)
    report = json.loads(report_path.read_text())
    feature = report['features']['splash_experiment']
    raw = candidate.read_bytes()
    f = Controller(raw)
    checks = []

    def check(name, value):
        checks.append(dict(name=name, passed=bool(value)))
        if not value:
            raise AssertionError(name)

    f.call(0x101E3D94)
    check('native-init-cold-state', f.words()[:12] == (MAGIC, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0))
    check('explicit-workspace-reservation', struct.unpack('<I', f.u.mem_read(CURSOR, 4))[0] == STATE + 64)
    check('reservation-guards', f.words()[12:] == (GUARD,) * 4)
    check('outside-reservation-untouched', bytes(f.u.mem_read(STATE - 16, 16)) == b'\xCC' * 16
          and bytes(f.u.mem_read(STATE + 64, 16)) == b'\xCC' * 16)
    f.u.mem_write(0xA181C988, bytes(4))
    f.call(0x102697F4)
    check('native-resource-calls-retained', [c[0] for c in f.calls if c[0] in (0x103FA168, 0x103F9C0A)]
          == [0x103FA168, 0x103F9C0A])
    check('armed-only-after-resource-init', f.words()[1] == 1 and f.words()[4] == 1)
    check('original-init-guard-consumed', bytes(f.u.mem_read(0xA1822D68, 4)) == bytes(4))
    check('render-forwarding-abi', f.render())
    check('firmware-native-two-image-order', [(d['pointer'], d['size']) for d in f.draws] == [
        (int(feature['splash_png'], 16), feature['splash_png_bytes']),
        (int(feature['black_png'], 16), feature['black_png_bytes'])])
    check('bounded-stack-descriptors', all(d['zero_tail'] and d['aligned'] for d in f.draws))
    check('consumed-before-recursive-render', all(d['phase'] == 2 for d in f.draws) and f.words()[6] == 2)
    check('native-delay-after-consumption', [c for c in f.calls if c[0] == 0x1017081E]
          == [(0x1017081E, 2000, 2)])
    check('completed-once', f.words()[1:6] == (3, 1, 0, 1, 1) and f.words()[10] == 1)
    check('records-original-caller', f.words()[8:10] == (FIRST_RENDER_CALLER, MEM + 0x800))
    check('second-render-abi', f.render())
    check('second-render-no-splash', len(f.draws) == 2 and f.words()[2] == 1)
    # Even re-entering original resource setup must not reset our latch.
    f.u.mem_write(0xA1822D68, struct.pack('<I', 1))
    f.call(0x102697F4)
    check('native-reinit-does-not-rearm', f.words()[1] == 3 and f.words()[2] == 1)
    for name, magic, phase, caller in (
        ('invalid-magic', 0, 1, FIRST_RENDER_CALLER),
        ('unarmed', MAGIC, 0, FIRST_RENDER_CALLER),
        ('wrong-caller', MAGIC, 1, STOP | 1),
        ('busy', MAGIC, 2, FIRST_RENDER_CALLER),
    ):
        f.setword(0, magic)
        f.setword(4, phase)
        check(name + '-forwarding-abi', f.render(caller))
        check(name + '-no-draw', len(f.draws) == 2)
    f.setword(0, MAGIC)
    f.setword(4, 1)
    for offset, value in ((0, 1), (4, 1), (8, 64), (12, 400), (16, 0x0E0E0EFF)):
        original = bytes(f.u.mem_read(MEM + 0x800 + offset, 4))
        f.u.mem_write(MEM + 0x800 + offset, struct.pack('<I', value))
        check(f'unmatched-clear-{offset}-abi', f.render())
        check(f'unmatched-clear-{offset}-no-draw', len(f.draws) == 2 and f.words()[1] == 1)
        f.u.mem_write(MEM + 0x800 + offset, original)
    f.setword(40, 0)
    f.delay_result = 0xFFFFFFFF
    check('delay-failure-abi', f.render())
    check('delay-failure-cleans-backing-and-consumes', len(f.draws) == 4 and f.words()[1] == 4
          and f.words()[3] == 0xFFFFFFFF and f.words()[10] == 0)
    f.render()
    check('delay-failure-no-retry', len(f.draws) == 4)
    check('final-reservation-guards', f.words()[12:] == (GUARD,) * 4
          and bytes(f.u.mem_read(STATE + 64, 16)) == b'\xCC' * 16)
    f.call(0x101E3D94)
    check('cold-init-resets-owned-state', f.words()[:12] == (MAGIC, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0))
    return dict(schema=1, checks=checks, passed=all(c['passed'] for c in checks),
                main_sha256=identity['sha256'], firmware_built=True, candidate_cleared=False,
                scope='Actual firmware hook instructions in Unicorn; native OS/GPU helper boundaries mocked.',
                limitations=['Single-thread instruction audit; native concurrency requires QEMU testing.',
                             'No camera, update-acceptance, recovery or physical display evidence.'])


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--stock', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = audit(a.candidate, a.report, a.stock)
    with a.output.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=result['passed'], checks=len(result['checks']))))
