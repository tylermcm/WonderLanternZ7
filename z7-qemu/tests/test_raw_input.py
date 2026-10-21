# SPDX-License-Identifier: GPL-2.0-or-later
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
"""RAW input acceptance and failure cases, with independent byte fixtures."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from raw_input import RawSequence, STORAGE


class RawInputTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.manifest = self.root/'manifest.json'
        self.data = dict(width=4, height=4, sample_bits=12, cfa='RGGB',
                         stride_bytes=12, storage=STORAGE, black_level=64,
                         white_level=4095, fps=30, frames=[])
        for index in range(2):
            # Deliberately nonzero padding: it is not part of the CFA samples.
            raw = b''.join(struct.pack('<4H', 64+index+y, 256, 1024, 4095)+b'\xff'*4 for y in range(4))
            name = f'{index}.raw'
            (self.root/name).write_bytes(raw)
            self.data['frames'].append(dict(index=index, timestamp_ns=index*33333333,
                filename=name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
        self.save()

    def save(self):
        self.manifest.write_text(json.dumps(self.data), encoding='utf-8')

    def test_order_bytes_padding_and_no_guest_claim(self):
        sequence = RawSequence(self.manifest)
        first, second = sequence.read_frame(0), sequence.read_frame(1)
        self.assertEqual(first.data, (self.root/'0.raw').read_bytes())
        self.assertNotEqual(first.sha256, second.sha256)
        self.assertLess(first.timestamp_ns, second.timestamp_ns)
        self.assertEqual(sequence.status()['validated_frames'], 2)
        self.assertEqual(sequence.status()['guest_frames_transferred'], 0)
        self.assertEqual(sequence.status()['firmware_frames_consumed'], 0)
        self.assertFalse(sequence.status()['cmos_input_connected'])

    def test_truncation_and_extra_bytes(self):
        path = self.root/'0.raw'
        original = path.read_bytes()
        for raw in (original[:-1], original+b'\0'):
            with self.subTest(length=len(raw)):
                path.write_bytes(raw)
                with self.assertRaisesRegex(ValueError, 'size mismatch'):
                    RawSequence(self.manifest)

    def test_payload_mutation_after_loading(self):
        sequence = RawSequence(self.manifest)
        path = self.root/'0.raw'
        raw = bytearray(path.read_bytes()); raw[0] ^= 1; path.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            sequence.read_frame(0)

    def test_high_bits_rejected_with_valid_checksum(self):
        path = self.root/'0.raw'
        raw = bytearray(path.read_bytes()); raw[:2] = struct.pack('<H', 4096)
        path.write_bytes(raw)
        self.data['frames'][0]['sha256'] = hashlib.sha256(raw).hexdigest(); self.save()
        with self.assertRaisesRegex(ValueError, 'sample exceeds'):
            RawSequence(self.manifest)

    def test_layout_and_metadata_rejected(self):
        for key, value in [('width', 3), ('height', True), ('sample_bits', 11),
                           ('stride_bytes', 7), ('stride_bytes', 13), ('cfa', 'RGB'),
                           ('white_level', 64), ('fps', 0), ('storage', 'packed12')]:
            original = self.data[key]
            with self.subTest(key=key, value=value):
                self.data[key] = value; self.save()
                with self.assertRaises(ValueError): RawSequence(self.manifest)
            self.data[key] = original

    def test_out_of_order_and_traversal(self):
        for key, value in [('index', 2), ('index', True), ('timestamp_ns', 0),
                           ('filename', '../0.raw'), ('filename', 'D:\\0.raw'), ('bytes', 47)]:
            original = self.data['frames'][1][key]
            with self.subTest(key=key, value=value):
                self.data['frames'][1][key] = value; self.save()
                with self.assertRaises(ValueError): RawSequence(self.manifest)
            self.data['frames'][1][key] = original

    def test_no_implicit_loop(self):
        sequence = RawSequence(self.manifest)
        for index in (-1, 2, True):
            with self.assertRaises(ValueError): sequence.read_frame(index)


if __name__ == '__main__':
    unittest.main()
