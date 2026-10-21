"""Windows entry point for the explicitly selected Ubuntu Z7 research environment."""
import argparse
import json
import os
from pathlib import Path, PureWindowsPath
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def windows_to_wsl(path):
    path = PureWindowsPath(path)
    if len(path.drive) != 2 or path.drive[1] != ':':
        raise ValueError('Use a checkout on a Windows drive such as C: or D:')
    return '/mnt/' + path.drive[0].lower() + '/' + '/'.join(path.parts[1:])


def command(args, host_os=None, executable=None):
    host_os = os.name if host_os is None else host_os
    executable = executable or sys.executable
    build = args.build_directory.resolve()
    convert = (lambda path: windows_to_wsl(Path(path).resolve())) if host_os == 'nt' else (lambda path: str(Path(path).resolve()))
    payload = 'stock-main.bin' if args.preset == 'stock' else args.preset + '.main.bin'
    values = [convert(ROOT / 'z7-qemu/tools/interactive.py'), '--firmware', convert(build / payload),
              '--port', str(args.port)]
    if args.preset != 'stock':
        values += ['--candidate-report', convert(build / (args.preset + '.json')),
                   '--stock-container', convert(ROOT / '.private/stock/Z_7_0380.bin')]
    values += ['--profile', 'menu'] if args.menu_only else ['--photo-liveview']
    if host_os != 'nt':
        return [args.linux_python or executable, *values]
    if args.linux_python:
        return ['wsl.exe', '-d', args.wsl_distro, '--exec', args.linux_python, *values]
    # Keep the shell fragment static; all user paths travel as separate arguments.
    return ['wsl.exe', '-d', args.wsl_distro, '--exec', 'sh', '-c',
            'exec "$HOME/.local/share/wonderlantern-z7/venv/bin/python" "$@"',
            'wonderlantern-z7', *values]


if __name__ == '__main__':
    configuration = ROOT / '.private/lab-environment.json'
    local = json.loads(configuration.read_text(encoding='utf-8')) if configuration.exists() else {}
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preset', choices=('stock', 'full', 'liveview-dual', 'shutter-sound', 'm900'), default='full')
    parser.add_argument('--port', type=int, default=8787)
    parser.add_argument('--build-directory', type=Path, default=ROOT / '.private/builds/20261020-09')
    parser.add_argument('--menu-only', action='store_true')
    parser.add_argument('--wsl-distro', default=local.get('wsl_distro', 'Ubuntu'))
    parser.add_argument('--linux-python', default=local.get('linux_python'))
    args = parser.parse_args()
    print(f'Starting {args.preset} research firmware at http://127.0.0.1:{args.port}/', flush=True)
    options = dict(creationflags=subprocess.CREATE_NO_WINDOW) if os.name == 'nt' else {}
    raise SystemExit(subprocess.call(command(args), **options))
