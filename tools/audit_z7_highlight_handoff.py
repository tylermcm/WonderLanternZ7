"""Cache-driven logical LCD/EVF handoff without native parameter packets.

SPDX-License-Identifier: MIT. Compiled module and native cache/converter/consumer/
source/frame/gate/driver execute. Engine, UI/FS/kernel and schedules supplied.
No full native boot/writer/index/lifetime closure or physical pixels proof.
"""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import struct
from unicorn import UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_PC

from audit_splash_image import STOCK_SHA
from audit_z7_highlight_evf import EVFFixture
from audit_z7_highlight_converter import request
from audit_z7_highlight_native_cache import WRITER, CACHE, STRIDE
from audit_z7_parameters import NATIVE
from audit_z7_frame_permission import FRAME
from build_z7_module_host import ROOT
from build_z7_module_host import STATE
from audit_z7_highlight_submission import enter, returned
from audit_z7_cache_observation import resume, CONSTRUCTOR
from audit_z7_parameters import CALLER_STACK


class HandoffFixture(EVFFixture):
    def __init__(self,*args):
        self.pause_cache=False;self.cache_copied=0;self.cache_watch=0
        super().__init__(*args)
        self.u.mem_map(0xa1f19000,0x4000)
        for output,bank in ((1,0),(2,1),(4,2)):
            self.u.mem_write(0xa180f274+output,bytes([bank]))
        self.u.hook_add(UC_HOOK_MEM_WRITE,self.cache_store,begin=CACHE,end=CACHE+3*STRIDE-1)
    def cache_store(self,u,access,address,size,value,context):
        if self.cache_watch<=address<self.cache_watch+36:self.cache_copied+=size
    def hook(self,u,address,size,context):
        if self.pause_cache and 0<self.cache_copied<36:
            self.pause_cache=False;u.emu_stop();return
        super().hook(u,address,size,context)
    def cache_put(self,selector,pattern,threshold):
        output=4 if selector else 1
        self.u.mem_write(NATIVE+0x7000,request(output,pattern,threshold))
        self.call(WRITER,output,0,NATIVE+0x7000,0)
    def settle(self):
        self.worker()
        if self.read(self.address('z7_highlight_owned_request')+132)==2:
            result=self.dispatch();self.worker();return result
        return None
    def origin_baseline(self,selector):
        # Extended record300 +publication12; baseline keeps its prefix offset60.
        return bytes(self.u.mem_read(self.address('z7_highlight_native_origins')+selector*312+60,100))
    def pause_writer(self,selector,pattern,threshold):
        output=4 if selector else 1
        self.u.mem_write(NATIVE+0x7100,request(output,pattern,threshold))
        self.cache_watch=CACHE+(2 if selector else 0)*STRIDE+0x58
        self.cache_copied=0;self.pause_cache=True
        guards=enter(self,WRITER,(output,0,NATIVE+0x7100,0),CALLER_STACK)
        if self.cache_copied!=16:raise AssertionError('Native cache partial-copy boundary')
        return self.u.context_save(),guards
    def resume_writer(self,context,guards):
        self.u.context_restore(context);resume(self)
        return returned(self,CALLER_STACK,guards)


