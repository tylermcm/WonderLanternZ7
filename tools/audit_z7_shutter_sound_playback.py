"""Shutter-sound playback trial: native post/dispatch/completion execution (MIT).

Executes the original-Z7 module host loader, the compiled module (WAV load, decode,
install, enqueue, private start handler) and the original sound-service post
function 0x100A2D78, message dispatcher 0x1006BB58 and completion 0x100A2D5E.
Supplied boundaries: filesystem request dispatcher, allocator, mailbox send
0x101F243C, speaker checks, the four low-level audio setters and the native start
handler (recorded, not executed). Handler-table contents come from a read-only
stock QEMU dump. No audio hardware, DMA, scheduler timing or camera is exercised.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3
from audit_z7_module_host import HostFixture
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output

WAV_PATH='A:\\SHUTTER1.WAV'
MAX_WAV=48000*4+4096
POST,DISPATCH,COMPLETION=0x100a2d78,0x1006bb58,0x100a2d5f
SEND,SPEAKER,SECOND=0x101f243c,0x100cf90a,0x100cf98c
SETTERS={0x1006b794:'format',0x1006b62c:'tones',0x1006b94a:'data',0x1006b7dc:'dma-start'}
NATIVE_START=0x1006bc46
STATE_ADDR,CONTEXT,MAILBOX,SLOT=0xa188d190,0xa21ab994,0xa18852ac,0xa188d278
LIVE_TABLE={0xa188d278:0x1006bc47,0xa188d298:0x1006be37,0xa188d29c:0x1006bee3,0xa188d28c:0x1006be25}
NOT_FOUND=0x80000010


def wav(channels=1,rate=48000,bits=16,frames=480,extra=b'',data_override=None,riff_delta=0,pad_chunk=False):
    samples=b''.join(struct.pack('<h',((i*997)%65536)-32768 if channels==1 else 0)+
                     (struct.pack('<h',-((i*331)%30000)) if channels==2 else b'') for i in range(frames))
    if channels==2:
        samples=b''.join(struct.pack('<hh',((i*997)%65536)-32768,-((i*331)%30000)) for i in range(frames))
    data=samples if data_override is None else data_override
    block=channels*bits//8
    fmt=struct.pack('<HHIIHH',1,channels,rate,rate*block,block,bits)
    body=b'WAVE'+b'fmt '+struct.pack('<I',16)+fmt+extra
    if pad_chunk:body+=b'LIST'+struct.pack('<I',3)+b'abc\0'
    body+=b'data'+struct.pack('<I',len(data))+data
    return b'RIFF'+struct.pack('<I',len(body)+riff_delta)+body


def reference(blob):
    """Expected interleaved stereo PCM for a valid test WAV (independent of module)."""
    channels=struct.unpack_from('<H',blob,22)[0]
    pos=blob.index(b'data');size=struct.unpack_from('<I',blob,pos+4)[0];data=blob[pos+8:pos+8+size]
    out=[]
    for i in range(0,size,channels*2):
        left=struct.unpack_from('<h',data,i)[0]
        right=struct.unpack_from('<h',data,i+2)[0] if channels==2 else left
        out+=[left,right]
    return out


class SoundFixture(HostFixture):
    def __init__(self,raw,host,packet,files=None,speaker=1,second=0,setter_results=None,
                 mailbox=0xa2950000,fingerprint_patch=None,slot_value=None,fail_alloc_after=None):
        super().__init__(raw,host,packet)
        self.u.mem_map(0xa21a0000,0x20000)
        self.files=dict(files or {});self.handles={};self.next_fd=0x40
        self.file_events=[];self.sends=[];self.setter_calls=[];self.native_starts=[];self.cleans=[]
        self.speaker,self.second=speaker,second
        self.setter_results=dict(setter_results or {})
        self.fail_alloc_after=fail_alloc_after
        for address,value in LIVE_TABLE.items():self.u.mem_write(address,struct.pack('<I',value))
        if slot_value is not None:self.u.mem_write(SLOT,struct.pack('<I',slot_value))
        self.u.mem_write(STATE_ADDR,bytes(16))
        self.u.mem_write(MAILBOX,struct.pack('<I',mailbox))
        if fingerprint_patch:self.u.mem_write(fingerprint_patch,b'\0\0\0\0')

    def r(self,reg):return self.u.reg_read(reg)
    def read(self,a):return struct.unpack('<I',bytes(self.u.mem_read(a,4)))[0]

    def hook(self,u,address,size,context):
        if address==0x1027beae:
            p=self.r(UC_ARM_REG_R0);words=struct.unpack('<42I',u.mem_read(p,168));op=bytes(u.mem_read(p+0x9c,1))[0]
            if op==5 and self.cstring(words[4])==WAV_PATH:
                assert words[5:7]==(0,0),'WAV open must be read-only'
                self.file_events.append(('open',WAV_PATH))
                if WAV_PATH not in self.files:self.ret(NOT_FOUND);return
                fd=self.next_fd;self.next_fd+=1;self.handles[fd]=0;self.ret(fd);return
            if op==8 and words[7] in self.handles:
                fd,pointer,capacity,actual=words[7],words[10],words[11],words[12]
                assert pointer%64==0 and capacity==MAX_WAV+1,'WAV read signature'
                data=self.files[WAV_PATH][self.handles[fd]:self.handles[fd]+capacity]
                if data:u.mem_write(pointer,data)
                self.handles[fd]+=len(data);u.mem_write(actual,struct.pack('<I',len(data)))
                self.file_events.append(('read',capacity,len(data)));self.ret(0);return
            if op==6 and words[7] in self.handles:
                del self.handles[words[7]];self.file_events.append(('close',));self.ret(0);return
            if op in (9,13):raise AssertionError('Sound module must never write or create files')
        if address==0x1016fe38 and self.fail_alloc_after is not None:
            if self.fail_alloc_after==0:self.ret(0);return
            self.fail_alloc_after-=1
        if address==SEND:
            self.sends.append((self.r(UC_ARM_REG_R0),self.r(UC_ARM_REG_R1)));self.ret(0);return
        if address==SPEAKER:
            u.mem_write(self.r(UC_ARM_REG_R0),bytes([self.speaker]));self.ret(0);return
        if address==SECOND:self.ret(self.second);return
        if address in SETTERS:
            name=SETTERS[address];arg=self.r(UC_ARM_REG_R0)
            self.setter_calls.append((name,struct.unpack('<8I',bytes(u.mem_read(arg,32))),self.r(UC_ARM_REG_R1)))
            self.ret(self.setter_results.get(name,1));return
        if address==NATIVE_START:
            self.native_starts.append(self.r(UC_ARM_REG_R0));self.ret(0x5a);return
        if address==0x101e9f38:self.cleans.append((self.r(UC_ARM_REG_R0),self.r(UC_ARM_REG_R1)))
        super().hook(u,address,size,context)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','boot_module','output'):p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
    p.add_argument('--clip',type=Path,help='Exact SHUTTER1.WAV intended for the card')
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256']
    def module(d):
        m=json.loads((d/'module.json').read_text());packet=(d/'Z7APP.BIN').read_bytes()
        assert hashlib.sha256(packet).hexdigest()==m['module_sha256'];return m,packet
    m,packet=module(a.module);bm,bpacket=module(a.boot_module)
    assert not m['boot_preview'] and bm['boot_preview'] and not m['photo_trigger']
    checks=[]
    def check(name,ok):
        assert ok,name
        checks.append(name)
    def load(files=None,packet=packet,meta=m,**kw):
        f=SoundFixture(raw,h,packet,files=files,**kw)
        f.loaded=f.call(h['symbols']['z7_module_load_once'],STATE)
        f.setword(40,f.loaded)  # z7_module_worker stores the status before its resident ticks
        f.base=f.words()[12];f.s=meta['symbols'];return f
    def sym(f,name):return f.base+f.s[name]
    def val(f,name):return f.read(sym(f,name))
    good=wav(frames=480)

    # Decode: valid/invalid WAVs through the compiled decoder (operation 2).
    f=load({WAV_PATH:good})
    buf,pcm=0xa2980000,0xa29a0000
    cases=[('mono-48k',wav(),True),('stereo-48k',wav(channels=2),True),('extra-list-chunk-odd-pad',wav(pad_chunk=True),True),
           ('one-second-max',wav(frames=48000),True),('over-one-second',wav(frames=48001),False),
           ('44k1-rejected',wav(rate=44100),False),('8-bit-rejected',wav(bits=8),False),
           ('riff-size-mismatch',wav(riff_delta=2),False),('odd-data-bytes',wav(data_override=b'\1\2\3'),False),
           ('empty-data',wav(data_override=b''),False),('not-riff',b'RIFX'+good[4:],False),('truncated',good[:40],False)]
    for name,blob,valid in cases:
        f.u.mem_write(buf,blob);f.u.mem_write(pcm,bytes(48000*4))
        n=f.call(sym(f,'z7_sound_operation'),2,buf,len(blob),pcm)
        if valid:
            expect=reference(blob)
            got=list(struct.unpack('<%dh'%(len(expect)),bytes(f.u.mem_read(pcm,len(expect)*2))))
            check('decode-'+name,n==len(expect)*2 and got==expect)
        else:check('decode-rejects-'+name,n==0)

    # Load and install.
    check('module-loads',f.loaded==8)
    check('loads-only-shutter1-read-only',f.file_events==[('open',WAV_PATH),('read',MAX_WAV+1,len(good)),('close',)])
    check('installs-after-valid-clip',val(f,'z7_sound_init_result')==3 and val(f,'z7_sound_installed')==1)
    check('start-slot-holds-module-handler',f.read(SLOT)==(sym(f,'z7_sound_start')|1))
    check('other-handler-table-entries-unchanged',all(f.read(a)==v for a,v in LIVE_TABLE.items() if a!=SLOT))
    check('clip-bytes-recorded',f.read(sym(f,'z7_sound_clip_bytes'))==480*4)
    for name,kw in (('missing-file',dict(files={})),('malformed-file',dict(files={WAV_PATH:wav(rate=44100)})),
                    ('foreign-slot',dict(files={WAV_PATH:good},slot_value=0x10123457))):
        g=load(**kw)
        installed=g.read(sym(g,'z7_sound_installed'))
        slot=g.read(SLOT)
        check('no-install-'+name,g.loaded==8 and not installed and slot==kw.get('slot_value',0x1006bc47))
        check('enqueue-refused-'+name,g.call(sym(g,'z7_sound_operation'),1,0,5,1)==0 and not g.sends)
    # A firmware mismatch fails module init: the host frees the module (INIT_FAILED=7).
    g=SoundFixture(raw,h,packet,files={WAV_PATH:good},fingerprint_patch=0x1006b7dc)
    result=g.call(h['symbols']['z7_module_load_once'],STATE)
    check('firmware-mismatch-fails-init-and-is-released',result==7 and g.words()[12]==0)
    check('firmware-mismatch-touches-no-file-or-slot',g.file_events==[] and g.read(SLOT)==0x1006bc47)

    # Enqueue -> native post -> message layout.
    f=load({WAV_PATH:good})
    check('preview-enqueued',f.call(sym(f,'z7_sound_operation'),1,0,5,1)==1)
    check('one-mailbox-send',len(f.sends)==1 and f.sends[0][0]==0xa2950000)
    msg=f.sends[0][1];job=sym(f,'z7_sound_job_slot')
    words=struct.unpack('<7I',bytes(f.u.mem_read(msg,28)))
    check('native-post-message-layout',words[3]==COMPLETION and words[4]==0x0418001e and words[5]==job and words[6]==msg)
    check('state-queued',val(f,'z7_sound_playback')==1)
    check('second-enqueue-while-queued-refused',f.call(sym(f,'z7_sound_operation'),1,0,5,1)==0 and len(f.sends)==1)

    # Native dispatcher -> module start -> setters -> completion.
    live_before=dict(f.live)
    f.call(DISPATCH,msg)
    check('setters-called-in-native-order',[c[0] for c in f.setter_calls]==['format','tones','data','dma-start'])
    fmt,tones,data,start=[c[1] for c in f.setter_calls]
    check('setters-receive-native-message',all(c[2]==msg for c in f.setter_calls))
    check('format-48k-stereo-pcm-bytes',fmt[0]==0x01010502 and fmt[1]==480*4)
    check('tones-native-shape',tones[:7]==(2,1,31,0,0,0,0))
    pcm_addr=sym(f,'z7_sound_pcm')
    check('data-points-at-module-pcm',data[:5]==(pcm_addr,480*4,1,0,0))
    check('dma-start-native-callback',start[0]==2 and start[1]==0x1006bc09)
    expect=reference(good)
    got=list(struct.unpack('<%dh'%len(expect),bytes(f.u.mem_read(pcm_addr,len(expect)*2))))
    check('full-volume-pcm-matches-wav',got==expect)
    check('pcm-cleaned-before-dma',(pcm_addr,480*4) in f.cleans)
    ctx=struct.unpack('<9I',bytes(f.u.mem_read(CONTEXT,36)))
    check('record-copied-to-native-context',ctx[:8]==(1,31,0,0,0,0,1,18) and ctx[8]==(sym(f,'z7_sound_done')|1))
    check('service-state-playing-left-only',bytes(f.u.mem_read(STATE_ADDR,3))==b'\1\1\0')
    check('dispatcher-wrote-success-status',f.read(job+8)==0)
    check('completion-freed-message',msg not in f.live and set(f.live)<=set(live_before))
    check('module-state-playing',val(f,'z7_sound_playback')==2 and val(f,'z7_sound_starts')==1)
    check('enqueue-refused-while-playing',f.call(sym(f,'z7_sound_operation'),1,0,5,1)==0 and len(f.sends)==1)
    done=ctx[8]
    f.call(done,0x04180022,0);check('started-notify-keeps-playing',val(f,'z7_sound_playback')==2)
    f.call(done,0x04180023,0);check('finished-event-returns-idle',val(f,'z7_sound_playback')==0 and val(f,'z7_sound_finished')==1)
    f.u.mem_write(STATE_ADDR,b'\0\0\0')
    check('replay-after-finish',f.call(sym(f,'z7_sound_operation'),1,0,3,1)==1)
    f.call(DISPATCH,f.sends[-1][1])
    gain=[(s*154)>>8 for s in expect]
    got=list(struct.unpack('<%dh'%len(expect),bytes(f.u.mem_read(pcm_addr,len(expect)*2))))
    check('volume-three-scales-pcm',got==gain)

    # Native requests pass through untouched.
    f.u.mem_write(STATE_ADDR,b'\0\0\0')
    native_job=0xa2970000;f.u.mem_write(native_job,bytes(16))
    nmsg=0xa2970100;f.u.mem_write(nmsg,struct.pack('<7I',0,0,0,0,0x0418001e,native_job,nmsg))
    setters_before=len(f.setter_calls)
    f.call(DISPATCH,nmsg)
    check('native-request-passes-through-same-message',f.native_starts==[nmsg] and len(f.setter_calls)==setters_before)
    check('native-request-counted',val(f,'z7_sound_passthrough')==1)

    # Rejections release the private job.
    for name,kw in (('speaker-unavailable',dict(speaker=0)),('second-check-busy',dict(second=1)),
                    ('tone-setter-fails',dict(setter_results={'tones':0})),('dma-start-fails',dict(setter_results={'dma-start':0}))):
        g=load({WAV_PATH:good},**kw)
        check('enqueue-'+name,g.call(sym(g,'z7_sound_operation'),1,0,5,1)==1)
        g.call(DISPATCH,g.sends[0][1])
        check('rejected-'+name+'-releases-to-idle',g.read(sym(g,'z7_sound_playback'))==0 and g.read(sym(g,'z7_sound_rejects'))==1)
        check('rejected-'+name+'-leaves-service-idle',bytes(g.u.mem_read(STATE_ADDR,3))==b'\0\0\0')
        check('rejected-'+name+'-status-failure',g.read(sym(g,'z7_sound_job_slot')+8)==1)
    g=load({WAV_PATH:good},mailbox=0)
    check('no-mailbox-refuses-enqueue',g.call(sym(g,'z7_sound_operation'),1,0,5,1)==0 and not g.sends and g.read(sym(g,'z7_sound_playback'))==0)
    g=load({WAV_PATH:good});g.u.mem_write(STATE_ADDR,b'\1')
    check('busy-native-sound-refuses-enqueue',g.call(sym(g,'z7_sound_operation'),1,0,5,1)==0 and not g.sends)
    g=load({WAV_PATH:good});g.fail_alloc_after=0
    check('post-allocation-failure-returns-idle',g.call(sym(g,'z7_sound_operation'),1,0,5,1)==0 and g.read(sym(g,'z7_sound_playback'))==0)
    g=load({WAV_PATH:good})
    check('invalid-clip-or-volume-refused',all(g.call(sym(g,'z7_sound_operation'),1,c,v,1)==0 for c,v in ((1,5),(0,0),(0,6))) and not g.sends)

    # Boot-preview variant: nothing at load; one preview on the 8th resident-worker tick.
    TICK=8
    def tick(f):f.call(h['symbols']['z7_module_worker_tick'])
    b=load({WAV_PATH:good},packet=bpacket,meta=bm)
    check('boot-preview-nothing-queued-at-load',b.loaded==8 and b.read(sym(b,'z7_sound_boot_queued'))==0 and not b.sends)
    for _ in range(TICK-1):tick(b)
    check('boot-preview-waits-for-worker-tick',val(b,'z7_sound_worker_ticks')==TICK-1 and not b.sends)
    tick(b)
    check('boot-preview-queued-on-tick',val(b,'z7_sound_boot_queued')==1 and len(b.sends)==1)
    b.call(DISPATCH,b.sends[0][1])
    check('boot-preview-plays',b.read(sym(b,'z7_sound_playback'))==2 and [c[0] for c in b.setter_calls]==['format','tones','data','dma-start'])
    b.call(b.read(CONTEXT+32),0x04180023,0)
    for _ in range(20):tick(b)
    check('boot-preview-never-repeats',len(b.sends)==1 and val(b,'z7_sound_worker_ticks')==TICK and val(b,'z7_sound_playback')==0)
    b=load({WAV_PATH:good},packet=bpacket,meta=bm);b.u.mem_write(STATE_ADDR,b'\1')
    for _ in range(TICK+4):tick(b)
    check('boot-preview-busy-service-refused-once',val(b,'z7_sound_boot_queued')==2 and not b.sends)
    b=load({},packet=bpacket,meta=bm)
    for _ in range(TICK+4):tick(b)
    check('boot-preview-silent-without-clip',b.read(sym(b,'z7_sound_boot_queued'))==0 and not b.sends and val(b,'z7_sound_worker_ticks')==0)
    clip=None
    if a.clip:
        # The exact card clip, end to end through the boot-preview module.
        clip=a.clip.read_bytes()
        b=load({WAV_PATH:clip},packet=bpacket,meta=bm)
        for _ in range(TICK):tick(b)
        check('card-clip-installs',b.loaded==8 and val(b,'z7_sound_init_result')==3)
        b.call(DISPATCH,b.sends[0][1])
        expect=reference(clip);pcm_addr=sym(b,'z7_sound_pcm')
        got=list(struct.unpack('<%dh'%len(expect),bytes(b.u.mem_read(pcm_addr,len(expect)*2))))
        check('card-clip-pcm-exact-at-volume-5',got==expect and b.setter_calls[0][1][1]==len(expect)*2)

    report=dict(passed=True,count=len(checks),checks=checks,module_sha256=m['module_sha256'],boot_module_sha256=bm['module_sha256'],
        clip_sha256=hashlib.sha256(clip).hexdigest() if clip else None,preview_worker_tick=TICK,
        host_main_sha256=h['main_payload_sha256'],camera_access=False,audio_hardware=False,photo_trigger=False,scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
