"""Original-Z7 pixel shift: BodyVr command-service bindings (MIT).

Static, read-only checks against the stock C 3.80 main firmware of the pieces a
pixel-shift port needs, following JKWTCN's MIT Z7II design (8aad350): the body
VR command service, its request layout, the position-read opcode 0xF040 and
the sensor-position opcode 0xF1F1 with a 10-byte payload. No emulation, no
module, no camera.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
from audit_splash_image import STOCK_SHA,BASE
from prepare_flash_review import require_private_output

SEND=0x100f1f9e
# (address, expected instruction) from the stock firmware.
EXPECT=[
    (SEND,'push.w {r3, r4, r5, r6, r7, r8, sb, sl, fp, lr}'),
    (0x100f1fa6,'ldr r4, [r0, #0x1c]'),          # request+0x1C: payload pointer
    (0x100f1fb6,'ldrh r1, [r6]'),                # request+0x00: opcode
    (0x100f1fbc,'ldrh r1, [r6, #0x22]'),
    (0x100f1fc2,'ldr r1, [r6, #0x24]'),          # request+0x24: output pointer
    (0x100f1fd2,'movs r2, #0x28'),               # 40-byte request copied
    (0x100f2000,'movw r3, #0xf1f1'),             # opcode switch: sensor position
    (0x100f200e,'sub.w r2, r2, #0xf000'),
    (0x100f2012,'subs r2, #0x40'),               # opcode switch: 0xF040 read
    (0x100f2048,'ldrb r1, [r4]'),                # 0xF1F1: payload byte 0 ...
    (0x100f2080,'ldrb r1, [r4, #9]'),            # ... through byte 9 (10 bytes)
    (0x100f209a,'movs r1, #0xa'),                # sent as a 10-byte command
    (0x100f2724,'movw r0, #0xf040'),             # native position read
    (0x100f271e,'movw r1, #0x1018'),             # at device address 0x1018
    (0x100f2738,'bl #0x100f1f9e'),
    (0x100f27a6,'bl #0x100f1f9e'),
]
NAMES={0x042f0000:'BodyVrCommandService',0x03060000:'BodyVrService',0x02050000:'BodyVrProtocolService'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output);raw=a.stock_main.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==STOCK_SHA
    md=Cs(CS_ARCH_ARM,CS_MODE_THUMB);checks=[]
    def check(name,ok):
        assert ok,name
        checks.append(name)
    def insn(address):
        i=next(md.disasm(raw[address-BASE:address-BASE+4],address));return f'{i.mnemonic} {i.op_str}'
    for address,text in EXPECT:check(f'{address:x}-{text.split()[0]}',insn(address)==text)
    for component,name in NAMES.items():
        hit=[o for o in range(0x11f98000-BASE,0x11f9a000-BASE,4) if struct.unpack_from('<I',raw,o)[0]==component]
        check(f'component-{component>>16:04x}-{name}',any(raw[o+4:o+20]==name.encode()[:16].ljust(16,bytes(1)) for o in hit))
    # Callers of the send function (BL decode).
    callers=[]
    for o in range(0,len(raw)-4,2):
        h1,h2=struct.unpack_from('<2H',raw,o)
        if (h1&0xf800)==0xf000 and (h2&0xd000)==0xd000:
            s=(h1>>10)&1;off=(s<<24)|((1-(((h2>>13)&1)^s))<<23)|((1-(((h2>>11)&1)^s))<<22)|((h1&0x3ff)<<12)|((h2&0x7ff)<<1)
            if s:off-=1<<25
            if BASE+o+4+off==SEND:callers.append(BASE+o)
    check('send-has-three-native-callers',[hex(c) for c in callers]==['0x100f2738','0x100f27a6','0x101c649a'])
    report=dict(passed=True,count=len(checks),checks=checks,send=hex(SEND|1),request_bytes=0x28,
                request_fields={'0x00':'opcode','0x1c':'payload','0x24':'output'},opcodes={'0xF040':'read (native: address 0x1018, 6 bytes)','0xF1F1':'sensor position, 10-byte payload'},
                camera_access=False,scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
