"""Execute API80 cache-copy bridges, SDK snapshot calls and native copy races.

SPDX-License-Identifier: MIT. Native memcpy/getter/writer/constructor, host and
loaded SDK probe execute. FS/kernel, bank indices and task schedules supplied.
No full boot/writer/index/lifetime closure or automatic display handoff proof.
"""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import struct

from unicorn import UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_CPSR, UC_ARM_REG_R12, UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3
from audit_splash_image import MEM, STOCK_SHA, STACK
from audit_z7_module_host import HostFixture
from audit_z7_highlight_native_cache import CacheFixture, CACHE, STRIDE, REQUEST_OFFSET, CALLER_STACK, WRITER
from audit_z7_cache_observation import CONSTRUCTOR, resume
from audit_z7_highlight_converter import request
from audit_z7_highlight_submission import enter, returned
from build_z7_module import build
from build_z7_module_host import ROOT, ZIG, STATE, CURSOR

SNAPSHOT=MEM+0x90000


class CacheHostFixture(HostFixture):
    def __init__(self,raw,report,packet,metadata):
        self.watch=self.copied=0;self.pause_copy=self.pause_validate=False;self.writes=[]
        super().__init__(raw,report,packet)
        self.u.mem_map(0xa1f18000,0x5000)
        self.u.mem_map(0xa24e1000,0x1000)
        self.write(0xa24e1e00,0)
        self.u.mem_map(0xa2510000,0x10000)
        # Observe cache stores only; filesystem/loader stack writes are outside
        # this schedule probe and retain their ordinary HostFixture execution.
        self.u.hook_add(UC_HOOK_MEM_WRITE,self.on_write,begin=CACHE,end=CACHE+3*STRIDE-1)
        self.metadata=metadata
    on_write=CacheFixture.on_write
    indices=CacheFixture.indices
    base=CacheFixture.base
    data=CacheFixture.data
    put=CacheFixture.put
    def read(self,p):return int.from_bytes(self.u.mem_read(p,4),'little')
    def write(self,p,v):self.u.mem_write(p,struct.pack('<I',v))
    def hook(self,u,address,size,context):
        if self.pause_validate and address==(self.report['symbols']['z7_native_cache_snapshot_valid']&~1):
            self.pause_validate=False;u.emu_stop();return
        if self.pause_copy and 0<self.copied<36:
            self.pause_copy=False;u.emu_stop();return
        super().hook(u,address,size,context)
    def load(self):
        if self.call(self.report['symbols']['z7_module_load_once'],STATE)!=8:raise AssertionError('API80 probe load')
        self.module_base=self.words()[12]
    def api(self,op,output=1,pointer=SNAPSHOT):
        return self.call(self.module_base+self.metadata['symbols']['z7_cache_probe_operation'],op,output,pointer)
    def observation(self):return struct.unpack('<4I',self.u.mem_read(STATE+336,16))
    def snapshot(self):return bytes(self.u.mem_read(SNAPSHOT,44))


