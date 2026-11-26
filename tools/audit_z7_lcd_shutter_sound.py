"""LCD module with shutter sound and a volume row: offline audit (MIT).

Runs the compiled LCD+sound module on the original-Z7 host loader, menu and
worker in the persistence fixture, with the sound files served separately:
  1. The complete LCD preset-persistence suite (audit_z7_lcd_preset_persistence)
     re-runs unchanged against this module with no sound files on the card, so
     display behavior, the v3 journal and DISP admission are unaffected.
  2. Sound: the root page shows "Shutter sound" with its level; OK steps
     OFF/1..7 and previews each level without any display-journal I/O; the
     worker writes A:\\Z7SND.DAT only after a change, and a reload restores it;
     a damaged file keeps level 5; with the 9-level build, 8 and 9 too; the capture event 0x0419000B plays at the
     chosen level only in Silent photography and never when OFF; Nikon's
     controller handler always runs; levels 6/7 boost and clip exactly.
Supplied: filesystem, sound post and start-path setters, property getter for
0x576, the native controller handler. No camera, no card.
"""
import argparse,hashlib,json,struct,sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1
import audit_z7_lcd_preset_persistence as preset_suite
from audit_z7_display_persistence import PersistenceFixture
from audit_z7_lcd_grid_persistence import NEW,OBJECT,v3record
from audit_z7_settings_files import PATHS,NOT_FOUND
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output

WAV='A:\\SHUTTER1.WAV';LEVEL='A:\\Z7SND.DAT'
SLOT,NATIVE,EXPOSURE=0xa18d1bd8,0x101426a9,0x0419000b
START_SLOT,MAILBOX,SND_STATE=0xa188d278,0xa18852ac,0xa188d190
GAINS=(64,102,154,205,256,362,512,724,1024)


class SoundAware(PersistenceFixture):
    sound_files={}
    def __init__(self,*a,**k):
        super().__init__(*a,**k)
        self.sound_files=dict(type(self).sound_files);self.sound_handles={};self.sound_events=[];self.next_sound_fd=0x700
        self.sends=[];self.native=[];self.setters=[];self.silent=1
        self.u.mem_write(MAILBOX,struct.pack('<I',0x1234));self.u.mem_write(SND_STATE,bytes(4))
        self.u.mem_write(SLOT,struct.pack('<I',NATIVE))  # stock boot value, as measured on the camera
        for base in (0xa21a0000,0xa2970000):  # sound context and a message page
            try:self.u.mem_map(base,0x10000)
            except Exception:pass
    def r(self,reg):return self.u.reg_read(reg)
    def call(self,address,*args):
        # The sound engine adds about 580 KB of BSS that the host loader clears
        # under the per-instruction fixture hook; allow more wall time, same guards.
        from audit_splash_image import ARGUMENTS,SAVED,STACK,STOP
        from unicorn.arm_const import UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
        u=self.u
        for reg in ARGUMENTS:u.reg_write(reg,0)
        for reg,value in zip(ARGUMENTS,args):u.reg_write(reg,value)
        guards={reg:0x51510000+i for i,reg in enumerate(SAVED)}
        for reg,value in guards.items():u.reg_write(reg,value)
        u.reg_write(UC_ARM_REG_SP,STACK);u.reg_write(UC_ARM_REG_LR,STOP|1)
        u.emu_start(address|1,STOP,timeout=600000000,count=200000000)
        if u.reg_read(UC_ARM_REG_PC)!=STOP or u.reg_read(UC_ARM_REG_SP)!=STACK:
            raise ValueError(f'Incomplete native call:pc={u.reg_read(UC_ARM_REG_PC):08x}')
        if any(u.reg_read(reg)!=value for reg,value in guards.items()):raise ValueError('Native call changed a callee-saved register')
        return u.reg_read(UC_ARM_REG_R0)
    def hook(self,u,address,size,context):
        if self.files_enabled and address==0x1027beae:
            p=self.r(UC_ARM_REG_R0);words=struct.unpack('<42I',u.mem_read(p,168));op=bytes(u.mem_read(p+0x9c,1))[0]
            path=self.cstring(words[4]) if op in (5,13) else None
            if path in (WAV,LEVEL) or (op in (6,8,9) and words[7] in self.sound_handles):
                result=0
                if op in (5,13):
                    self.sound_events.append(('open' if op==5 else 'create',path))
                    if op==5 and path not in self.sound_files:result=NOT_FOUND
                    else:
                        result=self.next_sound_fd;self.next_sound_fd+=1
                        self.sound_handles[result]=[path,0]
                        if op==13:self.sound_files[path]=b''
                elif op in (8,9):
                    fd,pointer,capacity,actual=words[7],words[10],words[11],words[12]
                    path,pos=self.sound_handles[fd]
                    if op==8:
                        data=self.sound_files[path][pos:pos+capacity]
                        if data:u.mem_write(pointer,data)
                        count=len(data)
                    else:
                        count=capacity;self.sound_files[path]+=bytes(u.mem_read(pointer,count))
                    self.sound_handles[fd][1]+=count;u.mem_write(actual,struct.pack('<I',count))
                    self.sound_events.append(('read' if op==8 else 'write',path,capacity,count))
                else:
                    self.sound_events.append(('close',self.sound_handles.pop(words[7])[0]))
                self.ret(result);return
        if address==0x100a2d78:
            self.sends.append((self.r(UC_ARM_REG_R0),self.r(UC_ARM_REG_R1)));self.ret(1);return
        if address==0x1016fef2 and self.r(UC_ARM_REG_R0)==0x576:
            self.ret(self.silent);return
        if address==NATIVE-1:
            self.native.append(tuple(self.u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1)));self.ret(0x600);return
        if address==0x100cf90a:
            u.mem_write(self.r(UC_ARM_REG_R0),b'\1');self.ret(0);return
        if address==0x100cf98c:self.ret(0);return
        if address in (0x1006b794,0x1006b62c,0x1006b94a,0x1006b7dc):
            self.setters.append((address,struct.unpack('<6I',u.mem_read(self.r(UC_ARM_REG_R0),24))));self.ret(1);return
        super().hook(u,address,size,context)


