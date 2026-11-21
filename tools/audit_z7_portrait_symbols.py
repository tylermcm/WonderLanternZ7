"""Compiled portrait symbol scope and draw through original bitmap/image bodies.

SPDX-License-Identifier: MIT. Native provider/context, PNG decode, font metrics
wrapper, image1A geometry and immediate finish execute. Resource/font metrics,
allocator, graphics-task query and GPU services supplied. No real assets, bitmap
mutex, task/writer closure, asynchronous finish path or GPU pixels established.
"""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import struct
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_LR
from audit_z7_native_symbol_provider import SymbolFixture,GETTER,OVERRIDE,ASSET,OUTPUT,GLYPH,MATRIX
from audit_z7_portrait_native_image import NativeImageFixture
from audit_z7_portrait_text import CODE,MEM,DESCRIPTOR,CONTEXT,UNIT
from audit_z7_portrait_text import MESSAGE,PAYLOAD,TABLE
from audit_z7_native_glyph import FONT_TABLE
from audit_splash_image import STOCK_SHA,synthetic_png
from build_z7_module import build
from build_z7_module_host import ROOT,ZIG

CONFIG,SCOPE,NESTED=MEM+0xd0000,MEM+0xd0100,MEM+0xd0200
LOOKUP=MEM+0xc0400
GPU_SERVICES={0x104303e6,0x1042f894,0x104500c6,0x104500e2,0x1045011a,0x1041477c,
    0x10450096,0x104501f8,0x104501c4,0x1045014e,0x104514e8,0x10451630,0x10450a7c,0x10450aca,
    0x1045004e,0x1045006a,0x1045007e,0x1045016a,0x1045018a,0x104502da,0x1045037e,0x10450a96,
    0x10450aae,0x10450b60,0x1042ecb2,0x10450c86,0x10451338,0x1045081e,0x101e3e2a}

class PortraitSymbolFixture(SymbolFixture):
    def __init__(self,*args):
        super().__init__(*args);self.api=[];self.native_payloads=[];self.images=[];self.order=[]
        self.output_base=0;self.no_asset=False;self.metrics_fail=False;self.output_fail=False;self.replace_provider=False
        self.metadata=args[2];self.image_bytes=self.metadata['image_bytes']
        self.symbol_tags=False;self.draw_phases=[];self.restored_at_ack=0
    def hook(self,u,a,size,context):
        r0=u.reg_read(UC_ARM_REG_R0)
        if a==LOOKUP:
            self.word(u.reg_read(UC_ARM_REG_R2),u.reg_read(UC_ARM_REG_R1));self.ret(0);return
        if a==0x1047aa90 and self.symbol_tags:
            # Font files/shaping are already supplied in DescriptorFixture.
            # Supply the native shaper's type5 tag for custom symbol glyphs;
            # native glyph/provider dispatch after this boundary executes.
            run=u.reg_read(UC_ARM_REG_R1);super().hook(u,a,size,context)
            for i in range(self.read(run+0x28)):
                slot=self.read(run+0x2c)+i*4;code=self.read(slot)
                if 0xe300<=code<=0xefff:self.word(slot,0x50000000|code)
            return
        if a==((CODE+self.metadata['symbols']['z7_portrait_symbol_draw'])&~1) and self.read(r0):
            p=self.read(CODE+self.metadata['symbols']['z7_portrait_symbol_current'])
            if p:self.draw_phases.append((struct.unpack('<6i',u.mem_read(p,24)),struct.unpack('<7i',u.mem_read(self.read(r0+8),28))))
        if a==0x104ba382 and self.symbol_tags:
            state=self.read(CONTEXT+0x45d8);provider=self.read(state+0xb8)
            assert self.read(CODE+self.metadata['symbols']['z7_portrait_symbol_current'])==0
            assert struct.unpack('<5I',u.mem_read(provider,20))==(0xe300,0xefff,0x104bb461,0x104bb605,DESCRIPTOR)
            self.restored_at_ack+=1
        if a in (GETTER,OVERRIDE) and self.no_asset:
            self.resource_calls.append((a==OVERRIDE,r0));self.word(u.reg_read(UC_ARM_REG_R1),0);self.word(u.reg_read(UC_ARM_REG_R2),0);self.ret(0);return
        if a==0x10476e28 and self.metrics_fail:self.ret(1);return
        if a==0x1016fe38 and self.output_fail and CODE<=(u.reg_read(UC_ARM_REG_LR)&~1)<CODE+self.image_bytes:self.ret(0);return
        if a==0x10372390 and self.read(r0+16)==0x4201001a:
            image=struct.unpack('<24I',u.mem_read(self.read(r0+20),96));self.images.append(image);self.order.append('image')
            self.output_base=next(p for p,n in self.live.items() if p<=image[2]<p+n)
            assert image[2]%128==0
            self.pixels=bytes(u.mem_read(image[2],32*24*4))
            if self.replace_provider:self.word(self.read(CONTEXT+0x45d8)+0xb8,0xa1804000)
        if a==0x1042eb0e:self.order.append('finish')
        if a==0x103726c8:self.order.append('owner-query');self.ret(0);return
        if a==0x1045004e:self.order.append('gpu-finish')
        if a==0x1016fe4a and self.output_base and r0==self.output_base:
            assert 'finish' in self.order;self.order.append('free')
        if a in GPU_SERVICES:
            # Every listed address is an explicit handled branch of this shared
            # backend fixture; its fallback super() path is never entered here.
            return NativeImageFixture.hook(self,u,a,size,context)
        super().hook(u,a,size,context)
    def configure(self,orientation=2,sx=57344,sy=57344,top=660,bottom=720,x=100,baseline=690):
        self.u.mem_write(CONFIG,struct.pack('<2I4i',DESCRIPTOR,orientation,sx,sy,top,bottom))
        mx,my=(baseline*UNIT,x*UNIT) if orientation==2 else ((720-baseline)*UNIT,(480-x)*UNIT)
        self.u.mem_write(MATRIX,struct.pack('<7i',0,-sy if orientation==2 else sy,mx,sx if orientation==2 else -sx,0,my,0))
        self.u.mem_write(GLYPH,struct.pack('<3I',1,0xe700,MATRIX))
    def operation(self,name):return CODE+self.metadata['symbols']['z7_portrait_symbol_'+name+'_probe']
    def begin(self):return self.call(self.operation('begin'),CONTEXT,CONFIG,SCOPE)
    def end(self):self.call(self.operation('end'),SCOPE)


