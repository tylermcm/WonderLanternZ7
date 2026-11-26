"""EXPERIMENTAL sound-lab build of the LCD module: offline audit (MIT).

Same fixture as audit_z7_lcd_shutter_sound.py. Checks:
  1. The complete LCD preset-persistence suite passes unchanged (277 checks).
  2. The Shutter sound row steps through all 16 lab settings in order
     (OFF, 1-9, then level 5 with driver tone 0/16/24/28/34/37), each previewed
     with the table's engine level and tone; the tone reaches both the copied
     record and Nikon's tone setter; a photo in Silent photography plays with
     the chosen setting; levels 8 and 9 produce the exact boosted, clipped
     samples; the lab saves Z7SND.DAT version 2 and ignores a version-1
     (release) file, keeping setting 5.
No camera, no card.
"""
import argparse,hashlib,json,struct,sys
from pathlib import Path
import audit_z7_lcd_preset_persistence as preset_suite
from audit_z7_lcd_shutter_sound import SoundAware,WAV,LEVEL,SLOT,EXPOSURE,START_SLOT,SND_STATE,wav,level_record
from audit_z7_lcd_grid_persistence import NEW,OBJECT,v3record
from audit_z7_settings_files import PATHS
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output

LAB=[('OFF',0,31)]+[(str(i),i,31) for i in range(1,10)]+[(f'5 T{t}',5,t) for t in (0,16,24,28,34,37)]
GAINS=(64,102,154,205,256,362,512,724,1024)
CONTEXT=0xa21ab994


def lab_record(index):
    check=0x444e5337^(2<<8)^(index*0x01010101)^0xa5a5a5a5
    return struct.pack('<4I',0x444e5337,2,index,check&0xffffffff)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--clip',type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256'] and hashlib.sha256(packet).hexdigest()==m['module_sha256']
    assert m['configuration']['sound_lab']
    clip=a.clip.read_bytes();symbols=m['symbols'];checks=[]
    def check(name,ok):
        assert ok,name
        checks.append(name)

    suite_out=out.with_name(out.stem+'-preset-suite.json')
    preset_suite.PersistenceFixture=SoundAware;SoundAware.sound_files={}
    argv=sys.argv;sys.argv=['x','--host',str(a.host),'--module',str(a.module),'--output',str(suite_out)]
    try:preset_suite.main()
    finally:sys.argv=argv
    suite=json.loads(suite_out.read_text())
    check('display-preset-suite-passes-unchanged',suite['passed'] and suite['checks']>=270)

    defaults=(3,15,1,0,5,0,127,7,0,127,4);journal={NEW[0]:v3record(defaults,0)}
    def load(sound):
        SoundAware.sound_files=sound
        f=SoundAware(raw,h,packet,dict(journal));f.file_paths=PATHS+NEW
        assert f.call(h['symbols']['z7_module_load_once'],STATE)==8
        f.base=f.words()[12];f.setword(40,8);f.write(f.base+symbols['sm_lcd_rows_ready'],1);return f
    def word(f,n):return f.read(f.base+symbols[n])
    def value(f):
        f.menu_labels.clear();f.call(f.base+symbols['sm_render'],OBJECT);return dict(f.menu_labels).get(244)
    def press(f):
        f.u.mem_write(OBJECT+22,struct.pack('<2H',6,0));f.call(f.base+symbols['sm_activate'])
    def finish(f):f.u.mem_write(SND_STATE,bytes(4));f.write(f.base+symbols['z7_sound_playback'],0)
    def start(f):
        msg=0xa2970100;f.u.mem_write(msg,struct.pack('<7I',0,0,0,0,0x0418001e,f.sends[-1][1],msg))
        return f.call(f.read(START_SLOT),msg)

    f=load({WAV:clip})
    check('lab-installed-default-5',word(f,'z7_sl_installed')==1 and word(f,'z7_sl_level')==5 and value(f)=='5')
    seen=[]
    for step in range(len(LAB)):
        press(f);index=(5+step+1)%len(LAB);text,volume,tone=LAB[index]
        row=dict(index=word(f,'z7_sl_level'),text=value(f),sends=len(f.sends))
        if volume:
            job=f.sends[-1][1];row['volume']=struct.unpack('<I',f.u.mem_read(job+20,4))[0]
            f.setters.clear();row['started']=start(f)
            row['context_tone']=f.read(CONTEXT+4)
            row['setter_tone']=next(s for a_,s in f.setters if a_==0x1006b62c)[2]
            finish(f)
        seen.append(row)
        check(f'lab-step-{index}-{text.replace(" ","-")}',row['index']==index and row['text']==text and
              (not volume or (row['volume']==volume and row['started']==1 and row['context_tone']==tone and row['setter_tone']==tone)))
    check('lab-cycles-all-16-and-returns-to-5',word(f,'z7_sl_level')==5 and len(seen)==16)

    for index in (9,15):
        g=load({WAV:clip,LEVEL:lab_record(index)})
        check(f'lab-reload-{index}',word(g,'z7_sl_level')==index and word(g,'z7_sl_loaded')==1)
        g.call(g.read(SLOT),EXPOSURE,0,0,0);g.setters.clear()
        job=g.sends[-1][1];started=start(g)
        tone=next(s for a_,s in g.setters if a_==0x1006b62c)[2]
        check(f'lab-photo-uses-setting-{index}',started==1 and struct.unpack('<I',g.u.mem_read(job+20,4))[0]==LAB[index][1] and tone==LAB[index][2])
    g=load({WAV:clip,LEVEL:level_record(7)})
    check('lab-ignores-release-v1-file',word(g,'z7_sl_level')==5 and word(g,'z7_sl_loaded')==2)
    for _ in range(4):press(g);finish(g)
    for _ in range(5):g.call(h['symbols']['z7_module_worker_tick'])
    check('lab-saves-version-2',g.sound_files.get(LEVEL)==lab_record(9))

    tone_wave=[0,16000,32767,-32768,-20000,100]*10
    for index in (8,9):
        g=load({WAV:wav(tone_wave),LEVEL:lab_record(index)})
        g.call(g.read(SLOT),EXPOSURE,0,0,0);g.setters.clear();started=start(g)
        data=next(s for a_,s in g.setters if a_==0x1006b94a)
        pcm=struct.unpack('<%dh'%(2*len(tone_wave)),g.u.mem_read(data[0],4*len(tone_wave)))
        want=tuple(max(-32768,min(32767,(v*GAINS[index-1])>>8)) for v in tone_wave for _ in (0,1))
        check(f'lab-level-{index}-pcm-exact',started==1 and pcm==want)

    report=dict(passed=True,count=len(checks),checks=checks,display_suite_checks=suite['checks'],steps=seen,
                module_sha256=m['module_sha256'],host_main_sha256=h['main_payload_sha256'],clip_sha256=hashlib.sha256(clip).hexdigest(),
                experimental=True,camera_access=False,scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks),display_suite_checks=suite['checks'])))


if __name__=='__main__':main()
