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


def run_focal_probe(camera, output, module, base, result, capture, native, key, check):
    if module['kind'] != 'original-Z7-display-focal-diagnostic':
        raise ValueError('Focal overlay diagnostic required')
    source = Path(__file__).read_bytes()
    (output / 'focal-probe-source.py').write_bytes(source)
    result['focal_probe_source_sha256'] = hashlib.sha256(source).hexdigest()
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
    baseline_masks = references[0]['information_masks']
    for bit in (1, 2): native('Disable extra component for focal pixel isolation', base + module['symbols']['z7_settings_component'], [model, 0, bit, 0])
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
    membership(wait_capture('focal-component-off'))
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
    membership(retired)
    result['focal_scope'] = dict(lcd_landscape=True, independent_other_toggle=True, fractional_and_whole_native_text=True,
        incoming_lens_properties_supplied=True, snapshot_visibility_or_pixels_supplied=False,
        evf_rotation_af_and_broader_lifecycle_unverified=True, actual_lens_telemetry_verified=False)
