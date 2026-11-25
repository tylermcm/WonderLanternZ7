"""Original-Z7 movie capacity and native duration ceiling contract (MIT).

All capacity, format lookup, bytes-to-time and arithmetic instructions execute.
Configuration, card capacity, allocation unit, reservation and quota are supplied.
No task hook, recorder update, hardware recording or recovery is established.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from audit_splash_image import NativePNG,MEM,STOCK_SHA
from prepare_flash_review import require_private_output

CAPACITY=0x10270c22
STOCK_MS=1799000
MAX_MS=359999000


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--candidate-build',type=Path)
    p.add_argument('--control-build',type=Path)
    a=p.parse_args();out=require_private_output(a.output);raw=a.stock_main.read_bytes()
    if bool(a.candidate_build)!=bool(a.control_build):p.error('Candidate and control builds must be supplied together')
    assert hashlib.sha256(raw).hexdigest()==STOCK_SHA
    f=NativePNG(raw);request=MEM+0x1000;config=MEM+0x2000;volumes=MEM+0x2100;reserve=MEM+0x2300
    checks=[];observations=[]
    def check(name,good):
        assert good,name
        checks.append(name)
    def run(policy,mode=0,rate=2,quality=0,free=64<<30,reserved=0,unit=0x20000,files=1,quota=1000000,volume_state=5,selected=0):
        configuration=bytearray(0x100);struct.pack_into('<I',configuration,0,1)
        configuration[4:7]=bytes([mode,rate,0]);configuration[12]=quality
        volume=bytearray(0x68);struct.pack_into('<I',volume,0,1)
        volume[8]=volume_state;volume[0x48]=selected
        struct.pack_into('<Q',volume,0x10,free);struct.pack_into('<I',volume,0x18,unit);struct.pack_into('<I',volume,0x20,quota)
        reservation=struct.pack('<2I',reserved,0)
        f.u.mem_write(config,bytes(configuration));f.u.mem_write(volumes,bytes(volume));f.u.mem_write(reserve,reservation)
        f.u.mem_write(request-4,b'HEAD'+struct.pack('<10I',policy,config,volumes,reserve,files,0xa5a5a5a5,0,0,0,0)+b'TAIL')
        inputs=[bytes(f.u.mem_read(address,length)) for address,length in ((config,0x100),(volumes,0x68),(reserve,8))]
        f.call(CAPACITY,request)
        result=struct.unpack('<10I',f.u.mem_read(request,40))
        check('bounded-native-output-'+str(len(checks)),bytes(f.u.mem_read(request-4,4))==b'HEAD' and bytes(f.u.mem_read(request+40,4))==b'TAIL' and result[:5]==(policy,config,volumes,reserve,files))
        check('native-inputs-unchanged-'+str(len(checks)),inputs==[bytes(f.u.mem_read(address,length)) for address,length in ((config,0x100),(volumes,0x68),(reserve,8))])
        return result[5],result[6:]
    for mode in (0,1):
        for rate in range(7):
            for quality in (0,1):
                ordinary,_=run(0,mode,rate,quality);alternative,_=run(1,mode,rate,quality)
                admitted=bool(mode or rate>=2)
                check(f'stock-format-admission-{mode}-{rate}-{quality}',ordinary==(STOCK_MS if admitted else 0))
                check(f'alternative-native-capacity-{mode}-{rate}-{quality}',STOCK_MS<alternative<=MAX_MS)
                observations.append(dict(mode=mode,rate=rate,quality=quality,ordinary_ms=ordinary,alternative_ms=alternative,ordinary_format_admitted=admitted))
    for kwargs in (dict(free=0),dict(free=4096,reserved=4096),dict(free=4096,reserved=8192),dict(unit=0),dict(unit=0x2000001),dict(volume_state=0),dict(quota=0),dict(selected=1)):
        duration,_=run(1,**kwargs)
        check('native-capacity-rejects-'+str(kwargs),duration==0)
    low,_=run(1,free=1<<30);high,_=run(1,free=64<<30)
    check('native-capacity-retains-free-space-dependence',0<low<STOCK_MS<high)
    candidate_sha=None
    if a.candidate_build:
        from z7_movie_duration import TABLE,FIRST_ORDINARY,ORDINARY_COUNT,EXTENDED_MS
        candidate=(a.candidate_build/'module-host.emulator.main.bin').read_bytes()
        control=(a.control_build/'module-host.emulator.main.bin').read_bytes()
        cm=json.loads((a.candidate_build/'module-host.emulator.json').read_text())
        bm=json.loads((a.control_build/'module-host.emulator.json').read_text())
        assert cm['extend_movie_duration'] and not bm['extend_movie_duration']
        assert hashlib.sha256(candidate).hexdigest()==cm['main_payload_sha256']
        assert hashlib.sha256(control).hexdigest()==bm['main_payload_sha256']
        start=TABLE+FIRST_ORDINARY*4-0x10020000;size=ORDINARY_COUNT*4
        check('exactly-the-reviewed-native-table-changes',candidate[:start]==control[:start] and candidate[start+size:]==control[start+size:])
        check('control-retains-native-ordinary-ceilings',control[start:start+size]==struct.pack('<24I',*([STOCK_MS]*24)))
        check('candidate-uses-existing-native-alternative-ceiling',candidate[start:start+size]==struct.pack('<24I',*([EXTENDED_MS]*24)))
        stock_fixture=f;candidate_fixture=NativePNG(candidate)
        for mode in (0,1):
            for rate in range(7):
                for quality in (0,1):
                    f=stock_fixture;reference=run(1 if mode or rate>=2 else 0,mode,rate,quality)
                    f=candidate_fixture;actual=run(0,mode,rate,quality)
                    check(f'candidate-native-capacity-and-flags-{mode}-{rate}-{quality}',actual==reference)
        for case in (dict(free=0),dict(free=1<<30),dict(free=4096,reserved=8192),dict(unit=0),dict(quota=0),dict(selected=1)):
            f=stock_fixture;reference=run(1,**case)
            f=candidate_fixture;actual=run(0,**case)
            check('candidate-retains-native-capacity-guard-'+str(case),actual==reference)
        candidate_sha=cm['main_payload_sha256']
    result=dict(passed=True,count=len(checks),checks=checks,stock_main_sha256=STOCK_SHA,
        native_capacity_entry=hex(CAPACITY),stock_ceiling_ms=STOCK_MS,alternative_ceiling_ms=MAX_MS,
        format_observations=observations,physical_card=False,camera_access=False,
        task_hooks_implemented=False,recording_duration_extended=False,scope=__doc__)
    if candidate_sha:
        result.update(candidate_main_sha256=candidate_sha,native_capacity_table_extended=True,
            full_recording_path_verified=False,physical_recording_verified=False)
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks),formats=len(observations))))


if __name__=='__main__':main()
