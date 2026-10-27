"""Append a guarded UI-surface spiral draw entry to the verified grid lab mode.

No new stock edits or lifecycle hooks. Preserves every parent MAIN byte; private
diagnostic image only, rejected by ordinary grid/flash-review admission.
"""
import argparse
import binascii
import hashlib
import json
from pathlib import Path

from build_grid_firmware import ROOT, build_image as build_grid
from spiral_geometry import overlay_png
from z30_extensions.container import extract_eg
from z30_extensions.patch import Edit
from z30_extensions.plan import Plan
from z30_extensions.platform import z7_380
from z30_extensions.features.spiral_probe_z7 import configure


def build_image(container):
    parent, old = build_grid(container, native_choice=True, extra_grids=True)
    source = extract_eg(container)
    plan = Plan(source, z7_380)
    plan.tail.extend(parent[len(source)-2:-2])
    plan.edits = [Edit(int(e['offset'], 16), bytes.fromhex(e['expected_hex']),
                       bytes.fromhex(e['replacement_hex']), e['name']) for e in old['edits']]
    plan.features = old['features']
    configure(plan, overlay_png()[1])
    eg, report = plan.finish()
    if eg[:len(parent)-2] != parent[:-2]:
        raise ValueError('Spiral probe changed its independently built parent')
    report.update(preset='grid-spiral-draw-emulator-only', emulator_only=True,
        container_sha256=old['container_sha256'], input_kind='stock_container',
        source_model='z7', main_payload_size=len(eg)-2,
        main_payload_sha256=hashlib.sha256(eg[:-2]).hexdigest(),
        parent_main_payload_sha256=old['main_payload_sha256'], parent_main_bytes=len(parent)-2,
        parent_bytes_unchanged=True, candidate_cleared=False,
        build_scope='Explicit UI-surface draw diagnostic, without automatic refresh/erase hooks or installation clearance.')
    return eg, report


def validate_candidate(path, report_path, stock_path):
    if report_path is None or stock_path is None:
        raise ValueError('Spiral probe needs its report and original container')
    recorded = json.loads(Path(report_path).read_text())
    if recorded.get('preset') != 'grid-spiral-draw-emulator-only' or not recorded.get('emulator_only'):
        raise ValueError('Unsupported spiral probe identity')
    eg, report = build_image(Path(stock_path).read_bytes())
    if Path(path).read_bytes() != eg[:-2] or recorded != report or binascii.crc_hqx(eg, 0):
        raise ValueError('Spiral probe differs from complete independent rebuild')
    return dict(modified=True, independently_rebuilt=True, emulator_only=True,
                camera_verified=False, preset=report['preset'],
                sha256=report['main_payload_sha256'], size=len(eg)-2)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, default=ROOT/'.private/stock/Z_7_0380.bin')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    output = args.output.resolve()
    output.relative_to((ROOT/'.private').resolve())
    if output == (ROOT/'.private').resolve() or output.exists():
        p.error('Use a new private output subdirectory')
    eg, report = build_image(args.source.read_bytes())
    output.mkdir(parents=True)
    (output/'spiral.emulator.eg.bin').write_bytes(eg)
    (output/'spiral.emulator.main.bin').write_bytes(eg[:-2])
    (output/'spiral.emulator.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    validate_candidate(output/'spiral.emulator.main.bin', output/'spiral.emulator.json', args.source)
    print(json.dumps(dict(main_bytes=len(eg)-2, main_sha256=report['main_payload_sha256'],
                          independently_rebuilt=True, parent_bytes_unchanged=True, candidate_cleared=False)))


if __name__ == '__main__':
    main()
