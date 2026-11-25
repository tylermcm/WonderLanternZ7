"""Native mux dispatcher open/split/close and metadata flow (MIT).

Request flags, file-open/split results, pose, contexts and external file services
are supplied. Native dispatcher, mux callbacks, copied close/header, sample
finalizer, movie/track constructors and scatter serializer execute. Empty sample
descriptions produce metadata only, not playable movies or a physical recording.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_PC,UC_ARM_REG_SP,UC_ARM_REG_LR
from audit_z7_movie_shadows import MovieFixture,ROOT,CONTROL,SLOT,IDENTITY
from audit_z7_module_host import HostFixture
from audit_z7_combined_display import CombinedFixture
from audit_splash_image import MEM,STACK,STOP
from build_z7_module_host import STATE
from movie_track_fixture import initialize_movie_context
from prepare_flash_review import require_private_output

MATRICES=(IDENTITY,struct.pack('>9i',0,-65536,0,65536,0,0,0,0,1<<30),
          struct.pack('>9i',0,65536,0,-65536,0,0,0,0,1<<30),
          struct.pack('>9i',-65536,0,0,0,-65536,0,0,0,1<<30))


class LifecycleFixture(MovieFixture):
    def __init__(self,*args):
        super().__init__(*args)
        self.dispatching=False;self.callbacks=[];self.native_metadata=[];self.header_results=[]
        self.record_code_cache=True
        self.execute_native_track=True;self.capture_stream=True

    def hook(self,u,a,size,context):
        if self.dispatching and a==0x10170c14:
            u.emu_stop()
        elif a in (0x10170944,0x1017093e):
            self.ret(1)  # Supplied mutex boundary; native error helpers execute.
        elif a in (0x1027db80,0x1027dcae,0x1027dbb8):
            HostFixture.hook(self,u,a,size,context)
        elif self.close_running and a in (0x102aa53c,0x102aa35c,0x102a819a):
            self.native_metadata.append(a)
            # Deliberately bypass MovieFixture's supplied builder returns.
            HostFixture.hook(self,u,a,size,context)
        elif a in (0x1027e50a,0x1027de96):
            super().hook(u,a,size,context)
            self.write(CONTROL,1);self.write(CONTROL+8,10)
        else:
            if self.dispatching and a==self.shadow:self.callbacks.append(u.reg_read(UC_ARM_REG_R0))
            if self.dispatching and a==self.close_shadow+0xc0:self.header_results.append(u.reg_read(UC_ARM_REG_R0))
            super().hook(u,a,size,context)

    def dispatch(self,event):
        assert self.u.reg_read(UC_ARM_REG_PC)==0x10170c14
        assert self.u.reg_read(UC_ARM_REG_R0)==ROOT+0x20
        assert self.u.reg_read(UC_ARM_REG_R1)==0xff003f
        self.write(self.u.reg_read(UC_ARM_REG_R2),event)
        self.ret(0)
        self.u.emu_start(self.u.reg_read(UC_ARM_REG_PC)|1,STOP,timeout=30000000,count=10000000)
        assert self.u.reg_read(UC_ARM_REG_PC)==0x10170c14,'Dispatcher did not return to wait'


class CumulativeLifecycleFixture(LifecycleFixture,CombinedFixture):pass


def matrix_from_stream(data):
    def atoms(lo,hi):
        cursor=lo;found=[]
        while cursor<hi:
            assert cursor+8<=hi
            size=int.from_bytes(data[cursor:cursor+4],'big');tag=data[cursor+4:cursor+8]
            assert 8<=size<=hi-cursor,(cursor,size,tag)
            found.append((tag,cursor,size))
            if tag in (b'moov',b'trak',b'mdia',b'minf',b'dinf',b'stbl',b'edts'):
                found+=atoms(cursor+8,cursor+size)
            cursor+=size
        assert cursor==hi
        return found
    tree=atoms(0,len(data));tkhd=[x for x in tree if x[0]==b'tkhd']
    assert len(tkhd)==1 and tkhd[0][2]==92 and tree[0][0]==b'moov'
    offset=tkhd[0][1]+48
    return data[offset:offset+36]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text())
    raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256']
    assert hashlib.sha256(packet).hexdigest()==m['module_sha256']
    assert hashlib.sha256(raw[0x10170840-0x10020000:0x1017085e-0x10020000]).hexdigest()=='16bd05bad7b8c180a1d4da2473677d7db51b8b3fd95278fde70109eaf0ddb616'
    cumulative=m.get('configuration',{}).get('movie_orientation',False)
    f=CumulativeLifecycleFixture(raw,h,packet,m) if cumulative else LifecycleFixture(raw,h,packet)
    checks=[]
    def check(n,ok):
        assert ok,n
        checks.append(n)
    f.write(0xa181503c,3)
    check('module-loads',f.call(h['symbols']['z7_module_load_once'],STATE)==8)
    base=f.words()[12];op=base+m['symbols']['z7_movie_rotation_operation']
    f.shadow=f.call(op,4);f.close_shadow=f.call(op,5);f.write(0xa181503c,0)
    check('explicit-publication-succeeds',f.call(op,7)==1)
    shadows=[(p,bytes(f.u.mem_read(p,n))) for p,n in f.cache_cleans]
    f.write(ROOT+0x30,0xff003f);f.dispatching=True
    for reg,val in ((UC_ARM_REG_R0,ROOT),(UC_ARM_REG_SP,STACK),(UC_ARM_REG_LR,STOP|1)):
        f.u.reg_write(reg,val)
    f.u.emu_start(0x10170841,STOP,timeout=30000000,count=1000000)
    streams=[];artifacts=out.with_suffix('');artifacts.mkdir()
    for split in (False,True):
        for pose in range(4):
            name=f'{"split" if split else "single"}-{pose}'
            f.file=1;f.reply=0;f.pose=pose;f.context=MEM+0x50000
            initialize_movie_context(f.u,f.context)
            before=f.opens
            f.dispatch(1)
            check(name+'-native-open-dispatched',f.opens==before+1 and f.read(0xa181503c)==1)
            expected_pose=pose
            if split:
                f.context=MEM+0x60000;f.pose=(pose+1)%4;expected_pose=f.pose
                initialize_movie_context(f.u,f.context)
                before=f.splits;f.dispatch(16)
                check(name+'-native-split-dispatched',f.splits==before+1 and f.read(0xa181503c)==1)
            # The close command and native file record are supplied request/I/O
            # boundaries. Do not alter the native task state before closing.
            f.write(CONTROL+0x64,1)
            f.u.mem_write(CONTROL+0x14c,struct.pack('<5I',1,0,0,0,0))
            record=CONTROL+0x3f0+0x88
            f.write(record,7);f.write(record+4,8)
            f.pose=(expected_pose+2)%4;f.stream=[];f.native_metadata=[];f.header_results=[]
            f.close_running=True;f.dispatch(32);f.close_running=False
            data=b''.join(f.stream)
            check(name+'-native-metadata-pipeline-runs',f.native_metadata==[0x102aa53c,0x102aa35c,0x102a819a])
            check(name+'-native-header-return-preserved',f.header_results==[0])
            check(name+'-native-stream-retains-file-pose',matrix_from_stream(data)==MATRICES[expected_pose])
            check(name+'-close-returns-idle-and-zero-files',f.read(0xa181503c)==0 and f.read(CONTROL)==0)
            check(name+'-native-record-context-cleared',f.read(record+0x2c)==0)
            check(name+'-owned-callback-remains-resident',f.read(SLOT)==f.shadow|1)
            (artifacts/(name+'.bin')).write_bytes(data)
            streams.append(dict(name=name+'.bin',bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),pose=expected_pose))
    check('all-published-code-remains-immutable',all(bytes(f.u.mem_read(p,len(b)))==b for p,b in shadows))
    check('all-events-use-owned-dispatch',f.callbacks==[1,32]*4+[1,16,32]*4)
    result=dict(schema=1,passed=True,count=len(checks),checks=checks,
        module_sha256=m['module_sha256'],cumulative_binary=cumulative,metadata_streams=streams,
        native_metadata_pipeline_executes=True,native_dispatch_executes=True,
        native_task_state_transitions_execute=True,event_wait_supplied=True,
        native_error_helpers_execute=True,mutex_operations_supplied=True,
        file_open_split_results_supplied=True,external_file_services_supplied=True,
        empty_sample_descriptions_supplied=True,physical_scheduler_verified=False,
        complete_playable_movie_verified=False,camera_access=False,scope=__doc__)
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
