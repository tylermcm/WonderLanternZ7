"""Native-update-driven logical EVF/LCD highlight admission and handoff.

SPDX-License-Identifier: MIT. Native requests, source/frame/gate/driver execute.
Output/scene/context, same shared engine, kernel/FS/UI/colors/MMIO are supplied.
No physical EVF mapping, engine lifetime or no-native-update handoff proof.
"""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import struct

from audit_splash_image import STOCK_SHA
from audit_z7_highlight_preferences import PreferenceFixture
from audit_z7_highlight_converter import request
from audit_z7_highlight_frame_gate import SOURCE_APPLY
from audit_z7_frame_permission import FRAME
from audit_z7_parameters import NATIVE, PACKET, PAYLOAD
from build_z7_module_host import ROOT


class EVFFixture(PreferenceFixture):
    def select(self, selector, scene=None):
        self.write(0xa181c764, 2 if selector else 1)
        self.u.mem_write(0xa180a568, bytes([selector]))
        self.u.mem_write(0xa18237c6, bytes([2 if selector else 0] if scene is None else [scene]))
        self.display = 2 if selector else 1
        self.call(self.report['symbols']['z7_display_before_update'])
    def convert_output(self, selector, pattern, threshold):
        output = 4 if selector else 1
        self.u.mem_write(NATIVE + 0x2300, request(output, pattern, threshold))
        self.u.mem_write(NATIVE + 0x2400, bytes(100))
        self.call(0x1034fe22, NATIVE + 0x2400, NATIVE + 0x2300, output)
        return bytes(self.u.mem_read(NATIVE + 0x2400, 100))
    def native_output(self, selector, parameters):
        self.u.mem_write(PAYLOAD, parameters + bytes(4))
        self.u.mem_write(PACKET, struct.pack('<7I', 0,0,0,0,0x42062007 if selector else 0x42060007,PAYLOAD,0))
        return self.call(0x10239840, PACKET)
    def present(self, selector): return self.call(SOURCE_APPLY, 2 if selector else 0, FRAME)


