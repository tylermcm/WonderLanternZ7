"""Audit progress publication and hardened restore on the working host (MIT)."""
import argparse
import hashlib
import json
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
from unicorn import UC_HOOK_MEM_WRITE
from compare_z7_working_restore import load,invoke
from audit_z7_grid_restore_readonly import audit as restore_audit
from audit_z7_battery_grid_menu_checkpoint import audit as grid_audit
from audit_splash_image import MEM
from build_z7_module import ROOT,HEADER
from grid_restore_record import encode
from prepare_flash_review import require_private_output


def inspect(folder):
    packet=(folder/'Z7APP.BIN').read_bytes();m=json.loads((folder/'module.json').read_text())
    assert hashlib.sha256(packet).hexdigest()==m['module_sha256']
    cs=Cs(CS_ARCH_ARM,CS_MODE_THUMB);cs.skipdata=True
    for name,fn in m['function_details'].items():
        assert fn['address']==m['symbols'][name]
        start=fn['address']&~1;size=fn['bytes'];assert size>0 and start+size<=m['image_bytes']
        instructions=list(cs.disasm(packet[HEADER+start:HEADER+start+size],start))
        assert sum(i.size for i in instructions)==size,name
        assert not any(i.mnemonic.startswith(('ldrex','strex','clrex')) for i in instructions),name
        if name=='worker_progress_tick':
            assert not any(i.mnemonic in ('bl','blx') for i in instructions)
    for name,digest in m['source_inputs_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest
    return packet,m


def menu(f,m):
    f.menu_active=True;f.grid_labels.clear();f.marks.clear()
    f.u.mem_write(0xa1836f8c+36,(MEM+0x10000).to_bytes(4,'little'))
    f.call(f.base+m['symbols']['grid_enter'],0xa1836f8c);f.menu_active=False
    assert len(f.grid_labels)==6
    return f.grid_labels[-1][1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('host','progress','restore','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256']=='24b2074559ca6089432011d98a72193f81e112c2621aee2aa0ed1359febfa7ce'
    pp,pm=inspect(a.progress);rp,rm=inspect(a.restore)
    assert pm['symbols']['worker_progress_ticks']%4==0
    assert all(rm['symbols'][n]%4==0 for n in ('restore_gui_seen','restore_state','restore_choice','restore_user_selected'))
    assert pm['kind']=='original-Z7-worker-progress-checkpoint' and rm['checkpoint_revision']==2
    assert not any(n.startswith(('restore_','z7_settings_','persistence_')) for n in pm['symbols'])
    assert not any(p in pp for p in (b'Z7GRID.DAT',b'Z7CFG0.DAT',b'Z7CFG1.DAT'))
    assert 'z7_settings_files_write' not in rm['symbols']
    stock=(ROOT/'.private/builds/20261021-laptop-01/stock-main.bin').read_bytes()
    progress_features=grid_audit(raw,h,pp,pm,stock,worker_expected=True,worker_progress=True)
    restore_features=grid_audit(raw,h,rp,rm,stock,worker_expected=True)
    print('Grid checks',len(progress_features['checks']),len(restore_features['checks']),flush=True)
    f=load(raw,h,pp,pm,b'');symbol=pm['symbols']['worker_progress_ticks']
    counter=lambda:int.from_bytes(f.u.mem_read(f.base+symbol,4),'little')
    assert counter()==0
    for _ in range(3):assert invoke(f,h['symbols']['z7_module_worker_tick'])
    assert counter()==3 and not f.labels
    f.call(h['symbols']['z7_display_before_paint']);f.call(h['symbols']['z7_display_after_paint'])
    assert f.labels==[('63%',299)] and menu(f,pm)=='Off [W 0003]'
    for _ in range(3):assert menu(f,pm)=='Off [W 0003]' and counter()==3
    observed=[]
    for value in (0,8,9,98,99,998,999,9998,9999):
        f.u.mem_write(f.base+symbol,value.to_bytes(4,'little'))
        writes=[];textbase=f.base+pm['symbols']['worker_progress_text']
        def text_write(u,access,address,size,data,context):writes.append(address)
        token=f.u.hook_add(UC_HOOK_MEM_WRITE,text_write,begin=textbase,end=textbase+12)
        assert invoke(f,h['symbols']['z7_module_worker_tick']);f.u.hook_del(token)
        expected=min(value+1,9999)
        assert counter()==expected and not writes and f.words()[51]==0
        label=menu(f,pm);assert label==f'Off [W {expected:04d}]'
        observed.append(label)
    before=counter()
    for choice in ('fourths','thirds','golden','center','dense'):assert invoke(f,f.base+pm['symbols'][choice]) and counter()==before
    f.setword(204,1);assert invoke(f,h['symbols']['z7_module_worker_tick']) and counter()==before;f.setword(204,0)
    assert not [e for e in f.file_events if e[0] not in ('clean','invalidate')]
    fresh=load(raw,h,pp,pm,b'');assert int.from_bytes(fresh.u.mem_read(fresh.base+symbol,4),'little')==0
    restore=restore_audit(raw,h,rp,rm)
    print('Restore checks',len(restore['checks']),flush=True)
    g=load(raw,h,rp,rm,encode(5));latch=g.base+rm['symbols']['restore_user_selected']
    g.call(h['symbols']['z7_display_before_paint']);g.call(h['symbols']['z7_display_after_paint'])
    assert invoke(g,h['symbols']['z7_module_worker_tick']) and int.from_bytes(g.u.mem_read(latch,4),'little')==0
    assert int.from_bytes(g.u.mem_read(g.base+rm['symbols']['restore_state'],4),'little')==2
    for choice in ('fourths','thirds','golden','center','dense','center'):
        assert invoke(g,g.base+rm['symbols'][choice])
        assert int.from_bytes(g.u.mem_read(latch,4),'little')==1
    assert menu(g,rm)=='Off [SD skip]'
    assert int.from_bytes(g.u.mem_read(g.base+rm['symbols']['checkpoint_grid_value'],4),'little')==4
    r=dict(passed=True,host_main_sha256=h['main_payload_sha256'],
           progress=dict(module_sha256=pm['module_sha256'],file_bytes=len(pp),compiled_functions_without_exclusives=len(pm['function_details']),grid_checks=len(progress_features['checks']),geometry_calls=progress_features['geometry_calls'],format_boundary_labels=observed,no_gui_calls_or_text_writes_from_worker=True,menu_reads_do_not_increment=True,saturates_at=9999,fresh_boot_zero=True,file_operations=0),
           restore=dict(module_sha256=rm['module_sha256'],file_bytes=len(rp),compiled_functions_without_exclusives=len(rm['function_details']),grid_checks=len(restore_features['checks']),geometry_calls=restore_features['geometry_calls'],fault_preemption_codec_checks=len(restore['checks']),read_only=True,gui_latch_stays_one_after_repeated_choices=True,selection_after_ready_vetoes_restore=True),
           card_written=False,hardware_tested=False,stage_authorized=False,
           limits=['Only compiled module functions scanned; called native routines are outside scan',
                   'UI/kernel/filesystem/telemetry and interleaving are supplied fixture boundaries',
                   'Selection latch assumes existing native GUI event ownership',
                   'No physical counter, card-read, cache/scheduler or recovery validation'])
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(r,indent=2)+'\n')
    print('All checkpoint checks passed',flush=True)


if __name__=='__main__':main()
