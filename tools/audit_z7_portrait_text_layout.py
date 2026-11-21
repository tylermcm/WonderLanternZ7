"""Compiled native callback menu text placement against explicit layout cases.

SPDX-License-Identifier: MIT. Original dispatch/completion execute; descriptor
processing, glyph emission, font state and kernel event are supplied. Does not
prove native font loading, inline symbols, pixels or graphics-task lifetime.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import struct
from audit_z7_portrait_text import (TextFixture,audit as fixed_audit,reference,UNIT,
    CONTEXT,DESCRIPTOR,MESSAGE,PAYLOAD,ORIGIN,OPTIONS,METRICS,BOUNDS,TABLE)
from audit_splash_image import STOCK_SHA
from build_z7_module import build
from build_z7_module_host import ROOT,ZIG


def audit(raw,packet,metadata):
    result=fixed_audit(raw,packet,metadata)
    f=TextFixture(raw,packet,metadata);checks=result['checks']
    entry=f.entry+(metadata['symbols']['z7_portrait_text_page_probe']-metadata['symbols']['z7_portrait_text_probe'])
    def check(name,good):
        checks.append(dict(name=name,passed=bool(good)))
        assert good,name
    # Explicit portrait destinations from the pinned layout: tile0 local10,20
    # moves down160; bottom-right tile11 moves left240/down233; title down162.
    S=43691;U=UNIT
    cases=[
        ('first-tile',1,10,320,80,20,(0,0,720,100),(U,U,0,160*U)),
        ('last-tile',1,610,390,80,20,(0,0,720,100),(U,U,-240*U,233*U)),
        ('title',1,120,250,100,20,(88,228,632,272),(U,U,-120*U,162*U)),
        ('descriptor-title-anchor',1,120,300,100,20,(88,228,632,272),(U,U,-120*U,162*U)),
        ('wide-title',1,100,250,544,20,(88,228,632,272),(U,U,-100*U,162*U)),
        ('dial',2,100,200,80,20,(0,0,720,100),(S,S,66*U-100*S,374*U-180*S)),
        ('dial-title-fits-page',2,120,250,100,20,(88,228,632,272),(S,S,80*U-120*S,422*U-252*S)),
        ('setting',3,100,200,80,20,(0,0,720,100),(S,U,66*U-100*S,235*U)),
        ('external',4,100,200,80,20,(0,0,720,100),(S,S,66*U-100*S,514*U-180*S)),
        ('grid-footer',1,300,450,80,20,(300,430,380,454),(57344,57344,-211*U,295*U)),
        ('dial-footer',2,300,450,80,20,(300,430,380,454),(57344,57344,-211*U,295*U)),
        ('left-footer-suppressed',1,100,450,80,20,(100,430,180,454),None),
        ('zero-footer-suppressed',2,300,450,0,0,(300,430,380,454),None),
        ('setting-footer-zero-size',3,100,450,0,0,(100,430,180,454),(S,U,0,235*U)),
        ('external-footer',4,100,450,80,20,(100,430,180,454),(S,S,0,394*U)),
        ('unmapped-grid-header',1,100,100,80,20,(0,0,720,100),'stock'),
        ('outside-right',1,720,320,80,20,(0,0,720,100),'stock'),
        ('outside-footer-right',1,720,450,80,20,(300,430,380,454),None),
    ]
    count=0
    for command,orientation,case in itertools.product((0x34,0x37,0x38),(1,2),cases):
        name,page,x,y,w,h,box,expected=case
        matrix=(U,0,0,0,U,0,1)
        f.reset(command,matrix,(orientation,U,U,0,0))
        f.u.mem_write(DESCRIPTOR,bytes(0xc8));f.word(DESCRIPTOR+0x94,CONTEXT)
        for off,v in ((8,w),(10,h),(0xac,w),(0xae,h),(0x5e,box[0]),(0x62,box[2]),(0x64,480-box[1]),(0x60,480-box[3])):
            f.u.mem_write(DESCRIPTOR+off,struct.pack('<H',v&0xffff))
        f.u.mem_write(ORIGIN,struct.pack('<2i',x*U,(480-y)*U))
        before=bytes(f.u.mem_read(DESCRIPTOR,0xc8));payload=bytes(f.u.mem_read(PAYLOAD,12))
        got=f.call(entry,MESSAGE,page,orientation)
        matrices=[] if expected is None else [matrix if expected=='stock' else reference(matrix,(orientation,*expected))]
        check(f'{name}-command{command:x}-orientation{orientation}',got==1 and
              [c[1] for c in f.calls]==matrices and f.matrix()==matrix and
              bytes(f.u.mem_read(DESCRIPTOR,0xc8))==before and bytes(f.u.mem_read(PAYLOAD,12))==payload and
              f.read(CONTEXT+0x45b4)==TABLE and bytes(f.u.mem_read(f.state,8))==bytes(8) and
              bytes(f.u.mem_read(f.state+28,8))==bytes(8) and
              f.events[-3:]==[('defer',0x42010063,0),('ack',0x42010063,0),'event'])
        count+=1
    for origin,metrics,bounds in itertools.product((0,ORIGIN),(0,METRICS),(0,BOUNDS)):
        if origin and not metrics and not bounds:continue
        matrix=(U,0,0,0,U,0,1);f.reset(0x34,matrix,(1,U,U,0,0),origin,metrics,bounds)
        check(f'query-{origin}-{metrics}-{bounds}-keeps-stock',f.call(entry,MESSAGE,1,1)==1 and
              f.calls==[((CONTEXT,OPTIONS,origin,metrics,bounds),matrix)])
    for page,orientation in ((0,1),(5,1),(1,0),(1,3),(0xffffffff,2)):
        f.reset(0x34,matrix,(1,U,U,0,0))
        check(f'invalid-page{page}-orientation{orientation}-no-publication',f.call(entry,MESSAGE,page,orientation)==0 and not f.events)
    for fallback in (False,True):
        scaled=(U//2,0,0,0,U,0,1);f.reset(0x37,scaled,(2,U,U,0,0))
        f.u.mem_write(DESCRIPTOR,bytes(0xc8));f.word(DESCRIPTOR+0x94,CONTEXT)
        for off,v in ((8,160),(10,20),(0xac,0 if fallback else 160),(0xae,0 if fallback else 20),(0x64,480),(0x60,380)):
            f.u.mem_write(DESCRIPTOR+off,struct.pack('<H',v))
        f.u.mem_write(ORIGIN,struct.pack('<2i',20*U+U//2,160*U+U//4))
        check(f'actual-native-scale-and-fractional-origin-fallback{fallback}',f.call(entry,MESSAGE,1,2)==1 and
              [c[1] for c in f.calls]==[reference(scaled,(2,U,U,0,160*U))])
    f.reset(0x37,(U,0,0,0,U,0,1),(1,U,U,0,0))
    f.word(f.state,1);f.word(f.state+28,0xa1802000);f.word(f.state+32,0xa1803000)
    state=bytes(f.u.mem_read(f.state,36))
    check('busy-owner-keeps-descriptor-and-planner-context',f.call(entry,MESSAGE,1,1)==0 and
          bytes(f.u.mem_read(f.state,36))==state and not f.events)
    f.word(f.state,0);f.word(f.state+28,0);f.word(f.state+32,0)
    # Invalid axis matrix is stock for ordinary text but suppresses footer text.
    for footer in (False,True):
        invalid=(U,1,0,0,U,0,1);f.reset(0x34,invalid,(1,U,U,0,0))
        f.u.mem_write(DESCRIPTOR+0x64,struct.pack('<H',50 if footer else 480))
        f.u.mem_write(DESCRIPTOR+0x60,struct.pack('<H',26 if footer else 380))
        check(f'invalid-matrix-footer{footer}',f.call(entry,MESSAGE,1,1)==1 and
              len(f.calls)==(0 if footer else 1) and f.matrix()==invalid)
    result.update(menu_layout_cases=count,compiled_callback_descriptor_metrics_and_page_reflow_execute=True,
                  descriptor_processing_and_glyph_rendering_supplied=True,
                  native_descriptor_reflow_inline_symbols_background_suppression_or_pixels_proven=False)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    raw=a.stock_main.read_bytes();assert hashlib.sha256(raw).hexdigest()==STOCK_SHA
    source=ROOT/'z7-native-modules/examples/portrait_text_layout_probe.c'
    packet,metadata=build(source,zig=ZIG);again,other=build(source,zig=ZIG);assert packet==again and metadata==other
    result=audit(raw,packet,metadata)
    names=['tools/audit_z7_portrait_text_layout.py','tools/audit_z7_portrait_text.py','tools/audit_splash_image.py','tools/build_z7_module.py',
           'z7-native-modules/examples/portrait_text_layout_probe.c','z7-native-modules/sdk/module.h','z7-native-modules/sdk/module.ld']
    names += ['z7-native-modules/plugins/'+n+'.h' for n in ('portrait_text_layout','portrait_text','portrait_bands','portrait_page_message',
              'portrait_grid_message','portrait_grid','portrait_footer','portrait_geometry','portrait_draw')]
    result.update(probe_sha256=hashlib.sha256(packet).hexdigest(),probe_bytes=len(packet),image_bytes=metadata['image_bytes'],
                  bss_bytes=metadata['bss_bytes'],relocations=len(metadata['relocations']),reproducible_probe=True,
                  source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(packet)
    (out/'probe.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),layout_cases=result['menu_layout_cases'],probe_bytes=len(packet))))


if __name__=='__main__':main()
