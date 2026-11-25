"""Read-only dump of original-Z7 capture-notification RAM slots in assisted QEMU (MIT).

Boots the host with the install-only shutter-sound module but no WAV (so it installs
nothing), then samples the capture-controller callback object and the still-file
callback slot at the GUI checkpoint and again after a few seconds of live view.
No hooks, no writes to guest memory, no camera.
"""
import argparse,hashlib,json,struct,sys,threading,time
from pathlib import Path
from build_z7_module_host import ROOT,validate_candidate
from probe_z7_module_host import HostCamera
sys.path.insert(0,str(ROOT/'z7-qemu/tools'))
import interactive as ui

REGIONS={'controller_objects':(0xa18d1b00,0x180),'still_file_slot':(0xa18d2700,0x80)}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--module',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private output file')
    meta=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(packet).hexdigest()==meta['module_sha256'] and not meta['boot_preview']
    ui.FIRMWARE=a.build/'module-host.emulator.main.bin';ui.FIRMWARE_REPORT=a.build/'module-host.emulator.json'
    ui.STOCK_CONTAINER=ROOT/'.private/stock/Z_7_0380.bin';ui.validate_firmware=validate_candidate
    host=json.loads(ui.FIRMWARE_REPORT.read_text())
    from sound_file_fixture import SoundFileFixture
    from module_file_fixture import ModuleFileRemote
    fixture=SoundFileFixture(packet,None)
    class BoundRemote(ModuleFileRemote):
        def __init__(self,port):super().__init__(port,fixture)
    ui.Remote=BoundRemote
    HostCamera.module_fixture=fixture;HostCamera.module_result_address=host['symbols']['z7_module_result'];HostCamera.module_waited=False
    camera=HostCamera(0,profile='menu')
    result=dict(host_main_sha256=host['main_payload_sha256'],assisted_qemu=True,camera_access=False,writes=False,samples=[])
    def stop():
        if camera.proc and camera.proc.poll() is None:camera.proc.terminate()
    watchdog=threading.Timer(420,stop);watchdog.daemon=True;watchdog.start()
    try:
        camera.boot()
        for label,wait in (('after-boot',0),('after-5s-live-view',5)):
            if wait:camera.continue_guest();time.sleep(wait)
            if camera.running:camera.pause()
            row=dict(label=label)
            for name,(base,size) in REGIONS.items():
                words=struct.unpack('<%dI'%(size//4),camera.remote.memory(base,size))
                row[name]={hex(base+4*i):hex(w) for i,w in enumerate(words) if w}
            result['samples'].append(row)
    finally:
        try:camera.close_guest()
        except Exception:pass
        watchdog.cancel()
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:len(v) if isinstance(v,dict) else v for k,v in result['samples'][-1].items()}))


if __name__=='__main__':main()
