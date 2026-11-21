"""Original Z7 bitmap-reader execution for bounded portrait symbol decode.

SPDX-License-Identifier: MIT. Native reader/header/pixel decode and cleanup run;
allocation is supplied. No symbol provider, resource registration, GPU rendering,
bitmap mutex/task exclusion, native font assets or camera pixels are proved.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_LR
from audit_splash_image import NativePNG,STOCK_SHA,MEM,synthetic_png
from build_z7_module import build,HEADER
from build_z7_module_host import ROOT,ZIG

CODE,ASSET,INFO=MEM+0x10000,MEM+0x20000,MEM+0x30000

class BitmapFixture(NativePNG):
    def __init__(self,raw,packet,metadata,fail=0,output_fail=False):
        super().__init__(raw,fail);self.native_call_timeout_us=0
        image=bytearray(packet[HEADER:HEADER+metadata['image_bytes']])
        for off in metadata['relocations']:struct.pack_into('<I',image,off,struct.unpack_from('<I',image,off)[0]+CODE)
        self.u.mem_write(CODE,bytes(image));self.u.mem_write(CODE+len(image),bytes(metadata['bss_bytes']))
        self.entry=CODE+metadata['symbols']['z7_portrait_symbol_bitmap_probe'];self.image_bytes=len(image)
        self.output_fail=output_fail;self.output_attempts=0;self.native=[]
    def hook(self,u,address,size,context):
        if address in (0x104313d0,0x10431278,0x104311f4,0x10373b40):self.native.append(address)
        if address==0x1016fe38 and CODE<=(u.reg_read(UC_ARM_REG_LR)&~1)<CODE+self.image_bytes:
            self.output_attempts+=1
            if self.output_fail:self.ret(0);return
            length=u.reg_read(UC_ARM_REG_R0)
            super().hook(u,address,size,context)
            u.mem_write(u.reg_read(UC_ARM_REG_R0),b'\xa5'*length);return
        super().hook(u,address,size,context)


def audit(raw,packet,metadata):
    checks=[];cases=0
    def check(name,good):checks.append(dict(name=name,passed=bool(good)));assert good,name
    for width,height,channels in ((32,24,3),(32,24,4),(17,9,4),(480,1,4),(1,480,3)):
        f=BitmapFixture(raw,packet,metadata);asset=synthetic_png(width,height,channels);f.u.mem_write(ASSET,asset)
        f.u.mem_write(INFO-16,b'\xa5'*84)
        allocation=f.call(f.entry,ASSET,len(asset),INFO);fields=struct.unpack('<13I',f.u.mem_read(INFO,52))
        check(f'decode-{width}x{height}-{channels}-bounded-allocation',allocation!=0 and list(f.live)==[allocation] and
              fields[:2]==(width,height) and fields[8]<=128*1024 and fields[9]*height<=fields[8] and f.output_attempts==1)
        pixels=(allocation+127)&~127;stride=fields[9]
        expected=bytes(value for y in range(height) for x in range(width)
                       for value in (255 if (x//8+y//8)%2 else 20,40,180,160 if channels==4 else 255))
        actual=b''.join(bytes(f.u.mem_read(pixels+y*stride,width*4)) for y in range(height))
        check(f'decode-{width}x{height}-{channels}-native-exact-active-rgba',actual==expected and pixels%128==0 and
              all(a in f.native for a in (0x104313d0,0x10431278,0x104311f4,0x10373b40)))
        tail=f.live[allocation]-(pixels-allocation)-fields[8]
        check(f'decode-{width}x{height}-{channels}-metadata-and-output-guards',tail>=0 and
              bytes(f.u.mem_read(INFO-16,16))==b'\xa5'*16 and bytes(f.u.mem_read(INFO+52,16))==b'\xa5'*16 and
              bytes(f.u.mem_read(allocation,pixels-allocation))==b'\xa5'*(pixels-allocation) and
              bytes(f.u.mem_read(pixels+fields[8],tail))==b'\xa5'*tail)
        f.call(0x1016fe4a,allocation);check(f'decode-{width}x{height}-{channels}-caller-release',not f.live)
        cases+=1
    for width,height in ((481,1),(1,481),(480,480)):
        f=BitmapFixture(raw,packet,metadata);asset=synthetic_png(width,height,4);f.u.mem_write(ASSET,asset)
        check(f'oversize-{width}x{height}-releases-reader-before-output-allocation',f.call(f.entry,ASSET,len(asset),INFO)==0 and
              not f.live and f.output_attempts==0 and 0x104311f4 not in f.native and 0x10373b40 in f.native)
    for fail in (1,2,3):
        f=BitmapFixture(raw,packet,metadata,fail);asset=synthetic_png(32,24,4);f.u.mem_write(ASSET,asset)
        check(f'reader-allocation-failure{fail}-returns-without-leak',f.call(f.entry,ASSET,len(asset),INFO)==0 and not f.live and f.output_attempts==0)
    f=BitmapFixture(raw,packet,metadata,output_fail=True);asset=synthetic_png(32,24,4);f.u.mem_write(ASSET,asset)
    check('output-allocation-failure-releases-reader',f.call(f.entry,ASSET,len(asset),INFO)==0 and not f.live and f.output_attempts==1)
    for args in ((0,10,INFO),(ASSET,0,INFO),(ASSET,10,0)):
        f=BitmapFixture(raw,packet,metadata)
        check(f'missing-input{args}-no-native-access',f.call(f.entry,*args)==0 and not f.live and not f.native)
    return dict(passed=True,checks=checks,exact_native_pixel_cases=cases,
                original_reader_header_png_pixel_decode_and_cleanup_execute=True,
                allocator_and_synthetic_png_assets_supplied=True,
                symbol_provider_native_assets_gpu_pixels_mutex_or_task_lifetime_proven=False,camera_card_access=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    raw=a.stock_main.read_bytes();assert hashlib.sha256(raw).hexdigest()==STOCK_SHA
    source=ROOT/'z7-native-modules/examples/portrait_symbol_bitmap_probe.c'
    packet,metadata=build(source,zig=ZIG);again,other=build(source,zig=ZIG);assert packet==again and metadata==other
    result=audit(raw,packet,metadata)
    names=('tools/audit_z7_portrait_symbol_bitmap.py','tools/audit_splash_image.py','tools/build_z7_module.py',
           'z7-native-modules/examples/portrait_symbol_bitmap_probe.c','z7-native-modules/sdk/module.h','z7-native-modules/sdk/module.ld',
           'z7-native-modules/plugins/portrait_symbol_bitmap.h')
    result.update(probe_sha256=hashlib.sha256(packet).hexdigest(),probe_bytes=len(packet),image_bytes=metadata['image_bytes'],
                  bss_bytes=metadata['bss_bytes'],relocations=len(metadata['relocations']),reproducible_probe=True,
                  source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(packet)
    (out/'probe.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),pixel_cases=result['exact_native_pixel_cases'])))


if __name__=='__main__':main()
