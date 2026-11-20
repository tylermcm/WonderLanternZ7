"""Execute native warning selection before the compiled readout callback.

SPDX-License-Identifier: MIT. Native selector, selected warning predicates,
caller instructions, update bridge and compiled policy execute. Status-property
inputs and unrelated predicates are supplied. No warning pixels or camera proof.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_SP, UC_ARM_REG_LR
from audit_splash_image import STACK, STOP
from audit_z7_display_readouts import ReadoutFixture, TABLE, SNAPSHOT
from build_z7_module_host import ROOT, STATE


class TransitionFixture(ReadoutFixture):
    def __init__(self, *args):
        super().__init__(*args)
        self.phase = False; self.properties = {}; self.errors = []
        self.predicates = {int.from_bytes(self.u.mem_read(0xa1822fb4 + i * 20, 4), 'little') & ~1: i for i in range(1, 34)}
        self.native_predicates = {16, 18, 19, 20, 26, 27, 28}
        self.trace = []

    def hook(self, u, address, size, context):
        if self.phase and address == 0x104065a4:
            key = u.reg_read(UC_ARM_REG_R0)
            self.trace.append(('status-property', key)); self.ret(self.properties.get(key, 0))
        elif self.phase and address == 0x104065a8:
            if u.reg_read(UC_ARM_REG_R0) != 0x1622 or u.reg_read(UC_ARM_REG_R2) != 0x11c:
                raise AssertionError('Native error snapshot signature')
            packet = bytearray(0x11c)
            for i, error in enumerate(self.errors): struct.pack_into('<I', packet, i * 4, error)
            struct.pack_into('<I', packet, 0x114, len(self.errors))
            u.mem_write(u.reg_read(UC_ARM_REG_R1), bytes(packet)); self.ret(0)
        elif self.phase and address == 0x103ec418:
            self.ret(0)
        elif self.phase and address in self.predicates:
            index = self.predicates[address]
            if index in self.native_predicates: self.trace.append(('native-predicate', index))
            else: self.ret(0)
        elif self.phase and address == 0x1036ae44:
            self.trace.append(('native-control-preparation-entry', 0))
        elif self.phase and address in (0x1036ad1a, 0x1036a83a, 0x1036a312, 0x10370728, 0x10369df0, 0x10369878):
            self.trace.append(('supplied-control-preparation-helper', address)); self.ret(0)
        elif self.phase and address == 0x10369c06:
            self.trace.append(('native-iso-control-preparation', 0))
        elif self.phase and address in (0x103ea09e, 0x1030d3ca, 0x10367c8a):
            self.ret(0)
        elif self.phase and address == 0x10369192:
            self.trace.append(('native-selector', 0))
        elif self.phase and address == 0x1036b10c:
            self.trace.append(('native-computation-entry', 0))
        elif self.phase and address == (self.report['symbols']['z7_display_before_update'] & ~1):
            self.trace.append(('host-update-callback', 0))
        elif self.phase and address == 0x1036b116:
            self.trace.append(('native-widget-loop-continuation', 0)); u.emu_stop()
        else:
            super().hook(u, address, size, context)


def audit(raw, host, packet, module):
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Fingerprint mismatch')
    f = TransitionFixture(raw, host, packet)
    if f.call(host['symbols']['z7_module_load_once'], STATE) != 8: raise AssertionError('Module load')
    base = f.words()[12]; symbols = module['symbols']
    def write(p, v): f.u.mem_write(p, struct.pack('<I', v))
    def word(p): return int.from_bytes(f.u.mem_read(p, 4), 'little')
    descriptors = [word(TABLE + i * 4) for i in (10, 11, 15)]
    original = [[word(p + 4 + bank * 12) for bank in range(2)] for p in descriptors]
    for p in descriptors: f.u.mem_write(word(p + 44), b'\1')
    write(0xa181f91c, 0xa2c41000); f.u.mem_write(0xa2c41000, struct.pack('<4I', 4, 1, 0, 0xa2c42000))
    f.u.mem_write(SNAPSHOT, bytes(0x33c)); f.u.mem_write(0xa18237b8, bytes(7))
    # Supplied automatic-ISO state; original preparation/computation executes.
    for offset, value in ((0x50, 1), (0x250, 2), (0x2d8, 1)): write(SNAPSHOT + offset, value)
    f.u.mem_write(0xa18237c6, b'\0')
    write(base + symbols['z7_readout_preset'], 2)
    if f.call(base + symbols['z7_settings_flag'], base + symbols['z7_menu_settings'], 0, 1) != 1: raise AssertionError('Model setter')
    f.call(host['symbols']['z7_display_before_update'])
    cases = []
    for name, properties, errors, expected in (
            ('normal', {}, [], 0), ('card-appears', {0x1605: 1}, [], 26),
            ('card-clears', {}, [], 0), ('error-appears', {}, [2], 27),
            ('error-clears', {}, [], 0), ('secondary-error-appears', {}, [0x3e], 28),
            ('secondary-error-clears', {}, [], 0), ('full-appears', {0x1605: 1 << 4}, [], 18),
            ('full-clears', {}, [], 0), ('second-full-appears', {0x1605: 1 << 5}, [], 19),
            ('second-full-clears', {}, [], 0), ('combined-full-appears', {0x1605: 1 << 4, 0x1618: 2}, [], 20),
            ('combined-full-clears', {}, [], 0), ('error-priority-over-card', {0x1605: 1}, [2], 27),
            ('higher-error-priority-over-card', {0x1605: 1}, [0x3e], 28), ('all-clear', {}, [], 0)):
        old = bytes(f.u.mem_read(0xa18237b8, 7)); f.properties = properties; f.errors = errors; f.trace = []; f.phase = True
        f.u.reg_write(UC_ARM_REG_SP, STACK); f.u.reg_write(UC_ARM_REG_LR, STOP | 1)
        # Original caller BL sequence: selector, precompute, widget computation.
        f.u.emu_start(0x10437b17, 0, timeout=10000000, count=1000000)
        f.phase = False
        current = bytes(f.u.mem_read(0xa18237b8, 7))
        phases = [v[0] for v in f.trace if v[0] not in ('status-property', 'native-predicate', 'supplied-control-preparation-helper', 'native-iso-control-preparation')]
        if phases != ['native-selector', 'native-control-preparation-entry', 'host-update-callback', 'native-computation-entry', 'native-widget-loop-continuation']:
            raise AssertionError((name, phases))
        if current[0] != expected: raise AssertionError((name, expected, current.hex(), f.trace))
        if ('native-iso-control-preparation', 0) not in f.trace:
            raise AssertionError('Native ISO preparation did not run after callback')
        for i, p in enumerate(descriptors):
            special = current[(0, 1, 5)[i]] != 0
            actual = [word(p + 4 + bank * 12) for bank in range(2)]
            wanted = [value if special else value & ~0x909 for value in original[i]]
            if actual != wanted: raise AssertionError((name, i, actual, wanted))
        cases.append(dict(name=name, passed=True, previous_formats=old.hex(), native_formats=current.hex(),
            shutter_format=expected, native_predicates_executed=sorted({v[1] for v in f.trace if v[0] == 'native-predicate'}),
            same_iteration_policy_matches_current_native_formats=True,
            native_iso_preparation_runs_after_callback=('native-iso-control-preparation', 0) in f.trace))
    return dict(passed=True, cases=cases, main_sha256=host['main_payload_sha256'], module_sha256=module['module_sha256'],
        native_caller_order_executes=True, native_selector_executes=True,
        selected_native_predicates=sorted(f.native_predicates), warning_pixels=False, camera_access=False,
        supplied_boundaries=['Loader and GUI instance services', 'Incoming native status properties and error-list snapshot',
            'Unrelated native format predicates return false', 'Other six native control-preparation helper returns',
            'Incoming automatic-ISO snapshot fields and three native context service results'],
        limitation='Stops at native widget loop; does not prove complete warning control layout, pixels or status producer semantics')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True); p.add_argument('--module', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); a = p.parse_args(); output = a.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists(): p.error('Choose a new private output')
    result = audit((a.build / 'module-host.emulator.main.bin').read_bytes(), json.loads((a.build / 'module-host.emulator.json').read_text()),
        (a.module / 'Z7APP.BIN').read_bytes(), json.loads((a.module / 'module.json').read_text()))
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, cases=len(result['cases']))))


if __name__ == '__main__': main()
