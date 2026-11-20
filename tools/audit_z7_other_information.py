"""Compiled original-Z7 Other group, native warnings and 48-word ownership.

SPDX-License-Identifier: MIT. Native loader/model/mask interpreter/invalidator
execute with supplied GUI and property state. No pixels, physical card or camera.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from audit_z7_other_identity import OTHER_BINDINGS, READOUT_WIDGETS, READOUT_FORMATS
from audit_z7_display_base import BaseFixture
from audit_z7_display_readouts import TABLE, SNAPSHOT
from build_z7_module_host import ROOT, STATE


def audit(raw,host,packet,module):
    if hashlib.sha256(raw).hexdigest()!=host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest()!=module['module_sha256']:
        raise ValueError('Fingerprint mismatch')
    if module.get('other_information_widgets')!=list(READOUT_WIDGETS[6:]) or module.get('readout_ownership_bits')!=64:
        raise ValueError('Other-information profile required')
    f=BaseFixture(raw,host,packet);s=module['symbols'];checks=[]
    def check(name,good):
        checks.append(dict(name=name,passed=bool(good)))
        if not good:raise AssertionError(name)
    check('module-loads',f.call(host['symbols']['z7_module_load_once'],STATE)==8)
    base=f.words()[12];model=base+s['z7_menu_settings']
    def read(p,n=4):return int.from_bytes(f.u.mem_read(p,n),'little')
    def write(p,v):f.u.mem_write(p,struct.pack('<I',v))
    def word(name,n=4):return read(base+s[name],n)
    def call(name,*args):return f.call(base+s[name],*args)
    def before():f.call(host['symbols']['z7_display_before_update'])
    def master(on):call('z7_settings_flag',model,0,on)
    def information(preset,bits):
        for group in range(7):
            if call('z7_settings_information',model,preset,group,bool(bits&(1<<group)))!=1:raise AssertionError('Model setter')
    for preset in range(4):call('z7_settings_component',model,preset,2,0)
    desc=[read(TABLE+i*4) for i in range(61)]
    check('compiled-widgets-match-independent-native-identity',bytes(f.u.mem_read(base+s['readout_widgets'],24))==bytes(READOUT_WIDGETS))
    check('compiled-shared-format-selectors-match-native-preparation',bytes(f.u.mem_read(base+s['readout_formats'],24))==bytes(READOUT_FORMATS))
    for widget in READOUT_WIDGETS:
        f.u.mem_write(desc[widget]+4,struct.pack('<9I',*([0xa5faffff^(widget<<20)]*9)))
        f.u.mem_write(read(desc[widget]+44),b'\1')
    f.u.mem_write(0xa18237b8,bytes(7))
    def masks():return [bytes(f.u.mem_read(p+4,36)) for p in desc]
    original=masks()
    def expected(bits,formats=bytes(7)):
        result=list(original)
        for i,widget in enumerate(READOUT_WIDGETS):
            words=list(struct.unpack('<9I',result[widget]));fmt=READOUT_FORMATS[i]
            if fmt==255 or not formats[fmt]:
                selected=bits&(1<<i if i<6 else 64)
                for bank in (0,3):
                    photo=(9 if words[bank]&1 else 0)|(0x900 if words[bank]&0x100 else 0)
                    words[bank]=(words[bank]&~0x909)|(photo if selected else 0)
            result[widget]=struct.pack('<9I',*words)
        return result
    before();check('default-off-preserves-all-native-descriptors',masks()==original and not word('z7_readout_active'))
    master(1)
    for preset in range(4):
        write(base+s['z7_readout_preset'],preset)
        for bits in range(128):
            information(preset,bits);snapshot=bytes(f.u.mem_read(SNAPSHOT,0x33c));before()
            check(f'preset{preset}-information{bits}-only-allowed-photo-words',masks()==expected(bits))
            check(f'preset{preset}-information{bits}-current-snapshot-preserved',bytes(f.u.mem_read(SNAPSHOT,0x33c))==snapshot)
    write(base+s['z7_readout_preset'],0)
    for bits in (0,127):
        information(0,bits);before()
        for bank in (0,1):
            f.u.mem_write(SNAPSHOT+0x338,struct.pack('<H',bank))
            for operation in (0,1):
                f.u.mem_write(SNAPSHOT+0x193,bytes([operation]))
                for page in (0,3):
                    f.u.mem_write(SNAPSHOT+0x18a,bytes([page]))
                    for widget in READOUT_WIDGETS:
                        check(f'native-mask-bits{bits}-bank{bank}-op{operation}-page{page}-widget{widget}',f.call(0x102f2690,widget)==int(bits==0))
        # These are supplied query inputs, not a real native page/property
        # transition. Restore them before invoking the ownership callback again.
        f.u.mem_write(SNAPSHOT+0x338,bytes(2));f.u.mem_write(SNAPSHOT+0x193,b'\0');f.u.mem_write(SNAPSHOT+0x18a,b'\0')
    information(0,63);before()
    check('query-fixture-return-keeps-native-base-ownership',word('z7_base_active')==1 and word('z7_readout_active')==1)
    for index in (2,3,4):
        for value in (*range(1,34),255):
            formats=bytearray(7);formats[index]=value;f.u.mem_write(0xa18237b8,bytes(formats));before()
            wanted=expected(63,formats);actual=masks()
            if actual!=wanted:
                raise AssertionError(dict(case=f'warning{index}-{value}',differences=[(i,actual[i].hex(),wanted[i].hex()) for i in range(61) if actual[i]!=wanted[i]],
                    active=word('z7_readout_active'),blocked=word('readout_blocked'),conflicts=word('z7_readout_conflicts'),base_active=word('z7_base_active')))
            check(f'other-off-native-format{index}-value{value}-retains-complete-shared-group',actual==wanted)
    f.u.mem_write(0xa18237b8,bytes(7));master(0);before()
    check('master-off-restores-all48-owned-words',masks()==original and not word('readout_pending',8))
    information(0,127);master(1)
    # Validate the complete plan before any mask stores, including late bindings.
    for widget in READOUT_WIDGETS[6:]:
        for table,name in ((TABLE,'descriptor'),(0x1064c67c,'updater')):
            address=table+widget*4;saved=read(address);write(address,0x100);before()
            check(f'bad-{name}-{widget}-rejects-before-any-mask-store',masks()==original and not word('z7_readout_active'))
            write(address,saved)
    before();check('all-valid-bindings-acquire-after-plan-validation',word('z7_readout_active')==1)
    # Every new descriptor can be abandoned; high-index pending bits must survive
    # master-off until its original binding returns, without truncating at32.
    for i,widget in enumerate(READOUT_WIDGETS[6:],6):
        information(0,63);master(1);before();filtered=masks()
        write(TABLE+widget*4,0x100);before();pending=3<<(i*2)
        check(f'abandoned-{widget}-both-lcd-words-pending64',word('readout_pending',8)==pending and not word('z7_readout_active'))
        check(f'abandoned-{widget}-old-words-not-written',masks()[widget]==filtered[widget])
        master(0);before()
        check(f'abandoned-{widget}-master-off-retains-full-pending64',word('readout_pending',8)==pending)
        write(TABLE+widget*4,desc[widget]);before()
        check(f'returned-{widget}-disabled-cleanup-restores-all-native-words',masks()==original and not word('readout_pending',8))
    # Conditional restoration also applies to high pending words changed by a
    # foreign owner while their descriptor is absent.
    widget=READOUT_WIDGETS[-1];information(0,63);master(1);before()
    write(TABLE+widget*4,0x100);before();write(desc[widget]+4,0xdeadbeef)
    master(0);before();write(TABLE+widget*4,desc[widget]);before()
    retained=list(original);words=list(struct.unpack('<9I',retained[widget]));words[0]=0xdeadbeef;retained[widget]=struct.pack('<9I',*words)
    check('high-index-return-preserves-foreign-word-and-restores-other-owned-words',masks()==retained and not word('readout_pending',8))
    check('policy-never-dispatches-or-paints-gui-objects',not f.readout_dispatches and not f.hud_redraws)
    return dict(passed=True,checks=checks,module_sha256=module['module_sha256'],main_sha256=host['main_payload_sha256'],
        information_groups=7,native_widgets=24,owned_words=48,ownership_bits=64,native_mask_interpreter_executes=True,
        warning_format_selectors=dict(capacity=2,flash=3,metering=4),
        supplied_boundaries=['Loader','Incoming native GUI/property/control/snapshot state','Native label/drawing sinks'],
        actual_pixels=False,camera_access=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True);p.add_argument('--module',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();output=args.output.resolve()
    if not output.is_relative_to(ROOT/'.private') or output.exists():p.error('Choose a new private output')
    result=audit((args.build/'module-host.emulator.main.bin').read_bytes(),json.loads((args.build/'module-host.emulator.json').read_text()),
        (args.module/'Z7APP.BIN').read_bytes(),json.loads((args.module/'module.json').read_text()))
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),native_widgets=24,owned_words=48)))


if __name__=='__main__':main()
