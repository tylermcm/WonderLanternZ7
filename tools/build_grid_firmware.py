"""Build and independently validate a standalone grid experiment for QEMU only."""
import argparse
import binascii
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'z7-firmware-extensions/src'))
from z30_extensions.container import extract_eg, Z7_CONTAINER_SHA256
from z30_extensions.features.grid_z7 import build


def build_image(container, persistent=False, native_choice=False, extra_grids=False):
    if hashlib.sha256(container).hexdigest() != Z7_CONTAINER_SHA256:
        raise ValueError('Requires original Z7 C 3.80 container')
    eg, report = build(extract_eg(container), persistent=persistent, native_choice=native_choice,
                       extra_grids=extra_grids)
    report.update(container_sha256=Z7_CONTAINER_SHA256, source_model='z7',
                  input_kind='stock_container', main_payload_size=len(eg) - 2,
                  main_payload_sha256=hashlib.sha256(eg[:-2]).hexdigest(),
                  build_scope='Standalone emulator-only grid experiment; no update package or installation clearance.')
    return eg, report


def validate_candidate(path, report_path, stock_path):
    if report_path is None or stock_path is None:
        raise ValueError('Grid candidate needs its report and original container')
    report = json.loads(Path(report_path).read_text(encoding='utf-8'))
    if (report.get('model') != 'Nikon Z7' or report.get('firmware') != 'C 3.80'
            or report.get('preset') not in ('grid-emulator-only', 'grid-persistent-emulator-only',
                                          'grid-native-value-emulator-only', 'grid-layouts-emulator-only')
            or not report.get('emulator_only')):
        raise ValueError('Unsupported grid experiment identity')
    persistent = report['preset'] == 'grid-persistent-emulator-only'
    eg, expected = build_image(Path(stock_path).read_bytes(), persistent=persistent,
                              native_choice=report['preset'] in ('grid-native-value-emulator-only', 'grid-layouts-emulator-only'),
                              extra_grids=report['preset'] == 'grid-layouts-emulator-only')
    data = Path(path).read_bytes()
    if data != eg[:-2] or binascii.crc_hqx(eg, 0) or report != expected:
        raise ValueError('Firmware/report differs from independent grid rebuild')
    return dict(modified=True, sha256=hashlib.sha256(data).hexdigest(), size=len(data),
                preset=report['preset'], independently_rebuilt=True,
                emulator_only=True, camera_verified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / '.private/stock/Z_7_0380.bin')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--persistent', action='store_true', help='Experimental native journal integration, emulator only')
    parser.add_argument('--native-choice', action='store_true', help='Existing-scalar third-value experiment, emulator only')
    parser.add_argument('--extra-grids', action='store_true', help='Additional native-scalar layouts; requires --native-choice')
    args = parser.parse_args()
    output = args.output.resolve()
    output.relative_to((ROOT / '.private').resolve())
    if output.exists():
        parser.error('Preserve prior candidates: choose a new private directory')
    container = args.source.read_bytes()
    eg, report = build_image(container, persistent=args.persistent, native_choice=args.native_choice, extra_grids=args.extra_grids)
    repeated, repeated_report = build_image(container, persistent=args.persistent, native_choice=args.native_choice, extra_grids=args.extra_grids)
    if repeated != eg or repeated_report != report or binascii.crc_hqx(eg, 0):
        raise RuntimeError('Build/report not reproducible or EG CRC failed')
    output.mkdir(parents=True)
    main_path = output / 'grid.emulator.main.bin'
    report_path = output / 'grid.emulator.json'
    (output / 'grid.emulator.eg.bin').write_bytes(eg)
    main_path.write_bytes(eg[:-2])
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    validate_candidate(main_path, report_path, args.source)
    print(json.dumps(dict(main_bytes=len(eg) - 2, appended_bytes=report['append_length'],
                          main_sha256=report['main_payload_sha256'], reproducible=True,
                          eg_crc_zero=True, emulator_only=True, candidate_cleared=False)))


if __name__ == '__main__':
    main()
