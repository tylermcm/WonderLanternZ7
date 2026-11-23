"""Check volatile LCD layout IDs stay out of native On/Off storage (MIT)."""
import argparse
import hashlib
import json
import math
import struct
from pathlib import Path
from audit_z7_display_persistence import PersistenceFixture
from audit_grid_native_value import NativeValueGrid
from audit_grid_geometry import GridFixture,BUILDER,DESCRIPTOR
from audit_z7_battery_grid_menu_checkpoint import LAYOUTS,OBJECT
from audit_splash_image import MEM
from trace_settings_storage import GRID_VALUE
from build_z7_module import ROOT
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--persistent',action='store_true',help='Audit the persistent display-preference checkpoint with RAM-only grid layout')
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256']
    assert hashlib.sha256(packet).hexdigest()==m['module_sha256']
    f=PersistenceFixture(raw,h,packet);assert f.call(h['symbols']['z7_module_load_once'],STATE)==8
    f.base=f.words()[12];symbols=m['symbols'];assert f.words()[50]==int(a.persistent)
    assert m['configuration']['persistent_settings']==a.persistent
    def fixture(image=raw,metadata=m,body=f):
        g=NativeValueGrid(image);g.initialize();g.u.mem_map(STATE,4096)
        g.u.mem_write(STATE,bytes(body.u.mem_read(STATE,256)))
        g.u.mem_write(body.base,bytes(body.u.mem_read(body.base,body.words()[14])))
        g.u.mem_write(OBJECT+40,struct.pack('<I',body.words()[32]));g.u.mem_write(OBJECT+16,struct.pack('<I',body.words()[33]))
        return g
    g=fixture();checks=[]
    def check(name,good):assert good,name;checks.append(name)
    check('default-layout-thirds',g.word(f.base+symbols['checkpoint_grid_value'])==2)
    for name,value,control,label in LAYOUTS:
        g.call(f.base+symbols[name if value else 'off_owned'])
        check(name+'-native-on-off-only',g.word(GRID_VALUE)==int(value!=0) and all(x in (0,1) for x in g.setters))
        if value:check(name+'-ram-layout',g.word(f.base+symbols['checkpoint_grid_value'])==value)
        g.labels.clear();g.rows.clear();g.marks.clear();g.u.mem_write(OBJECT+36,struct.pack('<I',MEM+0x10000))
        g.call(f.base+symbols['grid_enter'],OBJECT)
        check(name+'-seven-menu-rows-and-selection',g.labels==[(39+i,x[3]) for i,x in enumerate(LAYOUTS)]+[(45,'Display settings')] and g.rows==list(range(39,46)) and g.marks==[(control,1)])
    stock=(ROOT/'.private/builds/20261021-laptop-01/stock-main.bin').read_bytes();geometry_calls=0
    for viewport in ((0,0,720,480),(20,40,700,440),(0,0,640,426)):
        g.viewport=viewport;reference=GridFixture(stock,viewport,0)
        for mode in range(3):
            for crop in (0,1,2,4,8):
                reference.crop=crop;g.call(0x100704fa,0x402,crop,MEM+0x800)
                for name,value,_,_ in LAYOUTS[:-1]:
                    g.call(f.base+symbols[name]);g.call(BUILDER,mode)
                    actual=struct.unpack('<hhIHHhhIHHHHBBH',g.u.mem_read(DESCRIPTOR,32))
                    expected=reference.geometry(mode,{1:3,2:2,3:2,4:1,5:5}[value]);geometry_calls+=2
                    if value!=3:good=actual==expected
                    else:
                        good=all(actual[i]==expected[i] for i in (0,2,4,6,7,9,10,11,12,13,14))
                        for origin,interval,span in ((1,3,7),(5,8,2)):
                            offset=actual[origin]-(expected[origin]-expected[interval])
                            good &= abs(offset-expected[span]*((3-math.sqrt(5))/2))<1 and 2*offset+actual[interval]==expected[span]
                    check('geometry-'+str((viewport,mode,crop,value)),good and g.word(GRID_VALUE)==1)
    for name,address,value in (('evf',0xa18237c6,b'\2'),('movie',0xa201d510,b'\1')):
        old=bytes(g.u.mem_read(address,len(value)));g.u.mem_write(address,value)
        for choice in LAYOUTS[:-1]:
            g.call(f.base+symbols[choice[0]]);g.call(BUILDER,0)
            actual=struct.unpack('<hhIHHhhIHHHHBBH',g.u.mem_read(DESCRIPTOR,32));expected=reference.geometry(0,3)
            check(name+'-'+choice[0]+'-stock-geometry',actual==expected)
        g.u.mem_write(address,old)
    legacy=[]
    for value in (2,3,4,5):
        g.u.mem_write(GRID_VALUE,struct.pack('<I',value));writes=len(g.setters)
        g.labels.clear();g.marks.clear();g.call(f.base+symbols['grid_enter'],OBJECT)
        check('legacy-'+str(value)+'-read-compatible-without-rewrite',g.marks==[(LAYOUTS[value-1][2],1)] and len(g.setters)==writes and g.word(GRID_VALUE)==value)
        g.call(f.base+symbols['thirds']);check('legacy-'+str(value)+'-next-selection-normalizes-on-off',g.word(GRID_VALUE)==1)
        legacy.append(value)
    check('no-explicit-storage-programming',not g.operations)
    # Compare the owner-tested prior packet's UI argument, not a new camera run.
    olddir=ROOT/'.private/review/20261122-lcd-volatile-01/candidate'
    oldpacket=(olddir/'Z7APP.BIN').read_bytes();oldmeta=json.loads((olddir/'module.json').read_text())
    assert hashlib.sha256(oldpacket).hexdigest()=='9b076c6db032d6b17884aadda8ec75934be9b9456655e2ef30010870d51c8592'
    old=PersistenceFixture(raw,h,oldpacket);assert old.call(h['symbols']['z7_module_load_once'],STATE)==8;old.base=old.words()[12]
    previous=fixture(body=old);previous.call(old.base+oldmeta['symbols']['dense'])
    assert previous.setters[-1]==5
    report=dict(passed=True,module_sha256=m['module_sha256'],checks=len(checks),check_names=checks,geometry_calls=geometry_calls,
                native_setter_values=sorted(set(g.setters)),previous_dense_setter_value=previous.setters[-1],legacy_read_values=legacy,
                startup_rewrites_legacy_values=False,persistent_display_preferences=a.persistent,camera_access=False,card_written=False,
                limits=['Native On/Off setter and geometry instructions execute with supplied storage/UI/viewport boundaries',
                        'No physical grid pixels/capture/output lifecycle or persistence test',
                        'Layout is volatile, not saved in custom preference journal'])
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=True,checks=len(checks),geometry_calls=geometry_calls,native_setter_values=report['native_setter_values'])))


if __name__=='__main__':main()
