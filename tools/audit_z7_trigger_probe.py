"""Shutter-sound trigger probe: install, pass-through and log-file audit (MIT).

Executes the original-Z7 host loader and worker tick, the compiled probe module,
the original property getter wrapper and the native file create/write/close
wrappers. Supplied boundaries: the three native callbacks (recorded and given a
marker result, not executed), the filesystem request dispatcher, the property
value and the allocator. No camera, no card, no capture pipeline.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3
from audit_z7_module_host import HostFixture
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output
from read_z7_trigger_log import parse,SIZE,candidates

LOG='A:\\Z7TRIG.DAT'
SLOTS=(0xa18d1bd8,0xa18d1bdc,0xa18d2750)
NATIVE=(0x101426a9,0x1014708d,0x104db211)
GETTER=0x1016fef2
PACKET=0xa18d8000
MODULE_PATH='A:'+chr(92)+'Z7APP.BIN'
WAV_FILE='A:'+chr(92)+'SHUTTER1.WAV'


class ProbeFixture(HostFixture):
    def __init__(self,raw,host,packet,slot_values=NATIVE,silent=0,faults=None,fingerprint_patch=None):
        super().__init__(raw,host,packet)
        self.probe_setup(slot_values,silent,faults,fingerprint_patch)
    def probe_setup(self,slot_values=NATIVE,silent=0,faults=None,fingerprint_patch=None):
        try:self.u.mem_map(0xa18d0000,0x10000)
        except Exception:pass
        for a,v in zip(SLOTS,slot_values):self.u.mem_write(a,struct.pack('<I',v))
        if fingerprint_patch:self.u.mem_write(fingerprint_patch,bytes(4))
        self.native_calls=[];self.silent=silent;self.log_faults=dict(faults or {})
        self.log_files={};self.log_handles={};self.next_log_fd=0x70;self.log_events=[]
    def r(self,reg):return self.u.reg_read(reg)
    def read(self,a):return struct.unpack('<I',bytes(self.u.mem_read(a,4)))[0]
    def hook(self,u,address,size,context):
        for i,n in enumerate(NATIVE):
            if address==n-1:
                self.native_calls.append((i,)+tuple(self.r(x) for x in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)))
                self.ret(0x600+i);return
        if address==0x10070234:  # descriptor lookup below the original getter wrappers
            assert self.r(UC_ARM_REG_R0)==0x576,'probe must only read Silent photography'
            u.mem_write(self.r(UC_ARM_REG_R1),struct.pack('<I',self.silent));self.ret(0);return
        if address==0x1027beae:
            p=self.r(UC_ARM_REG_R0);words=struct.unpack('<42I',u.mem_read(p,168));op=bytes(u.mem_read(p+0x9c,1))[0]
            if op==13:
                path=self.cstring(words[4])
                if path!=LOG:raise AssertionError('probe created an unexpected file '+path)
                assert words[6]==0
                self.log_events.append(('create',path))
                if self.log_faults.get('create'):self.ret(self.log_faults['create']);return
                fd=self.next_log_fd;self.next_log_fd+=1;self.log_handles[fd]=path;self.log_files[path]=b'';self.ret(fd);return
            if op==9 and words[7] in self.log_handles:
                fd,pointer,capacity,actual=words[7],words[10],words[11],words[12]
                assert pointer%64==0 and capacity==SIZE,'log write signature'
                self.log_files[LOG]+=bytes(u.mem_read(pointer,capacity))
                u.mem_write(actual,struct.pack('<I',self.log_faults.get('actual',capacity)))
                self.log_events.append(('write',capacity));self.ret(self.log_faults.get('write',0));return
            if op==6 and words[7] in self.log_handles:
                self.log_events.append(('close',words[7]))
                if self.log_faults.get('close'):self.ret(self.log_faults['close']);return
                del self.log_handles[words[7]];self.ret(0);return
            if op==9:raise AssertionError('write outside the trigger log')
            if op in (5,16) and self.cstring(words[4]) not in (MODULE_PATH,WAV_FILE):raise AssertionError('unexpected file access')
        super().hook(u,address,size,context)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256']
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(packet).hexdigest()==m['module_sha256'] and not m['plays_sound']
    checks=[]
    def check(name,ok):
        assert ok,name
        checks.append(name)
    def load(**kw):
        f=ProbeFixture(raw,h,packet,**kw)
        f.loaded=f.call(h['symbols']['z7_module_load_once'],STATE);f.setword(40,f.loaded)
        f.base=f.words()[12];f.s=m['symbols'];return f
    def sym(f,n):return f.base+f.s[n]
    def tick(f,n=1):
        for _ in range(n):f.call(h['symbols']['z7_module_worker_tick'])
    def fire(f,slot,event,packet=0,a2=0x22,a3=0x33):
        return f.call(f.read(SLOTS[slot]),event,packet,a2,a3)

    f=load()
    check('module-loads',f.loaded==8)
    check('all-three-slots-wrapped',all(f.read(s)!=n and f.read(s)&1 for s,n in zip(SLOTS,NATIVE)) and f.read(sym(f,'z7_trig_init_result'))==7)
    check('nothing-written-at-load',not f.log_events)
    f.u.mem_write(PACKET,struct.pack('<2I',0x11223344,0x55667788))
    results=[fire(f,1,0x04190001,PACKET),fire(f,1,0x04190001,PACKET),fire(f,2,0x041e0002,PACKET),fire(f,0,0x04190008,0)]
    check('wrappers-return-native-result',results==[0x601,0x601,0x602,0x600])
    check('wrappers-pass-event-and-all-four-arguments',f.native_calls==[(1,0x04190001,PACKET,0x22,0x33),(1,0x04190001,PACKET,0x22,0x33),
                                                                     (2,0x041e0002,PACKET,0x22,0x33),(0,0x04190008,0,0x22,0x33)])
    check('no-file-write-outside-worker',not f.log_events)
    tick(f,2)
    check('no-write-before-third-tick',not f.log_events)
    tick(f)
    check('one-log-write-create-write-close',[e[0] for e in f.log_events]==['create','write','close'])
    log=parse(f.log_files[LOG])
    check('log-header',log['installed_mask']==7 and log['sequence']==1 and log['writes']==1 and log['ticks']==3)
    check('log-counts-per-slot',log['counts']['capture-consumer-0xA18D1BDC']=={'0x04190001':2} and
          log['counts']['still-file-0xA18D2750']=={'0x041E0002':1} and log['counts']['capture-controller-0xA18D1BD8']=={'0x04190008':1})
    events=[(e['slot'],e['event'],e['word0'],e['word1']) for e in log['ring']]
    check('log-ring-order-and-packet-words',events[:4]==[('capture-consumer-0xA18D1BDC','0x04190001','0x11223344','0x55667788')]*2+
          [('still-file-0xA18D2750','0x041E0002','0x11223344','0x55667788'),('capture-controller-0xA18D1BD8','0x04190008','0x00000000','0x00000000')])
    check('silent-marker-on-first-tick',events[4]==('silent-photography-0x576','0x05760000','0x00000000','0x00000000') and log['ring'][4]['tick']==1)
    tick(f,5)
    check('no-rewrite-when-unchanged',len(f.log_events)==3)
    f.silent=1;tick(f,3)
    log=parse(f.log_files[LOG])
    check('silent-change-logged-and-rewritten',len(f.log_events)==6 and log['silent_photography']==1 and log['ring'][-1]['event']=='0x05760001' and log['sequence']==2)
    for k in range(30):fire(f,1,0x04190100+k)
    tick(f,3);log=parse(f.log_files[LOG])
    check('event-table-overflow-counted-not-lost',len(log['counts']['capture-consumer-0xA18D1BDC'])==24 and log['dropped_event_kinds']==7)
    for k in range(200):fire(f,2,0x041e0002)
    tick(f,3);log=parse(f.log_files[LOG])
    still=[e for e in log['ring'] if e['event']=='0x041E0002']
    check('v2-repeated-event-logged-24-times-then-counted',len(still)==24 and log['counts']['still-file-0xA18D2750']['0x041E0002']==201 and
          log['extra']['capped']==201-24+7)  # + the 7 overflow kinds, also not logged
    check('packet-outside-ram-not-read',all(e['word0']=='0x00000000' for e in still[1:]))
    # Bounded writes.
    g=load()
    for k in range(450):
        fire(g,1,0x04190001);tick(g,3)
    check('write-count-capped-at-400',sum(1 for e in g.log_events if e[0]=='create')==400)
    # Slot mismatch and firmware mismatch.
    g=load(slot_values=(0x101426a9,0x12345679,0x104db211))
    check('foreign-slot-left-untouched',g.read(SLOTS[1])==0x12345679 and g.read(sym(g,'z7_trig_init_result'))==5)
    g=ProbeFixture(raw,h,packet,fingerprint_patch=0x1014708c)
    r=g.call(h['symbols']['z7_module_load_once'],STATE)
    check('firmware-mismatch-fails-init-no-slot-touched',r==7 and all(g.read(s)==n for s,n in zip(SLOTS,NATIVE)))
    # File failures.
    g=load(faults={'create':0x80000001});fire(g,1,0x04190001);tick(g,3)
    check('create-failure-retries-later',[e[0] for e in g.log_events]==['create'] and g.read(sym(g,'z7_trig_dirty'))==1)
    tick(g,3);check('create-retry',[e[0] for e in g.log_events]==['create','create'])
    g=load(faults={'close':0x80000002});fire(g,1,0x04190001);tick(g,3);fire(g,1,0x04190001);tick(g,9)
    check('close-failure-parks-logging',[e[0] for e in g.log_events]==['create','write','close'] and g.read(sym(g,'z7_trig_parked'))==1)
    g=load(faults={'actual':16});fire(g,1,0x04190001);tick(g,3)
    check('short-write-reported',g.read(sym(g,'z7_trig_write_result'))==0x5407e000)

    # Candidate ranking on a synthetic session: 3 photos saved as JPEG+NEF pairs,
    # plus consumer noise that fires regardless of photos.
    g=load()
    for n in range(3):
        for kind in (3,7):
            g.u.mem_write(PACKET,struct.pack('<2I',(1<<29)|(100<<19)|((40+n)<<5)|kind,1));fire(g,2,0x041e0002,PACKET)
        for _ in range(4):fire(g,1,0x04190001)
    tick(g,3);ranked=candidates(parse(g.log_files[LOG]),3)
    check('candidate-ranking-picks-per-photo-event',ranked[0]['matches_photos'] and ranked[0]['event']=='0x041E0002' and
          ranked[0]['count']==6 and not any(r['matches_photos'] for r in ranked[1:]))
    report=dict(passed=True,count=len(checks),checks=checks,module_sha256=m['module_sha256'],host_main_sha256=h['main_payload_sha256'],
                log_bytes=SIZE,camera_access=False,plays_sound=False,scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
