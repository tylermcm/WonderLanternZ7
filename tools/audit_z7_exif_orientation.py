"""Upside-down photo EXIF orientation: install and writer audit (MIT).

Executes the original-Z7 host loader, the compiled module, Nikon's IFD
descriptor consumer 0x1028BB2C (descriptor table 0x11533C14 -> RAM descriptor
0xA18D3410, whose live value comes from a read-only QEMU search) and Nikon's
Orientation writer 0x102868D9 for every pose the wrapper passes through. The
capture record and IFD entry buffers are supplied. No camera, no card, no JPEG.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from audit_z7_module_host import HostFixture
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output

SLOT=0xa18d3410
DESCRIPTOR=(0x1028bb5f,0x1028bb8b,0x1028bbaf,0x1028bbb9)
STOCK_TABLE=0x11532d94
WRITER=0x102868d9
BUF=0xa18d8000


class ExifFixture(HostFixture):
    def __init__(self,raw,host,packet,descriptor=DESCRIPTOR,fingerprint_patch=None):
        super().__init__(raw,host,packet)
        try:self.u.mem_map(0xa18d0000,0x10000)
        except Exception:pass
        self.u.mem_write(SLOT,struct.pack('<4I',*descriptor))
        if fingerprint_patch:self.u.mem_write(fingerprint_patch,bytes(4))
    def read(self,a,n=4):return bytes(self.u.mem_read(a,n))
    def word(self,a):return struct.unpack('<I',self.read(a))[0]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','slot_evidence','output'):p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256']
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(packet).hexdigest()==m['module_sha256']
    live=json.loads(a.slot_evidence.read_text())
    checks=[]
    def check(name,ok):
        assert ok,name
        checks.append(name)
    check('live-slot-from-qemu-search',live['hits']==[hex(SLOT)] and live['context'][hex(SLOT)][4:8]==[hex(x) for x in DESCRIPTOR])
    def load(**kw):
        f=ExifFixture(raw,h,packet,**kw);f.loaded=f.call(h['symbols']['z7_module_load_once'],STATE)
        f.base=f.words()[12];f.s=m['symbols'];return f
    f=load()
    sym=lambda n:f.base+f.s[n]
    stock=[struct.unpack_from('<4I',f.read(STOCK_TABLE,16*38),16*i) for i in range(38)]
    check('stock-entry-9-is-orientation',stock[9]==(0x00030112,1,0,WRITER))
    check('module-loads-and-installs',f.loaded==8 and f.word(sym('z7_exif_installed'))==1)
    check('only-getter-word-replaced',f.word(SLOT)==(sym('z7_exif_get')|1) and struct.unpack('<3I',f.read(SLOT+4,12))==DESCRIPTOR[1:])
    table=f.call(f.word(SLOT))
    copy=[struct.unpack_from('<4I',f.read(table,16*38),16*i) for i in range(38)]
    check('table-identical-except-orientation-writer',all(copy[i]==stock[i] for i in range(38) if i!=9) and
          copy[9][:3]==stock[9][:3] and copy[9][3]==(sym('z7_exif_orientation_write')|1))
    # Nikon's consumer 0x1028BB2C loads descriptor[index] from ROM table 0x11533C14
    # and calls its first word; IFD0 indices 0 and 1 both name this RAM descriptor.
    check('rom-descriptor-table-names-the-slot',[f.word(0x11533c14+4*i) for i in (0,1)]==[SLOT,SLOT] and
          f.word(((0x1028bb30+4)&~3)+0xa8)==0x11533c14 and f.read(0x1028bb40,4)==bytes.fromhex('28688047'))
    meta=BUF+0x200;entry=BUF+0x300
    def write(pose):
        capture=0xa18d9000-0x2000  # capture record base; pose byte at +0x24FD
        f.u.mem_write(capture+0x24fd,bytes([pose]))
        f.u.mem_write(meta,struct.pack('<3I',0,capture,0));f.u.mem_write(entry,bytes(12))
        f.call(copy[9][3],entry,meta,0)
        return struct.unpack('<6H',f.read(entry,12))
    results={pose:write(pose)[4] for pose in (0,1,2,3,4,7)}
    check('pose-3-writes-orientation-3',results[3]==3)
    check('other-poses-match-nikon-writer',results[0]==1 and results[1]==8 and results[2]==6 and results[4]==1 and results[7]==1)
    check('only-value-field-touched',write(3)[:4]==(0,0,0,0) and write(3)[5]==0)
    check('counters',f.word(sym('z7_exif_inverted'))==3 and f.word(sym('z7_exif_last_pose'))==3)
    g=load(descriptor=(0x10123457,)+DESCRIPTOR[1:])
    check('foreign-descriptor-untouched',g.loaded==8 and g.word(SLOT)==0x10123457 and g.word(g.base+m['symbols']['z7_exif_installed'])==0)
    g=ExifFixture(raw,h,packet,fingerprint_patch=WRITER-1)
    check('firmware-mismatch-fails-init',g.call(h['symbols']['z7_module_load_once'],STATE)==7 and g.word(SLOT)==DESCRIPTOR[0])
    report=dict(passed=True,count=len(checks),checks=checks,module_sha256=m['module_sha256'],host_main_sha256=h['main_payload_sha256'],
                slot=hex(SLOT),camera_access=False,pose_3_on_camera_established=False,scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
