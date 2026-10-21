import json
import unittest
from importlib.resources import files
from unittest.mock import patch

from z30_extensions.container import ZERO_ANCHOR, extract_eg, recover_mask


class ContainerTests(unittest.TestCase):
    def test_wrong_input_rejected_before_decoder(self):
        with patch('z30_extensions.container.decode_body') as decode:
            with self.assertRaisesRegex(ValueError, 'SHA-256'):
                extract_eg(b'wrong firmware')
            decode.assert_not_called()

    def test_mask_recovery_with_independent_synthetic_tables(self):
        samples = json.loads(files('z30_extensions.platform').joinpath('z30_120_zero_samples.json').read_text())
        self.assertEqual(len(samples), 511)
        body = bytearray(max(samples + [ZERO_ANCHOR + 255]) + 1)
        a = [(i * 37 + 19) & 255 for i in range(256)]
        b = [(i * 11 + 23) & 255 for i in range(256)]
        c = [(i * 53 + 47) & 255 for i in range(256)]
        for offset in samples + list(range(ZERO_ANCHOR, ZERO_ANCHOR + 256)):
            body[offset] = a[offset & 255] ^ b[(offset >> 8) & 255] ^ c[(offset >> 16) & 255]
        columns, rows, blocks = recover_mask(body)
        for i in range(256):
            for row, block in ((0, 0), (i, 255 - i), ((i + 17) & 255, (i * 7) & 255)):
                self.assertEqual(columns[i] ^ rows[row] ^ blocks[block], a[i] ^ b[row] ^ c[block])

    def test_short_body_rejected(self):
        with self.assertRaisesRegex(ValueError, 'short'):
            recover_mask(b'')


if __name__ == '__main__':
    unittest.main()
