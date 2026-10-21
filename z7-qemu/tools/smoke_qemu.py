# SPDX-License-Identifier: GPL-2.0-or-later
"""Realize the display machine, query QMP and quit, without any firmware."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('binary',type=Path)
    a=p.parse_args()
    with tempfile.TemporaryFile() as errors:
        proc=subprocess.Popen([str(a.binary.resolve()),'-M','nikon-z7-display',
            '-smp','2','-display','none','-serial','none','-monitor','none','-nic','none',
            '-chardev','null,id=z7uart','-S','-qmp','stdio'],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=errors,text=True)
        requests=''.join(json.dumps({'execute':s})+'\n' for s in ['qmp_capabilities','query-status','quit'])
        try:
            output,_=proc.communicate(requests,timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill();proc.wait();raise
        errors.seek(0)
        diagnostics=errors.read().decode('utf-8',errors='replace')
        messages=[json.loads(line) for line in output.splitlines()]
        statuses=[m['return'] for m in messages if isinstance(m.get('return'),dict) and 'running' in m['return']]
        if proc.returncode or any('error' in m for m in messages) or len(statuses)!=1 or statuses[0]['running']:
            raise RuntimeError('Firmware-free realization failed: '+diagnostics)
        print(json.dumps({'passed':True,'firmware_used':False,'machine':'nikon-z7-display','qmp_status':statuses[0]['status']}))

if __name__=='__main__':main()
