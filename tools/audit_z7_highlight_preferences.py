"""Execute preference codec migration, real menu edits and native programming.

SPDX-License-Identifier: MIT. Original native converter/consumer/gate/driver
instructions execute. Kernel/FS/UI/colors/surfaces, engines and MMIO supplied;
no physical pixels, card durability or camera installation assertion.
"""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import struct
import zlib

from audit_splash_image import STOCK_SHA
from audit_z7_module_host import HostFixture
from audit_z7_native_warning_transaction import TransactionFixture
from audit_z7_highlight_frame_gate import SOURCE_APPLY
from audit_z7_highlight_plane import MMIO
from audit_z7_frame_permission import FRAME
from audit_z7_parameters import NATIVE
from audit_z7_settings_files import PATHS
from build_z7_module import ROOT, build
from build_z7_module_host import STATE, ZIG

LEVELS = (255,248,235,224,213,202,191,180)
DEFAULT = (0,15,1,0,5,10,127,7,0,127,1,1)


def seal(data):
    b = bytearray(data); b[12:16] = bytes(4)
    struct.pack_into('<I', b, 12, zlib.crc32(b)); return bytes(b)


def wire(values, version=2):
    return seal(struct.pack('<16I',0x3143375a,version,0x03800007,0,*values[:10],
                            *(values[10:] if version == 2 else (0,0))))


