"""Compiled portrait orientation latch at pinned menu drawing triggers.

SPDX-License-Identifier: MIT. Caller-owned state and raw message inputs supplied;
compiled trigger parsing, acquire/release state access and reset execute. No native
page/output admission, band ownership/cleanup, real sensor scheduling or pixels.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from audit_splash_image import STOCK_SHA
from audit_z7_portrait_draw import PortraitFixture,CODE,BOX,MESSAGE,PAYLOAD,WORDS
from build_z7_module import build
from build_z7_module_host import ROOT,ZIG
STATE=BOX+256

def audit(raw,packet,metadata):
    meta=dict(metadata,symbols=dict(metadata['symbols']));meta['symbols']['z7_portrait_draw_probe']=metadata['symbols']['z7_portrait_layout_draw_probe']
    f=PortraitFixture(raw,packet,meta);f.native_call_timeout_us=0;checks=[]
    choose=CODE+metadata['symbols']['z7_portrait_layout_probe'];reset=CODE+metadata['symbols']['z7_portrait_layout_reset_probe']
    def check(name,good):checks.append(dict(name=name,passed=bool(good)));assert good,name
    def state(v=None):
        if v is not None:f.u.mem_write(STATE,struct.pack('<I',v))
        return int.from_bytes(f.u.mem_read(STATE,4),'little')
    def message(command,box):
        x,y,w,h=box;s=[0]*WORDS[command];s[:4]=[x,480-y-h,w,h]
        f.u.mem_write(PAYLOAD,struct.pack('<%dI'%len(s),*s))
        f.u.mem_write(MESSAGE,struct.pack('<7I',1,2,3,0x1042eadf,0x42010000+command,PAYLOAD,123))
    cases=[('filled-backdrop',0x13,(0,280,720,146),True,True),('clear-backdrop',0x17,(0,280,720,146),True,True),
           ('other-backdrop',0x16,(0,280,720,146),False,False),('title',0x17,(88,228,544,44),True,True),
           ('tile',0x17,(10,290,100,53),False,False),('top-edge',0x17,(0,278,120,2),False,False),
           ('dial-content',0x17,(199,100,201,111),False,True),('footer',0x17,(300,430,80,24),False,False),
           ('full-screen',0x17,(0,0,720,480),False,False)]
    for name,command,box,grid_trigger,dial_trigger in cases:
        message(command,box)
        before=(bytes(f.u.mem_read(MESSAGE,28)),bytes(f.u.mem_read(PAYLOAD,32)))
        for page in (1,2,3,4):
            for sampled in (0,1,2,3,4,0xffffffff):
                state(0);f.events.clear();f.rendered.clear()
                trigger=grid_trigger if page==1 else dial_trigger if page==2 else page==3
                expected=(sampled if sampled in (1,2) else 3) if trigger else 0
                got=f.call(choose,STATE,MESSAGE,page,sampled)
                check(f'trigger-{name}-page{page}-sample{sampled}',got==expected and state()==expected and not f.events and not f.rendered and
                      before==(bytes(f.u.mem_read(MESSAGE,28)),bytes(f.u.mem_read(PAYLOAD,32))))
    message(0x17,(10,290,100,53))
    for cached in (1,2,3):
        for page in (1,2,3,4):
            for sampled in (0,1,2,3,4,0xffffffff):
                state(cached);check(f'held-{cached}-page{page}-sample{sampled}',f.call(choose,STATE,0,page,sampled)==cached and state()==cached)
    for cached in (0,1,2,3,9):
        for page in (0,5,0xffffffff):
            state(cached);check(f'observed-exit-page{page}-state{cached}',f.call(choose,STATE,MESSAGE,page,1)==0 and state()==0)
    for page in (1,2,3,4):
        state(99);check(f'invalid-owned-state-reject-page{page}',f.call(choose,STATE,MESSAGE,page,1)==0 and state()==99)
    state(2);f.call(reset,STATE);check('explicit-reset-releases-layout',state()==0)
    check('null-state-rejected',f.call(choose,0,MESSAGE,1,1)==0)
    for page in (1,2,3):
        state(0);got=f.call(choose,STATE,0,page,2)
        check(f'missing-message-page{page}',got==(2 if page==3 else 0) and state()==(2 if page==3 else 0))
    return dict(passed=True,checks=checks,compiled_trigger_parser_orientation_latch_and_reset_execute=True,
                message_and_owned_state_inputs_supplied=True,native_page_lifecycle_band_cleanup_sensor_schedule_or_pixels_proven=False,camera_card_access=False)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    raw=a.stock_main.read_bytes();assert hashlib.sha256(raw).hexdigest()==STOCK_SHA
    packet,metadata=build(ROOT/'z7-native-modules/examples/portrait_layout_probe.c',zig=ZIG)
    again,other=build(ROOT/'z7-native-modules/examples/portrait_layout_probe.c',zig=ZIG);assert packet==again and metadata==other
    result=audit(raw,packet,metadata)
    names=('tools/audit_z7_portrait_layout.py','tools/audit_z7_portrait_draw.py','tools/audit_splash_image.py','tools/build_z7_module.py',
           'z7-native-modules/sdk/module.h','z7-native-modules/sdk/module.ld','z7-native-modules/plugins/portrait_layout.h','z7-native-modules/plugins/portrait_page_message.h',
           'z7-native-modules/plugins/portrait_grid_message.h','z7-native-modules/plugins/portrait_grid.h','z7-native-modules/plugins/portrait_footer.h',
           'z7-native-modules/plugins/portrait_geometry.h','z7-native-modules/plugins/portrait_draw.h','z7-native-modules/examples/portrait_layout_probe.c')
    result.update(probe_sha256=hashlib.sha256(packet).hexdigest(),reproducible_probe=True,probe_bytes=len(packet),source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(packet)
    (out/'probe.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),probe_bytes=len(packet))))

if __name__=='__main__':main()
