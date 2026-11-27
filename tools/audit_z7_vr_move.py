"""VR (IBIS) one-move test in the LCD module: offline audit (MIT).

Runs the compiled module on the original-Z7 host loader and worker (the LCD
sound fixture) against a simulated body-VR unit behind Nikon's send function
0x100F1F9E: reads (0xF040, window 0x0FE0) return telemetry laid out as
measured on the camera (target 0x00, error 0x06, state 0x22, measured 0x24),
and a position command (0xF1F1) puts the unit in hold (state 0x40) at
target (-4*x, -4*y, -4*y), as upstream's Z7II code expects. Completions are
delivered while the module sleeps in Nikon's delay 0x1017081E.

Checks that the module only moves once per boot, only after stabilisation is
active and settled on two reads, sends exactly upstream's 10-byte payload with
the tiny step x=4, y=0, always recentres once a move may have reached the
device (even if it was not followed or timed out), never moves on a parked,
unsettled, busy or mismatched camera, never sends anything after a refused
move, logs to A:\\Z7VRMOV.DAT with the documented layout, and goes quiet
afterwards. No camera, no card, no sensor movement.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1
from audit_z7_lcd_shutter_sound import SoundAware,WAV
from audit_z7_lcd_grid_persistence import NEW,v3record
from audit_z7_settings_files import PATHS
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output

SEND,DELAY,SLOT,BUSY,EVENT=0x100f1f9e,0x1017081e,0xa18b5d88,0xa18b6064,0x042f0021
LOG='A:'+chr(92)+'Z7VRMOV.DAT'
MOVE=bytes([0,4,0,0,0,16,16,0,0,2]);CENTRE=bytes([0,0,0,0,0,16,16,0,0,2])
PARK=(-770,-8591,-8598)
MAGIC=0x564d5637
F=dict(ARMED=1,MOVE_SENT=2,MOVE_ACK=4,MOVE_FOLLOWED=8,CENTRE_SENT=16,CENTRE_ACK=32,CENTRE_FOLLOWED=64,
       NORMAL_AGAIN=128,TIMED_OUT=256,GAVE_UP=512,DONE=1024)


class VrUnit(SoundAware):
    """Simulated VR unit. mode: 'active' (state 1, settled), 'parked' (state 0),
    'shaky' (state 1, error 200), 'blink' (state 1 on every other read)."""
    def __init__(self,*a,mode='active',follow=True,drop_move=False,refuse_move=False,normal_after=None,**k):
        super().__init__(*a,**k)
        self.mode=mode;self.follow=follow;self.drop_move=drop_move;self.refuse_move=refuse_move
        self.normal_after=normal_after;self.requests=[];self.pending=None;self.delays=[];self.reads=0
        self.state=1 if mode in('active','shaky','blink') else 0
        self.target=list(PARK if mode=='parked' else (120,-60,-55));self.reply_addr=None
    def telemetry(self):
        self.reads+=1
        if getattr(self,'normal_countdown',None) is not None:
            self.normal_countdown-=1
            if self.normal_countdown<=0:self.state=1;self.target=[0,0,0];self.normal_countdown=None
        state=self.state
        if self.mode=='blink' and state==1 and self.reads%2==0:state=0
        err=200 if self.mode=='shaky' and state==1 else 3
        measured=[t+err for t in self.target] if state else [-316,-2526,-2677]
        b=bytearray(42);struct.pack_into('<3h',b,0,*self.target)
        struct.pack_into('<3h',b,6,*[t-m for t,m in zip(self.target,measured)])
        b[0x22]=state;struct.pack_into('<3h',b,0x24,*measured);return bytes(b)
    def hook(self,u,address,size,context):
        if address==SEND:
            req=self.r(UC_ARM_REG_R0);cb=self.r(UC_ARM_REG_R1)
            w=struct.unpack('<HH9I',bytes(u.mem_read(req,40)))
            r=dict(opcode=w[0],address=w[2],length=w[3],payload_ptr=w[8],output=w[10],callback=cb,
                   payload=bytes(u.mem_read(w[8],10)) if w[0]==0xf1f1 and w[8] else None,
                   busy=struct.unpack('<I',bytes(u.mem_read(BUSY,4)))[0],slot=struct.unpack('<I',bytes(u.mem_read(SLOT,4)))[0])
            self.requests.append(r)
            if r['opcode']==0xf1f1 and self.refuse_move and r['payload']==MOVE:self.ret(0);return
            u.mem_write(SLOT,struct.pack('<I',cb));self.pending=r;self.ret(1);return
        if address==DELAY:
            self.delays.append(self.r(UC_ARM_REG_R0))
            p=self.pending
            if p:
                self.pending=None;status=0
                if p['opcode']==0xf040:u.mem_write(p['output'],self.telemetry())
                elif p['opcode']==0xf1f1:
                    if p['payload']==MOVE and self.drop_move:
                        u.mem_write(SLOT,bytes(4));self.ret(0);return   # reply lost; Nikon frees the slot
                    if self.follow or p['payload']==CENTRE:
                        x,y=struct.unpack('<2h',p['payload'][1:5]);self.state=0x40  # camera-measured layout (d6e6db28)
                        self.target=[max(-8180,min(8180,-4*v)) for v in (x,y,y)]
                        if p['payload']==CENTRE and self.normal_after is not None:self.normal_countdown=self.normal_after
                u.mem_write(self.reply_addr,struct.pack('<I',status));u.mem_write(SLOT,bytes(4))
            self.ret(0);return
        super().hook(u,address,size,context)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output','clip'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256'] and hashlib.sha256(packet).hexdigest()==m['module_sha256']
    assert m['configuration'].get('vr_move')
    clip=a.clip.read_bytes();symbols=m['symbols'];checks=[]
    def check(name,ok):
        assert ok,name
        checks.append(name)
    journal={NEW[0]:v3record((3,15,1,0,5,0,127,7,0,127,4),0)}
    def load(patch=None,busy=0,**kw):
        VrUnit.sound_files={WAV:clip}
        f=VrUnit(raw,h,packet,dict(journal),**kw);f.file_paths=PATHS+NEW
        f.u.mem_write(SLOT,bytes(4));f.u.mem_write(BUSY,struct.pack('<I',busy))
        if patch:f.u.mem_write(patch,bytes(4))
        assert f.call(h['symbols']['z7_module_load_once'],STATE)==8
        f.base=f.words()[12];f.setword(40,8);f.reply_addr=f.base+symbols['z7_vm_reply'];return f
    def tick(f,n=1):
        for _ in range(n):f.call(h['symbols']['z7_module_worker_tick'])
    def moves(f):return [r for r in f.requests if r['opcode']==0xf1f1]
    def log(f):
        d=f.sound_files.get(LOG,b'')
        if len(d)<32:return None
        head=struct.unpack('<8I',d[:32]);ents=[]
        for i in range(head[2]):
            e=d[32+56*i:32+56*i+56];ents.append(dict(tick=struct.unpack('<I',e[:4])[0],phase=e[4],poll=e[5],status=struct.unpack('<H',e[6:8])[0],bytes=e[8:50]))
        return dict(magic=head[0],version=head[1],entries=head[2],flags=head[3],sends=head[4],refused=head[5],timeouts=head[6],writes=head[7],entry=ents,size=len(d))

    # 1. Active, settled VR: one move, followed, recentred, watched.
    f=load(normal_after=5)
    check('nothing-sent-at-load',not f.requests)
    tick(f)
    mv=moves(f)
    check('arms-and-moves-on-first-qualifying-tick',len(mv)==2 and f.requests[0]['opcode']==0xf040 and f.requests[1]['opcode']==0xf040)
    check('move-payload-is-upstream-shape-tiny-step',mv[0]['payload']==MOVE)
    check('centre-payload',mv[1]['payload']==CENTRE)
    check('reads-target-telemetry-window',all(r['address']==0x0fe0 and r['length']==42 for r in f.requests if r['opcode']==0xf040))
    check('position-requests-carry-no-output-or-length',all(r['output']==0 and r['length']==0 and r['address']==0 for r in mv))
    check('every-send-with-service-idle',all(r['busy']!=1 and r['slot']==0 for r in f.requests))
    i0=f.requests.index(mv[0]);i1=f.requests.index(mv[1])
    check('telemetry-read-between-move-and-centre',i1-i0>=3)
    check('sleeps-are-short',max(f.delays)<=500 and sum(f.delays)<=12000)
    tick(f,40)
    L=log(f)
    check('log-written',L and L['magic']==MAGIC and L['version']==1 and L['size']==32+128*56)
    want=F['ARMED']|F['MOVE_SENT']|F['MOVE_ACK']|F['MOVE_FOLLOWED']|F['CENTRE_SENT']|F['CENTRE_ACK']|F['CENTRE_FOLLOWED']|F['NORMAL_AGAIN']|F['DONE']
    check('flags-full-success',L['flags']==want)
    ph=[e['phase'] for e in L['entry']]
    check('log-phases-in-order',ph[0]==1 and 0x12 in ph and 0x13 in ph and ph.index(0x12)<ph.index(0x13) and ph.count(4)==30)
    mvent=[e for e in L['entry'] if e['phase']==2]
    check('move-telemetry-shows-hold-at-minus-16',mvent and mvent[-1]['bytes'][0x22]==0x40 and struct.unpack('<3h',mvent[-1]['bytes'][:6])==(-16,0,0))
    n=len(f.requests);tick(f,10)
    check('quiet-after-done',len(f.requests)==n)
    check('exactly-one-move-and-one-centre-per-boot',len(moves(f))==2)

    # 2. Parked VR (as measured idle on the tripod): never moves, gives up, logs.
    g=load(mode='parked');tick(g,30)
    check('parked-never-moves',not moves(g))
    L=log(g);check('parked-periodic-log',L and L['flags']==0 and L['entries']>=2 and L['entry'][0]['bytes'][0x22]==0)
    # 3. Active but unsettled.
    g=load(mode='shaky');tick(g,8);check('unsettled-never-moves',not moves(g) and len(g.requests)==8)
    # 4. Active on one read only: confirmation read fails.
    g=load(mode='blink');tick(g,8);check('unconfirmed-never-moves',not moves(g) and len(g.requests)==8*2)
    # 5. Device ignores the move: still recentred.
    g=load(follow=False);tick(g)
    mv=moves(g);L=None;tick(g,31);L=log(g)
    check('ignored-move-still-recentred',[r['payload'] for r in mv]==[MOVE,CENTRE] and L['flags']&F['MOVE_ACK'] and
          not L['flags']&F['MOVE_FOLLOWED'] and L['flags']&F['CENTRE_FOLLOWED'])
    check('ignored-move-polls-bounded',sum(1 for e in L['entry'] if e['phase']==2)==20)
    # 6. Move reply lost (timeout): centre still sent once the slot frees.
    g=load(drop_move=True);tick(g);tick(g,31);L=log(g);mv=moves(g)
    check('timed-out-move-still-recentred',[r['payload'] for r in mv]==[MOVE,CENTRE] and L['flags']&F['TIMED_OUT'] and
          L['flags']&F['MOVE_SENT'] and not L['flags']&F['MOVE_ACK'] and L['flags']&F['CENTRE_FOLLOWED'])
    # 7. Refused move: nothing more is ever commanded.
    g=load(refuse_move=True);tick(g);tick(g,31);L=log(g);mv=moves(g)
    check('refused-move-no-centre-no-retry',[r['payload'] for r in mv]==[MOVE] and not L['flags']&F['MOVE_SENT'])
    # 8. Busy service: nothing sent.
    g=load(busy=1);tick(g,5);check('busy-service-sends-nothing',not g.requests)
    # 9. Firmware mismatch (the F1F1 switch): nothing sent.
    g=load(patch=0x100f2000);tick(g,5);check('firmware-mismatch-sends-nothing',not g.requests)
    report=dict(passed=True,count=len(checks),checks=checks,module_sha256=m['module_sha256'],host_main_sha256=h['main_payload_sha256'],
                move_payload=MOVE.hex(),centre_payload=CENTRE.hex(),camera_access=False,sensor_moved=False,scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
