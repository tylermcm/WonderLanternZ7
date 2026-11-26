"""VR one-move test with the D2 restore (pixel-shift step 2b): offline audit (MIT).

Same simulated body-VR unit as audit_z7_vr_move.py, plus Nikon's D2 sender
0x101C63F8 (selection, flags, callback): the module must snapshot the last D2
parameters Nikon sent (command-4 buffer 0xA235BA44: bytes 0-1 and 8) before
it moves, re-send exactly those after recentring - only with the BodyVr
service in state 1 and idle - and poll telemetry until the hold ends.
Checks the no-D2 (never moves), D2-changed (no re-send), refused-restore,
busy-service and firmware-mismatch paths and the version-2 log layout.
No camera, no card, no sensor movement.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from audit_z7_vr_move import VrUnit,MOVE,CENTRE,F,LOG,SLOT,BUSY,DELAY,MAGIC
from audit_z7_lcd_shutter_sound import WAV
from audit_z7_lcd_grid_persistence import NEW,v3record
from audit_z7_settings_files import PATHS
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2

D2,D2_SEND,SERVICE=0xa235ba44,0x101c63f8,0xa18b6030
R=dict(RESTORE_SENT=1<<11,RESTORE_CALLED_BACK=1<<12,RESTORED=1<<13,NO_D2=1<<14,D2_CHANGED=1<<15)
SEL=(2,0x11);FLAGS=0x85


class D2Unit(VrUnit):
    def __init__(self,*a,d2=(2,0x11,0x85),refuse_d2=False,change_d2=False,busy_service_after_centre=False,**k):
        self.d2=d2;self.refuse_d2=refuse_d2;self.change_d2=change_d2;self.busy_after=busy_service_after_centre
        super().__init__(*a,**k);self.d2_calls=[];self.called_addr=None
        for base in (0xa2350000,):
            try:self.u.mem_map(base,0x10000)
            except Exception:pass
        b=bytearray(12);b[0],b[1],b[8]=d2;self.u.mem_write(D2,bytes(b))
        self.u.mem_write(SERVICE,bytes([1]))
    def hook(self,u,address,size,context):
        if address==DELAY and self.pending and self.pending['opcode']==0xf1f1 and self.pending['payload']==CENTRE:
            if self.change_d2:u.mem_write(D2,bytes([1]))
            if self.busy_after:u.mem_write(SERVICE,bytes([0xc]))
        if address==D2_SEND:
            sel=bytes(u.mem_read(self.r(UC_ARM_REG_R0),2));fl=self.r(UC_ARM_REG_R1);cb=self.r(UC_ARM_REG_R2)
            svc=bytes(u.mem_read(SERVICE,1))[0];busy=struct.unpack('<I',bytes(u.mem_read(BUSY,4)))[0];slot=struct.unpack('<I',bytes(u.mem_read(SLOT,4)))[0]
            self.d2_calls.append(dict(selection=sel,flags=fl,callback=cb,service=svc,busy=busy,slot=slot,state=self.state))
            if self.refuse_d2:self.ret(0);return
            self.state=1;self.target=[0,0,0]          # unit leaves hold: normal stabilisation
            u.mem_write(self.called_addr,struct.pack('<I',1))
            self.ret(1);return
        super().hook(u,address,size,context)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output','clip'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256'] and hashlib.sha256(packet).hexdigest()==m['module_sha256']
    assert m['configuration'].get('vr_restore')
    clip=a.clip.read_bytes();symbols=m['symbols'];checks=[]
    def check(name,ok):
        assert ok,name
        checks.append(name)
    journal={NEW[0]:v3record((3,15,1,0,5,0,127,7,0,127,4),0)}
    def load(patch=None,**kw):
        D2Unit.sound_files={WAV:clip}
        f=D2Unit(raw,h,packet,dict(journal),**kw);f.file_paths=PATHS+NEW
        f.u.mem_write(SLOT,bytes(4));f.u.mem_write(BUSY,bytes(4))
        if patch:f.u.mem_write(patch,bytes(4))
        assert f.call(h['symbols']['z7_module_load_once'],STATE)==8
        f.base=f.words()[12];f.setword(40,8);f.reply_addr=f.base+symbols['z7_vm_reply'];f.called_addr=f.base+symbols['z7_vm_d2_called'];return f
    def tick(f,n=1):
        for _ in range(n):f.call(h['symbols']['z7_module_worker_tick'])
    def moves(f):return [r for r in f.requests if r['opcode']==0xf1f1]
    def log(f):
        d=f.sound_files.get(LOG,b'')
        if len(d)<48:return None
        head=struct.unpack('<12I',d[:48]);ents=[]
        for i in range(head[2]):
            e=d[48+56*i:48+56*i+56];ents.append(dict(tick=struct.unpack('<I',e[:4])[0],phase=e[4],poll=e[5],status=struct.unpack('<H',e[6:8])[0],bytes=e[8:50]))
        return dict(magic=head[0],version=head[1],entries=head[2],flags=head[3],d2=head[8],restore=head[9],restore_state=head[10],entry=ents,size=len(d))

    # 1. Full success.
    f=load();tick(f)
    mv=moves(f)
    check('move-then-centre',[r['payload'] for r in mv]==[MOVE,CENTRE])
    check('one-restore-call',len(f.d2_calls)==1)
    c=f.d2_calls[0]
    check('restore-resends-nikon-d2-exactly',c['selection']==bytes(SEL) and c['flags']==FLAGS)
    check('restore-has-callback-in-module',f.base<=c['callback']<f.base+0x100000)
    check('restore-only-with-service-state-1-and-idle',c['service']==1 and c['busy']!=1 and c['slot']==0)
    check('restore-after-centre-while-held',c['state']==0x40 and f.requests.index(mv[1])<len(f.requests))
    tick(f,40);L=log(f)
    check('log-v2-layout',L and L['magic']==MAGIC and L['version']==2 and L['size']==48+128*56)
    check('d2-snapshot-logged',L['d2']==SEL[0]|SEL[1]<<8|FLAGS<<16)
    want=F['ARMED']|F['MOVE_SENT']|F['MOVE_ACK']|F['MOVE_FOLLOWED']|F['CENTRE_SENT']|F['CENTRE_ACK']|F['CENTRE_FOLLOWED']|F['NORMAL_AGAIN']|F['DONE']|R['RESTORE_SENT']|R['RESTORE_CALLED_BACK']|R['RESTORED']
    check('flags-full-success',L['flags']==want)
    check('restored-state-normal',L['restore_state']==1 and L['restore']&0xff==1)
    ph=[e['phase'] for e in L['entry']]
    check('restore-phases-logged-in-order',0x15 in ph and 5 in ph and ph.index(0x13)<ph.index(0x15)<ph.index(5)<ph.index(4))
    n=len(f.requests);tick(f,5);check('quiet-after-done',len(f.requests)==n and len(f.d2_calls)==1)
    # 2. No D2 sent yet (buffer zero): never moves.
    g=load(d2=(0,0,0));tick(g,3);L=log(g)
    check('no-d2-never-moves',not moves(g) and not g.d2_calls and L and L['flags']==R['NO_D2']|F['DONE'])
    g=load(d2=(7,0,0));tick(g,3);check('implausible-d2-never-moves',not moves(g) and not g.d2_calls)
    # 3. Nikon re-sent D2 meanwhile: no second send.
    g=load(change_d2=True);tick(g);tick(g,31);L=log(g)
    check('d2-changed-no-resend',[r['payload'] for r in moves(g)]==[MOVE,CENTRE] and not g.d2_calls and L['flags']&R['D2_CHANGED'] and not L['flags']&R['RESTORE_SENT'])
    # 4. D2 sender refuses: three tries, bounded, reported.
    g=load(refuse_d2=True);tick(g);tick(g,31);L=log(g)
    check('refused-restore-three-tries',len(g.d2_calls)==3 and not L['flags']&R['RESTORE_SENT'] and not L['flags']&R['RESTORED'])
    check('refused-restore-polls-bounded',sum(1 for e in L['entry'] if e['phase']==5)==14)
    # 5. Service not in state 1: the sender is never called.
    g=load(busy_service_after_centre=True);tick(g);tick(g,31);L=log(g)
    check('service-not-ready-no-restore-call',not g.d2_calls and not L['flags']&R['RESTORE_SENT'] and (L['restore']>>8)&0xff==0)
    # 6. D2 sender firmware mismatch: never moves.
    g=load(patch=D2_SEND);tick(g,3);check('d2-firmware-mismatch-never-moves',not moves(g) and not g.d2_calls)
    report=dict(passed=True,count=len(checks),checks=checks,module_sha256=m['module_sha256'],host_main_sha256=h['main_payload_sha256'],
                d2_buffer=hex(D2),d2_sender=hex(D2_SEND|1),camera_access=False,sensor_moved=False,scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
