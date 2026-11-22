"""Check complete regenerated host with exact no-I/O worker A/B pair (MIT)."""
import argparse
import hashlib
import json
from pathlib import Path
from compare_z7_working_restore import load,invoke,code_for
from audit_z7_battery_grid_menu_checkpoint import audit as grids
from build_z7_module import ROOT
from prepare_flash_review import require_private_output


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','pair','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256'] and h['display_hooks']
    blob=json.loads((ROOT/'.private/builds/20261122-worker-task-guard-01/audit.json').read_text())
    assert h['host_sha256']==blob['host_blob_sha256']
    base=int(h['host_address'],16)-0x10020000
    assert hashlib.sha256(raw[base:base+h['host_bytes']]).hexdigest()==h['host_sha256']
    stock=(ROOT/'.private/builds/20261021-laptop-01/stock-main.bin').read_bytes();results={}
    for name,enabled in (('disabled',False),('enabled',True)):
        d=a.pair/name;packet=(d/'Z7APP.BIN').read_bytes();m=json.loads((d/'module.json').read_text())
        expected={'disabled':'412dffaf9a2b5f9aa5cf9e715b66e778e9de1e9f4c67eabc2963df7899a200f9','enabled':'767ada057f52df432aa037c341d300207d1bf436fea9258c5c58b78d4556a158'}[name]
        assert hashlib.sha256(packet).hexdigest()==m['module_sha256']==expected
        for n,digest in m['source_inputs_sha256'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==digest
        noop=code_for(packet,m,'worker_pair_noop');assert noop[0].mnemonic=='bx' and noop[0].op_str=='lr'
        feature=grids(raw,h,packet,m,stock,worker_expected=enabled,worker_pair=True)
        f=load(raw,h,packet,m,b'')
        for _ in range(64):
            f.call(h['symbols']['z7_display_before_paint']);f.call(h['symbols']['z7_display_after_paint'])
            assert invoke(f,h['symbols']['z7_module_worker_tick']) and f.words()[51]==0
        assert f.worker_entries==(64 if enabled else 0)
        assert f.labels and all(x==('63%',299) for x in f.labels)
        assert bool(f.words()[50])==enabled
        assert not [e for e in f.file_events if e[0] not in ('clean','invalidate')]
        results[name]=dict(module_sha256=expected,grid_checks=len(feature['checks']),geometry_calls=feature['geometry_calls'],
                           interleaved_gui_worker_ticks=64,callback_entries=f.worker_entries,worker_guard_released=True,file_operations=0)
        print(name,results[name],flush=True)
    r=dict(passed=True,host_main_sha256=h['main_payload_sha256'],host_blob_sha256=h['host_sha256'],results=results,
           complete_regenerated_host_used=True,card_written=False,physical_fix_verified=False,
           limits=['Native UI/telemetry/kernel/filesystem/viewport services supplied',
                   'Interleaving is explicit, not physical scheduler/cache behavior',
                   'No camera updater/flash writer, real boot or recovery executed'])
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(r,indent=2)+'\n')


if __name__=='__main__':main()