def wav(samples):
    data=struct.pack('<%dh'%len(samples),*samples)
    fmt=struct.pack('<HHIIHH',1,1,48000,96000,2,16)
    body=b'WAVE'+b'fmt '+struct.pack('<I',len(fmt))+fmt+b'data'+struct.pack('<I',len(data))+data
    return b'RIFF'+struct.pack('<I',len(body))+body


def level_record(level):
    check=0x444e5337^(1<<8)^(level*0x01010101)^0xa5a5a5a5
    return struct.pack('<4I',0x444e5337,1,level,check&0xffffffff)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--clip',type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256'] and hashlib.sha256(packet).hexdigest()==m['module_sha256']
    assert m['configuration']['shutter_sound'] and m['configuration']['settings_label_refresh'] and not m['configuration'].get('sound_lab')
    clip=a.clip.read_bytes();symbols=m['symbols'];checks=[]
    levels=m['configuration'].get('sound_levels') or 7
    def check(name,ok):
        assert ok,name
        checks.append(name)

    # 1. The full display-settings suite, unchanged, with no sound files.
    suite_out=out.with_name(out.stem+'-preset-suite.json')
    preset_suite.PersistenceFixture=SoundAware;SoundAware.sound_files={}
    argv=sys.argv;sys.argv=['x','--host',str(a.host),'--module',str(a.module),'--output',str(suite_out)]
    try:preset_suite.main()
    finally:sys.argv=argv
    suite=json.loads(suite_out.read_text())
    check('display-preset-suite-passes-unchanged',suite['passed'] and suite['checks']>=270)

    defaults=(3,15,1,0,5,0,127,7,0,127,4)
    journal={PATHS[0]:b'',NEW[0]:v3record(defaults,0)};del journal[PATHS[0]]
    def load(sound):
        SoundAware.sound_files=sound
        f=SoundAware(raw,h,packet,dict(journal));f.file_paths=PATHS+NEW
        assert f.call(h['symbols']['z7_module_load_once'],STATE)==8
        f.base=f.words()[12];f.setword(40,8);f.write(f.base+symbols['sm_lcd_rows_ready'],1);return f
    def word(f,n):return f.read(f.base+symbols[n])
    def labels(f):
        f.menu_labels.clear();f.call(f.base+symbols['sm_render'],OBJECT);return dict(f.menu_labels)
    def press(f,row):
        f.u.mem_write(OBJECT+22,struct.pack('<2H',row,0));f.call(f.base+symbols['sm_activate'])
    def ticks(f,n):
        for _ in range(n):f.call(h['symbols']['z7_module_worker_tick'])
    def finish(f):f.u.mem_write(SND_STATE,bytes(4));f.write(f.base+symbols['z7_sound_playback'],0)

    # 2. Sound with the exact click.
    f=load({WAV:clip})
    check('wav-loaded-and-installed',word(f,'z7_sl_installed')==1 and f.read(SLOT)==((f.base+symbols['z7_sl_controller'])|1)
          and f.read(START_SLOT)==((f.base+symbols['z7_sound_start'])|1))
    check('no-level-file-means-level-5-and-no-write',word(f,'z7_sl_level')==5 and [e[:2] for e in f.sound_events]==[('open',LEVEL),('open',WAV),('read',WAV),('close',WAV)])
    lab=labels(f)
    check('root-row-7-shows-shutter-sound-5',lab.get(237)=='Shutter sound' and lab.get(244)=='5' and lab.get(236)=='Battery percentage')
    check('root-other-rows-unchanged',[lab.get(231+i) for i in range(5)]==['Custom pages','Standard','Minimal','Composition','Exposure'])
    revision=word(f,'z7_settings_revision');files=list(f.file_events);model=bytes(f.u.mem_read(f.base+symbols['z7_menu_settings'],44))
    press(f,6)
    check('ok-steps-to-6-and-previews',word(f,'z7_sl_level')==6 and len(f.sends)==1 and word(f,'z7_sl_previews')==1)
    check('sound-row-touches-no-display-state',word(f,'z7_settings_revision')==revision and f.file_events==files and
          bytes(f.u.mem_read(f.base+symbols['z7_menu_settings'],44))==model and word(f,'z7_settings_view')==0)
    check('row-value-repainted',labels(f).get(244)=='6')
    finish(f)
    for want in range(7,levels+1):
        press(f,6);finish(f)
        check(f'steps-to-{want}',word(f,'z7_sl_level')==want and len(f.sends)==want-5 and labels(f).get(244)==str(want))
    press(f,6)
    check('wraps-to-off-without-preview',word(f,'z7_sl_level')==0 and len(f.sends)==levels-5 and labels(f).get(244)=='OFF')
    for _ in range(4):press(f,6);finish(f)
    check('cycles-back-to-4',word(f,'z7_sl_level')==4)
    ticks(f,1);check('no-write-while-unstable',not any(e[0]=='create' for e in f.sound_events))
    ticks(f,4)
    check('worker-saves-level-file',f.sound_files.get(LEVEL)==level_record(4) and word(f,'z7_sl_saves')==1)
    check('display-journal-untouched-by-sound-save',all(e[1] in NEW for e in f.file_events if e[0] in ('create','write')) and
          not any(e[0]=='create' for e in f.file_events))
    ticks(f,6);check('no-rewrite-without-change',sum(1 for e in f.sound_events if e[0]=='create')==1)
    g=load({WAV:clip,LEVEL:f.sound_files[LEVEL]})
    check('reload-restores-level',word(g,'z7_sl_level')==4 and word(g,'z7_sl_loaded')==1 and labels(g).get(244)=='4')
    g=load({WAV:clip,LEVEL:b'\0'*16})
    check('damaged-file-keeps-default',word(g,'z7_sl_level')==5 and word(g,'z7_sl_loaded')==2)

    # Trigger.
    g=load({WAV:clip,LEVEL:level_record(3)})
    r=g.call(g.read(SLOT),EXPOSURE,0x44,0x22,0x33)
    check('exposure-in-silent-plays-at-level',len(g.sends)==1 and word(g,'z7_sl_queued')==1)
    check('native-controller-runs-same-args',r==0x600 and g.native[-1]==(EXPOSURE,0x44))
    job=g.sends[0][1];check('queued-at-chosen-level',struct.unpack('<I',g.u.mem_read(job+20,4))[0]==3)
    g.call(g.read(SLOT),0x04190008,0,0,0)
    check('other-events-silent',len(g.sends)==1 and len(g.native)==2)
    g.call(g.read(SLOT),EXPOSURE,0,0,0)
    check('busy-counted-not-retried',len(g.sends)==1 and word(g,'z7_sl_busy')==1)
    finish(g);g.silent=0;g.call(g.read(SLOT),EXPOSURE,0,0,0)
    check('mechanical-shutter-no-sound',len(g.sends)==1)
    g=load({WAV:clip,LEVEL:level_record(0)});g.call(g.read(SLOT),EXPOSURE,0,0,0)
    check('off-never-plays',not g.sends and len(g.native)==1)
    g=load({});
    check('no-wav-leaves-slots-native',g.read(SLOT)==NATIVE and g.read(START_SLOT)==0x1006bc47 and word(g,'z7_sl_installed')==0)

    # Boosted levels clip exactly (start path with a full-scale test tone).
    tone=[0,16000,32767,-32768,-20000,100]*10
    for level in range(5,levels+1):
        g=load({WAV:wav(tone),LEVEL:level_record(level)})
        g.call(g.read(SLOT),EXPOSURE,0,0,0)
        msg=0xa2970100;g.u.mem_write(msg,struct.pack('<7I',0,0,0,0,0x0418001e,g.sends[0][1],msg))
        started=g.call(g.read(START_SLOT),msg)
        data=next(s for a_,s in g.setters if a_==0x1006b94a);pcm=struct.unpack('<%dh'%(2*len(tone)),g.u.mem_read(data[0],4*len(tone)))
        # The engine plays mono clips as interleaved stereo (each sample twice).
        want=tuple(max(-32768,min(32767,(v*GAINS[level-1])>>8)) for v in tone for _ in (0,1))
        check(f'level-{level}-pcm-exact',started==1 and data[1]==4*len(tone) and pcm==want)
        # Safety (sound lab, Nov 25): tone above 31 stopped audio on the camera.
        check(f'level-{level}-driver-tone-fixed-31',next(t for a_,t in g.setters if a_==0x1006b62c)[2]==31 and g.read(0xa21ab994+4)==31)

    report=dict(passed=True,count=len(checks),checks=checks,display_suite_checks=suite['checks'],module_sha256=m['module_sha256'],
                host_main_sha256=h['main_payload_sha256'],clip_sha256=hashlib.sha256(clip).hexdigest(),camera_access=False,scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks),display_suite_checks=suite['checks'])))


if __name__=='__main__':main()
