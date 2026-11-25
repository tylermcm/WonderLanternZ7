"""Boot host + shutter-sound field-test module in isolated assisted QEMU (MIT).

Supplies the module, the exact SHUTTER1.WAV (read-only) and accepts Z7TRIG.DAT
writes through explicit file fixtures; no physical card. Checks that both parts
install in the real guest, then runs until the tick-8 preview reaches the
emulator's known codec abort (any sound request does; see
probe_z7_sound_differential.py) and decodes the exception frame.
"""
import argparse,hashlib,json,struct,sys,threading,time
from pathlib import Path
from build_z7_module_host import ROOT,STATE,validate_candidate
from probe_z7_module_host import HostCamera
from probe_z7_sound_differential import FLASH_STORE,decode_exception
from read_z7_trigger_log import parse,SIZE
sys.path.insert(0,str(ROOT/'z7-qemu/tools'))
import interactive as ui

SLOTS=(0xa18d1bd8,0xa18d1bdc,0xa18d2750)
SOUND_SLOT=0xa188d278


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('build','module','clip','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    out.mkdir(parents=True)
    meta=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes();clip=a.clip.read_bytes()
    assert hashlib.sha256(packet).hexdigest()==meta['module_sha256'] and meta['kind']=='original-Z7-shutter-sound-field-test'
    ui.FIRMWARE=a.build/'module-host.emulator.main.bin';ui.FIRMWARE_REPORT=a.build/'module-host.emulator.json'
    ui.STOCK_CONTAINER=ROOT/'.private/stock/Z_7_0380.bin';ui.validate_firmware=validate_candidate
    host=json.loads(ui.FIRMWARE_REPORT.read_text())
    from trigger_file_fixture import FieldFileFixture
    from module_file_fixture import ModuleFileRemote
    fixture=FieldFileFixture(packet,clip,SIZE)
    class BoundRemote(ModuleFileRemote):
        def __init__(self,port):super().__init__(port,fixture)
    ui.Remote=BoundRemote
    HostCamera.module_fixture=fixture;HostCamera.module_result_address=host['symbols']['z7_module_result'];HostCamera.module_waited=False
    camera=HostCamera(0,profile='menu')
    result=dict(checks=[],samples=[],module_sha256=meta['module_sha256'],clip_sha256=hashlib.sha256(clip).hexdigest(),
                assisted_qemu=True,camera_access=False,physical_card=False,audible_output_claimed=False)
    def save():(out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    def check(name,ok):
        result['checks'].append(dict(name=name,passed=bool(ok)));save()
        if not ok:raise AssertionError(name)
    def word(addr):return int.from_bytes(camera.remote.memory(addr,4),'little')
    def sample(label):
        base=struct.unpack('<64I',camera.remote.memory(STATE,256))[12];s=meta['symbols']
        row=dict(label=label,module_base=hex(base),slots=[hex(word(x)) for x in SLOTS],sound_slot=hex(word(SOUND_SLOT)))
        if base:
            row.update(wrappers=[hex(base+s[f'z7_trig_wrap{i}']|1) for i in range(3)],start_handler=hex(base+s['z7_sound_start']|1),
                       installed=word(base+s['z7_sound_installed']),playback=word(base+s['z7_sound_playback']),
                       boot_queued=word(base+s['z7_sound_boot_queued']),live=parse(camera.remote.memory(base+s['z7_trig_live'],SIZE)))
        row['log_writes']=len(fixture.files)
        result['samples'].append(row);save();return row
    def stop():
        if camera.proc and camera.proc.poll() is None:camera.proc.terminate()
    watchdog=threading.Timer(600,stop);watchdog.daemon=True;watchdog.start()
    try:
        camera.boot()
        if camera.running:camera.pause()
        first=sample('after-boot')
        check('module-loaded',int(first['module_base'],16)!=0)
        check('wav-read-and-sound-installed',first['installed']==1 and first['sound_slot']==first['start_handler'] and
              any(e.get('component')=='sound' and e.get('operation')=='read' for e in fixture.events))
        check('three-trigger-wrappers-installed',first['slots']==first['wrappers'])
        check('nothing-queued-at-boot',first['boot_queued']==0 and first['playback']==0 and first['live']['ticks']<8)
        assert camera.remote.command(f'Z1,{FLASH_STORE:x},2')=='OK'
        timer=threading.Timer(150.0,camera.remote.request_fixture_stop);timer.daemon=True
        camera.remote.fixture_stop_requested=False
        camera.remote.send('c');camera.running=True;timer.start()
        camera.receive_stop();timer.cancel();camera.running=False
        regs=camera.remote.registers();pc=int(regs['r15'],16)
        result['exception']=decode_exception(camera.remote.memory(int(regs['r13'],16),0x300),int(regs['r13'],16)) if pc==FLASH_STORE else None
        camera.remote.command(f'z1,{FLASH_STORE:x},2')
        later=sample('after-preview')
        check('preview-queued-by-worker-on-tick-8',later['live']['ticks']>=8 and later['playback']==1 and later['boot_queued'] in (0,1))
        check('preview-reached-known-emulator-codec-abort',bool(result['exception']) and result['exception']['faulting_pc']=='0x100cbb3e')
        check('wrappers-still-installed',later['slots']==later['wrappers'])
        if fixture.files:
            log=parse(fixture.files[-1]);result['last_log']=log
            check('log-written-with-sound-state',log['installed_mask']==7 and log['sound'] and log['sound']['wav_loaded'] and log['sound']['installed'])
        result['log_write_completed']=bool(fixture.files)
    finally:
        log=getattr(camera,'live_log',None)
        try:
            if log and Path(log).exists():(out/'qemu-console.log').write_bytes(Path(log).read_bytes())
        except Exception:pass
        if fixture.files:(out/'Z7TRIG.DAT').write_bytes(fixture.files[-1])
        try:camera.close_guest()
        except Exception:pass
        watchdog.cancel()
    result['passed']=all(c['passed'] for c in result['checks']);save()
    print(json.dumps(dict(passed=result['passed'],checks=len(result['checks']),log_writes=len(fixture.files),
                          exception=(result.get('exception') or {}).get('faulting_pc'))))


if __name__=='__main__':main()
