"""Differential sound-request probe in isolated assisted QEMU (MIT).

Boots host + install-only shutter-sound module (with A:\\SHUTTER1.WAV supplied by
the explicit read-only file fixture), stops at the GUI checkpoint and queues ONE
request: none (baseline), a stock native beep record through the original post
function, or the module's private preview. Then runs 8 virtual-wall seconds with a
breakpoint on the RAM-resident flash-command store observed earlier (0xA2A40652),
recording whether it is reached and, if so, the registers and stack. No camera.

The RAM routine at 0xA2A40652 writes the CFI autoselect sequence (AAA<-AA,
554<-55, AAA<-90). In these runs it is reached from Nikon's CPU exception
reporter (0x100545EC), so the stack also holds the exception frame; it is decoded
into result['exception'] when found. --no-wav leaves the stock start slot in
place, making native mode a pure stock control.
"""
import argparse,hashlib,json,struct,sys,threading,time
from pathlib import Path
from build_z7_module_host import ROOT,STATE,validate_candidate
from probe_z7_module_host import HostCamera
from audit_z7_shutter_sound_playback import wav as synthetic_wav
sys.path.insert(0,str(ROOT/'z7-qemu/tools'))
import interactive as ui

FLASH_STORE=0xa2a40652
CHECKPOINT=0x100531bc
NATIVE_START_SLOT=0x1006bc47
NAMES=('init_result','installed','starts','playback','rejects','finished','passthrough')
# Return addresses of the original exception vector stubs into the reporter.
EXCEPTION_STUBS={0x10034f78:'undefined-instruction',0x10034fd4:'data-abort'}


def decode_exception(stack,sp):
    """Find 0x100545EC's frame (its local name strings sit at frame+0x14) and the
    register block the vector stub passed it (pushed r6). Returns None if absent."""
    at=stack.find(b'Prefetch abort.\0')
    if at<0x14:return None
    frame=at-0x14
    pushed=struct.unpack_from('<8I',stack,frame+0x60)  # r4..r10, lr
    block=pushed[2]-sp
    if not 0<=block<=len(stack)-68:return None
    regs=struct.unpack_from('<17I',stack,block)
    return dict(reporter_frame=hex(sp+frame),vector_return=hex(pushed[7]),
                kind=EXCEPTION_STUBS.get(pushed[7],'unknown'),register_block=hex(pushed[2]),
                registers={f'r{k}':hex(v) for k,v in enumerate(regs[:16])},cpsr=hex(regs[16]),
                faulting_pc=hex(regs[15]))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--module',type=Path,required=True)
    p.add_argument('--mode',choices=('none','native','module'),required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--no-wav',action='store_true',help='Supply no WAV: the module loads but installs nothing')
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    if a.no_wav and a.mode=='module':p.error('module mode needs the WAV')
    out.mkdir(parents=True)
    meta=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(packet).hexdigest()==meta['module_sha256'] and not meta['boot_preview']
    ui.FIRMWARE=a.build/'module-host.emulator.main.bin';ui.FIRMWARE_REPORT=a.build/'module-host.emulator.json'
    ui.STOCK_CONTAINER=ROOT/'.private/stock/Z_7_0380.bin';ui.validate_firmware=validate_candidate
    host=json.loads(ui.FIRMWARE_REPORT.read_text())
    from sound_file_fixture import SoundFileFixture
    from module_file_fixture import ModuleFileRemote
    fixture=SoundFileFixture(packet,None if a.no_wav else synthetic_wav(frames=4800))
    class BoundRemote(ModuleFileRemote):
        def __init__(self,port):super().__init__(port,fixture)
    ui.Remote=BoundRemote
    HostCamera.module_fixture=fixture;HostCamera.module_result_address=host['symbols']['z7_module_result'];HostCamera.module_waited=False
    camera=HostCamera(0,profile='menu')
    result=dict(mode=a.mode,wav_supplied=not a.no_wav,module_sha256=meta['module_sha256'],assisted_qemu=True,camera_access=False)
    def save():(out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    def counters(base):
        return {n:int.from_bytes(camera.remote.memory(base+meta['symbols']['z7_sound_'+n],4),'little') for n in NAMES}
    def stop():
        if camera.proc and camera.proc.poll() is None:camera.proc.terminate()
    watchdog=threading.Timer(480,stop);watchdog.daemon=True;watchdog.start()
    try:
        camera.boot()
        if camera.running:camera.pause()
        base=struct.unpack('<64I',camera.remote.memory(STATE,256))[12]
        result['before']=dict(counters=counters(base),service=camera.remote.memory(0xa188d190,4).hex(),
                              slot=hex(int.from_bytes(camera.remote.memory(0xa188d278,4),'little')))
        result['stock_start_slot']=result['before']['slot']==hex(NATIVE_START_SLOT)
        if a.no_wav:assert result['stock_start_slot'] and result['before']['counters']['installed']==0
        result['flash_code_prefix']=camera.remote.memory(FLASH_STORE&~0xff,0x200).hex()
        save()
        checkpoint=camera.run_to(CHECKPOINT)
        if a.mode=='native':
            # Persistent owned memory: the module's WAV load buffer, idle after init.
            area=base+meta['symbols']['z7_sound_wav']
            job,record=area,area+0x40
            camera.remote.write_memory(record,struct.pack('<9I',1,31,0,0,0,0,1,0,0))
            camera.remote.write_memory(job,struct.pack('<4I',record,0,0,0))
            r=camera.call(checkpoint,'Native beep request',0x100a2d79,b'\0'*8,[0x0418001e,job])
            result['request']=dict(kind='native-type0-record',post_returned_packet=r)
        elif a.mode=='module':
            r=camera.call(checkpoint,'Module preview request',(base+meta['symbols']['z7_sound_operation'])|1,b'\0'*8,[1,0,5,1])
            result['request']=dict(kind='module-private-preview',post_returned_packet=r)
        else:
            result['request']=dict(kind='none')
        save()
        assert camera.remote.command(f'Z1,{FLASH_STORE:x},2')=='OK'
        timer=threading.Timer(8.0,lambda:camera.remote.sock.sendall(b'\x03'));timer.daemon=True
        camera.remote.send('c');camera.running=True;timer.start()
        stop_packet=camera.receive_stop();timer.cancel()
        regs=camera.remote.registers();pc=int(regs['r15'],16)
        result['stop_pc']=hex(pc);result['flash_store_reached']=pc==FLASH_STORE
        if pc==FLASH_STORE:
            sp=int(regs['r13'],16)
            result['flash_registers']=regs
            stack=camera.remote.memory(sp,0x300)
            result['flash_stack']=stack.hex()
            result['exception']=decode_exception(stack,sp)
        camera.remote.command(f'z1,{FLASH_STORE:x},2')
        result['after']=dict(counters=counters(base),service=camera.remote.memory(0xa188d190,16).hex())
        save()
    except Exception as e:
        result['error']=repr(e);save();raise
    finally:
        log=getattr(camera,'live_log',None)
        try:
            if log and Path(log).exists():(out/'qemu-console.log').write_bytes(Path(log).read_bytes())
        except Exception:pass
        try:camera.close_guest()
        except Exception:pass
        watchdog.cancel()
    print(json.dumps(dict(mode=a.mode,wav_supplied=not a.no_wav,flash_store_reached=result.get('flash_store_reached'),
                          exception=result.get('exception'),stop_pc=result.get('stop_pc'),after=result.get('after'))))


if __name__=='__main__':main()
