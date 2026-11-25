"""Original-Z7 mux record/reply getter and registration contracts (MIT).

Original getter instructions execute with supplied mux pointer, file count and
record storage. No mux task launch, file operation, callback replacement or
physical camera operation. Zero/negative native indices are not module admission.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R9,UC_ARM_REG_SP,UC_ARM_REG_LR
from audit_splash_image import NativePNG,MEM,STACK,STOP,STOCK_SHA
from prepare_flash_review import require_private_output

CONTROL_SLOT=0xa1815030
FILE_GETTER=0x1027ef72
REPLIES={'open':(0x1027f002,0x160,8),'split':(0x1027ef9c,0x318,8),'close':(0x1027ef8e,0x370,8)}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output);raw=a.stock_main.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==STOCK_SHA
    f=NativePNG(raw);u=f.u;control=MEM+0x1000;checks=[]
    def check(name,good):
        assert good,name
        checks.append(name)
    check('file-getter-control-literal',struct.unpack_from('<I',raw,0x1027f014-0x10020000)[0]==CONTROL_SLOT)
    check('mux-task-registration-native-pointer',struct.unpack_from('<I',raw,0x1027ee80-0x10020000)[0]==0x1027e797)
    u.mem_write(CONTROL_SLOT,struct.pack('<I',control))
    for count in (1,5,10):
        u.mem_write(control,b'X'*0x1000);u.mem_write(control+8,struct.pack('<I',count))
        for file in range(1,12):
            snapshot=bytes(u.mem_read(control,0x1000))
            expected=control+0x3f0+0x88*file if file<=count else 0
            check(f'file-record-{count}-{file}',f.call(FILE_GETTER,file)==expected)
            check(f'file-getter-read-only-{count}-{file}',bytes(u.mem_read(control,0x1000))==snapshot)
            for name,(entry,offset,stride) in REPLIES.items():
                check(f'{name}-reply-{count}-{file}',f.call(entry,file)==control+offset+stride*file)
                check(f'{name}-reply-read-only-{count}-{file}',bytes(u.mem_read(control,0x1000))==snapshot)
    # Native helpers accept index0 and the file getter uses signed comparison.
    # The module must keep its own file>0/count bounds; do not inherit these.
    check('native-zero-index-not-module-admission',f.call(FILE_GETTER,0)==control+0x3f0)
    check('native-negative-index-not-module-admission',f.call(FILE_GETTER,0xffffffff)==control+0x3f0-0x88)
    # Native registration writes callback and priority after the event-name
    # helper. That helper alone is supplied; the original stores execute.
    class RegistrationFixture(NativePNG):
        def hook(self,u,address,size,context):
            if address==0x10170b5c:self.ret(1)
            else:super().hook(u,address,size,context)
    registration=RegistrationFixture(raw);cpu=registration.u;root=MEM+0x3000
    for reg,value in ((UC_ARM_REG_R0,root),(UC_ARM_REG_R1,0x1027e797),(UC_ARM_REG_R2,0xff003f),
                      (UC_ARM_REG_R3,MEM+0x4000),(UC_ARM_REG_SP,STACK),(UC_ARM_REG_LR,STOP|1)):
        cpu.reg_write(reg,value)
    cpu.emu_start(0x1017085f,0x10170878,timeout=10000000,count=10000000)
    check('native-registration-writes-callback-plus2c-and-priority-plus30',
          bytes(cpu.mem_read(root+0x2c,8))==struct.pack('<2I',0x1027e797,0xff003f))
    # The actual native open path passes file record +2C as the mux context
    # output pointer. Execute its argument construction, without calling I/O.
    record=control+0x3f0+0x88
    u.reg_write(UC_ARM_REG_R5,record);u.reg_write(UC_ARM_REG_R6,1);u.reg_write(UC_ARM_REG_R9,0)
    u.reg_write(UC_ARM_REG_SP,STACK);u.mem_write(STACK+0x50,struct.pack('<I',7))
    u.emu_start(0x1027e70b,0x1027e716,timeout=10000000,count=10000000)
    check('native-open-constructs-file-context-output-at-plus2c',
          bytes(u.mem_read(STACK+0x38,16))==struct.pack('<4I',record+0x2c,7,1,0))
    result=dict(schema=1,passed=True,count=len(checks),checks=checks,stock_main_sha256=STOCK_SHA,
        control_pointer_slot=hex(CONTROL_SLOT),file_record_base='0x3f0',file_record_stride='0x88',
        reply_layouts={n:dict(entry=hex(v[0]),offset=hex(v[1]),stride=v[2]) for n,v in REPLIES.items()},
        native_mux_task='0x1027E796',native_file_limit_verified=False,context_field_offset_verified=True,
        registration_callback_offset='0x2c',registration_root='0xA1F532F8',callback_slot='0xA1F53324',
        callback_installed=False,camera_access=False,physical_files=False,scope=__doc__)
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
