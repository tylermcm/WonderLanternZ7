"""Execute bounded original-Z7 module-read retries and close handling (MIT).

Filesystem/task/allocator boundaries are supplied. No camera or update writer.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_SP, UC_ARM_REG_LR
from audit_z7_module_host import HostFixture
from build_z7_module import pack_module
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output


class RetryFixture(HostFixture):
    def __init__(self, raw, host, packet, scenario):
        super().__init__(raw, host, packet)
        self.scenario = scenario

    def hook(self, u, address, size, context):
        original = self.case
        if address == 0x1027beae:
            p = u.reg_read(UC_ARM_REG_R0)
            op = bytes(u.mem_read(p+0x9c,1))[0]
            if op == 5:
                self.position = 0
            if self.scenario == 'missing':
                self.case = 'missing'
            elif self.scenario == 'bad-size':
                self.case = 'bad-size'
            elif op == 8 and self.scenario in ('permanent-read-error','read-error-then-ok','short-read-then-ok','read-and-close-error'):
                failing = self.scenario in ('permanent-read-error','read-and-close-error') or self.open_count <= 2
                if failing:
                    self.case = 'short-read' if self.scenario == 'short-read-then-ok' else 'read-error'
            elif op == 6 and self.scenario == 'read-and-close-error':
                self.case = 'close-error'
        try:
            super().hook(u,address,size,context)
        finally:
            self.case = original


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    host=json.loads((a.build/'module-host.emulator.json').read_text())
    raw=(a.build/'module-host.emulator.main.bin').read_bytes()
    assert host['retry_read_failures'] and hashlib.sha256(raw).hexdigest()==host['main_payload_sha256']
    packet=pack_module(bytes.fromhex('00207047')+bytes(60),64,0)
    failed_init=pack_module(bytes.fromhex('01207047')+bytes(60),64,0)
    corrupt=bytearray(packet);corrupt[0]=0
    checks=[];scenarios=[]
    def check(name,good):
        assert good,name
        checks.append(name)
    for case,attempts,status,data in (
        ('read-error-then-ok',3,8,packet),('short-read-then-ok',3,8,packet),
        ('permanent-read-error',100,4,packet),('read-and-close-error',1,5,packet),
        ('missing',100,1,packet),('bad-size',1,2,packet),
        ('invalid-module',1,6,bytes(corrupt)),('failed-init',1,7,failed_init)):
        f=RetryFixture(raw,host,data,case)
        f.u.reg_write(UC_ARM_REG_R0,STATE);f.u.reg_write(UC_ARM_REG_SP,0x503f0000)
        f.u.reg_write(UC_ARM_REG_LR,0x503ff001)
        f.u.emu_start(host['symbols']['z7_module_worker'],0,timeout=10000000,count=10000000)
        check(case+'-bounded-result',f.result_seen and f.words()[17]==attempts and f.words()[10]==status)
        check(case+'-bounded-backoff',sum(e==('delay',100) for e in f.events)==attempts-1)
        check(case+'-single-resident-park',f.events[-1]==('delay',1000))
        check(case+'-open-close-count',f.open_count==attempts and f.close_count==(0 if case=='missing' else attempts))
        check(case+'-no-leaked-raw-allocation',len(f.allocations)-f.frees==int(status==8))
        if case=='read-and-close-error':
            before=list(f.events)
            check('uncertain-close-remains-terminal',f.call(host['symbols']['z7_module_load_once'],STATE)==5 and f.events==before)
        scenarios.append(dict(case=case,attempts=attempts,status=status,opens=f.open_count,closes=f.close_count))
    report=dict(passed=True,count=len(checks),checks=checks,scenarios=scenarios,
        main_sha256=host['main_payload_sha256'],scope=__doc__,camera_access=False,
        firmware_update_authorized=False,upstream_commit='e9879e077028b20fc799b9bc13f7e585b71e9f32')
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks),scenarios=len(scenarios))))


if __name__=='__main__':
    main()
