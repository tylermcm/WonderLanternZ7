"""Read-only VR (IBIS) telemetry probe in the LCD module: offline audit (MIT).

Runs the compiled module on the original-Z7 host loader and worker (the LCD
sound fixture), with Nikon's BodyVr send function 0x100F1F9E supplied: it
records each request and stores the callback where Nikon does (0xA18B5D88).
Checks that the probe only ever sends position reads (opcode 0xF040, never the
0xF1F1 position command), cycles the four windows with the right addresses and
lengths, sends at most one request per tick and only with the service idle and
no callback outstanding, copies the returned bytes and statuses, times out
safely, stops after 48 rounds, writes A:\\Z7VRLOG.DAT with the documented
layout, and does nothing on a firmware mismatch.
No camera, no card, no sensor movement.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1
from audit_z7_lcd_shutter_sound import SoundAware,WAV
from audit_z7_lcd_grid_persistence import NEW,v3record
from audit_z7_settings_files import PATHS
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output

SEND,SLOT,BUSY,EVENT=0x100f1f9e,0xa18b5d88,0xa18b6064,0x042f0021
WINDOWS=[(0x0fe0,42),(0x1018,6),(0x1ff8,1),(0x1ff9,1)]
LOG='A:'+chr(92)+'Z7VRLOG.DAT'


class VrFixture(SoundAware):
    def __init__(self,*a,**k):
        super().__init__(*a,**k);self.requests=[];self.refuse=False
    def hook(self,u,address,size,context):
        if address==SEND:
            req=self.u.reg_read(UC_ARM_REG_R0);cb=self.u.reg_read(UC_ARM_REG_R1)
            words=struct.unpack('<HH9I',bytes(u.mem_read(req,40)))
            self.requests.append(dict(opcode=words[0],address=words[2],length=words[3],payload=words[8],output=words[10],callback=cb))
            if not self.refuse:u.mem_write(SLOT,struct.pack('<I',cb))
            self.ret(0 if self.refuse else 1);return
        super().hook(u,address,size,context)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--clip',type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256'] and hashlib.sha256(packet).hexdigest()==m['module_sha256']
    assert m['configuration'].get('vr_probe')
    clip=a.clip.read_bytes();symbols=m['symbols'];checks=[]
    def check(name,ok):
        assert ok,name
        checks.append(name)
    journal={NEW[0]:v3record((3,15,1,0,5,0,127,7,0,127,4),0)}
    def load(patch=None):
        VrFixture.sound_files={WAV:clip}
        f=VrFixture(raw,h,packet,dict(journal));f.file_paths=PATHS+NEW
        f.u.mem_write(SLOT,bytes(4));f.u.mem_write(BUSY,bytes(4))
        if patch:f.u.mem_write(patch,bytes(4))
        assert f.call(h['symbols']['z7_module_load_once'],STATE)==8
        f.base=f.words()[12];f.setword(40,8);return f
    def tick(f,n=1):
        for _ in range(n):f.call(h['symbols']['z7_module_worker_tick'])
    def complete(f,status=0,data=None):
        r=f.requests[-1]
        if data:f.u.mem_write(r['output'],bytes(data))
        res=0xa2970400;f.u.mem_write(res,bytes([status])+bytes(15))
        f.u.mem_write(SLOT,bytes(4))
        f.call(r['callback'],EVENT,res)

    f=load()
    check('nothing-sent-at-load',not f.requests)
    tick(f)
    check('first-tick-sends-one-read',len(f.requests)==1 and f.requests[0]['opcode']==0xf040)
    tick(f);check('waits-for-completion-no-second-send',len(f.requests)==1)
    complete(f,0,range(1,43));tick(f)
    for w,(addr,length) in enumerate(WINDOWS[1:],1):
        tick(f);complete(f,0,[0x10*w+i for i in range(length)]);tick(f)
    reqs=f.requests
    check('four-windows-in-order',[(r['address'],r['length']) for r in reqs]==WINDOWS)
    check('reads-only-never-position-command',all(r['opcode']==0xf040 and r['payload']==0 for r in reqs))
    check('output-buffer-in-module',all(r['output']==reqs[0]['output'] for r in reqs) and f.base<=reqs[0]['output']<f.base+0x100000)
    log_addr=f.base+symbols['z7_vp_log']
    head=struct.unpack('<8I',f.u.mem_read(log_addr,32))
    row=bytes(f.u.mem_read(log_addr+32,64))
    check('round-recorded',head[2]==1 and struct.unpack('<I',row[4:8])[0]==0 and row[8:50]==bytes(range(1,43)) and
          row[50:56]==bytes([0x10+i for i in range(6)]) and row[56]==0x20 and row[57]==0x30)
    # Busy service or an outstanding callback: no send.
    f.u.mem_write(BUSY,struct.pack('<I',1));n=len(f.requests);tick(f,3)
    check('busy-service-no-send',len(f.requests)==n)
    f.u.mem_write(BUSY,bytes(4));f.u.mem_write(SLOT,struct.pack('<I',0x10001));tick(f,3)
    check('outstanding-callback-no-send',len(f.requests)==n)
    f.u.mem_write(SLOT,bytes(4));tick(f)
    check('resumes-when-idle',len(f.requests)==n+1)
    # Error status recorded per window.
    complete(f,7);tick(f)
    st=struct.unpack('<I',bytes(f.u.mem_read(log_addr+32+64+4,4)))[0]
    check('error-status-recorded',st&0xff==7)
    # Timeout: no completion; after the timeout and once Nikon's slot clears.
    tick(f);n=len(f.requests);f.u.mem_write(SLOT,bytes(4));tick(f,6)
    check('timeout-moves-on',len(f.requests)>n)
    # Refused send counted, no wait.
    g=load();g.refuse=True;tick(g,2)
    check('refused-send-not-awaited',len(g.requests)==2 and struct.unpack('<8I',g.u.mem_read(g.base+symbols['z7_vp_log'],32))[4]>=2)
    # Bounded: 48 rounds then stop; log file written.
    g=load()
    for _ in range(48*4):
        tick(g);complete(g,0,[1]*42);tick(g)
    n=len(g.requests);tick(g,6)
    check('stops-after-48-rounds',n==48*4 and len(g.requests)==n)
    data=g.sound_files.get(LOG,b'')
    check('log-file-written',len(data)==32+48*64 and data[:4]==struct.pack('<I',0x47524637) and struct.unpack('<I',data[8:12])[0]==48)
    # Firmware mismatch: nothing sent.
    g=load(patch=0x100f31ce);tick(g,4)
    check('firmware-mismatch-sends-nothing',not g.requests)
    report=dict(passed=True,count=len(checks),checks=checks,module_sha256=m['module_sha256'],host_main_sha256=h['main_payload_sha256'],
                windows=[dict(address=hex(a_),length=l) for a_,l in WINDOWS],camera_access=False,sensor_moved=False,scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
