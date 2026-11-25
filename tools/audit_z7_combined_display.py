"""Combined v4 LCD grid/highlight codec, migration and native plane audit (MIT).

Original native converter/consumer/gate/driver execute. GUI, storage, palette,
surfaces, engines, MMIO and task handoff are supplied. No physical camera proof.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from audit_z7_highlight_preferences import seal,LEVELS
from audit_z7_native_warning_transaction import TransactionFixture
from audit_z7_module_host import HostFixture
from audit_z7_lcd_grid_persistence import NEW,v3record
from audit_z7_settings_files import PATHS
from audit_z7_settings_storage import record
from audit_z7_highlight_frame_gate import SOURCE_APPLY
from audit_z7_frame_permission import FRAME
from build_z7_module import ROOT,build
from build_z7_module_host import STATE,ZIG
from prepare_flash_review import require_private_output

EXT=('A:\\Z7EXT0.DAT','A:\\Z7EXT1.DAT')
DEFAULT=(0,15,1,0,5,0,127,7,0,127,2,0,1)


def wire(v,version=4):
    tail=(v[10],v[11]|(v[12]<<2)) if version==4 else (v[10],0) if version==3 else (v[11],v[12]) if version==2 else (0,0)
    return seal(struct.pack('<16I',0x3143375a,version,0x03800007,0,*v[:10],*tail))


class CombinedFixture(TransactionFixture):
    file_paths=PATHS+NEW+EXT
    def preferences(self):return tuple(struct.unpack('<13I',self.u.mem_read(self.address('z7_menu_settings'),52)))
    def action(self,view,row,preset=0):
        self.write(self.address('z7_settings_view'),view);self.write(self.address('z7_settings_preset'),preset)
        self.u.mem_write(0xa1833548+22,struct.pack('<2H',row,0));self.call(self.address('sm_activate'))
    def choose(self,pattern,threshold):
        for _ in range(3):
            if self.preferences()[11]==pattern:break
            self.action(4,1)
        for _ in range(8):
            if self.preferences()[12]==threshold:break
            self.action(4,2)
        assert self.preferences()[11:]==(pattern,threshold)
    def toggle(self):self.action(4,0)
    def start(self):
        self.load();self.choose(1,1)
        baseline=bytes(100);self.native(baseline)
        self.call(self.report['symbols']['z7_display_before_update']);self.gui();self.worker();self.dispatch();self.worker()
        self.write(FRAME+0x34,0)
        assert self.call(SOURCE_APPLY,0,FRAME)==1 and self.control()&1
        return baseline


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('host','module','installed-host','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert h['native_warning_transaction_hooks'] and m['configuration']['combined_preferences']
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256'] and hashlib.sha256(packet).hexdigest()==m['module_sha256']
    checks=[]
    def check(name,good):
        assert good,name
        checks.append(name)
    probe,meta=build(ROOT/'z7-native-modules/examples/settings_combined_probe.c',zig=ZIG)
    f=HostFixture(raw,h,probe);check('codec-probe-loads',f.call(h['symbols']['z7_module_load_once'],STATE)==8)
    base=f.words()[12];addr=lambda name:base+meta['symbols']['z7_settings_'+name]
    def model():return tuple(struct.unpack('<13I',f.u.mem_read(addr('model'),52)))
    def put(v):f.u.mem_write(addr('model'),struct.pack('<13I',*v))
    def op(n,a=0,b=0):return f.call(addr('operation'),n,a,b,0)
    check('safe-combined-defaults',model()==DEFAULT)
    sentinel=(0xa5a5a5a5,)*13
    for grid in range(1,6):
        for pattern in range(3):
            for threshold in range(8):
                v=DEFAULT[:10]+(grid,pattern,threshold);put(v)
                check(f'v4-encode-{grid}-{pattern}-{threshold}',op(1,64)==1 and bytes(f.u.mem_read(addr('output'),64))==wire(v))
                f.u.mem_write(addr('input'),wire(v));put(sentinel)
                check(f'v4-decode-{grid}-{pattern}-{threshold}',op(2,64)==1 and model()==v)
    for version in (1,2,3):
        incoming=(3,31,15,2,4,8,255,7,0,128,4,2,7)
        expected=incoming[:10]+((4,0,1) if version==3 else (2,2,7) if version==2 else (2,0,1))
        f.u.mem_write(addr('input'),wire(incoming,version));put(sentinel)
        check('legacy-migration-v'+str(version),op(2,64)==1 and model()==expected)
    invalid=[]
    for offset,value in ((4,5),(56,0),(56,6),(60,3),(60,32),(60,0xffffffff),(16,4),(20,0)):
        data=bytearray(wire(DEFAULT));struct.pack_into('<I',data,offset,value);invalid.append(seal(data))
    good=wire(DEFAULT)
    for bit in range(512):
        data=bytearray(good);data[bit//8]^=1<<(bit%8);invalid.append(bytes(data))
    for i,data in enumerate(invalid):
        f.u.mem_write(addr('input'),data);put(sentinel)
        check('invalid-record-preserves-model-'+str(i),op(2,64)==0 and model()==sentinel)
    # Default-safe migration and actual native plane behavior in one full profile.
    g=CombinedFixture(raw,h,packet,m);legacy=dict(g.files);g.load()
    check('v1-migrates-highlight-off-without-writing',g.preferences()[10:]==(2,0,1) and g.files==legacy)
    g.write(g.address('sm_lcd_rows_ready'),1)
    g.action(1,5)
    check('highlight-menu-has-four-physical-rows',g.read(g.address('sm_meta')+20)==0x00070004)
    labels=dict(g.menu_labels)
    check('highlight-submenu-labels-correct',[labels[231+i] for i in range(4)]==['Show on this page','Pattern (all pages)','Threshold (all pages)','Back'])
    g.call(g.address('sm_back_event'));check('back-returns-to-owning-preset',g.value('z7_settings_view')==1)
    g.choose(1,1);baseline=bytes(100);g.native(baseline)
    g.call(h['symbols']['z7_display_before_update']);g.gui();g.worker();g.dispatch();g.worker()
    for pattern in (1,2):
        for threshold in range(8):
            before=list(g.file_events);g.choose(pattern,threshold)
            check(f'gui-edit-no-file-io-{pattern}-{threshold}',g.file_events==before)
            g.gui();g.worker();g.dispatch();g.worker()
            check(f'native-parameters-{pattern}-{threshold}',g.parameters()==g.convert(pattern,LEVELS[threshold]))
            check(f'native-plane-{pattern}-{threshold}',g.call(SOURCE_APPLY,0,FRAME)==1 and g.control()&1==1)
    g.choose(0,7);g.gui();g.worker();g.dispatch();g.worker()
    check('off-restores-native-plane',g.parameters()==baseline and g.lease()==0 and not g.control()&1)
    for _ in range(7):g.worker()
    check('only-new-extension-journals-written',all(e[1] in EXT for e in g.file_events if e[0] in ('create','write')))
    check('legacy-files-byte-identical',all(g.files[n]==v for n,v in legacy.items()))
    check('new-journal-contains-v4',any(len(v)==80 and struct.unpack_from('<I',v,20)[0]==4 for n,v in g.files.items() if n in EXT))
    saved=dict(g.files);expected=g.preferences()
    cold=CombinedFixture(raw,h,packet,m);cold.files=saved;cold.load()
    check('v4-cold-load-restores-all-thirteen-settings',cold.preferences()==expected and cold.files==saved)
    configured=(1,15,9,0,4,8,255,0,0,255,4)
    migrating=CombinedFixture(raw,h,packet,m);migrating.files[NEW[0]]=v3record(configured,7)
    original=dict(migrating.files);migrating.load()
    check('v3-migration-preserves-grid-and-display-settings',migrating.preferences()==configured+(0,1) and migrating.files==original)
    migrating.action(4,1)
    for _ in range(7):migrating.worker()
    check('first-v4-save-preserves-both-older-namespaces',all(migrating.files[n]==v for n,v in original.items()))
    check('first-v4-save-writes-only-extension-journals',all(e[1] in EXT for e in migrating.file_events if e[0] in ('create','write')))
    blocked=CombinedFixture(raw,h,packet,m);blocked.files.update({NEW[0]:v3record(configured,7),EXT[0]:b'unknown format'})
    original=dict(blocked.files);blocked.load()
    check('unknown-extension-record-blocks-legacy-fallback',not blocked.value('z7_persistence_ready'))
    blocked.action(0,0)
    for _ in range(7):blocked.worker()
    check('unknown-extension-record-never-overwritten',blocked.files==original)
    old=json.loads((a.installed_host/'module-host.emulator.json').read_text())
    rejected=HostFixture((a.installed_host/'module-host.emulator.main.bin').read_bytes(),old,packet)
    check('installed-api44-rejects-before-ui-publication',rejected.call(old['symbols']['z7_module_load_once'],STATE)==7 and not rejected.words()[23])
    result=dict(passed=True,count=len(checks),checks=checks,module_sha256=m['module_sha256'],host_main_sha256=h['main_payload_sha256'],
        camera_access=False,physical_pixels=False,installed_host_compatible=False,settings_version=4,
        legacy_files_preserved=True,scope=__doc__)
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
