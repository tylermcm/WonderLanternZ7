"""Build an independent Z7 splash firmware experiment for QEMU only.

Outputs checked MAIN and EG firmware images in a fresh private directory.
No Nikon update package, card staging or camera access is performed.
"""
import argparse
import binascii
import hashlib
import io
import json
from pathlib import Path
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'z7-firmware-extensions/src'))
from z30_extensions.container import extract_eg, Z7_CONTAINER_SHA256
from z30_extensions.features.splash_z7 import build
from probe_splash_display import splash_asset


def build_image(container):
    if hashlib.sha256(container).hexdigest() != Z7_CONTAINER_SHA256:
        raise ValueError('Requires original Z7 C 3.80 container')
    stock = extract_eg(container)
    image, splash = splash_asset()
    black = io.BytesIO()
    Image.new('RGB', image.size, (0, 0, 0)).save(black, format='PNG')
    eg, report = build(stock, splash, black.getvalue())
    report.update(container_sha256=Z7_CONTAINER_SHA256, source_model='z7',
                  input_kind='stock_container', main_payload_size=len(eg) - 2,
                  main_payload_sha256=hashlib.sha256(eg[:-2]).hexdigest(),
                  expected_splash_rgb_sha256=hashlib.sha256(image.tobytes()).hexdigest(),
                  build_scope='Emulator-only independent firmware; no update package or installation clearance.')
    return eg, report


def validate_candidate(path, report_path, stock_path):
    """Independent complete rebuild, used only by the experiment's QEMU runner."""
    if report_path is None or stock_path is None:
        raise ValueError('Experimental candidate requires its report and original container')
    report = json.loads(Path(report_path).read_text(encoding='utf-8'))
    if (report.get('model') != 'Nikon Z7' or report.get('firmware') != 'C 3.80'
            or report.get('preset') != 'splash-emulator-only' or not report.get('emulator_only')):
        raise ValueError('Unsupported splash experiment identity')
    eg, expected = build_image(Path(stock_path).read_bytes())
    data = Path(path).read_bytes()
    if data != eg[:-2] or binascii.crc_hqx(eg, 0) or report != expected:
        raise ValueError('Firmware/report differs from independent splash rebuild')
    return dict(modified=True, sha256=hashlib.sha256(data).hexdigest(), size=len(data),
                preset='splash-emulator-only', independently_rebuilt=True,
                emulator_only=True, camera_verified=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / '.private/stock/Z_7_0380.bin')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.relative_to((ROOT / '.private').resolve())
    if output.exists():
        parser.error('Preserve previous candidates: choose a new private directory')
    container = args.source.read_bytes()
    eg, report = build_image(container)
    repeated, _ = build_image(container)
    if repeated != eg or binascii.crc_hqx(eg, 0):
        raise RuntimeError('Build is not reproducible or EG CRC failed')
    output.mkdir(parents=True)
    (output / 'splash.emulator.eg.bin').write_bytes(eg)
    (output / 'splash.emulator.main.bin').write_bytes(eg[:-2])
    (output / 'splash.emulator.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    validate_candidate(output / 'splash.emulator.main.bin', output / 'splash.emulator.json', args.source)
    print(json.dumps(dict(main_bytes=len(eg) - 2, appended_bytes=report['append_length'],
                          main_sha256=report['main_payload_sha256'], reproducible=True,
                          eg_crc_zero=True, emulator_only=True, candidate_cleared=False)))
