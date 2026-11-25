"""Read-only RAM pattern search and dump in assisted QEMU (MIT).

Boots the host with the install-only shutter-sound module but no WAV (so it installs
nothing), then searches a RAM range for a sequence of 32-bit words (for example a
native function-pointer pair) at the GUI checkpoint. No hooks, no writes to guest
memory, no camera.
"""
import argparse,hashlib,json,struct,sys,threading,time
from pathlib import Path
from build_z7_module_host import ROOT,validate_candidate
from probe_z7_module_host import HostCamera
sys.path.insert(0,str(ROOT/'z7-qemu/tools'))
import interactive as ui

CHUNK=0x8000


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--module',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--pattern',required=True,help='Comma-separated 32-bit words')
    p.add_argument('--range',required=True,help='start:end, hex')
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
    result=dict(host_main_sha256=host['main_payload_sha256'],assisted_qemu=True,camera_access=False,writes=False)
    def stop():
        if camera.proc and camera.proc.poll() is None:camera.proc.terminate()
    watchdog=threading.Timer(420,stop);watchdog.daemon=True;watchdog.start()
    try:
        camera.boot()
        if camera.running:camera.pause()
        needle=b''.join(struct.pack('<I',int(w,16)) for w in a.pattern.split(','))
        lo,hi=(int(x,16) for x in a.range.split(':'))
        hits=[];tail=b''
        for base in range(lo,hi,CHUNK):
            try:data=camera.remote.memory(base,CHUNK)
            except Exception as e:result.setdefault('unreadable',[]).append(hex(base));tail=b'';continue
            buf=tail+data;origin=base-len(tail);pos=buf.find(needle)
            while pos>=0:
                if (origin+pos)%4==0 and hex(origin+pos) not in hits:hits.append(hex(origin+pos))
                pos=buf.find(needle,pos+1)
            tail=data[-(len(needle)-1):] if len(needle)>1 else b''
        result.update(pattern=a.pattern,range=a.range,hits=hits)
        result['context']={h:[hex(w) for w in struct.unpack('<16I',camera.remote.memory(int(h,16)-16,64))] for h in hits[:8]}
    finally:
        try:camera.close_guest()
        except Exception:pass
        watchdog.cancel()
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(hits=result.get('hits'),unreadable=len(result.get('unreadable',[])))))


if __name__=='__main__':main()
