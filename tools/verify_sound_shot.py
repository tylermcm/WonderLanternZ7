"""Compare all three native shot callback paths and execute capture gating.

Callback, property RAM and audio queue are controlled boundaries. This does not
establish which events a physical electronic-shutter exposure produces. The
normal-notification queue expectations below encode an unproven capture meaning;
the owner subsequently reported repeated audio without shooting in live view.
These checks cannot clear that failure. See audit_sound_retrigger.py for the
notification-only rejection requirements that fail on the current image.
"""
import argparse
import json
from pathlib import Path
import struct

from unicorn.arm_const import (
    UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
    UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
    UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
    UC_ARM_REG_R12, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_CPSR,
)
from verify_sound_playback import Fixture, STATE, STACK, RETURN, ANCHOR

CALLBACK, OBJECT, EPILOGUE = 0x500FF100, 0xA18D1B98, 0x100726C4
MESSAGE = 0x50003000
REGS = (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
        UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
        UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
        UC_ARM_REG_R12, UC_ARM_REG_SP, UC_ARM_REG_LR)


class ShotFixture(Fixture):
    def __init__(self, stock, image, report, *, movie=0, silent=1, **kwargs):
        self.native_calls, self.labels, self.order = [], {}, []
        self.native_selection = []
        super().__init__(stock, image, report, movie=movie, silent=silent, **kwargs)

    def hook(self, u, address, size, context):
        if address == EPILOGUE:
            self.reached = True
            u.emu_stop()
        elif address == CALLBACK:
            r0, r1 = (u.reg_read(reg) for reg in (UC_ARM_REG_R0, UC_ARM_REG_R1))
            self.native_calls.append(dict(event=r0, pointer=r1, payload=self.words(r1, 8),
                                          stack_aligned=u.reg_read(UC_ARM_REG_SP) % 8 == 0))
            self.order.append('native_callback')
            for reg, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                                   UC_ARM_REG_R3, UC_ARM_REG_R12), range(0x3300, 0x3305)):
                u.reg_write(reg, value)
            u.reg_write(UC_ARM_REG_CPSR, (u.reg_read(UC_ARM_REG_CPSR) & ~0xF8000000) | 0xA8000000)
            u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR))
        elif address == 0x10405F00:
            self.ret(0)  # Native page construction UI-state boundary.
        elif address in (0x10402BC2, 0x10404CD8):
            self.native_selection.append(u.reg_read(UC_ARM_REG_R1))
            self.ret(0)
        elif address == 0x103FBB5C:
            pointer, slot = (u.reg_read(reg) for reg in (UC_ARM_REG_R0, UC_ARM_REG_R1))
            self.labels[slot] = bytes(u.mem_read(pointer, 80)).split(b'\0')[0].decode()
            self.ret(0)
        elif address in (0x1007158C, 0x1017088C):
            self.ret(0)  # Controller helper / semaphore boundaries, not sensor I/O.
        else:
            if address == self.f['trigger']:
                self.order.append('trigger')
            super().hook(u, address, size, context)

    def run_path(self, path, *, callback=True, absent=False):
        self.reached = False
        if absent:
            self.word(ANCHOR + 16, 0)
        self.word(OBJECT + 0x44, CALLBACK | 1 if callback else 0)
        for i, reg in enumerate(REGS[:13]):
            self.u.reg_write(reg, 0x11000000 + i * 0x101)
        self.u.reg_write(UC_ARM_REG_R5, OBJECT)
        self.u.reg_write(UC_ARM_REG_R6, 2)
        self.u.reg_write(UC_ARM_REG_R8, 0x04190001)
        self.u.reg_write(UC_ARM_REG_R2, CALLBACK | 1)
        self.u.reg_write(UC_ARM_REG_SP, STACK)
        self.u.reg_write(UC_ARM_REG_LR, RETURN | 1)
        payload = struct.pack('<8I', *range(0x7700, 0x7708))
        self.u.mem_write(STACK, payload)
        entry = {'completion': 0x10072722, 'alternate': 0x1007263A,
                 'normal': 0x100726A4}.get(path, 0x100725A0)
        if path.startswith('dispatch'):
            self.u.mem_write(OBJECT - 0x80 + 2, bytes([int(path == 'dispatch4')]))
            self.word(OBJECT - 0x80 + 0x44, 0)
            for offset in (0x1C, 0x20, 0x28, 0x2C):
                self.word(OBJECT + offset, int(offset == 0x20 and path == 'dispatch2'))
            self.u.mem_write(MESSAGE, payload)
            self.u.reg_write(UC_ARM_REG_R0, 0x041F0001)
            self.u.reg_write(UC_ARM_REG_R1, MESSAGE)
        error = None
        try:
            self.u.emu_start(entry | 1, RETURN, count=5000)
        except Exception as exc:
            error = str(exc)
        return dict(reached=self.reached, error=error, native_calls=self.native_calls,
                    registers=[self.u.reg_read(reg) for reg in REGS],
                    flags=self.u.reg_read(UC_ARM_REG_CPSR) & 0xF8000000,
                    payload=bytes(self.u.mem_read(STACK, 32)).hex())


