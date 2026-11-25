"""Record Nikon switch-state words while pressing buttons in assisted QEMU (MIT).

Presses buttons through Nikon's own AutoOperation entry 0x105230A6 (the same
path the QEMU harness uses for menu keys) and puts write watchpoints on the
switch-state object 0xA1F90AA0 (returned by 0x101B4A60) at +4, +0x18 and +0x2C.
Every write is recorded with the writing PC, so press and release edges, and the
code that publishes them, are visible. The watchpoints only observe. No hooks,
no camera.
"""
import argparse,hashlib,json,struct,sys,threading,time
from pathlib import Path
from build_z7_module_host import ROOT,validate_candidate
from probe_z7_module_host import HostCamera
sys.path.insert(0,str(ROOT/'z7-qemu/tools'))
import interactive as ui

CHECKPOINT=0x100531bc
SWITCH=0xa1f90aa0
WORDS=(SWITCH+4,SWITCH+0x18,SWITCH+0x2c)
BUTTONS={'fn1':59,'af-on':27,'fn2':60,'ss-center':51,'movie':9}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('build','module','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--buttons',default='fn1,af-on,fn2,ss-center,movie')
    p.add_argument('--hits',type=int,default=24)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    out.mkdir(parents=True)
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
    result=dict(buttons={},assisted_qemu=True,camera_access=False,switch_object=hex(SWITCH))
    def save():(out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    def words():return [hex(int.from_bytes(camera.remote.memory(w,4),'little')) for w in WORDS]
    def stop():
        if camera.proc and camera.proc.poll() is None:camera.proc.terminate()
    watchdog=threading.Timer(900,stop);watchdog.daemon=True;watchdog.start()
    try:
        camera.boot()
        if camera.running:camera.pause()
        camera.continue_guest();time.sleep(3);camera.pause()
        result['idle']=words();save()
        for name in a.buttons.split(','):
            index=BUTTONS[name]
            values=[0]*8;values[index//32]=1<<(index%32);values[4]=10
            if camera.running:camera.pause()
            pkt=camera.run_to(CHECKPOINT)
            before=words()
            camera.call(pkt,f'Press {name}',0x105230a6,struct.pack('<8I',*values),[('scratch',0),5,('scratch',20)])
            after_call=words()
            for w in WORDS:assert camera.remote.command(f'Z2,{w:x},4')=='OK'
            hits=[]
            timer=threading.Timer(4.0,camera.remote.request_fixture_stop);timer.daemon=True
            camera.remote.fixture_stop_requested=False
            camera.remote.send('c');camera.running=True;timer.start()
            while len(hits)<a.hits:
                packet_=camera.remote.receive()
                if 'watch' not in packet_:break
                thread=packet_.split('thread:')[1].split(';')[0];camera.remote.command('Hg'+thread)
                regs=camera.remote.registers()
                hits.append(dict(pc=regs['r15'],lr=regs['r14'],words=words()))
                # Step past the write, then continue with the watchpoints still armed.
                for w in WORDS:camera.remote.command(f'z2,{w:x},4')
                camera.remote.command('Hc'+thread);camera.remote.send('s');camera.remote.receive();camera.remote.command('Hc-1')
                for w in WORDS:camera.remote.command(f'Z2,{w:x},4')
                hits[-1]['after']=words()
                camera.remote.send('c')
            timer.cancel()
            if camera.running:
                camera.remote.fixture_stop_requested=False;camera.remote.request_fixture_stop()
                try:camera.receive_stop()
                except Exception:pass
            camera.running=False;camera.remote.fixture_stop_requested=False
            for w in WORDS:camera.remote.command(f'z2,{w:x},4')
            result['buttons'][name]=dict(ao_index=index,before=before,after_call=after_call,hits=hits,end=words());save()
    finally:
        try:camera.close_guest()
        except Exception:pass
        watchdog.cancel()
    print(json.dumps({k:dict(before=v['before'],after_call=v['after_call'],hits=[h['after'] for h in v['hits']][:4]) for k,v in result['buttons'].items()}))


if __name__=='__main__':main()
