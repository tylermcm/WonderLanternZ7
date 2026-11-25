"""Walk Nikon's own menus in isolated assisted QEMU and diff property RAM (MIT).

Boots the stock-equivalent host with the install-only sound module and no WAV (it
installs nothing), presses an explicit key sequence through the original key
event path, saves a screenshot after each key, and records which words changed
in a RAM window between the first and last frame. Without --set it is read-only
observation. --set KEY=VALUE calls Nikon's own property setter (0x104065B0) in
the paused GUI task before the key walk, recording its return and the stored
word; that is a deliberate guest-state change, in the isolated emulator only.
No hooks, no camera.

Keys: right left up down menu play delete i ok disp.
"""
import argparse,hashlib,json,struct,sys,threading,time
from pathlib import Path
from build_z7_module_host import ROOT,validate_candidate
from probe_z7_module_host import HostCamera
sys.path.insert(0,str(ROOT/'z7-qemu/tools'))
import interactive as ui
from probe import call_fixture

CHECKPOINT=0x100531bc
# Extra buttons through Nikon's AutoOperation table (AF_SHORTCUT_RESEARCH.md).
ui.KEYS.update({'fn1':59,'af-on':27,'ss-center':51});ui.LABELS.update({'fn1':'Fn1','af-on':'AF-ON','ss-center':'Sub-selector center'})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('build','module','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--keys',required=True,help='Comma-separated key names')
    p.add_argument('--window',default='a24e0000:a24f0000',help='RAM window start:end (hex) to diff')
    p.add_argument('--settle',type=float,default=0.6)
    p.add_argument('--profile',choices=('menu','shooting'),default='menu')
    p.add_argument('--initial-wait',type=float,default=1.0)
    p.add_argument('--set',action='append',default=[],help='KEY=VALUE (hex or decimal) through the native property setter')
    p.add_argument('--read',action='append',default=[],help='KEY=ADDRESS to record before/after each set')
    p.add_argument('--module-symbol',action='append',default=[],help='Module variable to record at the end')
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    out.mkdir(parents=True)
    keys=[k for k in a.keys.split(',') if k]
    assert all(k in ui.KEYS for k in keys),keys
    meta=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(packet).hexdigest()==meta['module_sha256'] and not meta.get('boot_preview')
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
    camera=HostCamera(0,profile=a.profile)
    lo,hi=(int(x,16) for x in a.window.split(':'))
    result=dict(keys=keys,window=a.window,frames=[],assisted_qemu=True,camera_access=False,guest_writes=False)
    def save():(out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    def snapshot():return camera.remote.memory(lo,hi-lo)
    def advance(seconds):
        if camera.running:camera.pause()
        camera.continue_guest();time.sleep(seconds);camera.pause()
    def frame(name):
        camera.refresh()
        (out/(name+'.png')).write_bytes(camera.png)
        result['frames'].append(dict(name=name,sha256=hashlib.sha256(camera.png).hexdigest()));save()
    def stop():
        if camera.proc and camera.proc.poll() is None:camera.proc.terminate()
    watchdog=threading.Timer(900,stop);watchdog.daemon=True;watchdog.start()
    try:
        camera.boot_shooting() if a.profile=='shooting' else camera.boot()
        advance(a.initial_wait)
        reads={int(k,0):int(v,0) for k,v in (x.split('=') for x in a.read)}
        def words():return {hex(k):hex(int.from_bytes(camera.remote.memory(v,4),'little')) for k,v in reads.items()}
        result['sets']=[]
        for item in a.set:
            key,value=(int(x,0) for x in item.split('='))
            prior=words()
            if camera.running:camera.pause()
            r=call_fixture(camera.remote,camera.run_to(CHECKPOINT),0x104065b1,bytes(8),[key,value])
            advance(a.settle)
            result['sets'].append(dict(key=hex(key),value=value,return_r0=r['return_r0'],before=prior,after=words()));save()
        result['guest_writes']=bool(a.set)
        frame('00-start');before=snapshot()
        def diff(x,y):
            return [dict(address=hex(lo+o),before=hex(struct.unpack_from('<I',x,o)[0]),after=hex(struct.unpack_from('<I',y,o)[0]))
                    for o in range(0,len(x),4) if x[o:o+4]!=y[o:o+4]]
        last=before;result['after_ok']=[]
        for n,k in enumerate(keys,1):
            if camera.running:camera.pause()
            camera.key(camera.run_to(CHECKPOINT),k)
            advance(a.settle);frame(f'{n:02d}-{k}')
            if k=='ok':
                now=snapshot();result['after_ok'].append(dict(frame=f'{n:02d}-{k}',changed=diff(last,now)[:64]));last=now;save()
        advance(1.0);after=snapshot()
        result['final_reads']=words();result['module_values']={}
        base=struct.unpack('<64I',camera.remote.memory(0xa9700000,256))[12]
        for name in a.module_symbol:
            result['module_values'][name]=hex(int.from_bytes(camera.remote.memory(base+meta['symbols'][name],4),'little')) if base else None
        changed=[]
        for off in range(0,len(before),4):
            x,y=struct.unpack_from('<I',before,off)[0],struct.unpack_from('<I',after,off)[0]
            if x!=y:changed.append(dict(address=hex(lo+off),before=hex(x),after=hex(y)))
        result['changed_words']=changed[:400];result['changed_count']=len(changed)
        save()
    finally:
        try:camera.close_guest()
        except Exception:pass
        watchdog.cancel()
    print(json.dumps(dict(frames=len(result['frames']),changed=result.get('changed_count'))))


if __name__=='__main__':main()
