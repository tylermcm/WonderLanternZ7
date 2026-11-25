"""Compiled AF shortcut capture/GUI-selection policy, no native AF writes (MIT).

Inputs are logical press edges, context, busy state, native assignment admission
and target availability. No physical button decoding or AF behavior is proved.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from audit_z7_module_host import HostFixture
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text())
    raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256']
    assert hashlib.sha256(packet).hexdigest()==m['module_sha256']
    f=HostFixture(raw,h,packet);checks=[]
    def check(n,ok):
        assert ok,n
        checks.append(n)
    check('probe-loads',f.call(h['symbols']['z7_module_load_once'],STATE)==8)
    base=f.words()[12];policy=base+m['symbols']['z7_af_policy'];operation=base+m['symbols']['z7_af_shortcut_operation']
    def op(n,a=0,b=0,c=0):return f.call(operation,n,a,b,c)
    def pending():return int.from_bytes(f.u.mem_read(policy+20,4),'little')
    def take(context=1,busy=0,buttons=31,targets=8191):return op(3,context,busy,buttons|(targets<<5))
    check('all-five-assignments-default-unassigned',bytes(f.u.mem_read(policy,24))==bytes(24))
    for button in range(5):
        for target in range(1,14):
            name=f'{button}-{target}';op(0);op(1,button,target)
            op(2,1,1<<button)
            check(name+'-press-captured',pending()==1<<button)
            check(name+'-busy-defers-without-consuming',take(busy=1)==0 and pending()==1<<button)
            check(name+'-gui-selects-once',take()==((button+1)<<8)|target)
            check(name+'-release-does-not-repeat',take()==0 and pending()==0)
            op(2,1,0);check(name+'-no-edge-no-repeat',take()==0)
            op(2,1,1<<button)
            check(name+'-native-assignment-takes-priority',take(buttons=31^(1<<button))==0 and pending()==0)
            op(2,1,1<<button)
            check(name+'-unavailable-target-consumes-without-action',take(targets=8191^(1<<(target-1)))==0 and pending()==0)
    for context in (0,1):
        for busy in (0,1):
            op(0);op(1,0,1);op(2,1,1)
            result=take(context=context,busy=busy)
            check(f'context-busy-{context}-{busy}',result==(257 if context and not busy else 0) and pending()==(1 if context and busy else 0))
    op(0)
    for i in range(5):op(1,i,i+1);op(2,1,1<<i)
    check('independent-input-events-merge',pending()==31)
    check('first-admitted-button-wins',take(buttons=28)==(3<<8)|3)
    check('coalesced-other-buttons-do-not-replay',take()==0)
    op(2,1,31);op(2,0,0)
    check('input-context-exit-cancels-pending',pending()==0)
    op(2,1,1);op(1,0,0)
    check('unassignment-before-gui-is-respected',take()==0)
    for button,target in ((5,1),(0,14),(0,0xffffffff),(0xffffffff,1)):
        before=bytes(f.u.mem_read(policy,24))
        check(f'invalid-assignment-{button}-{target}',op(1,button,target)==0 and bytes(f.u.mem_read(policy,24))==before)
    f.u.mem_write(policy,struct.pack('<I',0xffffffff));op(2,1,1)
    check('corrupt-target-not-captured',pending()==0)
    f.u.mem_write(policy+20,struct.pack('<I',1))
    check('corrupt-target-not-applied',take()==0)
    op(0);op(1,0,1);op(2,1,0xffffffe0)
    check('unknown-press-bits-ignored',pending()==0)
    check('probe-published-no-gui-hooks',not f.words()[23] and not f.words()[41])
    result=dict(schema=1,passed=True,count=len(checks),checks=checks,module_sha256=m['module_sha256'],
        buttons=5,logical_targets=13,physical_input_verified=False,native_af_setter_executed=False,
        camera_access=False,configuration_persistence_verified=False,cumulative_integration=False,scope=__doc__)
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))

if __name__=='__main__':main()