def verify(stock, image, report):
    checks = []

    def check(name, passed):
        checks.append(dict(name=name, passed=bool(passed)))

    for path, enabled, absent, callback in (
        ('completion', 1, False, True), ('alternate', 1, False, True),
        ('completion', 0, False, True), ('alternate', 0, False, True),
        ('completion', 0, True, True), ('alternate', 0, True, True),
        ('completion', 1, False, False),
        ('normal', 1, False, True), ('normal', 0, False, True),
        ('normal', 0, True, True), ('normal', 1, False, False),
        ('dispatch0', 1, False, True), ('dispatch2', 1, False, True),
        ('dispatch4', 1, False, True), ('dispatch0', 0, False, True),
        ('dispatch0', 0, True, True), ('dispatch0', 1, False, False),
    ):
        kwargs = dict(enabled=enabled)
        native = ShotFixture(stock, stock, report, **kwargs)
        patched = ShotFixture(stock, image, report, **kwargs)
        before = native.run_path(path, absent=absent, callback=callback)
        after = patched.run_path(path, absent=absent, callback=callback)
        label = f'{path}-enabled{enabled}-absent{int(absent)}-callback{int(callback)}'
        check(label + '-preserves-native-callback-and-return', before == after and after['reached'])
        expected = int(path in ('normal', 'dispatch0', 'dispatch2')
                       and enabled and not absent and callback)
        check(label + '-queues-only-enabled-normal-capture', len(patched.jobs) == expected)
        if expected:
            check(label + '-callback-before-trigger', patched.order == ['native_callback', 'trigger'])

    for name, kwargs, expected_status in (
        ('photo-mode-block', dict(movie=1), 1),
        ('silent-mode-block', dict(silent=0), 2),
        ('native-busy-block', dict(native_busy=1), 3),
    ):
        f = ShotFixture(stock, image, report, enabled=1, **kwargs)
        result = f.run_path('dispatch0')
        check(name, result['reached'] and len(f.native_calls) == 1 and not f.jobs
              and f.words(STATE + 116, 1)[0] == expected_status)

    for status, title in enumerate(('Waiting for capture', 'Photo mode required',
                                   'Silent mode required', 'Capture audio busy',
                                   'Capture sound queued', 'Capture callback seen',
                                   'Completion callback seen')):
        f = ShotFixture(stock, image, report, enabled=1)
        f.word(STATE + 116, status)
        f.call(f.f['labels'])
        check('status-title-' + str(status), f.labels.get(40) == title)

    f = ShotFixture(stock, image, report, enabled=1)
    f.run_path('dispatch0')
    f.run_path('completion')
    check('completion-does-not-duplicate-normal-capture-sound', len(f.jobs) == 1
          and f.words(STATE + 116, 1)[0] == 4)

    # The Z7's original Silent photography page selects its ON/OFF control via
    # its real getter. Give the old Z30 property contradictory values so a
    # copied key cannot make these tests pass merely through a matching mock.
    for silent, legacy in ((1, 0), (0, 1), (1, 2), (2, 1)):
        f = ShotFixture(stock, image, report, enabled=1, silent=silent,
                        legacy_silent=legacy)
        f.call(0x1049AC30, (STATE + 64,))
        expected_control = 0x15F2 if silent == 1 else 0x1567
        prefix = f'z7-silent{silent}-legacy{legacy}'
        check(prefix + '-native-menu-selection', f.native_selection == [expected_control] * 2
              and f.property_queries == [0x576])
        f.property_queries.clear()
        result = f.run_path('dispatch0')
        check(prefix + '-capture-matches-native-menu', result['reached']
              and len(f.jobs) == int(silent == 1)
              and f.words(STATE + 116, 1)[0] == (4 if silent == 1 else 2))
        check(prefix + '-trigger-uses-native-z7-key', f.property_queries == [0x138D, 0x576])

    return dict(passed=all(c['passed'] for c in checks), checks=checks,
                scope='All three callback paths and native dispatcher; original Silent photography menu constructor, property getter and descriptor tables; compiled trigger, native epilogue and diagnostic bindings.',
                limitations='Property RAM values, UI state/selection, controller helpers, semaphore, callbacks and queue boundaries controlled. No sensor exposure, real cue timing, physical audio or recovery evidence.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.stock.read_bytes(), args.image.read_bytes(), json.loads(args.report.read_text()))
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(not result['passed'])
