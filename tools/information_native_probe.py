"""Observe original information-page entry/return using native DISP inputs.

SPDX-License-Identifier: MIT. Assisted QEMU loader/sensor boundaries remain;
no custom page, lens value, native snapshot, visibility or pixel is supplied.
"""
import hashlib
from pathlib import Path

from PIL import Image, ImageChops


def run_information_native_probe(camera, output, module, base, result, capture, native, key, query, check, host=None):
    if module['kind'] != 'original-Z7-display-focal-diagnostic':
        raise ValueError('Use the inactive focal profile to observe its counters')
    source = Path(__file__).read_bytes()
    (output / 'information-native-probe-source.py').write_bytes(source)
    result['information_native_probe_source_sha256'] = hashlib.sha256(source).hexdigest()
    scope = result['information_app_control'] = dict(
        custom_information_implemented=False, focal_enabled=False,
        native_transition_via_disp_keys=True, baseline_pages_selected_by_native_setter_calls=True,
        incoming_lens_properties_supplied=False, snapshot_visibility_or_pixels_supplied=False)
    expected_update = (host['symbols'].get('z7_information_update_bridge', 0x102fda09)
                       if host and host.get('display_hooks') else 0x102fda09)
    scope['expected_information_update'] = hex(expected_update)
    scope['resident_information_update_wrapper'] = expected_update != 0x102fda09

    def word(address):
        return int.from_bytes(camera.remote.memory(address, 4), 'little')

    def app():
        return camera.remote.memory(0xa1829af4, 1)[0]

    def observe(name):
        native('Wait for native information-page drawing', 0x1017081e, [500])
        step = capture(name)
        index = app()
        if index >= 24:
            raise ValueError('Unrecognized native application index')
        step['native_information_app'] = dict(
            current=index, registry_descriptor=hex(word(0xa20207bc + index * 4)),
            key=hex(word(0xa182d180)), update=hex(word(0xa182d188)),
            event=hex(word(0xa182d184)),
            property2f15=query('Read original LCD page property', 0x104065a4, [0x2f15]),
            snapshot=camera.remote.memory(0xa20210c0, 0x100).hex())
        observed = step['native_information_app']
        step['native_lcd_registers'] = {hex(offset): hex(word(0x20144000 + offset)) for offset in (
            0x200, 0x204, 0x600, 0x604, 0x2110, 0x2200, 0x2204, 0x2208,
            0x2210, 0x2214, 0x2218, 0x2400, 0x2440, 0x24c0, 0x2500, 0x2540, 0x2580, 0x25c0)}
        check(name + '-keeps-original-information-key-event-and-expected-update',
              observed['key'] == '0x102fd647' and observed['event'] == '0x102fdaef' and
              observed['update'] == hex(expected_update))
        check(name + '-inactive-custom-focal-and-base',
              not step['information_base']['active'] and
              all(step['focal'][field] == 0 for field in ('object', 'samples', 'paints', 'presents')))
        return step

    native('Select original standard page for native app control', 0x103673de, [0])
    standard = observe('native-information-standard')
    check('native-information-control-starts-on-original-shooting-app',
          standard['native_information_app']['current'] == 0 and
          standard['native_information_app']['registry_descriptor'] == '0xa1829af8')
    native('Select original horizon page before native DISP entry', 0x103673de, [3])
    horizon = observe('native-information-horizon')
    check('native-information-control-horizon-page3', horizon['information_native_page'] == 3)
    key('disp', lambda: app() == 13)
    information = observe('native-information-visible')
    check('native-information-disp-enters-bound-app13',
          information['native_information_app']['current'] == 13 and
          information['native_information_app']['registry_descriptor'] == '0xa182d16c')
    check('native-information-entry-retains-native-page4', information['information_native_page'] == 4 and
          information['native_information_app']['property2f15'] == 4)
    def image(step):
        return Image.open(output / (step['name'] + '.png')).convert('RGB')
    check('native-information-panel-changes-real-pixels',
          all(ImageChops.difference(image(information), image(s)).getbbox() is not None
              for s in (standard, horizon)))
    key('disp', lambda: app() == 0)
    returned = observe('native-information-return')
    check('native-information-disp-returns-to-original-shooting-app0',
          returned['native_information_app']['current'] == 0 and
          returned['native_information_app']['registry_descriptor'] == '0xa1829af8')
    check('native-information-return-restores-native-page0', returned['information_native_page'] == 0 and
          returned['native_information_app']['property2f15'] == 0)
    check('native-information-control-preserves-all61-masks-at-entry-and-return',
          all(s['information_masks'] == standard['information_masks'] for s in (horizon, information, returned)))
    check('native-information-return-changes-panel-pixels',
          ImageChops.difference(image(information), image(returned)).getbbox() is not None)
    scope.update(observed_native_information_pixels=True, observed_native_return_pixels=True,
                 complete_rgb_restoration_asserted=False, physical_camera_verified=False)
