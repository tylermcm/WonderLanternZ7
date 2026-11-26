"""Shutter-sound folder build of the LCD module: offline audit (MIT).

Same fixture as audit_z7_lcd_shutter_sound.py. Runs the 277-check display
suite unchanged, then checks the folder feature: which of A:\\SHUTTER1.WAV and A:\\SHUTTER\\SOUND01-10
exist is scanned once at power-on; only the selected file is loaded; the root
Shutter sound row opens a page with Volume, Sound and Back; OK on Sound steps
through the available sounds only, and the worker loads the new file when no
sound is playing and then plays a preview; a photo uses the selected file; the
choice is saved with the level (Z7SND.DAT version 2) and restored, a saved
file that is gone falls back to the first available one, a version-1 file
keeps its level with Card, and Back returns to the root page.
No camera, no card.
"""
import argparse,hashlib,json,struct,sys
import audit_z7_lcd_preset_persistence as preset_suite
from pathlib import Path
from audit_z7_lcd_shutter_sound import SoundAware,WAV,LEVEL,SLOT,EXPOSURE,START_SLOT,SND_STATE,wav,level_record
from audit_z7_lcd_grid_persistence import NEW,OBJECT,v3record
from audit_z7_settings_files import PATHS
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output

FOLDER=['A:\\SHUTTER\\SOUND%02d.WAV'%i for i in range(1,11)]


def record_v2(level,sound):
    word=level|(sound<<8)
    check=0x444e5337^(2<<8)^(word*0x01010101)^0xa5a5a5a5
    return struct.pack('<4I',0x444e5337,2,word,check&0xffffffff)


def tone(seed,frames=480):
    return wav([((i*seed*37)%20000)-10000 for i in range(frames)])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256'] and hashlib.sha256(packet).hexdigest()==m['module_sha256']
    assert m['configuration']['sound_folder']
    symbols=m['symbols'];checks=[]
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
    journal={NEW[0]:v3record((3,15,1,0,5,0,127,7,0,127,4),0)}
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
    def ticks(f,n=1):
        for _ in range(n):f.call(h['symbols']['z7_module_worker_tick'])
    def finish(f):f.u.mem_write(SND_STATE,bytes(4));f.write(f.base+symbols['z7_sound_playback'],0)
    def reads(f):return [e[1] for e in f.sound_events if e[0]=='read' and e[1]!=LEVEL]  # sound files only
    def played_pcm(f):
        msg=0xa2970100;f.u.mem_write(msg,struct.pack('<7I',0,0,0,0,0x0418001e,f.sends[-1][1],msg))
        f.setters.clear();assert f.call(f.read(START_SLOT),msg)==1
        data=next(s for a_,s in f.setters if a_==0x1006b94a)
        return bytes(f.u.mem_read(data[0],data[1]))
    sounds={WAV:tone(1),FOLDER[0]:tone(2),FOLDER[2]:tone(3),FOLDER[9]:tone(4)}

    f=load(dict(sounds))
    check('scan-finds-available-files',word(f,'z7_sf_available')==(1|1<<1|1<<3|1<<10))
    check('only-selected-file-read-at-power-on',reads(f)==[WAV] and word(f,'z7_sf_selected')==0 and word(f,'z7_sf_loaded')==0)
    lab=labels(f)
    check('root-row-shows-shutter-sound-level',lab.get(237)=='Shutter sound' and lab.get(244)=='5')
    press(f,6)
    lab=labels(f)
    check('row-opens-sound-page',word(f,'z7_settings_view')==5 and lab.get(231)=='Volume' and lab.get(238)=='5' and
          lab.get(232)=='Sound' and lab.get(239)=='Card' and lab.get(233)=='Back' and not f.sends)
    press(f,1)
    check('sound-steps-to-next-available',word(f,'z7_sf_selected')==1 and labels(f).get(239)=='1' and not f.sends and reads(f)==[WAV])
    ticks(f)
    check('worker-loads-new-file-then-previews',reads(f)==[WAV,FOLDER[0]] and word(f,'z7_sf_loaded')==1 and len(f.sends)==1)
    pcm=played_pcm(f);finish(f)
    src=struct.unpack('<480h',tone(2)[44:])
    check('preview-plays-selected-file',struct.unpack('<%dh'%(len(pcm)//2),pcm)[0::2]==tuple(src))
    press(f,1);press(f,1)
    check('sound-skips-missing-files',word(f,'z7_sf_selected')==10 and labels(f).get(239)=='10')
    press(f,1);check('sound-wraps-to-card',word(f,'z7_sf_selected')==0)
    press(f,1);press(f,1)  # back to 3
    f.write(f.base+symbols['z7_sound_playback'],2);ticks(f)
    check('no-load-while-playing',word(f,'z7_sf_loaded')==1 and len(reads(f))==2)
    finish(f);ticks(f)
    check('loads-after-playback-ends',word(f,'z7_sf_loaded')==3 and reads(f)[-1]==FOLDER[2])
    finish(f)
    press(f,0);check('volume-row-steps-level',word(f,'z7_sl_level')==6 and labels(f).get(238)=='6')
    finish(f)
    f.call(f.read(SLOT),EXPOSURE,0,0,0)
    photo=played_pcm(f)
    check('photo-plays-selected-file',struct.unpack('<%dh'%(len(photo)//2),photo)[0::2]==tuple(max(-32768,min(32767,(v*362)>>8)) for v in struct.unpack('<480h',tone(3)[44:])))
    finish(f)
    press(f,2)
    check('back-returns-to-root',word(f,'z7_settings_view')==0 and labels(f).get(237)=='Shutter sound')
    ticks(f,5)
    check('choice-saved-with-level',f.sound_files.get(LEVEL)==record_v2(6,3))
    g=load({**sounds,LEVEL:f.sound_files[LEVEL]})
    check('reload-restores-sound-and-level',word(g,'z7_sf_selected')==3 and word(g,'z7_sl_level')==6 and reads(g)==[FOLDER[2]])
    g=load({WAV:tone(1),FOLDER[9]:tone(4),LEVEL:record_v2(4,3)})
    check('missing-saved-file-falls-back',word(g,'z7_sf_selected')==0 and word(g,'z7_sl_level')==4)
    g=load({WAV:tone(1),LEVEL:level_record(8)})
    check('version-1-file-keeps-level-with-card',word(g,'z7_sl_level')==8 and word(g,'z7_sf_selected')==0 and word(g,'z7_sl_loaded')==1)
    g=load({FOLDER[4]:tone(5)})
    check('folder-only-card-uses-first-folder-sound',word(g,'z7_sf_selected')==5 and word(g,'z7_sl_installed')==1)
    g=load({})
    check('no-sound-files-stays-off',word(g,'z7_sl_installed')==0 and g.read(SLOT)==0x101426a9)
    press(g,6);check('page-shows-none',labels(g).get(239)=='None')
    report=dict(passed=True,count=len(checks),checks=checks,display_suite_checks=suite['checks'],module_sha256=m['module_sha256'],host_main_sha256=h['main_payload_sha256'],
                camera_access=False,scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
