"""Isolate native Other/horizon repaint with the focal feature never enabled.

SPDX-License-Identifier: MIT. Uses the existing assisted QEMU loader/sensor
fixture. No lens properties, snapshots, visibility or pixels are supplied.
Complete captured RGB remains authoritative; object dumps remain private.
"""
import hashlib
from pathlib import Path
import struct

from PIL import Image, ImageChops
from display_pixel_geometry import control_scanout_box


def run_horizon_control(camera, output, module, base, result, capture, native, check):
    if module['kind'] != 'original-Z7-display-focal-diagnostic':
        raise ValueError('Focal diagnostic required to observe its inactive counters')
    for filename in ('focal_horizon_control.py', 'display_pixel_geometry.py'):
        source = Path(__file__).with_name(filename).read_bytes()
        (output / filename).write_bytes(source)
        result.setdefault('horizon_control_source_sha256', {})[filename] = hashlib.sha256(source).hexdigest()
    model = base + module['symbols']['z7_menu_settings']
    control = result['horizon_other_control'] = dict(
        focal_ever_enabled=False, incoming_lens_properties_supplied=False,
        snapshot_visibility_or_pixels_supplied=False, histories=[], comparisons=[],
        actual_lens_telemetry_verified=False, camera_access=False)

    def picture(step):
        return Image.open(output / (step['name'] + '.png')).convert('RGB')

    def observe(name):
        step = capture(name)
        # A never-created object rules out both its painter and retirement clear.
        check(name + '-focal-object-and-all-render-counters-stay-zero',
              all(step['focal'][field] == 0 for field in ('object', 'samples', 'paints', 'presents')))
        step['adl_objects'] = []
        for index, raw in enumerate(step['information_controls']['6']):
            pointer = struct.unpack_from('<I', bytes.fromhex(raw), 36)[0]
            if not 0xa1800000 <= pointer <= 0xc0000000 - 284:
                raise ValueError('Unexpected native ADL object address')
            data = camera.remote.memory(pointer, 284)
            filename = f'{name}-adl-object-{index}.bin'
            (output / filename).write_bytes(data)
            step['adl_objects'].append(dict(pointer=hex(pointer), file=filename,
                                            sha256=hashlib.sha256(data).hexdigest()))
        return step

    native('Select original standard control page', 0x103673de, [0])
    standard = observe('control-original-standard')
    native('Select original horizon control page', 0x103673de, [3])
    horizon = observe('control-original-horizon')
    check('control-original-horizon-page-selected', horizon['information_native_page'] == 3)
    native('Return to saved standard page before custom ownership', 0x103673de, [0])
    native('Explicitly keep focal disabled for entire control', base + module['symbols']['z7_settings_information'], [model, 0, 7, 0])
    native('Enable Other group for control', base + module['symbols']['z7_settings_information'], [model, 0, 6, 1])
    for bit in (1, 3):
        native('Disable unrelated histogram/highlight component', base + module['symbols']['z7_settings_component'], [model, 0, bit, 0])
    native('Select horizon component for control', base + module['symbols']['z7_settings_component'], [model, 0, 2, 1])
    native('Enable custom horizon control', base + module['symbols']['z7_settings_flag'], [model, 0, 1])

    def qualify(prefix):
        history = dict(name=prefix, frames=[], qualified=False)
        control['histories'].append(history)
        latest, repeats = {}, {}
        # Preserve the existing24-reference cap; this is a separate history,
        # not an extension of a previous failed run or a pixel tolerance.
        delays = (500, 125, 250, 375, 125, 250, 375, 125) + (500,) * 16
        for index, delay in enumerate(delays, 1):
            native('Observe unchanged-setting native Other control', 0x1017081e, [delay])
            step = observe(prefix + '-' + str(index))
            check(step['name'] + '-native-horizon-owned',
                  step['information_native_page'] == 3 and step['information_base']['active'] == 1)
            image = picture(step)
            rect = struct.unpack_from('<4h', bytes.fromhex(step['information_controls']['15'][0]), 10)
            phase = hashlib.sha256(image.crop(control_scanout_box(rect, image.size)).tobytes()).hexdigest()
            full_rgb = hashlib.sha256(image.tobytes()).hexdigest()
            previous = latest.get(phase)
            repeats[phase] = repeats.get(phase, 0) + 1 if previous and previous['full_rgb_sha256'] == full_rgb else 0
            record = dict(frame=step['name'], iso_phase_sha256=phase,
                          full_rgb_sha256=full_rgb, consecutive_same_phase_repeats=repeats[phase])
            history['frames'].append(record)
            latest[phase] = record
            # Information may be repainted; the level and every pixel outside
            # its source rectangles must still equal the original horizon.
            outside = ImageChops.difference(image, picture(horizon))
            for rows in step['information_controls'].values():
                for raw in rows:
                    r = struct.unpack_from('<4h', bytes.fromhex(raw), 10)
                    if r[0] < r[2] and r[1] < r[3]:
                        outside.paste((0, 0, 0), control_scanout_box(r, image.size))
            check(step['name'] + '-protects-level-and-non-information-pixels', outside.getbbox() is None)
            if len(latest) == 2 and all(n >= 2 for n in repeats.values()):
                history['qualified'] = True
                break
        check(prefix + '-two-native-iso-phases-observed', len(latest) == 2)
        check(prefix + '-complete-rgb-repeats-in-each-iso-phase', history['qualified'])
        return latest

    before = qualify('control-before-other-cycle')
    native('Disable Other with focal never enabled', base + module['symbols']['z7_settings_information'], [model, 0, 6, 0])
    native('Observe native Other suppression', 0x1017081e, [500])
    off = observe('control-other-off')
    check('control-other-off-owns-same-horizon', off['information_native_page'] == 3 and off['information_base']['active'] == 1)
    native('Restore Other with focal still never enabled', base + module['symbols']['z7_settings_information'], [model, 0, 6, 1])
    after = qualify('control-after-other-cycle')
    steps = {step['name']: step for step in result['steps']}
    check('control-before-and-after-have-same-iso-phase-set', set(before) == set(after))
    for phase, original in before.items():
        restored = after[phase]
        a, b = steps[original['frame']], steps[restored['frame']]
        difference = ImageChops.difference(picture(a), picture(b))
        control['comparisons'].append(dict(
            iso_phase_sha256=phase, original=a['name'], restored=b['name'],
            full_rgb_equal=difference.getbbox() is None, difference_bounds=difference.getbbox(),
            differing_rgb_pixels=sum(p != (0, 0, 0) for p in difference.get_flattened_data()),
            native_masks_equal=a['information_masks'] == b['information_masks'],
            native_adl_controls_equal=a['information_controls']['6'] == b['information_controls']['6']))
    control['native_background_changed_without_focal_object'] = any(not c['full_rgb_equal'] for c in control['comparisons'])
    native('Disable custom master after native Other control', base + module['symbols']['z7_settings_flag'], [model, 0, 0])
    native('Observe native master restoration', 0x1017081e, [500])
    retired = observe('control-master-off')
    check('control-master-off-restores-all61-native-masks', retired['information_masks'] == standard['information_masks'])
    check('control-master-off-restores-saved-native-page0', retired['information_native_page'] == 0 and not retired['information_base']['active'])
    check('control-other-cycle-restores-complete-settled-native-rgb',
          all(c['full_rgb_equal'] for c in control['comparisons']))
