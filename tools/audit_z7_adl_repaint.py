"""Compare original ADL updater requests for two immutable captured states.

SPDX-License-Identifier: MIT. This isolates request selection, not completed
painting. Incoming snapshots/controls, owned object storage, dirty predicate and
drawing sinks are supplied. Original updater, dual-image selection, output-style
query and object-reset instructions execute. Failed live evidence is permitted
and explicitly remains failed; this audit cannot clear its pixel mismatch.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from PIL import Image, ImageChops
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3
from audit_splash_image import NativePNG, MEM, STOCK_SHA
from audit_z7_other_identity import OtherIdentityFixture
from audit_z7_status_identity import SNAPSHOT
from build_z7_module_host import ROOT


class ADLFixture(OtherIdentityFixture):
    def hook(self, u, address, size, context):
        if address in (0x102f309a, 0x102f3006, 0x102f2b8c):
            return NativePNG.hook(self, u, address, size, context)
        if address in (0x102f2f80, 0x102f2090):
            self.events.append(dict(function=hex(address), arguments=[u.reg_read(r) for r in
                (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)]))
            self.ret(0)
        else:
            super().hook(u, address, size, context)


def audit(raw, evidence, reference, restored):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA:
        raise ValueError('Exact original-Z7 stock MAIN required')
    live = json.loads((evidence / 'result.json').read_text())
    steps = {s['name']: s for s in live['steps']}
    selected = [steps[n] for n in (reference, restored)]
    checks, cases, pictures = [], [], []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good:
            raise AssertionError(name)
    for step in selected:
        data = (evidence / (step['name'] + '.png')).read_bytes()
        check(step['name'] + '-immutable-png', hashlib.sha256(data).hexdigest() == step['frame_sha256'])
        pictures.append(Image.open(evidence / (step['name'] + '.png')).convert('RGB'))
        f = ADLFixture(raw)
        _, controls = f.prepare(6)
        descriptor = int.from_bytes(f.u.mem_read(0x1064d610 + 6 * 4, 4), 'little')
        check(step['name'] + '-native-adl-updater-binding',
            int.from_bytes(f.u.mem_read(0x1064c67c + 6 * 4, 4), 'little') == 0x102f354f)
        incoming = bytes.fromhex(step['information_native_snapshot'])
        f.u.mem_write(SNAPSHOT, incoming)
        f.u.mem_write(descriptor + 4, bytes.fromhex(step['information_masks'][6]))
        for i, text in enumerate(step['information_controls']['6']):
            row = bytearray.fromhex(text)
            struct.pack_into('<I', row, 36, MEM + 0x20000 + i * 256)
            f.u.mem_write(controls + i * 48, bytes(row))
        f.events = []
        f.call(0x102f354e)
        check(step['name'] + '-preserves-current-snapshot', bytes(f.u.mem_read(SNAPSHOT, len(incoming))) == incoming)
        check(step['name'] + '-selects-both-original-adl-images',
            [e['arguments'][:3] for e in f.events] == [[6, 1, 2968], [6, 0, 2969]])
        resets = [list(struct.unpack('<4I', f.u.mem_read(MEM + 0x20000 + i * 256 + 0x34, 16))) for i in range(2)]
        check(step['name'] + '-native-object-reset-values', all(r[0] == r[2] == 0x1000 and r[3] == 0x2eb for r in resets))
        cases.append(dict(frame=step['name'], native_draw_requests=f.events, native_object_resets=resets))
    check('incoming-current-snapshots-identical', selected[0]['information_native_snapshot'] == selected[1]['information_native_snapshot'])
    check('incoming-adl-control-records-identical', selected[0]['information_controls']['6'] == selected[1]['information_controls']['6'])
    check('incoming-all-descriptor-masks-identical', selected[0]['information_masks'] == selected[1]['information_masks'])
    check('original-native-draw-requests-identical', cases[0]['native_draw_requests'] == cases[1]['native_draw_requests'])
    check('original-native-reset-values-identical', cases[0]['native_object_resets'] == cases[1]['native_object_resets'])
    difference = ImageChops.difference(*pictures)
    return dict(passed=True, checks=checks, cases=cases, input_live_run_passed=live.get('passed') is True,
        input_live_error=live.get('error'), full_rgb_equal=difference.getbbox() is None,
        full_rgb_difference_bounds=difference.getbbox(), differing_rgb_pixels=sum(p != (0, 0, 0) for p in
            getattr(difference, 'get_flattened_data', difference.getdata)()),
        pixel_mismatch_cleared=False, native_updater_selection_equivalent=True,
        supplied_boundaries=['Captured incoming snapshots and controls', 'Owned substitute object storage',
            'Dirty predicate returns1', 'Native drawing sinks'],
        completed_paint_proven=False, camera_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main', type=Path, required=True)
    p.add_argument('--evidence', type=Path, required=True)
    p.add_argument('--reference', required=True)
    p.add_argument('--restored', required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    evidence, output = args.evidence.resolve(), args.output.resolve()
    if not evidence.is_relative_to(ROOT / '.private') or not output.is_relative_to(ROOT / '.private') or output.exists():
        p.error('Existing private evidence and a new private output required')
    result = audit(args.stock_main.read_bytes(), evidence, args.reference, args.restored)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']), input_live_run_passed=result['input_live_run_passed'],
        full_rgb_equal=result['full_rgb_equal'], differing_rgb_pixels=result['differing_rgb_pixels'], pixel_mismatch_cleared=False)))


if __name__ == '__main__':
    main()
