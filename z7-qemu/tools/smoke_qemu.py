# SPDX-License-Identifier: GPL-2.0-or-later
"""Realize the display machine, query QMP and quit, without any firmware."""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time

def smoke(binary, quit_timeout=10):
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
    with tempfile.TemporaryFile() as errors:
        options = dict(creationflags=subprocess.CREATE_NO_WINDOW) if os.name == 'nt' else {}
        proc=subprocess.Popen([str(binary.resolve()),'-M','nikon-z7-display',
            '-smp','2','-display','none','-serial','none','-monitor','none','-nic','none',
            '-chardev','null,id=z7uart','-S','-qmp',f'tcp:127.0.0.1:{port},server=on,wait=off'],
            stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=errors,**options)
        try:
            deadline = time.monotonic() + 10
            while True:
                try:
                    connection = socket.create_connection(('127.0.0.1', port), .5)
                    break
                except OSError:
                    if proc.poll() is not None or time.monotonic() >= deadline:
                        raise RuntimeError('QEMU did not open its QMP socket')
                    time.sleep(.05)
            # Use the controller's TCP transport. Windows stdio can corrupt
            # batched requests. Capability/status replies remain mandatory.
            with connection:
                connection.settimeout(5)
                with connection.makefile('rwb', buffering=0) as stream:
                    greeting = json.loads(stream.readline())
                    if 'QMP' not in greeting:
                        raise RuntimeError('Missing QMP greeting')
                    replies = []
                    for name in ('qmp_capabilities', 'query-status'):
                        stream.write(json.dumps({'execute': name}).encode() + b'\n')
                        while True:
                            line = stream.readline()
                            if not line:
                                raise RuntimeError('QMP closed before the reply to ' + name)
                            reply = json.loads(line)
                            if 'error' in reply:
                                raise RuntimeError(str(reply['error']))
                            if 'return' in reply:
                                replies.append(reply['return'])
                                break
                    # qapi/control.json explicitly permits termination before
                    # the quit reply reaches the client. Do not read or require
                    # that acknowledgement; require a clean, bounded exit.
                    stream.write(json.dumps({'execute': 'quit'}).encode() + b'\n')
                    proc.wait(timeout=quit_timeout)
            status = replies[1]
            if proc.returncode or status.get('running') is not False:
                raise RuntimeError('Unexpected QEMU status: ' + str(status))
        except Exception as error:
            if proc.poll() is None:
                proc.kill(); proc.wait(timeout=10)
            errors.seek(0)
            raise RuntimeError('Firmware-free realization failed: ' + str(error) + '\n' +
                               errors.read().decode('utf-8', errors='replace')) from error
        errors.seek(0)
        return {'passed':True,'firmware_used':False,'machine':'nikon-z7-display',
                'qmp_status':status['status'],'transport':'localhost-tcp'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('binary',type=Path)
    a=p.parse_args()
    print(json.dumps(smoke(a.binary)))

if __name__=='__main__':main()
