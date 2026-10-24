"""Launch the local Z7 lab using native Windows, Linux or an explicit WSL distro."""
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
    wsl = host_os == 'nt' and not getattr(args, 'native', False)
    convert = (lambda path: windows_to_wsl(Path(path).resolve())) if wsl else (lambda path: str(Path(path).resolve()))
    payload = 'stock-main.bin' if args.preset == 'stock' else args.preset + '.main.bin'
    values = [convert(ROOT / 'z7-qemu/tools/interactive.py'), '--firmware', convert(build / payload),
              '--port', str(args.port)]
    if args.preset != 'stock':
        values += ['--candidate-report', convert(build / (args.preset + '.json')),
                   '--stock-container', convert(ROOT / '.private/stock/Z_7_0380.bin')]
    values += ['--profile', 'menu'] if args.menu_only else ['--photo-liveview']
    if host_os == 'nt' and not wsl:
        return [executable, *values]
    if not wsl:
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
    parser.add_argument('--build-directory', type=Path,
                        default=ROOT / local.get('build_directory', '.private/builds/20261020-09'))
    parser.add_argument('--menu-only', action='store_true')
    parser.add_argument('--wsl-distro', default=local.get('wsl_distro', 'Ubuntu'))
    parser.add_argument('--linux-python', default=local.get('linux_python'))
    runtime = parser.add_mutually_exclusive_group()
    runtime.add_argument('--native', dest='native', action='store_true',
                         help='Use the current Windows Python and native QEMU build')
    runtime.add_argument('--wsl', dest='native', action='store_false', help='Use the selected WSL distribution')
    parser.set_defaults(native=local.get('runtime') == 'windows-native')
    args = parser.parse_args()
    print(f'Starting {args.preset} research firmware at http://127.0.0.1:{args.port}/', flush=True)
    options = dict(creationflags=subprocess.CREATE_NO_WINDOW) if os.name == 'nt' else {}
    raise SystemExit(subprocess.call(command(args), **options))
