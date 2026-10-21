"""Check candidate admission against real private inputs, including corruptions."""
import argparse
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'z7-qemu/tools'))
from firmware_input import validate_firmware


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    args = parser.parse_args()
    source = ROOT / '.private/stock/Z_7_0380.bin'
    checks = []

    def accepted(name, *values):
        identity = validate_firmware(*values)
        checks.append({'name': name, 'passed': True, 'identity': identity})

    def rejected(name, *values):
        try:
            validate_firmware(*values)
        except ValueError as error:
            checks.append({'name': name, 'passed': True, 'rejection': str(error)})
        else:
            raise AssertionError(f'{name}: invalid candidate accepted')

    accepted('stock', args.build / 'stock-main.bin')
    for preset in ('full', 'liveview-dual', 'shutter-sound', 'm900'):
        accepted(preset, args.build / f'{preset}.main.bin', args.build / f'{preset}.json', source)
    candidate = args.build / 'full.main.bin'
    report = args.build / 'full.json'
    rejected('candidate_needs_explicit_mode', candidate)
    rejected('candidate_needs_stock', candidate, report)
    with tempfile.TemporaryDirectory(dir=ROOT / '.private') as temporary:
        temp = Path(temporary)
        data = candidate.read_bytes()
        (temp / 'truncated.bin').write_bytes(data[:33052088])
        rejected('stock_length_truncation', temp / 'truncated.bin', report, source)
        altered = bytearray(data)
        altered[0x100] ^= 1
        (temp / 'altered.bin').write_bytes(altered)
        rejected('tampered_instruction', temp / 'altered.bin', report, source)
        altered = bytearray(data)
        altered[-1] ^= 1
        (temp / 'altered-tail.bin').write_bytes(altered)
        rejected('tampered_tail', temp / 'altered-tail.bin', report, source)
        wrong = json.loads(report.read_text())
        wrong['main_payload_sha256'] = '0' * 64
        (temp / 'wrong-hash.json').write_text(json.dumps(wrong))
        rejected('wrong_report_hash', candidate, temp / 'wrong-hash.json', source)
        wrong['model'] = 'Nikon Z7 II'
        (temp / 'wrong-model.json').write_text(json.dumps(wrong))
        rejected('wrong_model', candidate, temp / 'wrong-model.json', source)
        rejected('wrong_stock_container', candidate, report, args.build / 'stock-main.bin')
    destination = args.build / 'candidate-input-checks.json'
    destination.write_text(json.dumps({'checks': checks, 'passed': True}, indent=2) + '\n')
    print(f'{len(checks)} candidate-input checks passed: {destination}')


if __name__ == '__main__':
    main()
