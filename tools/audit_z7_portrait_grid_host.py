"""Loaded API84 module reflows original Z7 grid messages through resident bridge.

SPDX-License-Identifier: MIT. Loader, SDK registration, worker bridge, original
app registry/getters, target/orientation queries and dispatch/completion execute.
Filesystem/kernel/allocator, UI/registry/orientation state and backend renderer
are supplied. No complete boot, real tasks, pixels, camera/card or flash.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1
from audit_z7_module_host import HostFixture
from audit_z7_information_native import InformationFixture
from audit_z7_portrait_draw import BACKENDS,WORDS,reference_destination
from audit_z7_portrait_grid_message import packpoint
from audit_z7_portrait_page_message import strip19_reference
from build_z7_module import build
from build_z7_module_host import ROOT,STATE,ZIG
from audit_splash_image import MEM
SLOT,MESSAGE,PAYLOAD,TABLE=0xa1d75d60,0xa1d75000,0xa1d75100,0xa1d75200

class GridHostFixture(HostFixture):
    def __init__(self,raw,report,packet,metadata):
        super().__init__(raw,report,packet);self.metadata=metadata;self.native_call_timeout_us=0
        self.u.mem_map(0xa1d75000,0x1000);self.u.mem_map(0xa2010000,0x20000);self.u.mem_map(0xa1d40000,0x10000)
        self.stop_at=None;self.rendered=[];self.acks=[];self.flags=[];self.mutation=None;self.targets=0;self.orientations=0
        InformationFixture.prefix(self,0x1030cf74,0x1030d00a,MEM+0x60001)
        self.write(SLOT,0x10372391)
    def write(self,p,v):self.u.mem_write(p,struct.pack('<I',v))
    def read(self,p):return int.from_bytes(self.u.mem_read(p,4),'little')
    def variable(self,name):return self.words()[12]+self.metadata['symbols']['z7_portrait_grid_'+name]
    def setup(self,orientation=1):
        self.u.mem_write(0xa1829af4,b'\3');self.write(0xa20207bc+12,0xa1829970)
        self.u.mem_write(0xa18298b8,b'\3\0');self.u.mem_write(0xa201d4d0,b'\0')
        self.u.mem_write(0xa182ed2c,b'\4');self.u.mem_write(0xa183de04,b'\4')
        self.write(0xa1821394,1);self.write(0xa180ad84,12);self.write(0xa180ad88,TABLE)
        records=bytearray(660)
        for i in range(33):records[i*20+4]=255
        struct.pack_into('<IBxHHHII',records,40,0xb0000000,12,720,480,0,0,0)
        self.u.mem_write(TABLE,bytes(records));self.write(0xa1809074,0);self.u.mem_write(0xa1d49784,bytes([{0:1,1:3,2:4,3:2,4:0}[orientation]]))
        self.mutation=None
    def hook(self,u,address,size,context):
        if address==self.stop_at:u.emu_stop();return
        if address==0x10414756:self.targets+=1
        if address==0x101b331a:self.orientations+=1
        if address==0x1041477a and self.mutation:
            p,data=self.mutation;u.mem_write(p,data);self.mutation=None
        if address in BACKENDS.values():
            # This integration fixture uses rect17 and image19/1A/1C backends.
            length=28 if address==BACKENDS[0x17] else 88 if address==BACKENDS[0x1a] else 68
            self.rendered.append((address,bytes(u.mem_read(u.reg_read(UC_ARM_REG_R0),length))));self.ret(0);return
        if address==0x1042eade:self.acks.append((u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R1)))
        if address==0x10170be8:
            self.flags.append((u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R1)));self.ret(0);return
        super().hook(u,address,size,context)
    def dispatch(self,command=0x17,box=(10,290,100,53),clear=0):
        x,y,w,h=box;s=[0]*WORDS[command]
        if command==0x17:s[:4]=[x,480-y-h,w,h]
        else:
            s[4]=0;s[5]=packpoint(w,h);s[6]=packpoint(x,y);s[7]=packpoint(x+w,y+h)
            if command==0x1c:s[6:10]=[x<<16,y<<16,(x+w)<<16,(y+h)<<16]
            else:s[9]=clear
        data=struct.pack('<%dI'%len(s),*s);self.u.mem_write(PAYLOAD,data)
        msg=struct.pack('<7I',1,2,3,0x1042eadf,0x42010000+command,PAYLOAD,123);self.u.mem_write(MESSAGE,msg)
        self.rendered.clear();self.acks.clear();self.flags.clear();self.targets=0;self.orientations=0
        before=self.read(self.variable('handled'))
        self.call(self.report['symbols']['z7_graphics_dispatch_bridge'],MESSAGE)
        assert bytes(self.u.mem_read(PAYLOAD,len(data)))==data and bytes(self.u.mem_read(MESSAGE,24))==msg[:24]
        assert self.read(MESSAGE+24)==0 and self.acks==[(0x42010062,0)] and self.flags==[(0xa1d75e3c,1)]
        return self.read(self.variable('handled'))-before

def audit(raw,host,packet,metadata,old_raw,old_host):
    f=GridHostFixture(raw,host,packet,metadata);checks=[]
    def check(name,good):checks.append(dict(name=name,passed=bool(good)));assert good,name
    result=f.call(host['symbols']['z7_module_load_once'],STATE);f.setword(40,result)
    check('loaded-module-registers-staged-graphics-without-touching-native-slot',result==8 and f.read(SLOT)==0x10372391 and f.read(STATE+364)==1)
    f.call(host['symbols']['z7_module_worker_tick']);check('worker-binds-resident-host-bridge',f.read(SLOT)==host['symbols']['z7_graphics_dispatch_bridge'])
    for orientation in (1,2):
        for command in (0x17,0x19,0x1a,0x1c):
            f.setup(orientation);handled=f.dispatch(command)
            expected=reference_destination((10,450,100,53),orientation)
            backend,data=f.rendered[0]
            if command==0x17:
                x,y,w,h=struct.unpack_from('<4i',data);actual=(x,480-y-h,w,h)
            else:
                start,end=struct.unpack_from('<2I',data,24);x,y=start&65535,start>>16;actual=(x,y,(end&65535)-x,(end>>16)-y)
            check(f'loaded-native-message-{orientation}-{command}',handled==1 and len(f.rendered)==1 and actual==expected and f.targets==2 and f.orientations==1)
        f.setup(orientation);handled=f.dispatch(box=(480,280,1,73))
        check(f'loaded-split-border-completes-once-{orientation}',handled==1 and len(f.rendered)==2)
        for mode,page,commands in ((2,2,(0x17,0x19,0x1a,0x1c)),(1,3,(0x17,0x19,0x1a,0x1c))):
            for command in commands:
                f.setup(orientation);f.u.mem_write(0xa18298b8,bytes([mode,0]))
                handled=f.dispatch(command,box=(199,100,201,111))
                left=199*43691//65536;right=400*43691//65536
                top=100 if page==3 else 100*43691//65536
                bottom=211 if page==3 else 211*43691//65536
                expected=reference_destination((left,top+(235 if page==3 else 254),right-left,bottom-top),orientation)
                if page==2 and command==0x19:expected=strip19_reference(expected,201,111,90 if orientation==2 else 270)
                _,data=f.rendered[0]
                if command==0x17:
                    x,y,w,h=struct.unpack_from('<4i',data);actual=(x,480-y-h,w,h)
                else:
                    start,end=struct.unpack_from('<2I',data,24);x,y=start&65535,start>>16;actual=(x,y,(end&65535)-x,(end>>16)-y)
                check(f'loaded-page{page}-{orientation}-{command}',handled==1 and len(f.rendered)==1 and actual==expected)
        for mode in (3,2):
            for command in (0x17,0x19,0x1a,0x1c):
                f.setup(orientation);f.u.mem_write(0xa18298b8,bytes([mode,0]))
                handled=f.dispatch(command,box=(300,430,80,24),clear=1)
                expected=reference_destination((51,671,70,21),orientation)
                if command==0x19:expected=strip19_reference(expected,80,24,90 if orientation==2 else 270)
                _,data=f.rendered[0]
                if command==0x17:
                    x,y,w,h=struct.unpack_from('<4i',data);actual=(x,480-y-h,w,h)
                else:
                    x,y,x2,y2=struct.unpack_from('<4h',data,24);actual=(x,y,x2-x,y2-y)
                check(f'loaded-footer-{mode}-{orientation}-{command}',handled==1 and len(f.rendered)==1 and actual==expected)
            f.setup(orientation);f.u.mem_write(0xa18298b8,bytes([mode,0]))
            check(f'loaded-left-footer-image-consumed-{mode}-{orientation}',f.dispatch(0x19,box=(200,430,80,24))==1 and not f.rendered)
    for p,data in ((0xa1829af4,b'\0'),(0xa20207bc+12,bytes(4)),(0xa18298b8,b'\4'),(0xa201d4d0,b'\1'),
                   (0xa1821394,struct.pack('<I',2)),(0xa180ad84,b'\xff'),(TABLE+40,bytes(4)),(TABLE+46,struct.pack('<H',640)),
                   (0xa182ed2c,b'\1'),(0xa182ed2c,b'\2'),(0xa182ed2c,b'\3'),(0xa183de04,b'\1'),(0xa183de04,b'\2'),(0xa183de04,b'\3')):
        f.setup();f.u.mem_write(p,data)
        check(f'native-context-stock-fallback-{p}-{data.hex()}',f.dispatch()==0 and len(f.rendered)==1 and struct.unpack_from('<4i',f.rendered[0][1])==(10,137,100,53))
    for orientation in (0,3,4):
        f.setup(orientation);check(f'nonportrait-or-unknown-orientation{orientation}',f.dispatch()==0 and len(f.rendered)==1)
    f.setup();f.mutation=(0xa201d4d0,b'\1')
    check('scene-change-across-native-target-query-rejects-reflow',f.dispatch()==0 and len(f.rendered)==1)
    f.setup();f.mutation=(0xa18298b8,b'\2')
    check('page-change-across-native-target-query-rejects-reflow',f.dispatch()==0 and len(f.rendered)==1)
    f.setup();f.u.mem_write(0xa18298b8,b'\2')
    check('dial-image1a-strip-disables-source-clear',f.dispatch(0x1a,box=(199,100,201,111),clear=1)==1 and len(f.rendered)==1 and struct.unpack_from('<I',f.rendered[0][1],36)[0]==0)
    f.setup();f.write(SLOT,0x12345679);before=f.read(f.variable('received'))
    check('foreign-slot-prefetched-bridge-falls-back-without-module',f.dispatch()==0 and len(f.rendered)==1 and f.read(f.variable('received'))==before)
    old=GridHostFixture(old_raw,old_host,packet,metadata)
    result=old.call(old_host['symbols']['z7_module_load_once'],STATE)
    check('api80-runtime-rejection-frees-module-before-graphics-publication',result==7 and not old.live and old.read(STATE+48)==0 and old.read(SLOT)==0x10372391)
    return dict(passed=True,checks=checks,actual_loaded_sdk_module_bridge_page_target_orientation_dispatch_and_completion_execute=True,
                kernel_filesystem_allocator_backend_and_ui_task_registry_orientation_state_supplied=True,
                full_portrait_pending_request_fence_boot_task_schedule_or_pixels_proven=False,camera_card_access=False)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('host','report','old-host','old-report','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    host=json.loads(a.report.read_text(encoding='utf-8'));raw=a.host.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==host['main_payload_sha256'] and host.get('api_bytes')==84
    old_host=json.loads(a.old_report.read_text(encoding='utf-8'));old_raw=a.old_host.read_bytes()
    assert hashlib.sha256(old_raw).hexdigest()==old_host['main_payload_sha256'] and old_host.get('api_bytes')==80
    packet,metadata=build(ROOT/'z7-native-modules/examples/portrait_grid_host_probe.c',zig=ZIG)
    again,other=build(ROOT/'z7-native-modules/examples/portrait_grid_host_probe.c',zig=ZIG);assert packet==again and metadata==other
    result=audit(raw,host,packet,metadata,old_raw,old_host)
    names=('tools/audit_z7_portrait_grid_host.py','tools/audit_z7_module_host.py','tools/audit_z7_information_native.py','tools/audit_z7_portrait_draw.py',
           'tools/audit_z7_portrait_grid_message.py','tools/audit_z7_portrait_page_message.py','tools/audit_splash_image.py','tools/build_z7_module.py','z7-native-modules/sdk/module.ld',
           'z7-native-modules/examples/portrait_grid_host_probe.c','z7-native-modules/plugins/portrait_grid_message.h',
           'z7-native-modules/plugins/portrait_page_message.h','z7-native-modules/plugins/portrait_footer.h',
           'z7-native-modules/plugins/portrait_draw.h','z7-native-modules/plugins/portrait_geometry.h','z7-native-modules/plugins/portrait_grid.h',
           'z7-native-modules/plugins/portrait_page.h','z7-native-modules/plugins/portrait_takeover.h','z7-native-modules/plugins/portrait_target.h','z7-native-modules/plugins/orientation_sample.h')
    result.update(host_sha256=host['main_payload_sha256'],probe_sha256=hashlib.sha256(packet).hexdigest(),reproducible_probe=True,probe_bytes=len(packet),
                  source_sha256={**host['source_files'],**{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names}})
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(packet)
    (out/'probe.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),probe_bytes=len(packet))))

if __name__=='__main__':main()
