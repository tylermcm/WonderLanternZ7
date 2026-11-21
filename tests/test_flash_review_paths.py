"""The review helper must never stage firmware outside private local storage."""
import binascii
import json
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


class LCDReviewAdmissionTests(unittest.TestCase):
    def test_display_only_host_requires_exact_report_and_all_bytes(self):
        payload = b'LCD display-only host fixture'
        eg = payload + binascii.crc_hqx(payload, 0).to_bytes(2, 'big')
        report = {'preset': 'sd-display-host-emulator-only', 'display_hooks': True}
        with tempfile.TemporaryDirectory(dir=TEMP_PARENT) as temporary:
            root = Path(temporary)
            with patch('build_z7_module_host.build_image', return_value=(eg, report)) as builder:
                for corruption in (None, 'eg', 'main', 'advanced-host'):
                    (root/'module-host.emulator.eg.bin').write_bytes(eg if corruption != 'eg' else eg[:-1])
                    (root/'module-host.emulator.main.bin').write_bytes(payload if corruption != 'main' else payload[:-1])
                    recorded = {**report, **({'api_bytes': 92} if corruption == 'advanced-host' else {})}
                    (root/'module-host.emulator.json').write_text(json.dumps(recorded))
                    with self.subTest(corruption=corruption):
                        if corruption is None:
                            self.assertEqual(prepare_flash_review.reviewed_candidate(root, 'lcd-first-release', b'container', b'stock'), (eg, report))
                            builder.assert_called_once_with(b'container', display_hooks=True)
                        else:
                            with self.assertRaises(ValueError):
                                prepare_flash_review.reviewed_candidate(root, 'lcd-first-release', b'container', b'stock')

    def test_lcd_module_rejects_changed_bytes_or_report_and_wrong_profile(self):
        packet = b'LCD module fixture'
        report = dict(kind='original-Z7-LCD-first-release-candidate', api_minimum_bytes=44,
                      target=0x03800007, module_sha256=prepare_flash_review.sha256(packet))
        with tempfile.TemporaryDirectory(dir=TEMP_PARENT) as temporary:
            root = Path(temporary)
            for corruption in (None, 'packet', 'report', 'profile', 'api', 'target'):
                rebuilt_report = dict(report)
                if corruption == 'profile': rebuilt_report['kind'] = 'original-Z7-display-information-module'
                if corruption == 'api': rebuilt_report['api_minimum_bytes'] = 92
                if corruption == 'target': rebuilt_report['target'] = 0x03800008
                recorded = {**rebuilt_report, **({'modified': True} if corruption == 'report' else {})}
                (root/'Z7APP.BIN').write_bytes(packet if corruption != 'packet' else packet + b'X')
                (root/'module.json').write_text(json.dumps(recorded))
                with self.subTest(corruption=corruption), patch.object(prepare_flash_review, 'rebuild_lcd_module', return_value=(packet, rebuilt_report)):
                    if corruption is None:
                        self.assertEqual(prepare_flash_review.reviewed_lcd_module(root), (packet, report))
                    else:
                        with self.assertRaises(ValueError): prepare_flash_review.reviewed_lcd_module(root)


