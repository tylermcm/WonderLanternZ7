"""Execute the compiled Z7 pixel menu and 4/16/32 capture worker (MIT).

Uses the existing simulated BodyVr/capture/filesystem fixture, not hardware.
Checks disarmed boot, native menu actions, guarded capture, all half-step
targets, cleanup/rearming and refusal paths. No camera or card access.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
from audit_z7_pixel_shift import ShiftUnit
from audit_z7_pixel_release import RELEASE, SW0
from audit_z7_vr_move import SLOT, BUSY, CENTRE, DELAY
from audit_z7_lcd_shutter_sound import WAV
from audit_z7_lcd_grid_persistence import NEW, OBJECT, v3record
from audit_z7_settings_files import PATHS
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output

LOG='A:\\Z7PIX.DAT'
CORNERS=((0,0),(1,0),(1,1),(0,1))


class MenuUnit(ShiftUnit):
    def __init__(self,*a,cancel_after=None,post_capture_loss=False,**kw):
        super().__init__(*a,**kw)
        self.properties.update({0x209:0,0x008:0,0x576:1})
        self.cancel_after=cancel_after
        self.post_capture_loss=post_capture_loss
        self.arm_fires=0;self.press_polls=0

    def hook(self,u,address,size,context):
        if address==DELAY and self.r(UC_ARM_REG_R0)==100 and not self.hold_button and len(self.fires)==self.arm_fires:
            self.press_polls+=1
            if self.press_polls==2:u.mem_write(SW0,bytes(4))
        if address==0x104065a4:
            self.ret(self.properties.get(self.r(UC_ARM_REG_R0),0));return
        if address==DELAY and self.sym and self.cancel_after and len(self.fires)>=self.cancel_after:
            self.u.mem_write(self.base+self.symbols['z7_pm_cancel'],struct.pack('<I',1))
        if self.post_capture_loss and address==DELAY and self.pending_frame:
            super().hook(u,address,size,context)
            self.state=1
            return
        super().hook(u,address,size,context)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output','clip'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text())
    raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256']
    assert hashlib.sha256(packet).hexdigest()==m['module_sha256'] and m['configuration']['pixel_menu']
    symbols=m['symbols'];checks=[]
    def check(name,ok):
        assert ok,name
        checks.append(name)
        print(name,flush=True)
    def load(**kw):
        MenuUnit.sound_files={WAV:a.clip.read_bytes()}
        f=MenuUnit(raw,h,packet,{NEW[0]:v3record((3,15,1,0,5,0,127,7,0,127,4),0)},**kw)
        f.file_paths=PATHS+NEW
        f.u.mem_write(SLOT,bytes(4));f.u.mem_write(BUSY,bytes(4))
        assert f.call(h['symbols']['z7_module_load_once'],STATE)==8
        f.base=f.words()[12];f.symbols=symbols;f.setword(40,8)
        f.reply_addr=f.base+symbols['z7_vm_reply'];f.called_addr=f.base+symbols['z7_vm_d2_called']
        f.setup(f.base,symbols);f.write(f.base+symbols['sm_lcd_rows_ready'],1)
        return f
    def call(f,name,*v):return f.call(f.base+symbols[name],*v)
    def word(f,name):return f.read(f.base+symbols[name])
    def setword(f,name,v):f.write(f.base+symbols[name],v)
    def tick(f,n=1):
        for _ in range(n):f.call(h['symbols']['z7_module_worker_tick'])
    def labels(f):
        f.menu_labels.clear();call(f,'sm_render',OBJECT);return dict(f.menu_labels)
    def press(f,row):
        f.u.mem_write(OBJECT+22,struct.pack('<2H',row,0));call(f,'sm_activate')
    def moves(f):return [r['payload'] for r in f.requests if r['opcode']==0xf1f1]
    def arm(f,index=0):
        f.arm_fires=len(f.fires);f.press_polls=0
        setword(f,'z7_pm_count_index',index);setword(f,'z7_settings_view',7);press(f,1)
    def flags(f):return struct.unpack_from('<I',f.sound_files[LOG],12)[0]
    f=load();tick(f,3)
    check('boot-disarmed-no-VR-requests-or-fires',not f.requests and not f.fires)
    check('root-extras',labels(f).get(237)=='Extras')
    press(f,6);lab=labels(f)
    check('extras-has-pixel-shift',lab.get(233)=='Pixel shift' and lab.get(234)=='Back')
    press(f,2);lab=labels(f)
    check('pixel-page-title-and-four-default',word(f,'z7_settings_view')==7 and lab.get(230)=='Pixel shift' and lab.get(238)=='4')
    press(f,0);check('menu-count-16',labels(f).get(238)=='16')
    press(f,0);check('menu-count-32',labels(f).get(238)=='32')
    press(f,0);check('menu-count-wraps-4',labels(f).get(238)=='4')
    press(f,1);check('menu-arms-without-shooting',word(f,'z7_pm_requested')==1 and not f.fires and labels(f).get(240)=='Armed')
    press(f,0);check('count-cannot-change-while-armed',word(f,'z7_pm_count_index')==0)
    press(f,1);check('second-press-cancels-arm',word(f,'z7_pm_requested')==0)
    press(f,3);check('back-row-to-extras',word(f,'z7_settings_view')==5)
    press(f,2);call(f,'sm_back_event');check('back-key-to-extras',word(f,'z7_settings_view')==5)
    call(f,'sm_back_event');check('extras-back-to-root',word(f,'z7_settings_view')==0)
    setword(f,'z7_pm_lock',1);arm(f)
    check('menu-cannot-reset-active-worker',not word(f,'z7_pm_requested') and word(f,'z7_pm_lock')==1)
    setword(f,'z7_pm_lock',2);setword(f,'z7_pm_requested',1);tick(f)
    check('worker-cannot-enter-menu-reset',not f.requests and not f.fires)
    for index,count in enumerate((4,16,32)):
        f=load();arm(f,index);tick(f)
        expected=[];targets=[]
        for k in range(count):
            cx,cy=CORNERS[k&3];px,py=CORNERS[(k>>2)&3] if count>=16 else (0,0)
            x,y=20*cx+10*px,18*cy+9*py
            expected += [bytes([0,x,0,y+36,0,16,16,0,0,2]),bytes([0,x,0,y,0,16,16,0,0,2])]
            targets.append((0x40,[-4*x,-4*y,-4*y]))
        check(f'{count}-exact-count',len(f.fires)==count)
        check(f'{count}-every-approach-target-and-centre',moves(f)==expected+[CENTRE])
        check(f'{count}-every-shot-at-exact-target',[(x['state'],x['target']) for x in f.fires]==targets)
        check(f'{count}-restores-native-VR-once',len(f.d2_calls)==1)
        check(f'{count}-one-click-each',f.r_('z7_vr_clicks')==count)
        check(f'{count}-max-target-252',all(max(abs(v) for v in t[1])<=252 for t in targets))
        tick(f,32)
        check(f'{count}-complete-centred-restored',flags(f)&(1<<19) and flags(f)&64 and flags(f)&(1<<13))
        log=f.sound_files[LOG]
        check(f'{count}-log-v4-and-32-key-capacity',struct.unpack_from('<I',log,4)[0]==4 and len(log)==184+512*56)
        from decode_z7_pixel_menu_log import decode
        decoded=decode(log)
        check(f'{count}-log-decoder',decoded['frames']==count and 'series_complete' in decoded['flags'])
        n=len(f.fires);tick(f,2);check(f'{count}-no-unrequested-repeat',len(f.fires)==n)
        f.long_delays=0;f.u.mem_write(SW0,struct.pack('<I',0x80000000));arm(f,index);tick(f)
        check(f'{count}-explicit-rearm-new-group',len(f.fires)==2*count)
    for key,value in ((0x209,1),(0x008,1),(0x576,0)):
        f=load();f.properties[key]=value;arm(f);tick(f,2)
        check(f'guard-{key:x}-{value}-no-requests',not f.requests and not f.fires)
    f=load(no_press=True);arm(f);tick(f,4)
    check('arm-still-requires-half-press',not f.fires and not moves(f))
    f=load();arm(f);f.u.mem_write(0x104065a4,bytes(4));tick(f)
    check('getter-fingerprint-failure-no-requests',not f.requests)
    for address,value,size in ((0xa201d510,1,4),(0xa18237c6,1,1)):
        f=load();arm(f);f.u.mem_write(address,value.to_bytes(size,'little'));tick(f)
        check(f'photo-view-guard-{address:x}',not f.requests and not f.fires)
    f=load(lose_hold_frame=1);arm(f);tick(f);tick(f,32)
    check('lost-hold-before-exposure-aborts-and-restores',len(f.fires)==1 and flags(f)&(1<<18) and moves(f)[-1]==CENTRE and len(f.d2_calls)==1)
    f=load(post_capture_loss=True);arm(f);tick(f);tick(f,32)
    check('native-capture-disrupts-hold-aborts-and-restores',len(f.fires)==1 and flags(f)&(1<<18) and moves(f)[-1]==CENTRE)
    f=load(cancel_after=1);arm(f,2);tick(f);tick(f,32)
    check('cancel-bounds-32-frame-group',len(f.fires)==1 and moves(f)[-1]==CENTRE and not flags(f)&(1<<19))
    f=load(codes=[0,0xd]);arm(f,1);tick(f);tick(f,32)
    check('refused-capture-restores-and-is-incomplete',len(f.fires)==2 and moves(f)[-1]==CENTRE and not flags(f)&(1<<19))
    f=load();setword(f,'z7_vm_log',0) # state flags are separate from magic
    f.u.mem_write(f.base+symbols['z7_vm_log']+12,struct.pack('<I',256));arm(f)
    check('timed-out-VR-blocks-rearm',not word(f,'z7_pm_requested'))
    report=dict(passed=True,count=len(checks),checks=checks,module_sha256=m['module_sha256'],host_main_sha256=h['main_payload_sha256'],
                camera_access=False,card_access=False,exposures=0,scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
