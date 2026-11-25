"""Original-Z7 photo AF-area mode and focus mode properties: getter + menu evidence (MIT).

Offline: Nikon's scalar getter 0x104065A4 resolves property 0x568 to 0xA24E33F8 and
0x567 to 0xA24E33F4 (and no other key in 0x540..0x59F reads those words).
Evidence: read-only assisted-QEMU walks of Nikon's own Photo shooting menu
(tools/probe_z7_menu_walk.py), where each confirmed selection changed exactly one
word. The mode names come from the menu screenshots of the same runs.
No guest writes, no hooks, no camera.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from audit_splash_image import NativePNG,STOCK_SHA
from prepare_flash_review import require_private_output

GETTER=0x104065a4
AF_AREA=(0x568,0xa24e33f8)
FOCUS_MODE=(0x567,0xa24e33f4)
# Values measured in the menu walks, named from their screenshots.
AF_AREA_VALUES={0:'Pinpoint AF',1:'Single-point AF',2:'Dynamic-area AF',3:'Wide-area AF (S)',4:'Wide-area AF (L)',6:'Auto-area AF'}
FOCUS_VALUES={1:'AF-S',2:'AF-C'}
# (walk, expected per-OK word changes) from the recorded runs.
EXPECTED={'menu-walk-06':[[(0xa24e33f8,1,4)],[(0xa24e33f8,4,6)],[(0xa24e33f8,6,0)],[(0xa24e33f8,0,1)],[]],
          'menu-walk-07':[[(0xa24e33f8,1,3)],[(0xa24e33f4,1,2),(0xa24f7c04,1,2)],[(0xa24e33f8,3,6)]],
          'menu-walk-08':[[(0xa24e33f8,1,3)],[(0xa24e33f4,1,2),(0xa24f7c04,1,2)],[(0xa24e33f8,3,2)]]}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main',type=Path,required=True)
    p.add_argument('--walks',type=Path,required=True,help='Directory holding menu-walk-06/07/08')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output);raw=a.stock_main.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==STOCK_SHA
    f=NativePNG(raw);f.u.mem_map(0xa24e0000,0x20000);checks=[]
    def check(n,ok):
        assert ok,n
        checks.append(n)
    for key,address in (AF_AREA,FOCUS_MODE):
        for value in (0,1,2,3,4,6,0x12345678):
            f.u.mem_write(0xa24e0000,bytes(0x20000));f.u.mem_write(address,struct.pack('<I',value))
            check(f'getter-{key:x}-reads-{address:x}-{value:x}',f.call(GETTER,key)==value)
        f.u.mem_write(0xa24e0000,bytes(0x20000));f.u.mem_write(address,struct.pack('<I',0x5a5a1234))
        check(f'only-{key:x}-maps-to-{address:x}',[k for k in range(0x540,0x5a0) if f.call(GETTER,k)==0x5a5a1234]==[key])
    seen=set()
    for walk,expected in EXPECTED.items():
        r=json.loads((a.walks/walk/'result.json').read_text())
        got=[[(int(c['address'],16),int(c['before'],16),int(c['after'],16)) for c in x['changed']] for x in r['after_ok']]
        check(f'{walk}-each-confirm-changes-only-the-expected-words',got==expected)
        for frame in r['frames']:
            png=(a.walks/walk/(frame['name']+'.png')).read_bytes()
            assert hashlib.sha256(png).hexdigest()==frame['sha256'],(walk,frame['name'])
        check(f'{walk}-screenshots-match-recorded-hashes',True)
        for step in got:
            for address,before,after in step:
                if address==AF_AREA[1]:seen|={before,after}
    check('af-area-values-observed',seen==set(AF_AREA_VALUES))
    check('af-area-values-match-z7ii-area-table',set(AF_AREA_VALUES)=={0,1,2,3,4,6})
    report=dict(passed=True,count=len(checks),checks=checks,af_area_property=hex(AF_AREA[0]),af_area_storage=hex(AF_AREA[1]),
                af_area_values={str(k):v for k,v in AF_AREA_VALUES.items()},focus_mode_property=hex(FOCUS_MODE[0]),
                focus_mode_values={str(k):v for k,v in FOCUS_VALUES.items()},assisted_qemu=True,camera_access=False,
                availability_observed='Pinpoint greyed in AF-C; Dynamic-area greyed in AF-S (screenshots)',scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