class GridReviewAdmissionTests(unittest.TestCase):
    def test_gray_display_review_is_explicit_and_rejects_legacy_or_modified_files(self):
        payload = b'gray native LCD EVF spiral fixture'
        module = payload + binascii.crc_hqx(payload, 0).to_bytes(2, 'big')
        current = {'preset': 'grid-spiral-display-lifecycle-emulator-only', 'features': {}}
        legacy = {'preset': 'grid-spiral-lifecycle-emulator-only', 'features': {}}
        with tempfile.TemporaryDirectory(dir=TEMP_PARENT) as temporary:
            root = Path(temporary)
            def rebuild(raw, follow_display=False):
                return module, current if follow_display else legacy
            with patch('build_spiral_lifecycle.build_image', side_effect=rebuild) as builder:
                for corruption in (None, 'eg', 'main', 'legacy', 'explicit-only'):
                    (root/'spiral.emulator.eg.bin').write_bytes(module if corruption != 'eg' else module[:-1])
                    (root/'spiral.emulator.main.bin').write_bytes(payload if corruption != 'main' else payload[:-1])
                    recorded = legacy if corruption == 'legacy' else dict(current)
                    if corruption == 'explicit-only':
                        recorded['preset'] = 'grid-spiral-display-draw-emulator-only'
                    (root/'spiral.emulator.json').write_text(json.dumps(recorded))
                    with self.subTest(corruption=corruption):
                        if corruption is None:
                            self.assertEqual(prepare_flash_review.reviewed_candidate(
                                root, 'grid-spiral-display', b'container', b'stock'), (module, current))
                            builder.assert_called_once_with(b'container', follow_display=True)
                            with self.assertRaisesRegex(ValueError, 'report differs'):
                                prepare_flash_review.reviewed_candidate(root, 'grid-spiral', b'container', b'stock')
                        else:
                            with self.assertRaises(ValueError):
                                prepare_flash_review.reviewed_candidate(root, 'grid-spiral-display', b'container', b'stock')

    def test_spiral_review_requires_the_exact_automatic_build_and_all_bytes(self):
        payload = b'automatic spiral fixture'
        module = payload + binascii.crc_hqx(payload, 0).to_bytes(2, 'big')
        report = {'preset': 'grid-spiral-lifecycle-emulator-only',
                  'features': {'grid': {}, 'grid_native': {}, 'spiral_lifecycle': {}}}
        with tempfile.TemporaryDirectory(dir=TEMP_PARENT) as temporary:
            root = Path(temporary)
            eg, main, metadata = [root / ('spiral.emulator.' + name)
                                  for name in ('eg.bin', 'main.bin', 'json')]
            with patch('build_spiral_lifecycle.build_image', return_value=(module, report)) as rebuild:
                for corruption in (None, 'eg', 'main', 'report', 'explicit-draw'):
                    eg.write_bytes(module if corruption != 'eg' else module[:-1] + b'X')
                    main.write_bytes(payload if corruption != 'main' else payload[:-1])
                    recorded = dict(report)
                    if corruption == 'report':
                        recorded['unexpected'] = True
                    if corruption == 'explicit-draw':
                        recorded['preset'] = 'grid-spiral-draw-emulator-only'
                    metadata.write_text(json.dumps(recorded))
                    with self.subTest(corruption=corruption):
                        if corruption is None:
                            self.assertEqual(prepare_flash_review.reviewed_candidate(
                                root, 'grid-spiral', b'container', b'stock'), (module, report))
                            rebuild.assert_called_once_with(b'container')
                        else:
                            with self.assertRaises(ValueError):
                                prepare_flash_review.reviewed_candidate(root, 'grid-spiral', b'container', b'stock')

    def test_layouts_review_requires_the_exact_expanded_build(self):
        payload = b'six layout fixture'
        module = payload + binascii.crc_hqx(payload, 0).to_bytes(2, 'big')
        report = {'preset': 'grid-layouts-emulator-only', 'features': {'grid': {}, 'grid_native': {}}}
        with tempfile.TemporaryDirectory(dir=TEMP_PARENT) as temporary:
            root = Path(temporary)
            (root / 'grid.emulator.eg.bin').write_bytes(module)
            (root / 'grid.emulator.main.bin').write_bytes(payload)
            metadata = root / 'grid.emulator.json'
            metadata.write_text(json.dumps(report))
            with patch('build_grid_firmware.build_image', return_value=(module, report)) as rebuild:
                self.assertEqual(prepare_flash_review.reviewed_candidate(
                    root, 'grid-layouts', b'container', b'stock'), (module, report))
                rebuild.assert_called_once_with(b'container', persistent=False, native_choice=True, extra_grids=True)
                for wrong in ('grid-native-value-emulator-only', 'grid-spiral-draw-emulator-only'):
                    metadata.write_text(json.dumps(dict(report, preset=wrong)))
                    with self.subTest(preset=wrong), self.assertRaisesRegex(ValueError, 'report differs'):
                        prepare_flash_review.reviewed_candidate(root, 'grid-layouts', b'container', b'stock')

    def test_extra_layouts_cannot_use_existing_grid_flash_review(self):
        payload = b'additional layouts lab fixture'
        module = payload + binascii.crc_hqx(payload, 0).to_bytes(2, 'big')
        recorded = {'preset': 'grid-layouts-emulator-only', 'features': {'grid': {}, 'grid_native': {}}}
        released = {'preset': 'grid-native-value-emulator-only', 'features': {'grid': {}, 'grid_native': {}}}
        with tempfile.TemporaryDirectory(dir=TEMP_PARENT) as temporary:
            root = Path(temporary)
            (root / 'grid.emulator.eg.bin').write_bytes(module)
            (root / 'grid.emulator.json').write_text(json.dumps(recorded))
            with patch('build_grid_firmware.build_image', return_value=(module, released)):
                with self.assertRaisesRegex(ValueError, 'report differs'):
                    prepare_flash_review.reviewed_candidate(root, 'grid-native', b'container', b'stock')

    def test_native_choice_review_cannot_admit_ram_only_artifacts(self):
        def fixture(native):
            payload = b'native saved grid' if native else b'RAM grid'
            module = payload + binascii.crc_hqx(payload, 0).to_bytes(2, 'big')
            report = {'features': {'grid': {}, **({'grid_native': {}} if native else {})},
                      'preset': 'grid-native-value-emulator-only' if native else 'grid-emulator-only'}
            return module, report
        def rebuild(raw, persistent=False, native_choice=False):
            return fixture(native_choice)
        with tempfile.TemporaryDirectory(dir=TEMP_PARENT) as temporary:
            root = Path(temporary)
            with patch('build_grid_firmware.build_image', side_effect=rebuild):
                for native in (False, True):
                    module, report = fixture(native)
                    (root / 'grid.emulator.eg.bin').write_bytes(module)
                    (root / 'grid.emulator.main.bin').write_bytes(module[:-2])
                    (root / 'grid.emulator.json').write_text(json.dumps(report))
                    correct, wrong = ('grid-native', 'grid') if native else ('grid', 'grid-native')
                    self.assertEqual(prepare_flash_review.reviewed_candidate(
                        root, correct, b'container', b'stock'), (module, report))
                    with self.assertRaises(ValueError):
                        prepare_flash_review.reviewed_candidate(root, wrong, b'container', b'stock')

    def test_grid_review_rejects_mixed_or_modified_candidate_files(self):
        # Synthetic modules keep Nikon data out of this test. The independent
        # builder is the supplied boundary; artifact admission runs unchanged.
        payload = b'independent grid fixture'
        module = payload + binascii.crc_hqx(payload, 0).to_bytes(2, 'big')
        report = {'features': {'grid': {}}, 'preset': 'grid-emulator-only'}
        with tempfile.TemporaryDirectory(dir=TEMP_PARENT) as temporary:
            root = Path(temporary)
            eg, main, metadata = [root / ('grid.emulator.' + name)
                                  for name in ('eg.bin', 'main.bin', 'json')]
            with patch('build_grid_firmware.build_image', return_value=(module, report)):
                for corruption in (None, 'eg', 'main', 'report', 'persistent-report'):
                    eg.write_bytes(module if corruption != 'eg' else module[:-1] + b'X')
                    main.write_bytes(payload if corruption != 'main' else payload[:-1])
                    recorded = dict(report)
                    if corruption == 'report':
                        recorded['unexpected'] = True
                    if corruption == 'persistent-report':
                        recorded['preset'] = 'grid-persistent-emulator-only'
                    metadata.write_text(json.dumps(recorded))
                    with self.subTest(corruption=corruption):
                        if corruption is None:
                            self.assertEqual(prepare_flash_review.reviewed_candidate(
                                root, 'grid', b'container', b'stock'), (module, report))
                        else:
                            with self.assertRaises(ValueError):
                                prepare_flash_review.reviewed_candidate(
                                    root, 'grid', b'container', b'stock')

    def test_unknown_preset_is_rejected_before_reading_files(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            prepare_flash_review.reviewed_candidate(Path('unused'), 'grid-typo', b'', b'')

    def test_module_host_probe_is_excluded_from_installation_review(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            prepare_flash_review.reviewed_candidate(Path('unused'), 'sd-module-host-emulator-only', b'', b'')


if __name__ == '__main__':
    unittest.main()
