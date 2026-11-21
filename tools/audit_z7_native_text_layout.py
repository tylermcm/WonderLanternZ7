"""Original text descriptor/glyph execution through settings-page placement.

SPDX-License-Identifier: MIT. Native context/options, descriptors34/37/38,
glyph layout/contours, provider restore and destruction execute. Font face,
shaping, metrics, allocation and final GPU/emission remain supplied.
"""
import argparse
import gc
import hashlib
import itertools
import json
from pathlib import Path
from audit_z7_native_text_descriptor import DescriptorFixture,IDENTITY
from audit_z7_portrait_text import CODE,CONTEXT,DESCRIPTOR,MESSAGE,PAYLOAD,TABLE,UNIT,reference
from audit_splash_image import STOCK_SHA
from build_z7_module import build
from build_z7_module_host import ROOT,ZIG


def audit(raw,packet,metadata):
    checks=[];pairs=0
    def check(name,good):checks.append(dict(name=name,passed=bool(good)));assert good,name
    for command,orientation,text,alignment in itertools.product((0x34,0x37,0x38),(1,2),('A','ABC'),(0,2)):
        transform=(orientation,UNIT,UNIT,0,0)
        f=DescriptorFixture(raw,packet,metadata);f.prepare_descriptor(command,transform,text,alignment)
        f.baseline=True;f.call(0x10372390,MESSAGE)
        baseline=f.renders[:];metrics=bytes(f.u.mem_read(DESCRIPTOR+0xa8,0x20))
        check(f'pair{pairs}-baseline-emits-glyphs',len(f.bitmap_matrices if command==0x34 else f.outlines)==len(text) and
              any(r['origin'] and not r['metrics'] and not r['bounds'] for r in baseline))
        f.destroy();check(f'pair{pairs}-baseline-releases-buffers',not f.live);del f;gc.collect()
        f=DescriptorFixture(raw,packet,metadata);f.prepare_descriptor(command,transform,text,alignment)
        expected=[]
        for render in baseline:
            item=dict(render)
            if render['origin'] is not None and not render['metrics'] and not render['bounds']:
                # Settings has a fixed235-pixel vertical shift and2/3 horizontal
                # scaling. Native layout supplies fractional glyph origins; the
                # pinned placement aligns the floored label x to the pixel edge.
                assert render['matrix']==IDENTITY
                x=render['origin'][0]//UNIT
                t=(orientation,43691,UNIT,(x*43691//UNIT)*UNIT-x*43691,235*UNIT)
                item['matrix']=reference(IDENTITY,t)
            expected.append(item)
        message=bytes(f.u.mem_read(MESSAGE,28));payload=bytes(f.u.mem_read(PAYLOAD,12))
        got=f.call(CODE+metadata['symbols']['z7_portrait_text_page_probe'],MESSAGE,3,orientation)
        check(f'pair{pairs}-native-settings-query-draw-and-cleanup',got==1 and f.renders==expected and
              len(f.bitmap_matrices if command==0x34 else f.outlines)==len(text) and
              bytes(f.u.mem_read(DESCRIPTOR+0xa8,0x20))==metrics and f.matrix()==IDENTITY and
              f.read(CONTEXT+0x45b4)==TABLE and bytes(f.u.mem_read(f.state+28,8))==bytes(8) and
              bytes(f.u.mem_read(PAYLOAD,12))==payload and bytes(f.u.mem_read(MESSAGE,28))==message[:24]+bytes(4) and
              f.events[-3:]==[('defer',0x42010063,0),('ack',0x42010063,0),'event'])
        f.destroy();check(f'pair{pairs}-rotated-releases-buffers',not f.live);del f;gc.collect();pairs+=1
    return dict(passed=True,checks=checks,paired_native_settings_cases=pairs,
                original_descriptors_glyph_layout_settings_placement_and_destruction_execute=True,
                font_face_cache_metrics_shaping_allocator_gpu_and_final_emission_supplied=True,
                native_font_files_inline_symbols_other_page_native_descriptors_or_pixels_proven=False,camera_card_access=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    raw=a.stock_main.read_bytes();assert hashlib.sha256(raw).hexdigest()==STOCK_SHA
    source=ROOT/'z7-native-modules/examples/portrait_text_layout_probe.c'
    packet,metadata=build(source,zig=ZIG);again,other=build(source,zig=ZIG);assert packet==again and metadata==other
    result=audit(raw,packet,metadata)
    names=['tools/audit_z7_native_text_layout.py','tools/audit_z7_native_text_descriptor.py','tools/audit_z7_native_glyph.py',
           'tools/audit_z7_portrait_text.py','tools/audit_splash_image.py','tools/build_z7_module.py',
           'z7-native-modules/examples/portrait_text_layout_probe.c','z7-native-modules/sdk/module.h','z7-native-modules/sdk/module.ld']
    names += ['z7-native-modules/plugins/'+n+'.h' for n in ('portrait_text_layout','portrait_text','portrait_bands','portrait_page_message',
              'portrait_grid_message','portrait_grid','portrait_footer','portrait_geometry','portrait_draw')]
    result.update(probe_sha256=hashlib.sha256(packet).hexdigest(),reproducible_probe=True,
                  source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(packet)
    (out/'probe.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),native_pairs=result['paired_native_settings_cases'])))


if __name__=='__main__':main()
