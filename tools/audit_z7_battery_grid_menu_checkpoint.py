"""Volatile native-grid menu checkpoint: publication, UI and geometry (MIT).

Uses compiled host/module/native setters and builders with supplied UI,
viewport, telemetry, kernel, filesystem and storage boundaries. No card access.
"""
import argparse
import hashlib
import json
import math
import struct
from pathlib import Path
from unicorn import UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_R0
from audit_z7_battery_thirds_checkpoint import CheckpointFixture
from audit_grid_native_value import NativeValueGrid
from audit_grid_geometry import GridFixture,BUILDER,DESCRIPTOR,TABLE
from audit_splash_image import MEM,STOCK_SHA
from trace_settings_storage import GRID_VALUE
from build_z7_module_host import STATE,ROOT
from prepare_flash_review import require_private_output

OBJECT=0xa1836f8c
LAYOUTS=[('fourths',1,0x1901,'4x4 grid'),('thirds',2,0x7a30,'3x3 grid'),
         ('golden',3,0x7a31,'Golden ratio'),('center',4,0x7a32,'Center cross'),
         ('dense',5,0x7a33,'6x6 grid'),('off',0,0x1902,'Off')]


def audit(raw,host,packet,module,stock,worker_expected=False):
    assert hashlib.sha256(raw).hexdigest()==host['main_payload_sha256']
    assert hashlib.sha256(packet).hexdigest()==module['module_sha256']
    assert hashlib.sha256(stock).hexdigest()==STOCK_SHA
    expected_kind='original-Z7-grid-restore-readonly-checkpoint' if worker_expected else 'original-Z7-battery-grid-menu-checkpoint'
    assert module['kind']==expected_kind
    assert not any(n.startswith(('sm_','persistence_','preset_','focal_')) or
                   (n.startswith('z7_settings_') and not (worker_expected and n.startswith('z7_settings_files_')))
                   for n in module['symbols'])
    f=CheckpointFixture(raw,host,packet);checks=[]
    def check(name,good):
        assert good,name
        checks.append(name)
    protected={0xa1833548:44,0xa182ed34:4,0xa1829b0c:4,0xa1827408:36}
    snapshots={a:bytes(f.u.mem_read(a,n)) for a,n in protected.items()}
    old_menu=bytes(f.u.mem_read(OBJECT,44));stores=[]
    def write(u,access,address,size,value,context):
        if not STATE<=address<STATE+host['state_bytes']:stores.append(hex(address))
    hook=f.u.hook_add(UC_HOOK_MEM_WRITE,write,begin=0xa1800000,end=0xbfffffff)
    status=f.call(host['symbols']['z7_module_load_once'],STATE);f.u.hook_del(hook)
    check('init-no-native-stores-or-rendering',status==8 and not stores and not f.labels and not f.getter_calls)
    check('grid-page-not-published-in-initializer',bytes(f.u.mem_read(OBJECT,44))==old_menu and f.words()[34:36]==(1,0))
    check('only-expected-grid-paint-and-optional-worker-hooks',f.words()[28:30]==(0,0) and f.words()[36:49]==(0,)*13 and
          ((bool(f.words()[49]) and f.words()[50:52]==(1,0)) if worker_expected else f.words()[49:52]==(0,)*3))
    f.setword(92,0);f.call(host['symbols']['z7_display_before_paint'])
    check('not-ready-cannot-publish-grid-menu',f.words()[35]==0 and bytes(f.u.mem_read(OBJECT,44))==old_menu)
    f.setword(92,1)
    listing,records=0xa2908000,0xa2909000
    f.u.mem_write(0xa181f91c,struct.pack('<I',listing));f.u.mem_write(listing,struct.pack('<4I',16,1,1,records));f.u.mem_write(records,struct.pack('<I',OBJECT))
    f.call(host['symbols']['z7_display_before_paint'])
    check('active-grid-page-defers-publication',f.words()[35]==0 and bytes(f.u.mem_read(OBJECT,44))==old_menu)
    f.u.mem_write(records,struct.pack('<I',0xa1837bec));f.call(host['symbols']['z7_display_before_paint'])
    check('inactive-page-publishes-on-existing-gui-hook',f.words()[35]==1 and int.from_bytes(f.u.mem_read(OBJECT+40,4),'little')==f.words()[32] and int.from_bytes(f.u.mem_read(OBJECT+16,4),'little')==f.words()[33])
    f.u.mem_write(0xa181f91c,bytes(4));f.call(host['symbols']['z7_display_before_paint']);f.call(host['symbols']['z7_display_after_paint'])
    check('battery-still-renders',f.labels==[('63%',299)] and len(f.list_calls)==1)
    check('custom-page-dispatch-key-and-histogram-masks-untouched',all(bytes(f.u.mem_read(a,len(b)))==b for a,b in snapshots.items()))
    base,memory=f.words()[12],f.words()[14];symbols=module['symbols']
    a=NativeValueGrid(raw);a.initialize();a.u.mem_map(STATE,4096)
    a.u.mem_write(STATE,bytes(f.u.mem_read(STATE,256)));a.u.mem_write(base,bytes(f.u.mem_read(base,memory)))
    a.u.mem_write(OBJECT+40,struct.pack('<I',f.words()[32]));a.u.mem_write(OBJECT+16,struct.pack('<I',f.words()[33]))
    check('volatile-default-is-thirds',a.word(base+symbols['checkpoint_grid_value'])==2)
    meta=struct.unpack('<7I',a.u.mem_read(f.words()[32],28));maps=struct.unpack('<6I',a.u.mem_read(meta[4],24))
    for row,(name,value,control,label) in enumerate(LAYOUTS):
        if value:
            handlers=[fn for event,fn,_,_ in struct.iter_unpack('<4I',a.u.mem_read(maps[row],272)) if event==0x239]
            check(name+'-menu-event-calls-owned-adapter',handlers==[base+symbols[name]])
            a.call(handlers[0])
        else:a.call(0x104f5593)
        check(name+'-stores-only-native-on-off',a.word(GRID_VALUE)==int(value!=0) and all(v in (0,1) for v in a.setters))
        if value:check(name+'-volatile-choice',a.word(base+symbols['checkpoint_grid_value'])==value)
        a.labels.clear();a.rows.clear();a.marks.clear();a.u.mem_write(OBJECT+36,struct.pack('<I',MEM+0x10000));a.call(base+symbols['grid_enter'],OBJECT)
        check(name+'-six-labels-and-selection',a.labels==[(39+i,x[3]) for i,x in enumerate(LAYOUTS)] and a.rows==list(range(39,45)) and a.marks==[(control,1)])
        check(name+'-native-visibility',a.call(0x1037723e)==int(value!=0))
    check('menu-activation-does-not-program-internal-flash-in-fixture',not a.operations)
    geometry_calls=0
    for viewport in ((0,0,720,480),(20,40,700,440),(0,0,640,426)):
        a.viewport=viewport;reference=GridFixture(stock,viewport,0)
        for mode in range(3):
            for crop in (0,1,2,4,8):
                reference.crop=crop;a.call(0x100704fa,0x402,crop,MEM+0x800)
                for name,value,_,_ in LAYOUTS[:-1]:
                    a.call(base+symbols[name]);a.call(BUILDER,mode)
                    actual=struct.unpack('<hhIHHhhIHHHHBBH',a.u.mem_read(DESCRIPTOR,32))
                    expected=reference.geometry(mode,{1:3,2:2,3:2,4:1,5:5}[value]);geometry_calls+=2
                    if value!=3:good=actual==expected
                    else:
                        good=all(actual[i]==expected[i] for i in (0,2,4,6,7,9,10,11,12,13,14))
                        for origin,interval,span in ((1,3,7),(5,8,2)):
                            offset=actual[origin]-(expected[origin]-expected[interval])
                            good &= abs(offset-expected[span]*((3-math.sqrt(5))/2))<1 and 2*offset+actual[interval]==expected[span]
                    check('geometry-'+str((viewport,mode,crop,value)),good and a.word(GRID_VALUE)==1)
    for name,address,data in [('evf',0xa18237c6,b'\2'),('movie',0xa201d510,b'\1')]:
        old=bytes(a.u.mem_read(address,len(data)));a.u.mem_write(address,data)
        check(name+'-native-table',a.call(host['symbols']['z7_display_grid_source'])==TABLE)
        a.u.mem_write(address,old)
    check('all-menu-setters-normal-native-on-off',all(v in (0,1) for v in a.setters))
    check('protected-native-state-after-menu-geometry',all(bytes(a.u.mem_read(addr,len(data)))==data for addr,data in snapshots.items()))
    fresh=CheckpointFixture(raw,host,packet)
    check('fresh-load-resets-volatile-choice-to-thirds',fresh.call(host['symbols']['z7_module_load_once'],STATE)==8 and int.from_bytes(fresh.u.mem_read(fresh.words()[12]+symbols['checkpoint_grid_value'],4),'little')==2)
    bad=CheckpointFixture(raw,host,packet);bad.u.mem_write(OBJECT,struct.pack('<I',0xdeadbeef))
    check('foreign-native-page-rejects-without-residency',bad.call(host['symbols']['z7_module_load_once'],STATE)==7 and not bad.live and not bad.words()[23])
    class BadRegistration(CheckpointFixture):
        injected=False
        entry_body=0
        registration_target=0
        def hook(self,u,pc,size,context):
            if pc==host['symbols']['z7_module_call'] & ~1:self.entry_body=self.words()[19]
            if self.entry_body and pc==self.entry_body+module['entry_offset']:
                api=u.reg_read(UC_ARM_REG_R0)
                self.registration_target=int.from_bytes(u.mem_read(api+16,4),'little') & ~1
            if self.registration_target and pc==self.registration_target and not self.injected:
                candidate=u.reg_read(UC_ARM_REG_R0)
                meta=int.from_bytes(u.mem_read(candidate+8,4),'little')
                u.mem_write(meta+20,struct.pack('<I',0x00090009));self.injected=True
            super().hook(u,pc,size,context)
    failed=BadRegistration(raw,host,packet);native_page=bytes(failed.u.mem_read(OBJECT,44))
    check('registration-failure-rolls-back-before-native-publication',failed.call(host['symbols']['z7_module_load_once'],STATE)==7 and failed.injected and not failed.live and failed.words()[22:24]==(0,0) and bytes(failed.u.mem_read(OBJECT,44))==native_page)
    return dict(passed=True,checks=checks,geometry_calls=geometry_calls,module_sha256=module['module_sha256'],host_main_sha256=host['main_payload_sha256'],camera_access=False,card_written=False,physical_persistence_verified=False,limits=['Explicit UI/kernel/filesystem/telemetry/storage and viewport boundaries','Menu page-list state is supplied; actual scheduling and pixels unverified','Native On/Off persistence remains camera-owned; layout is deliberately volatile','No installation, hardware or recovery clearance'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--stock',type=Path,default=ROOT/'.private/builds/20261021-laptop-01/stock-main.bin')
    p.add_argument('--readonly-restore',action='store_true',help='Require the read-only restore profile and its one worker; feature audit does not run file I/O')
    a=p.parse_args();out=require_private_output(a.output)
    host=json.loads((a.host/'module-host.emulator.json').read_text());module=json.loads((a.module/'module.json').read_text())
    r=audit((a.host/'module-host.emulator.main.bin').read_bytes(),host,(a.module/'Z7APP.BIN').read_bytes(),module,a.stock.read_bytes(),a.readonly_restore)
    r['source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(r,indent=2)+'\n')
    print(json.dumps(dict(passed=True,checks=len(r['checks']),geometry_calls=r['geometry_calls'])))


if __name__=='__main__':main()
