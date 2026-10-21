import binascii
import unittest

from z30_extensions.patch import Edit, apply_patch
from z30_extensions.platform.z30_120 import StockImage, sha256
from z30_extensions.thumb import Thumb


class PatchTests(unittest.TestCase):
    def setUp(self):
        self.source = bytes(range(16))
        self.source += binascii.crc_hqx(self.source, 0).to_bytes(2, 'big')
        self.options = dict(expected_sha256=sha256(self.source), base=0x1000, capacity=32)

    def apply(self, edits=(), append=b'', source=None, **overrides):
        options = self.options | overrides
        return apply_patch(self.source if source is None else source, edits, append, **options)

    def test_no_edits_preserves_input(self):
        result, _ = self.apply()
        self.assertEqual(result, self.source)

    def test_edits_append_and_crc(self):
        edit = Edit(4, self.source[4:8], b'abcd', 'test')
        result, report = self.apply([edit], b'WXYZ')
        self.assertEqual(result[:4], self.source[:4])
        self.assertEqual(result[4:8], b'abcd')
        self.assertEqual(result[8:16], self.source[8:16])
        self.assertEqual(result[16:20], b'WXYZ')
        self.assertEqual(binascii.crc_hqx(result, 0), 0)
        self.assertEqual(report['sha256'], sha256(result))

    def test_wrong_source_rejected(self):
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            self.apply(source=b'wrong')

    def test_corrupt_crc_rejected_even_with_matching_hash(self):
        bad = self.source[:-1] + bytes([self.source[-1] ^ 1])
        with self.assertRaisesRegex(ValueError, 'CRC'):
            self.apply(source=bad, expected_sha256=sha256(bad))

    def test_overlapping_and_boundary_edits_rejected(self):
        invalid = (
            [Edit(2, self.source[2:6], b'abcd', 'first'), Edit(4, self.source[4:6], b'ef', 'overlap')],
            [Edit(-1, b'a', b'b', 'negative')],
            [Edit(15, self.source[15:17], b'ab', 'CRC boundary')],
        )
        for edits in invalid:
            with self.subTest(edits=edits), self.assertRaises(ValueError):
                self.apply(edits)

    def test_invalid_sizes_and_expected_bytes_rejected(self):
        for edit in (Edit(0, b'', b'', 'empty'), Edit(0, b'\0', b'ab', 'size'),
                     Edit(0, b'X', b'Y', 'wrong byte')):
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                self.apply([edit])

    def test_alignment_and_capacity_rejected(self):
        with self.assertRaisesRegex(ValueError, 'aligned'):
            self.apply(append=b'xx')
        with self.assertRaisesRegex(ValueError, 'capacity'):
            self.apply(append=bytes(20))

    def test_stock_guard_rejects_outer_container_or_other_firmware(self):
        with self.assertRaisesRegex(ValueError, 'unmodified'):
            StockImage(self.source)


class ThumbTests(unittest.TestCase):
    def test_repeat_finish_and_literal_value(self):
        emitter = Thumb(0x1002)
        emitter.load(0, 'target', 0x12345678)
        emitter.emit('7047')
        result = emitter.finish()
        self.assertEqual(result, emitter.finish())
        self.assertIn(bytes.fromhex('78563412'), result)
        self.assertEqual((0x1002 + len(result)) % 4, 0)

    def test_conflicting_literal_and_missing_branch_rejected(self):
        emitter = Thumb(0x1000)
        emitter.load(0, 'target', 1)
        with self.assertRaises(ValueError):
            emitter.load(0, 'target', 2)
        emitter.branch(0, 'missing')
        with self.assertRaises(ValueError):
            emitter.finish()

    def test_out_of_range_branch_rejected(self):
        emitter = Thumb(0x1000)
        emitter.branch(0, 'far')
        emitter.emit('00bf' * 140)
        emitter.label('far')
        with self.assertRaisesRegex(ValueError, 'range'):
            emitter.finish()


if __name__ == '__main__':
    unittest.main()
