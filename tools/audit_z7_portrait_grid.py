"""Compiled 6x2-to-4x3 grid reflow and batched original-Z7 drawing.

SPDX-License-Identifier: MIT. Actual dispatcher/normalizers/completion execute;
backend rendering and kernel event signaling supplied. Caller supplies admitted
page and stock geometry. No persistent hook, reflowed text, input or pixels.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from audit_z7_portrait_draw import PortraitFixture,CODE,BOX,MESSAGE,PAYLOAD,BACKENDS,WORDS,reference_destination
from audit_splash_image import STOCK_SHA
from build_z7_module import build
from build_z7_module_host import ROOT,ZIG

def tile(index,x,y,w,h):return (index%4*120+x,440+index//4*73+y,w,h)

def audit(raw,packet,metadata):
    fixture_metadata=dict(metadata,symbols=dict(metadata['symbols']))
    fixture_metadata['symbols']['z7_portrait_draw_probe']=metadata['symbols']['z7_portrait_grid_probe']
    f=PortraitFixture(raw,packet,fixture_metadata);f.native_call_timeout_us=0;checks=[];draws=0
    def check(name,good):
        checks.append(dict(name=name,passed=bool(good)));assert good,name
    def draw(name,stock,boxes,orientation,edge=0,command=0x17,batch=False):
        nonlocal draws
        source=[0]*WORDS[command]
        if command in (0x13,0x16,0x17):source[:4]=[10,20,30,40]
        else:
            source[4]=0;source[5]=30|(40<<16);source[6]=10|(20<<16);source[7]=40|(60<<16)
            if command==0x1c:source[6:10]=[10<<16,20<<16,40<<16,60<<16]
        before=struct.pack('<%dI'%len(source),*source);f.u.mem_write(PAYLOAD,before)
        msg=struct.pack('<7I',1,2,3,0x1042eadf,0x42010000+command,PAYLOAD,0xa5a5a5a5);f.u.mem_write(MESSAGE,msg)
        f.events.clear();f.rendered.clear()
        if batch:
            f.u.mem_write(BOX,b''.join(struct.pack('<4i',*b) for b in boxes))
            got=f.call(CODE+metadata['symbols']['z7_portrait_batch_probe'],MESSAGE,BOX,len(boxes),orientation)
        else:
            f.u.mem_write(BOX,struct.pack('<4i',*stock));got=f.call(f.operation,MESSAGE,BOX,orientation,edge)
        expected=[reference_destination(b,orientation) for b in boxes]
        actual=[]
        for backend,data in f.rendered:
            if command in (0x13,0x16,0x17):
                x,y,w,h=struct.unpack_from('<4i',data);actual.append((x,480-y-h,w,h))
            else:
                start,end=struct.unpack_from('<2I',data,24);x,y=start&65535,start>>16
                actual.append((x,y,(end&65535)-x,(end>>16)-y))
            check(name+'-backend'+str(len(actual)),backend==BACKENDS[0x1a if command==0x1c else command])
        check(name,got==1 and actual==expected and bytes(f.u.mem_read(PAYLOAD,len(before)))==before and
              bytes(f.u.mem_read(MESSAGE,24))==msg[:24] and int.from_bytes(f.u.mem_read(MESSAGE+24,4),'little')==0 and
              f.events==sum((['render',('deferred',0x42010062,0)] for _ in boxes),[])+[('ack',0x42010062,0),'event'])
        draws+=len(boxes)
    for orientation in (1,2):
        for command in (0x13,0x16,0x17):
            for index in range(12):
                row,col=divmod(index,6);stock=(col*120+10,280+row*73+10,100,53)
                draw(f'tile-{orientation}-{command}-{index}',stock,[tile(index,10,10,100,53)],orientation,command=command)
            for row in (0,1):
                for col in range(7):
                    stock=(col*120,280+row*73,1,73);right=row*6+col;boxes=[]
                    if col:boxes.append(tile(right-1,119,0,1,73))
                    if col<6 and (not col or right%4==0):boxes.append(tile(right,0,0,1,73))
                    draw(f'vertical-edge-{orientation}-{command}-{row}-{col}',stock,boxes,orientation,1,command)
            for row in range(3):
                for col in range(6):
                    stock=(col*120,280+row*73,120,1);boxes=[]
                    if row:boxes.append(tile((row-1)*6+col,0,72,120,1))
                    if row<2:boxes.append(tile(row*6+col,0,0,120,1))
                    draw(f'horizontal-edge-{orientation}-{command}-{row}-{col}',stock,boxes,orientation,1,command)
        for command in WORDS:
            draw(f'batched-command-{orientation}-{command}',None,[(10,440,100,2),(130,513,100,2)],orientation,command=command,batch=True)
    geometry=CODE+metadata['symbols']['z7_portrait_grid_geometry_probe']
    for index in range(12):
        row,col=divmod(index,6)
        for w in (1,100,120,121,132,133):
            for image in (0,1):
                stock=(col*120,280+row*73,w,40);f.u.mem_write(BOX,struct.pack('<4i',*stock))
                got=f.call(geometry,BOX,image);out=struct.unpack('<4i',bytes(f.u.mem_read(BOX,16)))
                valid=w<=120+(12 if image else 0)
                fw=min(w,120);fh=max(1,40*120//w) if w>120 else 40
                centre=stock[0]+w//2;selected=min(5,centre//120)
                expected=tile(row*6+selected,max(0,min(120-fw,centre-selected*120-fw//2)),max(0,min(73-fh,20-fh//2)),fw,fh)
                check(f'geometry-{index}-{w}-{image}',got==valid and out==(expected if valid else stock))
    for count,orientation,boxes in [(0,1,[(0,0,1,1)]),(3,1,[(0,0,1,1)]*3),(2,1,[(0,0,1,1),(480,0,1,1)]),(2,0,[(0,0,1,1)]*2)]:
        f.u.mem_write(BOX,b''.join(struct.pack('<4i',*b) for b in boxes));f.u.mem_write(MESSAGE,struct.pack('<7I',1,2,3,0x1042eadf,0x42010017,PAYLOAD,123))
        before=bytes(f.u.mem_read(MESSAGE,28));f.events.clear();f.rendered.clear()
        got=f.call(CODE+metadata['symbols']['z7_portrait_batch_probe'],MESSAGE,BOX,count,orientation)
        check(f'invalid-batch-{count}-{orientation}',got==0 and not f.events and not f.rendered and bytes(f.u.mem_read(MESSAGE,28))==before)
    return dict(passed=True,checks=checks,native_draws=draws,original_dispatch_normalization_and_completion_execute=True,
                backend_rendering_kernel_event_page_admission_and_stock_geometry_supplied=True,
                graphics_hook_text_input_full_page_policy_or_pixels_proven=False,camera_card_access=False)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    raw=a.stock_main.read_bytes();assert hashlib.sha256(raw).hexdigest()==STOCK_SHA
    packet,metadata=build(ROOT/'z7-native-modules/examples/portrait_grid_probe.c',zig=ZIG)
    again,other=build(ROOT/'z7-native-modules/examples/portrait_grid_probe.c',zig=ZIG);assert packet==again and metadata==other
    result=audit(raw,packet,metadata)
    names=('tools/audit_z7_portrait_grid.py','tools/audit_z7_portrait_draw.py','tools/audit_splash_image.py','tools/build_z7_module.py',
           'z7-native-modules/sdk/module.h','z7-native-modules/sdk/module.ld','z7-native-modules/plugins/portrait_grid.h',
           'z7-native-modules/plugins/portrait_draw.h','z7-native-modules/plugins/portrait_geometry.h','z7-native-modules/examples/portrait_grid_probe.c')
    result.update(probe_sha256=hashlib.sha256(packet).hexdigest(),reproducible_probe=True,probe_bytes=len(packet),source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(packet)
    (out/'probe.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),native_draws=result['native_draws'],probe_bytes=len(packet))))

if __name__=='__main__':main()
