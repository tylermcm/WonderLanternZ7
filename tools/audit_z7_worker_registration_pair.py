"""Check exact paired worker controls on the installed host, offline (MIT)."""
import argparse
import hashlib
import json
from pathlib import Path
from compare_z7_working_restore import load,invoke,code_for
from audit_z7_worker_exclusive_progress import guard
from audit_z7_battery_grid_menu_checkpoint import audit as grids
from audit_z7_battery_percent import audit as battery
from build_z7_module import ROOT,HEADER
from prepare_flash_review import require_private_output


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pair',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    folder=ROOT/'.private/builds/20261121-lcd-core-host-01'
    host=json.loads((folder/'module-host.emulator.json').read_text())
    raw=(folder/'module-host.emulator.main.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==host['main_payload_sha256']=='7d7356e7775db90483ed9fe5598f401afb7fb8498a7b42bd71900db849d7f057'
    stock=(ROOT/'.private/builds/20261021-laptop-01/stock-main.bin').read_bytes()
    g=guard(raw,0x10020000,host['symbols']);results={};packets=[];metas=[]
    for name,enabled in (('disabled',False),('enabled',True)):
        folder=a.pair/name;packet=(folder/'Z7APP.BIN').read_bytes()
        m=json.loads((folder/'module.json').read_text());packets.append(packet);metas.append(m)
        assert hashlib.sha256(packet).hexdigest()==m['module_sha256']
        assert m['configuration']['worker_registration_enabled']==enabled
        noop=code_for(packet,m,'worker_pair_noop')
        assert noop[0].mnemonic=='bx' and noop[0].op_str=='lr'
        for selection in ('fourths','thirds','golden','center','dense'):
            assert not any(i.mnemonic.startswith(('ldrex','strex')) for i in code_for(packet,m,selection))
        assert not any(n.startswith(('restore_','z7_settings_','persistence_')) for n in m['symbols'])
        feature=grids(raw,host,packet,m,stock,worker_expected=enabled,worker_pair=True)
        policy=battery(raw,host,packet,m);runs={}
        for fault in (False,True):
            f=load(raw,host,packet,m,b'')
            f.call(host['symbols']['z7_display_before_paint']);f.call(host['symbols']['z7_display_after_paint'])
            assert f.labels==[('63%',299)] and bool(f.words()[50])==enabled
            if enabled:assert f.callback==f.base+(m['symbols']['worker_pair_noop']&~1)
            if fault:f.fail_site=dict(pc=g['store'],register=g['status_register'])
            returned=invoke(f,host['symbols']['z7_module_worker_tick'],limit=4096)
            io=[e for e in f.file_events if e[0] not in ('clean','invalidate')]
            assert not io and returned==(not (fault and enabled))
            assert f.worker_entries==int(enabled and not fault)
            assert (f.exclusive_attempts>10)==(enabled and fault)
            runs['injected-store-failure' if fault else 'healthy']=dict(returned=returned,worker_entries=f.worker_entries,injected_failures=f.exclusive_attempts,file_operations=len(io))
        results[name]=dict(sha256=m['module_sha256'],grid_checks=len(feature['checks']),geometry_calls=feature['geometry_calls'],battery_checks=len(policy['checks']),worker_runs=runs)
        print(name,results[name],flush=True)
    for key in ('image_bytes','bss_bytes','entry_offset','relocations','symbols'):
        assert metas[0][key]==metas[1][key]
    offset=metas[0]['symbols']['worker_pair_enabled'];allowed=set(range(32,36))|set(range(HEADER+offset,HEADER+offset+4))
    assert len(packets[0])==len(packets[1])
    assert all(x==y or i in allowed for i,(x,y) in enumerate(zip(*packets)))
    assert int.from_bytes(packets[0][HEADER+offset:HEADER+offset+4],'little')==0
    assert int.from_bytes(packets[1][HEADER+offset:HEADER+offset+4],'little')==1
    report=dict(passed=True,host_main_sha256=host['main_payload_sha256'],results=results,only_flag_and_crc_differ=True,
                noop_first_instruction='bx lr',camera_access=False,card_written=False,hardware_cause_established=False,
                limits=['Supplied GUI, telemetry, storage and native service boundaries',
                        'Store-exclusive failure is injected; physical failure PC remains unknown',
                        'No camera acceptance, timing or recovery validation'])
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
