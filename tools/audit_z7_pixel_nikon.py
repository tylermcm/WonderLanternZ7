"""Compiled Nikon-style Z7 pixel controls, simulated capture and storage (MIT).

Native module load/init runs, then independent cases restore the same initialized
Unicorn RAM/CPU and supplied-services snapshot. Also cold-loads saved and corrupt
preference files. No physical camera, card, timing or recovery proof.
"""
import argparse
import copy
import hashlib
import json
import struct
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_PC
from audit_z7_pixel_menu import MenuUnit, CORNERS, LOG
from audit_z7_pixel_release import RELEASE, SW0, RSLOT
from audit_z7_vr_move import SLOT, BUSY, CENTRE, DELAY
from audit_z7_lcd_shutter_sound import WAV, PIXPREF
from audit_z7_lcd_grid_persistence import NEW, OBJECT, v3record
from audit_z7_settings_files import PATHS
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output
from decode_z7_pixel_menu_log import decode


def preference(word,version=4):
    if version==4 and not word&0x7f0000:word|=5<<16|3<<20
    return struct.pack('<4I',0x4e50375a,version,word,(0x4e50375a^(version<<8)^word*0x9e3779b1)&0xffffffff)


class NikonUnit(MenuUnit):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw);self.fire_times=[];self.off_after=None;self.input_forwarded=[]
        self.clock_offset=0;self.processing_ms=0;self.processing_per_frame=0
        self.folder_calls=[];self.folder_admission=1;self.folder_code=0x04390080
        self.properties[0x501]=0
        self.properties.update({0x136f:3,0x508:0,0x207:120,0xb08:120,0x205:48,0x204:72,0x20d:0,0x567:0,0x568:1})
        self.property_writes=[];self.exposures=[];self.reject_property=None
        self.metered_tv=96;self.metered_av=72
        self.effective_bias={}
        self.external_exposure=None;self.reject_property_value=None;self.j_after=None
        self.capture_latency_ms=0;self.remaining_capture_ms=0
        self.reject_log=False;self.short_log=False;self.centre_noise=False;self.noise_reads=0;self.hold_noise=0;self.hold_reads=0;self.ok_after=None
        self.u.mem_write(0xa238c1b4,struct.pack('<I',0x1005f757))
        self.u.mem_write(0xa1829b0c,struct.pack('<I',0x1030da57))
        self.u.mem_write(0xa238c140,struct.pack('<4I',*self.shutter_callbacks()))
        self.quality_writes=[];self.quality_reject=None;self.quality_partial=False
    def shutter_callbacks(self):
        # Derive the table from Nikon's own registration code (10060A38), not from a
        # hand-written list: run 8e1da6c8 froze because the list had full down and
        # half up swapped. Each literal is loaded right before "movs r0,#slot".
        table=[]
        for slot,(insn,literal) in enumerate(((0x10060a4c,0x10060cbc),(0x10060a7a,0x10060cc4),(0x10060a84,0x10060cc8),(0x10060a66,0x10060cc0))):
            assert struct.unpack('<H',bytes(self.u.mem_read(insn,2)))[0]==0x2000|slot,(slot,hex(insn))
            table.append(struct.unpack('<I',bytes(self.u.mem_read(literal,4)))[0])
        assert table==[0x10062a53,0x10062a37,0x10060a0d,0x100609d9],[hex(t) for t in table]
        return table
    def ok_press(self,address):
        # Physical OK (SW1 current 0xA1F90AB8, bit0) pressed once this many frames have fired.
        # 860b64f5 read SW0's previous-state word (0xA1F90AA8) instead.
        if self.ok_after is not None and address==DELAY and len(self.fires)>=self.ok_after:
            self.u.mem_write(0xa1f90ab8,struct.pack('<I',1))
    def telemetry(self):
        # Camera run 13e0ce7d: the centre hold read up to 19 units off on the tripod; 30 keeps centring unconfirmed past the tolerance.
        b=bytearray(super().telemetry())
        if self.centre_noise and self.read(self.base+self.symbols['z7_vm_stage'])==2 and b[0x22]==0x40 and self.target==[0,0,0]:
            self.noise_reads+=1
            struct.pack_into('<3h',b,0x24,*([30,-30,30] if self.noise_reads%2 else [-30,30,-30]))
        if self.hold_noise and b[0x22]==0x40:
            # Camera run 7a536ea7: held readings 13-19 units off target on the tripod.
            self.hold_reads+=1;d=self.hold_noise if self.hold_reads%2 else -self.hold_noise
            target=struct.unpack_from('<3h',b,0)
            struct.pack_into('<3h',b,0x24,*(v+d for v in target))
        return bytes(b)
    def nikon_half_pressed(self):
        # Nikon's view of S1 from the events the module let through (bit0 down, bit3 up).
        held=False
        for flags in self.input_forwarded:
            if flags&1:held=True
            if flags&8:held=False
        return held
    def hook(self,u,address,size,context):
        self.ok_press(address)
        pending_any=self.pending_frame if address==DELAY and self.sym else None
        pending=self.pending_frame if address==DELAY and self.sym and self.complete not in ('none','fail') else None
        previous_photos=self.r_('z7_vs_photos') if pending else 0
        suppress=False
        if pending_any and self.remaining_capture_ms:
            ms=u.reg_read(UC_ARM_REG_R0)
            self.remaining_capture_ms=max(0,self.remaining_capture_ms-ms)
            suppress=self.remaining_capture_ms>0
        if address==0x1027c0da and self.reject_log and self.cstring(u.reg_read(UC_ARM_REG_R0))==LOG:
            self.ret(0x80000001);return
        if address==0x1027c048 and self.short_log and self.sound_handles.get(u.reg_read(UC_ARM_REG_R0),[None])[0]==LOG:
            length=u.reg_read(UC_ARM_REG_R2)-1
            self.sound_files[LOG]=bytes(u.mem_read(u.reg_read(UC_ARM_REG_R1),length))
            u.mem_write(u.reg_read(UC_ARM_REG_R3),struct.pack('<I',length));self.ret(0);return
        if address==0x1033de5c:
            # Camera run ede43437: the exposure mode follows the physical dial; the PTP
            # mode write (key 0) is refused unless it would not change anything.
            if u.reg_read(UC_ARM_REG_R0)==0 and u.reg_read(UC_ARM_REG_R1)!=self.properties[0x136f]:
                self.mode_write_refusals=getattr(self,'mode_write_refusals',0)+1;self.ret(0x2019);return
            self.ret(0x2001);return
        if address==0x103fe8d8:
            key=u.reg_read(UC_ARM_REG_R0)
            assert key in (0x1308,0x1303,0x1309),hex(key)
            if key==0x1309:value=self.properties[0xb08] if self.properties[0x508] else self.properties[0x207]
            else:value=(self.properties[0x204] if key==0x1308 else self.properties[0x205]) if self.properties[0x136f]==3 else (self.metered_tv if key==0x1308 else self.metered_av)
            value+=self.effective_bias.get(key,0)
            value=((value&0xffffffff)^0x80000000)-0x80000000   # Nikon stores negative Tv/Av as 32-bit two's complement
            u.mem_write(u.reg_read(UC_ARM_REG_R1),struct.pack('<ii',24,value));self.ret(0);return
        if address==0x104065b0 and u.reg_read(UC_ARM_REG_R0)==0x501:
            key=u.reg_read(UC_ARM_REG_R0);value=u.reg_read(UC_ARM_REG_R1)
            self.quality_writes.append(value)
            rejected=value==self.quality_reject
            if not rejected or self.quality_partial:self.properties[key]=value
            self.ret(0 if rejected else 1);return
        if address==0x104065b0 and u.reg_read(UC_ARM_REG_R0) in (1,0x508,0x207,0x205,0x20d,0x204,0x209,0x008,0x576,0x568,0x567):
            key=u.reg_read(UC_ARM_REG_R0);value=u.reg_read(UC_ARM_REG_R1)
            self.property_writes.append((key,value))
            if key==self.reject_property or (key,value)==self.reject_property_value:self.ret(0);return
            self.properties[key]=value
            if key==1:self.properties[0x136f]=value
            self.ret(1);return
        if address==0x1005f756:
            self.input_forwarded.append(u.reg_read(UC_ARM_REG_R0));self.ret(0);return
        if address==0x101f50cc:
            u.mem_write(u.reg_read(UC_ARM_REG_R0),struct.pack('<2I',0,(self.clock_offset+sum(self.delays)+self.processing_ms)&0xffffffff));self.ret(0);return
        if address==0x10404c42:
            self.ret(1);return
        if address==0x104025ec:
            self.back_request=u.reg_read(UC_ARM_REG_R0);self.ret(0);return
        if address==0x1031fb12:self.ret(self.folder_admission);return
        if address==0x1031fa9c:
            self.folder_calls.append(dict(reset=u.reg_read(UC_ARM_REG_R0),moves=len([r for r in self.requests if r['opcode']==0xf1f1])))
            self.ret(self.folder_code);return
        if address==RELEASE:
            self.fire_times.append(sum(self.delays)+self.processing_ms);self.processing_ms+=self.processing_per_frame
            self.exposures.append(tuple(self.properties[k] for k in (0x136f,0x204,0x205,0x207,0x508)))
        if address==DELAY and self.sym and self.off_after and len(self.fires)>=self.off_after:
            for name,value in (('z7_pn_mode',0),('z7_pm_cancel',1),('z7_pm_requested',0)):
                u.mem_write(self.base+self.symbols[name],struct.pack('<I',value))
        if address==DELAY and self.external_exposure and self.fires:
            self.properties.update(self.external_exposure);self.external_exposure=None
        if address==DELAY and self.sym and self.j_after and len(self.fires)>=self.j_after:
            self.j_after=None;u.mem_write(self.base+self.symbols['z7_pm_cancel'],struct.pack('<I',1))
        saved_completion=self.complete
        if suppress:self.complete='none'
        super().hook(u,address,size,context)
        self.complete=saved_completion
        if address==RELEASE and u.reg_read(UC_ARM_REG_R0)==0:
            u.mem_write(RSLOT,struct.pack('<I',self.fires[-1]['callback']))
            self.remaining_capture_ms=self.capture_latency_ms
        if pending_any and self.pending_frame is None:u.mem_write(RSLOT,bytes(4))
        if pending and self.pending_frame is None:
            # Supply the native file notice, then execute the compiled still
            # wrapper/owned hook. Replace the legacy fixture's direct counter
            # increment; return via the original Delay caller (a void boundary).
            self.w('z7_vs_photos',previous_photos)
            u.mem_write(0xa18d8400,struct.pack('<I',(1000+pending)<<5)) # Native file key reserves low5 flag bits.
            for reg,value in ((UC_ARM_REG_R0,0x041e0002),(UC_ARM_REG_R1,0xa18d8400),(UC_ARM_REG_R2,0),(UC_ARM_REG_R3,0)):
                u.reg_write(reg,value)
            u.reg_write(UC_ARM_REG_PC,self.base+self.symbols['z7_ip_still'])


