"""Identify original-Z7 native mm text without borrowing Z7II widget bindings.

SPDX-License-Identifier: MIT. Original VR updater/formatter and preparation
prefix execute with supplied snapshots, control visibility and drawing sinks.
This identifies an existing shared text field, not a live-lens focal feature.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC
from audit_splash_image import STOCK_SHA, MEM, STACK, STOP
from audit_z7_other_identity import OtherIdentityFixture
from audit_z7_status_identity import SNAPSHOT
from build_z7_module_host import ROOT


class FocalFixture(OtherIdentityFixture):
    prefix = False
    prefix_reached = False
    def hook(self, u, address, size, context):
        if self.prefix and address == 0x1036f35c:
            self.prefix_reached = True
            u.emu_stop()
        else:
            super().hook(u, address, size, context)


def audit(raw):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA:
        raise ValueError('Exact original-Z7 stock MAIN required')
    f = FocalFixture(raw)
    checks, formats, gates = [], [], []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good:
            raise AssertionError(name)
    check('widget50-original-updater-binding', int.from_bytes(f.u.mem_read(0x1064c67c + 50 * 4, 4), 'little') == 0x102f6bf7)
    check('widget50-original-preparation-binding', int.from_bytes(f.u.mem_read(0x1064db98 + 50 * 4, 4), 'little') == 0x1036f2b1)
    descriptor = int.from_bytes(f.u.mem_read(0x1064d610 + 50 * 4, 4), 'little')
    check('widget50-shares-three-controls', f.u.mem_read(descriptor + 40, 1)[0] == 3)
    for output in (0, 2):
        for value, expected in ((0, '6mm'), (59, '6mm'), (60, '6mm'), (240, '24mm'),
                                (245, '24mm'), (39999, '3999mm'), (40000, '4000mm'),
                                (40001, '4000mm'), (0xffffffff, '4000mm')):
            _, controls = f.prepare(50)
            f.u.mem_write(0xa18237c6, bytes([output]))
            incoming = bytearray(0x33c)
            incoming[0xac] = 1
            struct.pack_into('<I', incoming, 0xb0, value)
            f.u.mem_write(SNAPSHOT, bytes(incoming))
            f.u.mem_write(controls + 2 * 48 + 1, b'\1')
            f.call(0x102f6bf6)
            text = [e for e in f.events if e.get('text') is not None]
            check(f'output{output}-value{value}-original-whole-mm-format', len(text) == 1 and text[0]['text'] == expected and
                  text[0]['widget'] == 50 and text[0]['control'] == 2 and text[0]['font'] == 19)
            check(f'output{output}-value{value}-current-snapshot-unchanged', bytes(f.u.mem_read(SNAPSHOT, len(incoming))) == incoming)
            formats.append(dict(output=output, snapshot_value_tenths=value, native_text=expected))
    f.u.mem_write(0xa18237c6, b'\0')
    for vr in (0, 1, 2, 3):
        for value in (0, 245):
            for context in (0, 1, 2, 3):
                _, controls = f.prepare(50)
                incoming = bytearray(0x33c)
                incoming[0xac], incoming[0x135] = vr, context
                struct.pack_into('<I', incoming, 0xb0, value)
                f.u.mem_write(SNAPSHOT, bytes(incoming))
                f.u.mem_write(0xa201d80c, bytes(v ^ 255 for v in incoming))
                f.prefix, f.prefix_reached = True, False
                f.u.reg_write(UC_ARM_REG_SP, STACK)
                f.u.reg_write(UC_ARM_REG_LR, STOP | 1)
                f.u.emu_start(0x1036f2b1, STOP, timeout=1000000, count=10000)
                f.prefix = False
                check(f'vr{vr}-value{value}-context{context}-prefix-boundary', f.prefix_reached and f.u.reg_read(UC_ARM_REG_PC) == 0x1036f35c)
                visible = f.u.mem_read(controls + 2 * 48 + 1, 1)[0]
                expected = bool(vr and value and context in (0, 2))
                check(f'vr{vr}-value{value}-context{context}-native-text-gate', visible == expected)
                gates.append(dict(vr_field=vr, focal_field=value, context135=context, prefix_text_visible=bool(visible)))
    # The original collector maps these fields through its own key array.
    # No equivalence to the pinned Z7II live-lens getter namespace is assumed.
    key_table = 0xa1828e88
    check('collector-vr-key-at-source-offset-e4', int.from_bytes(f.u.mem_read(key_table + 0xe4, 4), 'little') == 0x153d)
    check('collector-mm-key-at-source-offset-e8', int.from_bytes(f.u.mem_read(key_table + 0xe8, 4), 'little') == 0x1548)
    check('raw-original-key2014-is-not-admitted', f.call(0x10070204, 0x2014, MEM) == 0)
    return dict(passed=True, checks=checks, formatting_cases=formats, preparation_prefix_cases=gates,
        native_widget=50, shared_with='VR icons in controls0/1; mm text in control2', native_formatter='0x101709A8',
        source_snapshot_fields=dict(vr='0xac', focal='0xb0', context='0x135'),
        source_collector_fields=dict(vr_key='0x153d', mm_key='0x1548'),
        preparation_scope='Prefix1036F2B0 stops before native context/layout services at1036F35C',
        fractional_mm_supported_by_existing_formatter=False, zero_hides_via_preparation_before_clamping=True,
        raw_key2014_result_does_not_identify_the_z7ii_getter_namespace=True,
        live_lens_source_identified=False, focal_feature_implemented=False, actual_pixels=False,
        supplied_boundaries=['Incoming snapshots and controls', 'Dirty predicate', 'Drawing sinks and owned object storage'], camera_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists():
        p.error('Choose a new private output')
    result = audit(args.stock_main.read_bytes())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']), formatting_cases=len(result['formatting_cases']),
        preparation_prefix_cases=len(result['preparation_prefix_cases']), live_lens_source_identified=False)))


if __name__ == '__main__':
    main()
