"""Execute original-Z7 mode updaters and identify their native icon resources.

SPDX-License-Identifier: MIT. Snapshot/control state, property138D and drawing
sinks are supplied. Original updater instructions select the native image IDs.
Decoded firmware icons stay private; this does not establish actual scanout.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct

from PIL import Image, ImageDraw
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP
from audit_splash_image import NativePNG, BASE, STOCK_SHA, TABLE
from build_z7_module_host import ROOT

SNAPSHOT = 0xa201d4d0
# IDs independently selected by the original updaters and visually inspected.
GROUPS = (
    ('shooting', 5, 0x102f346e, 8, (1341, 1339, 1347, 1345, 2301, 1341)),
    ('focus', 2, 0x102f31a6, 0x1f7, (4533, 3050, 3046, 3050, 3048)),
    ('release', 51, 0x102f6d00, 0x5b, (4589, 4717, 4718, 4719, 4720, 4721, 5221, 5223, 3719, 3720, 3721, 3722)),
    # Negative controls: Z7II release/focus IDs identify different Z7 content.
    ('af_area_negative_control', 3, 0x102f3220, 0x1f8, (4218, 4275, 4277, 4281, 4279, 4218, 4273, 4218)),
    ('active_d_lighting_negative_control', 6, 0x102f354e, 0x1f4, (2968, 2964, 2966, 2958, 3698, 2956, 2968)),
)


class StatusFixture(NativePNG):
    def __init__(self, raw):
        super().__init__(raw)
        self.u.mem_map(0xa2010000, 0x20000)
        self.events = []
        self.property138d = 0

    def hook(self, u, address, size, context):
        if address in (0x102f309a, 0x102f2f80):
            args = [u.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)]
            self.events.append(dict(function=hex(address), widget=args[0], control=args[1],
                resource=args[2] if address == 0x102f2f80 else args[3],
                alternate_resource=int.from_bytes(u.mem_read(u.reg_read(UC_ARM_REG_SP), 4), 'little') if address == 0x102f309a else None))
            self.ret(0)
        elif address == 0x102f2f1e: self.ret(1)
        elif address == 0x104065a4:
            if u.reg_read(UC_ARM_REG_R0) != 0x138d: raise AssertionError('Unexpected property')
            self.ret(self.property138d)
        elif address in (0x102f3006, 0x102f2b8c): self.ret(0)
        else: super().hook(u, address, size, context)


def audit(raw, output):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA: raise ValueError('Exact original-Z7 stock MAIN required')
    f = StatusFixture(raw); cases = []; icons = []
    for name, widget, updater, offset, expected in GROUPS:
        actual_updater = int.from_bytes(f.u.mem_read(0x1064c67c + widget * 4, 4), 'little')
        if actual_updater != updater | 1: raise AssertionError('Updater table binding')
        for value, image_id in enumerate(expected):
            snapshot = bytearray(0x33c); snapshot[offset] = value
            f.u.mem_write(SNAPSHOT, bytes(snapshot)); f.events = []; f.call(updater)
            matches = [e for e in f.events if e['widget'] == widget and e['control'] == 1]
            if len(matches) != 1 or matches[0]['resource'] != image_id: raise AssertionError((name, value, f.events))
            if bytes(f.u.mem_read(SNAPSHOT, len(snapshot))) != snapshot: raise AssertionError('Updater altered supplied snapshot')
            _, length, _, _, pointer = struct.unpack_from('<5I', raw, TABLE - BASE + image_id * 20)
            data = raw[pointer - BASE:pointer - BASE + length]
            image = Image.open(io.BytesIO(data)).convert('RGBA'); icons.append((name, value, image_id, image))
            cases.append(dict(group=name, widget=widget, updater=hex(updater), snapshot_offset=hex(offset), value=value,
                image_id=image_id, native_image_sha256=hashlib.sha256(data).hexdigest(), dimensions=list(image.size), passed=True))
    sheet = Image.new('RGB', (800, ((len(icons) + 7) // 8) * 100), '#666666'); draw = ImageDraw.Draw(sheet)
    for index, (name, value, image_id, image) in enumerate(icons):
        x, y = index % 8 * 100, index // 8 * 100
        draw.text((x, y), f'{name[:8]} {value}', fill='white'); draw.text((x, y + 12), str(image_id), fill='white')
        sheet.paste(image, (x, y + 28), image)
    sheet.save(output / 'native-status-icons.png')
    return dict(passed=True, cases=cases, stock_main_sha256=STOCK_SHA,
        identified_widgets=dict(shooting=5, release=51, focus=2),
        negative_controls=dict(af_area=3, active_d_lighting=6),
        supplied_boundaries=['Snapshot/control data', 'Property138D', 'Dirty predicate and drawing sinks'],
        native_updaters_execute=True, actual_pixels=False, camera_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(); output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists(): p.error('Choose a new private output directory')
    output.mkdir(parents=True)
    result = audit(args.stock_main.read_bytes(), output)
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, cases=len(result['cases']))))


if __name__ == '__main__': main()
