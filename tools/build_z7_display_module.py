"""Build a reproducible original-Z7 display module into a new private bundle.

SPDX-License-Identifier: MIT. No firmware distribution, card staging or camera
operations. The module requires the experimental display-capable Z7 host.
"""
import argparse
import hashlib
import json
from pathlib import Path

from build_z7_module import ROOT, build
from build_z7_module_host import ZIG


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--zig', type=Path, default=ZIG)
    parser.add_argument('--diagnostics', action='store_true', help='Also build ownership and initializer-failure audit modules')
    parser.add_argument('--variant', choices=('grids', 'battery-probe', 'battery-sample', 'battery-native'), default='grids')
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists():
        parser.error('Choose a new directory under .private')
    if args.diagnostics and args.variant != 'grids':
        parser.error('Ownership diagnostic variants apply to the grid module')
    relative, kind, minimum_api = {
        'grids': ('plugins/grids_histogram.c', 'original-Z7-grids-histogram-module', 20),
        'battery-probe': ('examples/battery_display_probe.c', 'original-Z7-battery-text-diagnostic', 16),
        'battery-sample': ('examples/battery_sample_probe.c', 'original-Z7-battery-sample-diagnostic', 12),
        'battery-native': ('examples/battery_native_display_probe.c', 'original-Z7-battery-native-sample-diagnostic', 16),
    }[args.variant]
    source = ROOT / 'z7-native-modules' / relative
    packet, report = build(source, zig=args.zig.resolve())
    again, second = build(source, zig=args.zig.resolve())
    if packet != again or report != second:
        raise RuntimeError('Display module is not reproducible')
    report.update(kind=kind, emulator_only=True,
        module_sha256=hashlib.sha256(packet).hexdigest(), file_bytes=len(packet),
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        camera_verified=False, physical_card_verified=False, api_minimum_bytes=minimum_api)
    inputs = [source, ROOT / 'z7-native-modules/sdk/module.h', ROOT / 'z7-native-modules/sdk/display.h',
              ROOT / 'z7-native-modules/sdk/module.ld']
    if args.variant in ('battery-sample', 'battery-native'):
        inputs.append(ROOT / 'z7-native-modules/plugins/battery_sample.h')
    if args.variant == 'battery-native':
        inputs.append(ROOT / 'z7-native-modules/examples/battery_display_probe.c')
    report['source_inputs_sha256'] = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    output.mkdir(parents=True)
    (output / 'Z7APP.BIN').write_bytes(packet)
    (output / 'module.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    if args.diagnostics:
        variants = [
            ('probes', 'success', 'examples/display_probe.c', None),
            ('probes', 'failure', 'examples/display_probe.c', 'Z7_DISPLAY_PROBE_FAIL'),
            ('failures', 'failed-init', 'plugins/grids_histogram.c', 'Z7_DISPLAY_MODULE_FAIL'),
            ('failures', 'foreign-controls', 'plugins/grids_histogram.c', 'Z7_DISPLAY_MENU_FOREIGN_CONTROLS'),
            ('failures', 'foreign-callback', 'plugins/grids_histogram.c', 'Z7_DISPLAY_MENU_BAD_CALLBACK'),
        ]
        for folder, name, relative, define in variants:
            directory = output / folder
            directory.mkdir(exist_ok=True)
            original = ROOT / 'z7-native-modules' / relative
            diagnostic_source = directory / (name + '.c')
            diagnostic_source.write_text(('#define ' + define + ' 1\n' if define else '') + original.read_text(),
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
