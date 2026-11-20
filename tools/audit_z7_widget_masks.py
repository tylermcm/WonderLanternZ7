"""Execute original-Z7 mask selection and snapshot invalidation instructions.

SPDX-License-Identifier: MIT. Camera snapshots/control data are supplied.
No firmware patch, pixels, physical camera or controller behavior is verified.
"""
import argparse
import hashlib
import json
from itertools import product
from pathlib import Path
import struct

from audit_splash_image import NativePNG, STOCK_SHA
from build_z7_module_host import ROOT

TABLE, SNAPSHOT, PREVIOUS = 0x1064d610, 0xa201d4d0, 0xa201d80c
READOUTS = (10, 11, 15)


def audit(raw):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA:
        raise ValueError('Exact original-Z7 stock MAIN required')
    f = NativePNG(raw)
    f.u.mem_map(0xa2010000, 0x20000)
    descriptors = {i: int.from_bytes(f.u.mem_read(TABLE + i * 4, 4), 'little') for i in READOUTS}
    controls = {i: int.from_bytes(f.u.mem_read(p + 44, 4), 'little') for i, p in descriptors.items()}
    for p in controls.values(): f.u.mem_write(p, b'\1')
    cases = 0
    # Tuple fields: native operation state338, activity2E0, secondary2EC,
    # expected bank. The state2 branch takes priority over activity2E0.
    banks = ((0, 0, 0, 0), (1, 0, 0, 1), (2, 0, 0, 0),
             (2, 0, 1, 2), (0, 1, 0, 1), (2, 1, 0, 0))
    for widget, output, bank, movie, operation, page, bit in product(
            READOUTS, range(4), banks, range(2), (0, 1, 3), range(5), (*range(12), 15, 31)):
        state, activity, secondary, selected_bank = bank
        f.u.mem_write(0xa18237c6, bytes([output]))
        f.u.mem_write(SNAPSHOT + 0x338, struct.pack('<H', state))
        f.u.mem_write(SNAPSHOT + 0x2e0, struct.pack('<I', activity))
        f.u.mem_write(SNAPSHOT + 0x2ec, struct.pack('<I', secondary))
        f.u.mem_write(SNAPSHOT + 0x40, bytes([movie]))
        f.u.mem_write(SNAPSHOT + 0x193, bytes([operation]))
        f.u.mem_write(SNAPSHOT + 0x18a, bytes([page]))
        words = [0xffffffff] * 9
        words[selected_bank * 3 + min(output, 2)] = 1 << bit
        f.u.mem_write(descriptors[widget] + 4, struct.pack('<9I', *words))
        # Native operation193=1 selects bits8..11 independently of movie;
        # values0/3 use photo0..3 or movie4..7. Page4 bypasses this exclusion.
        selected_bit = page + (8 if operation == 1 else movie * 4)
        expected = int(page < 4 and bit != selected_bit)
        actual = f.call(0x102f2690, widget)
        if actual != expected:
            raise AssertionError(dict(widget=widget, output=output, bank=bank,
                movie=movie, operation=operation, page=page, bit=bit, actual=actual, expected=expected))
        cases += 1
    checks = []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    check('native-mask-bank-and-photo-movie-operation-page-matrix', cases == 30240)
    for widget in READOUTS:
        f.u.mem_write(controls[widget], b'\0')
        f.u.mem_write(descriptors[widget] + 4, bytes(36))
        check('inactive-first-control-bypasses-mask-query-' + str(widget), f.call(0x102f2690, widget) == 0)
    current = bytes((i * 37 + 11) & 255 for i in range(0x33c))
    indices = bytes((i * 19 + 3) & 255 for i in range(7))
    f.u.mem_write(SNAPSHOT, current)
    f.u.mem_write(0xa18237b8, indices)
    f.u.mem_write(PREVIOUS, bytes(0x33c) + b'CANARY12')
    f.u.mem_write(0xa18237bf, bytes(7) + b'XYZ')
    f.call(0x10367c5a)
    check('native-invalidation-inverts-previous-snapshot-exactly', bytes(f.u.mem_read(PREVIOUS, 0x33c)) == bytes(v ^ 255 for v in current))
    check('native-invalidation-preserves-current-snapshot-and-canary', bytes(f.u.mem_read(SNAPSHOT, 0x33c)) == current and
        bytes(f.u.mem_read(PREVIOUS + 0x33c, 8)) == b'CANARY12')
    check('native-invalidation-inverts-seven-previous-format-indices-only', bytes(f.u.mem_read(0xa18237bf, 10)) == bytes(v ^ 255 for v in indices) + b'XYZ')
    return dict(passed=True, native_matrix_cases=cases, checks=checks, stock_main_sha256=STOCK_SHA,
        widgets=list(READOUTS), photo_page_0_and_3_bits=hex(0x909), normal_movie_bits=hex(0xf0),
        lcd_bank_word_indices=[0, 3], unmodified_third_lcd_bank_word_index=6,
        supplied_boundaries=['Snapshot, output and native control data'], native_services_replaced=[],
        camera_access=False, pixel_validation=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(); output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists(): p.error('Choose a new private output')
    result = audit(args.stock_main.read_bytes())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, native_matrix_cases=result['native_matrix_cases'], checks=len(result['checks']))))


if __name__ == '__main__': main()
