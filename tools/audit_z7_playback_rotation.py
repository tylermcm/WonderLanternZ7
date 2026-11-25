"""Original-Z7 playback rotation chain: why upside-down photos play back unrotated (MIT).

Executes Nikon's own playback rotation code in an instruction fixture:
  * 0x103D4C10, the per-image turn lookup with its RAM cache at 0xA18E4DB8,
    maps the image record's 2-bit rotation field (byte +0x16, bits 4-5) as
    0->0, 1->1, 2->3, 3->0;
  * 0x10306586, the display rotation decision, indexes the ROM table
    0x11545DE4 {0,0,0,0, 0,1,0,3} by Rotate tall (0xA288E248+1) and turn, so
    turn 2 (half turn) gives 0 in both rows;
and checks the two places that fill the rotation field statically: the capture
path (pose 1->1, 2->2, else 0) and the file-read path (EXIF 8->1, 6->2, else 0).
Only the call boundaries around the lookup and the decision's playback-state
predicates are supplied. No firmware generation, no module, no camera.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
from unicorn.arm_const import UC_ARM_REG_R1
from audit_splash_image import NativePNG,STOCK_SHA,BASE
from prepare_flash_review import require_private_output

LOOKUP,DECIDE,FIELD=0x103d4c10,0x10306586,0x103397b0
TABLE,TABLE_USE=0x11545de4,0x103065cc
CACHE,SETTING=0xa18e4db8,0xa288e248
RECORD=0x50080000
EXPECTED_TURN={0:0,1:1,2:3,3:0}
EXPECTED_TABLE=bytes([0,0,0,0,0,1,0,3])
# (address, expected instruction) on the two field writers.
WRITERS=[(0x1026b4bc,'ldrb.w r0, [r5, #0x4fd]'),(0x1026b4c0,'cmp r0, #1'),(0x1026b4c4,'cmp r0, #2'),
         (0x1026b4ec,'movs r1, #2'),(0x1026b4f0,'movs r1, #1'),(0x1026b4c8,'movs r1, #0'),(0x1026b4cc,'bl #0x103397b8'),
         (0x1026b946,'ldrh r0, [r4, #0x38]'),(0x1026b948,'cmp r0, #6'),(0x1026b94c,'cmp r0, #8'),
         (0x1026b980,'movs r1, #2'),(0x1026b984,'movs r1, #1'),(0x1026b950,'movs r1, #0'),(0x1026b954,'bl #0x103397b8')]


class RotationFixture(NativePNG):
    def __init__(self,raw):
        super().__init__(raw)
        self.u.mem_map(0xa2880000,0x10000)
        self.stubs={}
        self.calls=[]
    def hook(self,u,address,size,context):
        stub=self.stubs.get(address)
        if stub is None:return super().hook(u,address,size,context)
        self.calls.append(address)
        self.ret(stub(u))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output);raw=a.stock_main.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==STOCK_SHA
    checks=[]
    def check(n,ok):
        assert ok,n
        checks.append(n)
    md=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
    def insn(address):
        i=next(md.disasm(raw[address-BASE:address-BASE+4],address))
        return f'{i.mnemonic} {i.op_str}'
    def word(address):return struct.unpack_from('<I',raw,address-BASE)[0]

    # The decision table and its single user.
    check('rotation-table-bytes',raw[TABLE-BASE:TABLE-BASE+8]==EXPECTED_TABLE)
    refs=[BASE+o for o in range(0,len(raw)-3,4) if raw[o:o+4]==struct.pack('<I',TABLE)]
    check('rotation-table-has-one-literal-reference',len(refs)==1)
    check('rotation-table-loaded-by-decision',insn(TABLE_USE)=='ldr r1, [pc, #0x3e4]' and ((TABLE_USE+4)&~3)+0x3e4==refs[0])
    check('lookup-cache-literal',word(((0x103d4c20+4)&~3)+0x8d4)==CACHE)
    check('rotate-tall-literal',word(((0x1035fffa+4)&~3)+0x110)==SETTING and insn(0x1035fffc)=='ldrb r0, [r0, #1]')
    for address,text in WRITERS:check(f'field-writer-{address:x}',insn(address)==text)

    # Lookup: miss path decodes the record field, hit path returns the cache.
    for field in range(4):
        f=RotationFixture(raw)
        f.u.mem_write(RECORD,bytes(0x40));f.u.mem_write(RECORD+0x16,bytes([field<<4|0x0f]))
        f.u.mem_write(RECORD+0x30,struct.pack('<I',0x1234+field))
        f.stubs={0x1031fa20:lambda u:1,
                 0x103d1bb2:lambda u:(u.mem_write(u.reg_read(UC_ARM_REG_R1),struct.pack('<I',RECORD)),1)[1]}
        turn=f.call(LOOKUP,RECORD+0x30)
        check(f'lookup-field-{field}-turn-{EXPECTED_TURN[field]}',turn==EXPECTED_TURN[field])
        cached=bytes(f.u.mem_read(CACHE,0x20))
        check(f'lookup-field-{field}-caches-turn-and-id',cached[0]==turn and struct.unpack_from('<I',cached,0x1c)[0]==0x1234+field)
        f.stubs={0x1031fa20:lambda u:0}
        f.u.mem_write(CACHE,bytes([7]))
        check(f'lookup-field-{field}-hit-returns-cache',f.call(LOOKUP,RECORD+0x30)==7)
    f=RotationFixture(raw)
    f.u.mem_write(RECORD+0x16,bytes([3<<4]))
    check('field-extractor-bits-4-5',f.call(FIELD,RECORD)==3)

    # Decision: table[rotate_tall*4+turn] when the playback predicates allow it.
    allow={0x10339ec6:lambda u:1,0x103d543a:lambda u:1,0x1036030e:lambda u:0,0x1036021e:lambda u:0}
    results={}
    for tall in (0,1):
        for turn in range(4):
            f=RotationFixture(raw);f.stubs=dict(allow)
            f.u.mem_write(SETTING,bytes([0,tall]))
            r=f.call(DECIDE,turn,0)
            results[f'{tall}:{turn}']=r
            check(f'decision-tall-{tall}-turn-{turn}',r==EXPECTED_TABLE[tall*4+turn])
            f.calls.clear()
    check('half-turn-never-rotates',results['0:2']==0 and results['1:2']==0)
    f=RotationFixture(raw);f.stubs=dict(allow);f.u.mem_write(SETTING,bytes([0,1]))
    check('decision-flag-suppresses-rotation',f.call(DECIDE,1,1)==0)

    report=dict(passed=True,count=len(checks),checks=checks,lookup=hex(LOOKUP),lookup_cache=hex(CACHE),
                decision=hex(DECIDE),decision_table=hex(TABLE),rotate_tall_setting=hex(SETTING)+'+1',
                field_to_turn={str(k):v for k,v in EXPECTED_TURN.items()},decision_results=results,
                camera_access=False,scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
