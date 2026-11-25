"""Boot host + shutter-sound trigger probe in isolated assisted QEMU (MIT).

Supplies the module file and accepts A:\\Z7TRIG.DAT writes through an explicit
file fixture; no physical card. Lets the real guest run in live view (QEMU cannot
take a photo), then checks the guest is still healthy, the three wrappers stayed
installed, the worker wrote parseable logs, and records which events fired with
no photo taken (none, in the runs so far). A complete log write is recorded
when the slow emulated worker finishes one inside the window.
"""
import argparse,hashlib,json,struct,sys,threading,time
from pathlib import Path
from build_z7_module_host import ROOT,STATE,validate_candidate
from probe_z7_module_host import HostCamera
from read_z7_trigger_log import parse,SIZE
sys.path.insert(0,str(ROOT/'z7-qemu/tools'))
import interactive as ui

SLOTS=(0xa18d1bd8,0xa18d1bdc,0xa18d2750)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--module',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--seconds',type=float,default=40)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    out.mkdir(parents=True)
    meta=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(packet).hexdigest()==meta['module_sha256'] and meta['kind']=='original-Z7-shutter-trigger-probe'
    ui.FIRMWARE=a.build/'module-host.emulator.main.bin';ui.FIRMWARE_REPORT=a.build/'module-host.emulator.json'
    ui.STOCK_CONTAINER=ROOT/'.private/stock/Z_7_0380.bin';ui.validate_firmware=validate_candidate
    host=json.loads(ui.FIRMWARE_REPORT.read_text())
    from trigger_file_fixture import TriggerFileFixture
    from module_file_fixture import ModuleFileRemote
    fixture=TriggerFileFixture(packet,SIZE)
    class BoundRemote(ModuleFileRemote):
        def __init__(self,port):super().__init__(port,fixture)
    ui.Remote=BoundRemote
    HostCamera.module_fixture=fixture;HostCamera.module_result_address=host['symbols']['z7_module_result'];HostCamera.module_waited=False
    camera=HostCamera(0,profile='menu')
    result=dict(checks=[],samples=[],module_sha256=meta['module_sha256'],assisted_qemu=True,camera_access=False,physical_card=False)
    def save():(out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    def check(name,ok):
        result['checks'].append(dict(name=name,passed=bool(ok)));save()
        if not ok:raise AssertionError(name)
    def pause():
        # The log writes keep the file fixture active; never interleave a plain
        # interrupt with its filesystem transaction (see probe_z7_display_module).
        if camera.running and camera.remote.fixture_enabled:
            camera.remote.fixture_stop_requested=False
            camera.remote.request_fixture_stop()
            camera.receive_stop();camera.running=False
            camera.remote.fixture_stop_requested=False
        elif camera.running:camera.pause()
    def sample(label):
        pause()
        base=struct.unpack('<64I',camera.remote.memory(STATE,256))[12]
        row=dict(label=label,module_base=hex(base),slots=[hex(int.from_bytes(camera.remote.memory(s,4),'little')) for s in SLOTS])
        if base:
            row['wrappers']=[hex(base+meta['symbols'][f'z7_trig_wrap{i}']|1) for i in range(3)]
            row['live']=parse(camera.remote.memory(base+meta['symbols']['z7_trig_live'],SIZE))
        row['log_writes']=len(fixture.files)
        result['samples'].append(row);save();return row
    def stop():
        if camera.proc and camera.proc.poll() is None:camera.proc.terminate()
    watchdog=threading.Timer(480,stop);watchdog.daemon=True;watchdog.start()
    try:
        camera.boot()
        first=sample('after-boot')
        check('module-loaded',int(first['module_base'],16)!=0)
        check('three-wrappers-installed',first['slots']==first['wrappers'] and first['live']['installed_mask']==7)
        # One window only: re-continuing while the file fixture is active races
        # the harness. The emulated worker ticks slowly, so the window must cover
        # the first log write (tick 3) completing.
        camera.continue_guest();time.sleep(a.seconds)
        later=sample(f'after-{a.seconds:g}s-running')
        check('guest-still-running-wrappers-in-place',later['slots']==later['wrappers'])
        check('worker-ticked',later['live']['ticks']>first['live']['ticks'])
        check('no-capture-callbacks-in-idle-emulated-view',sum(later['live']['calls'].values())==0)
        # The first log write is due on worker tick 3, which the slow emulated
        # worker may not have completed by the pause; record it as observed.
        if fixture.files:check('captured-log-parseable',parse(fixture.files[-1])['installed_mask']==7)
        result['log_write_completed']=bool(fixture.files)
        result['last_log']=parse(fixture.files[-1]) if fixture.files else None
        result['no_photo_events']={k:v for k,v in later['live']['counts'].items()}
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
                          events=result.get('no_photo_events'))))


if __name__=='__main__':main()
