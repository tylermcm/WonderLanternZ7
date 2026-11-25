"""Original-Z7 AF-area apply component audit (MIT).

Executes the original-Z7 host loader, the compiled af_area_native.h seam and
Nikon's real property getter for 0x567/0x568 (storage 0xA24E33F4/0xA24E33F8).
The native setter 0x101D61EE is supplied (recorded, stores the value) because it
locks and notifies other tasks; it was exercised for real in assisted QEMU
(tools/probe_z7_menu_walk.py --set), where it accepted every value, including
greyed-out and nonexistent modes, which is why this component validates first.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1
from audit_z7_module_host import HostFixture
from build_z7_module_host import STATE
from build_z7_module import ROOT,build
from build_z7_module_host import ZIG
from prepare_flash_review import require_private_output

AREA,FOCUS=0xa24e33f8,0xa24e33f4
SETTER=0x101d61ee


class AfFixture(HostFixture):
    def __init__(self,raw,host,packet,focus=1,area=1,setter_result=1,setter_stores=True):
        super().__init__(raw,host,packet)
        try:self.u.mem_map(0xa24e0000,0x20000)
        except Exception:pass
        self.u.mem_write(FOCUS,struct.pack('<I',focus));self.u.mem_write(AREA,struct.pack('<I',area))
        self.sets=[];self.setter_result=setter_result;self.setter_stores=setter_stores
    def hook(self,u,address,size,context):
        if address==SETTER:
            key,value=u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R1);self.sets.append((key,value))
            if self.setter_stores and key==0x568:u.mem_write(AREA,struct.pack('<I',value))
            self.ret(self.setter_result);return
        super().hook(u,address,size,context)
    def area(self):return struct.unpack('<I',bytes(self.u.mem_read(AREA,4)))[0]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host',type=Path,required=True)
    p.add_argument('--setter-walk',type=Path,required=True,help='result.json of the QEMU setter walk')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256']
    source=ROOT/'z7-native-modules/plugins/af_area_probe.c'
    packet,m=build(source,zig=ZIG.resolve());again,_=build(source,zig=ZIG.resolve());assert packet==again
    checks=[]
    def check(n,ok):
        assert ok,n
        checks.append(n)
    walk=json.loads(a.setter_walk.read_text())
    check('qemu-native-setter-accepts-anything',[(s['value'],s['return_r0'],s['after']['0x568']) for s in walk['sets']]==
          [(3,'0x00000001','0x3'),(2,'0x00000001','0x2'),(5,'0x00000001','0x5'),(4,'0x00000001','0x4')] and walk['sets'][1]['after']['0x567']=='0x1')
    def load(**kw):
        f=AfFixture(raw,h,packet,**kw);f.loaded=f.call(h['symbols']['z7_module_load_once'],STATE)
        f.base=f.words()[12];return f
    def op(f,o,x=0):return f.call(f.base+m['symbols']['z7_af_operation'],o,x)
    f=load()
    check('module-loads-fingerprints-match',f.loaded==8 and op(f,3)==1)
    check('af-s-availability',op(f,1)==0b1011011)
    g=load(focus=2);check('af-c-availability',op(g,1)==0b1011110)
    for focus in (0,3,4,0x10):
        g=load(focus=focus);check(f'unknown-focus-{focus}-allows-nothing',op(g,1)==0 and op(g,2,1)==0 and not g.sets)
    for area,expect in ((0,1),(1,2),(2,0),(3,1),(4,1),(5,0),(6,1),(7,0),(32,0),(0xffffffff,0)):
        g=load(focus=1,area=1)
        r=op(g,2,area)
        check(f'af-s-apply-{area:x}',r==expect and (g.sets==[(0x568,area)])==(expect==1) and (g.area()==area)==(expect in (1,2)))
    g=load(focus=2,area=3);check('af-c-dynamic-allowed',op(g,2,2)==1 and g.area()==2)
    g=load(focus=2,area=3);check('af-c-pinpoint-refused',op(g,2,0)==0 and not g.sets and g.area()==3)
    g=load(setter_result=0);check('setter-failure-reported',op(g,2,3)==3)
    g=load(setter_stores=False);check('readback-mismatch-reported',op(g,2,3)==3)
    report=dict(passed=True,count=len(checks),checks=checks,module_sha256=hashlib.sha256(packet).hexdigest(),host_main_sha256=h['main_payload_sha256'],
                camera_access=False,scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
