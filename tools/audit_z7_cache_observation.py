"""Compiled observation core against native setter/constructor partial copies.

SPDX-License-Identifier: MIT. Observation begin/end boundaries and schedules are
supplied by this audit; firmware bridges and complete writer closure are absent.
Native cache copies and compiled atomic observation instructions execute.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_CPSR, UC_ARM_REG_R0
from audit_splash_image import MEM, STOCK_SHA, STOP
from audit_z7_highlight_native_cache import CacheFixture, GETTER, WRITER, CALLER_STACK, REQUEST_OFFSET
from audit_z7_highlight_converter import request
from audit_z7_highlight_submission import enter, returned
from build_z7_module import build, HEADER
from build_z7_module_host import ROOT, ZIG

PROBE, OBSERVATION, TICKET = MEM+0x10000, MEM+0x20000, MEM+0x21000
CONSTRUCTOR, MEMCPY = 0x10433c78, 0x10170a1c


def resume(f):
    f.u.emu_start(f.u.reg_read(UC_ARM_REG_PC) | ((f.u.reg_read(UC_ARM_REG_CPSR)>>5)&1),
                  STOP,timeout=10000000,count=10000000)


class ObservationFixture(CacheFixture):
    def __init__(self, raw, packet, metadata):
        self.stop_copy_entry=False
        super().__init__(raw)
        # This is a flat, zero-relocation pure-core instruction probe. It does
        # not exercise the module host loader or claim installation validation.
        if metadata['relocations']: raise AssertionError('Unexpected probe relocation')
        self.u.mem_write(PROBE,packet[HEADER:HEADER+metadata['image_bytes']])
        self.operation=PROBE+metadata['symbols']['z7_cache_operation']
    def hook(self,u,address,size,context):
        if self.stop_copy_entry and address==MEMCPY and u.reg_read(UC_ARM_REG_R0)==self.watch:
            self.stop_copy_entry=False;u.emu_stop();return
        super().hook(u,address,size,context)
    def op(self,op,token=0): return self.call(self.operation,op,OBSERVATION,token,TICKET)
    def write(self,address,value):self.u.mem_write(address,struct.pack('<I',value))
    def read(self,address):return int.from_bytes(self.u.mem_read(address,4),'little')
    def reset(self,active=0,serial=0,halted=0):
        self.u.mem_write(OBSERVATION,struct.pack('<3I',active,serial,halted))
        self.write(TICKET,0xa5a5a5a5)
    def state(self):return struct.unpack('<3I',self.u.mem_read(OBSERVATION,12))


def audit(raw,packet,metadata):
    checks=[]
    def check(n,good):
        checks.append(dict(name=n,passed=bool(good)))
        if not good:raise AssertionError(n)
    f=ObservationFixture(raw,packet,metadata);f.reset()
    check('idle-zero-ticket-is-valid',f.op(3)==1 and f.read(TICKET)==0 and f.op(4,0)==1)
    check('first-writer-begins-without-waiting-for-readers',f.op(1)==1 and f.state()==(1,1,0))
    f.write(TICKET,0xa5a5a5a5)
    check('active-writer-rejects-ticket-without-output-mutation',f.op(3)==0 and f.read(TICKET)==0xa5a5a5a5 and f.op(4,0)==0)
    check('overlapping-writers-reject-even-serial',f.op(1)==1 and f.state()==(2,2,0) and f.op(3)==0 and f.op(4,2)==0)
    f.op(2,1)
    check('first-overlapping-writer-retirement-keeps-readers-out',f.state()==(1,3,0) and f.op(3)==0)
    f.op(2,1)
    check('last-writer-retirement-permits-new-ticket',f.state()==(0,4,0) and f.op(3)==1 and f.read(TICKET)==4)
    check('completed-write-invalidates-earlier-ticket',f.op(4,0)==0 and f.op(4,4)==1)
    f.op(2,0)
    check('zero-token-retirement-is-inert',f.state()==(0,4,0))
    f.op(2,1)
    check('unbalanced-retirement-halts-observation',f.state()[2]==1 and f.op(3)==0)
    f.reset();f.op(2,2)
    check('invalid-token-halts-observation',f.state()==(0,0,1) and f.op(1)==0)
    f.reset(active=0xffffffff)
    check('active-counter-exhaustion-does-not-wrap',f.op(1)==0 and f.state()==(0xffffffff,0,1) and f.op(3)==0)
    for serial in (0xfffffffe,0xffffffff):
        f.reset(serial=serial)
        check(f'serial-{serial}-writer-still-receives-balanced-retirement-token',f.op(1)==1 and f.state()[0]==1)
        f.op(2,1)
        check(f'serial-{serial}-exhaustion-halts-without-counter-reuse',f.state()==(0,0xffffffff,1) and f.op(3)==0 and f.op(4,0xffffffff)==0)

    for writer in ('setter','constructor'):
        for output,bank in ((1,0),(4,2)):
            f.reset();f.indices(0,1,2)
            old=request(output,1,248);new=request(output,2,180)
            f.put(output,old);f.watch=f.base(bank)+REQUEST_OFFSET;f.copied=0
            if writer=='setter':
                f.u.mem_write(MEM+0x1000,new)
                entry,args=WRITER,(output,0,MEM+0x1000,0)
            else:
                config=bytearray(0x5c);config[0x38:0x5c]=new
                f.u.mem_write(MEM+0x3000,bytes(config));f.u.mem_write(MEM+0x2000,bytes(12))
                f.write(CALLER_STACK,MEM+0x3000)
                entry,args=CONSTRUCTOR,(output,0,MEM+0x2000,0)
            f.stop_copy_entry=True
            guards=enter(f,entry,args,CALLER_STACK)
            check(f'{writer}-output{output}-stops-before-actual-request-copy',f.copied==0 and f.u.reg_read(UC_ARM_REG_PC)==MEMCPY)
            context=f.u.context_save()
            check(f'{writer}-output{output}-precopy-ticket',f.op(3)==1 and f.read(TICKET)==0)
            check(f'{writer}-output{output}-begin-observation',f.op(1)==1)
            f.u.context_restore(context);f.pause_copy=True;resume(f)
            check(f'{writer}-output{output}-actual-native-copy-pauses-after16-stored-bytes',f.copied==16 and not returned(f,CALLER_STACK,guards))
            context=f.u.context_save()
            pointer=f.call(GETTER,output,0,0)
            a=bytes(f.u.mem_read(pointer,36));b=bytes(f.u.mem_read(pointer,36))
            check(f'{writer}-output{output}-uncoordinated-equal-reads-are-torn',a==b and a!=old and a!=new)
            check(f'{writer}-output{output}-compiled-observer-rejects-torn-read-and-old-ticket',f.op(3)==0 and f.op(4,0)==0)
            f.u.context_restore(context);resume(f)
            check(f'{writer}-output{output}-native-writer-completes-with-original-guards',returned(f,CALLER_STACK,guards) and f.data(bank)==new)
            f.op(2,1)
            check(f'{writer}-output{output}-completed-snapshot-admitted-with-new-generation',f.op(3)==1 and f.read(TICKET)==2 and f.op(4,2)==1)
    f.reset(halted=1);f.put(4,request(4,2,191))
    check('halted-observation-does-not-block-original-native-cache-writer',f.op(1)==0 and f.data(2)==request(4,2,191) and f.op(3)==0)
    return dict(passed=True,checks=checks,compiled_observation_and_native_copy_instructions_execute=True,
                observation_boundaries_and_task_schedules_supplied=True,flat_probe_loader_validation_exercised=False,
                setter_and_constructor_partial_request_reads_rejected=True,
                native_writer_exclusion_or_later_apply_atomicity_proven=False,
                firmware_copy_bridges_all_writer_closure_bank_lifetime_or_boot_activation_proven=False,
                automatic_no_native_update_handoff_implemented=False,camera_card_access=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private output directory')
    raw=a.stock_main.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=STOCK_SHA:p.error('Exact stock MAIN required')
    source=ROOT/'z7-native-modules/examples/cache_observation_probe.c'
    packet,metadata=build(source,zig=ZIG);again,repeated=build(source,zig=ZIG)
    if packet!=again or metadata!=repeated:raise AssertionError('Probe must build reproducibly')
    result=audit(raw,packet,metadata)
    names=('z7-native-modules/plugins/cache_observation.h','z7-native-modules/examples/cache_observation_probe.c',
           'tools/audit_z7_cache_observation.py','tools/audit_z7_highlight_native_cache.py','tools/audit_z7_highlight_converter.py',
           'tools/audit_z7_highlight_submission.py','tools/audit_splash_image.py','tools/audit_z7_display_parameters.py',
           'tools/build_z7_module.py','z7-native-modules/sdk/module.h','z7-native-modules/sdk/module.ld')
    result.update(stock_main_sha256=STOCK_SHA,probe_sha256=hashlib.sha256(packet).hexdigest(),reproducible=True,
                  source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(packet)
    (out/'probe.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),probe_bytes=len(packet))))


if __name__=='__main__':main()
