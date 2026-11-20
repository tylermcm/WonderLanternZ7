"""Private QEMU focal pixels with explicitly supplied lens property values.

SPDX-License-Identifier: MIT. Native masks/snapshots/visibility and pixels are
not supplied. This is a rendering fixture, not electronic-lens telemetry.
"""
import hashlib
import json
from pathlib import Path
import struct

from PIL import Image, ImageChops
from display_pixel_geometry import control_scanout_box


def run_focal_probe(camera, output, module, base, result, capture, native, key, check, horizon=False):
    if module['kind'] != 'original-Z7-display-focal-diagnostic':
        raise ValueError('Focal overlay diagnostic required')
    source = Path(__file__).read_bytes()
    (output / 'focal-probe-source.py').write_bytes(source)
    result['focal_probe_source_sha256'] = hashlib.sha256(source).hexdigest()
    geometry = Path(__file__).with_name('display_pixel_geometry.py').read_bytes()
    (output / 'geometry-source.py').write_bytes(geometry)
    result['information_geometry_source_sha256'] = hashlib.sha256(geometry).hexdigest()
    result['focal_source_scope'] = 'Supplied original properties1C14/1C01; no live lens hardware'
    originals = {hex(a): camera.remote.memory(a, 4).hex() for a in (0xa24e2600, 0xa24e25a8)}
    result['focal_incoming_property_fixture'] = dict(original_values=originals, updates=[])
    def incoming(kind, value):
        for address, word in ((0xa24e2600, kind), (0xa24e25a8, value)):
            data = struct.pack('<I', word)
            if camera.remote.command(f'M{address:x},4:' + data.hex()) != 'OK':
                raise RuntimeError('Incoming lens property fixture rejected')
        result['focal_incoming_property_fixture']['updates'].append(dict(type=kind, tenths=value))
    def image(step): return Image.open(output / (step['name'] + '.png')).convert('RGB')
    model = base + module['symbols']['z7_menu_settings']
    incoming(1, 245)
    native('Original standard focal baseline', 0x103673de, [0])
    references = [capture('focal-disabled-control-1')]
    native('Native layout invalidation while focal is disabled', 0x10367c5a, [])
    references.append(capture('focal-disabled-control-2'))
    for page in (1, 3, 0):
        key('disp', lambda: camera.remote.memory(0xa201d4d0 + 0x18a, 1)[0] == page)
        step = capture('focal-disabled-cycle-' + str(page))
        check('focal-disabled-native-cycle-' + str(page), step['information_native_page'] == page)
        if page == 0: references.append(step)
        elif page == 3: native_horizon_reference = step
    baseline_masks = references[0]['information_masks']
    standard_references = list(references)
    for bit in (1, 2): native('Disable extra component for focal pixel isolation', base + module['symbols']['z7_settings_component'], [model, 0, bit, 0])
    if horizon:
        native('Keep focal off while qualifying complete horizon references', base + module['symbols']['z7_settings_information'], [model, 0, 7, 0])
        native('Select native horizon component', base + module['symbols']['z7_settings_component'], [model, 0, 2, 1])
        native('Enable custom horizon baseline', base + module['symbols']['z7_settings_flag'], [model, 0, 1])
        native('Wait for native horizon baseline', 0x1017081e, [500])
        def iso_signature(step):
            rect = struct.unpack_from('<4h', bytes.fromhex(step['information_controls']['15'][0]), 10)
            picture = image(step)
            return hashlib.sha256(picture.crop(control_scanout_box(rect, picture.size)).tobytes()).hexdigest()
        wanted = {iso_signature(s) for s in standard_references}; observed = set(); references = []
        # ISO phase alone cannot qualify a whole reference. The ADL edge was
        # still changing before focal was enabled in horizon-live-01. Require
        # repeated complete native RGB within every observed blink phase.
        phase_frames, phase_repeats = {}, {}
        delays = (None, None, 125, 250, 375, 125, 250, 375) + (500,) * 16
        for index, delay in enumerate(delays, 1):
            if index == 2: native('Native invalidation with focal still off on horizon', 0x10367c5a, [])
            if delay: native('Observe unchanged-setting native horizon phase', 0x1017081e, [delay])
            step = capture('focal-horizon-disabled-reference-' + str(index))
            check('focal-horizon-reference-' + str(index) + '-owns-native-page3', step['information_native_page'] == 3 and step['information_base']['active'] == 1)
            picture = image(step); delta = ImageChops.difference(picture, image(native_horizon_reference))
            for rows in step['information_controls'].values():
                for raw in rows:
                    rect = struct.unpack_from('<4h', bytes.fromhex(raw), 10)
                    if rect[0] < rect[2] and rect[1] < rect[3]: delta.paste((0, 0, 0), control_scanout_box(rect, picture.size))
            check('focal-horizon-reference-' + str(index) + '-protects-level-and-non-information-pixels', delta.getbbox() is None)
            phase = iso_signature(step)
            fingerprint = hashlib.sha256(picture.tobytes()).hexdigest()
            phase_repeats[phase] = phase_repeats.get(phase, 0) + 1 if phase_frames.get(phase) == fingerprint else 0
            phase_frames[phase] = fingerprint
            observed.add(phase); references.append(step)
            result.setdefault('focal_horizon_reference_stability', []).append(dict(
                frame=step['name'], iso_phase_sha256=phase, full_rgb_sha256=fingerprint,
                consecutive_same_phase_repeats=phase_repeats[phase]))
            if observed == wanted and all(phase_repeats.get(p, 0) >= 2 for p in wanted): break
        check('focal-horizon-complete-native-iso-phases-qualified', observed == wanted)
        check('focal-horizon-whole-native-rgb-repeats-in-every-iso-phase',
              observed == wanted and all(phase_repeats.get(p, 0) >= 2 for p in wanted))
    native('Enable independent focal information', base + module['symbols']['z7_settings_information'], [model, 0, 7, 1])
    native('Enable custom focal preset', base + module['symbols']['z7_settings_flag'], [model, 0, 1])
    def wait_capture(name):
        native('Wait for native focal drawing', 0x1017081e, [500])
        return capture(name)
    def membership(step, region=None):
        picture = image(step); matches = []
        for ref in references:
            if ref['information_formats'] != step['information_formats']: continue
            diff = ImageChops.difference(picture, image(ref)); bounds = diff.getbbox()
            if region is None:
                if bounds is None: matches.append(dict(reference=ref['name']))
            elif bounds:
                outside = diff.copy(); outside.paste((0, 0, 0), region)
                if outside.getbbox() is None: matches.append(dict(reference=ref['name'], difference_bounds=bounds))
        result.setdefault('focal_pixel_membership', []).append(dict(frame=step['name'], allowed_window=region, matches=matches))
        check(step['name'] + ('-only-owned-focal-window-changes' if region else '-complete-native-rgb-restored'), bool(matches))
    active = wait_capture('focal-fractional-active')
    box = control_scanout_box((110, 194, 220, 218), image(active).size)
    check('fractional-focal-label-and-native-object-painted', active['focal']['text'] == '24.5mm' and active['focal']['paints'] > 0 and active['focal']['presents'] > 0)
    membership(active, box)
    incoming(1, 240)
    whole = wait_capture('focal-whole-active')
    check('whole-focal-label-updates', whole['focal']['text'] == '24mm')
    check('fractional-to-whole-changes-real-focal-pixels', image(active).crop(box).tobytes() != image(whole).crop(box).tobytes())
    membership(whole, box)
    native('Disable Other while focal stays enabled', base + module['symbols']['z7_settings_information'], [model, 0, 6, 0])
    other_off = wait_capture('focal-other-off')
    check('other-off-keeps-independent-focal-text-and-pixels', other_off['focal']['text'] == '24mm' and image(other_off).crop(box).tobytes() == image(whole).crop(box).tobytes())
    native('Restore Other information', base + module['symbols']['z7_settings_information'], [model, 0, 6, 1])
    native('Disable independent focal information', base + module['symbols']['z7_settings_information'], [model, 0, 7, 0])
    component_off = wait_capture('focal-component-off')
    membership(component_off)
    if horizon:
        # The no-focal Other control reproduces the ADL transient and returns
        # to the SAME complete native frames after settling. Before testing
        # focal reenable, require that exact restoration against the original
        # fixed references, rather than treating a500ms delay as a paint fence.
        restored_repeats = {phase: 0 for phase in phase_frames}
        restored_phases = set()
        for index in range(1, 25):
            native('Observe native background restoration with focal still off', 0x1017081e, [500])
            step = capture('focal-horizon-after-other-reference-' + str(index))
            phase = iso_signature(step)
            full_rgb = hashlib.sha256(image(step).tobytes()).hexdigest()
            restored_phases.add(phase)
            matches_fixed_native_frame = phase_frames.get(phase) == full_rgb
            restored_repeats[phase] = restored_repeats.get(phase, 0) + 1 if matches_fixed_native_frame else 0
            result.setdefault('focal_horizon_after_other_stability', []).append(dict(
                frame=step['name'], iso_phase_sha256=phase, full_rgb_sha256=full_rgb,
                matches_original_settled_native_frame=matches_fixed_native_frame,
                same_phase_restored_repeats=restored_repeats[phase]))
            check(step['name'] + '-focal-stays-disabled-with-sampling-stopped',
                  not (int.from_bytes(camera.remote.memory(model + 40, 4), 'little') & 128) and
                  step['focal']['samples'] == component_off['focal']['samples'])
            if restored_phases == set(phase_frames) and all(n >= 2 for n in restored_repeats.values()): break
        check('focal-horizon-other-return-matches-original-complete-native-phases-before-reenable',
              restored_phases == set(phase_frames) and all(n >= 2 for n in restored_repeats.values()))
    native('Restore independent focal information', base + module['symbols']['z7_settings_information'], [model, 0, 7, 1])
    incoming(1, 245)
    membership(wait_capture('focal-reenabled'), box)
    incoming(0, 245)
    absent = wait_capture('focal-lens-absent-stale-value')
    check('absent-lens-rejects-stale-focal-value', absent['focal']['tenths'] == 0xffffffff)
    membership(absent)
    incoming(1, 245)
    membership(wait_capture('focal-lens-return'), box)
    native('Disable custom focal master', base + module['symbols']['z7_settings_flag'], [model, 0, 0])
    retired = wait_capture('focal-master-off')
    check('master-off-restores-all-native-descriptor-masks', retired['information_masks'] == baseline_masks)
    if horizon:
        check('focal-horizon-master-off-restores-saved-native-page0', retired['information_native_page'] == 0 and not retired['information_base']['active'])
        references = standard_references
    membership(retired)
    result['focal_scope'] = dict(lcd_landscape=True, independent_other_toggle=True, fractional_and_whole_native_text=True,
        incoming_lens_properties_supplied=True, snapshot_visibility_or_pixels_supplied=False, native_horizon_combination=horizon,
        evf_rotation_af_and_broader_lifecycle_unverified=True, actual_lens_telemetry_verified=False)
