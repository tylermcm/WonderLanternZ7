"""Original-Z7 property lookup/read boundary for AF shortcut research (MIT).

Original group admission, descriptor lookup, scalar reads and paired selector
execute with supplied runtime property values. Numeric property presence does
not establish AF target meaning, key binding, setter behavior or camera behavior.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from audit_splash_image import NativePNG,MEM,STOCK_SHA
from prepare_flash_review import require_private_output

SCALARS={0x56c:0xa24e3408,0x579:0xa24e343c,0x1145:0xa24f2c24,
         0x114a:0xa24f2c38,0x114f:0xa24f2c4c,0x1153:0xa24f2c5c,0x1156:0xa24f2c68}
# Independently decoded native selector's nine (result, first, second) rows.
# Human target names remain unqualified; these are not shortcut target enums.
PAIRS=((4,3,3),(0,2,2),(1,1,2),(2,2,3),(3,1,3),(5,3,5),(6,3,7),(7,3,9),(8,0,0))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output);raw=a.stock_main.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==STOCK_SHA
    f=NativePNG(raw);f.u.mem_map(0xa24e0000,0x20000);checks=[]
    def check(n,ok):
        assert ok,n
        checks.append(n)
    for key,address in SCALARS.items():
        for value in (0,1,255,0x12345678):
            f.u.mem_write(address,struct.pack('<I',value))
            before=bytes(f.u.mem_read(0xa24e0000,0x20000))
            check(f'scalar-read-{key:x}-{value}',f.call(0x104065a4,key)==value)
            check(f'scalar-read-preserves-properties-{key:x}-{value}',bytes(f.u.mem_read(0xa24e0000,0x20000))==before)
    for key in (0x580,0x58a,0x58b,0x11a6,0xffff):
        f.u.mem_write(MEM,struct.pack('<I',0xabcdef01))
        check(f'group-limit-rejects-{key:x}',f.call(0x10070204,key,MEM)==0)
        check(f'rejected-lookup-preserves-output-{key:x}',bytes(f.u.mem_read(MEM,4))==struct.pack('<I',0xabcdef01))
        check(f'rejected-getter-defaults-zero-{key:x}',f.call(0x104065a4,key)==0)
    for first in (0,1,2,3,4,255):
        for second in (*range(11),255):
            f.u.mem_write(SCALARS[0x579],struct.pack('<I',first))
            f.u.mem_write(SCALARS[0x56c],struct.pack('<I',second))
            before=bytes(f.u.mem_read(0xa24e0000,0x20000))
            expected=next((row[0] for row in PAIRS if row[1:]==(first,second)),0)
            check(f'native-paired-selector-{first}-{second}',f.call(0x1033e738)==expected)
            check(f'selector-read-only-{first}-{second}',bytes(f.u.mem_read(0xa24e0000,0x20000))==before)
    result=dict(schema=1,passed=True,count=len(checks),checks=checks,
        stock_main_sha256=STOCK_SHA,scalar_addresses={hex(k):hex(v) for k,v in SCALARS.items()},
        group5_count=128,upstream_subtype_keys_rejected=[hex(k) for k in (0x58a,0x58b)],
        human_target_meaning_verified=False,native_setter_executed=False,
        input_binding_verified=False,camera_access=False,scope=__doc__)
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
