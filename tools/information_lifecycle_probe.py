"""Compare native/owned information MENU lifecycle and capture native draw data.

SPDX-License-Identifier: MIT. Uses native input and compiled settings APIs. Draw
files are opt-in private read-only observations, armed only for named phases.
No app/snapshot/mask/pixel or incoming lens values are supplied.
"""
import hashlib
from pathlib import Path
import struct


def run_information_lifecycle_probe(camera, output, module, base, result, capture, native, key, query, check, pages):
    if module['kind'] != 'original-Z7-display-information-diagnostic':
        raise ValueError('Full information profile required')
    source = Path(__file__).read_bytes()
    (output / 'information-lifecycle-probe-source.py').write_bytes(source)
    result['information_lifecycle_probe_source_sha256'] = hashlib.sha256(source).hexdigest()
    result['information_lifecycle_scope'] = dict(native_inactive_control=True, native_menu_inputs=True,
        app_snapshot_mask_pixel_or_lens_values_supplied=False, graphics_capture_changes_rendering=False,
        physical_camera_verified=False, native_information_visual_acceptance=False)
    symbols = module['symbols']
    model = base + symbols['z7_menu_settings']

    def word(address):
        return int.from_bytes(camera.remote.memory(address, 4), 'little')

    def value(name):
        return word(base + symbols[name])

    def app():
        return camera.remote.memory(0xa1829af4, 1)[0]

    def setting(name, *args):
        check('lifecycle-setting-' + name + '-' + '-'.join(map(str, args)),
              query('Edit compiled display setting', base + symbols['z7_settings_' + name], [model, *args]) == 1)

    def observe(name):
        native('Wait for native MENU/application update', 0x1017081e, [500])
        step = capture(name)
        step['information_lifecycle'] = dict(app=app(), preset=value('z7_readout_preset'),
            ledger=list(struct.unpack('<5I', camera.remote.memory(base + symbols['z7_information_ledger'], 20))),
            property=query('Read native LCD page', 0x104065a4, [0x2f15]),
            errors=value('z7_information_errors'), menu=pages(), key=hex(word(0xa182d180)), event=hex(word(0xa182d184)))
        check(name + '-preserves-native-information-key-and-event',
              word(0xa182d180) == 0x102fd647 and word(0xa182d184) == 0x102fdaef)
        return step

    def draw_records():
        return sorted(camera.gpu_draw_dump.glob('[0-9][0-9][0-9][0-9]-regs.bin'))

    def arm(name):
        before = len(draw_records())
        camera.gpu_draw_gate.write_text(name, encoding='utf-8')
        return before

    def disarm(name, before):
        camera.gpu_draw_gate.unlink()
        after = len(draw_records())
        result.setdefault('graphics_capture_phases', []).append(dict(name=name, first=before, after_last=after))
        check(name + '-captures-bounded-private-native-draws', before < after <= 512)

    before = arm('native-horizon')
    native('Select original user horizon page with custom settings inactive', 0x103673de, [3])
    baseline = observe('lifecycle-native-horizon')
    disarm('native-horizon', before)
    check('native-control-starts-on-shooting-page3', app() == 0 and baseline['information_native_page'] == 3)
    before = arm('native-information')
    key('disp', lambda: app() == 13)
    control = observe('lifecycle-native-information')
    disarm('native-information', before)
    check('native-control-enters-original-information-app', control['information_lifecycle']['property'] == 4 and value('z7_information_entries') == 0)
    key('menu', lambda: bool(pages()))
    control_menu = observe('lifecycle-native-information-menu')
    check('native-control-menu-is-open', bool(control_menu['information_lifecycle']['menu']))
    key('menu', lambda: not pages())
    control_closed = observe('lifecycle-native-information-menu-closed')
    check('native-control-menu-is-closed', not control_closed['information_lifecycle']['menu'])
    if app() == 13:
        key('disp', lambda: app() == 0)
    check('native-control-returns-to-shooting-before-custom-test', app() == 0)
    native('Restore original user horizon baseline for owned test', 0x103673de, [3])
    for preset in range(4):
        for bit in (1, 2):
            setting('component', preset, bit, 0)
    setting('page', 4, 1)
    for preset in (1, 2, 3):
        setting('page', preset, 0)
    setting('flag', 0, 1)
    selected = observe('lifecycle-custom-preset0')
    check('owned-preset-retains-original-user-page3', selected['information_base']['saved'] == 3 and selected['information_base']['active'] == 1)
    key('disp', lambda: app() == 13)
    owned = observe('lifecycle-owned-information')
    check('owned-information-entry-releases-all61-masks', owned['information_masks'] == baseline['information_masks'] and
          owned['information_base']['active'] == 0 and value('z7_readout_preset') == 4)
    key('menu', lambda: bool(pages()))
    owned_menu = observe('lifecycle-owned-information-menu')
    check('owned-information-menu-preserves-native-application-choice',
          owned_menu['information_lifecycle']['app'] == control_menu['information_lifecycle']['app'] and
          bool(owned_menu['information_lifecycle']['menu']) and owned_menu['information_masks'] == baseline['information_masks'])
    key('menu', lambda: not pages())
    owned_closed = observe('lifecycle-owned-information-menu-closed')
    check('owned-information-menu-return-matches-native-application',
          owned_closed['information_lifecycle']['app'] == control_closed['information_lifecycle']['app'])
    if app() == 0:
        check('native-menu-return-reacquires-owned-preset-and-original-baseline',
              value('z7_readout_preset') == 0 and owned_closed['information_base']['saved'] == 3)
        key('disp', lambda: app() == 13)
    key('menu', lambda: bool(pages()))
    setting('flag', 0, 0)
    off_menu = observe('lifecycle-master-off-while-menu-open')
    check('master-off-keeps-native-menu-open', bool(off_menu['information_lifecycle']['menu']))
    key('menu', lambda: not pages())
    restored = observe('lifecycle-master-off-menu-closed')
    check('menu-return-after-master-off-restores-native-user-page3', app() == 0 and
          restored['information_native_page'] == 3 and restored['information_lifecycle']['property'] == 3 and
          restored['information_lifecycle']['ledger'][0] == 0 and restored['information_base']['active'] == 0 and
          restored['information_masks'] == baseline['information_masks'])
    check('native-menu-roundtrips-do-not-produce-owned-transition-errors', value('z7_information_errors') == 0)
