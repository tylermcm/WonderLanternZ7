"""Boot host + shutter-sound playback module in isolated assisted QEMU (MIT).

Supplies the module file and A:\\SHUTTER1.WAV through an explicit read-only file
fixture; no physical card. Observes the module's own counters and the live sound
service state while the real guest tasks run. No audible output is claimed.

The assisted emulator does not model the audio codec path: any sound request,
stock or private, ends in a data abort in the codec task (see
probe_z7_sound_differential.py). For the boot-preview build this probe therefore
checks that boot completes with nothing queued, then that the preview is queued
by the resident worker and reaches that same, already-characterized abort.
Playback itself needs a camera.
"""
import argparse,hashlib,json,struct,sys,threading,time
from pathlib import Path
from build_z7_module_host import ROOT,STATE,validate_candidate
from probe_z7_module_host import HostCamera
from audit_z7_shutter_sound_playback import wav as synthetic_wav
from probe_z7_sound_differential import FLASH_STORE,decode_exception
sys.path.insert(0,str(ROOT/'z7-qemu/tools'))
import interactive as ui

NAMES=('init_result','installed','boot_queued','starts','playback','rejects','finished','passthrough')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--module',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--clip',type=Path,help='Exact WAV to supply (default: synthetic 0.1 s clip)')
    p.add_argument('--no-wav',action='store_true',help='Supply no SHUTTER1.WAV (negative control)')
    a=p.parse_args()
    out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    out.mkdir(parents=True)
    meta=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(packet).hexdigest()==meta['module_sha256'] and meta['kind']=='original-Z7-shutter-sound-playback-trial'
    preview=meta['boot_preview']
    ui.FIRMWARE=a.build/'module-host.emulator.main.bin';ui.FIRMWARE_REPORT=a.build/'module-host.emulator.json'
    ui.STOCK_CONTAINER=ROOT/'.private/stock/Z_7_0380.bin';ui.validate_firmware=validate_candidate
    host=json.loads(ui.FIRMWARE_REPORT.read_text())
    from sound_file_fixture import SoundFileFixture
    from module_file_fixture import ModuleFileRemote
    clip=None if a.no_wav else (a.clip.read_bytes() if a.clip else synthetic_wav(frames=4800))
    fixture=SoundFileFixture(packet,clip)
    class BoundRemote(ModuleFileRemote):
        def __init__(self,port):super().__init__(port,fixture)
    ui.Remote=BoundRemote
    HostCamera.module_fixture=fixture;HostCamera.module_result_address=host['symbols']['z7_module_result'];HostCamera.module_waited=False
    camera=HostCamera(0,profile='menu')
    result=dict(checks=[],samples=[],module_sha256=meta['module_sha256'],boot_preview=preview,
                clip_sha256=hashlib.sha256(clip).hexdigest() if clip else None,
                wav_supplied=clip is not None,assisted_qemu=True,camera_access=False,physical_card=False,audible_output_claimed=False)
    def save():(out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    def check(name,ok):
        result['checks'].append(dict(name=name,passed=bool(ok)));save()
        if not ok:raise AssertionError(name)
    def sample(label):
        if camera.running:camera.pause()
        words=struct.unpack('<64I',camera.remote.memory(STATE,256));base=words[12]
        row=dict(label=label,module_base=hex(base),
                 slot=hex(int.from_bytes(camera.remote.memory(0xa188d278,4),'little')),
                 service_state=camera.remote.memory(0xa188d190,16).hex(),
                 mailbox=hex(int.from_bytes(camera.remote.memory(0xa18852ac,4),'little')),
                 events=list(fixture.events))
        if base:
            names=NAMES+(('worker_ticks',) if preview else ())
            for n in names:
                row[n]=int.from_bytes(camera.remote.memory(base+meta['symbols']['z7_sound_'+n],4),'little')
            row['start_handler']=hex(base+meta['symbols']['z7_sound_start']|1)
        result['samples'].append(row);save();return row
    def stop():
        if camera.proc and camera.proc.poll() is None:camera.proc.terminate()
    watchdog=threading.Timer(480,stop);watchdog.daemon=True;watchdog.start()
    try:
        camera.boot()
        first=sample('after-boot')
        check('module-loaded',int(first['module_base'],16)!=0)
        if clip is None:
            check('no-wav-no-install',first['installed']==0 and first['slot']=='0x1006bc47')
            check('no-wav-no-preview-queued',first['boot_queued']==0)
        else:
            check('wav-read-through-fixture',any(e.get('component')=='sound' and e.get('operation')=='read' for e in first['events']))
            check('installed-into-live-start-slot',first['installed']==1 and first['slot']==first['start_handler'])
            if preview:
                check('boot-completes-before-preview',first['boot_queued']==0 and first['playback']==0 and first['worker_ticks']<8)
                assert camera.remote.command(f'Z1,{FLASH_STORE:x},2')=='OK'
                timer=threading.Timer(60.0,lambda:camera.remote.sock.sendall(b'\x03'));timer.daemon=True
                camera.remote.send('c');camera.running=True;timer.start()
                camera.receive_stop();timer.cancel();camera.running=False
                regs=camera.remote.registers();pc=int(regs['r15'],16)
                stack=camera.remote.memory(int(regs['r13'],16),0x300) if pc==FLASH_STORE else b''
                result['exception']=decode_exception(stack,int(regs['r13'],16)) if stack else None
                camera.remote.command(f'z1,{FLASH_STORE:x},2')
                later=sample('after-preview')
                # The sound task preempts the worker (and then aborts) before the
                # worker stores enqueue's return value, so use the QUEUED state,
                # which enqueue sets before posting.
                check('worker-queued-preview-on-tick-8',later['worker_ticks']==8 and later['boot_queued'] in (0,1) and later['playback']==1)
                check('preview-reached-known-emulator-codec-abort',bool(result['exception']) and
                      result['exception']['kind']=='data-abort' and result['exception']['faulting_pc']=='0x100cbb3e')
            else:
                check('install-only-queues-nothing',first['boot_queued']==0 and first['playback']==0)
                camera.continue_guest();time.sleep(4)
                later=sample('after-4s-running')
                check('idle-guest-never-starts-private-job',later['starts']==later['rejects']==later['playback']==0)
                check('slot-still-installed-while-running',later['slot']==later['start_handler'])
    finally:
        log=getattr(camera,'live_log',None)
        try:
            if log and Path(log).exists():(out/'qemu-console.log').write_bytes(Path(log).read_bytes())
        except Exception:pass
        try:camera.close_guest()
        except Exception:pass
        watchdog.cancel()
    result['passed']=all(c['passed'] for c in result['checks']);save()
    print(json.dumps(dict(passed=result['passed'],checks=len(result['checks']),boot_preview=preview,wav_supplied=clip is not None)))


if __name__=='__main__':main()
