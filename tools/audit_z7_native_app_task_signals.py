"""Original Z7 program stop callbacks and native task-start signaling (MIT).

Executes original manager, veneers, all five stop callbacks, wake flag getter/
setter and task-start wrapper. Only the final kernel event-set result is supplied.
This does not run task polls, scheduling, real handles or task acknowledgement.
"""
import argparse
import hashlib
import json
from pathlib import Path

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1
from audit_splash_image import NativePNG, STOCK_SHA, MEM
from audit_z7_native_app_transition import AppTransition, audit as transition_audit
from audit_z7_native_touch_driver import GETTERS

WAKE_WORD, WAKE = 0xa181f910, MEM + 0x90000
STOPS = (0x10269a16, 0x1048b35a, 0x1050095a, 0x10333706, 0x1026ad26)


class NativeTaskSignals(AppTransition):
    instances = []
    kernel_result = 0

    def __init__(self, raw):
        super().__init__(raw)
        self.write(WAKE_WORD, WAKE)
        self.kernel_events = []
        self.stop_callbacks = []
        self.visited = set()
        self.instances.append(self)

    def hook(self, u, address, size, context):
        if address in (0x1015b862, 0x1015b866):
            self.services.append((address, u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)))
        if address in STOPS:
            self.stop_callbacks.append(address)
        if address in (0x1020ba86, 0x1020ba90, 0x10406474, 0x104064cc, 0x103ff902):
            self.visited.add(address)
        if address == 0x10170be8:
            self.kernel_events.append((u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)))
            self.ret(self.kernel_result)
            return
        # Deliberately bypass AppTransition's modeled start/stop veneers.
        NativePNG.hook(self, u, address, size, context)


def audit(raw):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA:
        raise ValueError('Requires exact original Z7 C3.80 MAIN')
    scenarios = []
    checks = 0
    for result in (0, 0x80000001):
        NativeTaskSignals.kernel_result = result
        core = transition_audit(raw, NativeTaskSignals)
        f = NativeTaskSignals.instances.pop()
        checks += core['checks']
        objects = [f.call(getter) for getter in GETTERS]
        expected = [pair for target in range(5) for pair in ((WAKE, 1), (objects[target] + 0x20, 1))]
        assert f.kernel_events == expected
        assert f.stop_callbacks == [STOPS[(target - 1) % 5] for target in range(5)]
        assert f.visited == {0x1020ba86, 0x1020ba90, 0x10406474, 0x104064cc, 0x103ff902}
        assert all(f.read(obj + 0x30) == 0x2468 for obj in objects)
        checks += 4
        scenarios.append(dict(kernel_event_set_result=result, core_checks=core['checks'],
                              native_stop_callbacks=5, native_start_signals=5,
                              manager_enters_pending_states_without_checking_event_set_result=True))
    names = ('audit_z7_native_app_task_signals.py', 'audit_z7_native_app_transition.py',
             'audit_z7_native_touch_driver.py', 'audit_z7_native_touch_queue.py', 'audit_splash_image.py')
    root = Path(__file__).resolve().parent.parent
    return dict(schema=1, passed=True, checks=checks, scenarios=scenarios,
                stock_main_sha256=STOCK_SHA,
                original_manager_stop_callbacks_wake_wrappers_and_start_signals_execute=True,
                supplied_boundaries=['active program objects and supplied opaque event handle', 'kernel event-set result', 'external start/stop acknowledgements'],
                findings=['Native stop callbacks signal shared wake bit1; they do not themselves run task polls',
                          'Native task-start wrapper stores parameter at object+30 and signals object+20 bit1',
                          'Program manager enters pending states with either supplied event-set return; external acknowledgements are still required'],
                limits=['No task poll, actual acknowledgement, scheduling or lifetime proof', 'No real kernel handles or kernel-failure recovery proof', 'No physical camera, flash or recovery clearance'],
                installation_candidate=False,
                source_sha256={'tools/'+name:hashlib.sha256((root/'tools'/name).read_bytes()).hexdigest() for name in names})


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
    print(json.dumps({k:v for k,v in result.items() if k != 'source_sha256'}))


if __name__ == '__main__':
    main()
