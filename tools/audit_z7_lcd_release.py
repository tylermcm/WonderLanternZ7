"""LCD first-release menu scope, legacy settings filtering and persistence (MIT).

Executes actual loader/module/menu callbacks and journal/file wrappers. Kernel,
filesystem and menu rendering services are supplied; no visual, real card, full
lifecycle, installation or recovery acceptance is established.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from audit_z7_display_persistence import PersistenceFixture
from audit_z7_settings_files import PATHS
from audit_z7_settings_storage import record
from build_z7_module_host import ROOT, STATE

OBJECT = 0xa1833548
DEFAULTS = (0, 15, 1, 0, 5, 0, 127, 7, 0, 127)


def audit(raw, host, packet, module):
    assert hashlib.sha256(raw).hexdigest() == host['main_payload_sha256']
    assert hashlib.sha256(packet).hexdigest() == module['module_sha256']
    symbols = module['symbols']
    checks = []

    def check(name, good):
        assert good, name
        checks.append(name)

    def load(files=None):
        f = PersistenceFixture(raw, host, packet, files)
        status = f.call(host['symbols']['z7_module_load_once'], STATE)
        f.base = f.words()[12]
        f.setword(40, status)
        check('load-' + str(len(checks)), status == 8)
        # This instruction fixture supplies native renderer readiness. The live
        # QEMU probe separately verifies the actual before-paint publication.
        f.write(f.base + symbols['sm_lcd_rows_ready'], 1)
        return f

    def word(f, name):
        return f.read(f.base + symbols[name])

    def model(f):
        return struct.unpack('<10I', f.u.mem_read(f.base + symbols['z7_menu_settings'], 40))

    def call(f, name, *args):
        return f.call(f.base + symbols[name], *args)

    def action(f, row):
        f.u.mem_write(OBJECT + 22, struct.pack('<2H', row, 0))
        before = list(f.file_events)
        call(f, 'sm_activate')
        check('menu-action-no-io-' + str(len(checks)), f.file_events == before)

    def rows(f, count):
        return word(f, 'sm_geometry') == 7 and f.read(f.base + symbols['sm_meta'] + 20) == (count | 7 << 16)

    def labels(f):
        return dict(f.menu_labels)

    def tick(f):
        for _ in range(5):
            f.call(host['symbols']['z7_module_worker_tick'])

    f = load()
    check('four-supported-default-presets', model(f) == DEFAULTS)
    check('no-native-information-hook-registration', f.words()[44] == f.words()[46] == 0 and f.words()[50] == 1)
    check('information-transition-code-not-linked', not any(n.startswith('z7_information_') for n in symbols))
    call(f, 'sm_render', OBJECT)
    check('compact-root-controls', rows(f, 6) and [labels(f)[231+i] for i in range(6)] ==
          ['Custom pages', 'Standard', 'Minimal', 'Composition', 'Exposure', 'Battery percentage'])
    before = model(f)
    action(f, 6)
    check('out-of-range-root-action-ignored', model(f) == before)
    action(f, 0)
    action(f, 5)
    check('master-and-battery-toggle-without-info-page', model(f)[:2] == (3, 15) and word(f, 'z7_battery_enabled') == 1)
    action(f, 1)
    check('compact-preset-controls', rows(f, 5) and [labels(f)[231+i] for i in range(5)] ==
          ['Page enabled', 'Shooting information', 'Framing grid', 'Virtual horizon', 'Reset preset'])
    action(f, 3)
    check('compact-horizon-action-maps-correctly', model(f)[2] == 5)
    action(f, 4)
    check('compact-reset-restores-supported-default', model(f)[2] == 1 and all(not x & 10 for x in model(f)[2:6]))
    action(f, 1)
    check('six-native-information-groups-and-more', rows(f, 7))
    action(f, 6)
    check('compact-extra-controls', rows(f, 3) and [labels(f)[231+i] for i in range(3)] == ['Other information', 'Focal length', 'Back'])
    action(f, 1)
    check('focal-choice-retained', model(f)[6] == 255)
    action(f, 2)
    check('compact-back-returns-to-information', word(f, 'z7_settings_view') == 2 and rows(f, 7))
    call(f, 'sm_back_event')
    call(f, 'sm_back_event')
    check('back-returns-to-compact-root', word(f, 'z7_settings_view') == 0 and rows(f, 6))
    check('unsupported-controls-not-present', not any(text in ('Histogram', 'Photo highlights', 'Information display') for _, text in f.menu_labels))
    saved = model(f)
    tick(f)
    check('worker-saves-supported-model', word(f, 'z7_persistence_saves') == 1 and record(saved, 0) in f.files.values())
    restarted = load(dict(f.files))
    check('restart-restores-menu-and-battery-preferences', model(restarted) == saved and word(restarted, 'z7_battery_enabled') == 1)
    legacy = (3, 16, 15, 10, 8, 2, 255, 7, 0, 127)
    original = record(legacy, 7)
    migrated = load({PATHS[0]: original})
    expected = (3, 1, 5, 0, 0, 0, 255, 7, 0, 127)
    check('legacy-info-only-and-unsupported-components-filtered', model(migrated) == expected)
    check('startup-filter-does-not-write-files', not any(e[0] == 'write' for e in migrated.file_events) and migrated.files[PATHS[0]] == original)
    check('filtered-load-marked-dirty', word(migrated, 'z7_settings_revision') == 2)
    tick(migrated)
    check('normalization-saved-to-other-journal-slot', migrated.files[PATHS[0]] == original and migrated.files[PATHS[1]] == record(expected, 8))
    again = load(dict(migrated.files))
    check('normalized-restart-is-stable', model(again) == expected and word(again, 'z7_settings_revision') == 0)
    cycle = load()
    call(cycle, 'z7_settings_flag', cycle.base + symbols['z7_menu_settings'], 0, 1)
    for expected_preset in (1, 2, 3, 0):
        cycle.call(0x1030da56, 0x29)
        check('native-disp-selects-' + str(expected_preset), word(cycle, 'z7_readout_preset') == expected_preset)
        cycle.call(host['symbols']['z7_display_before_update'])
    for preset in (0, 2):
        call(cycle, 'z7_settings_page', cycle.base + symbols['z7_menu_settings'], preset, 0)
    for expected_preset in (1, 3, 1):
        cycle.call(0x1030da56, 0x29)
        check('native-disp-skips-disabled-to-' + str(expected_preset), word(cycle, 'z7_readout_preset') == expected_preset)
    for label, address, data in (
        ('movie', 0xa201d510, b'\1'), ('evf', 0xa18237c6, b'\2'),
        ('menu', 0xa2c41008, struct.pack('<I', 1))):
        saved_bytes = bytes(cycle.u.mem_read(address, len(data)))
        cycle.u.mem_write(address, data)
        previous = word(cycle, 'z7_preset_cycles')
        cycle.call(0x1030da56, 0x29)
        check(label + '-does-not-consume-custom-cycle', word(cycle, 'z7_preset_cycles') == previous)
        cycle.u.mem_write(address, saved_bytes)
    return dict(schema=1, passed=True, checks=len(checks), check_names=checks,
                scope='Actual API44 load, compact menu callbacks/count metadata, supported defaults, battery/focal switches, reset, worker save/restart, v1 legacy normalization and native DISP cycling/page skipping/context fallback',
                limits=['UI rendering services supplied; compact menu needs native visual/lifecycle validation',
                        'No complete overlay/output/capture lifecycle or physical card validation',
                        'Not an installation-cleared candidate'], installation_candidate=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('build', 'module', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():
        parser.error('Choose a new private output')
    raw = (args.build/'module-host.emulator.main.bin').read_bytes()
    host = json.loads((args.build/'module-host.emulator.json').read_text())
    packet = (args.module/'Z7APP.BIN').read_bytes()
    module = json.loads((args.module/'module.json').read_text())
    result = audit(raw, host, packet, module)
    names = ('audit_z7_lcd_release', 'audit_z7_display_persistence', 'audit_z7_settings_files', 'audit_z7_settings_storage',
             'audit_z7_display_information', 'audit_z7_focal_overlay', 'audit_z7_histogram_component', 'audit_z7_module_host', 'audit_splash_image')
    result.update(module_sha256=module['module_sha256'], host_sha256=host['main_payload_sha256'],
                  source_sha256={**host['source_files'], **module['source_inputs_sha256'],
                      **{'tools/'+n+'.py':hashlib.sha256((ROOT/'tools'/(n+'.py')).read_bytes()).hexdigest() for n in names}})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('check_names', 'source_sha256')}))


if __name__ == '__main__':
    main()
