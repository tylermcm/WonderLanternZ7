"""Exact-host battery/thirds boundary and native geometry regression (MIT).

Supplied filesystem/kernel, GUI telemetry/rendering, viewport and crop inputs.
No physical camera, pixels, card writes or recovery validation.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_R0
from audit_z7_battery_percent import AutomaticFixture
from audit_grid_geometry import TABLE,BUILDER,DESCRIPTOR
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output

RAW=0xa24f182c


class CheckpointFixture(AutomaticFixture):
    geometry_active=False
    viewport=(0,0,720,480)
    crop=0

    def __init__(self,*args):
        super().__init__(*args)
        self.u.mem_map(0xa24f1000,4096)  # Explicit native On/Off property input.

    def hook(self,u,address,size,context):
        if self.geometry_active and address==0x104065a4:
            assert u.reg_read(UC_ARM_REG_R0)==0x402
            self.ret(self.crop)
        elif self.geometry_active and address==0x10437190:
            pointer=u.reg_read(UC_ARM_REG_R0)
            for offset in (8,0x14):u.mem_write(pointer+offset,struct.pack('<4h',*self.viewport))
            u.mem_write(pointer+0x28,b'\1');self.ret(0)
        else:super().hook(u,address,size,context)


def audit(raw,host,packet,module):
    assert hashlib.sha256(raw).hexdigest()==host['main_payload_sha256']
    assert hashlib.sha256(packet).hexdigest()==module['module_sha256']
    assert module['kind']=='original-Z7-battery-thirds-checkpoint'
    assert not any(n.startswith(('sm_','persistence_','z7_settings_','preset_','focal_')) for n in module['symbols'])
    f=CheckpointFixture(raw,host,packet);checks=[]
    def check(name,good):
        assert good,name
        checks.append(name)
    watched={0xa1833548:44,0xa182ed34:4,0xa1836f8c:44,0xa1829b0c:4,0xa1827408:36,RAW:4}
    before={a:bytes(f.u.mem_read(a,n)) for a,n in watched.items()}
    stores=[]
    def write(u,access,address,size,value,context):
        if not STATE<=address<STATE+host['state_bytes']:stores.append(hex(address))
    h=f.u.hook_add(UC_HOOK_MEM_WRITE,write,begin=0xa1800000,end=0xbfffffff)
    status=f.call(host['symbols']['z7_module_load_once'],STATE);f.u.hook_del(h)
    check('load-without-native-ram-stores-or-rendering',status==8 and not stores and not f.getter_calls and not f.labels and not f.list_calls)
    w=f.words();base=w[12]
    check('only-grid-source-and-battery-paint-hooks',bool(w[26]) and w[27:30]==(0,)*3 and bool(w[30]) and bool(w[31]) and w[32:52]==(0,)*20)
    check('no-native-menu-dispatch-key-mask-or-setting-init-change',all(bytes(f.u.mem_read(a,len(b)))==b for a,b in before.items()))
    stock=bytes(f.u.mem_read(TABLE,96));thirds=bytearray(stock)
    for row in range(3):
        for offset in (10,22):struct.pack_into('<H',thirds,row*32+offset,2)
    check('initial-stock-off-input-falls-back',f.call(host['symbols']['z7_display_grid_source'])==TABLE)
    # Select native On explicitly as an input; module must not write the setting.
    f.u.mem_write(RAW,struct.pack('<I',1))
    pointer=f.call(host['symbols']['z7_display_grid_source'])
    check('owned-grid-table-only-changes-six-count-fields',pointer==base+module['symbols']['checkpoint_thirds'] and bytes(f.u.mem_read(pointer,96))==bytes(thirds))
    for key,value in ((0x102d,0),(0x102d,1),(0x102d,2),(0x102d,5),(0x1234,7)):
        check('native-scalar-unchanged-'+str(key)+'-'+str(value),f.call(host['symbols']['z7_display_scalar'],key,value)==value)
    for name,address,data in [('off',RAW,bytes(4)),('other-grid-value',RAW,struct.pack('<I',2)),('evf',0xa18237c6,b'\2'),('movie',0xa201d510,b'\1')]:
        saved=bytes(f.u.mem_read(address,len(data)));f.u.mem_write(address,data)
        check(name+'-uses-stock-table',f.call(host['symbols']['z7_display_grid_source'])==TABLE)
        f.u.mem_write(address,saved)
    f.setword(92,0)
    check('before-host-ready-stock-grid',f.call(host['symbols']['z7_display_grid_source'])==TABLE)
    f.call(host['symbols']['z7_display_before_paint']);f.call(host['symbols']['z7_display_after_paint'])
    check('before-host-ready-no-battery-work',not f.getter_calls and not f.labels and not f.list_calls)
    f.setword(92,1)
    examples=[];f.geometry_active=True
    for viewport in ((0,0,720,480),(20,40,700,440),(0,0,640,426)):
        f.viewport=viewport;left,top,right,bottom=viewport
        for mode in range(3):
            for crop in (0,1,2,4,8):
                f.crop=crop;f.call(BUILDER,mode)
                d=struct.unpack('<hhIHHhhIHHHHBBH',f.u.mem_read(DESCRIPTOR,32))
                check('native-third-spacing-'+str((viewport,mode,crop)),(d[4],d[9])==(2,2) and d[3]==(bottom-top)//3 and d[8]==(right-left)//3)
                f.u.mem_write(0xa18237c6,b'\2');f.call(BUILDER,mode)
                stock_d=struct.unpack('<hhIHHhhIHHHHBBH',f.u.mem_read(DESCRIPTOR,32));f.u.mem_write(0xa18237c6,b'\0')
                check('stock-evf-and-preserved-extents-'+str((viewport,mode,crop)),
                      (stock_d[4],stock_d[9])==(3,3) and
                      all(stock_d[i]==d[i] for i in (0,2,6,7,10,11,12,13,14)) and
                      d[1]-d[3]==stock_d[1]-stock_d[3] and d[5]-d[8]==stock_d[5]-stock_d[8])
                if viewport==(0,0,720,480) and crop==0:examples.append(dict(mode=mode,descriptor=list(d)))
    f.geometry_active=False
    f.call(host['symbols']['z7_display_before_paint']);f.call(host['symbols']['z7_display_after_paint'])
    check('battery-remains-visible',f.labels==[('63%',299)] and f.getter_calls==1 and len(f.list_calls)==1)
    check('native-menu-and-dispatch-still-unchanged',all(bytes(f.u.mem_read(a,len(b)))==b for a,b in before.items() if a!=RAW))
    check('native-grid-on-value-not-rewritten',bytes(f.u.mem_read(RAW,4))==struct.pack('<I',1))
    bad=CheckpointFixture(raw,host,packet);bad.u.mem_write(TABLE+10,bytes(2))
    check('foreign-grid-schema-rejected-without-residency',bad.call(host['symbols']['z7_module_load_once'],STATE)==7 and not bad.live and not bad.words()[23])
    return dict(passed=True,checks=checks,native_geometry_examples=examples,
                module_sha256=module['module_sha256'],host_main_sha256=host['main_payload_sha256'],
                camera_verified=False,card_written=False,
                limits=['Incoming telemetry, viewport, crop and selected UI/kernel/filesystem services supplied',
                        'Native builder/host/module instructions execute; no physical pixels or task scheduler',
                        'No hardware approval or recovery clearance'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('host','module','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    host=json.loads((a.host/'module-host.emulator.json').read_text(encoding='utf-8'))
    module=json.loads((a.module/'module.json').read_text(encoding='utf-8'))
    r=audit((a.host/'module-host.emulator.main.bin').read_bytes(),host,(a.module/'Z7APP.BIN').read_bytes(),module)
    r['source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(r,indent=2)+'\n')
    print(json.dumps(dict(passed=True,checks=len(r['checks']))))


if __name__=='__main__':main()
