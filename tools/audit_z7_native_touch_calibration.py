"""Independent original-Z7 touch coordinate audit (MIT).

Executes stock conversion wrappers and their integer implementation. Synthetic
60-byte packets have zero gesture distance: distance/sqrt handling, driver
registration, queue lifetime, scheduling and physical calibration are outside
this audit. No firmware is generated or installed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from audit_splash_image import NativePNG, STOCK_SHA, MEM

OFFSETS = (0x12, 0x1a, 0x28, 0x2c, 0x30, 0x34)
TABLE = 0x10649be8
PACKET = MEM + 0x10000


def divide(n, d):
    return n // d if n >= 0 else -((-n) // d)


def audit(raw):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA:
        raise ValueError('Requires exact original Z7 C3.80 MAIN')
    f = NativePNG(raw)
    f.native_call_timeout_us = 0
    table = struct.unpack('<8h', f.u.mem_read(TABLE, 16))
    assert table == (720, 480, 1024, 682, 720, 480, 1024, 682)
    checks = 1
    packets = coordinates = 0
    # Both wrappers derive their dimensions directly from immutable stock ROM.
    for entry, source, target in (
        (0x103332aa, (1024, 682), (720, 480)),
        (0x10333294, (720, 480), (1024, 682)),
    ):
        for axis in (0, 1):
            values = list(range(source[axis] + 1)) + [-32768, -4, -1, 32767]
            for value in values:
                # Packet guards and unrelated bytes must survive native conversion.
                packet = bytearray((i * 17 + 3) & 255 for i in range(60))
                packet[0xc:0xe] = b'\0\0'
                expected = bytearray(packet)
                for offset in OFFSETS:
                    pair = [0, 0]
                    pair[axis] = value
                    struct.pack_into('<2h', packet, offset, *pair)
                    result = [divide(pair[a] * target[a] + source[a] // 2,
                                     source[a]) for a in (0, 1)]
                    result = [((v + 32768) % 65536) - 32768 for v in result]
                    struct.pack_into('<2h', expected, offset, *result)
                guard = b'\xa5' * 16
                f.u.mem_write(PACKET - 16, guard + bytes(packet) + guard)
                assert f.call(entry, PACKET) == 1
                assert bytes(f.u.mem_read(PACKET - 16, 92)) == guard + bytes(expected) + guard
                checks += 2
                packets += 1
                coordinates += 1
    # Equal dimensions return without touching any packet bytes.
    dimensions = PACKET + 0x100
    f.u.mem_write(dimensions, struct.pack('<2h', 720, 480))
    before = bytes(f.u.mem_read(PACKET, 60))
    assert f.call(0x103330d0, PACKET, dimensions, dimensions) == 0
    assert bytes(f.u.mem_read(PACKET, 60)) == before
    checks += 2
    return {
        'schema': 1, 'passed': True, 'checks': checks,
        'stock_main_sha256': STOCK_SHA,
        'dimension_table': list(table), 'native_packets': packets,
        'distinct_axis_samples': coordinates,
        'scope': 'Original forward/inverse wrappers; every in-range integer on both axes in all six point fields; signed sentinels; zero gesture distance; packet guards and ABI preservation',
        'limits': ['Synthetic packets; no physical touch calibration',
                   'No driver registration or queue copy/lifetime proof',
                   'No nonzero gesture-distance or sqrt-path proof',
                   'No input task, camera boot, installation or recovery proof'],
        'installation_candidate': False,
        'source_sha256': {
            str(p.relative_to(Path(__file__).resolve().parent.parent)).replace('\\', '/'):
                hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__).resolve(),
                      Path(__file__).resolve().with_name('audit_splash_image.py'))
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--main', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Output must not already exist')
    result = audit(args.main.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
