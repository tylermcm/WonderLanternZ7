"""Original-Z7 exposure conversion research for whole-group AE bracketing (MIT).

Executes original PTP exposure compensation and shutter conversion/validation
paths and their ROM tables. Property reads, admission and writes are supplied.
This establishes units and keys, not metering lock, exposure settling, Auto ISO,
capture results, restore/recovery, or an implemented pixel bracketing feature.
No camera or card access.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2
from audit_splash_image import NativePNG, STOCK_SHA, MEM
from prepare_flash_review import require_private_output


class ExposureFixture(NativePNG):
    def __init__(self, raw):
        super().__init__(raw)
        self.properties={0x204:72,0x20d:0,0x203:0,0x136f:3,0x508:0,0x207:120}
        self.effective_sv=120
        self.admission=[];self.writes=[];self.reject=False
        self.u.mem_map(0xa2800000,0x100000)

    def hook(self,u,address,size,context):
        r0=u.reg_read(UC_ARM_REG_R0);r1=u.reg_read(UC_ARM_REG_R1)
        if address==0x103095da:self.ret(0);return # Supplied photo context.
        if address==0x1033dee4:self.ret(0);return # Property-change publication boundary.
        if address==0x103fe8d8:
            assert r0==0x1309,hex(r0)
            u.mem_write(r1,struct.pack('<ii',24,self.effective_sv));self.ret(0);return
        if address==0x103fe85e:
            assert r0 in self.properties,hex(r0)
            self.ret(self.properties[r0]);return
        if address==0x1033de5c:
            self.admission.append((r0,r1))
            self.ret(0x201c if self.reject else 0x2001);return
        if address==0x103fe99e:
            self.writes.append((r0,r1));self.properties[r0]=r1
            self.ret(0);return
        if address==0x103fe9b0:
            count=u.reg_read(UC_ARM_REG_R2)
            keys=struct.unpack('<'+'I'*count,u.mem_read(r0,count*4))
            values=struct.unpack('<'+'I'*count,u.mem_read(r1,count*4))
            self.writes.extend(zip(keys,values));self.properties.update(zip(keys,values))
            self.ret(0);return
        super().hook(u,address,size,context)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raw=a.stock_main.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==STOCK_SHA
    out=require_private_output(a.output);checks=[]
    def check(name,ok):
        assert ok,name
        checks.append(name)
    f=ExposureFixture(raw)
    for milli,sixths in ((-2000,-12),(-1000,-6),(-333,-2),(0,0),(333,2),(1000,6),(2000,12)):
        f.u.mem_write(MEM,struct.pack('<h',milli));f.writes.clear()
        check(f'compensation-{milli}-milliEV-maps-to-{sixths}-sixths',
              f.call(0x1052ebbe,MEM)==0x2001 and f.writes==[(0x203,sixths&0xffffffff)])
    f.u.mem_write(MEM,struct.pack('<h',6000));f.writes.clear()
    check('compensation-out-of-range-refused-without-write',f.call(0x1052ebbe,MEM)==0x201c and not f.writes)
    f.reject=True;f.u.mem_write(MEM,struct.pack('<h',1000))
    check('compensation-admission-refusal-does-not-write',f.call(0x1052ebbe,MEM)==0x201c and not f.writes)
    f.reject=False
    for time,tv in ((1250,72),(10000,0),(20000,-24),(300000,-120)):
        check(f'shutter-{time}-units-conversion-succeeds',f.call(0x1032f1e0,time,MEM+0x100,MEM+0x104)==0x2001)
        mode,value=struct.unpack('<2I',f.u.mem_read(MEM+0x100,8))
        check(f'shutter-{time}-maps-to-Tv24-{tv}',mode==0 and value==tv&0xffffffff)
        f.writes.clear()
        check(f'shutter-{time}-writes-original-20d-and-204-keys',
              f.call(0x1032f264,mode,value)==0x2001 and f.writes==[(0x20d,0),(0x204,tv&0xffffffff)])
    f.writes.clear()
    check('unlisted-shutter-refuses-before-write',f.call(0x1032f1e0,1234567,MEM+0x100,MEM+0x104)==0x201c and not f.writes)
    f.reject=True
    check('shutter-admission-refusal-does-not-write',f.call(0x1032f264,0,72)==0x201c and not f.writes)
    f.reject=False
    for native,ptp in enumerate((2,4,3,1)):
        check(f'native-mode-{native}-maps-to-PTP-{ptp}',f.call(0x1053059c,native)==ptp)
    f.u.mem_write(MEM,struct.pack('<H',1));f.writes.clear()
    check('native-manual-mode-request-writes-key-one-value-three',f.call(0x10530460,MEM)==0x2001 and f.writes==[(1,3)])
    f.u.mem_write(MEM,struct.pack('<H',100));f.writes.clear()
    check('native-ISO100-setter-writes-Sv24-120-to-207',f.call(0x1052f162,MEM)==0x2001 and f.writes==[(0x207,120)])
    for value in (0,1):
        f.u.mem_write(MEM,bytes([value]));f.writes.clear()
        check(f'AutoISO-{value}-uses-original-key-508',f.call(0x1052fae8,MEM)==0x2001 and f.writes==[(0x508,value)])
    for sv,iso in ((120,100),(168,400),(192,800)):
        f.effective_sv=sv
        check(f'actual-ISO-getter-reads-Sv1309-{sv}-as-ISO{iso}',f.call(0x1052fb32)==iso)
    out.write_text(json.dumps(dict(passed=True,count=len(checks),checks=checks,stock_sha256=STOCK_SHA,
                                 camera_access=False,card_written=False,scope=__doc__),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
