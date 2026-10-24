"""Portable launcher checks; no WSL process, emulator or camera is started."""
import argparse
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import launch_z7


class LauncherTests(unittest.TestCase):
    def args(self, **updates):
        values = dict(preset='full', build_directory=Path('/tmp/project with spaces/build'),
                      port=8787, menu_only=False, linux_python=None, wsl_distro='Ubuntu')
        values.update(updates)
        return argparse.Namespace(**values)

    def test_windows_drive_conversion(self):
        self.assertEqual(launch_z7.windows_to_wsl(r'D:\Lab with spaces\firmware.bin'),
                         '/mnt/d/Lab with spaces/firmware.bin')
        with self.assertRaises(ValueError):
            launch_z7.windows_to_wsl(r'\\server\share\project')

    def test_linux_preserves_paths_and_candidate_validation(self):
        result = launch_z7.command(self.args(), host_os='posix', executable='/venv/bin/python')
        self.assertEqual(result[0], '/venv/bin/python')
        self.assertIn(str((self.args().build_directory / 'full.main.bin').resolve()), result)
        self.assertIn('--candidate-report', result)
        self.assertIn('--stock-container', result)

    def test_stock_menu_profile(self):
        result = launch_z7.command(self.args(preset='stock', menu_only=True), host_os='posix')
        self.assertNotIn('--candidate-report', result)
        self.assertEqual(result[-2:], ['--profile', 'menu'])

    def test_native_windows_preserves_paths_and_validation(self):
        with patch.object(launch_z7, 'windows_to_wsl', side_effect=AssertionError('Native launch used WSL')):
            result = launch_z7.command(self.args(native=True), host_os='nt', executable='C:/lab/python.exe')
        self.assertEqual(result[0], 'C:/lab/python.exe')
        self.assertIn('--candidate-report', result)
        self.assertIn('--stock-container', result)
        self.assertEqual(result[-1], '--photo-liveview')

    def test_wsl_interpreter_and_argument_boundaries(self):
        with patch.object(launch_z7, 'windows_to_wsl', side_effect=lambda path: '/mnt/c/Lab with spaces/' + path.name):
            direct = launch_z7.command(self.args(linux_python='/home/user/lab/bin/python'), host_os='nt')
            self.assertEqual(direct[:5], ['wsl.exe', '-d', 'Ubuntu', '--exec', '/home/user/lab/bin/python'])
            fallback = launch_z7.command(self.args(), host_os='nt')
            self.assertIn('exec "$HOME/.local/share/wonderlantern-z7/venv/bin/python" "$@"', fallback)
            self.assertIn('/mnt/c/Lab with spaces/full.main.bin', fallback)


if __name__ == '__main__':
    unittest.main()
