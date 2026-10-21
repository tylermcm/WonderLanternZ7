"""Build local Z7 research images and run upstream tests against private stock input."""
import argparse
import binascii
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATCHER = ROOT / 'z7-firmware-extensions'
sys.path.insert(0, str(PATCHER / 'src'))
from z30_extensions.build import build, PRESETS
from z30_extensions.container import extract_eg


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / '.private/stock/Z_7_0380.bin')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    container = args.source.read_bytes()
    stock = extract_eg(container)
    args.output.mkdir(parents=True, exist_ok=False)
    stock_path = args.output / 'stock-main.bin'
    stock_path.write_bytes(stock[:-2])
    summary = {'stock_container_sha256': digest(container),
               'stock_main_sha256': digest(stock[:-2]), 'candidates': {},
               'physical_camera_tested': False}
    summary['patcher_source_sha256'] = {
        str(path.relative_to(PATCHER)).replace('\\', '/'): digest(path.read_bytes())
        for path in sorted((PATCHER / 'src').rglob('*.py'))}
    # Bind the upstream integration tests to private input without copying it into source.
    suite = unittest.defaultTestLoader.discover(str(PATCHER / 'tests'))
    integration = sys.modules['test_z7_integration']
    integration.FIRMWARE = args.source.resolve()
    integration.Z7IntegrationTests.__unittest_skip__ = False
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    summary['upstream_tests'] = {'run': result.testsRun, 'failures': len(result.failures),
                                 'errors': len(result.errors), 'skipped': len(result.skipped)}
    if not result.wasSuccessful():
        raise RuntimeError('Upstream firmware tests failed')
    spec = importlib.util.spec_from_file_location('z7_gate_verifier', PATCHER / 'tools/verify_liveview_gates.py')
    gates = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gates)
    for preset in PRESETS:
        output, report = build(stock, preset, model='z7')
        rebuilt, _ = build(stock, preset, model='z7')
        if rebuilt != output or binascii.crc_hqx(output, 0):
            raise RuntimeError('Non-reproducible output or bad CRC')
        module = args.output / f'{preset}.eg.bin'
        payload = args.output / f'{preset}.main.bin'
        report.update(source_model='z7', input_kind='stock_container',
                      container_sha256=digest(container),
                      main_payload_size=len(output) - 2,
                      main_payload_sha256=digest(output[:-2]))
        module.write_bytes(output)
        payload.write_bytes(output[:-2])
        (args.output / f'{preset}.json').write_text(json.dumps(report, indent=2) + '\n')
        entry = {'module': str(module.resolve()), 'payload': str(payload.resolve()),
                 'main_bytes': len(output) - 2, 'sha256': digest(output[:-2]),
                 'appended_bytes': report['append_length'], 'reproducible': True}
        if preset in ('full', 'liveview-dual'):
            entry['gate_verification'] = gates.verify(stock, preset, model='z7')
        if preset in ('full', 'shutter-sound'):
            from verify_sound_hook import verify as verify_sound_hook
            entry['sound_hook_verification'] = verify_sound_hook(output[:-2])
            if not entry['sound_hook_verification']['passed']:
                raise RuntimeError('Z7 sound config hook violates the native calling convention')
            from verify_sound_route import verify as verify_sound_route
            entry['sound_route_verification'] = verify_sound_route(stock[:-2], output[:-2])
            if not entry['sound_route_verification']['passed']:
                raise RuntimeError('Z7 sound route fallback differs from the stock instructions')
            from verify_sound_data import verify as verify_sound_data
            complete = int(report['features']['shutter_sound']['functions']['complete'], 16)
            entry['sound_data_verification'] = verify_sound_data(stock[:-2], output[:-2], complete)
            if not entry['sound_data_verification']['passed']:
                raise RuntimeError('Z7 sound data fallback differs from the stock instructions')
            from verify_sound_menu_layout import verify as verify_sound_menu_layout
            entry['sound_menu_verification'] = verify_sound_menu_layout(stock[:-2], output[:-2], report)
            if not entry['sound_menu_verification']['passed']:
                raise RuntimeError('Z7 sound menu violates native page/layout/callback contracts')
        summary['candidates'][preset] = entry
        print(f'{preset}: {len(output)-2} MAIN bytes, {report["append_length"]} appended', flush=True)
    # Vendored source directories resolve Git commands to the workspace repo on
    # a fresh laptop clone. Record their pinned provenance explicitly instead.
    upstreams = json.loads((ROOT / 'UPSTREAMS.json').read_text(encoding='utf-8'))
    for name, provenance in upstreams['components'].items():
        summary[name + '_commit'] = provenance['commit']
    try:
        summary['workspace_commit'] = subprocess.check_output(
            ['git', '-c', 'safe.directory=' + str(ROOT), '-C', str(ROOT),
             'rev-parse', 'HEAD'], text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        summary['workspace_commit'] = None
    (args.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