def audit(raw,packet,metadata):
    checks=[];cases=0
    def check(name,good):checks.append(dict(name=name,passed=bool(good)));assert good,name
    expected_pixels=bytes(v for y in range(24) for x in range(32) for v in (255 if (x//8+y//8)%2 else 20,40,180,160))
    for orientation in (1,2):
        for name,sx,sy,top,bottom,baseline,box in (
            ('footer',57344,57344,660,720,690,(100,662,28,21)),
            ('dial',43691,43691,283,440,350,(100,328,21,16)),
            ('settings',43691,UNIT,235,720,400,(100,368,21,24)),
            ('external',43691,43691,394,720,500,(100,478,21,16))):
            f=PortraitSymbolFixture(raw,packet,metadata);f.prepare_symbol();f.configure(orientation,sx,sy,top,bottom,100,baseline)
            state=f.read(CONTEXT+0x45d8);old=f.read(state+0xb8);before=set(f.live)
            original=bytes(f.u.mem_read(old,20))
            check(f'{name}-{orientation}-temporary-provider-keeps-measurement',f.begin()==1 and f.read(state+0xb8)==SCOPE and
                  bytes(f.u.mem_read(SCOPE,12))==original[:12] and f.read(SCOPE+16)==DESCRIPTOR)
            callback=f.read(SCOPE+12)
            check(f'{name}-{orientation}-nested-same-provider-rejected',f.call(f.operation('begin'),CONTEXT,CONFIG,NESTED)==0 and f.read(state+0xb8)==SCOPE)
            f.call(f.operation('end'),NESTED)
            check(f'{name}-{orientation}-stock-measure-still-operates',f.call(f.read(SCOPE+8),0xe700,OUTPUT,DESCRIPTOR)==0 and
                  struct.unpack('<4i',f.u.mem_read(OUTPUT,16))==(0,UNIT,104857,0))
            f.resource_calls.clear();f.api.clear();f.events.clear();f.order.clear()
            got=f.call(callback,GLYPH,0,0,DESCRIPTOR)
            x,y,w,h=box
            dest=(y,480-x-w,h,w) if orientation==2 else (720-y-h,x,h,w)
            a,b,c,d=dest;image=f.images[0] if f.images else None
            check(f'{name}-{orientation}-native-png-rotated-image-and-no-source-mutation',got==0 and len(f.images)==1 and image[1]==1 and
                  image[5]==32|(24<<16) and image[6]==a|(b<<16) and image[7]==(a+c)|((b+d)<<16) and
                  image[8]==0xffffffff and image[15]==(90 if orientation==2 else 270) and image[16:18]==(0,0) and
                  image[19:21]==(32,24) and f.pixels==expected_pixels and f.resource_calls==[(False,0xe700)])
            check(f'{name}-{orientation}-native-image-angle-and-finish-before-free',len(f.native_payloads)==1 and
                  [v[0] for a,v in f.api if a==0x1045011a]==[90 if orientation==2 else 270] and
                  [a for a,_ in f.api]==[0x104500c6,0x1045011a,0x104500e2,0x10451338] and
                  f.order==['image','gpu-finish','finish','owner-query','gpu-finish','free'] and set(f.live)==before)
            f.end();check(f'{name}-{orientation}-restores-provider-and-no-stale-draw',f.read(state+0xb8)==old and
                          bytes(f.u.mem_read(old,20))==original and f.call(f.operation('draw'),GLYPH,DESCRIPTOR)==0 and len(f.images)==1)
            f.destroy();check(f'{name}-{orientation}-native-destruction-releases-all',not f.live)
            del f;gc.collect();cases+=1
    for kind in ('left','right','top','bottom','no-asset','metrics-failure','output-allocation','disabled','wrong-descriptor','oversize'):
        f=PortraitSymbolFixture(raw,packet,metadata);f.prepare_symbol();f.configure();before=set(f.live)
        if kind=='left':f.configure(x=-1)
        if kind=='right':f.configure(x=460)
        if kind=='top':f.configure(baseline=680)
        if kind=='bottom':f.configure(baseline=730)
        if kind=='no-asset':f.no_asset=True
        if kind=='metrics-failure':f.metrics_fail=True
        if kind=='output-allocation':f.output_fail=True
        if kind=='disabled':f.word(GLYPH,0)
        if kind=='oversize':f.asset=synthetic_png(481,1,4);f.u.mem_write(ASSET,f.asset)
        assert f.begin()==1
        check(kind+'-no-image-or-finish-or-leak',f.call(f.read(SCOPE+12),GLYPH,0,0,DESCRIPTOR+4 if kind=='wrong-descriptor' else DESCRIPTOR)==0 and
              not f.images and not f.order and set(f.live)==before)
        f.end();f.destroy();check(kind+'-native-destruction-releases-all',not f.live);del f;gc.collect()
    f=PortraitSymbolFixture(raw,packet,metadata);f.prepare_symbol();f.configure();state=f.read(CONTEXT+0x45d8);old=f.read(state+0xb8)
    assert f.begin()==1;f.replace_provider=True;f.call(f.read(SCOPE+12),GLYPH,0,0,DESCRIPTOR);f.end()
    check('foreign-provider-replacement-is-preserved',f.read(state+0xb8)==0xa1804000)
    f.word(state+0xb8,old);f.destroy();check('foreign-replacement-fixture-cleanup',not f.live)
    f=PortraitSymbolFixture(raw,packet,metadata);f.prepare_symbol();f.configure()
    state=f.read(CONTEXT+0x45d8);provider=f.read(state+0xb8);config=bytes(f.u.mem_read(CONFIG,24));source=bytes(f.u.mem_read(provider,20))
    for name,address,value in (('orientation',CONFIG+4,0),('sx-zero',CONFIG+8,0),('sy-large',CONFIG+12,0x20001),
        ('clip-negative',CONFIG+16,0xffffffff),('clip-too-tall',CONFIG+20,721),('descriptor-span',CONFIG,0xaffffffc),
        ('provider-count',state+0xb4,2),('provider-span',state+0xb8,0xaffffffc),('measure',provider+8,0),
        ('draw',provider+12,0),('provider-descriptor',provider+16,DESCRIPTOR+4)):
        f.u.mem_write(CONFIG,config);f.u.mem_write(provider,source);f.word(state+0xb4,1);f.word(state+0xb8,provider);f.word(address,value)
        before=f.read(state+0xb8)
        check('scope-rejects-'+name,f.begin()==0 and f.read(state+0xb8)==before and
              f.read(CODE+metadata['symbols']['z7_portrait_symbol_current'])==0 and not f.images)
    f.u.mem_write(provider,source);f.word(state+0xb4,1);f.word(state+0xb8,provider);f.destroy()
    check('rejected-provider-fixture-cleanup',not f.live);del f;gc.collect()
    native_cases=0
    for command in (0x34,0x37,0x38):
        for orientation in (1,2):
            for page,top,bottom,left,right in ((1,430,454,300,380),(2,100,124,100,180),(3,300,324,100,180),(4,100,124,100,180)):
                for text,override in (('\ue700',False),('A\ue701B',True)):
                    f=PortraitSymbolFixture(raw,packet,metadata);f.prepare_descriptor(command,(orientation,UNIT,UNIT,0,0),text,0)
                    f.word(0xa180ada0,GETTER|1);f.word(0xa180ada4,OVERRIDE|1);f.word(FONT_TABLE+0x28,LOOKUP|1);f.u.mem_write(ASSET,f.asset)
                    f.u.mem_write(DESCRIPTOR+0x5e,struct.pack('<4H',left,480-bottom,right,480-top))
                    if override:f.u.mem_write(DESCRIPTOR+0x86,b'\1');f.word(DESCRIPTOR+0x88,0x12345678)
                    # Native34 registers this provider itself. Native37/38 use
                    # the previously registered descriptor provider as input.
                    if command!=0x34:assert f.call(0x104bbaa2,DESCRIPTOR,CONTEXT)==1
                    f.symbol_tags=True;message=bytes(f.u.mem_read(MESSAGE,28));payload=bytes(f.u.mem_read(PAYLOAD,12))
                    got=f.call(CODE+metadata['symbols']['z7_portrait_text_page_probe'],MESSAGE,page,orientation)
                    check(f'native-text{native_cases}-descriptor-symbol-image-and-once-ack',got==1 and len(f.images)==1 and
                          len(f.draw_phases)==1 and f.restored_at_ack==1 and f.pixels==expected_pixels and
                          f.resource_calls and all(c==(override,0x12345678 if override else 0xe700) for c in f.resource_calls) and
                          f.matrix()==(UNIT,0,0,0,UNIT,0,1) and f.read(CONTEXT+0x45b4)==TABLE and
                          bytes(f.u.mem_read(PAYLOAD,12))==payload and bytes(f.u.mem_read(MESSAGE,28))==message[:24]+bytes(4) and
                          f.events[-3:]==[('defer',0x42010063,0),('ack',0x42010063,0),'event'])
                    config,m=f.draw_phases[0];_,o,sx,sy,clip_top,clip_bottom=config
                    px=m[5] if o==2 else 480*UNIT-m[5];baseline=m[2] if o==2 else 720*UNIT-m[2]
                    logical=(px//UNIT,(baseline-(32*UNIT*sy//UNIT))//UNIT,32*sx//UNIT,24*sy//UNIT)
                    x,y,w,h=logical;dest=(y,480-x-w,h,w) if o==2 else (720-y-h,x,h,w)
                    a,b,c,d=dest;image=f.images[0]
                    check(f'native-text{native_cases}-actual-native-glyph-phase-and-clipping',image[6]==(a|(b<<16)) and
                          image[7]==((a+c)|((b+d)<<16)) and y>=clip_top and y+h<=clip_bottom and
                          f.order.index('image')<f.order.index('finish')<f.order.index('free'))
                    f.destroy();check(f'native-text{native_cases}-native-destruction-releases-all',not f.live)
                    del f;gc.collect();native_cases+=1
    return dict(passed=True,checks=checks,native_rotated_symbol_cases=cases,native_text_symbol_cases=native_cases,
                compiled_scope_rotation_clipping_original_png_image1a_format_and_immediate_finish_execute=True,
                original_descriptors_glyph_provider_dispatch_and_temporary_scope_restoration_execute=True,
                resource_font_metrics_glyph_lookup_shaping_type5_tags_allocator_gpu_and_task_query_supplied=True,
                real_font_classification_assets_bitmap_mutex_async_finish_task_lifetime_or_pixels_proven=False,camera_card_access=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    raw=a.stock_main.read_bytes();assert hashlib.sha256(raw).hexdigest()==STOCK_SHA
    source=ROOT/'z7-native-modules/examples/portrait_text_layout_probe.c';packet,metadata=build(source,zig=ZIG);again,other=build(source,zig=ZIG)
    assert packet==again and metadata==other
    result=audit(raw,packet,metadata)
    names=['tools/audit_z7_portrait_symbols.py','tools/audit_z7_native_symbol_provider.py','tools/audit_z7_native_text_descriptor.py','tools/audit_z7_native_glyph.py',
           'tools/audit_z7_portrait_native_image.py','tools/audit_z7_portrait_page_message.py','tools/audit_z7_portrait_grid_message.py','tools/audit_z7_portrait_draw.py',
           'tools/audit_z7_portrait_text.py','tools/audit_splash_image.py','tools/build_z7_module.py',
           'z7-native-modules/examples/portrait_text_layout_probe.c','z7-native-modules/sdk/module.h','z7-native-modules/sdk/module.ld']
    names+=['z7-native-modules/plugins/'+n+'.h' for n in ('portrait_text_layout','portrait_text','portrait_symbols','portrait_symbol_bitmap','portrait_bands',
             'portrait_page_message','portrait_grid_message','portrait_grid','portrait_footer','portrait_geometry','portrait_draw')]
    result.update(probe_sha256=hashlib.sha256(packet).hexdigest(),probe_bytes=len(packet),image_bytes=metadata['image_bytes'],bss_bytes=metadata['bss_bytes'],
                  relocations=len(metadata['relocations']),reproducible_probe=True,source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(packet)
    (out/'probe.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),symbol_cases=result['native_rotated_symbol_cases'],native_text_cases=result['native_text_symbol_cases'])))


if __name__=='__main__':main()
