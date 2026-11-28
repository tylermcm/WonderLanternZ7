"""Execute Nikon's original Z7 unused-folder selection helper (MIT).

The original DCF bitmap search and helper execute. Card locking, the context
snapshot, property publication and durable storage are supplied boundaries.
No card access, physical creation, interrupted-write or recovery proof.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1
from audit_splash_image import NativePNG,STOCK_SHA
from prepare_flash_review import require_private_output

SUCCESS,NO_FOLDER=0x04390080,0x04390089

class FolderFixture(NativePNG):
    def __init__(self,raw,used,current=100,result=SUCCESS):
        super().__init__(raw);self.context=bytearray(124)
        struct.pack_into('<H',self.context,0,current);self.context[2]=1
        for folder in used:
            bit=folder-99;offset=8+(bit//32)*4
            word=struct.unpack_from('<I',self.context,offset)[0]
            struct.pack_into('<I',self.context,offset,word|1<<(bit%32))
        self.selected=[];self.resets=0;self.events=[];self.result=result
    def hook(self,u,address,size,context):
        if address in (0x10262fb2,0x10262ffa):
            self.events.append('lock' if address==0x10262fb2 else 'unlock');self.ret(0)
        elif address==0x10253cb6:self.ret(0)
        elif address==0x1031ccdc:
            u.mem_write(u.reg_read(UC_ARM_REG_R1),bytes(self.context));self.ret(SUCCESS)
        elif address==0x10253f02:
            self.selected.append(u.reg_read(UC_ARM_REG_R0));self.ret(self.result)
        elif address==0x10253f36:self.resets+=1;self.ret(SUCCESS)
        elif address==0x1031d07a:self.ret(SUCCESS)
        else:super().hook(u,address,size,context)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raw=a.stock_main.read_bytes();assert hashlib.sha256(raw).hexdigest()==STOCK_SHA
    out=require_private_output(a.output);checks=[]
    def check(name,ok):
        assert ok,name
        checks.append(name)
    for reset in (0,1):
        f=FolderFixture(raw,[100,101,102,103,104,110])
        check(f'new-folder-reset{reset}-admitted',f.call(0x1031fb12)==1)
        r=f.call(0x1031fa9c,reset)
        check(f'new-folder-reset{reset}-selects-unused-105',r==SUCCESS and f.selected==[105])
        check(f'new-folder-reset{reset}-resets-only-when-requested',f.resets==reset)
        check(f'new-folder-reset{reset}-balances-native-card-lock',f.events==['lock','unlock','lock','unlock'])
    f=FolderFixture(raw,range(100,1000),current=999)
    check('all-900-folders-used-refuses-admission',f.call(0x1031fb12)==0)
    check('all-folders-used-does-not-reset-or-select',f.call(0x1031fa9c,1)==NO_FOLDER and not f.selected and not f.resets)
    f=FolderFixture(raw,[100],result=NO_FOLDER)
    check('native-selection-error-does-not-reset-counter',f.call(0x1031fa9c,1)==NO_FOLDER and not f.resets)
    check('native-selection-error-unlocks-card',f.events==['lock','unlock'])
    out.write_text(json.dumps(dict(passed=True,checks=checks,count=len(checks),stock_sha256=STOCK_SHA,camera_access=False,card_written=False,scope=__doc__),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,checks=len(checks))))

if __name__=='__main__':main()