def codec_audit(raw, host, packet, metadata):
    f = HostFixture(raw, host, packet)
    if f.call(host['symbols']['z7_module_load_once'], STATE) != 8: raise AssertionError('Codec probe load')
    base = f.words()[12]; addr = lambda n: base + metadata['symbols']['z7_settings_' + n]
    def model(): return tuple(struct.unpack('<12I', f.u.mem_read(addr('model'), 48)))
    def put(v): f.u.mem_write(addr('model'), struct.pack('<12I', *v))
    def call(op, a=0, b=0): return f.call(addr('operation'), op, a, b, 0)
    checks = []
    def check(n, good):
        checks.append(dict(name=n, passed=bool(good)))
        if not good: raise AssertionError(n)
    check('defaults-preserve-legacy-pattern1-threshold248', model() == DEFAULT)
    sentinel = (0xa5a5a5a5,) * 12
    for pattern in range(3):
        for threshold in range(8):
            values = DEFAULT[:10] + (pattern, threshold)
            put(DEFAULT)
            check(f'isolated-preference-edit-{pattern}-{threshold}', call(9, pattern, threshold) == 1 and model() == values)
            check(f'independent-v2-wire-{pattern}-{threshold}', call(1, 64) == 1 and bytes(f.u.mem_read(addr('output'),64)) == wire(values))
            f.u.mem_write(addr('input'), wire(values)); put(sentinel)
            check(f'v2-decode-{pattern}-{threshold}', call(2,64) == 1 and model() == values)
    legacy = (3,31,15,2,4,8,255,7,0,128,1,1)
    f.u.mem_write(addr('input'), wire(legacy,1)); put(sentinel)
    check('legacy-v1-migrates-only-global-preferences', call(2,64) == 1 and model() == legacy)
    check('migrated-v1-reencodes-canonical-v2-at-same64-byte-size', call(1,64) == 1 and bytes(f.u.mem_read(addr('output'),64)) == wire(legacy))
    for pattern, threshold in ((3,1),(1,8),(0xffffffff,1),(1,0xffffffff)):
        put(DEFAULT)
        check(f'invalid-preference-edit-{pattern}-{threshold}-preserves-model', call(9,pattern,threshold) == 0 and model() == DEFAULT)
    invalid = []
    for version, offset, value in ((1,56,1),(1,60,1),(2,56,3),(2,60,8),(2,4,3),(2,16,4),(2,20,0)):
        b=bytearray(wire(DEFAULT,version));struct.pack_into('<I',b,offset,value);invalid.append(seal(b))
    for i,b in enumerate(invalid):
        f.u.mem_write(addr('input'),b);put(sentinel)
        check(f'sealed-invalid-schema-fields-{i}-preserve-entire-output',call(2,64)==0 and model()==sentinel)
    reference=wire(DEFAULT)
    for bit in range(512):
        b=bytearray(reference);b[bit//8]^=1<<(bit%8);f.u.mem_write(addr('input'),bytes(b));put(sentinel)
        check(f'v2-single-bit-damage-{bit}-preserves-model',call(2,64)==0 and model()==sentinel)
    for size in (0,1,63,65,0xffffffff):
        put(DEFAULT);f.u.mem_write(addr('output'),b'\xa5'*64)
        check(f'wrong-encode-size-{size}',call(1,size)==0 and bytes(f.u.mem_read(addr('output'),64))==b'\xa5'*64)
        f.u.mem_write(addr('input'),reference);put(sentinel)
        check(f'wrong-decode-size-{size}',call(2,size)==0 and model()==sentinel)
    put(DEFAULT[:10]+(2,7))
    check('per-preset-reset-preserves-global-preferences',call(4,0)==1 and model()==DEFAULT[:10]+(2,7))
    return checks


class PreferenceFixture(TransactionFixture):
    def __init__(self, *args, files=None):
        super().__init__(*args)
        if files is not None: self.files = {p:bytes(data) for p,data in files.items()}
    def preferences(self):
        return tuple(struct.unpack('<12I',self.u.mem_read(self.address('z7_menu_settings'),48)))
    def action(self, view, row, preset=0):
        self.write(self.address('z7_settings_view'),view);self.write(self.address('z7_settings_preset'),preset)
        self.u.mem_write(0xa1833548+22,struct.pack('<2H',row,0));self.call(self.address('sm_activate'))
    def choose(self,pattern,threshold):
        for _ in range(3):
            if self.preferences()[10]==pattern:break
            self.action(4,1)
        for _ in range(8):
            if self.preferences()[11]==threshold:break
            self.action(4,2)
        if self.preferences()[10:]!=(pattern,threshold):raise AssertionError('Preference menu failed to cycle')


def profile_audit(raw,host,packet,module):
    checks=[]
    def check(n,good):
        checks.append(dict(name=n,passed=bool(good)))
        if not good:raise AssertionError(n)
    f=PreferenceFixture(raw,host,packet,module);legacy_files=dict(f.files);baseline=f.start(False,0)
    check('v1-journal-load-migrates-default-preferences-without-writing',f.preferences()[10:]==(1,1) and f.files==legacy_files)
    before=f.preferences();events=len(f.file_events)
    f.action(1,5)
    labels=dict(f.menu_labels)
    check('preset-highlight-entry-opens-submenu-without-toggling-page',f.value('z7_settings_view')==4 and f.preferences()==before)
    check('menu-emits-global-scope-pattern-and-threshold-labels',labels[231]=='Show on this page' and labels[232]=='Pattern (all pages)' and
          labels[233]=='Threshold (all pages)' and labels[239]=='Type 1' and labels[240]=='248')
    f.call(f.address('sm_back_event'))
    check('back-restores-highlight-row-on-owning-preset',f.value('z7_settings_view')==1 and
          sum(struct.unpack('<2H',f.u.mem_read(0xa1833548+22,4)))==5 and len(f.file_events)==events)
    for pattern in (1,2):
        for threshold in range(8):
            events=len(f.file_events);f.choose(pattern,threshold)
            check(f'gui-preferences-{pattern}-{threshold}-never-access-files',len(f.file_events)==events)
            f.gui();f.worker()
            check(f'owned-preferences-{pattern}-{threshold}-consume-current-publication',f.dispatch()==1)
            f.worker();expected=f.convert(pattern,LEVELS[threshold])
            check(f'native-converted-parameters-{pattern}-{threshold}-match-independent-request',f.parameters()==expected and f.lease()==1)
            check(f'frame-programs-selected-preferences-{pattern}-{threshold}',f.call(SOURCE_APPLY,0,FRAME)==1 and f.control()&1==1)
            config=f.programs[-1][2]
            half=lambda offset:int.from_bytes(config[offset:offset+2],'little')
            check(f'actual-pattern-threshold-registers-{pattern}-{threshold}',
                  f.read(MMIO+0x430)==1|((config[0]&3)<<8) and f.read(MMIO+0x434)==(half(2)|0xff)|(half(4)<<16) and f.read(MMIO+0x43c)==config[6])
    expected=f.convert(2,180);native_baseline=f.convert(1,213);f.native(native_baseline)
    check('foreign-native-update-uses-current-global-preferences',f.parameters()==expected and f.lease()==1)
    f.choose(0,7);f.gui();f.worker();f.dispatch();f.worker()
    check('global-pattern-off-restores-latest-native-baseline',f.parameters()==native_baseline and f.lease()==0 and f.control()&1==0)
    check('global-off-preserves-page-checkbox-and-threshold',f.preferences()[2]&8 and f.preferences()[10:]==(0,7))
    f.choose(1,3);f.gui();f.worker();f.dispatch();f.worker();f.call(SOURCE_APPLY,0,FRAME)
    f.toggle();f.gui();f.worker();f.dispatch();f.worker()
    check('page-toggle-does-not-change-global-style-threshold',f.preferences()[10:]==(1,3) and f.parameters()==native_baseline and f.control()&1==0)
    f.toggle();f.choose(1,2);f.gui();f.worker()
    cancelled=f.owned('cancelled');before=f.parameters()
    f.choose(2,4)  # Settings change before the next GUI publication/consume.
    check('queued-old-preferences-cancel-before-copy-after-menu-edit',
          f.dispatch()==0 and f.owned('cancelled')==cancelled+1 and f.parameters()==before)
    f.gui();f.worker()
    check('retry-consumes-new-pattern-and-threshold-snapshot',f.dispatch()==1 and f.parameters()==f.convert(2,213))
    f.worker();f.call(SOURCE_APPLY,0,FRAME)
    check('fresh-preference-retry-programs-native-plane',f.control()&1==1)
    f.toggle();f.gui();f.worker();f.dispatch();f.worker()
    check('final-page-off-restores-baseline-with-global-choice-preserved',
          f.parameters()==native_baseline and f.control()&1==0 and f.preferences()[10:]==(2,4))
    for _ in range(7):f.worker()
    check('worker-saves-v2-payload-in-original80-byte-journal',any(len(v)==80 and struct.unpack_from('<I',v,20)[0]==2 for v in f.files.values()))
    check('first-v2-save-preserves-legacy-slot',f.files[PATHS[0]]==legacy_files[PATHS[0]])
    saved={p:bytes(data) for p,data in f.files.items()};settings=f.preferences();del f;gc.collect()
    g=PreferenceFixture(raw,host,packet,module,files=saved);g.load()
    check('restart-loads-all-v2-preferences-and-existing-settings',g.preferences()==settings and g.files==saved)
    return checks


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True);p.add_argument('--module',type=Path,required=True)
    p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private output directory')
    if hashlib.sha256(a.stock_main.read_bytes()).hexdigest()!=STOCK_SHA:p.error('Exact stock main required')
    host=json.loads((a.build/'module-host.emulator.json').read_text(encoding='utf-8'));module=json.loads((a.module/'module.json').read_text(encoding='utf-8'))
    raw=(a.build/'module-host.emulator.main.bin').read_bytes();packet=(a.module/'Z7APP.BIN').read_bytes()
    if not host.get('native_warning_transaction_hooks') or not module.get('highlight_preferences') or (
        hashlib.sha256(raw).hexdigest()!=host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest()!=module['module_sha256']):p.error('Exact preference module and API72 host required')
    probe,metadata=build(ROOT/'z7-native-modules/examples/highlight_preferences_model_probe.c',zig=ZIG)
    result=dict(passed=True,codec_checks=codec_audit(raw,host,probe,metadata),profile_checks=profile_audit(raw,host,packet,module),
                host_sha256=host['main_payload_sha256'],module_sha256=module['module_sha256'],camera_card_access=False,
                probe_sha256=hashlib.sha256(probe).hexdigest(),
                physical_pixels_menu_raster_or_card_durability_proven=False)
    names={*module['source_inputs_sha256'],'tools/audit_z7_highlight_preferences.py','tools/audit_z7_highlight_owned.py',
           'tools/audit_z7_highlight_cleanup.py','z7-native-modules/examples/highlight_preferences_model_probe.c','z7-native-modules/examples/display_settings_probe.c'}
    result['source_sha256']={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in sorted(names)}
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(probe)
    (out/'probe.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,codec_checks=len(result['codec_checks']),profile_checks=len(result['profile_checks']))))


if __name__=='__main__':main()
