"""Build a reproducible original-Z7 display module into a new private bundle.

SPDX-License-Identifier: MIT. No firmware distribution, card staging or camera
operations. The module requires the experimental display-capable Z7 host.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from build_z7_module import ROOT, HEADER, build, seal
from build_z7_module_host import ZIG


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--zig', type=Path, default=ZIG)
    parser.add_argument('--diagnostics', action='store_true', help='Also build ownership and initializer-failure audit modules')
    parser.add_argument('--variant', choices=('grids', 'battery-probe', 'battery-sample', 'battery-native', 'battery-percent', 'combined', 'clean-probe', 'disp-key-probe', 'settings-probe', 'settings-menu-probe', 'display-settings', 'display-readouts-probe', 'display-disp-probe', 'display-base-probe', 'display-histogram-probe', 'display-groups-probe', 'display-other-probe', 'gui-update-probe'), default='grids')
    parser.add_argument('--battery-percent', choices=('on', 'off'), help='Initial battery feature setting in its SD module')
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists():
        parser.error('Choose a new directory under .private')
    if args.diagnostics and args.variant not in ('grids', 'combined'):
        parser.error('Ownership diagnostic variants apply to grids or combined modules')
    if args.battery_percent is not None and args.variant not in ('battery-percent', 'combined'):
        parser.error('--battery-percent applies only to battery-percent or combined modules')
    relative, kind, minimum_api = {
        'grids': ('plugins/grids_histogram.c', 'original-Z7-grids-histogram-module', 20),
        'battery-probe': ('examples/battery_display_probe.c', 'original-Z7-battery-text-diagnostic', 16),
        'battery-sample': ('examples/battery_sample_probe.c', 'original-Z7-battery-sample-diagnostic', 12),
        'battery-native': ('examples/battery_native_display_probe.c', 'original-Z7-battery-native-sample-diagnostic', 16),
        'battery-percent': ('plugins/battery_percent.c', 'original-Z7-battery-percent-module', 16),
        'combined': ('plugins/combined_display.c', 'original-Z7-combined-display-module', 20),
        'clean-probe': ('examples/clean_display_probe.c', 'original-Z7-clean-display-diagnostic', 20),
        'disp-key-probe': ('examples/disp_key_probe.c', 'original-Z7-disp-key-diagnostic', 20),
        'settings-probe': ('examples/display_settings_probe.c', 'original-Z7-display-settings-diagnostic', 12),
        'settings-menu-probe': ('examples/settings_menu_probe.c', 'original-Z7-display-settings-menu-diagnostic', 20),
        'display-settings': ('examples/settings_menu_entry.c', 'original-Z7-display-settings-module', 20),
        'display-readouts-probe': ('examples/display_readouts_probe.c', 'original-Z7-display-readouts-diagnostic', 24),
        'display-disp-probe': ('examples/display_disp_probe.c', 'original-Z7-display-disp-diagnostic', 28),
        'display-base-probe': ('examples/display_base_probe.c', 'original-Z7-display-base-diagnostic', 28),
        'gui-update-probe': ('examples/gui_update_probe.c', 'original-Z7-gui-update-diagnostic', 32),
        'display-histogram-probe': ('examples/display_histogram_probe.c', 'original-Z7-display-histogram-diagnostic', 32),
        'display-groups-probe': ('examples/display_groups_probe.c', 'original-Z7-display-groups-diagnostic', 32),
        'display-other-probe': ('examples/display_other_probe.c', 'original-Z7-display-other-diagnostic', 32),
    }[args.variant]
    source = ROOT / 'z7-native-modules' / relative
    packet, report = build(source, zig=args.zig.resolve())
    again, second = build(source, zig=args.zig.resolve())
    if packet != again or report != second:
        raise RuntimeError('Display module is not reproducible')
    if args.variant in ('battery-percent', 'combined'):
        enabled = args.battery_percent != 'off'
        offset = report['symbols']['z7_battery_enabled']
        if offset % 4 or not 0 <= offset <= report['image_bytes'] - 4 or offset in report['relocations']:
            raise RuntimeError('Battery setting is not an owned initialized data word')
        if struct.unpack_from('<I', packet, HEADER + offset)[0] != 1:
            raise RuntimeError('Unexpected battery setting default')
        configured = bytearray(packet)
        struct.pack_into('<I', configured, HEADER + offset, int(enabled))
        packet = seal(configured)
        report['configuration'] = dict(battery_percent_enabled=enabled, scope='LCD photo; native battery visibility')
    report.update(kind=kind, emulator_only=True,
        module_sha256=hashlib.sha256(packet).hexdigest(), file_bytes=len(packet),
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        camera_verified=False, physical_card_verified=False, api_minimum_bytes=minimum_api)
    requested_variant = args.variant
    if requested_variant in ('display-groups-probe', 'display-other-probe'):
        # The six-group adapter includes the complete histogram/base stack.
        args.variant = 'display-histogram-probe'
        report['information_groups'] = dict(shutter=10, aperture=11, iso=15, shooting=5, release=51, focus=2)
        if requested_variant == 'display-other-probe':
            report['other_information_widgets'] = [3,6,7,8,9,13,14,16,17,26,27,34,38,41,44,46,50,53]
            report['readout_ownership_bits'] = 64
    inputs = [source, ROOT / 'z7-native-modules/sdk/module.h', ROOT / 'z7-native-modules/sdk/display.h',
              ROOT / 'z7-native-modules/sdk/module.ld']
    if args.variant in ('battery-sample', 'battery-native', 'battery-percent', 'combined', 'clean-probe', 'disp-key-probe', 'settings-menu-probe', 'display-settings', 'display-readouts-probe', 'display-disp-probe', 'display-base-probe', 'display-histogram-probe'):
        inputs.append(ROOT / 'z7-native-modules/plugins/battery_sample.h')
    if args.variant == 'battery-native':
        inputs.append(ROOT / 'z7-native-modules/examples/battery_display_probe.c')
    if args.variant in ('combined', 'clean-probe', 'disp-key-probe', 'settings-menu-probe', 'display-settings', 'display-readouts-probe', 'display-disp-probe', 'display-base-probe', 'display-histogram-probe'):
        inputs += [ROOT / 'z7-native-modules/plugins/grids_histogram.c', ROOT / 'z7-native-modules/plugins/battery_percent.c']
    if args.variant in ('clean-probe', 'disp-key-probe'):
        inputs += [ROOT / 'z7-native-modules/plugins/combined_display.c', ROOT / 'z7-native-modules/examples/clean_display_policy.h']
    if args.variant == 'settings-probe':
        inputs += [ROOT / 'z7-native-modules/plugins/display_settings.c', ROOT / 'z7-native-modules/plugins/display_settings.h']
    if args.variant in ('settings-menu-probe', 'display-settings', 'display-readouts-probe', 'display-disp-probe', 'display-base-probe', 'display-histogram-probe'):
        inputs += [ROOT / 'z7-native-modules/plugins/combined_display.c', ROOT / 'z7-native-modules/examples/settings_menu_policy.h',
                   ROOT / 'z7-native-modules/plugins/display_settings.c', ROOT / 'z7-native-modules/plugins/display_settings.h']
    if args.variant in ('display-readouts-probe', 'display-disp-probe', 'display-base-probe', 'display-histogram-probe'):
        inputs += [ROOT / 'z7-native-modules/examples/settings_menu_entry.c', ROOT / 'z7-native-modules/examples/display_readouts_policy.h', ROOT / 'z7-native-modules/sdk/update.h']
    if args.variant in ('display-disp-probe', 'display-base-probe', 'display-histogram-probe'):
        inputs += [ROOT / 'z7-native-modules/examples/display_readouts_probe.c', ROOT / 'z7-native-modules/examples/display_disp_policy.h', ROOT / 'z7-native-modules/sdk/disp.h']
    if args.variant in ('display-base-probe', 'display-histogram-probe'):
        inputs += [ROOT / 'z7-native-modules/examples/display_disp_probe.c', ROOT / 'z7-native-modules/examples/display_base_policy.h']
    if args.variant in ('gui-update-probe', 'display-histogram-probe'):
        inputs += [ROOT / 'z7-native-modules/sdk/gui.h', ROOT / 'z7-native-modules/sdk/disp.h', ROOT / 'z7-native-modules/sdk/update.h']
    if args.variant == 'display-histogram-probe':
        inputs += [ROOT / 'z7-native-modules/examples/display_base_probe.c', ROOT / 'z7-native-modules/examples/display_histogram_policy.h']
    if requested_variant in ('display-groups-probe', 'display-other-probe'):
        inputs.append(ROOT / 'z7-native-modules/examples/display_histogram_probe.c')
    if requested_variant == 'display-other-probe':
        inputs += [ROOT / 'z7-native-modules/examples/display_groups_probe.c', ROOT / 'z7-native-modules/examples/display_other_bindings.h']
    report['source_inputs_sha256'] = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    output.mkdir(parents=True)
    (output / 'Z7APP.BIN').write_bytes(packet)
    (output / 'module.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    if args.diagnostics:
        variants = [
            ('probes', 'success', 'examples/display_probe.c', None),
            ('probes', 'failure', 'examples/display_probe.c', 'Z7_DISPLAY_PROBE_FAIL'),
            ('probes', 'update-success', 'examples/update_probe.c', None),
            ('probes', 'update-failure', 'examples/update_probe.c', 'Z7_UPDATE_PROBE_FAIL'),
            ('probes', 'cycle-success', 'examples/disp_cycle_probe.c', None),
            ('probes', 'cycle-failure', 'examples/disp_cycle_probe.c', 'Z7_CYCLE_PROBE_FAIL'),
            ('probes', 'gui-success', 'examples/gui_update_probe.c', None),
            ('probes', 'gui-failure', 'examples/gui_update_probe.c', 'Z7_GUI_PROBE_FAIL'),
            ('failures', 'failed-init', 'plugins/grids_histogram.c', 'Z7_DISPLAY_MODULE_FAIL'),
            ('failures', 'foreign-controls', 'plugins/grids_histogram.c', 'Z7_DISPLAY_MENU_FOREIGN_CONTROLS'),
            ('failures', 'foreign-callback', 'plugins/grids_histogram.c', 'Z7_DISPLAY_MENU_BAD_CALLBACK'),
        ]
        for folder, name, relative, define in variants:
            directory = output / folder
            directory.mkdir(exist_ok=True)
            if args.variant == 'combined' and folder == 'failures': relative = 'plugins/combined_display.c'
            original = ROOT / 'z7-native-modules' / relative
            diagnostic_source = directory / (name + '.c')
            diagnostic_source.write_text(('#define ' + define + ' 1\n' if define else '') + '#include "' + original.as_posix() + '"\n',
                                         encoding='utf-8', newline='\n')
            diagnostic, metadata = build(diagnostic_source, zig=args.zig.resolve())
            repeat, repeated_metadata = build(diagnostic_source, zig=args.zig.resolve())
            if diagnostic != repeat or metadata != repeated_metadata:
                raise RuntimeError('Diagnostic module is not reproducible: ' + name)
            (directory / (name + '.BIN')).write_bytes(diagnostic)
            (directory / (name + '.json')).write_text(json.dumps(metadata, indent=2) + '\n',
                                                    encoding='utf-8', newline='\n')
    print(json.dumps(dict(module_bytes=len(packet), sha256=report['module_sha256'],
                         image=report['image_bytes'], bss=report['bss_bytes'], reproducible=True)))


if __name__ == '__main__':
    main()