def audit(raw, host, packet, module):
    checks=[]
    def check(n,good):
        checks.append(dict(name=n,passed=bool(good)))
        if not good:raise AssertionError(n)
    f=EVFFixture(raw,host,packet,module);f.load()
    f.call(host['symbols']['z7_display_before_update']);f.gui();f.worker()
    check('initial-unobserved-shared-parameters-do-not-establish-native-baseline',not f.queued and f.lease()==0)
    lcd=f.convert_output(0,2,224)
    check('lcd-native-update-captures-matching-origin-and-converts',f.native_output(0,lcd)==1 and f.parameters()==f.convert_output(0,1,248))
    f.write(FRAME+0x34,0)
    check('lcd-native-source-programs-owned-plane',f.present(0)==1 and f.control()&1==1)
    f.select(1);f.gui();f.worker()
    check('output-switch-queues-only-old-owned-disable',f.dispatch()==1 and f.read(NATIVE+0x28)==0 and f.control()&1==0 and f.lease(28)==1)
    f.worker();queued=len(f.queued);f.worker();f.worker()
    check('no-evf-native-update-does-not-import-lcd-baseline-or-queue-evf-apply',len(f.queued)==queued and f.lease(40)==0)
    evf=f.convert_output(1,2,235)
    check('evf-native-update-converts-with-output4-palette13',f.native_output(1,evf)==1 and
          f.parameters()==f.convert_output(1,1,248) and f.read(PAYLOAD+100)==1 and f.lease(40)==1)
    check('evf-source-uses-shared-native-gate-and-real-enable-register',f.present(1)==1 and f.control()&1==1 and
          bytes(f.u.mem_read(NATIVE+0x88,1))==b'\x02')
    f.choose(2,4);f.gui();f.worker()
    check('evf-preference-edit-owned-request-uses-evf-command',f.read(f.queued[-1]+16)==0x42062007 and f.dispatch()==1 and
          f.parameters()==f.convert_output(1,2,213))
    f.worker();f.present(1)
    for pattern in (1,2):
        for index,threshold in enumerate((255,248,235,224,213,202,191,180)):
            f.choose(pattern,index);f.gui();f.worker()
            check(f'evf-owned-pattern{pattern}-threshold{threshold}-matches-independent-output4-conversion',
                  f.read(f.queued[-1]+16)==0x42062007 and f.dispatch()==1 and
                  f.parameters()==f.convert_output(1,pattern,threshold))
            f.worker();f.present(1)
    f.choose(0,4);f.gui();f.worker();f.dispatch();f.worker()
    check('global-off-in-evf-restores-exact-native-evf-baseline',f.parameters()==evf and f.lease()==0 and f.control()&1==0)
    f.choose(1,1);f.gui();f.worker()
    check('evf-reenable-uses-observed-native-origin-after-restoration',f.dispatch()==1 and f.parameters()==f.convert_output(1,1,248))
    f.worker();f.present(1)
    f.select(0);f.gui();f.worker();f.dispatch();f.worker();queued=len(f.queued);f.worker()
    check('lcd-return-without-native-update-disables-evf-without-importing-evf-baseline',
          f.read(NATIVE+0x28)==0 and f.control()&1==0 and len(f.queued)==queued and f.lease(40)==1)
    latest=f.convert_output(0,1,202)
    check('new-lcd-update-establishes-own-baseline-after-evf',f.native_output(0,latest)==1 and f.parameters()==f.convert_output(0,1,248) and f.lease(40)==0)
    f.present(0);f.choose(0,1);f.gui();f.worker();f.dispatch();f.worker()
    check('lcd-off-restores-latest-lcd-baseline-not-earlier-evf-or-lcd',f.parameters()==latest and f.lease()==0 and f.control()&1==0)
    disabled=bytes(4)+b'\xa5'*96
    check('disabled-native-payload-keeps-undefined-tail-before-ownership',f.native_output(0,disabled)==1 and f.parameters()==disabled)
    f.choose(1,1);f.gui();f.worker()
    check('disabled-native-origin-admits-owned-conversion-without-interpreting-tail',f.dispatch()==1 and f.parameters()==f.convert_output(0,1,248))
    f.worker();f.present(0);f.choose(0,1);f.gui();f.worker();f.dispatch();f.worker()
    check('disabled-baseline-restoration-normalizes-undefined-tail',f.parameters()==bytes(100) and f.lease()==0 and f.control()&1==0)
    del f;gc.collect()

    f=EVFFixture(raw,host,packet,module);f.load();f.select(1,scene=0)
    baseline=f.convert_output(1,1,224)
    check('evf-native-update-before-gui-scene-keeps-native-parameters',f.native_output(1,baseline)==1 and f.parameters()==baseline and f.lease()==0)
    f.u.mem_write(0xa18237c6,b'\x02');f.gui();f.worker()
    check('later-evf-gui-can-queue-from-observed-origin-without-second-native-update',f.read(f.queued[-1]+16)==0x42062007 and
          f.dispatch()==1 and f.parameters()==f.convert_output(1,1,248))
    f.worker();f.write(FRAME+0x34,0);f.present(1)
    # EVF preferences are global rather than tied to the last LCD page mask.
    f.toggle();f.gui();f.worker();f.worker()
    check('evf-global-preference-does-not-follow-lcd-page-checkbox',f.lease()==1 and f.parameters()==f.convert_output(1,1,248))
    f.write(0xa24e1e00,1);f.gui();movie=f.convert_output(1,2,191)
    check('movie-native-parameters-are-not-converted-in-evf-profile',f.native_output(1,movie)==1 and f.parameters()==movie and f.lease()==0)
    del f;gc.collect()

    f=EVFFixture(raw,host,packet,module);f.load();f.select(1);f.gui()
    f.write(f.address('z7_highlight_native_origin'),1)
    baseline=f.convert_output(1,2,180)
    check('busy-native-origin-publication-preserves-foreign-payload-and-parks-owned-work',f.native_output(1,baseline)==1 and
          f.parameters()==baseline and f.owned('parked')==1 and f.lease()==0)
    return dict(passed=True,checks=checks,host_sha256=host['main_payload_sha256'],module_sha256=module['module_sha256'],
                native_update_driven_two_output_conversion_verified=True,no_native_update_new_output_claim_performed=False,
                automatic_no_native_update_handoff_implemented=False,physical_evf_mapping_engine_lifetime_or_pixels_proven=False,
                same_shared_engine_and_context_schedule_supplied=True,camera_card_access=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True);p.add_argument('--module',type=Path,required=True)
    p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private output file')
    if hashlib.sha256(a.stock_main.read_bytes()).hexdigest()!=STOCK_SHA:p.error('Exact stock main required')
    host=json.loads((a.build/'module-host.emulator.json').read_text(encoding='utf-8'));module=json.loads((a.module/'module.json').read_text(encoding='utf-8'))
    raw=(a.build/'module-host.emulator.main.bin').read_bytes();packet=(a.module/'Z7APP.BIN').read_bytes()
    if not host.get('native_warning_transaction_hooks') or not module.get('highlight_evf_native_update_required') or (
        hashlib.sha256(raw).hexdigest()!=host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest()!=module['module_sha256']):p.error('Exact EVF profile and API72 host required')
    result=audit(raw,host,packet,module)
    names={*module['source_inputs_sha256'],'tools/audit_z7_highlight_evf.py','tools/audit_z7_highlight_preferences.py',
           'tools/audit_z7_highlight_owned.py','tools/audit_z7_highlight_cleanup.py'}
    result['source_sha256']={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in sorted(names)}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']))))


if __name__=='__main__':main()
