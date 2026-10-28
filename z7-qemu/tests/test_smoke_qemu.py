# SPDX-License-Identifier: GPL-2.0-or-later
"""Exercise the real smoke transport against a synthetic local QMP process."""
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import smoke_qemu


def peer(mode, arguments):
    endpoint = arguments[arguments.index('-qmp') + 1].split(',')[0]
    _, host, port = endpoint.split(':')
    with socket.socket() as listener:
        listener.bind((host, int(port)))
        listener.listen(1)
        while True:
            connection, _ = listener.accept()
            started = False
            try:
                with connection, connection.makefile('rwb', buffering=0) as stream:
                    stream.write(b'{"QMP": {}}\n')
                    for name in ('qmp_capabilities', 'query-status', 'quit'):
                        line = stream.readline()
                        if not line and not started:
                            break
                        request = json.loads(line)
                        if request != {'execute': name}:
                            raise AssertionError('Unexpected command order')
                        started = True
                        stage = {'qmp_capabilities': 'caps', 'query-status': 'status', 'quit': 'quit'}[name]
                        if mode == stage + '-reset':
                            layout = 'HH' if os.name == 'nt' else 'ii'
                            connection.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack(layout, 1, 0))
                            return 0
                        if mode == stage + '-eof':
                            return 0
                        if mode == stage + '-error':
                            stream.write(b'{"error": {"class": "GenericError", "desc": "synthetic rejection"}}\n')
                            return 0
                        if name == 'quit':
                            if mode == 'quit-hang':
                                time.sleep(30)
                            if mode == 'quit-nonzero':
                                return 7
                        # Events cannot substitute for a command reply.
                        stream.write(b'{"event": "SYNTHETIC"}\n')
                        value = {'status': 'prelaunch', 'running': mode == 'status-running'} if name == 'query-status' else {}
                        stream.write(json.dumps({'return': value}).encode() + b'\n')
                    else:
                        return 0
            except OSError:
                if started:
                    raise
            # Like a QMP server, accept another client if an initial connect
            # attempt timed out/closed before sending any command. Never retry
            # the actual protocol scenario once capabilities has been sent.
    return 0


class SmokeTests(unittest.TestCase):
    def run_peer(self, mode):
        spawn = subprocess.Popen
        def start(command, **options):
            return spawn([sys.executable, '-B', str(Path(__file__).resolve()),
                          '--qmp-peer', mode, *command[1:]], **options)
        with patch.object(smoke_qemu.subprocess, 'Popen', side_effect=start):
            return smoke_qemu.smoke(Path('synthetic-qemu'),
                                    quit_timeout=.3 if mode == 'quit-hang' else 10)

    def test_quit_reply(self):
        self.assertTrue(self.run_peer('quit-reply')['passed'])

    def test_quit_eof_without_reply(self):
        self.assertTrue(self.run_peer('quit-eof')['passed'])

    def test_quit_reset_without_reply(self):
        self.assertTrue(self.run_peer('quit-reset')['passed'])

    def test_capabilities_eof_is_failure(self):
        with self.assertRaisesRegex(RuntimeError, 'qmp_capabilities'):
            self.run_peer('caps-eof')

    def test_capabilities_reset_is_failure(self):
        with self.assertRaises(RuntimeError):
            self.run_peer('caps-reset')

    def test_status_eof_is_failure(self):
        with self.assertRaisesRegex(RuntimeError, 'query-status'):
            self.run_peer('status-eof')

    def test_status_reset_is_failure(self):
        with self.assertRaises(RuntimeError):
            self.run_peer('status-reset')

    def test_capabilities_error_is_failure(self):
        with self.assertRaisesRegex(RuntimeError, 'synthetic rejection'):
            self.run_peer('caps-error')

    def test_status_error_is_failure(self):
        with self.assertRaisesRegex(RuntimeError, 'synthetic rejection'):
            self.run_peer('status-error')

    def test_running_status_is_failure(self):
        with self.assertRaisesRegex(RuntimeError, 'Unexpected QEMU status'):
            self.run_peer('status-running')

    def test_quit_nonzero_exit_is_failure(self):
        with self.assertRaisesRegex(RuntimeError, 'Unexpected QEMU status'):
            self.run_peer('quit-nonzero')

    def test_quit_hang_is_failure(self):
        with self.assertRaisesRegex(RuntimeError, 'timed out'):
            self.run_peer('quit-hang')


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--qmp-peer':
        raise SystemExit(peer(sys.argv[2], sys.argv[3:]))
    unittest.main()
