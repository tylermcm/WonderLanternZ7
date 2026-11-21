"""Loaded portrait graphics latch and native central navigation integration.

SPDX-License-Identifier: MIT. Loader, SDKs, resident bridges, native page/task
getters, graphics entry latch, native focus/item reads and key handler prefixes
execute. Page/scene/output/sensor/task state, native selector/callbacks and render
services supplied. No full input task exclusion, touch, real selection or pixels.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1
from audit_z7_portrait_grid_host import GridHostFixture
from audit_z7_portrait_input import MODE,COUNT,INDEX,FOCUS,UI,ITEMS,cycle
from build_z7_module import build
from build_z7_module_host import ROOT,STATE,ZIG

class PortraitNavigationFixture(GridHostFixture):
    def __init__(self,raw,report,packet,metadata):
        super().__init__(raw,report,packet,metadata)
        self.functions=struct.unpack('<34I',self.u.mem_read(0x11eca198,136))[1::2]
        self.nav_stock=[];self.selected=[];self.item_reads=[];self.nav_mutation=None
    def nav_var(self,name):return self.words()[12]+self.metadata['symbols']['z7_portrait_nav_'+name]
    def hook(self,u,address,size,context):
        if address in {v&~1 for v in getattr(self,'functions',())}:
            direction=u.reg_read(UC_ARM_REG_R0);self.nav_stock.append(direction);self.ret(direction^0x5a5a0000);return
        if address==0x103dde4a:self.selected.append(u.reg_read(UC_ARM_REG_R0));self.ret(0);return
        if address==0x103dde3a:self.item_reads.append(u.reg_read(UC_ARM_REG_R1))
        if address==0x10385b78 and self.nav_mutation:
            p,data=self.nav_mutation;self.u.mem_write(p,data);self.nav_mutation=None
        super().hook(u,address,size,context)
    def nav_setup(self,orientation=1,current=0,disabled=0,prime=True):
        self.setup(orientation,prime);self.u.mem_write(0xa18298b8,b'\0\0');self.u.mem_write(MODE,b'\0')
        self.write(COUNT,12);self.write(INDEX,0x12345678);self.u.mem_write(UI,b'\0');self.write(FOCUS+4,current)
        for i in range(12):self.u.mem_write(ITEMS+8*i,struct.pack('<2I',bool(disabled&(1<<i)),0x9000+i))
        self.nav_stock.clear();self.selected.clear();self.item_reads.clear();self.nav_mutation=None
    def navigate(self,direction,entry=0x104389b1):
        self.nav_stock.clear();self.selected.clear();self.item_reads.clear()
        before=self.read(self.nav_var('handled'));result=self.call(entry,direction)
        return result,self.read(self.nav_var('handled'))-before


def audit(raw,host,packet,metadata):
    f=PortraitNavigationFixture(raw,host,packet,metadata);checks=[];grid_cases=0
    def check(name,good):checks.append(dict(name=name,passed=bool(good)));assert good,name
    loaded=f.call(host['symbols']['z7_module_load_once'],STATE);f.setword(40,loaded)
    check('loaded-module-stages-graphics-and-navigation',loaded==8 and f.read(STATE+364)==1 and f.read(STATE+388)==1)
    f.call(host['symbols']['z7_module_worker_tick'])
    for orientation in (1,2):
        for current in range(12):
            for direction in range(4):
                path=cycle(current,direction,orientation)
                for disabled in (0,1<<path[0],0xfff):
                    f.nav_setup(orientation,current,disabled)
                    target=next((p for p in path if p==current or not disabled&(1<<p)),current)
                    result,handled=f.navigate(direction)
                    check(f'loaded-grid{grid_cases}-uses-real-graphics-latch-and-native-item-selection',result==0 and handled==1 and
                          f.selected==[target] and not f.nav_stock and f.read(INDEX)==target and
                          f.read(f.variable('layout'))==orientation and f.read(STATE+392)==0)
                    grid_cases+=1
        for mode in range(17):
            for direction in range(4):
                f.nav_setup(orientation);f.u.mem_write(MODE,bytes([mode]));f.u.mem_write(0xa18298b8,b'\1\0')
                mapped=({1:(3,2,0,1),2:(2,3,1,0)}[orientation])[direction]
                result,handled=f.navigate(direction)
                check(f'loaded-settings-mode{mode}-orientation{orientation}-direction{direction}',handled==1 and result==(mapped^0x5a5a0000) and
                      f.nav_stock==[mapped] and not f.selected)
    for label,location,data in (
        ('native-menu',0xa182ed2c,b'\1'),('native-play',0xa183de04,b'\1'),('foreign-app',0xa1829af4,b'\0'),
        ('foreign-scene',0xa201d4d0,b'\1'),('nonlcd-output',0xa1821394,struct.pack('<I',2)),
        ('unknown-layout',None,0),('landscape-layout',None,3),('dial',0xa18298b8,b'\2\0')):
        f.nav_setup()
        if location is None:f.write(f.variable('layout'),data)
        else:f.u.mem_write(location,data)
        result,handled=f.navigate(0)
        check('loaded-'+label+'-delegates-native-direction',handled==0 and result==0x5a5a0000 and f.nav_stock==[0] and not f.selected)
    f.nav_setup(prime=False);result,handled=f.navigate(0)
    check('input-before-graphics-entry-latch-stays-native',handled==0 and f.read(f.variable('layout'))==0 and f.nav_stock==[0])
    for location,data in ((0xa201d4d0,b'\1'),(0xa18298b8,b'\2\0'),(0xa1821394,struct.pack('<I',2))):
        f.nav_setup();f.nav_mutation=(location,data);result,handled=f.navigate(0)
        check(f'native-page-getter-change-{location}-rejects-mapping',handled==0 and f.nav_stock==[0] and not f.selected)
    for direction,entry in ((0,0x103877c1),(1,0x103877e9),(2,0x10387781),(3,0x10387671)):
        f.nav_setup(2);result,handled=f.navigate(0,entry)
        check(f'original-imenu-key-handler{entry}-reaches-resident-portrait-navigation',handled==1 and
              f.selected==[cycle(0,direction,2)[0]] and not f.nav_stock)
    return dict(passed=True,checks=checks,loaded_grid_navigation_cases=grid_cases,
                loader_sdk_graphics_latch_native_page_focus_item_and_key_handler_integration_execute=True,
                native_selector_callbacks_rendering_and_scene_page_output_sensor_task_state_supplied=True,
                full_task_pending_screen_fence_touch_native_selection_completion_or_pixels_proven=False,camera_card_access=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('host','report','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    host=json.loads(a.report.read_text());raw=a.host.read_bytes();assert hashlib.sha256(raw).hexdigest()==host['main_payload_sha256'] and host['api_bytes']==88
    source=ROOT/'z7-native-modules/examples/portrait_navigation_host_probe.c';packet,metadata=build(source,zig=ZIG);again,other=build(source,zig=ZIG)
    assert packet==again and metadata==other
    result=audit(raw,host,packet,metadata)
    names=['tools/audit_z7_portrait_navigation_host.py','tools/audit_z7_portrait_grid_host.py','tools/audit_z7_portrait_input.py','tools/audit_z7_module_host.py',
           'tools/audit_z7_information_native.py','tools/audit_splash_image.py','tools/build_z7_module.py','tools/build_z7_module_host.py',
           'tools/audit_z7_portrait_draw.py','tools/audit_z7_portrait_grid_message.py','tools/audit_z7_portrait_page_message.py',
           'z7-native-modules/examples/portrait_navigation_host_probe.c','z7-native-modules/examples/portrait_grid_host_probe.c']
    names+=['z7-native-modules/plugins/'+n+'.h' for n in ('portrait_input','portrait_navigation','portrait_layout','portrait_bands','portrait_page','portrait_takeover',
             'portrait_target','orientation_sample','portrait_page_message','portrait_grid_message','portrait_geometry','portrait_grid','portrait_footer','portrait_draw',
             'portrait_text_layout','portrait_text','portrait_symbols','portrait_symbol_bitmap')]
    result.update(host_sha256=host['main_payload_sha256'],probe_sha256=hashlib.sha256(packet).hexdigest(),probe_bytes=len(packet),
                  reproducible_probe=True,source_sha256={**host['source_files'],**{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names}})
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(packet)
    (out/'probe.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),grid_cases=result['loaded_grid_navigation_cases'],probe_bytes=len(packet))))


if __name__=='__main__':main()
