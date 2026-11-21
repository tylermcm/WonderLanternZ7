"""Original Z7 message geometry extraction and native GRID reflow dispatch.

SPDX-License-Identifier: MIT. Native dispatch/normalizers/completion execute;
backend rendering/events and page admission supplied. No installed callback,
complete footer/dial/text/input policy, task scheduling or pixels are proved.
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

def packpoint(x,y):return (x&65535)|((y&65535)<<16)
def tile(i,x=10,y=10,w=100,h=53):return (i%4*120+x,440+i//4*73+y,w,h)

def audit(raw,packet,metadata):
    meta=dict(metadata,symbols=dict(metadata['symbols']));meta['symbols']['z7_portrait_draw_probe']=metadata['symbols']['z7_portrait_grid_message_probe']
    f=PortraitFixture(raw,packet,meta);f.native_call_timeout_us=0;checks=[];draws=0
    extract=CODE+metadata['symbols']['z7_portrait_message_source_probe']
    def check(name,good):checks.append(dict(name=name,passed=bool(good)));assert good,name
    def source(command,box,mode=0,angle=0):
        x,y,w,h=box;s=[0]*WORDS[command]
        if command in (0x13,0x16,0x17):s[:4]=[x,480-y-h,w,h]
        else:
            s[0]=mode;s[4]=packpoint(-5,-7);s[5]=packpoint(w-5,h-7)
            if command==0x1c:
                s[6:10]=[(x<<16)|32768,(y<<16)|32768,((x+(17 if mode else w))<<16)|32768,((y+(19 if mode else h))<<16)|32768]
            else:
                s[6]=packpoint(x,y);s[7]=packpoint(x+(17 if mode else w),y+(19 if mode else h));s[15]=0xabcd0000|angle;s[16]=0x12345678
        return s
    def prepare(command,s):
        data=struct.pack('<%dI'%len(s),*(v&0xffffffff for v in s));f.u.mem_write(PAYLOAD,data)
        msg=struct.pack('<7I',1,2,3,0x1042eadf,0x42010000+command,PAYLOAD,0xa5a5a5a5);f.u.mem_write(MESSAGE,msg)
        f.events.clear();f.rendered.clear();return msg,data
    def draw(name,command,box,expected,orientation,mode=0,angle=0):
        nonlocal draws
        s=source(command,box,mode,angle);msg,data=prepare(command,s)
        f.u.mem_write(BOX,b'\x6b'*36)
        got=f.call(extract,MESSAGE,BOX)
        decoded=struct.unpack('<4i3I2i',bytes(f.u.mem_read(BOX,36)))
        image=command>=0x19
        check(name+'-extract',got==1 and decoded==tuple(box)+(command,int(image),0 if command==0x1c else angle,box[2] if image else 0,box[3] if image else 0))
        got=f.call(f.operation,MESSAGE,orientation)
        actual=[]
        for backend,dataout in f.rendered:
            if image:
                start,end=struct.unpack_from('<2I',dataout,24);x,y=start&65535,start>>16
                actual.append((x,y,(end&65535)-x,(end>>16)-y))
                check(name+'-angle'+str(len(actual)),struct.unpack_from('<H',dataout,60)[0]==((90 if orientation==2 else 270)+angle)%360)
            else:
                x,y,w,h=struct.unpack_from('<4i',dataout);actual.append((x,480-y-h,w,h))
            check(name+'-backend'+str(len(actual)),backend==BACKENDS[0x1a if command==0x1c else command])
        check(name,got==1 and actual==[reference_destination(b,orientation) for b in expected] and
              bytes(f.u.mem_read(PAYLOAD,len(data)))==data and bytes(f.u.mem_read(MESSAGE,24))==msg[:24] and
              int.from_bytes(f.u.mem_read(MESSAGE+24,4),'little')==0 and
              f.events==sum((['render',('deferred',0x42010062,0)] for _ in expected),[])+[('ack',0x42010062,0),'event'])
        draws+=len(expected)
    for orientation in (1,2):
        for command in WORDS:
            for mode in ((0,1) if command>=0x19 else (0,)):
                for i in range(12):
                    row,col=divmod(i,6);box=(col*120+10,280+row*73+10,100,53)
                    draw(f'tile-{orientation}-{command}-{mode}-{i}',command,box,[tile(i)],orientation,mode,360 if command==0x1a else 0)
                draw(f'title-image-or-rect-{orientation}-{command}-{mode}',command,(120,208,100,40),[(0,370,100,40)],orientation,mode)
        for command in (0x13,0x16,0x17):
            draw(f'split-vertical-{orientation}-{command}',command,(480,280,1,73),[tile(3,119,0,1,73),tile(4,0,0,1,73)],orientation)
            draw(f'split-horizontal-{orientation}-{command}',command,(0,353,120,1),[tile(0,0,72,120,1),tile(6,0,0,120,1)],orientation)
        for command in (0x13,0x17):
            draw(f'backdrop-{orientation}-{command}',command,(0,280,720,146),[(0,440,480,219)],orientation)
        title=(88,228,544,44)
        inverse=(228,88,44,282) if orientation==1 else (208,88,44,282)
        draw(f'title-clear-{orientation}',0x17,title,[(0,370,480,70),inverse],orientation)
    # Rejection must neither change source/message/output nor render/acknowledge.
    invalid=[]
    for command in WORDS:
        invalid.append((command,source(command,(0,0,720,480)),1,None))
    for command in (0x19,0x1a):
        for angle in (1,90,180,270,361):invalid.append((command,source(command,(10,290,100,53),angle=angle),1,None))
        for mode in (2,255):
            s=source(command,(10,290,100,53));s[0]=mode;invalid.append((command,s,1,None))
    for command in (0x13,0x16,0x17):
        for index,value in ((0,0xffffffff),(1,0x80000000),(2,0),(2,0x7fffffff),(3,0xffffffff)):
            s=source(command,(10,290,100,53));s[index]=value;invalid.append((command,s,1,None))
    for p in (0,0xa1800001,0xaffffffc,0xb0000000):invalid.append((0x17,source(0x17,(10,290,100,53)),1,(MESSAGE+20,p)))
    invalid.append((0x17,source(0x17,(10,290,100,53)),1,(MESSAGE+12,0x1042eadc)))
    invalid.append((0x17,source(0x17,(10,290,100,53)),1,(MESSAGE+16,0x42010018)))
    for orientation in (0,3,4,0xffffffff):invalid.append((0x17,source(0x17,(10,290,100,53)),orientation,None))
    for n,(command,s,orientation,patch) in enumerate(invalid):
        _,data=prepare(command,s)
        if patch:f.u.mem_write(patch[0],struct.pack('<I',patch[1]))
        msg=bytes(f.u.mem_read(MESSAGE,28));f.u.mem_write(BOX,b'\x6b'*36)
        parsed=f.call(extract,MESSAGE,BOX)
        if not parsed:check(f'rejected-extraction-output{n}',bytes(f.u.mem_read(BOX,36))==b'\x6b'*36)
        got=f.call(f.operation,MESSAGE,orientation)
        check(f'rejected-message{n}',got==0 and not f.events and not f.rendered and bytes(f.u.mem_read(MESSAGE,28))==msg and bytes(f.u.mem_read(PAYLOAD,len(data)))==data)
    return dict(passed=True,checks=checks,native_draws=draws,original_dispatch_normalization_completion_and_message_extraction_execute=True,
                backend_rendering_kernel_events_and_page_admission_supplied=True,
                installed_callback_footer_dial_text_input_task_schedule_or_pixels_proven=False,camera_card_access=False)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    raw=a.stock_main.read_bytes();assert hashlib.sha256(raw).hexdigest()==STOCK_SHA
    packet,metadata=build(ROOT/'z7-native-modules/examples/portrait_grid_message_probe.c',zig=ZIG)
    again,other=build(ROOT/'z7-native-modules/examples/portrait_grid_message_probe.c',zig=ZIG);assert packet==again and metadata==other
    result=audit(raw,packet,metadata)
    names=('tools/audit_z7_portrait_grid_message.py','tools/audit_z7_portrait_draw.py','tools/audit_splash_image.py','tools/build_z7_module.py',
           'z7-native-modules/sdk/module.h','z7-native-modules/sdk/module.ld','z7-native-modules/plugins/portrait_grid.h',
           'z7-native-modules/plugins/portrait_draw.h','z7-native-modules/plugins/portrait_geometry.h',
           'z7-native-modules/plugins/portrait_grid_message.h','z7-native-modules/plugins/portrait_footer.h','z7-native-modules/examples/portrait_grid_message_probe.c')
    result.update(probe_sha256=hashlib.sha256(packet).hexdigest(),reproducible_probe=True,probe_bytes=len(packet),source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(packet)
    (out/'probe.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),native_draws=result['native_draws'],probe_bytes=len(packet))))

if __name__=='__main__':main()
