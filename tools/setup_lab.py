"""Create a laptop-local Linux environment, build QEMU and generate test input.

Run inside Linux/WSL with Python 3.12+. Nikon firmware is supplied separately.
This script does not install OS packages, create a WSL distro or access a camera.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--environment-dir', type=Path,
                        default=Path.home() / '.local/share/wonderlantern-z7')
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--skip-qemu', action='store_true', help='Keep an existing checked QEMU build')
    args = parser.parse_args()
    if os.name == 'nt' or sys.version_info < (3, 12):
        parser.error('Run inside Linux/WSL with Python 3.12 or newer')
    if not 1 <= args.jobs <= 64:
        parser.error('--jobs must be 1..64')
    environment = args.environment_dir.expanduser().resolve()
    python = environment / 'venv/bin/python'
    if not python.exists():
        venv.EnvBuilder(with_pip=True).create(environment / 'venv')
    subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(ROOT / 'requirements-lab.txt')], check=True)
    # Candidate admission rebuilds the vendored patcher, including from direct
    # interactive/probe commands. A clean venv must be able to import that source.
    packages = Path(subprocess.check_output([str(python), '-c',
        'import sysconfig; print(sysconfig.get_path("purelib"))'], text=True).strip())
    (packages / 'wonderlantern-source.pth').write_text(
        str(ROOT / 'z7-firmware-extensions/src') + '\n', encoding='utf-8')
    if not args.skip_qemu:
        subprocess.run([str(python), str(ROOT / 'z7-qemu/tools/build.py'),
                        '--work-dir', str(environment / 'qemu'), '--jobs', str(args.jobs)], check=True)
    subprocess.run([str(python), str(ROOT / 'z7-qemu/tools/make_cmos.py')], check=True)
    configuration = ROOT / '.private/lab-environment.json'
    configuration.parent.mkdir(parents=True, exist_ok=True)
    configuration.write_text(json.dumps(dict(
        linux_python=str(python), wsl_distro=os.environ.get('WSL_DISTRO_NAME', 'Ubuntu'),
        qemu_work_dir=str(environment / 'qemu')), indent=2) + '\n', encoding='utf-8')
    print('Local environment: ' + str(configuration))
    print('Next: supply .private/stock/Z_7_0380.bin and rebuild the private candidates.')


if __name__ == '__main__':
    main()
