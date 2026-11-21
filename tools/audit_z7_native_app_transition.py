"""Original Z7 application-switch protocol and task-state observation gap (MIT).

Executes the original program-manager state machine and callback registration.
Task start/stop services and active program objects are supplied. This does not
identify every pending-menu request or prove native scheduling/task exclusion.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1
from audit_splash_image import NativePNG, STOCK_SHA, MEM
from audit_z7_native_touch_driver import PROGRAMS, GETTERS

CONTROL, REQUEST = PROGRAMS - 0x10, MEM + 0x10000


class AppTransition(NativePNG):
    def __init__(self, raw):
        super().__init__(raw)
        self.native_call_timeout_us = 0
        self.services = []

    def read(self, address):
        return int.from_bytes(self.u.mem_read(address, 4), 'little')

    def write(self, address, value):
        self.u.mem_write(address, struct.pack('<I', value))

    def hook(self, u, address, size, context):
        if address in (0x1015b862, 0x1015b866):
            self.services.append((address, u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)))
            self.ret(0)
            return
        super().hook(u, address, size, context)


def audit(raw):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA:
        raise ValueError('Requires exact original Z7 C3.80 MAIN')
    f = AppTransition(raw)
    checks = []

    def check(name, good):
        assert good, name
        checks.append(name)

    # CONTROL+8 is a registered acknowledgement CALLBACK, not a request flag.
    callback, context = MEM + 0x70001, 0x12345678
    f.write(CONTROL + 8, 0)
    check('ack-callback-registers', f.call(0x1008fcc2, callback, context) == 1 and
          (f.read(CONTROL + 8), f.read(CONTROL + 12)) == (callback, context))
    check('ack-callback-occupied-rejects', f.call(0x1008fcc2, callback + 2, 7) == 0 and
          (f.read(CONTROL + 8), f.read(CONTROL + 12)) == (callback, context))
    check('ack-callback-clears', f.call(0x1008fcc2, 0, 0) == 1 and f.read(CONTROL + 8) == 0)
    objects = [f.call(getter) for getter in GETTERS]
    for index, obj in enumerate(objects):
        f.write(PROGRAMS + 0x10 + 12 * index, obj)
    f.write(CONTROL, 1)
    f.write(CONTROL + 4, 1)
    snapshots = []
    for target in range(5):
        current = (target - 1) % 5  # Includes AUTOOP0 -> MENU1.
        f.u.mem_write(PROGRAMS, bytes([current, 5, 0, 0]))
        f.write(PROGRAMS + 8, 2)
        f.u.mem_write(0xa182ecb8 + 0x74, b'\4')
        f.u.mem_write(0xa183dd90 + 0x74, b'\4')
        f.u.mem_write(REQUEST, struct.pack('<2I', target, 0x2468))
        f.services.clear()
        # Event4 supplies a new target while native manager state2 is idle.
        f.call(0x1008fcd8, 4, REQUEST)
        check(f'target{target}-stop-current-before-start', len(f.services) == 1 and
              f.services[0][0:2] == (0x1015b866, objects[current]))
        check(f'target{target}-pending-state3-retains-current', bytes(f.u.mem_read(PROGRAMS, 2)) == bytes([current, target]) and
              f.read(PROGRAMS + 8) == 3 and f.read(PROGRAMS + 4) == 0x2468)
        check(f'target{target}-menu-play-task-states-can-still-be4',
              bytes(f.u.mem_read(0xa182ecb8 + 0x74, 1)) == bytes(f.u.mem_read(0xa183dd90 + 0x74, 1)) == b'\4')
        snapshots.append(dict(target=target, current=current, pending_manager_state=3, menu_state=4, play_state=4))
        # Event3 completes stop; the manager requests target start and waits1.
        f.call(0x1008fcd8, 3, 0)
        check(f'target{target}-start-target-awaits-state1', f.services[-1] == (0x1015b862, objects[target], 0x2468) and
              f.read(PROGRAMS + 8) == 1)
        # Event2 acknowledges start, selects target, and returns to idle2.
        f.call(0x1008fcd8, 2, 0)
        check(f'target{target}-start-ack-selects-target-and-idles2', bytes(f.u.mem_read(PROGRAMS, 2)) == bytes([target, 5]) and
              f.read(PROGRAMS + 8) == 2)
        check(f'target{target}-native-active-program-getter-agrees', f.call(0x1008fdc0) == objects[target])
    return dict(schema=1, passed=True, checks=len(checks), check_names=checks,
                stock_main_sha256=STOCK_SHA, native_targets=5, pending_snapshots=snapshots,
                stable_program_manager_state=2, stop_pending_state=3, start_pending_state=1,
                acknowledgement_callback_address='0xa1815c5c', program_manager_state_address='0xa1815c6c',
                scope='Original program-manager events4/3/2, stop/start/ack transition and actual active-program getter; callback registration identity prevents misclassifying a function pointer as a pending flag',
                supplied_boundaries=['active program objects', 'task stop/start services'],
                limits=['No real task state evolution, scheduling or exclusion', 'Does not locate every pending menu/UI request', 'No installed transition guard, camera boot, flash or recovery proof'],
                installation_candidate=False,
                source_sha256={str(p.relative_to(Path(__file__).resolve().parent.parent)).replace('\\', '/'):
                               hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in (Path(__file__).resolve(), Path(__file__).resolve().with_name('audit_splash_image.py'),
                                         Path(__file__).resolve().with_name('audit_z7_native_touch_driver.py'),
                                         Path(__file__).resolve().with_name('audit_z7_native_touch_queue.py'))})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--main', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Output must not already exist')
    result = audit(args.main.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('check_names', 'source_sha256')}))


if __name__ == '__main__':
    main()