def snapshot(f):
    memory=[(lo,bytes(f.u.mem_read(lo,hi-lo+1))) for lo,hi,_ in f.u.mem_regions()]
    attrs={}
    for name,value in vars(f).items():
        if name=='u':continue
        try:attrs[name]=copy.deepcopy(value)
        except (TypeError,ValueError):pass
    context=f.u.context_save()
    def restore():
        for lo,data in memory:f.u.mem_write(lo,data)
        for name,value in attrs.items():setattr(f,name,copy.deepcopy(value))
        f.u.context_restore(context)
        return f
    return restore


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output','clip'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--warm-only',action='store_true',help='Development run omitting cold preference reloads; report scope records this')
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes();symbols=m['symbols']
    assert hashlib.sha256(packet).hexdigest()==m['module_sha256'] and m['configuration']['pixel_nikon_menu']
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256']
    checks=[]
    def check(name,ok):
        if not ok:
            debug=dict(check=name,fires=len(f.fires),quality_writes=f.quality_writes,
                       properties={hex(k):v for k,v in f.properties.items()},
                       state={n:f.read(f.base+symbols[n]) for n in ('z7_vm_stage','z7_vs_photos','z7_pn_mode','z7_pn_job_error','z7_pn_job_active','z7_pn_exposure_owned') if n in symbols})
            if LOG in f.sound_files:
                out.with_suffix('.failed.dat').write_bytes(f.sound_files[LOG])
                try:debug['log']={k:v for k,v in decode(f.sound_files[LOG]).items() if k!='entries'}
                except ValueError as e:debug['log_error']=str(e)
            print(json.dumps(debug),flush=True)
        assert ok,name
        checks.append(name);print(name,flush=True)
    def load(files=None):
        NikonUnit.sound_files={WAV:a.clip.read_bytes(),**(files or {})}
        # Camera run 13e0ce7d: Nikon hands VR back (state 1) after every capture.
        f=NikonUnit(raw,h,packet,{NEW[0]:v3record((3,15,1,0,5,0,127,7,0,127,4),0)},no_press=True,post_capture_loss=True)
        f.u.mem_write(0xa238c1b4,struct.pack('<I',0x1005f757))
        f.u.mem_write(0xa238c140,struct.pack('<4I',*f.shutter_callbacks()))
        f.file_paths=PATHS+NEW;f.u.mem_write(SLOT,bytes(4));f.u.mem_write(BUSY,bytes(4))
        assert f.call(h['symbols']['z7_module_load_once'],STATE)==8
        f.base=f.words()[12];f.symbols=symbols;f.setword(40,8)
        f.reply_addr=f.base+symbols['z7_vm_reply'];f.called_addr=f.base+symbols['z7_vm_d2_called']
        f.setup(f.base,symbols);f.write(f.base+symbols['sm_lcd_rows_ready'],1)
        return f
    def word(f,n):return f.read(f.base+symbols[n])
    def put(f,n,v):f.write(f.base+symbols[n],v)
    def tick(f,n=1):
        for _ in range(n):f.call(h['symbols']['z7_module_worker_tick'])
    def labels(f):
        f.menu_labels.clear();f.call(f.base+symbols['sm_render'],OBJECT);return dict(f.menu_labels)
    def press(f,row):
        f.u.mem_write(OBJECT+22,struct.pack('<2H',row,0));f.call(f.base+symbols['sm_activate'])
    def choose(f,root,choice):
        put(f,'z7_settings_view',7);press(f,root)
        if root==3:
            for _ in range(choice):f.call(f.base+symbols['sm_pn_interval_up'])
            press(f,0)
        else:press(f,choice)
    def trigger(f):
        f.arm_fires=len(f.fires);f.press_polls=0;f.long_delays=0
        f.u.mem_write(SW0,bytes(4));tick(f)
        # The real order from 10060A38: half down, full down, full up, half up.
        f.u.mem_write(SW0,struct.pack('<I',0x80000000));f.call(f.base+symbols['z7_pn_input_dispatch'],1)
        f.u.mem_write(SW0,struct.pack('<I',0xc0000000))
        f.call(f.base+symbols['z7_pn_input_dispatch'],2)
        f.u.mem_write(SW0,struct.pack('<I',0x80000000));f.call(f.base+symbols['z7_pn_input_dispatch'],4)
        f.u.mem_write(SW0,bytes(4));f.call(f.base+symbols['z7_pn_input_dispatch'],8)
        assert not f.nikon_half_pressed(),'Nikon left half-pressed'
        tick(f)
    def moves(f):return [r['payload'] for r in f.requests if r['opcode']==0xf1f1]
    f=load();restore=snapshot(f)
    f.call(0x1049d133)
    check('original-NEF-row-writes-quality-501-to-one',f.properties[0x501]==1 and f.quality_writes==[1])
    check('original-quality-converter-identifies-NEF-only',f.call(0x104a6443,0,1,0)==13)
    f=restore();choose(f,0,1)
    check('mode-menu-does-not-write-quality',not f.quality_writes)
    trigger(f)
    check('single-worker-selects-RAW-and-restores-original-JPEG',f.quality_writes==[1,0] and f.properties[0x501]==0 and len(f.fires)==4 and not word(f,'z7_pn_raw_owned'))
    f=restore();f.properties[0x501]=1;choose(f,0,1);trigger(f)
    check('existing-RAW-quality-never-rewritten',not f.quality_writes and len(f.fires)==4)
    f=restore();f.properties[0x501]=3;choose(f,0,0);trigger(f);tick(f,32)
    check('series-retains-RAW-until-mode-Off',f.quality_writes==[1] and f.properties[0x501]==1)
    choose(f,0,2);tick(f)
    check('Off-restores-original-RAW-plus-JPEG',f.quality_writes==[1,3] and f.properties[0x501]==3)
    f=restore();choose(f,0,0);tick(f);f.properties[0x501]=2;tick(f)
    check('external-quality-change-cancels-without-overwriting-user',word(f,'z7_pn_mode')==0 and f.properties[0x501]==2 and f.quality_writes==[1] and not f.fires)
    f=restore();f.quality_reject=1;choose(f,0,1);trigger(f);tick(f)
    check('RAW-refusal-disables-before-sensor-or-release',not f.requests and not f.fires and word(f,'z7_pn_mode')==0 and word(f,'z7_pn_raw_error')==1 and f.properties[0x501]==0)
    f=restore();f.quality_reject=1;f.quality_partial=True;choose(f,0,1);trigger(f);tick(f)
    check('partial-RAW-refusal-restores-before-rearm',not f.requests and not f.fires and f.quality_writes==[1,0] and f.properties[0x501]==0)
    f=restore();f.quality_reject=0;choose(f,0,1);trigger(f);tick(f,5)
    check('failed-quality-restore-is-latched-without-repeated-writes',word(f,'z7_pn_raw_error')==2 and f.quality_writes==[1,0])
    choose(f,0,1);check('failed-quality-restore-prevents-rearm',word(f,'z7_pn_mode')==0)
    f=restore();f.properties[0x501]=99;choose(f,0,1);trigger(f)
    check('unknown-quality-refuses-without-movement-or-write',not f.requests and not f.fires and not f.quality_writes and word(f,'z7_pn_mode')==0)
    f=restore()
    check('shutter-callback-table-derived-from-Nikon-registration-code',f.read(0xa238c140+4)==0x10062a37 and f.read(0xa238c140+12)==0x100609d9)
    check('native-input-slot-published',f.read(0xa238c1b4)==(f.base+symbols['z7_pn_input_dispatch']|1) and word(f,'z7_pn_input_ready')==1)
    f.call(f.base+symbols['z7_pn_input_dispatch'],2|4|0x4000)
    check('mode-Off-preserves-normal-full-down-up-and-other-events',f.input_forwarded==[2,4,0x4000] and not word(f,'z7_pn_full_pending'))
    f=restore();choose(f,0,0);f.call(f.base+symbols['z7_pn_input_dispatch'],1)
    check('half-press-forwarded-without-queuing-pixel-group',f.input_forwarded==[1] and not word(f,'z7_pn_full_pending'))
    f.call(f.base+symbols['z7_pn_input_dispatch'],2)
    f.call(f.base+symbols['z7_pn_input_dispatch'],2)
    check('full-press-queues-once-without-native-capture-or-worker-work',word(f,'z7_pn_full_pending')==1 and word(f,'z7_pn_input_requests')==1 and not f.requests and not f.fires and f.input_forwarded==[1])
    choose(f,0,2);f.call(f.base+symbols['z7_pn_input_dispatch'],4)
    check('Off-cancels-pending-and-owned-full-release-stays-consumed',not word(f,'z7_pn_full_pending') and not word(f,'z7_pn_full_owned') and f.input_forwarded==[1])
    f.call(f.base+symbols['z7_pn_input_dispatch'],8)
    check('half-up-always-reaches-Nikon-so-it-never-stays-half-pressed',f.input_forwarded==[1,8] and not f.nikon_half_pressed())
    f=restore();choose(f,0,1);trigger(f)
    check('post-capture-VR-handback-does-not-stop-the-group',len(f.fires)==4 and word(f,'z7_pn_job_error')==0 and
          all(x['state']==0x40 for x in f.fires))
    for count_index,count in enumerate((4,8)):
        f=restore();f.hold_noise=19;choose(f,1,count_index);choose(f,0,1);trigger(f);tick(f,40)
        check(f'camera-hold-noise-19-completes-{count}-frames-and-restores',f.hold_reads>=count*3 and len(f.fires)==count and
              all(x['state']==0x40 for x in f.fires) and word(f,'z7_pn_job_error')==0 and f.properties[0x501]==0 and not word(f,'z7_pn_job_active'))
    f=restore();f.hold_noise=40;choose(f,0,1);trigger(f);tick(f,40)
    check('hold-noise-beyond-tolerance-never-fires-and-restores',not f.fires and f.properties[0x501]==0 and not word(f,'z7_pn_job_active'))
    f=restore();f.ok_after=1;choose(f,0,1);trigger(f);f.u.mem_write(0xa1f90ab8,bytes(4));tick(f,5)
    check('physical-OK-during-group-cancels-after-first-frame',len(f.fires)==1 and word(f,'z7_pn_ok_cancels')==1 and
          word(f,'z7_pn_mode')==0 and f.properties[0x501]==0 and not word(f,'z7_pn_job_active'))
    f=restore();f.ok_after=0;choose(f,0,1);trigger(f);f.u.mem_write(0xa1f90ab8,bytes(4));tick(f,5)
    check('physical-OK-in-settle-cancels-before-any-frame',not f.fires and word(f,'z7_pn_mode')==0 and not word(f,'z7_pn_job_active'))
    f=restore();choose(f,0,1);trigger(f);tick(f,3)
    check('watch-ends-once-VR-is-normal',word(f,'z7_vm_stage')==3)
    choose(f,1,1);put(f,'z7_settings_view',7)
    check('shot-count-can-change-seconds-after-a-group',word(f,'z7_pm_count_index')==1 and labels(f).get(239)=='8')
    f=restore();f.centre_noise=True;choose(f,0,1);trigger(f);tick(f,40)
    check('noisy-centre-still-restores-settings-once-VR-is-normal',f.noise_reads>=20 and len(f.fires)==4 and word(f,'z7_pn_job_error')==0 and
          f.properties[0x501]==0 and not word(f,'z7_pn_raw_owned') and not word(f,'z7_pn_job_active'))
    put(f,'z7_settings_view',7);check('noisy-centre-shows-Off-not-Reboot','Off' in labels(f).values() and 'Reboot' not in labels(f).values())
    f=restore();choose(f,0,1);trigger(f)
    check('full-press-cycle-forwards-half-down-and-up-and-owns-only-full',f.input_forwarded[:2]==[1,8] and
          not any(x&6 for x in f.input_forwarded) and not f.nikon_half_pressed() and len(f.fires)==4)
    f=restore();choose(f,0,1)
    for bit in (1,8,1,8):f.call(f.base+symbols['z7_pn_input_dispatch'],bit)
    check('half-press-and-release-never-arms-a-group',f.input_forwarded==[1,8,1,8] and not word(f,'z7_pn_full_pending') and not word(f,'z7_pn_input_requests'))
    f=restore();choose(f,0,1)
    for bit in (1,2):f.call(f.base+symbols['z7_pn_input_dispatch'],bit)
    for bit in (4,8):f.call(f.base+symbols['z7_pn_input_dispatch'],bit)
    for bit in (1,2,4,8):f.call(f.base+symbols['z7_pn_input_dispatch'],bit)
    check('second-press-while-armed-is-consumed-but-half-stays-balanced',f.input_forwarded==[1,8,1,8] and word(f,'z7_pn_input_requests')==1 and not f.nikon_half_pressed())
    f=restore();f.u.mem_write(0xa238c1b4,struct.pack('<I',0x10001));f.call(f.base+symbols['z7_pn_input_publish'])
    check('input-publication-never-overwrites-foreign-owner',f.read(0xa238c1b4)==0x10001)
    f=restore()
    photo=0xa1833548+0x29*44
    meta=f.read(photo+40);controls=f.read(meta+12);maps=f.read(meta+16)
    check('photo-menu-preserves-all-33-native-controls',bytes(f.u.mem_read(controls,33*28))==bytes(f.u.mem_read(0x113ec730,33*28)))
    check('photo-menu-preserves-all-33-native-maps',bytes(f.u.mem_read(maps,33*4))==bytes(f.u.mem_read(0x114384c8,33*4)))
    check('photo-menu-adds-one-row-with-native-eight-row-viewport',f.read(meta+20)==0x00080022)
    f.call(f.base+symbols['z7_pn_photo_open'])
    check('photo-entry-opens-pixel-root',word(f,'z7_settings_view')==7 and word(f,'z7_pn_photo_origin')==1)
    f.call(f.base+symbols['sm_back_event'])
    check('photo-entry-Back-pops-to-parent',f.back_request==0x3a1 and word(f,'z7_pn_photo_origin')==0)
    f=restore();choose(f,3,0)
    put(f,'z7_settings_view',7);press(f,3)
    f.call(f.base+symbols['sm_pn_interval_down'])
    check('numeric-interval-clamps-at-zero',word(f,'z7_pn_interval_draft')==0)
    for _ in range(35):f.call(f.base+symbols['sm_pn_interval_up'])
    check('numeric-interval-clamps-at-thirty',word(f,'z7_pn_interval_draft')==30)
    f.call(f.base+symbols['sm_back_event'])
    check('numeric-interval-cancel-preserves-committed-value',word(f,'z7_pn_interval_index')==0)
    choose(f,3,17);check('numeric-interval-supports-non-preset-seventeen',word(f,'z7_pn_interval_index')==17)
    f=restore()
    tick(f,3);check('boot-Off-no-VR-or-capture',not f.requests and not f.fires and word(f,'z7_pn_mode')==0)
    put(f,'z7_settings_view',7);lab=labels(f)
    check('six-Nikon-root-labels',[lab.get(231+i) for i in range(6)]==['Pixel shift shooting mode','Number of shots','Delay','Interval until next shot','Options','Starting storage folder'])
    check('Nikon-title',lab.get(230)=='Pixel shift shooting')
    choose(f,0,1);check('single-mode-selects-without-arming',word(f,'z7_pn_mode')==2 and not word(f,'z7_pm_requested'))
    choose(f,1,1);check('eight-shot-menu-selection',word(f,'z7_pm_count_index')==1 and labels(f).get(239)=='8')
    choose(f,2,0);check('ten-second-delay-selection',word(f,'z7_pn_delay_index')==5)
    choose(f,3,3);check('three-second-interval-selection',word(f,'z7_pn_interval_index')==3)
    put(f,'z7_settings_view',7);press(f,4);check('options-default-Off',labels(f).get(231)=='AE bracketing' and labels(f).get(239)=='*')
    press(f,0);check('AE-opens-shot-count-and-increment',word(f,'z7_settings_view')==15 and labels(f).get(231)=='Number of shots' and labels(f).get(232)=='Increment')
    press(f,0);f.call(f.base+symbols['sm_pn_interval_up']);press(f,0);press(f,2)
    check('AE-Done-commits-five-groups',word(f,'z7_pn_ae_enabled')==1 and word(f,'z7_pn_ae_count')==6)
    choose(f,4,1)
    check('Options-Off-disables-AE',word(f,'z7_pn_ae_enabled')==0)
    press(f,5);check('folder-checkboxes-default-Off',labels(f).get(231)=='New folder' and labels(f).get(238)=='[ ]' and labels(f).get(239)=='[ ]')
    check('folder-entry-focuses-New-folder',f.read(OBJECT+22)&0xffff==0)
    press(f,1);check('reset-numbering-requires-new-folder',word(f,'z7_pn_reset_numbering')==0)
    press(f,0);press(f,1)
    check('folder-checkboxes-toggle-without-card-actions',word(f,'z7_pn_new_folder')==1 and word(f,'z7_pn_reset_numbering')==1 and not f.folder_calls)
    f.call(f.base+symbols['sm_back_event']);check('folder-Back-restores-correct-root-row',word(f,'z7_settings_view')==7 and f.read(OBJECT+22)&0xffff==5)
    f=restore();tick(f,5);check('no-default-preference-write',PIXPREF not in f.sound_files)
    choose(f,1,1);choose(f,2,0);choose(f,3,3);tick(f,5)
    check('count-delay-interval-saved',f.sound_files.get(PIXPREF)==preference(1|5<<4|3<<8))
    n=word(f,'z7_pn_saves');choose(f,0,1);tick(f,5)
    check('mode-never-persisted',word(f,'z7_pn_saves')==n and f.sound_files.get(PIXPREF)==preference(1|5<<4|3<<8))
    for index,count in enumerate((4,8,16,32)):
        f=restore();choose(f,1,index);choose(f,0,1);trigger(f)
        check(f'{count}-exact-capture-count',len(f.fires)==count)
        expected=[]
        for k in range(count):
            cx,cy=CORNERS[k&3];px,py=CORNERS[(k>>2)&3] if count>=16 else (0,0)
            expected.append((0x40,[-4*(20*cx+10*px),-4*(18*cy+9*py),-4*(18*cy+9*py)]))
        check(f'{count}-positions-correct',[(r['state'],r['target']) for r in f.fires]==expected)
        check(f'{count}-single-mode-automatically-Off',word(f,'z7_pn_mode')==0)
        check(f'{count}-centres-and-restores',moves(f)[-1]==CENTRE and len(f.d2_calls)==1)
        tick(f,32);trigger(f);check(f'{count}-Off-does-not-repeat',len(f.fires)==count)
    f=restore();choose(f,0,0);trigger(f);tick(f,32)
    check('series-mode-remains-On',word(f,'z7_pn_mode')==1 and len(f.fires)==4)
    tick(f,2);check('series-needs-new-trigger',len(f.fires)==4)
    trigger(f);check('series-new-trigger-captures-second-group',len(f.fires)==8)
    f=restore();choose(f,2,0);choose(f,0,1);trigger(f)
    check('selected-delay-at-least-ten-seconds',f.fire_times[0]>=10000)
    f=restore();choose(f,2,5);choose(f,3,5);choose(f,0,1);trigger(f)
    check('zero-delay-keeps-Z7-minimum-settling',f.fire_times[0]>=7500)
    check('five-second-interval-is-minimum',all(b-a>=5000 for a,b in zip(f.fire_times,f.fire_times[1:])))
    f=restore();f.processing_per_frame=2000;choose(f,3,30);choose(f,0,1);trigger(f)
    # The <=100 ms poll plus final native telemetry read add 110 ms in this
    # fixture. The injected 2000 ms processing must not be added again.
    processing_intervals=[b-a for a,b in zip(f.fire_times,f.fire_times[1:])]
    check('interval-uses-real-clock-including-capture-processing',len(f.fires)==4 and all(30000<=d<30200 for d in processing_intervals))
    f=restore();f.clock_offset=0xfffffc18;choose(f,3,5);choose(f,0,1);trigger(f)
    check('millisecond-clock-wrap-preserves-four-frames-and-interval',len(f.fires)==4 and all(b-a>=5000 for a,b in zip(f.fire_times,f.fire_times[1:])))
    f=restore();put(f,'z7_pn_new_folder',1);put(f,'z7_pn_reset_numbering',1);choose(f,0,0);trigger(f)
    check('folder-created-once-before-any-sensor-move',f.folder_calls==[dict(reset=1,moves=0)] and len(f.fires)==4)
    tick(f,32);trigger(f);check('series-creates-a-new-folder-for-each-group',len(f.folder_calls)==2 and len(f.fires)==8)
    f=restore();put(f,'z7_pn_new_folder',1);f.folder_admission=0;choose(f,0,1);trigger(f)
    check('folder-unavailable-aborts-without-moving-or-firing',not moves(f) and not f.fires and not f.folder_calls and word(f,'z7_pn_mode')==0)
    f=restore();put(f,'z7_pn_new_folder',1);f.folder_code=0x04390089;choose(f,0,1);trigger(f)
    check('native-folder-failure-aborts-without-moving-or-firing',not moves(f) and not f.fires and len(f.folder_calls)==1)
    f=restore();choose(f,0,0);f.off_after=1;trigger(f)
    check('Off-cancels-active-series-and-restores',len(f.fires)==1 and moves(f)[-1]==CENTRE and len(f.d2_calls)==1 and word(f,'z7_pn_mode')==0)
    f=restore();choose(f,0,1);f.lose_hold_frame=1;trigger(f)
    check('lost-hold-aborts-and-clears-single-mode',len(f.fires)==1 and moves(f)[-1]==CENTRE and word(f,'z7_pn_mode')==0)
    f=restore();choose(f,0,1);f.codes=[0,0xd];trigger(f)
    check('refused-capture-aborts-restores-and-disables',len(f.fires)==2 and len(f.d2_calls)==1 and word(f,'z7_pn_mode')==0)
    for key,value in ((0x209,1),(0x008,1),(0x576,0)):
        f=restore();choose(f,0,1);f.properties[key]=value;trigger(f)
        check(f'configuration-{key:x}-prepared-and-restored',len(f.fires)==4 and f.properties[key]==value)
    f=restore();choose(f,0,1);f.u.mem_write(0xa18237c6,bytes([1]));trigger(f)
    check('menu-playback-guard-does-not-arm',not f.fires and not f.requests)
    for index,count in enumerate((4,8,16,32)):
        f=restore();put(f,'z7_pn_ae_enabled',1);choose(f,1,index);choose(f,0,1);trigger(f)
        expected=[(3,tv,48,120,0) for tv in (72,96,48) for _ in range(count)]
        check(f'AE-{count}-each-group-holds-one-exposure',f.exposures==expected)
        log=decode(f.sound_files[LOG])
        check(f'AE-{count}-all-groups-have-distinct-complete-key-sets',len(log['groups'])==3 and all(g['complete'] and len(g['file_keys'])==count for g in log['groups']) and len(set(log['file_keys']))==3*count)
        check(f'AE-{count}-centres-restores-each-group-and-exposure',len(f.d2_calls)==3 and f.properties[0x204]==72 and not word(f,'z7_pn_exposure_owned') and word(f,'z7_pn_mode')==0)
    f=restore();put(f,'z7_pn_ae_enabled',1);put(f,'z7_pn_ae_count',8);choose(f,1,3);choose(f,0,1);trigger(f)
    log=decode(f.sound_files[LOG])
    check('AE-nine-by-thirty-two-captures-288-files',len(f.fires)==288 and len(log['file_keys'])==288 and len(set(log['file_keys']))==288 and len(log['groups'])==9)
    check('AE-largest-log-retains-final-frame-beyond-byte-index',any(e['phase']==7 and e['poll']==288 for e in log['entries']) and log['entries_used']<4608)
    for mode in (0,1,2):
        f=restore();f.properties.update({0x136f:mode,0x508:1,0xb08:168});choose(f,0,1);trigger(f)
        check(f'dial-mode-{mode}-refused-before-any-write-or-move',not f.fires and not f.exposures and word(f,'z7_pn_job_error')==6 and
              not getattr(f,'mode_write_refusals',0) and not any(k in (1,0x508,0x207,0x205,0x20d,0x204) for k,_ in f.property_writes))
        check(f'dial-mode-{mode}-leaves-settings-and-shows-Use-M',all(f.properties[k]==v for k,v in {0x136f:mode,0x508:1,0x207:120,0x205:48,0x204:72}.items()) and
              not word(f,'z7_pn_exposure_owned') and word(f,'z7_pn_mode')==0)
    f=restore();f.properties.update({0x567:2,0x568:2,0x209:2,0x008:1,0x576:0});choose(f,0,1);trigger(f)
    check('AF-C-dynamic-and-release-setup-restored-after-group',len(f.fires)==4 and all(f.properties[k]==v for k,v in {0x567:2,0x568:2,0x209:2,0x008:1,0x576:0}.items()))
    f=restore();f.external_exposure={0x204:60};choose(f,0,1);trigger(f)
    check('external-exposure-change-aborts-and-is-preserved',len(f.fires)==1 and f.properties[0x204]==60 and word(f,'z7_pn_mode')==0)
    f=restore();put(f,'z7_pn_ae_enabled',1);f.reject_property_value=(0x204,96);choose(f,0,1);trigger(f)
    check('between-group-exposure-refusal-prevents-next-group',len(f.fires)==4 and f.properties[0x204]==72 and decode(f.sound_files[LOG])['groups'][0]['complete'])
    f=restore();put(f,'z7_pn_ae_enabled',1);put(f,'z7_pn_ae_count',0);f.reject_property_value=(0x204,72);choose(f,0,1);trigger(f)
    check('failed-exposure-restore-latches-ownership-and-blocks-rearm',len(f.fires)==8 and word(f,'z7_pn_exposure_owned') and word(f,'z7_pn_job_error')==2 and word(f,'z7_pn_mode')==0)
    choose(f,0,1);check('failed-exposure-restore-cannot-enable-mode',word(f,'z7_pn_mode')==0)
    f=restore();put(f,'z7_pm_running',1);f.u.mem_write(0xa1f90ab8,struct.pack('<I',1));f.call(f.base+symbols['z7_pn_gui_key'],0,1,2,3)
    check('physical-J-key-callback-latches-cancellation',word(f,'z7_pm_cancel')==1 and word(f,'z7_pn_j_cancels')==1)
    f=restore();f.u.mem_write(SW0+4,struct.pack('<I',1));choose(f,0,1);trigger(f);f.u.mem_write(SW0+4,bytes(4));tick(f,5)
    check('SW0-previous-word-is-not-OK-and-never-cancels',len(f.fires)==4 and not word(f,'z7_pn_ok_cancels'))
    if a.warm_only:
        out.write_text(json.dumps(dict(passed=True,count=len(checks),checks=checks,module_sha256=m['module_sha256'],cold_preferences_tested=False,camera_access=False),indent=2)+'\n')
        print(json.dumps(dict(passed=True,checks=len(checks),cold_preferences_tested=False)));return
    print('cold preference reloads',flush=True)
    f=load({PIXPREF:preference(1|5<<4|3<<8)})
    check('cold-reload-retains-settings-but-mode-Off',word(f,'z7_pm_count_index')==1 and word(f,'z7_pn_delay_index')==5 and word(f,'z7_pn_interval_index')==3 and word(f,'z7_pn_mode')==0)
    f=load({PIXPREF:preference(15)})
    check('invalid-config-falls-back-to-disarmed-defaults',word(f,'z7_pm_count_index')==0 and word(f,'z7_pn_delay_index')==0 and word(f,'z7_pn_mode')==0 and word(f,'z7_pn_loaded')==2)
    f=load({PIXPREF:preference(2|3<<4|6<<8,version=1)})
    check('v1-preferences-migrate-to-ten-second-delay-thirty-second-interval',word(f,'z7_pm_count_index')==2 and word(f,'z7_pn_delay_index')==5 and word(f,'z7_pn_interval_index')==30 and word(f,'z7_pn_mode')==0)
    f=load({PIXPREF:preference(1|5<<4|17<<8|1<<13|1<<14,version=3)})
    check('v3-folder-flags-and-numeric-interval-cold-load-with-mode-Off',word(f,'z7_pn_new_folder')==1 and word(f,'z7_pn_reset_numbering')==1 and word(f,'z7_pn_interval_index')==17 and word(f,'z7_pn_mode')==0)
    report=dict(passed=True,count=len(checks),checks=checks,processing_interval_ms=processing_intervals,module_sha256=m['module_sha256'],host_main_sha256=h['main_payload_sha256'],
                camera_access=False,card_written=False,scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