def audit(raw,host,stock,packet,module):
    checks=[]
    def check(n,good):
        checks.append(dict(name=n,passed=bool(good)))
        if not good:raise AssertionError(n)
    f=CacheHostFixture(raw,host,packet,module);f.load();f.indices(0,1,2)
    api=struct.unpack('<3I',f.u.mem_read(f.module_base+module['symbols']['z7_cache_probe_api'],12))
    check('loaded-sdk-probe-receives-api80-compatible-prefix-and-correct-function-pointers',api==(host.get('api_bytes',80),host['symbols']['z7_native_cache_snapshot'],host['symbols']['z7_native_cache_snapshot_valid']))
    f.u.mem_write(SNAPSHOT,b'\xa5'*44)
    check('unobserved-cache-does-not-establish-ready-baseline',f.api(1)==0 and f.snapshot()==b'\xa5'*44)
    baseline=CacheFixture(stock);baseline.indices(0,1,2)
    # Compare original full writer effects, not only the copied request. Keep
    # the same incoming caller-scratch register and flags in both machines.
    for mask in range(8):
        for pattern in (0,1,2):
            for bank in range(3):
                for fixture in (f,baseline):fixture.u.mem_write(fixture.base(bank),b'\x6b'*STRIDE)
            data=request(4,pattern,213)
            states=[]
            for fixture in (baseline,f):
                fixture.u.reg_write(UC_ARM_REG_R12,0x1234abcd)
                fixture.u.reg_write(UC_ARM_REG_CPSR,(fixture.u.reg_read(UC_ARM_REG_CPSR)&~0xf8000000)|0xa8000000)
                result=fixture.put(mask,data)
                states.append((result,fixture.u.reg_read(UC_ARM_REG_CPSR)&0xf8000000,
                               tuple(fixture.u.reg_read(reg) for reg in (UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R12))))
            check(f'writer-mask{mask}-pattern{pattern}-matches-original-all-bank-bytes',bytes(f.u.mem_read(CACHE,3*STRIDE))==bytes(baseline.u.mem_read(CACHE,3*STRIDE)))
            check(f'writer-mask{mask}-pattern{pattern}-matches-original-return-flags-and-caller-scratch',states[0]==states[1])
    del baseline;gc.collect()
    for output,bank in ((1,0),(4,2)):
        data=request(output,2,180);f.put(output,data)
        check(f'output{output}-sdk-snapshot-copies-complete-native-request-and-generation',f.api(1,output)==1 and f.snapshot()[:36]==data and struct.unpack_from('<2I',f.snapshot(),36)==(f.observation()[1],bank) and f.api(2,output)==1)
        f.put(output,request(output,1,248))
        check(f'output{output}-later-native-copy-invalidates-old-sdk-snapshot',f.api(2,output)==0)
    for output in (0,2,3,0xffffffff):
        f.u.mem_write(SNAPSHOT,b'\xa5'*44)
        check(f'unsupported-output{output}-leaves-snapshot-output-unchanged',f.api(1,output)==0 and f.snapshot()==b'\xa5'*44)
    check('null-and-misaligned-sdk-output-rejected',f.api(1,1,0)==0 and f.api(1,1,SNAPSHOT+1)==0 and f.api(2,1,0)==0)
    f.indices(2,1,0);f.u.mem_write(SNAPSHOT,b'\xa5'*44)
    check('unexpected-bank-index-mapping-refuses-snapshot',f.api(1,1)==0 and f.api(1,4)==0 and f.snapshot()==b'\xa5'*44)
    f.indices(0,1,2)
    # Snapshot starts first, then a complete writer runs before validation.
    # The staged old bytes must never leak into the caller's output buffer.
    f.u.mem_write(SNAPSHOT,b'\xa5'*44);f.pause_validate=True
    guards=enter(f,f.module_base+module['symbols']['z7_cache_probe_operation'],(1,1,SNAPSHOT),CALLER_STACK)
    check('snapshot-pauses-after-copy-before-final-validation',f.u.reg_read(UC_ARM_REG_PC)==(host['symbols']['z7_native_cache_snapshot_valid']&~1) and f.snapshot()==b'\xa5'*44)
    context=f.u.context_save();f.put(1,request(1,2,202));f.u.context_restore(context);resume(f)
    check('native-write-during-snapshot-invalidates-staged-copy-without-output-mutation',returned(f,CALLER_STACK,guards) and f.u.reg_read(UC_ARM_REG_R0)==0 and f.snapshot()==b'\xa5'*44)
    check('snapshot-retry-after-native-write-observes-new-complete-request',f.api(1,1)==1 and f.snapshot()[:36]==request(1,2,202))
    snapshot=f.snapshot();f.write(SNAPSHOT+40,2)
    check('sdk-validation-rejects-tampered-bank',f.api(2,1)==0)
    f.u.mem_write(SNAPSHOT,snapshot);f.write(SNAPSHOT+36,f.read(SNAPSHOT+36)+1)
    check('sdk-validation-rejects-tampered-generation',f.api(2,1)==0)
    f.put(1,request(1,2,224));f.api(1,1);before=f.snapshot();f.write(0xa24e1e00,1)
    check('movie-mode-refuses-photo-snapshot-without-output-mutation',f.api(1,1)==0 and f.api(2,1)==0 and f.snapshot()==before)
    f.put(1,request(1,1,180));f.write(0xa24e1e00,0)
    check('movie-cache-copy-is-not-reused-as-photo-baseline-after-mode-return',f.api(1,1)==0 and f.observation()[3]&1==0)
    f.put(1,request(1,2,235))
    check('fresh-photo-copy-readmits-photo-snapshot',f.api(1,1)==1 and f.snapshot()[:36]==request(1,2,235))
    for start_mode,end_mode in ((0,1),(1,0)):
        f.write(0xa24e1e00,start_mode);f.u.mem_write(MEM+0x1000,request(1,1,202))
        f.watch=f.base(0)+REQUEST_OFFSET;f.copied=0;f.pause_copy=True
        guards=enter(f,WRITER,(1,0,MEM+0x1000,0),CALLER_STACK)
        context=f.u.context_save();f.write(0xa24e1e00,end_mode);f.u.context_restore(context);resume(f)
        f.write(0xa24e1e00,0)
        check(f'copy-spanning-mode{start_mode}-to{end_mode}-does-not-publish-photo-ready',returned(f,CALLER_STACK,guards) and f.observation()[3]&1==0 and f.api(1,1)==0)
        f.put(1,request(1,2,235))
    # Constructor's nonzero first field /zero second field exercises the extra
    # displaced load in its unaligned ten-byte jump window without GPU calls.
    for output,bank in ((1,0),(4,2)):
        for first in (0,1):
            config=bytearray(0x5c);struct.pack_into('<I',config,0,first)
            data=request(output,2,191);config[0x38:0x5c]=data
            f.u.mem_write(MEM+0x3000,bytes(config));f.u.mem_write(MEM+0x2000,bytes(12));f.write(STACK,MEM+0x3000)
            check(f'constructor-output{output}-first-field{first}-preserves-native-return-and-publishes-complete-cache',f.call(CONSTRUCTOR,output,0,MEM+0x2000,0)==1 and f.data(bank)==data and f.api(1,output)==1 and f.snapshot()[:36]==data)
    for writer in ('setter','constructor'):
        for output,bank in ((1,0),(4,2)):
            old=request(output,1,248);new=request(output,2,180)
            f.put(output,old);check(f'{writer}-output{output}-captures-prior-ticket',f.api(1,output)==1)
            old_snapshot=f.snapshot()
            if writer=='setter':
                f.u.mem_write(MEM+0x1000,new);entry,args=WRITER,(output,0,MEM+0x1000,0)
            else:
                config=bytearray(0x5c);config[0x38:0x5c]=new
                f.u.mem_write(MEM+0x3000,bytes(config));f.write(CALLER_STACK,MEM+0x3000)
                entry,args=CONSTRUCTOR,(output,0,MEM+0x2000,0)
            f.watch=f.base(bank)+REQUEST_OFFSET;f.copied=0;f.pause_copy=True
            guards=enter(f,entry,args,CALLER_STACK)
            check(f'{writer}-output{output}-real-bridge-owns-incomplete-native-copy',f.copied==16 and f.observation()[0]==1 and not returned(f,CALLER_STACK,guards))
            context=f.u.context_save();before=f.snapshot()
            check(f'{writer}-output{output}-sdk-rejects-partial-copy-without-output-mutation',f.api(1,output)==0 and f.snapshot()==before and f.api(2,output)==0)
            # A second actual native writer overlaps while the first is paused.
            # Each native caller owns its request until its synchronous copy
            # returns. Do not overwrite the first writer's paused source.
            f.u.mem_write(MEM+0x4000,request(2,2,202))
            f.call(WRITER,2,0,MEM+0x4000,0)
            check(f'{writer}-output{output}-overlapping-other-output-copy-does-not-admit-snapshot',f.observation()[0]==1 and f.api(1,output)==0)
            f.u.context_restore(context);resume(f)
            check(f'{writer}-output{output}-real-bridge-retires-after-complete-native-copy',returned(f,CALLER_STACK,guards) and f.observation()[0]==0 and f.api(1,output)==1 and f.snapshot()[:36]==new and f.snapshot()!=old_snapshot)
    f.setword(344,1);f.u.mem_write(SNAPSHOT,b'\xa5'*44)
    check('halted-observation-leaves-snapshot-output-unchanged',f.api(1,1)==0 and f.snapshot()==b'\xa5'*44)
    data=request(4,2,224);f.put(4,data)
    check('halted-observation-keeps-original-native-copy-behavior',f.data(2)==data and f.observation()[0]==0)
    del f;gc.collect()
    for serial in (0xfffffffe,0xffffffff):
        f=CacheHostFixture(raw,host,packet,module);f.load();f.indices(0,1,2);f.setword(340,serial)
        data=request(1,2,213);f.put(1,data)
        check(f'serial{serial}-exhaustion-does-not-wrap-or-skip-native-copy',f.observation()[:3]==(0,0xffffffff,1) and f.data(0)==data and f.api(1,1)==0)
        del f;gc.collect()
    f=CacheHostFixture(raw,host,packet,module);f.load();f.indices(0,1,2);f.setword(336,0xffffffff)
    data=request(1,2,213);f.put(1,data)
    check('active-counter-exhaustion-preserves-native-copy-without-wrap',f.observation()[:3]==(0xffffffff,0,1) and f.data(0)==data and f.api(1,1)==0)
    del f;gc.collect()
    f=CacheHostFixture(raw,host,packet,module);f.load();f.indices(0,1,2);f.setword(352,0)
    data=request(4,2,235);f.put(4,data)
    check('bad-state-guard-refuses-observation-with-native-copy-fallback',f.api(1,4)==0 and f.data(2)==data)
    del f;gc.collect()
    f=CacheHostFixture(raw,host,packet,module)
    f.u.mem_write(STATE+336,b'\x5a'*24)
    check('actual-cold-workspace-hook-clears-observation-and-reserves384',f.call(0x101e3d94)==STATE and f.read(CURSOR)==STATE+384 and f.observation()==(0,0,0,0) and f.read(STATE+352)==f.read(STATE+356)==0xa5a5a5a5)
    check('cold-hook-preserves-native-continuation-registers-and-flags',f.heap_observation==dict(r0=STATE,r1=CURSOR,r2=0x22334455,r3=0x66778899,flags=0xf8000000))
    return dict(passed=True,checks=checks,host_sha256=host['main_payload_sha256'],loaded_sdk_probe_sha256=hashlib.sha256(packet).hexdigest(),
                actual_copy_bridges_constructor_setter_getter_memcpy_and_sdk_calls_execute=True,
                copy_begin_end_photo_mode_source_tracking_checked=True,
                kernel_filesystem_bank_indices_and_task_schedule_supplied=True,
                full_native_boot_pre_cold_writer_closure_index_aba_bank_lifetime_or_apply_atomicity_proven=False,
                automatic_no_native_update_display_handoff_implemented=False,camera_card_access=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True);p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private output directory')
    stock=a.stock_main.read_bytes();host=json.loads((a.build/'module-host.emulator.json').read_text(encoding='utf-8'));raw=(a.build/'module-host.emulator.main.bin').read_bytes()
    if (hashlib.sha256(stock).hexdigest()!=STOCK_SHA or hashlib.sha256(raw).hexdigest()!=host['main_payload_sha256'] or
        not host.get('native_cache_copy_hooks') or not host.get('native_cache_photo_copies_only')):p.error('Exact stock MAIN and photo-source-tracked cache-copy host required')
    source=ROOT/'z7-native-modules/examples/native_cache_probe.c';packet,module=build(source,zig=ZIG);again,repeated=build(source,zig=ZIG)
    if packet!=again or module!=repeated:raise AssertionError('SDK probe must build reproducibly')
    result=audit(raw,host,stock,packet,module)
    names={*host['source_files'],'tools/audit_z7_native_cache_host.py','tools/audit_z7_module_host.py','tools/build_z7_module_host.py',
           'tools/audit_z7_highlight_native_cache.py','tools/audit_z7_cache_observation.py','tools/audit_z7_highlight_submission.py',
           'tools/audit_z7_highlight_converter.py','tools/audit_splash_image.py','z7-native-modules/examples/native_cache_probe.c'}
    result['source_sha256']={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in sorted(names)}
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(packet)
    (out/'probe.json').write_text(json.dumps(module,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),probe_bytes=len(packet))))


if __name__=='__main__':main()
