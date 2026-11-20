"""Native ISO preparation/phase selection versus the compiled Shooting switch.

SPDX-License-Identifier: MIT. Compiled mask policy and original ISO preparation,
layout and phase/visibility helpers execute. Loader, incoming snapshots and
three unrelated native context services are supplied. No pixels or paint fence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from audit_z7_display_base import BaseFixture
from build_z7_module_host import ROOT, STATE


class PhaseFixture(BaseFixture):
    def hook(self, u, address, size, context):
        if address in (0x1030d3ca, 0x10367c8a, 0x103ea09e): self.ret(0)
        else: super().hook(u, address, size, context)


def audit(raw, host, packet, module):
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Fingerprint mismatch')
    f = PhaseFixture(raw, host, packet)
    if f.call(host['symbols']['z7_module_load_once'], STATE) != 8: raise AssertionError('Load')
    base, symbols = f.words()[12], module['symbols']; model = base + symbols['z7_menu_settings']
    snapshot, previous = 0xa201d4d0, 0xa201d80c
    descriptor = int.from_bytes(f.u.mem_read(0x1064d610 + 15 * 4, 4), 'little')
    controls = int.from_bytes(f.u.mem_read(descriptor + 44, 4), 'little')
    shooting_descriptor = int.from_bytes(f.u.mem_read(0x1064d610 + 5 * 4, 4), 'little')
    shooting_baseline = [int.from_bytes(f.u.mem_read(shooting_descriptor + 4 + bank * 12, 4), 'little') for bank in (0, 1)]
    checks, cases = [], []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    for selected in (0, 1):
        f.call(base + symbols['z7_settings_information'], model, 0, 3, selected)
        f.call(base + symbols['z7_settings_component'], model, 0, 2, 1)
        f.call(base + symbols['z7_settings_flag'], model, 0, 1)
        for phase in (0, 1):
            incoming = bytearray(0x33c); incoming[0x18a] = 3
            for offset, value in ((4, phase), (0x3c, phase), (0x24c, phase), (0x50, 1), (0x250, 2), (0x2d8, 1)):
                struct.pack_into('<I', incoming, offset, value)
            f.u.mem_write(snapshot, bytes(incoming)); f.properties[0x2f15] = 3
            f.u.mem_write(previous, bytes(0x33c)); f.u.mem_write(0xa18237b8, bytes(7)); f.u.mem_write(0xa18237bf, b'\xff' * 7)
            f.call(host['symbols']['z7_display_before_update'])
            expected = [(v & ~0x909) | (((9 if v & 1 else 0) | (0x900 if v & 0x100 else 0)) if selected else 0) for v in shooting_baseline]
            check(f'shooting{selected}-phase{phase}-compiled-shooting-mask-actually-follows-selection',
                [int.from_bytes(f.u.mem_read(shooting_descriptor + 4 + bank * 12, 4), 'little') for bank in (0, 1)] == expected)
            check(f'shooting{selected}-phase{phase}-compiled-policy-preserves-native-current-snapshot', bytes(f.u.mem_read(snapshot, 0x33c)) == incoming)
            f.call(0x10369c06)
            check(f'shooting{selected}-phase{phase}-original-selector-reads-native-phase', f.call(0x102f2586, 15) == phase)
            for control in (1, 2): f.call(0x102f2656, 15, control)
            records = [bytes(f.u.mem_read(controls + i * 48, 3)) for i in range(4)]
            check(f'shooting{selected}-phase{phase}-native-auto-visibility-follows-phase', all(records[i][1] == phase and records[i][2] == 1 for i in (1, 2)))
            check(f'shooting{selected}-phase{phase}-native-preparation-preserves-current-snapshot', bytes(f.u.mem_read(snapshot, 0x33c)) == incoming)
            cases.append(dict(shooting_selected=selected, native_phase=phase, iso_controls=[v.hex() for v in records], passed=True))
    for phase in (0, 1):
        same_phase = [v['iso_controls'] for v in cases if v['native_phase'] == phase]
        check(f'phase{phase}-same-native-iso-controls-with-shooting-on-or-off', same_phase[0] == same_phase[1])
    return dict(passed=True, checks=checks, cases=cases, main_sha256=host['main_payload_sha256'], module_sha256=module['module_sha256'],
        original_iso_preparation='0x10369C06', original_phase_selector='0x102F2586', original_visibility_helper='0x102F2656',
        native_phase_sources=['snapshot+4', 'snapshot+0x3C', 'snapshot+0x24C'],
        scope='At fixed supplied native phase, Shooting selection does not alter ISO control preparation or visibility in this executed native path',
        supplied_boundaries=['Loader', 'Incoming snapshot and GUI/property state', 'Native context services1030D3CA/10367C8A/103EA09E return0'],
        actual_pixels=False, temporal_phase_producer_proven=False, camera_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True); p.add_argument('--module', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(); output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists(): p.error('Choose a new private output')
    result = audit((args.build / 'module-host.emulator.main.bin').read_bytes(), json.loads((args.build / 'module-host.emulator.json').read_text()),
        (args.module / 'Z7APP.BIN').read_bytes(), json.loads((args.module / 'module.json').read_text()))
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']), cases=len(result['cases']))))


if __name__ == '__main__': main()
