"""Original-Z7 native shadow preparation and per-file wrappers (MIT).

Compiled copies/relocation/wrappers execute. Native open/split/track completion,
pose and file contexts are supplied. No callback installed, complete native mux
task or physical file/recording behavior proved.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
from unicorn.arm_const import UC_ARM_REG_R0
from audit_z7_module_host import HostFixture
from audit_splash_image import MEM
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output

ROOT=0xa1f532f8;CONTROL=ROOT+0x40;SLOT=ROOT+0x2c
IDENTITY=struct.pack('>9i',65536,0,0,0,65536,0,0,0,1<<30)
class MovieFixture(HostFixture):
    def __init__(self,*args):
        super().__init__(*args);self.u.mem_map(0xa1f50000,0x10000)
        self.write(0xa1815030,CONTROL);self.write(SLOT,0x1027e797)
        self.file=1;self.pose=1;self.reply=0;self.context=MEM+0x10000;self.track_result=0
        self.opens=self.splits=self.tracks=self.pose_reads=0
    def write(self,a,v):self.u.mem_write(a,struct.pack('<I',v))
    def read(self,a):return int.from_bytes(self.u.mem_read(a,4),'little')
    def hook(self,u,a,size,context):
        if a==0x1027db80:self.ret(1)
        elif a==0x1027dcae:self.ret(0)
        elif a in (0x1027e50a,0x1027de96):
            if a==0x1027e50a:self.opens+=1;offset=0x160
            else:self.splits+=1;offset=0x318
            if 1<=self.file<=10:
                self.write(CONTROL+offset+8*self.file+4,self.reply)
                self.write(CONTROL+0x3f0+0x88*self.file+0x2c,self.context)
            self.ret(self.file)
        elif a==0x101b331a:self.pose_reads+=1;self.ret(self.pose)
        elif a==0x102a9c2c:
            self.tracks+=1;p=u.reg_read(UC_ARM_REG_R0)
            if not self.track_result and p:u.mem_write(p+0x109,IDENTITY)
            self.ret(self.track_result)
        else:super().hook(u,a,size,context)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('host','module','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256'] and hashlib.sha256(packet).hexdigest()==m['module_sha256']
    f=MovieFixture(raw,h,packet);checks=[]
    def check(n,good):
        assert good,n
        checks.append(n)
    check('prepare-only-module-loads',f.call(h['symbols']['z7_module_load_once'],STATE)==8)
    base=f.words()[12];s=m['symbols'];operation=base+s['z7_movie_rotation_operation']
    def op(n,arg=0):return f.call(operation,n,arg)
    check('prepare-does-not-publish-task-callback',f.read(SLOT)==0x1027e797 and not f.opens and not f.splits and not f.tracks)
    check('all-native-shadows-prepared',f.read(base+s['z7_movie_prepared'])==1 and not f.read(base+s['z7_movie_installed']))
    cs=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
    groups=(('task',0x1027e796,0x700,0x2fa,op(4),{0x4a:base+s['movie_open'],0x1d4:base+s['movie_split'],0x23e:op(5)|1}),
            ('close',0x1027dcfe,0x300,0x12c,op(5),{0xbc:op(6)|1}),
            ('header',0x102aa66c,0x7c,0x7c,op(6),{0x1c:base+s['movie_track']}))
    for name,native,length,body,dest,overrides in groups:
        check(name+'-preserves-pc-alignment',dest%4==native%4)
        original=raw[native-0x10020000:native-0x10020000+length]
        for ins in cs.disasm(original[:body],native):
            if ins.mnemonic not in ('bl','blx') or not ins.op_str.startswith('#'):continue
            offset=ins.address-native;new=list(cs.disasm(bytes(f.u.mem_read(dest+offset,4)),dest+offset))[0]
            stub=int(new.op_str[1:],16)
            expected=overrides.get(offset,int(ins.op_str[1:],16)|(0 if ins.mnemonic=='blx' else 1))
            check(name+'-call-'+hex(offset),new.mnemonic=='bl' and bytes(f.u.mem_read(stub,4))==bytes.fromhex('dff800f0') and f.read(stub+4)==expected)
        # All bytes apart from original call words remain exact native bytes.
        changed=set()
        for ins in cs.disasm(original[:body],native):
            if ins.mnemonic in ('bl','blx') and ins.op_str.startswith('#'):changed.update(range(ins.address-native,ins.address-native+4))
        shadow=bytes(f.u.mem_read(dest,length))
        check(name+'-preserves-native-bytes-and-literal-pools',all(shadow[i]==b for i,b in enumerate(original) if i not in changed))
    for file in range(1,11):
        f.file=file;f.context=MEM+0x10000+file*0x1000
        for pose in (0,1,2,3):
            f.pose=pose;f.reply=0
            check(f'open-returns-native-file-{file}-{pose}',op(1)==file)
            f.pose=(pose+1)%4
            op(3,f.context)
            matrices={1:(0,-65536,0,65536,0,0,0,0,1<<30),2:(0,65536,0,-65536,0,0,0,0,1<<30),3:(-65536,0,0,0,-65536,0,0,0,1<<30)}
            expected=struct.pack('>9i',*matrices[pose]) if pose else IDENTITY
            check(f'header-retains-open-pose-{file}-{pose}',bytes(f.u.mem_read(f.context+0x109,36))==expected)
    f.file=1;f.reply=0;f.pose=3;f.context=MEM+0x32000
    f.write(0xa181503c,0);before=f.opens
    f.call(op(4),1)
    check('relocated-native-task-open-event-runs-owned-wrapper',f.opens==before+1)
    op(3,f.context)
    check('task-open-event-latches-pose',bytes(f.u.mem_read(f.context+0x109,36))==struct.pack('>9i',-65536,0,0,0,-65536,0,0,0,1<<30))
    f.pose=2;f.context=MEM+0x33000;f.write(0xa181503c,1);before=f.splits
    f.call(op(4),16)
    check('relocated-native-task-split-event-runs-owned-wrapper',f.splits==before+1)
    op(3,f.context)
    check('task-split-event-latches-pose',bytes(f.u.mem_read(f.context+0x109,36))==struct.pack('>9i',0,65536,0,-65536,0,0,0,0,1<<30))
    f.file=1;f.context=MEM+0x30000;f.pose=1;op(1)
    f.context=MEM+0x31000;f.pose=2;check('split-returns-native-file',op(2)==1)
    op(3,MEM+0x30000);check('split-invalidates-old-context-pose',bytes(f.u.mem_read(MEM+0x30109,36))==IDENTITY)
    op(3,f.context);check('split-latches-new-file-pose',bytes(f.u.mem_read(f.context+0x109,36))!=IDENTITY)
    f.reply=1;before=f.pose_reads;op(1);op(3,f.context)
    check('failed-open-clears-old-pose-without-sampling',f.pose_reads==before and bytes(f.u.mem_read(f.context+0x109,36))==IDENTITY)
    f.reply=0;f.pose=4;op(1);op(3,f.context)
    check('unknown-pose-leaves-native-matrix',bytes(f.u.mem_read(f.context+0x109,36))==IDENTITY)
    f.pose=1;op(1);f.track_result=3;f.u.mem_write(f.context+0x109,b'X'*36)
    check('track-failure-return-and-bytes-preserved',op(3,f.context)==3 and bytes(f.u.mem_read(f.context+0x109,36))==b'X'*36)
    check('callback-still-native-after-all-wrapper-calls',f.read(SLOT)==0x1027e797)
    original=bytes(f.u.mem_read(0x1027e796,1));f.u.mem_write(0x1027e796,bytes([original[0]^1]))
    check('native-fingerprint-change-rejects-without-publication',op(0)==0 and not f.read(base+s['z7_movie_prepared']) and f.read(SLOT)==0x1027e797)
    f.u.mem_write(0x1027e796,original)
    check('exact-native-fingerprint-prepares-again',op(0)==1)
    f.write(SLOT,0x1027e799);check('foreign-callback-rejects-preparation',op(0)==0)
    result=dict(passed=True,count=len(checks),checks=checks,module_sha256=m['module_sha256'],
        prepare_only=True,callback_installed=False,camera_access=False,physical_movie=False,
        native_open_split_track_results_supplied=True,complete_native_task_verified=False,scope=__doc__)
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
