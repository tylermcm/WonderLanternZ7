"""Execute original source-tag routing and RAM-backed DISP output selection.

SPDX-License-Identifier: MIT. Source lists/receiver storage/output-kind/property
mode are supplied incoming state. Native tag selection, comparisons, source
setters, output-kind getter and DISP property-selector instructions execute.
No pixel/hardware output, source producer or cross-task snapshot is established.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0
from audit_splash_image import BASE, MEM, STOCK_SHA, NativePNG
from build_z7_module_host import ROOT

SOURCE_SELECT, DISP_SELECT, OUTPUT_KIND = 0x103484dc, 0x103673ac, 0x103fef80
REAR_TAG, EVF_TAG = 0x1062a5b8, 0x1062a5c8
STATE, LIST, REAR_COPY, EVF_COPY = MEM + 0x1000, MEM + 0x2000, MEM + 0x3000, MEM + 0x3100
REAR_RECEIVERS = (0xa180a534, MEM + 0x6000, MEM + 0x7000)
EVF_RECEIVERS = (0xa180a3bc, 0xa180ab80)
SETTERS = (0x1024589c, 0x1025b97e, 0x1024570e, 0x1034e25a, 0x1034e672)
MODE, PROPERTY_KEYS, PROPERTY_CACHE = 0xa24e1e00, 0xa1828e88, 0xa201f260


class OutputFixture(NativePNG):
    def __init__(self, raw):
        super().__init__(raw)
        self.u.mem_map(0xa24e1000, 0x1000)
        self.u.mem_map(0xa2010000, 0x20000)
        self.properties, self.kinds, self.setters = [], [], []
        self.write(0xa180a588, STATE)
        self.write(0xa180a52c, REAR_RECEIVERS[1])
        self.write(0xa180a520, REAR_RECEIVERS[2])
        self.u.mem_write(REAR_COPY, raw[REAR_TAG - BASE:REAR_TAG - BASE + 16])
        self.u.mem_write(EVF_COPY, raw[EVF_TAG - BASE:EVF_TAG - BASE + 16])
        # Matching prefix but distinct final byte must not pass16-byte compare.
        invalid = bytearray(raw[REAR_TAG - BASE:REAR_TAG - BASE + 16])
        invalid[-1] ^= 1
        self.u.mem_write(MEM + 0x3200, bytes(invalid))

    def write(self, address, value):
        self.u.mem_write(address, struct.pack('<I', value))

    def read(self, address):
        return int.from_bytes(self.u.mem_read(address, 4), 'little')

    def hook(self, u, address, size, context):
        if address == 0x104065a4:
            self.properties.append(u.reg_read(UC_ARM_REG_R0))
        if address == OUTPUT_KIND:
            self.kinds.append(self.read(0xa181c764))
        if address in SETTERS:
            self.setters.append((address, u.reg_read(UC_ARM_REG_R0)))
        super().hook(u, address, size, context)


def audit(raw):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA:
        raise ValueError('Exact private original-Z7 C3.80 main required')
    checks = []

    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good:
            raise AssertionError(name)

    f = OutputFixture(raw)
    candidates = (0, REAR_COPY, EVF_COPY, MEM + 0x3200)
    for output, tag, mirrors, setter_list in (
        (0, REAR_COPY, REAR_RECEIVERS, SETTERS[:3]),
        (2, EVF_COPY, EVF_RECEIVERS, SETTERS[3:])):
        for primary, secondary in itertools.product(candidates, repeat=2):
            for offset, value in ((0, primary), (4, 0xa5a5a5a5), (8, 0x5a5a5a5a),
                                  (12, 0xf0f0f0f0), (16, secondary)):
                f.write(LIST + offset, value)
            incoming = bytes(f.u.mem_read(LIST, 20))
            for address in (*REAR_RECEIVERS, *EVF_RECEIVERS):
                f.write(address, 0xc3c3c3c3)
            f.write(STATE + 8, 0xc3c3c3c3)
            f.write(STATE + 12, 0xc3c3c3c3)
            f.u.mem_write(0xa180a568, b'\2')
            f.setters.clear()
            expected = secondary if secondary == tag else primary if primary == tag else 0
            value = f.call(SOURCE_SELECT, LIST, 0xfeedface, output)
            label = f'output{output}-primary{candidates.index(primary)}-secondary{candidates.index(secondary)}'
            check(label + '-native-selects-matching-tag-secondary-first', value == expected and
                  f.read(STATE + (8 if output == 0 else 12)) == expected)
            check(label + '-native-setters-publish-only-matching-output-or-retain-stale-mirrors-on-no-match',
                  all(f.read(a) == (expected or 0xc3c3c3c3) for a in mirrors) and
                  all(f.read(a) == 0xc3c3c3c3 for a in (EVF_RECEIVERS if output == 0 else REAR_RECEIVERS)) and
                  f.setters == ([(a, expected) for a in setter_list] if expected else []))
            check(label + '-source-list-other-output-and-active-selector-unchanged',
                  bytes(f.u.mem_read(LIST, 20)) == incoming and
                  f.read(STATE + (12 if output == 0 else 8)) == 0xc3c3c3c3 and
                  f.u.mem_read(0xa180a568, 1) == b'\2')

    # Distinct pointers with identical native tag prove address-independent
    # matching and priority. Original ROM tag is read directly, never supplied
    # as the result of the native comparison service.
    for output, original, clone in ((0, REAR_TAG, REAR_COPY), (2, EVF_TAG, EVF_COPY)):
        for primary, secondary in ((original, clone), (clone, original)):
            f.write(LIST, primary)
            f.write(LIST + 16, secondary)
            check(f'output{output}-distinct-identical-tags-select-secondary{secondary:x}',
                  f.call(SOURCE_SELECT, LIST, 0, output) == secondary)
    for output in (3, 4, 0xffffffff):
        before = bytes(f.u.mem_read(STATE, 32))
        f.setters.clear()
        check(f'unsupported-source-output{output:x}-does-not-publish', f.call(SOURCE_SELECT, LIST, 0, output) == LIST and
              bytes(f.u.mem_read(STATE, 32)) == before and not f.setters)

    for kind in range(6):
        f.write(0xa181c764, kind)
        check(f'output-kind{kind}-original-getter-reads-supplied-ram-word', f.call(OUTPUT_KIND) == kind)
        for mode in (0, 1):
            f.write(MODE, mode)
            f.properties.clear()
            f.kinds.clear()
            expected = (0x2f17 if mode else 0x2f15) + int(kind != 1)
            check(f'output-kind{kind}-mode{mode}-native-disp-selector-uses-real-kind-getter',
                  f.call(DISP_SELECT) == expected and f.properties == [0x138d] and f.kinds == [kind])

    check('native-mode-property-key-resolves-to-exact-rom-descriptor',
          f.call(0x10070204, 0x138d, MEM + 0x8000) == 1 and f.read(MEM + 0x8000) == 0x467 and
          bytes(f.u.mem_read(0x114d501c, 12)) == struct.pack('<3I', 7, 4, MODE))
    mode_index = 0x21c // 4
    check('native-bulk-property-key-table-contains-mode-at-exact-cache-index',
          f.read(PROPERTY_KEYS + mode_index * 4) == 0x138d)
    for mode in (0, 1, 2, 0xffffffff):
        f.write(MODE, mode)
        f.write(MEM + 0x8000, 0xaaaaaaaa)
        check(f'mode{mode:x}-native-property-wrappers-read-live-word-without-supplied-return',
              f.call(0x104065a4, 0x138d) == mode and
              f.call(0x10070234, 0x138d, MEM + 0x8000) == 1 and f.read(MEM + 0x8000) == mode)
        # Execute the real bulk wrapper and loop for a one-key slice of the
        # original table. Other269 property locations are intentionally not
        # initialized. This proves the exact mode-cache write, not all snapshot
        # fields or a whole-camera transaction.
        f.u.mem_write(PROPERTY_CACHE + 0x21c - 4, b'\xa5' * 12)
        check(f'mode{mode:x}-native-bulk-snapshot-copies-mode-and-preserves-neighbors',
              f.call(0x10376414, PROPERTY_KEYS + 0x21c, PROPERTY_CACHE + 0x21c, 1) == 1 and
              bytes(f.u.mem_read(PROPERTY_CACHE + 0x21c - 4, 12)) == b'\xa5' * 4 + struct.pack('<I', mode) + b'\xa5' * 4)
    return dict(passed=True, checks=checks, stock_main_sha256=STOCK_SHA,
                native_source_select_compare_and_all_five_setters_execute=True,
                native_output_kind_getter_execute=True, native_output_kind_word='0xa181c764',
                logical_source_output0_tag='rear-monitor', logical_source_output2_tag='EVF',
                source_selection_does_not_change_active_selector=True,
                source_no_match_clears_primary_pointer_but_retains_downstream_mirrors=True,
                native_mode_property_lookup_getters_and_single_key_bulk_copy_execute=True,
                native_mode_live_word=hex(MODE), native_mode_cache_word=hex(PROPERTY_CACHE + 0x21c),
                mode_and_source_ram_contents_supplied=True, native_mode_or_output_getter_return_supplied=False,
                mode_snapshot_producer_and_cross_task_coherence_bound=False,
                physical_display_or_warning_pixels_verified=False,
                full_profile_highlight_preference_connected=False, physical_camera_or_card_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists():
        p.error('Choose a new private output')
    result = audit(a.stock_main.read_bytes())
    result['audit_source_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__':
    main()