def audit(raw,host,packet,module):
    checks=[]
    def check(n,good):
        checks.append(dict(name=n,passed=bool(good)))
        if not good:raise AssertionError(n)
    f=HandoffFixture(raw,host,packet,module);f.load()
    f.call(host['symbols']['z7_display_before_update']);f.gui();f.worker()
    check('unobserved-cache-and-no-foreign-origin-do-not-claim-shared-state',not f.queued and f.lease()==0)
    f.cache_put(0,2,224);f.cache_put(1,2,235)
    lcd=f.convert_output(0,2,224);evf=f.convert_output(1,2,235)
    check('native-cache-writes-do-not-submit-native-display-parameter-packets',not f.queued and f.value('z7_highlight_native_parameter_generation')==0)
    f.gui()
    check('lcd-owned-apply-starts-from-native-cache-without-native-parameter-update',f.settle()==1 and f.parameters()==f.convert_output(0,1,248) and f.origin_baseline(0)==lcd)
    f.write(FRAME+0x34,0)
    check('lcd-native-source-enables-owned-plane',f.present(0)==1 and f.control()&1==1)
    f.select(1);f.gui()
    check('switch-to-evf-disables-old-owned-plane-first',f.settle()==1 and f.read(NATIVE+0x28)==0 and f.control()&1==0 and f.lease(28)==1)
    check('next-worker-applies-evf-from-own-native-cache-without-parameter-update',f.settle()==1 and f.lease(40)==1 and f.parameters()==f.convert_output(1,1,248) and f.origin_baseline(1)==evf)
    check('evf-native-frame-enables-owned-plane-after-cache-handoff',f.present(1)==1 and f.control()&1==1)
    for pattern in (1,2):
        for index,threshold in enumerate((255,248,235,224,213,202,191,180)):
            f.choose(pattern,index);f.gui()
            check(f'cache-owned-evf-pattern{pattern}-threshold{threshold}-uses-native-output4-converter',
                  f.settle()==1 and f.parameters()==f.convert_output(1,pattern,threshold) and f.origin_baseline(1)==evf)
            f.present(1)
    f.choose(0,1);f.gui()
    check('evf-off-restores-own-native-baseline',f.settle()==1 and f.parameters()==evf and f.lease()==0 and f.control()&1==0)
    f.choose(1,1);f.gui();f.settle();f.present(1)
    f.select(0);f.gui();f.settle()
    check('return-to-lcd-applies-without-native-parameter-update',f.settle()==1 and f.lease(40)==0 and f.parameters()==f.convert_output(0,1,248) and f.origin_baseline(0)==lcd)
    f.present(0);f.choose(0,1);f.gui()
    check('lcd-off-restores-own-baseline-after-two-output-round-trip',f.settle()==1 and f.parameters()==lcd and f.lease()==0 and f.control()&1==0)
    check('whole-cache-driven-round-trip-used-no-foreign-parameter-update',f.value('z7_highlight_native_parameter_generation')==0 and f.value('z7_highlight_parameter_count')==0)
    del f;gc.collect()
    f=HandoffFixture(raw,host,packet,module)
    # Actual cache constructor copies can precede module loading. Native boot
    # ordering is still supplied, rather than inferred from this call sequence.
    for selector in (0,1):
        output=4 if selector else 1
        config=bytearray(0x5c);config[0x38:0x5c]=request(output,2,224 if not selector else 235)
        f.u.mem_write(NATIVE+0x7300,bytes(config));f.u.mem_write(NATIVE+0x7200,bytes(12))
        f.write(0x503f0000,NATIVE+0x7300)
        check(f'constructor-output{output}-can-publish-before-module-load',f.call(CONSTRUCTOR,output,0,NATIVE+0x7200,0)==1)
    f.load();f.call(host['symbols']['z7_display_before_update']);f.gui()
    check('pre-module-native-constructor-cache-admits-initial-owned-lcd',f.settle()==1 and f.origin_baseline(0)==f.convert_output(0,2,224))
    f.write(FRAME+0x34,0);f.present(0)
    f.cache_put(0,1,202)
    check('cache-only-update-inhibits-owned-frame-before-worker-refresh',f.present(0)==1 and f.control()&1==0)
    check('cache-only-update-refreshes-restoration-baseline-without-gui-or-native-packet',f.settle()==1 and f.origin_baseline(0)==f.convert_output(0,1,202))
    old_baseline=f.origin_baseline(0)
    f.u.mem_write(NATIVE+0x5000,struct.pack('<256I',*[(255-i)<<24|i for i in range(256)]));f.write(0xa1f18fac,NATIVE+0x5000)
    check('palette-change-reconverts-cache-derived-baseline',f.settle()==1 and f.origin_baseline(0)==f.convert_output(0,1,202) and f.origin_baseline(0)!=old_baseline)
    f.present(0);f.choose(0,1);f.gui()
    check('off-restores-latest-cache-only-native-preference',f.settle()==1 and f.parameters()==f.convert_output(0,1,202) and f.lease()==0 and f.control()&1==0)
    check('cache-refresh-path-still-has-no-foreign-parameter-update',f.value('z7_highlight_native_parameter_generation')==0)
    f.u.mem_write(NATIVE+0x7000,bytes(4)+b'\xa5'*32);f.call(WRITER,1,0,NATIVE+0x7000,0)
    f.choose(1,1);f.gui()
    check('disabled-native-cache-ignores-undefined-request-tail',f.settle()==1 and f.origin_baseline(0)==bytes(100))
    f.present(0);f.choose(0,1);f.gui()
    check('off-restores-normalized-disabled-cache-baseline',f.settle()==1 and f.parameters()==bytes(100) and f.lease()==0 and f.control()&1==0)
    del f;gc.collect()

    f=HandoffFixture(raw,host,packet,module);f.load();f.cache_put(0,2,224);f.cache_put(1,2,235)
    f.call(host['symbols']['z7_display_before_update']);f.gui()
    foreign_lcd=f.convert_output(0,1,202);f.native_output(0,foreign_lcd)
    f.write(FRAME+0x34,0);f.present(0)
    check('foreign-native-baseline-remains-exact-even-when-different-from-cache',f.origin_baseline(0)==foreign_lcd)
    f.cache_put(1,1,224)
    check('other-bank-cache-write-refreshes-ticket-without-replacing-foreign-lcd-baseline',f.settle()==1 and f.origin_baseline(0)==foreign_lcd)
    f.u.mem_write(NATIVE+0x5000,struct.pack('<256I',*[(255-i)<<24|i for i in range(256)]));f.write(0xa1f18fac,NATIVE+0x5000)
    check('palette-change-preserves-exact-foreign-native-baseline',f.settle()==1 and f.origin_baseline(0)==foreign_lcd)
    f.select(1);f.gui();f.settle();f.settle();f.present(1)
    foreign_evf=f.convert_output(1,2,180);f.native_output(1,foreign_evf);f.present(1)
    check('evf-foreign-native-baseline-is-kept-separately',f.origin_baseline(1)==foreign_evf and f.origin_baseline(0)==foreign_lcd)
    f.select(0);f.gui();f.settle()
    check('lcd-return-retains-foreign-baseline-despite-other-output-native-generation',f.settle()==1 and f.origin_baseline(0)==foreign_lcd)
    f.present(0);f.choose(0,1);f.gui()
    check('round-trip-off-restores-foreign-lcd-baseline-exactly',f.settle()==1 and f.parameters()==foreign_lcd)
    del f;gc.collect()

    f=HandoffFixture(raw,host,packet,module);f.load();f.cache_put(0,2,224);f.cache_put(1,2,235)
    f.call(host['symbols']['z7_display_before_update']);f.gui();f.settle();f.write(FRAME+0x34,0);f.present(0)
    # Change global preference and output together while the old plane is owned.
    f.choose(0,1);f.select(1);f.gui()
    check('off-destination-handoff-first-disables-old-owned-plane',f.settle()==1 and f.control()&1==0 and f.lease(28)==1)
    check('off-destination-handoff-restores-target-native-baseline-and-relinquishes',f.settle()==1 and f.parameters()==f.convert_output(1,2,235) and f.lease()==0)
    f.write(FRAME+0x34,1)
    check('off-destination-subsequent-frame-keeps-native-warning-permission',f.present(1)==1 and f.control()&1==1)
    del f;gc.collect()

    f=HandoffFixture(raw,host,packet,module);f.load();f.cache_put(0,2,224);f.cache_put(1,2,235)
    f.call(host['symbols']['z7_display_before_update']);f.gui();f.settle();f.write(FRAME+0x34,0);f.present(0)
    context,guards=f.pause_writer(0,1,202)
    check('actual-native-partial-cache-write-immediately-inhibits-owned-frame',f.present(0)==1 and f.control()&1==0)
    check('worker-can-disable-owned-parameters-while-cache-writer-is-busy',f.settle()==1 and f.lease(28)==1 and f.read(NATIVE+0x28)==0)
    queued=len(f.queued);f.worker();f.worker()
    check('busy-cache-does-not-create-repeated-apply-or-stale-restore',len(f.queued)==queued and f.origin_baseline(0)==f.convert_output(0,2,224))
    check('native-cache-writer-resumes-with-original-stack-and-register-guards',f.resume_writer(context,guards))
    check('worker-recovers-owned-highlight-and-new-baseline-after-cache-copy-finishes',f.settle()==1 and f.parameters()==f.convert_output(0,1,248) and f.origin_baseline(0)==f.convert_output(0,1,202))
    f.present(0);f.choose(0,1);f.gui()
    check('recovered-cache-busy-off-restores-completed-native-request',f.settle()==1 and f.parameters()==f.convert_output(0,1,202) and f.control()&1==0)
    f.choose(1,1);f.gui();f.settle();f.present(0)
    context,guards=f.pause_writer(0,2,191);f.choose(0,1);f.gui()
    check('off-during-partial-cache-write-disables-before-restoration',f.settle()==1 and f.lease(28)==1 and f.read(NATIVE+0x28)==0 and f.control()&1==0)
    check('off-during-partial-cache-write-native-producer-resumes',f.resume_writer(context,guards))
    check('pending-off-restores-completed-cache-baseline-without-gui-or-native-packet',f.settle()==1 and f.parameters()==f.convert_output(0,2,191) and f.lease()==0 and f.control()&1==0)
    del f;gc.collect()

    f=HandoffFixture(raw,host,packet,module);f.load();f.cache_put(0,2,224)
    f.call(host['symbols']['z7_display_before_update']);f.gui();f.worker();before=f.parameters()
    context,guards=f.pause_writer(0,1,191)
    check('queued-apply-cancels-before-copy-while-native-cache-is-incomplete',f.dispatch()==0 and f.parameters()==before and f.lease()==0)
    f.worker();check('cancelled-apply-native-writer-resumes',f.resume_writer(context,guards))
    check('queued-apply-retries-with-completed-latest-cache-baseline',f.settle()==1 and f.origin_baseline(0)==f.convert_output(0,1,191))
    f.cache_put(0,1,202);f.worker();f.cache_put(0,2,224)
    check('cache-change-after-queue-uses-latest-complete-baseline-at-consumer',f.dispatch()==1 and f.origin_baseline(0)==f.convert_output(0,2,224))
    f.worker()
    del f;gc.collect()

    f=HandoffFixture(raw,host,packet,module);f.load();f.cache_put(0,2,224)
    f.call(host['symbols']['z7_display_before_update']);f.gui();f.settle();f.write(FRAME+0x34,0);f.present(0)
    f.write(STATE+340,0xffffffff);f.cache_put(0,1,202)
    check('actual-native-cache-counter-exhaustion-inhibits-cache-owned-frame',f.present(0)==1 and f.control()&1==0 and f.read(STATE+344)==1)
    check('exhausted-cache-observation-drains-owned-override-without-stale-restoration',f.settle()==1 and f.lease(28)==1 and f.read(NATIVE+0x28)==0 and f.control()&1==0)
    queued=len(f.queued);f.worker();f.worker()
    check('exhausted-cache-observation-does-not-retry-untrusted-baseline',len(f.queued)==queued)
    f.choose(0,1);f.gui();native=f.convert_output(0,1,202);f.native_output(0,native)
    check('fresh-native-parameter-update-after-cache-halt-retains-native-ownership',f.parameters()==native and f.lease()==0 and f.control()&1==0)
    del f;gc.collect()

    f=HandoffFixture(raw,host,packet,module);f.load();f.cache_put(0,2,224)
    f.call(host['symbols']['z7_display_before_update']);f.gui();f.settle();f.write(FRAME+0x34,0);f.present(0)
    f.write(0xa24e1e00,1);f.u.mem_write(0xa201d4d0+0x40,b'\x01')
    f.call(host['symbols']['z7_display_before_update']);f.gui()
    check('movie-departure-disables-photo-owned-plane',f.settle()==1 and f.lease(28)==1 and f.control()&1==0)
    f.cache_put(0,1,180)
    f.write(0xa24e1e00,0);f.u.mem_write(0xa201d4d0+0x40,b'\x00')
    f.call(host['symbols']['z7_display_before_update']);f.gui();queued=len(f.queued);f.worker();f.worker()
    check('photo-return-does-not-import-native-cache-written-in-movie-mode',len(f.queued)==queued and f.read(NATIVE+0x28)==0 and f.lease(28)==1)
    f.cache_put(0,2,202)
    check('fresh-photo-cache-copy-recovers-without-foreign-parameter-packet',f.settle()==1 and f.origin_baseline(0)==f.convert_output(0,2,202))
    f.present(0);f.choose(0,1);f.gui()
    check('photo-return-off-restores-photo-source-instead-of-movie-cache',f.settle()==1 and f.parameters()==f.convert_output(0,2,202) and f.lease()==0)
    check('photo-movie-photo-cache-recovery-needs-no-foreign-display-packet',f.value('z7_highlight_native_parameter_generation')==0)
    del f;gc.collect()
    return dict(passed=True,checks=checks,host_sha256=host['main_payload_sha256'],module_sha256=module['module_sha256'],
                logical_two_output_handoff_without_foreign_parameter_packets=True,
                movie_cache_not_imported_after_photo_return_checked=True,
                native_cache_producer_updates_required=True,kernel_ui_fs_context_engine_and_schedule_supplied=True,
                full_boot_writer_index_engine_lifetime_or_physical_mapping_proven=False,camera_card_access=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True);p.add_argument('--module',type=Path,required=True)
    p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private output file')
    if hashlib.sha256(a.stock_main.read_bytes()).hexdigest()!=STOCK_SHA:p.error('Exact stock MAIN required')
    host=json.loads((a.build/'module-host.emulator.json').read_text(encoding='utf-8'));module=json.loads((a.module/'module.json').read_text(encoding='utf-8'))
    raw=(a.build/'module-host.emulator.main.bin').read_bytes();packet=(a.module/'Z7APP.BIN').read_bytes()
    if (not host.get('native_cache_copy_hooks') or not host.get('native_cache_photo_copies_only') or not module.get('highlight_cache_handoff') or
        hashlib.sha256(raw).hexdigest()!=host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest()!=module['module_sha256']):p.error('Exact photo-source-tracked API80 host and handoff module required')
    result=audit(raw,host,packet,module)
    names={*module['source_inputs_sha256'],'tools/audit_z7_highlight_handoff.py','tools/audit_z7_highlight_evf.py',
           'tools/audit_z7_highlight_preferences.py','tools/audit_z7_highlight_cleanup.py','tools/audit_z7_module_host.py'}
    result['source_sha256']={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in sorted(names)}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']))))


if __name__=='__main__':main()
