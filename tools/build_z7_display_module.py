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
    parser.add_argument('--variant', choices=('grid-restore-readonly-checkpoint', 'battery-grid-menu-checkpoint', 'battery-thirds-checkpoint', 'lcd-first-release', 'grids', 'battery-probe', 'battery-sample', 'focal-sample', 'battery-native', 'battery-percent', 'combined', 'clean-probe', 'disp-key-probe', 'settings-probe', 'settings-menu-probe', 'display-settings', 'display-readouts-probe', 'display-disp-probe', 'display-base-probe', 'display-histogram-probe', 'display-groups-probe', 'display-other-probe', 'display-focal-probe', 'gui-update-probe', 'information-host-probe', 'information-transition-probe', 'display-information-probe', 'worker-probe', 'settings-storage-probe', 'settings-files-probe', 'display-persistence-probe', 'display-highlight-context-probe', 'display-highlight-parameters-probe', 'display-highlight-owned-probe', 'display-highlight-frame-probe', 'display-highlight-cleanup-probe', 'display-highlight-cached-probe', 'display-highlight-coordinated-probe', 'display-highlight-native-transaction-probe', 'display-highlight-preferences-probe', 'display-highlight-evf-probe', 'display-highlight-handoff-probe'), default='grids')
    parser.add_argument('--battery-percent', choices=('on', 'off'), help='Initial battery feature setting in its SD module')
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists():
        parser.error('Choose a new directory under .private')
    if args.diagnostics and args.variant not in ('grids', 'combined'):
        parser.error('Ownership diagnostic variants apply to grids or combined modules')
    if args.battery_percent is not None and args.variant not in ('battery-percent', 'combined', 'battery-thirds-checkpoint', 'battery-grid-menu-checkpoint', 'grid-restore-readonly-checkpoint'):
        parser.error('--battery-percent applies only to configurable battery variants')
    relative, kind, minimum_api = {
        'grid-restore-readonly-checkpoint': ('plugins/grid_restore_readonly_checkpoint.c', 'original-Z7-grid-restore-readonly-checkpoint', 44),
        'battery-grid-menu-checkpoint': ('plugins/battery_grid_menu_checkpoint.c', 'original-Z7-battery-grid-menu-checkpoint', 20),
        'battery-thirds-checkpoint': ('plugins/battery_thirds_checkpoint.c', 'original-Z7-battery-thirds-checkpoint', 16),
        'lcd-first-release': ('plugins/lcd_release.c', 'original-Z7-LCD-first-release-candidate', 44),
        'grids': ('plugins/grids_histogram.c', 'original-Z7-grids-histogram-module', 20),
        'battery-probe': ('examples/battery_display_probe.c', 'original-Z7-battery-text-diagnostic', 16),
        'battery-sample': ('examples/battery_sample_probe.c', 'original-Z7-battery-sample-diagnostic', 12),
        'focal-sample': ('examples/focal_sample_probe.c', 'original-Z7-focal-sample-diagnostic', 12),
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
        'information-transition-probe': ('examples/information_transition_probe.c', 'original-Z7-information-transition-diagnostic', 12),
        'information-host-probe': ('examples/information_host_probe.c', 'original-Z7-information-host-diagnostic', 40),
        'worker-probe': ('examples/worker_probe.c', 'original-Z7-resident-worker-diagnostic', 44),
        'settings-storage-probe': ('examples/settings_storage_probe.c', 'original-Z7-settings-storage-diagnostic', 12),
        'settings-files-probe': ('examples/settings_files_probe.c', 'original-Z7-settings-files-diagnostic', 12),
        'display-histogram-probe': ('examples/display_histogram_probe.c', 'original-Z7-display-histogram-diagnostic', 32),
        'display-groups-probe': ('examples/display_groups_probe.c', 'original-Z7-display-groups-diagnostic', 32),
        'display-other-probe': ('examples/display_other_probe.c', 'original-Z7-display-other-diagnostic', 32),
        'display-information-probe': ('examples/display_information_probe.c', 'original-Z7-display-information-diagnostic', 40),
        'display-persistence-probe': ('examples/display_persistence_probe.c', 'original-Z7-display-persistence-diagnostic', 44),
        'display-highlight-context-probe': ('examples/display_highlight_context_probe.c', 'original-Z7-display-highlight-context-diagnostic', 48),
        'display-highlight-parameters-probe': ('examples/display_highlight_parameters_probe.c', 'original-Z7-display-highlight-parameters-diagnostic', 52),
        'display-highlight-owned-probe': ('examples/display_highlight_owned_probe.c', 'original-Z7-display-highlight-owned-diagnostic', 52),
        'display-highlight-frame-probe': ('examples/display_highlight_frame_probe.c', 'original-Z7-display-highlight-frame-diagnostic', 56),
        'display-highlight-cleanup-probe': ('examples/display_highlight_cleanup_probe.c', 'original-Z7-display-highlight-cleanup-diagnostic', 56),
        'display-highlight-cached-probe': ('examples/display_highlight_cached_probe.c', 'original-Z7-display-highlight-cached-diagnostic', 60),
        'display-highlight-coordinated-probe': ('examples/display_highlight_coordinated_probe.c', 'original-Z7-display-highlight-coordinated-diagnostic', 64),
        'display-highlight-native-transaction-probe': ('examples/display_highlight_native_transaction_probe.c', 'original-Z7-display-highlight-native-transaction-diagnostic', 72),
        'display-highlight-preferences-probe': ('examples/display_highlight_preferences_probe.c', 'original-Z7-display-highlight-preferences-diagnostic', 72),
        'display-highlight-evf-probe': ('examples/display_highlight_evf_probe.c', 'original-Z7-display-highlight-evf-diagnostic', 72),
        'display-highlight-handoff-probe': ('examples/display_highlight_handoff_probe.c', 'original-Z7-display-highlight-handoff-diagnostic', 80),
        'display-focal-probe': ('examples/display_focal_probe.c', 'original-Z7-display-focal-diagnostic', 32),
    }[args.variant]
    source = ROOT / 'z7-native-modules' / relative
    packet, report = build(source, zig=args.zig.resolve())
    again, second = build(source, zig=args.zig.resolve())
    if packet != again or report != second:
        raise RuntimeError('Display module is not reproducible')
    if args.variant in ('battery-percent', 'combined', 'battery-thirds-checkpoint', 'battery-grid-menu-checkpoint', 'grid-restore-readonly-checkpoint'):
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
    dependency_variant = 'display-persistence-probe' if requested_variant in ('lcd-first-release', 'display-highlight-context-probe', 'display-highlight-parameters-probe', 'display-highlight-owned-probe', 'display-highlight-frame-probe', 'display-highlight-cleanup-probe', 'display-highlight-cached-probe', 'display-highlight-coordinated-probe', 'display-highlight-native-transaction-probe', 'display-highlight-preferences-probe', 'display-highlight-evf-probe', 'display-highlight-handoff-probe') else requested_variant
    if dependency_variant in ('display-groups-probe', 'display-other-probe', 'display-focal-probe', 'display-information-probe', 'display-persistence-probe'):
        # The six-group adapter includes the complete histogram/base stack.
        args.variant = 'display-histogram-probe'
        report['information_groups'] = dict(shutter=10, aperture=11, iso=15, shooting=5, release=51, focus=2)
        if dependency_variant in ('display-other-probe', 'display-focal-probe', 'display-information-probe', 'display-persistence-probe'):
            report['other_information_widgets'] = [3,6,7,8,9,13,14,16,17,26,27,34,38,41,44,46,50,53]
            report['readout_ownership_bits'] = 64
    inputs = [source, ROOT / 'z7-native-modules/sdk/module.h', ROOT / 'z7-native-modules/sdk/display.h',
              ROOT / 'z7-native-modules/sdk/module.ld']
    if requested_variant == 'grid-restore-readonly-checkpoint':
        inputs.extend(ROOT / 'z7-native-modules/plugins' / n for n in ('battery_grid_menu_checkpoint.c', 'battery_percent.c', 'battery_sample.h', 'grids_histogram.c', 'grid_restore_record.h', 'settings_files.c', 'settings_files.h', 'settings_storage.h', 'display_settings.h'))
        inputs.extend(ROOT / 'z7-native-modules/sdk' / n for n in ('worker.h', 'information.h', 'gui.h', 'disp.h', 'update.h'))
        report['checkpoint_scope'] = 'One post-GUI read of Z7GRID.DAT, applied on grid-menu entry unless user selected first; no camera writes'
    if requested_variant == 'battery-grid-menu-checkpoint':
        inputs.extend(ROOT / 'z7-native-modules/plugins' / n for n in ('battery_percent.c', 'battery_sample.h', 'grids_histogram.c'))
        report['checkpoint_scope'] = 'Battery plus six volatile rear-photo-LCD grid choices; native stored grid remains Off/On; default thirds each reboot'
    if requested_variant == 'battery-thirds-checkpoint':
        inputs.extend(ROOT / 'z7-native-modules/plugins' / n for n in ('battery_percent.c', 'battery_sample.h'))
        report['checkpoint_scope'] = 'Battery plus native On/Off thirds on rear photo LCD; no custom menu/scalar/settings/worker'
    if requested_variant == 'focal-sample':
        inputs.append(ROOT / 'z7-native-modules/plugins/focal_sample.h')
    if requested_variant == 'information-transition-probe':
        inputs.append(ROOT / 'z7-native-modules/plugins/information_transition.h')
    if requested_variant in ('information-host-probe', 'worker-probe'):
        inputs.extend(ROOT / 'z7-native-modules/sdk' / name for name in ('information.h', 'gui.h', 'disp.h', 'update.h'))
    if requested_variant == 'worker-probe':
        inputs.append(ROOT / 'z7-native-modules/sdk/worker.h')
    if args.variant in ('battery-sample', 'battery-native', 'battery-percent', 'combined', 'clean-probe', 'disp-key-probe', 'settings-menu-probe', 'display-settings', 'display-readouts-probe', 'display-disp-probe', 'display-base-probe', 'display-histogram-probe'):
        inputs.append(ROOT / 'z7-native-modules/plugins/battery_sample.h')
    if args.variant == 'battery-native':
        inputs.append(ROOT / 'z7-native-modules/examples/battery_display_probe.c')
    if args.variant in ('combined', 'clean-probe', 'disp-key-probe', 'settings-menu-probe', 'display-settings', 'display-readouts-probe', 'display-disp-probe', 'display-base-probe', 'display-histogram-probe'):
        inputs += [ROOT / 'z7-native-modules/plugins/grids_histogram.c', ROOT / 'z7-native-modules/plugins/battery_percent.c']
    if args.variant in ('clean-probe', 'disp-key-probe'):
        inputs += [ROOT / 'z7-native-modules/plugins/combined_display.c', ROOT / 'z7-native-modules/examples/clean_display_policy.h']
    if args.variant in ('settings-probe', 'settings-storage-probe', 'settings-files-probe'):
        inputs += [ROOT / 'z7-native-modules/plugins/display_settings.c', ROOT / 'z7-native-modules/plugins/display_settings.h']
    if requested_variant in ('settings-storage-probe', 'settings-files-probe'):
        inputs += [ROOT / 'z7-native-modules/plugins/settings_storage.c', ROOT / 'z7-native-modules/plugins/settings_storage.h']
    if requested_variant == 'settings-files-probe':
        inputs += [ROOT / 'z7-native-modules/plugins/settings_files.c', ROOT / 'z7-native-modules/plugins/settings_files.h']
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
    if dependency_variant in ('display-groups-probe', 'display-other-probe', 'display-focal-probe', 'display-information-probe', 'display-persistence-probe'):
        inputs.append(ROOT / 'z7-native-modules/examples/display_histogram_probe.c')
    if dependency_variant in ('display-other-probe', 'display-focal-probe', 'display-information-probe', 'display-persistence-probe'):
        inputs += [ROOT / 'z7-native-modules/examples/display_groups_probe.c', ROOT / 'z7-native-modules/examples/display_other_bindings.h']
    if dependency_variant in ('display-focal-probe', 'display-information-probe', 'display-persistence-probe'):
        inputs += [ROOT / 'z7-native-modules/examples/display_other_probe.c', ROOT / 'z7-native-modules/examples/display_focal_policy.h', ROOT / 'z7-native-modules/plugins/focal_sample.h']
        report['focal_overlay_scope'] = 'LCD landscape custom presets; EVF and rotation remain open'
        report['focal_owned_slot'] = 1198
        report['focal_label_slot'] = 298
    if dependency_variant in ('display-information-probe', 'display-persistence-probe'):
        inputs += [ROOT / 'z7-native-modules/examples/display_focal_probe.c', ROOT / 'z7-native-modules/examples/display_information_policy.h', ROOT / 'z7-native-modules/plugins/information_transition.h', ROOT / 'z7-native-modules/sdk/information.h']
        report['information_app_index'] = 13
    if dependency_variant == 'display-persistence-probe':
        inputs += [ROOT / 'z7-native-modules/examples/display_information_probe.c', ROOT / 'z7-native-modules/examples/display_persistence_policy.h', ROOT / 'z7-native-modules/sdk/worker.h']
        inputs.extend(ROOT / 'z7-native-modules/plugins' / name for name in ('settings_storage.c', 'settings_storage.h', 'settings_files.c', 'settings_files.h'))
        report['configuration_storage'] = dict(record_bytes=80, slots=2, worker_api=44, physical_card_verified=False)
    if requested_variant in ('display-highlight-context-probe', 'display-highlight-parameters-probe', 'display-highlight-owned-probe', 'display-highlight-frame-probe', 'display-highlight-cleanup-probe', 'display-highlight-cached-probe', 'display-highlight-coordinated-probe', 'display-highlight-native-transaction-probe', 'display-highlight-preferences-probe', 'display-highlight-evf-probe', 'display-highlight-handoff-probe'):
        inputs.extend(ROOT / 'z7-native-modules' / name for name in (
            'examples/display_persistence_probe.c', 'examples/display_highlight_context_policy.h',
            'plugins/highlight_context.h', 'plugins/highlight_epoch.h', 'sdk/highlight.h'))
        report['highlight_scope'] = 'GUI epoch publication and source/worker observation only; no parameter submission or warning writes'
    if requested_variant in ('display-highlight-parameters-probe', 'display-highlight-owned-probe', 'display-highlight-frame-probe', 'display-highlight-cleanup-probe', 'display-highlight-cached-probe', 'display-highlight-coordinated-probe', 'display-highlight-native-transaction-probe', 'display-highlight-preferences-probe', 'display-highlight-evf-probe', 'display-highlight-handoff-probe'):
        inputs.extend(ROOT / 'z7-native-modules' / name for name in (
            'examples/display_highlight_context_probe.c', 'sdk/parameters.h'))
        report['highlight_scope'] = 'Eligible native photo payload conversion; no owned requests, source flag writes, restoration or warning pixels accepted'
    if requested_variant in ('display-highlight-owned-probe', 'display-highlight-frame-probe', 'display-highlight-cleanup-probe', 'display-highlight-cached-probe', 'display-highlight-coordinated-probe', 'display-highlight-native-transaction-probe', 'display-highlight-preferences-probe', 'display-highlight-evf-probe', 'display-highlight-handoff-probe'):
        inputs.extend(ROOT / 'z7-native-modules' / name for name in (
            'examples/display_highlight_parameters_probe.c', 'examples/display_highlight_owned_policy.h',
            'plugins/highlight_request.h', 'plugins/highlight_lease.h'))
        report['highlight_scope'] = 'Native and owned photo parameters with generation-qualified lease/restore/disable; frame permissions remain native'
    if requested_variant in ('display-highlight-frame-probe', 'display-highlight-cleanup-probe', 'display-highlight-cached-probe', 'display-highlight-coordinated-probe', 'display-highlight-native-transaction-probe', 'display-highlight-preferences-probe', 'display-highlight-evf-probe', 'display-highlight-handoff-probe'):
        inputs.extend(ROOT / 'z7-native-modules' / name for name in ('examples/display_highlight_owned_probe.c', 'sdk/frame_permission.h'))
        report['highlight_scope'] = 'Owned/native parameter lease and consumption-time primary frame permission; pending frame data untouched; physical pixels unverified'
    if requested_variant in ('display-highlight-cleanup-probe', 'display-highlight-cached-probe', 'display-highlight-coordinated-probe', 'display-highlight-native-transaction-probe', 'display-highlight-preferences-probe', 'display-highlight-evf-probe', 'display-highlight-handoff-probe'):
        inputs.extend(ROOT / 'z7-native-modules' / name for name in ('examples/display_highlight_frame_probe.c', 'examples/display_highlight_cleanup_policy.h'))
        report['highlight_scope'] = 'API56 frame gating plus qualified native-consumer no-frame restoration and register verification; physical pixels unverified'
    if requested_variant in ('display-highlight-cached-probe', 'display-highlight-coordinated-probe', 'display-highlight-native-transaction-probe', 'display-highlight-preferences-probe', 'display-highlight-evf-probe', 'display-highlight-handoff-probe'):
        inputs.extend(ROOT / 'z7-native-modules' / name for name in ('examples/display_highlight_cleanup_probe.c', 'sdk/cached_frame_permission.h'))
        report['highlight_scope'] = 'API60 native cached metadata and NULL gate refresh filtering plus API56 cleanup; native cross-lane serialization remains unproven'
    if requested_variant in ('display-highlight-coordinated-probe', 'display-highlight-native-transaction-probe', 'display-highlight-preferences-probe', 'display-highlight-evf-probe', 'display-highlight-handoff-probe'):
        inputs.extend(ROOT / 'z7-native-modules' / name for name in ('examples/display_highlight_cached_probe.c', 'sdk/owned_frame_coordination.h'))
        report['highlight_scope'] = 'API64 whole primary-frame / module-owned parameter exclusion; foreign native parameter writers, engine lifetime and generation exhaustion shutdown remain open'
    if requested_variant in ('display-highlight-native-transaction-probe', 'display-highlight-preferences-probe', 'display-highlight-evf-probe', 'display-highlight-handoff-probe'):
        inputs.extend(ROOT / 'z7-native-modules' / name for name in ('examples/display_highlight_coordinated_probe.c', 'sdk/native_warning_transaction.h'))
        report['highlight_scope'] = 'API72 warning-gate and owned/foreign parameter transactions; caller closure, native math/task scheduling and engine lifetime remain open'
    if requested_variant in ('display-highlight-preferences-probe', 'display-highlight-evf-probe', 'display-highlight-handoff-probe'):
        inputs.append(ROOT / 'z7-native-modules/examples/display_highlight_native_transaction_probe.c')
        report['highlight_preferences'] = dict(patterns=3, thresholds=[255,248,235,224,213,202,191,180], global_preferences=True, settings_payload_version=2, legacy_v1_defaults=[1,1])
        report['highlight_scope'] = 'API72 LCD photo highlight preferences, epoch-qualified owned/native conversion and version2 persistent settings; hardware pixels/EVF/orientation remain open'
    if requested_variant in ('display-highlight-evf-probe', 'display-highlight-handoff-probe'):
        inputs.append(ROOT / 'z7-native-modules/examples/display_highlight_preferences_probe.c')
        report['highlight_evf_native_update_required'] = True
        report['highlight_scope'] = 'API72 dual logical output highlight conversion after matching native baseline updates; no automatic unobserved baseline import or physical EVF proof'
    if requested_variant == 'display-highlight-handoff-probe':
        inputs.extend(ROOT / 'z7-native-modules' / name for name in (
            'examples/display_highlight_evf_probe.c', 'examples/display_highlight_handoff_policy.h', 'sdk/native_cache.h'))
        report['highlight_cache_handoff'] = True
        report['highlight_evf_native_update_required'] = False
        report['highlight_scope'] = 'API80 cache-driven logical LCD/EVF handoff with separate native origins; native boot/writer/index/lifetime closure and physical pixels unproven'
    if requested_variant == 'lcd-first-release':
        inputs.append(ROOT / 'z7-native-modules/plugins/lcd_release_policy.h')
        report.pop('information_app_index', None)
        report['release_scope'] = dict(presets=4, outputs='landscape photo LCD',
            included=['grids', 'native horizon', 'information groups', 'battery percentage', 'focal display', 'settings persistence'],
            deferred=['custom Info page', 'custom histogram', 'photo highlights', 'portrait', 'EVF/external extensions'],
            configuration='Existing v1 journal; unsupported components/page removed after load and before edits commit',
            installation_candidate_cleared=False)
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
            ('probes', 'information-success', 'examples/information_host_probe.c', None),
            ('probes', 'information-failure', 'examples/information_host_probe.c', 'Z7_INFORMATION_PROBE_FAIL'),
            ('probes', 'worker-success', 'examples/worker_probe.c', None),
            ('probes', 'worker-failure', 'examples/worker_probe.c', 'Z7_WORKER_PROBE_FAIL'),
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
