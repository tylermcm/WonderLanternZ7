"""Execute original mux event dispatcher across callback publication (MIT).

Event waits, native file-open results, pose and cache-clean services are supplied.
CPU contexts are paused/restored at exact instruction boundaries to enumerate
publication interleavings. This is not a physical scheduler or quiescence proof.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_SP,UC_ARM_REG_LR
from audit_z7_movie_shadows import MovieFixture,ROOT,SLOT,IDENTITY
from audit_z7_combined_display import CombinedFixture
from audit_splash_image import MEM,STACK,STOP
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output


class DispatchFixture(MovieFixture):
    def __init__(self,*args):
        super().__init__(*args)
        self.dispatching=False
        self.delivered=0
        self.dispatch_calls=[]
        self.contexts=[]
        self.record_code_cache=True

    def hook(self,u,a,size,context):
        if self.dispatching and a==0x10170c14:
            if self.delivered==2:
                u.emu_stop()
                return
            assert u.reg_read(UC_ARM_REG_R0)==ROOT+0x20
            assert u.reg_read(UC_ARM_REG_R1)==0xff003f
            event=1 if not self.delivered else 0
            if event:
                self.file=1
                self.context=MEM+0x11000
                self.contexts.append(self.context)
            self.delivered+=1
            self.write(u.reg_read(UC_ARM_REG_R2),event)
            self.ret(0)
        elif self.dispatching and a in (0x1027e796,self.shadow):
            self.dispatch_calls.append((a,u.reg_read(UC_ARM_REG_R0)))
            super().hook(u,a,size,context)
        else:
            super().hook(u,a,size,context)


class CumulativeDispatchFixture(DispatchFixture,CombinedFixture):
    pass


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text())
    raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256']
    assert hashlib.sha256(packet).hexdigest()==m['module_sha256']
    dispatcher_sha=hashlib.sha256(raw[0x10170840-0x10020000:0x1017085e-0x10020000]).hexdigest()
    assert dispatcher_sha=='16bd05bad7b8c180a1d4da2473677d7db51b8b3fd95278fde70109eaf0ddb616'
    checks=[]
    def check(n,ok):
        assert ok,n
        checks.append(n)
    observations=[]
    for name,boundary,old_first in (('before-wait',0x1017084c,False),
                                    ('before-pointer-load',0x10170856,False),
                                    ('after-pointer-load',0x10170858,True)):
        cumulative=m.get('configuration',{}).get('movie_orientation',False)
        f=(CumulativeDispatchFixture if cumulative else DispatchFixture)(raw,h,packet,m) if cumulative else DispatchFixture(raw,h,packet)
        # The cumulative profile's normal init attempt rejects ROM state3.
        # Exercise later publication explicitly, using the exact compiled body.
        f.write(0xa181503c,3)
        check(name+'-module-initialization-succeeds',f.call(h['symbols']['z7_module_load_once'],STATE)==8)
        check(name+'-starts-with-native-slot',f.read(SLOT)==0x1027e797)
        base=f.words()[12];op=base+m['symbols']['z7_movie_rotation_operation']
        f.shadow=f.call(op,4)
        f.write(0xa181503c,0)
        f.write(ROOT+0x30,0xff003f)
        f.dispatching=True
        for reg,val in ((UC_ARM_REG_R0,ROOT),(UC_ARM_REG_SP,STACK),(UC_ARM_REG_LR,STOP|1)):
            f.u.reg_write(reg,val)
        f.u.emu_start(0x10170841,boundary,timeout=30000000,count=1000000)
        saved=f.u.context_save()
        saved_stack=bytes(f.u.mem_read(STACK-0x1000,0x2000))
        # Publish with an independent CPU context; restore the suspended native
        # dispatch registers afterward. Shared memory retains the pointer store.
        check(name+'-publication-succeeds',f.call(op,7)==1)
        check(name+'-owned-slot-published',f.read(SLOT)==f.shadow|1)
        shadows=[(p,bytes(f.u.mem_read(p,n))) for p,n in f.cache_cleans]
        f.u.mem_write(STACK-0x1000,saved_stack)
        f.u.context_restore(saved)
        f.u.emu_start(boundary|1,STOP,timeout=30000000,count=1000000)
        expected=[(0x1027e796 if old_first else f.shadow,1),(f.shadow,0)]
        check(name+'-dispatcher-reloads-callback-per-event',f.dispatch_calls==expected)
        check(name+'-open-and-empty-event-return',f.opens==1 and f.delivered==2)
        check(name+'-all-code-cleaned-before-dispatch',len(f.cache_cleans)==3)
        check(name+'-published-code-remains-immutable',all(bytes(f.u.mem_read(p,len(b)))==b for p,b in shadows))
        f.dispatching=False
        for index,ctx in enumerate(f.contexts):
            check(name+'-track-wrapper-return-'+str(index),f.call(op,3,ctx)==0)
            actual=bytes(f.u.mem_read(ctx+0x109,36))
            rotated=struct.pack('>9i',0,-65536,0,65536,0,0,0,0,1<<30)
            check(name+'-pose-or-native-fallback-'+str(index),actual==(IDENTITY if old_first else rotated))
        observations.append(dict(boundary=name,old_callback_once=old_first,
                                 events=2,callbacks=['native' if x[0]==0x1027e796 else 'owned' for x in f.dispatch_calls]))
    result=dict(schema=1,passed=True,count=len(checks),checks=checks,
        module_sha256=m['module_sha256'],host_main_sha256=h['main_payload_sha256'],
        original_dispatcher_sha256=dispatcher_sha,
        observations=observations,event_wait_supplied=True,native_open_results_supplied=True,
        cache_clean_supplied=True,cpu_context_interleavings_supplied=True,
        cumulative_binary=cumulative,physical_scheduler_verified=False,task_quiescence_verified=False,
        camera_access=False,scope=__doc__)
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
