"""Synthetic card inputs; backups stay private and sources must be read-only."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import inspect_z7_card as card


class CardInspectionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=card.ROOT / '.private')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'card'
        self.source.mkdir()
        self.output = self.root / 'backup'
        self.identity = dict(drive='E', system_drive='C', bus='USB', boot=False,
                             system=False, disk_id='synthetic-card', volume_id='synthetic-volume')

    def inspect(self, identity=None, recheck=None):
        return card.inspect_card(self.source, self.output, identity or self.identity,
                                 recheck or (lambda: dict(self.identity)))

    def test_named_backups_readback_and_source_access_are_read_only(self):
        originals = {'EG161080.BIN': b'synthetic firmware', 'Z7CFG0.DAT': b'preferences',
                     'unrelated-photo.NEF': b'leave this untouched'}
        for name, data in originals.items(): (self.source / name).write_bytes(data)
        opened, original_open = [], Path.open
        def observe(path, mode='r', *args, **kwargs):
            if path.parent == self.source: opened.append((path.name, mode))
            return original_open(path, mode, *args, **kwargs)
        with patch.object(Path, 'open', observe): report = self.inspect()
        self.assertTrue(report['complete'])
        self.assertFalse(report['card_written'])
        self.assertFalse(report['installation_cleared'])
        self.assertFalse(report['installed_image_readback'])
        self.assertTrue(opened)
        self.assertTrue(all(mode == 'rb' for _, mode in opened))
        self.assertEqual({p.name: p.read_bytes() for p in self.source.iterdir()}, originals)
        self.assertEqual((self.output/'EG161080.BIN').read_bytes(), originals['EG161080.BIN'])
        self.assertFalse((self.output/'unrelated-photo.NEF').exists())
        self.assertFalse(report['files']['Z7CFG1.DAT']['present'])
        self.assertTrue(report['files']['Z7CFG0.DAT']['backup_readback_verified'])

    def test_system_or_internal_disk_is_rejected_before_output_creation(self):
        for change in ({'drive': 'C'}, {'boot': True}, {'system': True}, {'bus': 'NVMe'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.inspect(identity={**self.identity, **change})
            self.assertFalse(self.output.exists())

    def test_existing_backup_is_never_overwritten(self):
        self.output.mkdir()
        sentinel = self.output/'keep.txt'
        sentinel.write_text('original')
        with self.assertRaises(ValueError): self.inspect()
        self.assertEqual(sentinel.read_text(), 'original')
        self.assertEqual(list(self.output.iterdir()), [sentinel])

    def test_identity_change_preserves_incomplete_private_report(self):
        (self.source/'Z7APP.BIN').write_bytes(b'synthetic module')
        with self.assertRaisesRegex(ValueError, 'identity changed'):
            self.inspect(recheck=lambda: {**self.identity, 'disk_id': 'different-card'})
        report = json.loads((self.output/'inspection.json').read_text())
        self.assertFalse(report['complete'])
        self.assertFalse(report['card_written'])
        self.assertEqual((self.output/'Z7APP.BIN').read_bytes(), b'synthetic module')

    def test_outside_private_destination_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            outside = Path(temporary)/'backup'
            with self.assertRaises(ValueError):
                card.inspect_card(self.source, outside, self.identity, lambda: self.identity)
            self.assertFalse(outside.exists())

    def test_oversized_journal_is_not_copied_or_changed(self):
        source = self.source/'Z7CFG0.DAT'
        source.write_bytes(b'x'*4097)
        with self.assertRaisesRegex(ValueError, 'exceeds inspection limit'): self.inspect()
        self.assertFalse((self.output/source.name).exists())
        self.assertEqual(source.read_bytes(), b'x'*4097)
        self.assertFalse(json.loads((self.output/'inspection.json').read_text())['complete'])

    def test_drive_argument_cannot_be_a_path_or_command(self):
        with patch.object(card.subprocess, 'run') as run:
            for value in ('C:', 'E:\\', 'E;dir', ''):
                with self.subTest(value=value), self.assertRaises(ValueError): card.drive_identity(value)
            run.assert_not_called()

    def test_file_change_during_backup_cannot_report_success(self):
        source = self.source/'EG161080.BIN'
        source.write_bytes(b'original synthetic firmware')
        original_open, reads = Path.open, 0
        def changing_input(path, mode='r', *args, **kwargs):
            nonlocal reads
            if path == source and mode == 'rb':
                reads += 1
                if reads == 2:
                    # Simulate an external replacement before verification.
                    with original_open(source, 'wb') as handle: handle.write(b'changed input')
            return original_open(path, mode, *args, **kwargs)
        with patch.object(Path, 'open', changing_input), self.assertRaisesRegex(ValueError, 'Source changed'):
            self.inspect()
        self.assertEqual((self.output/source.name).read_bytes(), b'original synthetic firmware')
        self.assertFalse(json.loads((self.output/'inspection.json').read_text())['complete'])


if __name__ == '__main__': unittest.main()
