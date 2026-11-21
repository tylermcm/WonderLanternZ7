"""Observed portrait band lifecycle through original transparent clear body.

SPDX-License-Identifier: MIT. Compiled ownership and native clear/image bodies,
normalization/completion execute. GPU state/creation/draw, page admission and
sensor direction supplied. No unobserved exits, buffer lifetime, scheduling/pixels.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_LR
from audit_z7_portrait_native_image import NativeImageFixture
from audit_z7_portrait_draw import CODE,BOX,MESSAGE,PAYLOAD
from audit_splash_image import STOCK_SHA
from build_z7_module import build
from build_z7_module_host import ROOT,ZIG
STATE=BOX+256
COLOR=struct.pack('<4f',.25,.5,.75,1)

class BandsFixture(NativeImageFixture):
    def __init__(self,raw,packet,metadata):
        meta=dict(metadata,symbols=dict(metadata['symbols']));meta['symbols']['z7_portrait_page_message_probe']=metadata['symbols']['z7_portrait_bands_dispatch_probe']
        super().__init__(raw,packet,meta);self.image_bytes=metadata['image_bytes'];self.color=COLOR;self.clears=[];self.clear_colors=[]
    def hook(self,u,a,size,context):
        if a==0x1042f5a8:
            p=u.reg_read(UC_ARM_REG_R0);lr=u.reg_read(UC_ARM_REG_LR)&~1;internal=CODE<=lr<CODE+self.image_bytes
            rect=struct.unpack('<4I',u.mem_read(p,16));self.clears.append((internal,rect))
            self.events.append(('band-clear',rect) if internal else 'render');return
        if a==0x104501f8 and u.reg_read(UC_ARM_REG_R0)==0x1121:
            assert u.reg_read(UC_ARM_REG_R1)==4;u.mem_write(u.reg_read(UC_ARM_REG_R2),self.color);self.ret(0);return
        if a==0x1045016a and u.reg_read(UC_ARM_REG_R0)==0x1121:
            assert u.reg_read(UC_ARM_REG_R1)==4;self.color=bytes(u.mem_read(u.reg_read(UC_ARM_REG_R2),16));self.ret(0);return
        if a==0x1045081e:self.clear_colors.append(self.color)
        super().hook(u,a,size,context)

def audit(raw,packet,metadata):
    f=BandsFixture(raw,packet,metadata);checks=[]
    f.u.mem_write(STATE,bytes(12))
    def check(name,good):checks.append(dict(name=name,passed=bool(good)));assert good,name
    def state():return struct.unpack('<3I',f.u.mem_read(STATE,12))
    def reset_streams():f.events.clear();f.api.clear();f.native_payloads.clear();f.rendered.clear();f.clears.clear();f.clear_colors.clear()
    def prepare(command=0x1a,box=(300,430,80,24)):
        if command==0x1a:msg,data,_=f.prepare(command,clear=1,box=box)
        else:
            x,y,w,h=box;data=struct.pack('<6I',x,480-y-h,w,h,0,0);f.u.mem_write(PAYLOAD,data)
            msg=struct.pack('<7I',1,2,3,0x1042eadf,0x42010017,PAYLOAD,123);f.u.mem_write(MESSAGE,msg)
        reset_streams();return msg,data
    def run(name,page,orientation,internal,expected_state,command=0x1a,box=(300,430,80,24),handled=1):
        msg,data=prepare(command,box);got=f.call(f.operation,STATE,MESSAGE,page,orientation)
        actual=[rect for own,rect in f.clears if own]
        check(name,got==handled and actual==internal and state()==expected_state)
        check(name+'-native-clear-color-restored',f.color==COLOR and all(c==bytes(16) for c in f.clear_colors))
        check(name+'-producer-completes-once',sum(isinstance(e,tuple) and e[0]=='ack' for e in f.events)==1 and f.events[-2:]==[('ack',0x42010062,0),'event'])
        check(name+'-payload-preserved',bytes(f.u.mem_read(PAYLOAD,len(data)))==data and bytes(f.u.mem_read(MESSAGE,24))==msg[:24] and int.from_bytes(f.u.mem_read(MESSAGE+24,4),'little')==0)
        # Internal native clears precede producer rendering/completion.
        check(name+'-clear-before-producer',f.events[:len(internal)]==[('band-clear',r) for r in internal])
    left=(0,0,60,480);right=(660,0,60,480);dial=(280,0,157,480)
    run('first-footer',1,1,[left],(1,0,0))
    run('repeated-footer',1,1,[],(1,0,0))
    prepare(0x17,(0,0,720,480));f.call(CODE+metadata['symbols']['z7_portrait_bands_observe_probe'],STATE,MESSAGE)
    check('logical-clear-observation-only-marks-dirty',state()==(1,1,0) and not f.events and not f.api)
    run('dirty-footer',1,1,[left],(1,0,0))
    run('dial-entry',2,1,[dial],(1,0,1),box=(199,100,201,111))
    run('settings-release',3,1,[left,dial],(0,0,0),command=0x17,box=(10,290,100,53))
    run('footer-reentry',1,1,[left],(1,0,0))
    run('owned-orientation-replacement',1,2,[left,right],(2,0,0))
    run('foreign-page-forgets-without-band-clear',0,2,[],(0,0,0),command=0x17,box=(10,290,100,53),handled=0)
    run('full-clear-dirties-band',1,1,[],(0,1,0),command=0x17,box=(0,0,720,480),handled=0)
    run('footer-after-full-clear',1,1,[left],(1,0,0))
    f.call(CODE+metadata['symbols']['z7_portrait_bands_forget_probe'],STATE)
    check('explicit-forget-drops-ownership',state()==(0,0,0))
    return dict(passed=True,checks=checks,original_clear_body_color_save_transparent_black_restore_and_completion_execute=True,
                gpu_services_page_and_orientation_admission_supplied=True,
                unobserved_lifecycle_native_task_exclusion_buffer_lifetime_or_pixels_proven=False,camera_card_access=False)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    raw=a.stock_main.read_bytes();assert hashlib.sha256(raw).hexdigest()==STOCK_SHA
    packet,metadata=build(ROOT/'z7-native-modules/examples/portrait_bands_probe.c',zig=ZIG)
    again,other=build(ROOT/'z7-native-modules/examples/portrait_bands_probe.c',zig=ZIG);assert packet==again and metadata==other
    result=audit(raw,packet,metadata)
    names=('tools/audit_z7_portrait_bands.py','tools/audit_z7_portrait_native_image.py','tools/audit_z7_portrait_page_message.py','tools/audit_z7_portrait_draw.py','tools/audit_z7_portrait_grid_message.py','tools/audit_splash_image.py','tools/build_z7_module.py',
           'z7-native-modules/sdk/module.h','z7-native-modules/sdk/module.ld','z7-native-modules/plugins/portrait_bands.h','z7-native-modules/plugins/portrait_page_message.h',
           'z7-native-modules/plugins/portrait_grid_message.h','z7-native-modules/plugins/portrait_footer.h','z7-native-modules/plugins/portrait_grid.h','z7-native-modules/plugins/portrait_geometry.h','z7-native-modules/plugins/portrait_draw.h','z7-native-modules/examples/portrait_bands_probe.c')
    result.update(probe_sha256=hashlib.sha256(packet).hexdigest(),reproducible_probe=True,probe_bytes=len(packet),source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(packet)
    (out/'probe.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),probe_bytes=len(packet))))

if __name__=='__main__':main()
