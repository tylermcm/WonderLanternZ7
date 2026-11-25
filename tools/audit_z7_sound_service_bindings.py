"""Static checks for the original-Z7 sound-service binding map (MIT).

Verifies the literals, call targets and dispatcher instructions cited in
SHUTTER_SOUND_SD_PORT.md against the original Z7 C 3.80 MAIN, and optionally a
private read-only live-RAM dump from a stock assisted-QEMU boot. No firmware is
executed, built or written; no camera or card is accessed.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
from prepare_flash_review import require_private_output

BASE=0x10020000
STOCK_MAIN_SHA256=None  # recorded from the input; see report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main',type=Path,required=True)
    p.add_argument('--live-ram',type=Path)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    img=a.stock_main.read_bytes()
    cs=Cs(CS_ARCH_ARM,CS_MODE_THUMB);cs.skipdata=True
    checks=[]
    def check(name,ok):
        assert ok,name
        checks.append(name)
    def word(addr):return struct.unpack_from('<I',img,addr-BASE)[0]
    def ins(start,end):return [(i.address,i.mnemonic,i.op_str) for i in cs.disasm(img[start-BASE:end-BASE],start)]
    def calls(start,end):return [int(o.split('#')[1],16) for _,m,o in ins(start,end) if m in ('bl','blx') and '#' in o]
    def literals(value):
        needle=struct.pack('<I',value);out=[];pos=0
        while True:
            pos=img.find(needle,pos)
            if pos<0 or BASE+pos>=0x10700000:return out
            if pos%4==0:out.append(BASE+pos)
            pos+=1

    for addr,value,name in ((0x100a2da4,0xa18852ac,'post-mailbox-handle'),(0x100a2da8,0x100a2d5f,'post-completion'),
                            (0x1006bf28,0xa188d190,'start-service-state'),(0x1006c040,0xa188d190,'data-service-state'),
                            (0x1006bf24,0xa21ab988,'start-record-copy-base'),(0x1006bf2c,0x04180022,'start-notify-event'),
                            (0x1006bf30,0x1006bc09,'start-dma-callback'),(0x1006c03c,0x04180023,'finished-event')):
        check(f'literal-{name}-{addr:08x}',word(addr)==value)
    post=ins(0x100a2d78,0x100a2da4)
    check('post-stores-event-at-0x10',any(m=='strd' and 'r0, r5, [r1, #0xc]' in o for _,m,o in post))
    check('post-stores-payload-at-0x14',any(m=='strd' and 'r4, r1, [r1, #0x14]' in o for _,m,o in post))
    disp=ins(0x1006bb58,0x1006bbc8)
    check('dispatcher-subtracts-0x4180000',any(m=='sub.w' and '#0x4180000' in o for _,m,o in disp))
    check('dispatcher-subtracts-0x1e',any(m=='subs' and 'r5, #0x1e' in o for _,m,o in disp))
    check('dispatcher-bounds-four-events',any(m=='cmp' and 'r5, #4' in o for _,m,o in disp))
    check('dispatcher-table-offset-0xe8',any(m=='adds' and 'r0, #0xe8' in o for _,m,o in disp))
    check('dispatcher-stores-result-job-2',any(m=='str' and 'r0, [r6, #8]' in o for _,m,o in disp))
    start=calls(0x1006bc46,0x1006be24)
    for target,name in ((0x100cf90a,'speaker'),(0x100cf98c,'second-check'),(0x1006b794,'format'),
                        (0x1006b62c,'tones'),(0x1006bfe6,'data-provider'),(0x1006b7dc,'dma-start')):
        check(f'start-calls-{name}',target in start)
    check('start-copies-0x24-record',any(m=='movs' and 'r2, #0x24' in o for _,m,o in ins(0x1006bcfc,0x1006bd04)))
    check('start-rejects-type-ge-18',any(m=='movs' and 'r2, #0x12' in o for _,m,o in ins(0x1006bcea,0x1006bcf0)))
    check('data-provider-calls-data-setter',0x1006b94a in calls(0x1006bfe6,0x1006c036))
    check('completion-calls-job-release',[m for _,m,_ in ins(0x100a2d64,0x100a2d6c)]==['ldr','ldr','cbz','blx'])
    for value in (0x041a000f,0x041b0090):
        check(f'z7ii-photo-event-{value:08x}-absent',not literals(value))
    report=dict(passed=True,checks=checks,count=len(checks),stock_main_sha256=hashlib.sha256(img).hexdigest(),
                camera_access=False,firmware_built=False,scope=__doc__)
    if a.live_ram:
        live=json.loads(a.live_ram.read_text())
        w=live['sound_state']['words']
        check('live-start-slot-holds-native-start',w['0xa188d278']=='0x1006bc47')
        check('live-playing-state-stop-handler',w[hex(0xa188d278+16+12)]=='0x1006bee3')
        check('live-still-file-consumer',live['still_slot_a18d2750']['words']['0xa18d2750']=='0x104db211')
        check('live-capture-consumer',live['controller_a18d1b98']['words']['0xa18d1bdc']=='0x1014708d')
        report.update(count=len(checks),live_ram_sha256=hashlib.sha256(a.live_ram.read_bytes()).hexdigest(),assisted_qemu=True)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
