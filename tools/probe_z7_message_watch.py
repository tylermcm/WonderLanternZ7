"""Record native message-queue posts while pressing keys in assisted QEMU (MIT).

Boots the host with the install-only sound module (no WAV, installs nothing),
presses keys through Nikon's AutoOperation path, then breaks on the queue post
0x101F243C and records each posted message's words. For the first message of a
chosen component (default 0x0416, PlaybackProcess) it arms a read watchpoint on
the message's command word, so the stop shows the receiving code. Observation
only: breakpoints and watchpoints, no guest writes, no camera.
"""
import argparse,collections,hashlib,json,struct,sys,threading,time
from pathlib import Path
from build_z7_module_host import ROOT,validate_candidate
from probe_z7_module_host import HostCamera
sys.path.insert(0,str(ROOT/'z7-qemu/tools'))
import interactive as ui

CHECKPOINT=0x100531bc
POST=0x101f243c


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('build','module','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--keys',default='play')
    p.add_argument('--component',type=lambda x:int(x,0),default=0x416)
    p.add_argument('--posts',type=int,default=4000)
    p.add_argument('--watch',type=int,default=6)
    p.add_argument('--profile',choices=('menu','shooting'),default='shooting')
    p.add_argument('--seconds',type=float,default=60)
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
    camera=HostCamera(0,profile=a.profile)
    result=dict(keys=a.keys,component=hex(a.component),posts=[],ids={},receivers=[],assisted_qemu=True,camera_access=False,guest_writes=False)
    def save():(out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    def stop():
        if camera.proc and camera.proc.poll() is None:camera.proc.terminate()
    watchdog=threading.Timer(1200,stop);watchdog.daemon=True;watchdog.start()
    r=None
    def word(x):return struct.unpack('<I',r.memory(x,4))[0]
    try:
        camera.boot_shooting() if a.profile=='shooting' else camera.boot()
        r=camera.remote
        if camera.running:camera.pause()
        camera.continue_guest();time.sleep(3);camera.pause()
        for k in a.keys.split(','):
            if camera.running:camera.pause()
            camera.key(camera.run_to(CHECKPOINT),k)
        camera.refresh();(out/'00-after-keys.png').write_bytes(camera.png)
        ids=collections.Counter();watched={}
        assert r.command(f'Z1,{POST:x},2')=='OK'
        timer=threading.Timer(a.seconds,r.request_fixture_stop);timer.daemon=True
        r.fixture_stop_requested=False
        r.send('c');camera.running=True;timer.start()
        total=0
        while total<a.posts:
            total+=1
            pkt=r.receive()
            if 'thread:' not in pkt or r.fixture_stop_requested:camera.running=False;break
            thread=pkt.split('thread:')[1].split(';')[0];r.command('Hg'+thread)
            regs=r.registers();pc=int(regs['r15'],16)
            if pc==POST:
                q=int(regs['r0'],16);m=int(regs['r1'],16)
                words=[word(m+4*i) for i in range(7)] if 0xa0000000<=m<0xb0000000 and not m&3 else []
                if words:
                    ids[hex(words[4])]+=1
                    if words[4]>>16==a.component and len(watched)<a.watch and m not in watched:
                        result['posts'].append(dict(queue=hex(q),message=hex(m),words=[hex(w) for w in words],lr=regs['r14'],thread=thread))
                        if r.command(f'Z3,{m+16:x},4')=='OK':watched[m]=words[4]
                # step past the breakpoint
                r.command(f'z1,{POST:x},2');r.command('Hc'+thread);r.send('s');r.receive();r.command('Hc-1')
                r.command(f'Z1,{POST:x},2')
            else:
                hit=dict(pc=hex(pc),lr=regs['r14'],thread=thread,r0=regs['r0'],r1=regs['r1'],r4=regs['r4'],stop=pkt[:80])
                result['receivers'].append(hit)
                for mm in list(watched):r.command(f'z3,{mm+16:x},4')
                r.command('Hc'+thread);r.send('s');r.receive();r.command('Hc-1')
                for mm in list(watched):r.command(f'Z3,{mm+16:x},4')
                if len(result['receivers'])>=3*a.watch:
                    for mm in list(watched):r.command(f'z3,{mm+16:x},4')
                    watched.clear()
            result['ids']=dict(ids.most_common(60));save()
            r.send('c')
        timer.cancel()
    finally:
        try:
            if r is None:raise RuntimeError
            r.command(f'z1,{POST:x},2')
            if camera.running:
                r.fixture_stop_requested=False;r.request_fixture_stop()
                try:camera.receive_stop()
                except Exception:pass
        except Exception:pass
        save()
        try:camera.close_guest()
        except Exception:pass
        watchdog.cancel()
    print(json.dumps(dict(posts=len(result['posts']),receivers=result['receivers'][:6],top=list(result['ids'].items())[:12])))


if __name__=='__main__':main()
