"""Movie file-pose policy and original-Z7 native matrix emission spans (MIT).

Compiled independent latches/matrices execute. Original track-writer prefix and
its matrix-copy instruction span execute with supplied context storage. Native
mux task/file I/O, completed headers and real orientation remain unverified.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R4,UC_ARM_REG_SP,UC_ARM_REG_LR
from audit_splash_image import NativePNG,MEM,STACK,STOP,STOCK_SHA
from audit_z7_module_host import HostFixture
from build_z7_module import ROOT,build
from build_z7_module_host import STATE,ZIG
from prepare_flash_review import require_private_output


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('host','stock-main','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    raw=a.stock_main.read_bytes();assert hashlib.sha256(raw).hexdigest()==STOCK_SHA
    h=json.loads((a.host/'module-host.emulator.json').read_text());hostraw=(a.host/'module-host.emulator.main.bin').read_bytes()
    assert hashlib.sha256(hostraw).hexdigest()==h['main_payload_sha256']
    packet,m=build(ROOT/'z7-native-modules/examples/movie_orientation_probe.c',zig=ZIG)
    f=HostFixture(hostraw,h,packet);checks=[]
    def check(name,good):
        assert good,name
        checks.append(name)
    check('pure-probe-loads',f.call(h['symbols']['z7_module_load_once'],STATE)==8)
    base=f.words()[12];address=lambda n:base+m['symbols']['z7_movie_'+n]
    def op(n,a=0,b=0,c=0):return f.call(address('operation'),n,a,b,c)
    def current(file,context):f.u.mem_write(address('contexts')+4*file,struct.pack('<I',context))
    def snapshot():return bytes(f.u.mem_read(address('records'),88))
    for file in range(1,11):
        context=0xa2000000+file*0x100
        for pose in range(4):
            check(f'latch-{file}-{pose}',op(1,file,context,pose)==1)
            current(file,context);check(f'matched-current-file-{file}-{pose}',op(2,context)==pose)
            current(file,context+4);check(f'stale-file-context-{file}-{pose}',op(2,context)==0)
            current(file,context);check(f'close-clears-{file}-{pose}',op(3,file)==1 and op(2,context)==0)
    for file in (0,11,0xffffffff):
        before=snapshot();check('invalid-file-preserves-records-'+str(file),op(1,file,0xa2000000,1)==0 and snapshot()==before)
    current(1,0xa2000100);check('valid-before-reuse',op(1,1,0xa2000100,1)==1)
    f.u.mem_write(address('reply'),struct.pack('<I',1))
    check('failed-open-clears-prior-file-pose',op(1,1,0xa2000100,2)==0 and op(2,0xa2000100)==0)
    f.u.mem_write(address('reply'),bytes(4));op(1,1,0xa2000100,1)
    check('unknown-native-pose-clears-prior-file-pose',op(1,1,0xa2000100,4)==0 and op(2,0xa2000100)==0)
    current(1,0xa2000100);current(2,0xa2000100);op(1,1,0xa2000100,1);op(1,2,0xa2000100,2)
    check('ambiguous-context-refuses-rotation',op(2,0xa2000100)==0)
    matrices={1:(0,-65536,0,65536,0,0,0,0,1<<30),2:(0,65536,0,-65536,0,0,0,0,1<<30),3:(-65536,0,0,0,-65536,0,0,0,1<<30)}
    identity=struct.pack('>9i',65536,0,0,0,65536,0,0,0,1<<30)
    for pose in (0,1,2,3,4,0xffffffff):
        before=identity+b'CANARIES';f.u.mem_write(address('matrix'),before)
        result=op(4,pose,44)
        expected=struct.pack('>9i',*matrices[pose]) if pose in matrices else identity
        check('matrix-exact-and-bounded-'+str(pose),result==int(pose in matrices) and bytes(f.u.mem_read(address('matrix'),44))==expected+b'CANARIES')
    before=b'X'*44;f.u.mem_write(address('matrix'),before)
    check('short-matrix-buffer-untouched',op(4,1,35)==0 and bytes(f.u.mem_read(address('matrix'),44))==before)
    # Execute the native prefix which copies its original identity matrix to SP+2C.
    native=NativePNG(raw);u=native.u;context=MEM+0x1000
    u.reg_write(UC_ARM_REG_R0,context);u.reg_write(UC_ARM_REG_SP,STACK);u.reg_write(UC_ARM_REG_LR,STOP|1)
    u.emu_start(0x102a9c2d,0x102a9c40,timeout=10000000,count=10000000)
    stack=u.reg_read(UC_ARM_REG_SP)
    check('native-track-prefix-creates-iso-identity-matrix',bytes(u.mem_read(stack+0x2c,36))==identity)
    u.mem_write(context,b'X'*0x180);u.reg_write(UC_ARM_REG_R4,context)
    u.emu_start(0x102aa2ef,0x102aa2fa,timeout=10000000,count=10000000)
    data=bytes(u.mem_read(context,0x180))
    check('native-matrix-emission-is-context-plus109-only',data==b'X'*0x109+identity+b'X'*(0x180-0x109-36))
    result=dict(passed=True,count=len(checks),checks=checks,probe_sha256=hashlib.sha256(packet).hexdigest(),
        stock_main_sha256=STOCK_SHA,native_track_builder='0x102A9C2C',native_matrix_offset='0x109',
        file_task_hooks_installed=False,completed_track_headers_verified=False,physical_orientation_verified=False,
        source_hashes={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('z7-native-modules/plugins/movie_orientation.h','z7-native-modules/examples/movie_orientation_probe.c','tools/audit_z7_movie_orientation.py')},scope=__doc__)
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
