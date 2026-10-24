"""The review helper must never stage firmware outside private local storage."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import prepare_flash_review

TEMP_PARENT = prepare_flash_review.ROOT / '.private'


class ReviewOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        TEMP_PARENT.mkdir(exist_ok=True)

    def test_private_new_subdirectory_is_accepted(self):
        with tempfile.TemporaryDirectory(dir=TEMP_PARENT) as temporary:
            root = Path(temporary)
            with patch.object(prepare_flash_review, 'ROOT', root):
                output = root / '.private/review/new'
                self.assertEqual(prepare_flash_review.require_private_output(output), output.resolve())
                self.assertFalse(output.exists())

    def test_outside_and_parent_escape_are_rejected_without_writing(self):
        with tempfile.TemporaryDirectory(dir=TEMP_PARENT) as temporary:
            root = Path(temporary)
            with patch.object(prepare_flash_review, 'ROOT', root):
                for output in [root / 'card', root / '.private/../card', root / '.private']:
                    with self.subTest(output=output), self.assertRaises(ValueError):
                        prepare_flash_review.require_private_output(output)
                self.assertEqual(list(root.iterdir()), [])

    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory(dir=TEMP_PARENT) as temporary:
            root = Path(temporary)
            output = root / '.private/review'
            output.mkdir(parents=True)
            sentinel = output / 'keep.txt'
            sentinel.write_text('keep')
            with patch.object(prepare_flash_review, 'ROOT', root), self.assertRaises(ValueError):
                prepare_flash_review.require_private_output(output)
            self.assertEqual(sentinel.read_text(), 'keep')


if __name__ == '__main__':
    unittest.main()
