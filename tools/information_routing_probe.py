"""Observe full custom-DISP/native-information routing in assisted QEMU.

SPDX-License-Identifier: MIT. Settings are edited through compiled module APIs;
native DISP keys drive transitions. No application/snapshot/mask/pixel writes.
"""
import hashlib
from pathlib import Path
import struct


def run_information_routing_probe(camera, output, module, base, result, capture, native, key, query, check):
    if module['kind'] != 'original-Z7-display-information-diagnostic':
        raise ValueError('Full information profile required')
    source = Path(__file__).read_bytes()
    (output / 'information-routing-probe-source.py').write_bytes(source)
    result['information_routing_probe_source_sha256'] = hashlib.sha256(source).hexdigest()
    result['information_routing_scope'] = dict(full_focal_other_histogram_profile=True,
        settings_edited_through_compiled_apis=True, native_disp_keys=True,
        app_snapshot_mask_or_pixel_writes=False, lens_properties_supplied=False,
        physical_camera_verified=False, visual_acceptance=False)
    symbols = module['symbols']
    model = base + symbols['z7_menu_settings']

    def word(address):
        return int.from_bytes(camera.remote.memory(address, 4), 'little')

    def value(name):
        return word(base + symbols[name])

    def app():
        return camera.remote.memory(0xa1829af4, 1)[0]

    def setting(name, *args):
        check('setting-' + name + '-' + '-'.join(map(str, args)),
              query('Edit compiled display setting', base + symbols['z7_settings_' + name], [model, *args]) == 1)

    def observe(name):
        native('Wait for native app update and rendering', 0x1017081e, [500])
        step = capture(name)
        step['information_routing'] = dict(app=app(), preset=value('z7_readout_preset'),
            ledger=list(struct.unpack('<5I', camera.remote.memory(base + symbols['z7_information_ledger'], 20))),
            pending=value('z7_information_pending'), suspended=value('z7_information_suspended'),
            entries=value('z7_information_entries'), returns=value('z7_information_returns'),
            errors=value('z7_information_errors'), property=query('Read native page', 0x104065a4, [0x2f15]),
            key=hex(word(0xa182d180)), event=hex(word(0xa182d184)))
        return step

    native('Select original user horizon page before custom ownership', 0x103673de, [3])
    baseline = observe('information-routing-native-page3')
    check('starts-on-native-user-page3', baseline['information_native_page'] == 3 and app() == 0)
    for preset in range(4):
        for bit in (1, 2):
            setting('component', preset, bit, 0)
    setting('page', 4, 1)
    setting('flag', 0, 1)
    initial = observe('information-routing-preset0')
    check('custom-preset0-retains-user-baseline3', initial['information_base']['saved'] == 3 and
          initial['information_base']['active'] == 1 and value('z7_readout_preset') == 0)
    for preset in (1, 2, 3):
        key('disp', lambda: value('z7_readout_preset') == preset)
        step = observe('information-routing-preset' + str(preset))
        check('native-key-selects-custom-preset-' + str(preset), app() == 0 and step['information_base']['saved'] == 3)
    key('disp', lambda: app() == 13)
    information = observe('information-routing-visible')
    check('fifth-choice-enters-actual-native-information-app', app() == 13 and value('z7_readout_preset') == 4 and
          information['information_native_page'] == 4 and information['information_routing']['property'] == 4)
    check('information-entry-releases-masks-and-base', information['information_masks'] == baseline['information_masks'] and
          information['information_base']['active'] == 0 and information['information_routing']['suspended'] == 1)
    check('information-native-key-event-still-original', information['information_routing']['key'] == '0x102fd647' and
          information['information_routing']['event'] == '0x102fdaef')
    key('disp', lambda: app() == 0 and value('z7_readout_preset') == 0)
    returned = observe('information-routing-return-preset0')
    check('native-return-reacquires-preset-with-original-baseline3', returned['information_base']['active'] == 1 and
          returned['information_base']['saved'] == 3 and returned['information_routing']['ledger'][0] == 0)
    setting('flag', 0, 0)
    restored = observe('information-routing-master-off')
    check('master-off-restores-user-page-and-all61-masks', restored['information_native_page'] == 3 and
          restored['information_routing']['property'] == 3 and restored['information_masks'] == baseline['information_masks'])
    for preset in range(4):
        setting('page', preset, 0)
    setting('flag', 0, 1)
    only = observe('information-routing-only-information')
    check('information-only-config-enters-native-app', app() == 13 and only['information_routing']['preset'] == 4)
    count = value('z7_preset_cycles')
    key('disp', lambda: value('z7_preset_cycles') > count)
    same = observe('information-routing-only-disp')
    check('information-only-disp-keeps-native-app', app() == 13 and same['information_native_page'] == 4)
    setting('flag', 0, 0)
    off = observe('information-routing-only-master-off')
    check('master-off-from-information-restores-native-user-page3', app() == 0 and off['information_native_page'] == 3 and
          off['information_routing']['property'] == 3 and off['information_routing']['ledger'][0] == 0 and
          off['information_masks'] == baseline['information_masks'])
    check('routing-completes-without-owned-transition-errors', value('z7_information_errors') == 0)
    # Separate, explicitly supplied lens phase. Native property producers and
    # actual hardware telemetry are not established by these two incoming words.
    fixture = result['information_routing_lens_fixture'] = dict(
        type=1, tenths=245, addresses=['0xa24e2600', '0xa24e25a8'],
        scope='Incoming source fixture only for the following focal-retirement phase')
    for address, number in ((0xa24e2600, fixture['type']), (0xa24e25a8, fixture['tenths'])):
        if camera.remote.command(f'M{address:x},4:' + struct.pack('<I', number).hex()) != 'OK':
            raise RuntimeError('Incoming focal source fixture rejected')
    result['information_routing_scope']['lens_properties_supplied'] = True
    result['information_routing_scope']['native_only_phase_precedes_lens_fixture'] = True
    setting('page', 0, 1)
    setting('information', 0, 7, 1)
    setting('flag', 0, 1)
    focal = observe('information-routing-focal-visible')
    check('full-profile-focal-text-renders-before-information-entry', app() == 0 and
          focal['focal']['object'] != 0 and focal['focal']['text'] == '24.5mm' and
          focal['focal']['paints'] > 0 and focal['focal']['presents'] > 0 and
          focal['information_base']['saved'] == 3)
    key('disp', lambda: app() == 13)
    retired = observe('information-routing-focal-retired-in-information')
    check('native-information-entry-follows-focal-painter-retirement', app() == 13 and
          word(retired['focal']['object'] + 0x28) == 0 and
          retired['information_masks'] == baseline['information_masks'] and
          retired['information_routing']['ledger'][0] == 2)
    key('disp', lambda: app() == 0 and value('z7_readout_preset') == 0)
    focal_return = observe('information-routing-focal-returned')
    check('full-profile-focal-text-reappears-after-native-return', focal_return['focal']['text'] == '24.5mm' and
          focal_return['focal']['paints'] > focal['focal']['paints'] and
          focal_return['focal']['presents'] > focal['focal']['presents'] and
          focal_return['information_base']['saved'] == 3)
    setting('flag', 0, 0)
    final = observe('information-routing-focal-master-off')
    check('focal-roundtrip-master-off-restores-user-page-and-masks', app() == 0 and
          final['information_native_page'] == 3 and final['information_routing']['property'] == 3 and
          final['information_masks'] == baseline['information_masks'] and
          word(final['focal']['object'] + 0x28) == 0 and value('z7_information_errors') == 0)
