"""Original-Z7 AF-area shortcut runtime audit (MIT).

Executes the host loader, the compiled af_shortcut_runtime.h seam (switch polling,
edge capture, af_shortcut_policy.h, af_area_native.h) and Nikon's real property
getter. Switch-state words are supplied in RAM as Nikon's edge routine leaves
them; the setter is recorded as in audit_z7_af_area_apply.py. Button words and
masks come from the QEMU AutoOperation watch runs (re-checked here).
"""
import argparse,hashlib,json,struct
from pathlib import Path
from audit_z7_af_area_apply import AfFixture
from build_z7_module_host import STATE,ZIG
from build_z7_module import ROOT,build
from prepare_flash_review import require_private_output

SW0,SW1,SW2=0xa1f90aa4,0xa1f90ab8,0xa1f90acc
IDLE0=0x200
FN1,AF_ON,FN2,SS,MOVIE=0,1,2,3,4


class RuntimeFixture(AfFixture):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)
        try:self.u.mem_map(0xa1f90000,0x10000)
        except Exception:pass
        self.switches(0,0,0)
    def switches(self,w0,w1,w2):
        for addr,v in ((SW0,IDLE0|w0),(SW1,w1),(SW2,w2)):self.u.mem_write(addr,struct.pack('<I',v))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host',type=Path,required=True)
    p.add_argument('--watches',type=Path,required=True,help='Directory with switch-watch-01/02 and per-button runs')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256']
    source=ROOT/'z7-native-modules/plugins/af_shortcut_probe.c'
    packet,m=build(source,zig=ZIG.resolve());again,_=build(source,zig=ZIG.resolve());assert packet==again
    checks=[]
    def check(n,ok):
        assert ok,n
        checks.append(n)
    w=lambda name:json.loads((a.watches/name/'result.json').read_text())['buttons']
    check('qemu-fn1-sets-sw0-0x4000',w('switch-watch-02')['fn1']['after_call']==['0x4200','0x0','0x0'])
    check('qemu-af-on-sets-sw0-0x200000',w('switch-watch-af-on')['af-on']['after_call']==['0x200200','0x0','0x0'])
    check('qemu-ss-center-sets-sw2-0x8000',w('switch-watch-ss-center')['ss-center']['after_call']==['0x200','0x0','0x8000'])
    check('qemu-fn2-and-movie-unobserved',w('switch-watch-fn2')['fn2']['after_call']==['0x200','0x0','0x0'] and
          w('switch-watch-movie')['movie']['after_call']==['0x200','0x0','0x0'])
    def load(**kw):
        f=RuntimeFixture(raw,h,packet,**kw);f.loaded=f.call(h['symbols']['z7_module_load_once'],STATE)
        f.base=f.words()[12];return f
    def op(f,*x):return f.call(f.base+m['symbols']['z7_af_shortcut_operation'],*x)
    ALL=0x1f
    f=load(focus=1,area=1)
    check('loads',f.loaded==8)
    check('assign-fn1-wide-s-and-af-on-auto',op(f,1,FN1,4)==1 and op(f,1,AF_ON,7)==1 and op(f,1,SS,1)==1)
    check('idle-step-does-nothing',op(f,2,1,0,ALL)==0 and not f.sets)
    f.switches(0x4000,0,0)
    check('fn1-press-applies-wide-s',op(f,2,1,0,ALL)==1 and f.sets==[(0x568,3)] and f.area()==3)
    check('hold-does-not-repeat',op(f,2,1,0,ALL)==0 and len(f.sets)==1)
    f.switches(0,0,0);check('release-does-nothing',op(f,2,1,0,ALL)==0)
    f.switches(0x4000,0,0)
    check('second-press-already-selected-no-write',op(f,2,1,0,ALL)==2 and len(f.sets)==1)
    f.switches(0,0,0);op(f,2,1,0,ALL)
    f.switches(0x200000,0,0)
    check('af-on-press-applies-auto',op(f,2,1,0,ALL)==1 and f.sets[-1]==(0x568,6))
    f.switches(0,0,0);op(f,2,1,0,ALL)
    f.switches(0,0,0x8000)
    check('ss-center-pinpoint-in-af-s',op(f,2,1,0,ALL)==1 and f.sets[-1]==(0x568,0))
    f.switches(0,0,0);op(f,2,1,0,ALL)
    n=len(f.sets)
    f.switches(0,0x2000,0x4000)
    check('fn2-and-movie-bits-ignored',op(f,2,1,0,ALL)==0 and len(f.sets)==n and op(f,3)==0)
    f.switches(0,0,0);op(f,2,1,0,ALL)
    f.switches(0x4000,0,0)
    check('not-native-none-refused',op(f,2,1,0,ALL&~1)==0 and len(f.sets)==n)
    f.switches(0,0,0);op(f,2,1,0,ALL);f.switches(0x4000,0,0)
    check('outside-photo-context-dropped',op(f,2,0,0,ALL)==0)
    f.switches(0,0,0);check('dropped-press-not-applied-later',op(f,2,1,0,ALL)==0 and len(f.sets)==n)
    f.switches(0x4000,0,0);check('busy-defers',op(f,2,1,1,ALL)==0 and len(f.sets)==n)
    f.switches(0,0,0);check('applied-once-when-free',op(f,2,1,0,ALL)==1 and len(f.sets)==n+1 and f.sets[-1]==(0x568,3))
    g=load(focus=1,area=1);op(g,1,FN1,3)
    g.switches(0x4000,0,0);check('dynamic-target-unavailable-in-af-s',op(g,2,1,0,ALL)==0 and not g.sets)
    g=load(focus=2,area=1);op(g,1,FN1,3)
    g.switches(0x4000,0,0);check('dynamic-target-applies-in-af-c',op(g,2,1,0,ALL)==1 and g.sets==[(0x568,2)])
    g=load(focus=3,area=1);op(g,1,FN1,2)
    g.switches(0x4000,0,0);check('unmeasured-focus-mode-does-nothing',op(g,2,1,0,ALL)==0 and not g.sets)
    for t in (6,8,13):
        g=load(focus=1,area=1);assert op(g,1,FN1,t)==1;g.switches(0x4000,0,0)
        check(f'target-{t}-not-a-z7-mode',op(g,2,1,0,ALL)==0 and not g.sets)
    # Native f2 assignments read through Nikon's getter (storage from the f2 menu walks).
    ASSIGN={0x1048:0xa24f1898,0x1050:0xa24f18b8,0x1054:0xa24f18c8,0x1057:0xa24f18d4}
    walk=json.loads((a.watches/'f2-walk-04'/'result.json').read_text())
    check('qemu-f2-walk-assignment-words',[[(c['address'],c['before'],c['after']) for c in x['changed']] for x in walk['after_ok'] if x['changed']]==
          [[('0xa24f18b8','0x8','0x27')],[('0xa24f18c8','0x3','0x4')],[('0xa24f18d4','0x0','0x6')]])
    def assign(g,values):
        for key,v in values.items():g.u.mem_write(ASSIGN[key],struct.pack('<I',v))
    g=load(focus=1,area=1);assign(g,{0x1048:0x1f,0x1050:8,0x1054:3,0x1057:0})
    check('stock-defaults-only-movie-is-none',op(g,5)==1<<MOVIE)
    assign(g,{0x1048:0,0x1054:0});check('none-assignments-read',op(g,5)==(1<<FN1)|(1<<SS)|(1<<MOVIE))
    op(g,1,FN1,5);op(g,1,AF_ON,7)
    g.switches(0x200000,0,0);check('af-on-with-native-function-not-taken',op(g,6,1,0)==0 and not g.sets)
    g.switches(0,0,0);op(g,6,1,0);g.switches(0x4000,0,0)
    check('fn1-set-to-none-acts',op(g,6,1,0)==1 and g.sets==[(0x568,4)])
    report=dict(passed=True,count=len(checks),checks=checks,module_sha256=hashlib.sha256(packet).hexdigest(),host_main_sha256=h['main_payload_sha256'],
                verified_buttons=['Fn1','AF-ON','sub-selector center'],unverified_buttons=['Fn2','movie record'],camera_access=False,scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
