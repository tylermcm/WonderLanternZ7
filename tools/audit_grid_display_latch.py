"""Exercise the traced display-config write contract in QEMU without firmware.

Synthetic ARM instructions issue one MMIO transaction, followed by a deliberately
unmodeled marker. Acceptance means execution reaches the marker; it does not
establish the physical function of the retained configuration bit.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM

ROOT = Path(__file__).resolve().parents[1]
MARKER = 0x12340000


def audit(manifest_path, private_output):
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    binary = Path(manifest['binary'])
    if hashlib.sha256(binary.read_bytes()).hexdigest() != manifest['binary_sha256']:
        raise ValueError('QEMU binary differs from build manifest')
    source = ROOT / 'z7-qemu/qemu/nikon-z7-lab.c'
    if hashlib.sha256(source.read_bytes()).hexdigest() != manifest['sources']['qemu/nikon-z7-lab.c']:
        raise ValueError('QEMU display model needs rebuilding')
    private_output.resolve().relative_to((ROOT / '.private').resolve())
    private_output.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ)
    if manifest.get('native_runtime_path'):
        env['PATH'] = manifest['native_runtime_path'] + os.pathsep + env['PATH']
    # Peripheral diagnostics must not inherit another experiment's test inputs.
    env = {key: value for key, value in env.items() if not key.startswith('Z7_')}
    cases = []
    for base in (0x20140000, 0x20144000, 0x20148000):
        cases += [(base + 0x1620, 'str', value, True) for value in (0, 1)]
        cases += [(base + 0x1620, 'str', 2, False),
                  (base + 0x1620, 'ldr', 0, False)]
    cases += [(0x20145624, 'str', 1, False), (0x20145620, 'strb', 1, False)]
    checks = []
    assembler = Ks(KS_ARCH_ARM, KS_MODE_ARM)
    for index, (address, operation, value, accepted) in enumerate(cases):
        code = (f'movw r0, #{address & 65535}; movt r0, #{address >> 16}; '
                f'mov r1, #{value}; {operation} r1,[r0]; '
                f'movw r0, #{MARKER & 65535}; movt r0, #{MARKER >> 16}; '
                'str r1,[r0]; b .;')
        payload = private_output / f'case-{index}.bin'
        payload.write_bytes(bytes(assembler.asm(code, 0x10020000)[0]))
        options = dict(creationflags=subprocess.CREATE_NO_WINDOW) if os.name == 'nt' else {}
        result = subprocess.run([
            str(binary), '-M', 'nikon-z7-display', '-smp', '1', '-display', 'none',
            '-monitor', 'none', '-serial', 'none', '-nic', 'none',
            '-chardev', 'null,id=z7uart',
            '-device', f'loader,file={payload.resolve()},addr=0x10020000,force-raw=on',
            '-device', 'loader,addr=0x10020000,cpu-num=0',
        ], capture_output=True, timeout=15, env=env, **options)
        log = result.stderr.decode(errors='replace')
        (private_output / f'case-{index}.log').write_text(log, encoding='utf-8')
        expected = MARKER if accepted else address
        passed = result.returncode == 2 and f'Z7_LAB_UNMODELED write addr=0x{expected:08x}' in log
        if operation == 'ldr':
            passed = result.returncode == 2 and f'Z7_LAB_UNMODELED read addr=0x{address:08x}' in log
        checks.append(dict(address=hex(address), operation=operation, value=value,
                           accepted=accepted, passed=passed))
    return dict(schema=1, scope='Firmware-free synthetic ARM MMIO transactions in the real QEMU binary. No pixels, IRQ/completion or physical hardware validation.',
                binary_sha256=manifest['binary_sha256'], checks=checks,
                all_passed=all(check['passed'] for check in checks), camera_access=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private-output', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(ROOT / 'z7-qemu/.local/build-manifest.json', args.private_output)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(checks=len(result['checks']), all_passed=result['all_passed'])))
    if not result['all_passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
