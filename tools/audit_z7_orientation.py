"""Native orientation read/override branches and compiled portrait box math.

SPDX-License-Identifier: MIT. Native getter/wrapper/setter/notification dispatch
and compiled sampling/geometry execute. Sensor/gate inputs and notify sink are
supplied. No physical IMU, graphics hook, pixel rotation or camera/card proof.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import random
import struct

from audit_splash_image import NativePNG, BASE, MEM, STOCK_SHA
from build_z7_module import build, HEADER
from build_z7_module_host import ROOT, ZIG
from z30_extensions.assembly import assemble, constant

GETTER, NORMALIZED, SETTER = 0x101b331a, 0x10532fd6, 0x101b4224
STATE, DATA = 0xa180906c, 0xa1d494f4
GATE, SELECTOR, SENSOR, NOTIFY = STATE+8, DATA+0x290, DATA+0xe8, STATE+0x1c
CODE, CALLBACK, LOG, INPUT, OUTPUT = (MEM+off for off in (0x10000,0x20000,0x30000,0x40000,0x40100))
MAPPING = {1:0,2:3,3:1,4:2}


class OrientationFixture(NativePNG):
    def __init__(self,raw,packet,metadata):
        super().__init__(raw)
        # These small calls retain NativePNG's instruction bound. Avoid a new
        # Unicorn timeout thread for each matrix cell on Windows.
        self.native_call_timeout_us=0
        self.u.mem_map(0xa1d49000,0x1000)
        if metadata['relocations']:raise AssertionError('Unexpected flat-probe relocation')
        self.u.mem_write(CODE,packet[HEADER:HEADER+metadata['image_bytes']])
        self.operation=CODE+metadata['symbols']['z7_portrait_probe_operation']
        self.write(NOTIFY,0)
    def write(self,p,v):self.u.mem_write(p,struct.pack('<I',v))
    def read(self,p):return int.from_bytes(self.u.mem_read(p,4),'little')
    def box(self,p):return struct.unpack('<4i',self.u.mem_read(p,16))
    def op(self,operation,orientation=0,inp=INPUT,out=OUTPUT):return self.call(self.operation,operation,orientation,inp,out)


def projected_box(box,orientation):
    # Independent reference: rotate four exclusive edge corners, then take
    # their enclosing bounds instead of repeating the C rectangle expression.
    x,y,w,h=box
    points=[(x,y),(x+w,y),(x,y+h),(x+w,y+h)]
    points=[(py,720-px) if orientation==1 else (480-py,px) for px,py in points]
    xs,ys=zip(*points)
    return min(xs),min(ys),max(xs)-min(xs),max(ys)-min(ys)


def audit(raw,packet,metadata):
    f=OrientationFixture(raw,packet,metadata);checks=[]
    def check(name,good):
        checks.append(dict(name=name,passed=bool(good)))
        if not good:raise AssertionError(name)
    check('native-literal-pool-binds-gate-state-and-sensor-control-data',
          struct.unpack_from('<2I',raw,0x101b36d0-BASE)==(DATA,STATE))
    # Gate word exactly1 selects the supplied physical sample. Otherwise only
    # override1..4 selects a known value; selector0 is unknown4, not physical.
    rows=0
    for gate,selector in itertools.product((0,1,2,0xffffffff),(*range(8),0xffffffff)):
        f.write(GATE,gate);f.write(SELECTOR,selector)
        for sensor in range(256):
            f.u.mem_write(SENSOR,bytes([sensor]))
            expected=sensor if gate==1 else MAPPING.get(selector,4)
            actual=f.call(GETTER);normal=f.call(NORMALIZED)
            f.u.mem_write(OUTPUT,b'\xa5'*16);sample=f.op(0)
            expected_out=struct.pack('<I',expected)+b'\xa5'*12 if expected<4 else b'\xa5'*16
            check(f'gate{gate}-selector{selector}-sensor{sensor}-native-and-bounded-sample',
                  actual==expected and normal==(0 if expected==4 else expected) and sample==int(expected<4) and
                  bytes(f.u.mem_read(OUTPUT,16))==expected_out and f.read(GATE)==gate and f.read(SELECTOR)==selector and bytes(f.u.mem_read(SENSOR,1))==bytes([sensor]))
            rows+=1
    check('null-orientation-output-rejected',f.op(0,out=0)==0)
    print('Native orientation matrix passed: '+str(rows),flush=True)
    # Supplied callback sink executes Thumb instructions, while the original
    # setter/getters/conditional tail dispatch execute without replacements.
    code=constant('r2',LOG)+' str r0,[r2]; str r1,[r2,#4]; ldr r3,[r2,#8]; adds r3,#1; str r3,[r2,#8]; movs r0,#0; bx lr;'
    f.u.mem_write(CALLBACK,assemble(code,CALLBACK,64));f.write(NOTIFY,CALLBACK|1)
    event=(struct.unpack_from('<I',raw,0x101b4434-BASE)[0]+1)&0xffffffff
    notifications=0
    for gate,sensor,before,after in itertools.product((0,1),(0,1,2,3,4,255),range(6),(0,1,2,3,4,5,0xffffffff)):
        f.write(GATE,gate);f.write(SELECTOR,before);f.u.mem_write(SENSOR,bytes([sensor]));f.u.mem_write(LOG,bytes(12))
        old=sensor if gate==1 else MAPPING.get(before,4);new=sensor if gate==1 else MAPPING.get(after,4)
        f.call(SETTER,after);observed=struct.unpack('<3I',f.u.mem_read(LOG,12))
        check(f'override-gate{gate}-sensor{sensor}-from{before}-to{after}-native-notification',
              f.read(SELECTOR)==after and f.call(GETTER)==new and observed==((event,new,1) if new!=old else (0,0,0)))
        notifications+=1
    f.write(NOTIFY,0);f.write(GATE,0);f.write(SELECTOR,1);f.call(SETTER,3)
    check('null-native-notification-slot-keeps-original-override-behavior',f.call(GETTER)==1 and f.read(SELECTOR)==3)
    # Representative HUD/control sizes plus every edge and extreme invalid word.
    boxes=set()
    for x,y,w,h in itertools.product((0,1,40,110,283,360,719),(0,1,194,218,420,479),(1,2,24,40,110,200,480,720),(1,2,24,40,60,200,480)):
        if x+w<=720 and y+h<=480:boxes.add((x,y,w,h))
    for box in sorted(boxes):
        for orientation in (1,2):
            f.u.mem_write(INPUT,struct.pack('<4i',*box));before=bytes(f.u.mem_read(INPUT,16))
            good=f.op(1,orientation)==1;rotated=f.box(OUTPUT);x,y,w,h=rotated
            good=good and rotated==projected_box(box,orientation) and x>=0 and y>=0 and x+w<=480 and y+h<=720 and w*h==box[2]*box[3] and bytes(f.u.mem_read(INPUT,16))==before
            f.u.mem_write(INPUT,struct.pack('<4i',*rotated))
            good=good and f.op(2,orientation)==1 and f.box(OUTPUT)==box
            f.u.mem_write(INPUT,before)
            good=good and f.op(1,orientation,out=INPUT)==1 and f.box(INPUT)==rotated and f.op(2,orientation,out=INPUT)==1 and f.box(INPUT)==box
            check(f'portrait{orientation}-box{box}-corners-bounds-area-and-inplace-round-trip',good)
    invalid=[(-1,0,1,1),(0,-1,1,1),(0,0,0,1),(0,0,1,0),(720,0,1,1),(0,480,1,1),(0,0,721,1),(0,0,1,481),
             (0x7fffffff,0,1,1),(-0x80000000,0,1,1),(0,0,0x7fffffff,1),(0,0,1,-0x80000000)]
    rng=random.Random(0x7c0380)
    invalid += [tuple(rng.randint(-0x80000000,0x7fffffff) for _ in range(4)) for _ in range(256)]
    for operation,orientation,box in itertools.product((1,2),(1,2),invalid):
        width,height=(720,480) if operation==1 else (480,720)
        x,y,w,h=box
        if x>=0 and y>=0 and w>0 and h>0 and x+w<=width and y+h<=height:continue
        f.u.mem_write(INPUT,struct.pack('<4i',*box));f.u.mem_write(OUTPUT,b'\xa5'*16)
        check(f'invalid-op{operation}-portrait{orientation}-box{box}-preserves-output',f.op(operation,orientation)==0 and bytes(f.u.mem_read(OUTPUT,16))==b'\xa5'*16)
    f.u.mem_write(INPUT,struct.pack('<4i',0,0,1,1))
    for operation,orientation in itertools.product((1,2),(0,3,4,0xffffffff)):
        f.u.mem_write(OUTPUT,b'\xa5'*16)
        check(f'unsupported-op{operation}-orientation{orientation}-preserves-output',f.op(operation,orientation)==0 and bytes(f.u.mem_read(OUTPUT,16))==b'\xa5'*16)
    for operation in (1,2):
        f.u.mem_write(OUTPUT,b'\xa5'*16)
        check(f'null-op{operation}-input-or-output-rejected',f.op(operation,1,inp=0)==0 and bytes(f.u.mem_read(OUTPUT,16))==b'\xa5'*16 and f.op(operation,1,out=0)==0)
    return dict(passed=True,checks=checks,native_orientation_cases=rows,native_override_notification_cases=notifications,
                valid_box_cases=len(boxes)*2,stock_main_sha256=STOCK_SHA,
                native_getter_normalizing_wrapper_setter_and_notification_dispatch_execute=True,
                compiled_readonly_sampler_and_geometry_execute=True,flat_probe_loader_validation_exercised=False,
                sensor_gate_selector_inputs_and_notification_sink_supplied=True,
                physical_imu_live_graphics_hook_rotated_pixels_or_installation_proven=False,camera_card_access=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private output directory')
    raw=a.stock_main.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=STOCK_SHA:p.error('Exact original-Z7 C3.80 MAIN required')
    source=ROOT/'z7-native-modules/examples/portrait_geometry_probe.c';packet,metadata=build(source,zig=ZIG);again,repeated=build(source,zig=ZIG)
    if packet!=again or metadata!=repeated:raise AssertionError('Probe must build reproducibly')
    result=audit(raw,packet,metadata)
    names=('tools/audit_z7_orientation.py','tools/audit_splash_image.py','tools/build_z7_module.py','z7-native-modules/sdk/module.h',
           'z7-native-modules/sdk/module.ld','z7-native-modules/plugins/portrait_geometry.h','z7-native-modules/plugins/orientation_sample.h',
           'z7-native-modules/examples/portrait_geometry_probe.c')
    result.update(probe_sha256=hashlib.sha256(packet).hexdigest(),reproducible_probe=True,
                  source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(packet)
    (out/'probe.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),native_cases=result['native_orientation_cases'],geometry_cases=result['valid_box_cases'],probe_bytes=len(packet))))


if __name__=='__main__':main()
