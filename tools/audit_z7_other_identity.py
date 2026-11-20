"""Original-Z7 ordinary-status identities and shared native warning selectors.

SPDX-License-Identifier: MIT. Original updaters/formatters select icons/text;
drawing, property138D/1D01 and incoming controls/snapshots are supplied. Native
preparation prefixes identify format selectors; full preparation is not claimed.
Firmware icons, strings and generated contact sheets stay private.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct

from PIL import Image, ImageDraw
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_LR
from audit_splash_image import BASE, MEM, STACK, STOP, STOCK_SHA, TABLE
from audit_z7_status_identity import StatusFixture, SNAPSHOT
from build_z7_module_host import ROOT

# widget, descriptor, updater, ordinary family, shared format, image control/id.
OTHER_BINDINGS = (
    (3,0xa1823ab4,0x102f3221,'af_area_status',255,1,4218),
    (6,0xa1823d84,0x102f354f,'dynamic_lighting',255,1,2968),
    (7,0xa1823e74,0x102f35e3,'exposure_meter',4,1,4690),
    (8,0xa1823f04,0x102f3617,'exposure_lock',255,1,4271),
    (9,0xa1823f94,0x102f3637,'flash_value_lock',255,1,4299),
    (13,0xa1824414,0x102f3abd,'flash_adjustment',255,1,4713),
    (14,0xa18244d4,0x102f3add,'exposure_adjustment',255,1,4763),
    (16,0xa1824954,0x102f3f8b,'remaining_capacity',2,None,None),
    (17,0xa18249e4,0x102f3fdf,'flash_mode',3,1,4544),
    (26,0xa1826534,0x102f4f9d,'picture_profile',255,1,4035),
    (27,0xa18265c4,0x102f501b,'image_area',255,1,4672),
    (34,0xa1827614,0x102f5685,'microphone_wind_filter',255,1,1321),
    (38,0xa182796c,0x102f66cd,'multi_exposure',255,1,5354),
    (41,0xa1827b1c,0x102f6817,'touch_release',255,0,3712),
    (44,0xa1827f0c,0x102f5911,'image_file_quality',255,1,3750),
    (46,0xa18280ec,0x102f6a7f,'quiet_shutter',255,1,4356),
    (50,0xa182844c,0x102f6bf7,'stabilization',255,1,4645),
    (53,0xa18286bc,0x102f6d75,'flicker_status',255,1,4557),
)
READOUT_WIDGETS = (10,11,15,5,51,2) + tuple(v[0] for v in OTHER_BINDINGS)
READOUT_FORMATS = (0,1,5,255,255,255) + tuple(v[4] for v in OTHER_BINDINGS)


class OtherIdentityFixture(StatusFixture):
    observe_prefix = False
    def hook(self, u, address, size, context):
        if self.observe_prefix and address == 0x1037071a:
            self.prefix_argument = u.reg_read(UC_ARM_REG_R0); u.emu_stop()
        elif address == 0x104065a4:
            key = u.reg_read(UC_ARM_REG_R0)
            if key not in (0x138d, 0x1d01): raise AssertionError('Unexpected property boundary')
            self.ret(0)
        elif address == 0x102f32ae:
            font, widget, control, pointer = [u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
            self.events.append(dict(function=hex(address),font=font,widget=widget,control=control,
                text=bytes(u.mem_read(pointer,80)).split(b'\0')[0].decode('ascii',errors='replace')))
            self.ret(0)
        elif address in (0x103faec6,0x103faee0,0x103fac5a): self.ret(0)
        else: super().hook(u,address,size,context)

    def prepare(self, widget):
        descriptor = int.from_bytes(self.u.mem_read(0x1064d610 + widget*4,4),'little')
        controls = int.from_bytes(self.u.mem_read(descriptor+44,4),'little')
        for row in range(self.u.mem_read(descriptor+40,1)[0]):
            self.u.mem_write(controls+row*48,bytes((1,int(row<2 or (widget==16 and row in (6,7))),0))+bytes(7))
            self.u.mem_write(controls+row*48+36,struct.pack('<I',MEM+0x20000+row*256))
        incoming = bytearray(0x33c)
        if widget == 16:
            for offset,value in ((0x1e0,1),(0x1cc,1),(0x1d8,17)): struct.pack_into('<I',incoming,offset,value)
        if widget == 44: incoming[0x185] = 3
        self.u.mem_write(SNAPSHOT,bytes(incoming)); self.u.mem_write(0xa18237b8,bytes(7)); self.events=[]
        return bytes(incoming), controls


def audit(raw, output):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA: raise ValueError('Exact stock MAIN required')
    f=OtherIdentityFixture(raw); checks=[]; cases=[]; icons=[]
    def check(name,good):
        checks.append(dict(name=name,passed=bool(good)))
        if not good: raise AssertionError(name)
    for widget,descriptor,updater,name,fmt,control,image_id in OTHER_BINDINGS:
        check(name+'-original-descriptor-and-updater-bindings',
            int.from_bytes(f.u.mem_read(0x1064d610+widget*4,4),'little')==descriptor and
            int.from_bytes(f.u.mem_read(0x1064c67c+widget*4,4),'little')==updater)
        incoming,_=f.prepare(widget); f.call(updater)
        if image_id is None: match=any(e.get('text')=='17' and e['control']==6 for e in f.events)
        else: match=any(e.get('resource')==image_id and e['control']==control for e in f.events)
        check(name+'-native-normal-formatter-or-image',match)
        check(name+'-updater-preserves-supplied-current-snapshot',bytes(f.u.mem_read(SNAPSHOT,0x33c))==incoming)
        cases.append(dict(widget=widget,family=name,format_selector=fmt,events=f.events,passed=True))
        for e in f.events:
            resource=e.get('resource',65535)
            if not 0<resource<20000: continue
            _,length,_,_,pointer=struct.unpack_from('<5I',raw,TABLE-BASE+resource*20)
            data=raw[pointer-BASE:pointer-BASE+length]
            if data.startswith(b'\x89PNG'): icons.append((widget,resource,Image.open(io.BytesIO(data)).convert('RGBA')))
    for fmt,text in ((7,'-E-'),(26,'Err')):
        _,controls=f.prepare(16); f.u.mem_write(controls+8*48+1,b'\1')
        f.u.mem_write(0xa18237b8+2,bytes([fmt])); f.call(0x102f3f8a)
        check('capacity-shares-native-warning-format-'+str(fmt),any(e.get('text')==text for e in f.events))
        cases.append(dict(widget=16,warning_format=fmt,events=f.events,passed=True))
    # A special child of the ordinary profile widget must not be mistaken for
    # its normal content, as happened in the earlier all-visible atlas.
    _,controls=f.prepare(26); f.u.mem_write(controls+3*48+1,b'\1'); f.call(0x102f4f9c)
    check('picture-profile-has-distinct-native-log-child',any(e.get('resource')==4734 and e['control']==3 for e in f.events))
    for widget,preparation,index in ((7,0x10369d30,4),(16,0x10369f84,2),(17,0x10369e80,3)):
        f.observe_prefix=True; f.prefix_argument=None
        f.u.reg_write(UC_ARM_REG_SP,STACK); f.u.reg_write(UC_ARM_REG_LR,STOP|1)
        f.u.emu_start(preparation|1,STOP,count=10000,timeout=1000000); f.observe_prefix=False
        check('native-preparation-prefix-selects-format-'+str(widget),f.prefix_argument==index)
        for value in (0,1,7,26,255):
            f.u.mem_write(0xa18237b8+index,bytes([value]))
            check(f'widget{widget}-original-format-query-{value}',f.call(0x1037071a,index)==int(value==0))
    sheet=Image.new('RGB',(1000,((len(icons)+9)//10)*100),'#666666');draw=ImageDraw.Draw(sheet)
    for n,(widget,resource,picture) in enumerate(icons):
        x,y=n%10*100,n//10*100;draw.text((x,y),f'w{widget} id{resource}',fill='white');sheet.paste(picture,(x,y+20),picture)
    sheet.save(output/'native-other-icons.png')
    return dict(passed=True,checks=checks,cases=cases,stock_main_sha256=STOCK_SHA,
        normal_updaters_execute=True,native_preparation_prefixes_only=True,
        manual_reference='https://onlinemanual.nikonimglib.com/z7_z6/en/14_technical_notes_01.html',
        supplied_boundaries=['Incoming snapshots/control visibility and owned object storage','Properties138D/1D01 return0','Drawing sinks'],
        actual_pixels=False,camera_access=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();output=args.output.resolve()
    if not output.is_relative_to(ROOT/'.private') or output.exists():p.error('Choose a new private output directory')
    output.mkdir(parents=True);result=audit(args.stock_main.read_bytes(),output)
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),normal_widgets=len(OTHER_BINDINGS))))


if __name__=='__main__':main()
