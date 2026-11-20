"""Trace original-Z7 text rectangle/font selection before extending the overlay.

SPDX-License-Identifier: MIT. Executes the original text wrapper; object storage,
initialization and drawing services are supplied boundaries.
This does not establish EVF pixels, rotation transforms or installation safety.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2
from audit_splash_image import NativePNG, MEM, STACK, STOCK_SHA
from audit_z7_other_identity import OtherIdentityFixture
from audit_z7_status_identity import SNAPSHOT
from build_z7_module_host import ROOT


class LayoutFixture(OtherIdentityFixture):
    construct = False

    def hook(self, u, address, size, context):
        if self.construct and address == 0x103fcf0e:
            self.allocations.append(tuple(u.reg_read(r) for r in
                                          (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2)))
            self.ret(MEM + 0x40000)
            return
        if self.construct and address == 0x103faeba:
            self.lists.append((u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)))
            self.ret(1)
            return
        if address == 0x102f32ae:
            # The identity fixture normally replaces this wrapper with a sink.
            return NativePNG.hook(self, u, address, size, context)
        if address == 0x103fbc32:
            self.fonts.append(u.reg_read(UC_ARM_REG_R0))
            # This native query returns a small font attribute, not height.
            return NativePNG.hook(self, u, address, size, context)
        elif address in (0x10384d82, 0x103fb340, 0x103fb32e, 0x103fb344):
            self.ret(0)
        elif address == 0x103fbb5c:
            self.labels.append((u.reg_read(UC_ARM_REG_R1),
                                u.reg_read(UC_ARM_REG_R2)))
            self.ret(0)
        else:
            super().hook(u, address, size, context)


def audit(raw):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA:
        raise ValueError('Exact original-Z7 stock MAIN required')
    f = LayoutFixture(raw)
    checks, cases = [], []

    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good:
            raise AssertionError(name)

    # Scene >=2 clamps geometry to bank2; font column1 requires exactly scene2.
    # Orientation is varied separately: this wrapper does not apply transforms.
    rectangles = ((40, 194, 107, 218), (62, 292, 129, 316),
                  (284, 16, 360, 40))
    for scene in (0, 1, 2, 3, 255):
        for orientation in (0, 1, 2, 3):
            incoming, controls = f.prepare(50)
            source_controls = bytes(f.u.mem_read(controls, 3 * 48))
            f.fonts, f.labels = [], []
            f.u.mem_write(0xa18237c6, bytes([scene]))
            f.u.mem_write(SNAPSHOT + 0x338, struct.pack('<H', orientation))
            snapshot = bytes(f.u.mem_read(SNAPSHOT, len(incoming)))
            f.u.mem_write(MEM + 0x30000, b'24.5mm\0')
            # Caller-selected native paint argument, not a Z7II palette binding.
            paint = 0x2f6 if scene == 2 else 1
            f.u.mem_write(STACK, struct.pack('<I', paint))
            f.call(0x102f32ae, 19, 50, 2, MEM + 0x30000)
            obj = MEM + 0x20200
            rectangle = struct.unpack('<4h', f.u.mem_read(obj + 16, 8))
            font = 109 if scene == 2 else 100
            prefix = f'scene{scene}-orientation{orientation}'
            check(prefix + '-original-rectangle', rectangle == rectangles[min(scene, 2)])
            check(prefix + '-original-font', f.fonts == [font] and f.labels == [(60, font)])
            check(prefix + '-original-font-query',
                  int.from_bytes(f.u.mem_read(obj + 0x18, 4), 'little') == 1)
            check(prefix + '-caller-paint-retained',
                  int.from_bytes(f.u.mem_read(obj + 56, 4), 'little') == paint)
            check(prefix + '-native-style-values',
                  struct.unpack('<4I', f.u.mem_read(obj + 0x34, 16)) ==
                  (0x1000, paint, 0x1000, 0x2eb))
            check(prefix + '-source-controls-unchanged',
                  bytes(f.u.mem_read(controls, 3 * 48)) == source_controls)
            check(prefix + '-snapshot-unchanged',
                  bytes(f.u.mem_read(SNAPSHOT, len(incoming))) == snapshot)
            cases.append(dict(scene=scene, orientation=orientation,
                              rectangle=rectangle, font=font, paint=paint,
                              native_font_query_result=1,
                              font_table_height=f.u.mem_read(0xa182158c + font * 16 + 1, 1)[0]))
    constructors = []
    for scene in (0, 1, 2, 3, 255):
        incoming, controls = f.prepare(50)
        before = bytearray(f.u.mem_read(controls, 3 * 48))
        obj, counter, pool, parent = MEM + 0x40000, MEM + 0x50000, MEM + 0x51000, MEM + 0x52000
        f.u.mem_write(obj, bytes(284))
        f.u.mem_write(counter, struct.pack('<I', 71))
        f.u.mem_write(0xa201e388 + 0x24, struct.pack('<I', pool))
        f.u.mem_write(0xa201e388 + 0xc, struct.pack('<I', parent))
        f.u.mem_write(0xa18237c6, bytes([scene]))
        f.allocations, f.lists, f.construct = [], [], True
        f.call(0x102f17b8, 50, 2, counter)
        f.construct = False
        prefix = f'constructor-scene{scene}'
        check(prefix + '-native-allocation-arguments', f.allocations == [(pool, 0, 71)])
        check(prefix + '-slot-counter-increments',
              int.from_bytes(f.u.mem_read(counter, 4), 'little') == 72)
        check(prefix + '-native-rectangle',
              struct.unpack('<4h', f.u.mem_read(obj + 16, 8)) == rectangles[min(scene, 2)])
        check(prefix + '-same-object-in-three-native-lists',
              f.lists == [(a, obj) for a in (0xa201e3b4, 0xa201e47c, 0xa201e544)])
        check(prefix + '-native-parent-binding',
              int.from_bytes(f.u.mem_read(obj + 0x48, 4), 'little') == parent)
        struct.pack_into('<I', before, 2 * 48 + 36, obj)
        check(prefix + '-only-source-object-pointer-updated',
              bytes(f.u.mem_read(controls, 3 * 48)) == before)
        check(prefix + '-snapshot-unchanged', bytes(f.u.mem_read(SNAPSHOT, len(incoming))) == incoming)
        constructors.append(dict(scene=scene, lists=[hex(a) for a, _ in f.lists],
                                 rectangle=rectangles[min(scene, 2)]))
    return dict(passed=True, checks=checks, cases=cases,
                constructors=constructors,
                stock_main_sha256=STOCK_SHA, native_text_wrapper='0x102F32AE',
                logical_font=19, font_table='0xA18237E8',
                native_geometry_copy='0x102F333E',
                corrected_function_roles={'0x10369214': 'control dirty-state propagation',
                                          '0x102F27A8': 'native permission/visibility selection'},
                supplied_boundaries=['Owned object storage and incoming control/snapshot state',
                                     'Text initialization, binding, visibility and draw sinks',
                                     'Caller paint argument', 'Constructor allocation and list insertion sinks; pool/parent context'],
                actual_pixels=False, rotation_transform_verified=False,
                evf_overlay_implemented=False, camera_access=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock-main', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists():
        parser.error('Choose a new private output')
    result = audit(args.stock_main.read_bytes())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']), cases=len(result['cases']))))


if __name__ == '__main__':
    main()
