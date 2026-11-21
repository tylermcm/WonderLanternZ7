"""Execute original image19/1A renderers behind compiled portrait strip adapter.

SPDX-License-Identifier: MIT. Native geometry, float/trig helpers, clear branches,
dispatch and completion execute. GPU state/creation/draw, target shape, sampler
and cacheability services supplied. No rasterization, real buffers, allocation
capacity/lifetime or native task scheduling/pixels are proved.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_SP
from audit_splash_image import MEM,STOCK_SHA
from audit_z7_portrait_draw import PortraitFixture,CODE,MESSAGE,PAYLOAD,WORDS,reference_destination
from audit_z7_portrait_page_message import scaled,strip19_reference
from audit_z7_portrait_grid_message import packpoint
from build_z7_module import build
from build_z7_module_host import ROOT,ZIG

class NativeImageFixture(PortraitFixture):
    def __init__(self,raw,packet,metadata):
        meta=dict(metadata,symbols=dict(metadata['symbols']));meta['symbols']['z7_portrait_draw_probe']=metadata['symbols']['z7_portrait_page_message_probe']
        super().__init__(raw,packet,meta);self.native_call_timeout_us=0
        self.gpu={};self.api=[];self.native_payloads=[]
    def hook(self,u,a,size,context):
        regs=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
        if a in (0x104303e6,0x1042f894):
            self.events.append('render');self.native_payloads.append((a,bytes(u.mem_read(regs[0],68 if a==0x104303e6 else 88))));return
        if a in (0x104500c6,0x104500e2,0x1045011a):
            values=[struct.unpack('<f',struct.pack('<I',v))[0] for v in regs[:1 if a==0x1045011a else 2]]
            self.api.append((a,values));self.ret(0);return
        if a==0x1041477c:u.mem_write(regs[1],struct.pack('<2h',720,480));self.ret(0);return
        if a==0x10450096:u.mem_write(regs[0],struct.pack('<9f',1,0,0,0,1,0,0,0,1));self.ret(0);return
        if a==0x104501f8:
            assert 0<regs[1]<=8;u.mem_write(regs[2],bytes(regs[1]*4));self.ret(0);return
        if a==0x104501c4:self.ret(self.gpu.get(regs[0],0));return
        if a==0x1045014e:self.gpu[regs[0]]=regs[1];self.ret(0);return
        if a in (0x104514e8,0x10451630,0x10450a7c,0x10450aca):self.ret(22);return
        if a in (0x1045004e,0x1045006a,0x1045007e,0x1045016a,0x1045018a,0x104502da,0x1045037e,0x10450a96,0x10450aae,0x10450b60,0x1042ecb2):self.ret(0);return
        if a in (0x10450c86,0x10451338,0x1045081e):
            self.api.append((a,regs));self.ret(0);return
        if a==0x101e3e2a:self.ret(0);return
        super().hook(u,a,size,context)
    def prepare(self,command,angle=0,mode=0,clear=0,aux=0,sw=160,sh=80,box=(199,100,201,111)):
        x,y,w,h=box
        if mode:w,h=sw,sh
        s=[0]*WORDS[command];s[0]=mode;s[1]=0;s[2]=MEM+0x100000;s[4]=0;s[5]=packpoint(sw,sh)
        s[6]=packpoint(x,y);s[7]=packpoint(x+w,y+h);s[11]=1
        if command==0x1c:s[6:10]=[x<<16,y<<16,(x+w)<<16,(y+h)<<16];s[10]=1;s[11]=0
        else:s[9]=clear;s[10]=0x12345678;s[14]=aux;s[15]=angle
        data=struct.pack('<%dI'%len(s),*(v&0xffffffff for v in s));self.u.mem_write(PAYLOAD,data)
        msg=struct.pack('<7I',1,2,3,0x1042eadf,0x42010000+command,PAYLOAD,123);self.u.mem_write(MESSAGE,msg)
        self.events.clear();self.api.clear();self.native_payloads.clear();return msg,data,(x,y,w,h)

def audit(raw,packet,metadata):
    f=NativeImageFixture(raw,packet,metadata);checks=[];cases=0
    def check(name,good):checks.append(dict(name=name,passed=bool(good)));assert good,(name,f.api)
    for command in (0x19,0x1a):
        for clear in (0,1):
            msg,data,_=f.prepare(command,angle=90,clear=clear)
            f.call(0x10372391,MESSAGE)
            clears=[v for a,v in f.api if a==0x1045081e]
            check(f'original-command{command}-clear-field9-{clear}',len(clears)==(int(clear) if command==0x19 else 4*int(clear)) and
                  f.events==['render',('ack',0x42010062,0),'event'] and bytes(f.u.mem_read(PAYLOAD,len(data)))==data)
    for command in (0x19,0x1a,0x1c):
        for orientation in (1,2):
            for angle in ((0,) if command==0x1c else (0,90,180,270,360)):
                for mode in (0,1):
                    msg,data,box=f.prepare(command,angle,mode,1)
                    got=f.call(f.operation,MESSAGE,2,orientation)
                    final_angle=((90 if orientation==2 else 270)+angle)%360
                    physical=reference_destination(scaled(box,2),orientation)
                    if command==0x19:physical=strip19_reference(physical,160,80,final_angle)
                    _,out=f.native_payloads[0]
                    x,y,x2,y2=struct.unpack_from('<4h',out,24)
                    rotations=[v[0] for a,v in f.api if a==0x1045011a]
                    draws=[v for a,v in f.api if a in (0x10450c86,0x10451338)]
                    clears=[v for a,v in f.api if a==0x1045081e]
                    check(f'strip-command{command}-orientation{orientation}-angle{angle}-mode{mode}',
                          got==1 and len(f.native_payloads)==1 and (x,y,x2-x,y2-y)==physical and struct.unpack_from('<I',out,36)[0]==0 and
                          not clears and len(draws)==1 and rotations==[final_angle if command!=0x19 and final_angle in (90,270) else -final_angle] and
                          f.events==['render',('deferred',0x42010062,0),('ack',0x42010062,0),'event'] and
                          bytes(f.u.mem_read(PAYLOAD,len(data)))==data and bytes(f.u.mem_read(MESSAGE,24))==msg[:24] and int.from_bytes(f.u.mem_read(MESSAGE+24,4),'little')==0)
                    order=[a for a,_ in f.api]
                    draw_api=0x10450c86 if command==0x19 else 0x10451338
                    expected_order=[0x104500c6,0x1045011a,0x104500e2] if command!=0x19 and final_angle in (90,270) else [0x104500e2,0x104500c6,0x1045011a]
                    check(f'native-geometry-order-{command}-{orientation}-{angle}-{mode}',order==expected_order+[draw_api])
                    cases+=1
    for args in (dict(command=0x19,aux=1),dict(command=0x19,sw=0),dict(command=0x19,sh=0),dict(command=0x19,sw=720,sh=1),dict(command=0x1a,angle=1)):
        msg,data,_=f.prepare(**args)
        got=f.call(f.operation,MESSAGE,2,1)
        check('unsupported-strip-consumes-once-'+str(args),got==1 and not f.api and not f.native_payloads and
              f.events==[('ack',0x42010062,0),'event'] and bytes(f.u.mem_read(PAYLOAD,len(data)))==data and bytes(f.u.mem_read(MESSAGE,24))==msg[:24])
    return dict(passed=True,checks=checks,native_renderer_cases=cases,original_image19_and_image1a_geometry_float_trig_clear_and_completion_execute=True,
                gpu_state_image_creation_draw_target_shape_sampler_cacheability_and_page_admission_supplied=True,
                exact_ideal_pixel_phase_gpu_rasterization_buffer_lifetime_or_task_schedule_proven=False,camera_card_access=False)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    raw=a.stock_main.read_bytes();assert hashlib.sha256(raw).hexdigest()==STOCK_SHA
    packet,metadata=build(ROOT/'z7-native-modules/examples/portrait_page_message_probe.c',zig=ZIG)
    again,other=build(ROOT/'z7-native-modules/examples/portrait_page_message_probe.c',zig=ZIG);assert packet==again and metadata==other
    result=audit(raw,packet,metadata)
    names=('tools/audit_z7_portrait_native_image.py','tools/audit_z7_portrait_page_message.py','tools/audit_z7_portrait_draw.py','tools/audit_z7_portrait_grid_message.py','tools/audit_splash_image.py','tools/build_z7_module.py',
           'z7-native-modules/sdk/module.h','z7-native-modules/sdk/module.ld','z7-native-modules/plugins/portrait_page_message.h',
           'z7-native-modules/plugins/portrait_grid_message.h','z7-native-modules/plugins/portrait_footer.h','z7-native-modules/plugins/portrait_grid.h','z7-native-modules/plugins/portrait_geometry.h','z7-native-modules/plugins/portrait_draw.h','z7-native-modules/examples/portrait_page_message_probe.c')
    result.update(probe_sha256=hashlib.sha256(packet).hexdigest(),reproducible_probe=True,probe_bytes=len(packet),source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(packet)
    (out/'probe.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),native_renderer_cases=result['native_renderer_cases'],probe_bytes=len(packet))))

if __name__=='__main__':main()
