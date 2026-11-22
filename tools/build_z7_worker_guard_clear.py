"""Build the private, manually triggered CLREX-only addition control (MIT)."""
import argparse
import hashlib
import json
from pathlib import Path
from build_z7_module import ROOT,build
from build_z7_module_host import ZIG
from prepare_flash_review import require_private_output


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=require_private_output(a.output)
    source=ROOT/'z7-native-modules/plugins/worker_guard_clear.c'
    data,meta=build(source,zig=ZIG.resolve());again,other=build(source,zig=ZIG.resolve())
    assert data==again and meta==other
    baseline=json.loads((ROOT/'.private/builds/20261122-worker-registration-pair-01/disabled/module.json').read_text())
    inputs={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in baseline['source_inputs_sha256'] if not n.endswith('worker_registration_pair.c')}
    inputs['z7-native-modules/plugins/worker_guard_clear.c']=hashlib.sha256(source.read_bytes()).hexdigest()
    assert not any(n.startswith(('restore_','z7_settings_','persistence_')) for n in meta['symbols'])
    meta.update(kind='original-Z7-worker-guard-clear',file_bytes=len(data),module_sha256=hashlib.sha256(data).hexdigest(),
                source_inputs_sha256=inputs,configuration=dict(battery_percent_enabled=True,worker_registration_enabled=False),
                reproducible=True,do_not_stage=True,firmware_image=False,repair_claimed=False,
                scope='Manual Center selection: CLREX then proven ordinary read; no LDREX, STREX, worker or host writes')
    out.mkdir(parents=True,exist_ok=False)
    (out/'Z7APP.BIN').write_bytes(data)
    (out/'module.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(bytes=len(data),sha256=meta['module_sha256'],reproducible=True)))


if __name__=='__main__':main()
