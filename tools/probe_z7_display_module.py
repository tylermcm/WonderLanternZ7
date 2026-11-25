"""Native-key menus or live pixels for the loaded original-Z7 display module.

SPDX-License-Identifier: MIT. Assisted QEMU, explicit read-only file-service HLE,
synthetic sensor/calibration inputs. No physical card/camera or flash operations.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import threading
import time

from PIL import Image, ImageChops
from build_z7_module_host import ROOT, STATE, validate_candidate
from probe_z7_module_host import HostCamera, bind_module_fixture, ui
from cmos_config import active_manifest, active_ingress

LAYOUTS = [('fourths', 1, 3), ('thirds', 2, 2), ('golden', 3, 2), ('center', 4, 1), ('dense', 5, 5), ('off', 0, 0)]


class DisplayCamera(HostCamera):
    def pause(self):
        # A getter breakpoint can already be queued when the caller requests a
        # pause. Return that stop without auto-resuming it through the fixture.
        active = getattr(getattr(self, 'remote', None), 'histogram_enabled', False)
        if active: self.remote.histogram_pause_requested = True
        try:
            if self.running and getattr(self.remote, 'fixture_enabled', False):
                self.remote.request_fixture_stop()
                self.receive_stop()
                return
            return super().pause()
        finally:
            if active: self.remote.histogram_pause_requested = False

    def call(self, packet, name, function, payload, arguments):
        if name == 'Waiting for the native display':
            arguments = [getattr(self, 'native_display_wait_ms', 100)]
        return super().call(packet, name, function, payload, arguments)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--module', type=Path, required=True)
    parser.add_argument('--view', choices=('menu', 'live', 'inspect', 'battery', 'battery-auto', 'clean', 'disp-input', 'disp-admission', 'disp-key', 'settings-menu', 'settings-entry', 'settings-root', 'settings-battery', 'readouts', 'disp-presets', 'gui-update', 'histogram', 'information-groups', 'focal'), required=True)
    parser.add_argument('--root-label-loss-fixture', action='store_true', help='Explicit GUI-side empty-name/cache fault, with old/new control; settings-root only')
    parser.add_argument('--histogram-preset-menu', action='store_true', help='Exercise integrated Histogram + Virtual horizon preset controls; settings-root only')
    parser.add_argument('--information-page-menu', action='store_true', help='Exercise the opt-in full Information display and relocated battery switch; settings-root only')
    parser.add_argument('--battery-icon-fixture', action='store_true', help='Supply one native icon visibility request for the automatic GUI test')
    parser.add_argument('--battery-source-fixture', action='store_true', help='Supply typed bar inputs at the native converter; LCD candidate battery-auto only, not physical telemetry')
    parser.add_argument('--settings-battery-control', action='store_true', help='Record startup separately and enter/leave native settings while disabled before qualifying the battery baseline')
    parser.add_argument('--grid-components', action='store_true', help='For the base-page DISP probe, set a native golden grid and verify component suppression and same-page edits')
    parser.add_argument('--information-horizon', action='store_true', help='For information-groups, verify selected native information on the horizon base')
    parser.add_argument('--focal-horizon', action='store_true', help='For focal view, validate focal text with the native horizon base')
    parser.add_argument('--focal-horizon-control', action='store_true', help='For focal view, isolate Other OFF/ON on horizon with focal never enabled')
    parser.add_argument('--information-native-control', action='store_true', help='For focal view, observe original information-page DISP entry/return with custom settings inactive')
    parser.add_argument('--information-routing', action='store_true', help='For focal view, exercise full five-choice native-information routing')
    parser.add_argument('--information-lifecycle', action='store_true', help='For focal view, compare native MENU lifecycle with owned information routing')
    parser.add_argument('--graphics-information', action='store_true', help='Capture settled native information refresh and repeated MENU controls; requires information-native-control')
    parser.add_argument('--graphics-api-trace', action='store_true', help='Observe bounded native OpenVG entry arguments; requires information-native-control')
    parser.add_argument('--other-information', action='store_true', help='For information-groups, toggle the independently identified Other status group')
    parser.add_argument('--battery-lifecycle', action='store_true', help='Also exercise native MENU entry/return with the automatic overlay')
    parser.add_argument('--battery-playback', action='store_true', help='Also inspect native no-card PLAY entry/return; requires battery lifecycle')
    parser.add_argument('--histogram-context-fixture', action='store_true',
                        help='Explicitly supply native histogram context 1; not a camera-derived observation')
    parser.add_argument('--histogram-sample-fixture', action='store_true',
                        help='Supply bins only to the owned module getter boundary; histogram view only, not real statistics')
    parser.add_argument('--trace-histogram-writes', action='store_true', help='Record bounded native histogram control watchpoints')
    parser.add_argument('--trace-histogram-context', action='store_true', help='Observe native context producer instead of widget stores')
    parser.add_argument('--battery-text-trial', action='store_true', help='Diagnostic native text object with supplied 63 percent; inspect view only')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.root_label_loss_fixture and args.view != 'settings-root':
        parser.error('Root label-loss fixture requires settings-root view')
    if args.histogram_preset_menu and (args.view != 'settings-root' or args.root_label_loss_fixture):
        parser.error('Histogram preset menu requires settings-root without the label-loss fixture')
    if args.information_page_menu and (args.view != 'settings-root' or args.root_label_loss_fixture or args.histogram_preset_menu):
        parser.error('Information page menu requires settings-root without another menu fixture')
    if args.focal_horizon and args.view != 'focal':
        parser.error('Focal horizon requires focal view')
    if args.focal_horizon_control and (args.view != 'focal' or args.focal_horizon):
        parser.error('Focal horizon control requires focal view without focal-horizon')
    if args.information_native_control and (args.view != 'focal' or args.focal_horizon or args.focal_horizon_control):
        parser.error('Native information control requires focal view without focal horizon modes')
    if args.information_horizon and args.view != 'information-groups':
        parser.error('Information horizon requires information-groups view')
    if args.information_routing and (args.view != 'focal' or args.information_native_control or
                                    args.focal_horizon_control or args.focal_horizon):
        parser.error('Information routing requires focal view without other focal/control modes')
    if args.information_lifecycle and (args.view != 'focal' or args.information_routing or args.information_native_control or
                                      args.focal_horizon_control or args.focal_horizon):
        parser.error('Information lifecycle requires focal view without other focal/control modes')
    if args.graphics_information and (args.view != 'focal' or not args.information_native_control):
        parser.error('Graphics information capture requires focal view with information-native-control')
    if args.graphics_api_trace and (args.view != 'focal' or not args.information_native_control or args.graphics_information):
        parser.error('Graphics API observation requires information-native-control without graphics-information')
    if args.other_information and args.view != 'information-groups':
        parser.error('Other information requires information-groups view')
    if args.histogram_context_fixture and args.view != 'live':
        parser.error('Histogram context fixture requires live view')
    if args.histogram_sample_fixture and args.view != 'histogram':
        parser.error('Supplied histogram samples require histogram view')
    if args.battery_text_trial and args.view != 'inspect':
        parser.error('Battery text trial requires inspect view')
    if args.battery_icon_fixture and args.view not in ('battery-auto', 'settings-battery'):
        parser.error('Battery icon fixture requires battery-auto or settings-battery view')
    if args.battery_source_fixture and not (args.view == 'battery-auto' and args.battery_icon_fixture):
        parser.error('Battery source fixture requires battery-auto and explicit icon fixture')
    if args.view == 'settings-battery' and not args.battery_icon_fixture:
        parser.error('Settings-battery requires its explicit icon fixture')
    if args.settings_battery_control and args.view != 'settings-battery':
        parser.error('Settings battery control requires settings-battery view')
    if args.grid_components and args.view != 'disp-presets':
        parser.error('Grid component validation requires disp-presets view')
    if args.battery_lifecycle and not (args.view == 'battery-auto' and args.battery_icon_fixture):
        parser.error('Battery lifecycle requires battery-auto with its explicit icon fixture')
    if args.battery_playback and not args.battery_lifecycle:
        parser.error('Battery playback requires battery lifecycle')
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists():
        parser.error('Choose a new private evidence directory')
    output.mkdir(parents=True)
    probe_source = Path(__file__).read_bytes()
    (output / 'probe-source.py').write_bytes(probe_source)
    ui.FIRMWARE = args.build / 'module-host.emulator.main.bin'
    ui.FIRMWARE_REPORT = args.build / 'module-host.emulator.json'
    ui.STOCK_CONTAINER = ROOT / '.private/stock/Z_7_0380.bin'
    ui.validate_firmware = validate_candidate
    host = json.loads(ui.FIRMWARE_REPORT.read_text())
    module = json.loads((args.module / 'module.json').read_text())
    packet = (args.module / 'Z7APP.BIN').read_bytes()
    if hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Module fingerprint mismatch')
    settings_root = module['kind'] == 'original-Z7-LCD-settings-root-checkpoint'
    if args.view == 'settings-root' and not settings_root:
        raise ValueError('Settings root checkpoint required')
    lcd_release = module['kind'] == 'original-Z7-LCD-first-release-candidate' or settings_root
    fixture = bind_module_fixture(output, packet, host, settings=lcd_release,
        settings_paths=(b'A:\\Z7CFG0.DAT', b'A:\\Z7CFG1.DAT', b'A:\\Z7DSP0.DAT', b'A:\\Z7DSP1.DAT') if settings_root else None)
    bar_fixture = None
    if args.battery_source_fixture:
        if not lcd_release:
            raise ValueError('Battery source fixture requires the persistent LCD candidate')
        from battery_bar_fixture import BatteryBarFixture, battery_bar_remote, POINT
        source = Path(__file__).with_name('battery_bar_fixture.py').read_bytes()
        (output / 'battery-bar-fixture-source.py').write_bytes(source)
        with ui.FIRMWARE.open('rb') as incoming:
            incoming.seek(POINT - 0x10020000)
            bar_fixture = BatteryBarFixture(incoming.read(2))
        ui.Remote = battery_bar_remote(ui.Remote, bar_fixture)
    if args.graphics_api_trace:
        from graphics_api_observer import observing_remote
        source = Path(__file__).with_name('graphics_api_observer.py').read_bytes()
        (output / 'graphics-api-observer-source.py').write_bytes(source)
        ui.Remote = observing_remote(ui.Remote, output)
    sample_fixture = None
    fixture_source_hash = None
    if args.histogram_sample_fixture:
        from histogram_sample_fixture import HistogramSampleFixture, sample_remote, histogram_scanout_box
        fixture_source = Path(__file__).with_name('histogram_sample_fixture.py').read_bytes()
        (output / 'histogram-fixture-source.py').write_bytes(fixture_source)
        fixture_source_hash = hashlib.sha256(fixture_source).hexdigest()
        ui.Remote = sample_remote(ui.Remote)
    options = {} if args.view in ('menu', 'settings-menu', 'settings-entry', 'settings-root') else dict(capture_control_test=True,
        raw_source=active_manifest('native0'), exmcu_no_lens=True, tg_periodic_test=True,
        tg_paired_test=True, raw_ingress_test=active_ingress(), isp_boundary_test=True,
        orientation_fixture=0, keep_awake=True, photo_liveview=True)
    camera = DisplayCamera(0, profile='menu' if args.view == 'menu' else 'shooting', **options)
    if args.information_lifecycle or args.graphics_information:
        camera.gpu_draw_dump = output / 'graphics-draws'
        camera.gpu_draw_dump.mkdir()
        camera.gpu_draw_gate = output / 'graphics-capture.enabled'
    if args.view in ('battery-auto', 'settings-battery', 'readouts', 'disp-presets', 'gui-update', 'histogram', 'information-groups', 'focal'):
        # Retain the base fixture's native StartLV settling delay before MENU.
        # Acknowledgement alone can precede the first completed native draw.
        camera.native_display_wait_ms = 5000
    result = dict(view=args.view, checks=[], steps=[], module_sha256=module['module_sha256'],
        main_sha256=host['main_payload_sha256'], modeled_module_file=True, camera_access=False, physical_card=False,
        supplied_histogram_context=args.histogram_context_fixture,
        modeled_settings_files=lcd_release)
    result['probe_script_sha256'] = hashlib.sha256(probe_source).hexdigest()
    if fixture_source_hash: result['histogram_fixture_source_sha256'] = fixture_source_hash
    if args.view == 'information-groups':
        geometry_source = Path(__file__).with_name('display_pixel_geometry.py').read_bytes()
        (output / 'geometry-source.py').write_bytes(geometry_source)
        result['information_geometry_source_sha256'] = hashlib.sha256(geometry_source).hexdigest()
    if args.view in ('battery-auto', 'settings-battery', 'readouts', 'disp-presets', 'gui-update', 'histogram', 'information-groups', 'focal'): result['native_start_lv_display_wait_ms'] = camera.native_display_wait_ms
    def save():
        (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    def check(name, passed):
        result['checks'].append(dict(name=name, passed=bool(passed)))
        save()
        if not passed:
            raise AssertionError(name)
    def checkpoint():
        if camera.running:
            camera.pause()
        return camera.run_to(0x100531bc)
    def advance(seconds=.3):
        if getattr(camera.remote, 'fixture_enabled', False):
            # Persistent settings keep the filesystem observation point live.
            # Pump it while running; a sleep with no receive can strand the
            # guest at DISPATCH. Match the proven persistence-probe wait.
            if camera.running: camera.pause()
            camera.remote.fixture_stop_requested = False
            timer = threading.Timer(seconds, camera.remote.request_fixture_stop)
            timer.daemon = True
            camera.remote.send('c'); camera.running = True
            timer.start()
            try:
                camera.receive_stop()
            finally:
                timer.cancel(); timer.join(1)
                camera.remote.fixture_stop_requested = False
            return checkpoint()
        if not camera.running:
            camera.continue_guest()
        time.sleep(seconds)
        return checkpoint()
    def state():
        return struct.unpack('<64I', camera.remote.memory(STATE, 256))
    def pages():
        p = int.from_bytes(camera.remote.memory(0xa181f91c, 4), 'little')
        stride, capacity, count, data = struct.unpack('<4I', camera.remote.memory(p, 16))
        if not 0 <= count <= min(capacity, 20) or not 4 <= stride <= 1024:
            raise ValueError('Unexpected native page list')
        rows = []
        for i in range(count):
            page = int.from_bytes(camera.remote.memory(data + i * stride, 4), 'little')
            kind = int.from_bytes(camera.remote.memory(page, 4), 'little') >> 16
            a, b = struct.unpack('<HH', camera.remote.memory(page + 22, 4))
            rows.append(dict(page=kind, row=a + b))
        return rows
    def on_page(number):
        path = pages()
        return bool(path) and path[-1]['page'] == number
    def key(name, predicate):
        for _ in range(3):
            advance(.2)
            camera.key(checkpoint(), name)
            for _ in range(12):
                advance(.3)
                if predicate():
                    return
        raise RuntimeError('Native key did not reach expected state: ' + name)
    def row(page, target):
        check('row-on-page-' + hex(page), on_page(page))
        for _ in range(60):
            current = pages()[-1]['row']
            if current == target:
                return
            following = current + (1 if current < target else -1)
            key('down' if current < target else 'up', lambda: on_page(page) and pages()[-1]['row'] == following)
        raise RuntimeError('Native row navigation exceeded limit')
    def capture(name, settle=1):
        if settle: advance(settle)
        camera.refresh()
        (output / (name + '.png')).write_bytes(camera.png)
        stored = int.from_bytes(camera.remote.memory(0xa24f182c, 4), 'little')
        step = dict(name=name, stored_grid=stored, frame_sha256=hashlib.sha256(camera.png).hexdigest(), pages=pages())
        if args.view == 'battery-auto':
            step['battery'] = {field: int.from_bytes(camera.remote.memory(base + module['symbols']['z7_battery_' + field], 4), 'little')
                               for field in ('enabled', 'object', 'percent', 'samples', 'paints')}
            step['native_battery_bar'] = camera.remote.memory(0xa201d4d0 + 0x1aa, 1).hex()
            step['native_battery_controls'] = camera.remote.memory(0xa1824a14, 96).hex()
            pointer = int.from_bytes(camera.remote.memory(0xa1824a14 + 48 + 36, 4), 'little')
            step['native_foreground_icon'] = camera.remote.memory(pointer, 100).hex() if pointer else None
        if args.view == 'histogram':
            step['histogram'] = {name: int.from_bytes(camera.remote.memory(base + module['symbols']['z7_histogram_' + name], 4), 'little')
                for name in ('result', 'attempts', 'draws', 'paints', 'presents', 'last_end', 'context_bits')}
            step['histogram']['outcomes'] = list(struct.unpack('<16I', camera.remote.memory(base + module['symbols']['z7_histogram_outcomes'], 64)))
            step['histogram']['masks'] = camera.remote.memory(0xa1827408, 36).hex()
            step['histogram']['control'] = camera.remote.memory(0xa18273d4, 48).hex()
            obj = int.from_bytes(camera.remote.memory(0xa18273f8, 4), 'little')
            step['histogram']['object'] = hex(obj)
            step['histogram']['object_words'] = list(struct.unpack('<25I', camera.remote.memory(obj, 100))) if obj else []
            step['histogram']['scale'] = int.from_bytes(camera.remote.memory(0xa201d33c, 4), 'little')
            step['histogram']['active_outputs'] = int.from_bytes(camera.remote.memory(0xa1821394, 4), 'little')
            step['histogram']['native_formats'] = camera.remote.memory(0xa18237b8, 7).hex()
            iso_descriptor = 0xa1824654
            iso_control = int.from_bytes(camera.remote.memory(iso_descriptor + 44, 4), 'little')
            step['histogram']['native_iso_visibility'] = [camera.remote.memory(iso_control + i * 48 + 1, 1).hex()
                for i in range(camera.remote.memory(iso_descriptor + 40, 1)[0])]
        if args.view == 'gui-update':
            step['gui_probe'] = {name: int.from_bytes(camera.remote.memory(base + module['symbols']['z7_gui_probe_' + name], 4), 'little')
                for name in ('mask', 'calls', 'busy_samples', 'last_busy', 'recurse')}
            step['native_page'] = camera.remote.memory(0xa201d4d0 + 0x18a, 1)[0]
        if args.view == 'settings-battery':
            step['battery_controls'] = []
            for i in range(10):
                record = camera.remote.memory(0xa1824a14 + i * 48, 48)
                pointer = int.from_bytes(record[36:40], 'little')
                step['battery_controls'].append(dict(index=i, record=record.hex(), pointer=hex(pointer),
                    object_words=list(struct.unpack('<25I', camera.remote.memory(pointer, 100))) if pointer else []))
            step['battery_state'] = {name: int.from_bytes(camera.remote.memory(base + module['symbols']['z7_battery_' + name], 4), 'little')
                for name in ('enabled', 'object', 'samples', 'paints', 'percent')}
        if args.view in ('settings-menu', 'settings-entry', 'settings-root', 'settings-battery'):
            step['settings_view'] = int.from_bytes(camera.remote.memory(base + module['symbols']['z7_settings_view'], 4), 'little')
            labels = []
            for slot in range(230, 245):
                length, pointer, font = struct.unpack('<3I', camera.remote.memory(0xa2019e78 + slot * 12, 12))
                labels.append(dict(slot=slot, length=length, font=font, text=camera.remote.memory(pointer, 51).split(b'\0')[0].decode('utf-8', errors='replace')))
            step['dynamic_labels'] = labels
            pool_pointer = int.from_bytes(camera.remote.memory(0xa1833548 + 36, 4), 'little')
            if pool_pointer:
                total, compounds, regular_count, unused, slots, values = struct.unpack('<4H2I', camera.remote.memory(pool_pointer, 16))
                step['settings_native_label_objects'] = []
                step['settings_native_value_objects'] = []
                for row in range(7):
                    pointer = int.from_bytes(camera.remote.memory(slots + (regular_count + row) * 4, 4), 'little')
                    if pointer:
                        record = camera.remote.memory(pointer, 100)
                        step['settings_native_label_objects'].append(dict(row=row, pointer=hex(pointer), words=list(struct.unpack('<25I', record))))
                    for child in range(7):
                        pointer = int.from_bytes(camera.remote.memory(values + (row * 7 + child) * 4, 4), 'little')
                        if pointer:
                            record = camera.remote.memory(pointer, 100)
                            step['settings_native_value_objects'].append(dict(row=row, child=child, pointer=hex(pointer), words=list(struct.unpack('<25I', record))))
        if args.view in ('information-groups', 'focal'):
            step['information_formats'] = camera.remote.memory(0xa18237b8, 7).hex()
            step['information_native_snapshot'] = camera.remote.memory(0xa201d4d0, 0x33c).hex()
            step['information_phase_source'] = camera.remote.memory(0xa201f260 + 0x44, 12).hex()
            step['information_native_page'] = camera.remote.memory(0xa201d4d0 + 0x18a, 1)[0]
            step['information_base'] = {name: int.from_bytes(camera.remote.memory(base + module['symbols']['z7_base_' + name], 4), 'little')
                for name in ('active', 'saved', 'applied', 'conflicts', 'errors')}
            step['information_masks'] = []
            step['information_controls'] = {}
            for widget in range(61):
                descriptor = int.from_bytes(camera.remote.memory(0x1064d610 + widget * 4, 4), 'little')
                step['information_masks'].append(camera.remote.memory(descriptor + 4, 36).hex())
                if widget in (10, 11, 15, 5, 51, 2) or widget in module.get('other_information_widgets', []):
                    pointer = int.from_bytes(camera.remote.memory(descriptor + 44, 4), 'little')
                    step['information_controls'][str(widget)] = [camera.remote.memory(pointer + row * 48, 48).hex()
                        for row in range(camera.remote.memory(descriptor + 40, 1)[0])]
        if args.view == 'focal':
            step['focal'] = {name: int.from_bytes(camera.remote.memory(base + module['symbols']['z7_focal_' + name], 4), 'little')
                for name in ('object', 'tenths', 'samples', 'paints', 'presents', 'status')}
            record = camera.remote.memory(0xa2019e78 + 298 * 12, 12)
            length, pointer, font = struct.unpack('<3I', record)
            step['focal']['text'] = camera.remote.memory(pointer, min(length, 55)).decode('ascii', errors='replace') if pointer and length else ''
            step['focal']['label_font'] = font
        if args.view == 'disp-presets':
            step['readout_native_snapshot'] = camera.remote.memory(0xa201d4d0, 0x33c).hex()
            step['native_grid_descriptor'] = camera.remote.memory(0xa2020c2c, 32).hex()
            grid_enables = re.findall(r'Z7_GRID_ENABLE instance=1 value=(\d)', camera.live_log.read_text(errors='replace'))
            step['native_grid_plane_gate'] = int(grid_enables[-1]) if grid_enables else None
            if module['kind'] == 'original-Z7-display-base-diagnostic':
                step['native_base_policy'] = {name: int.from_bytes(camera.remote.memory(base + module['symbols']['z7_base_' + name], 4), 'little')
                    for name in ('active', 'saved', 'applied', 'conflicts', 'errors', 'changes')}
            step['readout_native_source_states'] = camera.remote.memory(0xa201f260 + 0x44, 12).hex()
            step['readout_native_formats'] = camera.remote.memory(0xa18237b8, 7).hex()
            step['readout_controls'] = []
            for widget in (10, 11, 15):
                descriptor = int.from_bytes(camera.remote.memory(0x1064d610 + widget * 4, 4), 'little')
                controls = int.from_bytes(camera.remote.memory(descriptor + 44, 4), 'little')
                rows = []
                for row in range(camera.remote.memory(descriptor + 40, 1)[0]):
                    control = camera.remote.memory(controls + row * 48, 48)
                    pointer = struct.unpack_from('<I', control, 36)[0]
                    obj = camera.remote.memory(pointer, 100).hex() if 0xa1800000 <= pointer <= 0xc0000000 - 100 else None
                    rows.append(dict(control=control.hex(), object_pointer=hex(pointer), object=obj))
                step['readout_controls'].append(dict(widget=widget, masks=camera.remote.memory(descriptor + 4, 36).hex(), rows=rows))
        if args.view == 'live':
            step['descriptor'] = list(struct.unpack('<hhIHHhhIHHHHBBH', camera.remote.memory(0xa2020c2c, 32)))
            step['registers'] = list(struct.unpack('<7I', camera.remote.memory(0x20145600, 28)))
            log = camera.live_log.read_text(errors='replace')
            enabled = re.findall(r'Z7_GRID_ENABLE instance=1 value=(\d)', log)
            step['enable'] = int(enabled[-1]) if enabled else None
        result['steps'].append(step)
        save()
        print('Captured', name, 'stored grid', stored, flush=True)
        return step
    def native(name, fn, arguments):
        camera.call(checkpoint(), name, fn, bytes(32), arguments)
    def check_battery_menu_frames(initial, enabled, disabled):
        pictures = [Image.open(output / (name + '.png')).convert('RGB') for name in (initial, enabled, disabled)]
        width, height = pictures[0].size
        check('native-battery-status-frame-dimensions-stable', all(p.size == (width, height) for p in pictures))
        box = tuple(round(v * scale) for v, scale in zip((570, 374, 696, 422), (width / 720, height / 480, width / 720, height / 480)))
        regions = [p.crop(box) for p in pictures]
        pixels = [region.tobytes() for region in regions]
        # Native selection pulses between bright and dark gold. Compare exact
        # black glyph cores, retaining RGB hashes to expose that background change.
        glyphs = [bytes(pixel == (0, 0, 0) for pixel in getattr(region, 'get_flattened_data', region.getdata)()) for region in regions]
        result['native_battery_status_pixels'] = dict(box=box, initial_off_sha256=hashlib.sha256(pixels[0]).hexdigest(),
            enabled_sha256=hashlib.sha256(pixels[1]).hexdigest(), disabled_sha256=hashlib.sha256(pixels[2]).hexdigest(),
            black_glyph_mask_sha256=[hashlib.sha256(mask).hexdigest() for mask in glyphs])
        check('native-battery-on-status-glyphs-change-with-setting', all(any(mask) for mask in glyphs) and glyphs[1] != glyphs[0])
        check('native-battery-off-status-glyphs-return-to-initial-off', glyphs[2] == glyphs[0])
    def check_settings_focus_pixels(name):
        picture = Image.open(output / (name + '.png')).convert('RGB')
        selected = pages()[-1]['row']
        colors = [picture.getpixel((round(100 * picture.width / 720), round((64 + row * 52) * picture.height / 480))) for row in range(7)]
        result.setdefault('native_settings_focus_pixels', []).append(dict(name=name, selected=selected, colors=colors))
        check(name + '-highlight-follows-native-selected-row', 0 <= selected < 7 and
            all((r > 100 and g > 80 and b < 80) if row == selected else (r < 100 and g < 100)
                for row, (r, g, b) in enumerate(colors)))
    def query(name, fn, arguments):
        observed = ui.call_fixture(camera.remote, checkpoint(), fn, bytes(32), arguments)
        result.setdefault('native_queries', []).append(dict(name=name, function=hex(fn), arguments=arguments,
                                                          return_r0=observed['return_r0']))
        save()
        return int(observed['return_r0'], 16)
    def stop():
        if camera.proc and camera.proc.poll() is None:
            camera.proc.terminate()
    watchdog = threading.Timer(1800 if args.information_horizon or args.focal_horizon or args.focal_horizon_control else 1200, stop)
    watchdog.daemon = True
    watchdog.start()
    try:
        camera.boot(announce_ready=False) if args.view in ('menu', 'settings-menu', 'settings-entry', 'settings-root') else camera.boot_shooting()
        checkpoint()
        if args.view in ('settings-battery', 'readouts', 'disp-presets', 'gui-update', 'histogram', 'information-groups', 'focal'):
            # StartLV acknowledgement and a fixed delay are insufficient. This
            # diagnostic gate observes native pipeline progress without writing
            # readiness flags or inventing peripheral completion responses.
            camera.refresh_device_evidence()
            previous = dict(camera.device_evidence or {})
            samples = result.setdefault('native_pipeline_readiness', [])
            ready = False
            for attempt in range(6):
                camera.call(checkpoint(), 'Observe native RAW/ISP/scanout progress', 0x1017081e, bytes(8), [1000])
                camera.refresh_device_evidence()
                current = dict(camera.device_evidence or {})
                health = ui.capture_health(camera.remote, current)
                application = health['application']
                progress = {name: current.get(name, 0) - previous.get(name, 0)
                    for name in ('raw_batches', 'isp_batches', 'lcd_frames_observed')}
                ready = (all(value > 0 for value in progress.values()) and
                    current.get('processed_buffer_scanned', False) and
                    application['ready'] & 3 == 3 and application['stage'] == 0)
                samples.append(dict(attempt=attempt, previous=previous, current=current,
                    progress=progress, health=health, qualified=bool(ready)))
                save()
                if ready: break
                previous = current
            check('native-raw-isp-and-processed-scanout-progress-before-rendering-test', ready)
        if args.view not in ('menu', 'settings-menu', 'settings-entry', 'settings-root'):
            result['histogram_source_state'] = dict(
                viewport_flag=camera.remote.memory(0xa2367974 + 0x28, 1).hex(),
                native_driver_state=camera.remote.memory(0xa188d70c, 3).hex(),
                normalized_maximum=camera.remote.memory(0xa201d33c, 4).hex())
        check('module-loaded-and-callbacks-committed', state()[10] == 8 and state()[23] == 1 and
              (fixture.module_finished if lcd_release else fixture.finished))
        combined = module['kind'] == 'original-Z7-combined-display-module'
        if args.view not in ('battery', 'battery-auto', 'gui-update') or combined:
            for _ in range(20):
                if state()[35]:
                    break
                advance()
            check('grid-menu-published-on-gui-path', state()[35] == 1)
        base = state()[12]
        if args.view == 'focal':
            if args.information_lifecycle:
                from information_lifecycle_probe import run_information_lifecycle_probe
                run_information_lifecycle_probe(camera, output, module, base, result, capture, native, key, query, check, pages)
            elif args.information_routing:
                from information_routing_probe import run_information_routing_probe
                run_information_routing_probe(camera, output, module, base, result, capture, native, key, query, check)
            elif args.information_native_control:
                from information_native_probe import run_information_native_probe
                run_information_native_probe(camera, output, module, base, result, capture, native, key, query, check, host=host, pages=pages)
            elif args.focal_horizon_control:
                from focal_horizon_control import run_horizon_control
                run_horizon_control(camera, output, module, base, result, capture, native, check)
            else:
                from focal_pixel_probe import run_focal_probe
                run_focal_probe(camera, output, module, base, result, capture, native, key, check, horizon=args.focal_horizon)
        elif args.view == 'information-groups':
            if module['kind'] not in ('original-Z7-display-groups-diagnostic','original-Z7-display-other-diagnostic'): raise ValueError('Information diagnostic required')
            other_widgets = module.get('other_information_widgets', [])
            if args.other_information and not other_widgets: raise ValueError('Other-information profile required')
            readout_widgets = (10,11,15,5,51,2) + tuple(other_widgets)
            format_by_widget = dict(zip((10,11,15),(0,1,5)))
            if other_widgets: format_by_widget.update({7:4,16:2,17:3})
            all_details = 127 if other_widgets else 63
            from display_pixel_geometry import control_scanout_box
            native('Original standard base for ordinary information groups', 0x103673de, [0])
            references = [capture('information-disabled-control-1')]
            native('Native invalidation with custom pages disabled', 0x10367c5a, [])
            references.append(capture('information-disabled-control-2'))
            for target in (1, 3, 0):
                key('disp', lambda: camera.remote.memory(0xa201d4d0 + 0x18a, 1)[0] == target)
                reference = capture('information-disabled-native-cycle-' + str(target))
                if target == 0: references.append(reference)
                elif target == 3: native_horizon_reference = reference
            original_masks = references[0]['information_masks']
            model = base + module['symbols']['z7_menu_settings']
            def selected_masks(details, formats):
                expected = list(original_masks)
                for group, widget in enumerate(readout_widgets):
                    if widget in format_by_widget and bytes.fromhex(formats)[format_by_widget[widget]]: continue
                    words = list(struct.unpack('<9I', bytes.fromhex(expected[widget])))
                    for bank in (0, 3):
                        photo = (9 if words[bank] & 1 else 0) | (0x900 if words[bank] & 0x100 else 0)
                        words[bank] = (words[bank] & ~0x909) | (photo if details & (1 << group if group < 6 else 64) else 0)
                    expected[widget] = struct.pack('<9I', *words).hex()
                return expected
            def control_boxes(step, widgets, picture):
                boxes = []
                for widget in widgets:
                    for control in step['information_controls'][str(widget)]:
                        rectangle = struct.unpack_from('<4h', bytes.fromhex(control), 10)
                        if rectangle[0] < rectangle[2] and rectangle[1] < rectangle[3]:
                            boxes.append(control_scanout_box(rectangle, picture.size))
                return boxes
            standard_references = list(references)
            if args.information_horizon:
                native('Enable horizon component in preset0', base + module['symbols']['z7_settings_component'], [model, 0, 2, 1])
                native('Enable custom information on native horizon base', base + module['symbols']['z7_settings_flag'], [model, 0, 1])
                native('Wait for native horizon information', 0x1017081e, [500])
                references = []
                def iso_signature(step):
                    picture = Image.open(output / (step['name'] + '.png')).convert('RGB')
                    box = control_boxes(step, (15,), picture)[0]
                    return hashlib.sha256(picture.crop(box).tobytes()).hexdigest()
                wanted_iso_phases = {iso_signature(r) for r in standard_references}
                observed_iso_phases = set()
                # Vary native sampling intervals while settings remain fixed.
                # Complete captured RGB qualifies phases; RAM flags only record
                # diagnostics and never substitute for completed painting.
                for index, delay in enumerate((None, None, 125, 250, 375, 125, 250, 375), 1):
                    if index == 2: native('Native invalidation for second all-on horizon reference', 0x10367c5a, [])
                    if delay: native('Observe native information phase with unchanged settings', 0x1017081e, [delay])
                    step = capture('information-horizon-all-on-' + str(index))
                    check('horizon-all-on-' + str(index) + '-uses-owned-native-page3', step['information_native_page'] == 3 and
                        step['information_base']['active'] == 1 and step['information_base']['saved'] == 0 and step['information_base']['applied'] == 3)
                    check('horizon-all-on-' + str(index) + '-only-selected-lcd-eligibility-bits', step['information_masks'] == selected_masks(all_details, step['information_formats']))
                    picture = Image.open(output / (step['name'] + '.png')).convert('RGB')
                    baseline = Image.open(output / (native_horizon_reference['name'] + '.png')).convert('RGB')
                    difference = ImageChops.difference(picture, baseline)
                    boxes = control_boxes(step, readout_widgets, picture)
                    protected = difference.copy()
                    for box in boxes: protected.paste((0, 0, 0), box)
                    check('horizon-all-on-' + str(index) + '-protects-native-horizon-and-all-non-information-pixels', protected.getbbox() is None)
                    for widget in (5, 51, 2):
                        regions = control_boxes(step, (widget,), picture)
                        matches = [r['name'] for r in standard_references if r['information_formats'] == step['information_formats'] and
                            all(picture.crop(box).tobytes() == Image.open(output / (r['name'] + '.png')).convert('RGB').crop(box).tobytes() for box in regions)]
                        check('horizon-all-on-' + str(index) + '-native-information-matches-standard-widget-' + str(widget), bool(matches))
                        if widget in (5, 51, 2): check('horizon-all-on-' + str(index) + '-adds-selected-widget-' + str(widget),
                            any(picture.crop(box).tobytes() != baseline.crop(box).tobytes() for box in regions))
                    references.append(step)
                    signature = iso_signature(step)
                    check('horizon-all-on-' + str(index) + '-iso-region-is-a-complete-native-standard-phase', signature in wanted_iso_phases)
                    observed_iso_phases.add(signature)
                    result.setdefault('information_horizon_references', []).append(dict(frame=step['name'], native_reference=native_horizon_reference['name'],
                        native_control_boxes=boxes, total_difference_bounds=difference.getbbox(), protected_pixels_exact=True,
                        iso_region_sha256=signature, native_sampling_delay=delay))
                    if observed_iso_phases == wanted_iso_phases: break
                check('horizon-native-iso-pixel-phases-qualified-with-information-settings-unchanged', observed_iso_phases == wanted_iso_phases)
            def native_membership(step, widget=None):
                picture = Image.open(output / (step['name'] + '.png')).convert('RGB')
                targets = ((widget,) if isinstance(widget,int) else tuple(widget)) if widget is not None else ()
                boxes = control_boxes(step, targets, picture) if targets else []
                matches = []
                for reference in references:
                    if reference['information_formats'] != step['information_formats']: continue
                    baseline = Image.open(output / (reference['name'] + '.png')).convert('RGB')
                    difference = ImageChops.difference(picture, baseline)
                    bounds = difference.getbbox()
                    if widget is None:
                        if bounds is None: matches.append(dict(reference=reference['name']))
                    elif bounds:
                        protected = difference.copy()
                        for box in boxes: protected.paste((0, 0, 0), box)
                        if protected.getbbox() is None:
                            matches.append(dict(reference=reference['name'], difference_bounds=bounds))
                result.setdefault('information_pixel_membership', []).append(dict(frame=step['name'], widget=widget, native_control_boxes=boxes, matches=matches))
                check(step['name'] + ('-only-native-group-pixels-change' if widget is not None else '-complete-native-rgb-restored'), bool(matches))
            toggles = (('other',6,None),) if args.other_information else (('shooting',3,5),('release',4,51),('focus',5,2))
            for name, group, widget in toggles:
                native('Disable ' + name + ' information in preset0', base + module['symbols']['z7_settings_information'], [model, 0, group, 0])
                native('Enable custom page model', base + module['symbols']['z7_settings_flag'], [model, 0, 1])
                native('Wait for native information update', 0x1017081e, [500])
                active = capture('information-' + name + '-off')
                expected = selected_masks(all_details & ~(1 << group), active['information_formats'])
                check(name + '-selected-lcd-mask-policy-matches-native-eligibility', active['information_masks'] == expected)
                if group == 6:
                    formats = bytes.fromhex(active['information_formats'])
                    targets = tuple(w for w in other_widgets if w not in format_by_widget or not formats[format_by_widget[w]])
                    native_membership(active, targets)
                    picture = Image.open(output / (active['name'] + '.png')).convert('RGB')
                    warning_widgets = [w for w in other_widgets if w in format_by_widget and formats[format_by_widget[w]]]
                    warning_matches = []
                    for reference in references:
                        if reference['information_formats'] != active['information_formats']: continue
                        baseline = Image.open(output / (reference['name'] + '.png')).convert('RGB')
                        regions = control_boxes(active, warning_widgets, picture)
                        if all(picture.crop(box).tobytes() == baseline.crop(box).tobytes() for box in regions):
                            warning_matches.append(reference['name'])
                    result['other_warning_pixels'] = dict(widgets=warning_widgets,exact_native_references=warning_matches)
                    check('other-off-keeps-complete-native-shared-warning-pixels', bool(warning_matches))
                else: native_membership(active, widget)
                native('Restore ' + name + ' information', base + module['symbols']['z7_settings_information'], [model, 0, group, 1])
                native('Wait for native information restoration', 0x1017081e, [500])
                restored = capture('information-' + name + '-on')
                check(name + '-all-selected-information-mask-words-restore', restored['information_masks'] == selected_masks(all_details, restored['information_formats']))
                native_membership(restored)
            native('Disable custom page model', base + module['symbols']['z7_settings_flag'], [model, 0, 0])
            retired = capture('information-master-off')
            check('information-master-off-restores-native-masks', retired['information_masks'] == original_masks)
            if args.information_horizon:
                check('horizon-master-off-restores-saved-native-page0', retired['information_native_page'] == 0 and not retired['information_base']['active'])
                references = standard_references
            native_membership(retired)
            result['information_scope'] = dict(groups_bound=7 if other_widgets else 6,native_widgets=len(readout_widgets),other_group_tested=args.other_information,
                settings_setters_supplied=True, snapshot_or_visibility_stores_supplied=False,
                actual_native_disp_baseline_cycle=True, control_snapshots_are_not_paint_fences=True, other_unbound=not bool(other_widgets),focal_unbound=True,
                custom_horizon_information=args.information_horizon, native_phase_reference_sampling=args.information_horizon,
                temporal_paint_coherence_proven=False, custom_page_eligibility_from_each_bank_and_operation_standard_bit=True)
        elif args.view == 'histogram':
            if module['kind'] != 'original-Z7-display-histogram-diagnostic':
                raise ValueError('Histogram component diagnostic required')
            native('Original standard base for histogram diagnostic', 0x103673de, [0])
            histogram_references = [capture('histogram-disabled-control-1')]
            native('Native full layout invalidation while custom display is disabled', 0x10367c5a, [])
            histogram_references.append(capture('histogram-disabled-control-2'))
            for target in (1, 3, 0):
                key('disp', lambda: camera.remote.memory(0xa201d4d0 + 0x18a, 1)[0] == target)
                step = capture('histogram-disabled-native-cycle-' + str(target))
                if target == 0: histogram_references.append(step)
            if args.histogram_sample_fixture:
                sample_fixture = HistogramSampleFixture(base, module['image_bytes'], module['image_bytes'] + module['bss_bytes'],
                    module['symbols']['histogram_samples'])
                camera.remote.enable_histogram_samples(sample_fixture)
            def histogram_word(name):
                return int.from_bytes(camera.remote.memory(base + module['symbols']['z7_histogram_' + name], 4), 'little')
            def wait_histogram(previous_draws=0):
                for _ in range(5):
                    native('Wait for native histogram drawing' if args.histogram_sample_fixture else 'Wait for native histogram sampling', 0x1017081e, [500])
                    if histogram_word('draws' if args.histogram_sample_fixture else 'attempts') > previous_draws:
                        return
            def histogram_visible_pixels(step):
                picture = Image.open(output / (step['name'] + '.png')).convert('RGB')
                x1, y1, x2, y2 = struct.unpack_from('<4h', bytes.fromhex(step['histogram']['control']), 10)
                box = histogram_scanout_box((x1, y1, x2, y2), picture.size)
                matches = []
                for reference in histogram_references:
                    if reference['histogram']['native_formats'] != step['histogram']['native_formats']: continue
                    baseline = Image.open(output / (reference['name'] + '.png')).convert('RGB')
                    difference = ImageChops.difference(picture, baseline)
                    bounds = difference.getbbox()
                    changed = sum(pixel != (0, 0, 0) for pixel in difference.crop(box).getdata())
                    if bounds and changed > 50 and box[0] <= bounds[0] <= bounds[2] <= box[2] and box[1] <= bounds[1] <= bounds[3] <= box[3]:
                        matches.append(dict(reference=reference['name'], changed_histogram_pixels=changed, difference_bounds=bounds,
                            same_iso_control_snapshot=reference['histogram']['native_iso_visibility'] == step['histogram']['native_iso_visibility']))
                result.setdefault('histogram_pixel_membership', []).append(dict(frame=step['name'], native_histogram_box=box, matches=matches))
                check(step['name'] + '-native-histogram-visible-and-all-other-pixels-protected', bool(matches))
            def histogram_retired_pixels(step):
                picture = Image.open(output / (step['name'] + '.png')).convert('RGB').tobytes()
                # Native visibility flags can precede actual painting. Require
                # complete captured-native RGB, not a control snapshot as fence.
                matches = [r['name'] for r in histogram_references if r['histogram']['native_formats'] == step['histogram']['native_formats'] and
                    Image.open(output / (r['name'] + '.png')).convert('RGB').tobytes() == picture]
                result.setdefault('histogram_retired_membership', []).append(dict(frame=step['name'], exact_native_references=matches))
                check(step['name'] + '-complete-native-frame-restored', bool(matches))
            native('Enable histogram component in preset0', base + module['symbols']['z7_settings_component'],
                   [base + module['symbols']['z7_menu_settings'], 0, 1, 1])
            native('Enable custom display model', base + module['symbols']['z7_settings_flag'],
                   [base + module['symbols']['z7_menu_settings'], 0, 1])
            wait_histogram()
            active = capture('histogram-custom-active')
            check('histogram-pass-reaches-owned-getter-boundary' if args.histogram_sample_fixture else 'histogram-pass-reaches-real-native-getter', active['histogram']['attempts'] > 0)
            check('histogram-temporary-masks-restored', active['histogram']['masks'] == struct.pack('<9I', *([0x444] * 6 + [0x440] * 3)).hex())
            if args.histogram_sample_fixture:
                check('supplied-bins-reach-native-painter-and-present-request',
                    active['histogram']['draws'] > 0 and active['histogram']['paints'] > 0 and active['histogram']['presents'] > 0)
                histogram_visible_pixels(active)
            elif not active['histogram']['draws']:
                check('unavailable-or-empty-native-samples-fail-closed',
                    sum(active['histogram']['outcomes'][8:10]) > 0 and not active['histogram']['paints'] and not active['histogram']['presents'])
                references = [Image.open(output / (step['name'] + '.png')).convert('RGB').tobytes()
                    for step in histogram_references if step['histogram']['native_formats'] == active['histogram']['native_formats']]
                check('sample-failure-keeps-complete-native-frame', Image.open(output / 'histogram-custom-active.png').convert('RGB').tobytes() in references)
            else:
                result['native_histogram_success_observed'] = True
            native('Disable histogram component in preset0', base + module['symbols']['z7_settings_component'],
                   [base + module['symbols']['z7_menu_settings'], 0, 1, 0])
            retired = capture('histogram-component-off')
            check('component-off-does-not-retain-module-painter', not retired['histogram']['object_words'] or
                retired['histogram']['object_words'][19] in (0x10433913, 0x102f1545))
            if args.histogram_sample_fixture:
                histogram_retired_pixels(retired)
                previous = histogram_word('draws')
                native('Re-enable histogram component on the same native page', base + module['symbols']['z7_settings_component'],
                       [base + module['symbols']['z7_menu_settings'], 0, 1, 1])
                wait_histogram(previous)
                histogram_visible_pixels(capture('histogram-reenabled'))
            native('Disable custom display model', base + module['symbols']['z7_settings_flag'],
                   [base + module['symbols']['z7_menu_settings'], 0, 0])
            master_off = capture('histogram-master-off')
            if args.histogram_sample_fixture:
                histogram_retired_pixels(master_off)
                checkpoint(); camera.remote.disable_histogram_samples()
            result['histogram_scope'] = dict(supplied_samples=args.histogram_sample_fixture, statistics_event_completion_invented=False,
                native_getter_executed=not args.histogram_sample_fixture, native_pixel_histogram_success_proven=args.histogram_sample_fixture,
                real_statistics_production_proven=False, control_snapshot_is_not_a_paint_fence=True)
        elif args.view == 'gui-update':
            if module['kind'] != 'original-Z7-gui-update-diagnostic':
                raise ValueError('After-GUI diagnostic required')
            check('resident-wrapper-owns-update-slot', camera.remote.memory(0xa1829b14, 4) == struct.pack('<I', host['symbols']['z7_gui_update_bridge']))
            check('native-key-event-slots-preserved', camera.remote.memory(0xa1829b0c, 8) == struct.pack('<2I', 0x1030da57, 0x1030dd1f))
            check('gui-only-registration-ready', state()[41:43] == (1, 0) and not state()[24] and not state()[37])
            before = capture('gui-native-before')
            check('owned-registration-contracts-pass', before['gui_probe']['mask'] == 63)
            check('native-gui-has-called-module', before['gui_probe']['calls'] > 0)
            key('disp', lambda: camera.remote.memory(0xa201d4d0 + 0x18a, 1)[0] != before['native_page'])
            after = capture('gui-native-disp')
            check('native-disp-still-changes-page', after['native_page'] != before['native_page'])
            check('native-update-callback-continues-after-disp', after['gui_probe']['calls'] > before['gui_probe']['calls'])
            check('no-observed-render-busy-callback', after['gui_probe']['busy_samples'] == 0 and after['gui_probe']['last_busy'] == 0)
            result['gui_scope'] = dict(after_native_shooting_update_return=True, extra_paint=False,
                frame_or_isp_fence=False, statistics_producer=False)
        elif args.view == 'readouts':
            if module['kind'] != 'original-Z7-display-readouts-diagnostic': raise ValueError('Readout diagnostic required')
            def readout_word(name): return int.from_bytes(camera.remote.memory(base + module['symbols']['z7_readout_' + name], 4), 'little')
            descriptors = [int.from_bytes(camera.remote.memory(0x1064d610 + i * 4, 4), 'little') for i in (10, 11, 15)]
            controls = [int.from_bytes(camera.remote.memory(p + 44, 4), 'little') for p in descriptors]
            def readout_state():
                return [dict(widget=widget, format=camera.remote.memory(0xa18237b8 + fmt, 1).hex(),
                    visible=[camera.remote.memory(control + row * 48 + 1, 1).hex()
                        for row in range(camera.remote.memory(p + 40, 1)[0])],
                    masks=camera.remote.memory(p + 4, 36).hex())
                    for widget, fmt, p, control in zip((10, 11, 15), (0, 1, 5), descriptors, controls)]
            native('Select original native standard photo page for readout diagnostic', 0x103673de, [0])
            capture('readouts-native-baseline')
            baseline_rgb = Image.open(io.BytesIO(camera.png)).convert('RGB')
            initial = readout_state(); original_masks = [row['masks'] for row in initial]
            result['readout_fixture'] = dict(explicit_native_standard_page=True, preset_selection_diagnostic=True,
                compiled_model_setter=True, native_menu_callback_outside_menu=False, direct_mask_or_visibility_writes=False, initial=initial)
            check('readouts-default-master-disabled', not readout_word('active'))
            camera.remote.write_memory(base + module['symbols']['z7_readout_preset'], struct.pack('<I', 2))
            native('Compiled validated settings master for readout diagnostic', base + module['symbols']['z7_settings_flag'],
                [base + module['symbols']['z7_menu_settings'], 0, 1])
            for _ in range(30):
                advance(.3)
                if readout_word('active') and all(row['format'] != '00' or not any(v == '01' for v in row['visible']) for row in readout_state()): break
            capture('readouts-composition-filter')
            filtered_rgb = Image.open(io.BytesIO(camera.png)).convert('RGB')
            filtered = readout_state(); result['readout_fixture']['filtered'] = filtered
            eligible = [i for i, row in enumerate(initial) if row['format'] == '00' and any(v == '01' for v in row['visible'])]
            check('readout-baseline-has-ordinary-visible-groups', bool(eligible))
            check('compiled-settings-master-applies-owned-readout-policy', readout_word('active') == 1 and readout_word('changes') > 0)
            check('native-updaters-hide-ordinary-readout-controls', all(not any(v == '01' for v in filtered[i]['visible']) for i in eligible))
            check('readout-frame-dimensions-stable', filtered_rgb.size == baseline_rgb.size)
            width, height = baseline_rgb.size
            left, top, right = round(116 * width / 720), round(420 * height / 480), round(590 * width / 720)
            protected = ((0, 0, width, top), (0, top, left, height), (right, top, width, height))
            result['readout_fixture']['pixel_scope'] = dict(native_readout_strip=[116, 420, 590, 480],
                scaled_strip=[left, top, right, height])
            check('readout-filter-preserves-all-pixels-outside-bottom-readout-strip', all(
                baseline_rgb.crop(box).tobytes() == filtered_rgb.crop(box).tobytes() for box in protected))
            check('readout-filter-changes-target-strip-pixels', baseline_rgb.crop((left, top, right, height)).tobytes() !=
                filtered_rgb.crop((left, top, right, height)).tobytes())
            native('Compiled validated settings master disable for readout restoration', base + module['symbols']['z7_settings_flag'],
                [base + module['symbols']['z7_menu_settings'], 0, 0])
            for _ in range(30):
                advance(.3)
                if not readout_word('active') and all(any(v == '01' for v in row['visible']) for i, row in enumerate(readout_state()) if i in eligible): break
            capture('readouts-native-restored')
            restored = readout_state(); result['readout_fixture']['restored'] = restored
            check('readout-disable-restores-all-six-mask-words-exactly', [row['masks'] for row in restored] == original_masks)
            check('native-updaters-restore-ordinary-readout-controls', all(any(v == '01' for v in restored[i]['visible']) for i in eligible))
            check('readout-disable-restores-complete-rgb-frame', Image.open(io.BytesIO(camera.png)).convert('RGB').tobytes() == baseline_rgb.tobytes())
        elif args.view == 'settings-battery':
            if module['kind'] != 'original-Z7-display-settings-module': raise ValueError('Native settings-entry module required')
            def battery_word(name): return int.from_bytes(camera.remote.memory(base + module['symbols']['z7_battery_' + name], 4), 'little')
            def battery_visible():
                pointer = battery_word('object')
                return bool(pointer and int.from_bytes(camera.remote.memory(pointer + 40, 4), 'little'))
            def foreground_battery_glyph():
                pointer = int.from_bytes(camera.remote.memory(0xa1824a14 + 48 + 36, 4), 'little')
                if not pointer: return None
                words = struct.unpack('<25I', camera.remote.memory(pointer, 100))
                return words[2] if (camera.remote.memory(0xa1824a14 + 49, 1) == b'\1' and words[1] == 4 and words[3] == 0 and
                    words[4:6] == (2 | (396 << 16), 62 | (428 << 16)) and words[10] == 1 and words[18] == 0xa201e3b4 and
                    words[19] == 0x10384969 and words[2] in (0x1120, 0x1122, 0x1124, 0x1126, 0x1128)) else None
            def request_battery(label):
                result.setdefault('settings_battery_fixture', dict(supplied_percentage=False, bar=1, requests=[]))['requests'].append(label)
                packet = checkpoint()
                camera.remote.write_memory(0xa201d4d0 + 0x1aa, b'\1')
                for i in (0, 1): camera.remote.write_memory(0xa1824a14 + i * 48, b'\1\1')
                # Do not run another checkpoint between supplying this paused
                # request and dispatching it: native tasks can overwrite it.
                camera.call(packet, 'Native battery renderer after labeled GUI request: ' + label, 0x102f40a0, bytes(32), [])
                icon = int.from_bytes(camera.remote.memory(0xa1824a14 + 48 + 36, 4), 'little')
                result['settings_battery_fixture'].setdefault('request_observations', []).append(dict(label=label,
                    snapshot_bar=camera.remote.memory(0xa201d4d0 + 0x1aa, 1).hex(),
                    descriptor=camera.remote.memory(0xa1824bf4, 48).hex(),
                    foreground_glyph=hex(int.from_bytes(camera.remote.memory(icon + 8, 4), 'little')) if icon else None,
                    eligible_foreground=foreground_battery_glyph()))
            def open_settings():
                if not pages(): key('menu', lambda: bool(pages()))
                for _ in range(10):
                    if on_page(1): break
                    camera.key(checkpoint(), 'left'); advance(.5)
                check('settings-battery-reaches-native-menu-tabs', on_page(1))
                row(1, 3); key('right', lambda: on_page(0x125)); row(0x125, 4)
                key('right', lambda: on_page(0x127)); row(0x127, 28)
                key('right', lambda: on_page(0x153)); row(0x153, 6)
                key('right', lambda: on_page(0)); row(0, 6)
            def return_shooting():
                for _ in range(10):
                    if not pages(): return
                    camera.key(checkpoint(), 'menu'); advance(.5)
                raise RuntimeError('Native MENU did not return to shooting')
            check('settings-battery-default-off', battery_word('enabled') == 0)
            if args.settings_battery_control:
                capture('settings-battery-before-disabled-menu-control')
                open_settings(); return_shooting()
                check('disabled-native-menu-control-preserves-disabled-renderer', battery_word('enabled') == 0 and not battery_visible())
                result['disabled_menu_control_before_baseline'] = True
            # A delayed stock power notification can replace the supplied bar
            # request with its adapter state. Retain every attempt and qualify
            # the actual native foreground glyph in the captured paused state.
            for attempt in range(3):
                request_battery('initial disabled baseline attempt ' + str(attempt + 1))
                baseline_name = 'settings-battery-stock-baseline' + (('-retry-' + str(attempt)) if attempt else '')
                capture(baseline_name)
                baseline_glyph = foreground_battery_glyph()
                if baseline_glyph is not None: break
            check('settings-battery-baseline-has-native-foreground-battery-glyph', baseline_glyph is not None)
            result['settings_battery_fixture'].update(qualified_baseline_frame=baseline_name, baseline_glyph=hex(baseline_glyph))
            baseline = Image.open(io.BytesIO(camera.png)).convert('RGB')
            open_settings(); capture('settings-battery-initially-off-in-native-menu')
            key('right', lambda: battery_word('enabled') == 1)
            capture('settings-battery-enabled-in-native-menu')
            return_shooting(); request_battery('after native menu enable')
            for _ in range(30):
                advance(.3)
                if battery_visible(): break
            capture('settings-battery-enabled-in-shooting')
            check('native-menu-enables-actual-percentage-renderer', battery_visible() and battery_word('samples') > 0)
            open_settings(); key('right', lambda: battery_word('enabled') == 0)
            capture('settings-battery-disabled-in-native-menu')
            check_battery_menu_frames('settings-battery-initially-off-in-native-menu',
                'settings-battery-enabled-in-native-menu', 'settings-battery-disabled-in-native-menu')
            return_shooting(); request_battery('after native menu disable')
            capture('settings-battery-stock-restored')
            restored = Image.open(io.BytesIO(camera.png)).convert('RGB')
            check('native-menu-disable-leaves-no-owned-percentage', not battery_visible())
            check('restored-native-battery-glyph-matches-qualified-baseline', foreground_battery_glyph() == baseline_glyph)
            check('native-menu-disable-restores-stock-battery-region', restored.crop((2, 552, 112, 622)).tobytes() == baseline.crop((2, 552, 112, 622)).tobytes())
            result['settings_battery_integration'] = dict(supplied_setting_word=False, supplied_percentage=False,
                native_snapshot_percent=battery_word('percent'), full_frame_restored=restored.tobytes() == baseline.tobytes(), hardware_telemetry=False)
        elif args.view == 'settings-root' and args.information_page_menu:
            if not module['configuration'].get('information_page'):
                raise ValueError('Integrated information-page profile required')
            key('left', lambda: on_page(1)); row(1, 3)
            key('right', lambda: on_page(0x125)); row(0x125, 8)
            key('right', lambda: on_page(0))
            model_address=base+module['symbols']['z7_menu_settings']
            def setting_word(offset):
                return int.from_bytes(camera.remote.memory(model_address+offset,4),'little')
            meta=base+module['symbols']['sm_meta']
            check('seven-root-controls',camera.remote.memory(meta+20,4)==struct.pack('<I',0x00070007))
            check('information-page-default-off',setting_word(4)==15)
            capture('information-page-default-off')
            row(0,5);key('right',lambda:setting_word(4)==31)
            capture('information-page-enabled')
            row(0,6);key('right',lambda:bool(setting_word(0)&2))
            check('battery-switch-remains-independent',setting_word(4)==31)
            capture('information-and-battery-enabled')
            row(0,5);key('right',lambda:setting_word(4)==15)
            check('information-off-retains-battery-switch',bool(setting_word(0)&2))
            capture('information-disabled-battery-retained')
            result['information_page_menu']=dict(native_keys=True,menu_only=True,
                information_default_off=True,battery_independent=True,live_information_pixels=False)
        elif args.view == 'settings-root' and args.histogram_preset_menu:
            if not module['configuration'].get('histogram_presets'):
                raise ValueError('Integrated histogram preset profile required')
            key('left', lambda: on_page(1)); row(1, 3)
            key('right', lambda: on_page(0x125)); row(0x125, 8)
            key('right', lambda: on_page(0)); row(0, 1)
            view_address=base+module['symbols']['z7_settings_view']
            components=base+module['symbols']['z7_menu_settings']+8
            def view(): return int.from_bytes(camera.remote.memory(view_address,4),'little')
            def bits(): return int.from_bytes(camera.remote.memory(components,4),'little')
            def preset_row(target):
                row(0,target)
            key('right',lambda:view()==1)
            capture('histogram-preset-controls')
            meta=base+module['symbols']['sm_meta']
            check('six-preset-controls',camera.remote.memory(meta+20,4)==struct.pack('<I',0x00070006))
            preset_row(3); key('right',lambda:bool(bits()&2))
            capture('histogram-enabled')
            preset_row(4); key('right',lambda:bool(bits()&4))
            capture('histogram-and-horizon-enabled')
            check('grid-histogram-horizon-combined',bits()==7)
            # Preset value column, rows 0 and 2..4: pixels contrasting with the
            # cell's own background (works for highlighted and plain rows).
            def value_cells_lit(name):
                image=Image.open(output/(name+'.png')).convert('RGB')
                lit={}
                for r in (0,2,3,4):
                    y=88+r*52
                    cell=list(image.crop((590,y-18,690,y+18)).get_flattened_data())
                    background=max(set(cell),key=cell.count)
                    lit[r]=sum(1 for px in cell if sum(abs(a-b) for a,b in zip(px,background))>150)
                return lit
            immediate=value_cells_lit('histogram-and-horizon-enabled')
            capture('histogram-and-horizon-settled', settle=5)
            settled=value_cells_lit('histogram-and-horizon-settled')
            check('settled-preset-values-visible',all(v>20 for v in settled.values()))
            result['preset_value_pixels']=dict(immediate=immediate,settled=settled,
                immediate_blank_rows=[r for r,v in immediate.items() if v<=20])
            key('left',lambda:view()==0); row(0,1); key('right',lambda:view()==1)
            capture('histogram-preset-reopened')
            check('combined-components-retained-on-menu-reentry',bits()==7)
            result['histogram_preset_menu']=dict(native_keys=True,components=bits(),
                real_statistics_verified=False,menu_only=True)
        elif args.view == 'settings-root' and args.root_label_loss_fixture:
            key('left', lambda: on_page(1)); row(1, 3)
            key('right', lambda: on_page(0x125)); row(0x125, 8)
            capture('name-before-fault')
            def root_name():
                length, pointer, font = struct.unpack('<3I', camera.remote.memory(0xa2019e78 + 45 * 12, 12))
                return camera.remote.memory(pointer, min(length, 50)).decode('ascii')
            check('initial-entry-name-visible', root_name() == 'Display settings')
            pool = int.from_bytes(camera.remote.memory(0xa18367a4 + 36, 4), 'little')
            reserved = int.from_bytes(camera.remote.memory(pool + 4, 2), 'little')
            pointers = int.from_bytes(camera.remote.memory(pool + 8, 4), 'little')
            widget = int.from_bytes(camera.remote.memory(pointers + (reserved + 8) * 4, 4), 'little')
            camera.call(checkpoint(), 'Explicitly clear shared name label, diagnostic only',
                        0x103fbb5c, bytes(32), [('scratch', 0), 45, 0])
            native('Invalidate diagnostic stale name cache', 0x104e983a, [widget])
            native('Bind the empty diagnostic name', 0x103fb340, [widget, 45, 2])
            capture('name-after-injected-loss')
            # Opening and returning recreates the row while the shared label
            # was empty. Test the actual pixels, not just the registry text.
            key('right', lambda: on_page(0)); capture('opened-after-label-loss')
            key('left', lambda: on_page(0x125)); capture('name-after-open-back')
            repaired = bool(module['configuration'].get('settings_label_refresh'))
            def name_pixels(name):
                return Image.open(output/(name+'.png')).convert('RGB').crop((114,68,560,104))
            initial_name = name_pixels('name-before-fault')
            restored_name = name_pixels('name-after-open-back')
            check('shared-registry-reseeded-on-back', root_name() == 'Display settings' and on_page(0x125))
            check('new-build-repairs-recreated-row-pixels' if repaired else 'old-build-reproduces-cached-blank-name',
                  restored_name.tobytes() == initial_name.tobytes() if repaired else len(set(restored_name.getdata())) == 1)
            result['label_loss_fixture'] = dict(explicit_shared_label_clear=True,
                explicit_native_font_cache_invalidation=True, repaired_recreated_row=repaired,
                physical_cold_start_cause_established=False)
        elif args.view == 'settings-root':
            grid_before = camera.remote.memory(0xa24f182c, 4)
            key('left', lambda: on_page(1)); row(1, 3)
            key('right', lambda: on_page(0x125))
            capture('custom-settings-overview')
            row(0x125, 8)
            capture('display-settings-entry')
            if module['configuration'].get('settings_category_entry'):
                def prefix_style():
                    pool = int.from_bytes(camera.remote.memory(0xa18367a4 + 36, 4), 'little')
                    slots = int.from_bytes(camera.remote.memory(pool + 12, 4), 'little')
                    prefix = int.from_bytes(camera.remote.memory(slots + 8 * 28 + 3 * 4, 4), 'little')
                    check('category-prefix-widget-exists', bool(prefix))
                    words = struct.unpack('<18I', camera.remote.memory(prefix, 72))
                    pool_words = struct.unpack('<4I', camera.remote.memory(pool, 16))
                    primary = pool_words[2]
                    reserved = pool_words[1] & 0xffff
                    observation = dict(prefix=list(words), primary=[])
                    for index in (8, reserved + 8):
                        pointer = int.from_bytes(camera.remote.memory(primary + index * 4, 4), 'little')
                        observation['primary'].append(list(struct.unpack('<18I', camera.remote.memory(pointer, 72))) if pointer else [])
                    header = int.from_bytes(camera.remote.memory(0xa18367a4 + 12, 4), 'little')
                    observation['header_focus'] = int.from_bytes(camera.remote.memory(header + 0x30, 4), 'little') if header else None
                    result.setdefault('category_observations', []).append(observation)
                    save()
                    return dict(label=words[2], kind=words[3], foreground_mode=words[13], color=words[14])
                selected = prefix_style()
                check('h-selected-dark-rose', selected == dict(label=46, kind=2, foreground_mode=2, color=0xa00040ff))
                key('left', lambda: on_page(1)); capture('display-settings-unfocused')
                idle = prefix_style()
                check('h-unfocused-bright-rose', idle == dict(label=46, kind=2, foreground_mode=2, color=0xff5599ff))
                key('right', lambda: on_page(0x125)); row(0x125, 8)
                capture('display-settings-refocused')
                check('h-selection-color-restored', prefix_style() == selected)
            key('right', lambda: on_page(0))
            capture('display-settings-root')
            check('direct-entry-opens-owned-page', on_page(0))
            if module['configuration'].get('shutter_sound'):
                def sound_level(): return int.from_bytes(camera.remote.memory(base + module['symbols']['z7_sl_level'], 4), 'little')
                check('shutter-sound-row-default-5', sound_level() == 5)
                row(0, 6)
                capture('shutter-sound-row-focused')
                key('ok', lambda: sound_level() == 6)
                capture('shutter-sound-level-6')
                key('ok', lambda: sound_level() == 7)
                capture('shutter-sound-level-7')
                check('shutter-sound-row-steps-level', sound_level() == 7 and on_page(0))
                row(0, 0)
            row(0, 1); key('right', lambda: int.from_bytes(camera.remote.memory(base + module['symbols']['z7_settings_view'], 4), 'little') == 1)
            capture('standard-preset')
            key('left', lambda: int.from_bytes(camera.remote.memory(base + module['symbols']['z7_settings_view'], 4), 'little') == 0)
            key('left', lambda: on_page(0x125))
            capture('display-settings-back')
            check('back-restores-custom-settings-overview', on_page(0x125))
            row(0x125, 4); key('right', lambda: on_page(0x127)); row(0x127, 28)
            key('right', lambda: on_page(0x153))
            capture('grid-only-six-choices')
            meta = int.from_bytes(camera.remote.memory(0xa1836f8c + 40, 4), 'little')
            check('grid-has-six-choices-without-settings-row', camera.remote.memory(meta + 20, 4) == struct.pack('<I', 0x00060006))
            check('menu-navigation-does-not-change-grid', camera.remote.memory(0xa24f182c, 4) == grid_before)
            key('left', lambda: on_page(0x127)); key('left', lambda: on_page(0x125))
            row(0x125, 8); key('right', lambda: on_page(0))
            capture('display-settings-reentry')
            check('separate-entry-reopens-after-grid-menu', on_page(0))
        elif args.view in ('settings-menu', 'settings-entry'):
            expected_kind = 'original-Z7-display-settings-module' if args.view == 'settings-entry' else 'original-Z7-display-settings-menu-diagnostic'
            if module['kind'] != expected_kind and not (args.view == 'settings-menu' and module['kind'] == 'original-Z7-display-settings-module'):
                raise ValueError('Matching settings menu profile required')
            def settings(): return list(struct.unpack('<10I', camera.remote.memory(base + module['symbols']['z7_menu_settings'], 40)))
            def view(): return int.from_bytes(camera.remote.memory(base + module['symbols']['z7_settings_view'], 4), 'little')
            check('settings-page-zero-owned-with-seven-row-metadata', camera.remote.memory(0xa1833548, 4) == struct.pack('<I', 2))
            if args.view == 'settings-entry':
                key('left', lambda: on_page(1)); row(1, 3)
                key('right', lambda: on_page(0x125)); row(0x125, 4)
                key('right', lambda: on_page(0x127)); row(0x127, 28)
                key('right', lambda: on_page(0x153)); row(0x153, 6)
                capture('settings-grid-entry')
                key('right', lambda: on_page(0))
            else:
                native('Open explicitly supplied native settings page-zero entry', 0x10404c42, [2, 0])
            for _ in range(20):
                advance(.3)
                if on_page(0): break
            capture('settings-root')
            result['settings_page_diagnostics'] = dict(object_words=list(struct.unpack('<11I', camera.remote.memory(0xa1833548, 44))),
                title_record=camera.remote.memory(0xa2019e78 + 230 * 12, 12).hex(),
                title_buffer=camera.remote.memory(int.from_bytes(camera.remote.memory(0xa2019e78 + 230 * 12 + 4, 4), 'little'), 51).hex(),
                header=query('Owned settings header lookup', 0x103faebe, [0x203, int.from_bytes(camera.remote.memory(0xa1833548 + 12, 4), 'little')]))
            regular_base = int.from_bytes(camera.remote.memory(0xa181c778, 4), 'little')
            regular = camera.remote.memory(regular_base, 1200 * 284)
            candidates = []
            for i in range(1200):
                record = regular[i * 284:(i + 1) * 284]
                identifier, kind, label, image_kind = struct.unpack_from('<4I', record)
                box = struct.unpack_from('<4h', record, 16)
                if identifier and 0 <= box[1] < 60 and struct.unpack_from('<I', record, 76)[0]:
                    candidates.append(dict(pointer=hex(regular_base + i * 284), identifier=hex(identifier), label=hex(label),
                        image_kind=image_kind, box=box, parent=hex(struct.unpack_from('<I', record, 72)[0]),
                        painter=hex(struct.unpack_from('<I', record, 76)[0])))
            result['settings_page_diagnostics']['top_text_objects'] = candidates
            save()
            check('native-router-opens-owned-page-zero', on_page(0))
            row(0, 6); capture('settings-battery-initial-off')
            key('right', lambda: settings()[0] == 2)
            capture('settings-battery-first-on')
            key('right', lambda: settings()[0] == 0)
            capture('settings-battery-first-off')
            check_battery_menu_frames('settings-battery-initial-off', 'settings-battery-first-on', 'settings-battery-first-off')
            row(0, 0); key('right', lambda: settings()[0] == 1)
            capture('settings-master-on')
            row(0, 1); key('right', lambda: view() == 1)
            capture('settings-standard')
            check_settings_focus_pixels('settings-standard')
            row(0, 2); key('right', lambda: settings()[2] == 0)
            check('native-controls-change-only-standard-grid-choice', settings()[2:6] == [0, 0, 5, 10])
            row(0, 1); key('right', lambda: view() == 2)
            capture('settings-information')
            check_settings_focus_pixels('settings-information')
            information_picture = Image.open(output / 'settings-information.png').convert('RGB')
            normal_on = [information_picture.crop((570, 62 + row * 52, 696, 110 + row * 52)).tobytes() for row in range(1, 6)]
            white_pixels = [sum(min(pixels[i:i + 3]) > 200 for i in range(0, len(pixels), 3)) for pixels in normal_on]
            result['information_on_pixels'] = dict(white_pixels=white_pixels, sha256=[hashlib.sha256(pixels).hexdigest() for pixels in normal_on])
            check('information-subview-all-five-unselected-on-values-render-identically', information_picture.size == (720, 480) and
                pages()[-1]['row'] == 0 and settings()[6] == 127 and all(white_pixels) and len(set(normal_on)) == 1)
            row(0, 0); key('right', lambda: settings()[6] == 126)
            key('left', lambda: view() == 1); key('left', lambda: view() == 0)
            capture('settings-root-return')
            row(0, 6); key('right', lambda: settings()[0] == 3)
            row(0, 5); key('right', lambda: settings()[1] == 31)
            capture('settings-global-choices')
            check('native-setting-edits-retain-other-preset-values', settings() == [3, 31, 0, 0, 5, 10, 126, 7, 0, 127])
            check('native-battery-setting-published-to-renderer', camera.remote.memory(base + module['symbols']['z7_battery_enabled'], 4) == struct.pack('<I', 1))
            key('left', lambda: not on_page(0))
            capture('settings-native-back')
            check('native-root-back-leaves-owned-page', not on_page(0))
            if args.view == 'settings-entry':
                check('settings-back-restores-grid-page-without-changing-grid-setting', on_page(0x153) and camera.remote.memory(0xa24f182c, 4) == bytes(4))
            result['settings_menu'] = dict(model=settings(), explicit_diagnostic_entry=args.view == 'settings-menu', card_io=False, battery_binding=True, custom_page_renderer_binding=False)
        elif args.view == 'disp-presets':
            base_bound = module['kind'] == 'original-Z7-display-base-diagnostic'
            if module['kind'] not in ('original-Z7-display-disp-diagnostic', 'original-Z7-display-base-diagnostic'):
                raise ValueError('DISP preset diagnostic required')
            if args.grid_components and not base_bound: raise ValueError('Grid component validation requires base-page module')
            def preset(): return int.from_bytes(camera.remote.memory(base + module['symbols']['z7_readout_preset'], 4), 'little')
            def cycles(): return int.from_bytes(camera.remote.memory(base + module['symbols']['z7_preset_cycles'], 4), 'little')
            def native_page(): return camera.remote.memory(0xa201d4d0 + 0x18a, 1)[0]
            check('preset-diagnostic-preserves-original-key-binding', camera.remote.memory(0xa1829b0c, 4) == struct.pack('<I', 0x1030da57))
            native('Original standard page for DISP preset diagnostic', 0x103673de, [0])
            startup_step = capture('presets-disabled-startup')
            native_references = []
            def retain_reference(step):
                snapshot = bytes.fromhex(step['readout_native_snapshot'])
                formats = bytes.fromhex(step['readout_native_formats'])
                if snapshot[0x18a] not in ((0, 3) if base_bound else (0,)) or any(formats[index] for index in (0, 1, 5)):
                    raise RuntimeError('Native reference must be an eligible base page with ordinary formats')
                native_references.append(step)
            retain_reference(startup_step)
            if args.grid_components:
                native('Compiled native golden grid choice', base + module['symbols']['golden'], [])
                native('Native grid enabled for component baseline', 0x10377236, [1])
                step = capture('presets-grid-enabled-startup'); retain_reference(step)
                descriptor = struct.unpack('<hhIHHhhIHHHHBBH', bytes.fromhex(step['native_grid_descriptor']))
                registers = struct.unpack('<7I', camera.remote.memory(0x20145600, 28))
                picture = Image.open(io.BytesIO(camera.png)).convert('RGB')
                off_picture = Image.open(output / 'presets-disabled-startup.png').convert('RGB')
                x, y = registers[1] & 65535, registers[0] >> 16 & 16383
                dy, dx = registers[4] & 65535, registers[4] >> 16
                color = (registers[6] >> 16 & 255, registers[6] >> 8 & 255, registers[6] & 255)
                points = [(picture.width // 2 + 37, y + i * dy) for i in range(2)] + [(x + i * dx, 300) for i in range(2)]
                result['native_grid_component_reference'] = dict(points=points, color=color, native_style=step['stored_grid'])
                check('native-grid-reference-has-visible-golden-lines', step['stored_grid'] == 3 and
                    descriptor[4] == descriptor[9] == 2 and all(0 <= a < picture.width and 0 <= b < picture.height and
                        picture.getpixel((a, b)) == color and off_picture.getpixel((a, b)) != color for a, b in points))
            # Exercise one complete native cycle while the custom master is off.
            # Retain this separately from the qualified comparison baseline.
            for target in (1, 3, 0):
                key('disp', lambda: native_page() == target)
                control_step = capture('presets-disabled-control-' + str(target))
                if target == 0 or (base_bound and target == 3): retain_reference(control_step)
            result['disabled_native_cycle_control_before_baseline'] = True
            if args.grid_components:
                native('Native grid OFF control before custom mode', 0x104f5592, [])
                retain_reference(capture('presets-grid-disabled-control'))
                native('Compiled native golden grid restored before custom mode', base + module['symbols']['golden'], [])
                native('Native grid enabled again before custom mode', 0x10377236, [1])
            baseline_step = capture('presets-native-baseline')
            retain_reference(baseline_step)
            baseline = Image.open(io.BytesIO(camera.png)).convert('RGB')
            def iso_state(step):
                snapshot = bytes.fromhex(step['readout_native_snapshot'])
                mode = struct.unpack_from('<I', snapshot, 0x250)[0]
                # Original102F2586 selects one source. Unselected source words
                # can change independently and do not determine this ISO label.
                source = 0x3c if mode == 1 else 0x24c if mode == 3 else 4
                return ([mode, source, struct.unpack_from('<I', snapshot, source)[0]],
                    [bytes.fromhex(row['control'])[1] for row in step['readout_controls'][-1]['rows']])
            def reference_capture(name, expected_page=0, expected_grid=None):
                if args.grid_components and expected_grid is None: expected_grid = True
                step = capture(name)
                current = Image.open(io.BytesIO(camera.png)).convert('RGB')
                matching = [reference for reference in native_references
                    if bytes.fromhex(reference['readout_native_snapshot'])[0x18a] == expected_page and
                    (expected_grid is None or bool(reference['stored_grid']) == expected_grid) and
                    Image.open(output / (reference['name'] + '.png')).convert('RGB').tobytes() == current.tobytes()]
                result.setdefault('native_iso_reference_matches', []).append(dict(name=name,
                    state=iso_state(step), expected_native_base_page=expected_page,
                    expected_native_grid=expected_grid,
                    exact_rgb_references=[reference['name'] for reference in matching],
                    same_control_state_references=[reference['name'] for reference in native_references
                        if iso_state(reference) == iso_state(step)],
                    control_snapshot_is_not_a_completed_paint_fence=True))
                save()
                # Accept only an entire previously captured native image. State
                # records are diagnostics: they can precede native painting.
                if not matching:
                    if args.grid_components:
                        result['grid_failed_frame_diagnostics'] = dict(frame=name,
                            observation_after_failed_frame_not_a_paint_fence=True,
                            native_visibility=query('Original grid visibility after failed frame', 0x1037723e, []),
                            host_scalar=query('Owned grid scalar after failed frame', host['symbols']['z7_display_scalar'], [0x102d, step['stored_grid']]))
                        save()
                    raise AssertionError('No exact captured native reference for ' + name)
                reference = matching[-1]
                return Image.open(output / (reference['name'] + '.png')).convert('RGB')
            check('preset-diagnostic-starts-at-zero', preset() == 0)
            native('Compiled custom master for native DISP presets', base + module['symbols']['z7_settings_flag'],
                [base + module['symbols']['z7_menu_settings'], 0, 1])
            for target in (1, 2, 3, 0):
                previous = cycles()
                key('disp', lambda: preset() == target and cycles() > previous)
                expected_page = 0
                if base_bound:
                    components = int.from_bytes(camera.remote.memory(base + module['symbols']['z7_menu_settings'] + 8 + target * 4, 4), 'little')
                    expected_page = 3 if components & 4 else 0
                reference = None
                if target == 2: capture('preset-' + str(target))
                else: reference = reference_capture('preset-' + str(target), expected_page,
                    bool(components & 1) if args.grid_components else None)
                current = Image.open(io.BytesIO(camera.png)).convert('RGB')
                check('admitted-disp-selects-preset-' + str(target), preset() == target and cycles() == previous + 1)
                check('preset-selects-native-base-page-' + str(target), native_page() == expected_page)
                if args.grid_components:
                    descriptor = struct.unpack('<hhIHHhhIHHHHBBH', camera.remote.memory(0xa2020c2c, 32))
                    check('grid-component-preserves-style-and-selects-native-plane-' + str(target),
                        int.from_bytes(camera.remote.memory(0xa24f182c, 4), 'little') == 3 and descriptor[4] == descriptor[9] == 2 and
                        result['steps'][-1]['native_grid_plane_gate'] == int(bool(components & 1)))
                if target == 2:
                    native_baseline = Image.open(output / 'presets-disabled-control-3.png').convert('RGB') if expected_page == 3 else baseline
                    width, height = native_baseline.size
                    left, top, right = round(116 * width / 720), round(420 * height / 480), round(590 * width / 720)
                    protected = ((0, 0, width, top), (0, top, left, height), (right, top, width, height))
                    check('composition-preset-preserves-pixels-outside-readouts', all(native_baseline.crop(box).tobytes() == current.crop(box).tobytes() for box in protected))
                    check('composition-preset-changes-readout-pixels', current.tobytes() != native_baseline.tobytes())
                else:
                    check('preset-restores-all-three-readout-pixels-' + str(target), current.tobytes() == reference.tobytes())
            if args.grid_components:
                model = base + module['symbols']['z7_menu_settings']
                for enabled in (0, 1, 0):
                    native('Compiled current-preset grid component ' + str(enabled), base + module['symbols']['z7_settings_component'], [model, 0, 0, enabled])
                    reference = reference_capture('grid-component-edit-' + str(enabled) + '-' + str(len(result['steps'])), 0, bool(enabled))
                    check('same-page-grid-edit-retires-or-restores-native-pixels-' + str(enabled), native_page() == 0 and
                        Image.open(io.BytesIO(camera.png)).convert('RGB').tobytes() == reference.tobytes() and
                        int.from_bytes(camera.remote.memory(0xa24f182c, 4), 'little') == 3 and cycles() == 4)
            native('Compiled custom master off after preset cycle', base + module['symbols']['z7_settings_flag'],
                [base + module['symbols']['z7_menu_settings'], 0, 0])
            reference = reference_capture('presets-native-restored')
            check('preset-master-off-restores-complete-frame', Image.open(io.BytesIO(camera.png)).convert('RGB').tobytes() == reference.tobytes())
            if base_bound:
                check('preset-master-off-releases-native-base-page-ownership', native_page() == 0 and
                    int.from_bytes(camera.remote.memory(base + module['symbols']['z7_base_active'], 4), 'little') == 0)
            key('disp', lambda: native_page() != 0)
            capture('presets-disabled-native-cycle')
            check('disabled-master-resumes-native-page-cycle', native_page() != 0 and cycles() == 4)
            result['preset_cycle'] = dict(native_key_injection=True, original_key_binding_retained=True,
                compiled_master_setter=True, preset_word_supplied=False, explicit_native_standard_page=True,
                information_app_bound=False, base_component_selection_bound=base_bound,
                grid_component_bound=args.grid_components, histogram_highlights_components_bound=False, readout_groups_bound=3)
        elif args.view == 'disp-key':
            if module['kind'] != 'original-Z7-disp-key-diagnostic': raise ValueError('Native-key diagnostic required')
            def key_word(name): return int.from_bytes(camera.remote.memory(base + module['symbols']['z7_disp_key_' + name], 4), 'little')
            def mode(): return int.from_bytes(camera.remote.memory(0xa201d4d0 + 0x18a, 1), 'little')
            def next_mode():
                old = mode(); key('disp', lambda: mode() != old)
            def reach(target):
                for _ in range(8):
                    if mode() == target: return
                    next_mode()
                raise RuntimeError('Native-key diagnostic cannot reach requested DISP mode')
            check('key-callback-owns-published-resident-module', int.from_bytes(camera.remote.memory(0xa1829b0c, 4), 'little') ==
                  (base + module['symbols']['clean_key']) | 1)
            check('key-diagnostic-defaults-disabled', key_word('enabled') == 0)
            native('Native-key diagnostic golden grid', base + module['symbols']['golden'], [])
            native('Native grid enabled for native-key diagnostic', 0x10377236, [1])
            reach(1); capture('key-native-simplified-baseline'); stock = camera.png
            reach(0)
            camera.remote.write_memory(base + module['symbols']['z7_disp_key_enabled'], struct.pack('<I', 1))
            advance(1)
            next_mode(); capture('key-clean-simplified')
            check('native-disp-key-activates-simplified-clean-page', mode() == 1 and key_word('accepted') > 0 and
                  int.from_bytes(camera.remote.memory(base + module['symbols']['z7_clean_active'], 4), 'little') == 1)
            objects = [int.from_bytes(camera.remote.memory(0xa1824684 + i * 48 + 36, 4), 'little') for i in range(1, 5)]
            check('native-key-clean-page-hides-four-brackets', all(camera.remote.memory(p + 40, 4) == bytes(4) for p in objects))
            camera.remote.write_memory(base + module['symbols']['z7_disp_key_enabled'], bytes(4)); advance(1)
            reach(0); reach(1); capture('key-native-simplified-restored')
            check('native-key-master-disable-restores-complete-frame', Image.open(io.BytesIO(stock)).convert('RGB').tobytes() ==
                  Image.open(io.BytesIO(camera.png)).convert('RGB').tobytes())
            result['native_key_diagnostic'] = dict(accepted=key_word('accepted'), rejected=key_word('rejected'),
                                                  explicit_master_setting=True, full_custom_pages=False)
        elif args.view in ('disp-input', 'disp-admission'):
            slot = int.from_bytes(camera.remote.memory(0xa1829b0c, 4), 'little')
            check('original-shooting-key-callback-binding', slot == 0x1030da57)
            capture('disp-input-before')
            initial_mode = camera.remote.memory(0xa201d4d0 + 0x18a, 1).hex()
            # Observe during the AO injection and bounded native task delays:
            # the event can run on another CPU before the injection returns.
            packet = checkpoint()
            saved_trace = ui.probe.TRACE_CALL, ui.probe.TRACE_REPEAT
            observed_calls = []
            try:
                ui.probe.TRACE_CALL = [0x1030d7ac, 0x103673f6, 0x1037061c]
                ui.probe.TRACE_REPEAT = {0x1030d7ac}
                if args.view == 'disp-admission':
                    # Observe original post-call branch inputs. Do not invoke
                    # the gates separately or supply their return values.
                    ui.probe.TRACE_CALL += [0x1030da56, 0x1030da60, 0x1030da74,
                        0x1030da7e, 0x1030daf2, 0x1030db40,
                        0x1036741a, 0x10367440, 0x10367448, 0x1036744e,
                        0x10367454, 0x1036745a, 0x10367460]
                    ui.probe.TRACE_REPEAT = set(ui.probe.TRACE_CALL)
                values = [0] * 8; values[83 // 32] = 1 << (83 % 32); values[4] = 10
                observed_calls.append(ui.call_fixture(camera.remote, packet, 0x105230a6,
                    struct.pack('<8I', *values), [('scratch', 0), 5, ('scratch', 20)]))
                for _ in range(5):
                    packet = 'T05thread:' + observed_calls[-1]['return_cpu'] + ';'
                    observed_calls.append(ui.call_fixture(camera.remote, packet, 0x1017081e, bytes(32), [1000]))
                    reached = 0x1030da56 if args.view == 'disp-admission' else 0x103673f6
                    if any(int(e['registers']['r15'], 16) == reached and
                        (args.view != 'disp-admission' or int(e['registers']['r0'], 16) == 0x29)
                        for call in observed_calls for e in call['trace']): break
            finally:
                ui.probe.TRACE_CALL, ui.probe.TRACE_REPEAT = saved_trace
            (output / 'native-disp-call-trace.json').write_text(json.dumps(observed_calls, indent=2) + '\n', encoding='utf-8')
            events = [e['registers'] for call in observed_calls for e in call['trace']]
            keys = [e['r0'] for e in events if int(e['r15'], 16) == 0x1030d7ac]
            result['native_disp_input'] = dict(callback_slot=hex(slot), dispatcher='0x1030d7ac', keys=keys,
                                             mode_before=initial_mode, supplied_native_ao_press=True)
            if args.view == 'disp-admission':
                result['native_disp_admission'] = dict(
                    original_gate_returns_observed=True, native_return_values_supplied=False,
                    incoming_snapshot=camera.remote.memory(0xa201d4d0, 0x33c).hex(),
                    device_evidence=camera.device_evidence,
                    original_callback_key29_observed=any(int(e['r15'], 16) == 0x1030da56 and
                        int(e['r0'], 16) == 0x29 for e in events),
                    trace_events=len(events))
                capture('disp-admission-after')
                check('native-admission-trace-observes-original-key29-callback',
                    result['native_disp_admission']['original_callback_key29_observed'])
                # A rejection is an observation, not a probe failure. Preserve
                # the branch inputs rather than requiring successful admission.
                result['native_disp_input']['mode_after'] = camera.remote.memory(0xa201d4d0 + 0x18a, 1).hex()
                check('original-callback-remains-unchanged-after-key', camera.remote.memory(0xa1829b0c, 4) == struct.pack('<I', slot))
            else:
                check('injected-native-disp-reaches-z7-key-29', any(int(k, 16) == 0x29 for k in keys))
                check('injected-native-disp-reaches-original-admission', any(int(e['r15'], 16) == 0x103673f6 for e in events))
                capture('disp-input-after')
                result['native_disp_input']['mode_after'] = camera.remote.memory(0xa201d4d0 + 0x18a, 1).hex()
                check('original-callback-remains-unchanged-after-key', camera.remote.memory(0xa1829b0c, 4) == struct.pack('<I', slot))
        elif args.view == 'clean':
            if module['kind'] != 'original-Z7-clean-display-diagnostic':
                raise ValueError('Clean view requires the disabled-by-default clean diagnostic')
            request_address = base + module['symbols']['z7_clean_request']
            def cycle_mode(target):
                for _ in range(8):
                    if camera.remote.memory(0xa201d4d0 + 0x18a, 1) == bytes([target]): return
                    camera.key(checkpoint(), 'disp'); advance(.5)
                raise RuntimeError('Cannot reach native DISP mode')
            descriptors = [int.from_bytes(camera.remote.memory(0x1064d610 + i * 4, 4), 'little') for i in range(61)]
            original_masks = [camera.remote.memory(p + 4, 36) for p in descriptors]
            native('Clean diagnostic golden grid choice', base + module['symbols']['golden'], [])
            native('Native grid enabled for clean diagnostic', 0x10377236, [1])
            cycle_mode(1); capture('clean-native-baseline')
            camera.remote.write_memory(request_address, struct.pack('<I', 1)); advance(.5)
            cycle_mode(0); cycle_mode(1)
            capture('clean-requested-simplified')
            check('clean-diagnostic-masks-apply-exactly', all(camera.remote.memory(p + 4, 36) ==
                  struct.pack('<9I', *(x & ~0x22222 for x in struct.unpack('<9I', saved)))
                  for p, saved in zip(descriptors, original_masks)))
            objects = [int.from_bytes(camera.remote.memory(0xa1824684 + i * 48 + 36, 4), 'little') for i in range(1, 5)]
            result['clean_brackets'] = [dict(pointer=hex(p), visible=camera.remote.memory(p + 40, 4).hex(),
                painter=camera.remote.memory(p + 76, 4).hex()) for p in objects]
            check('clean-diagnostic-bracket-objects-hidden', all(camera.remote.memory(p + 40, 4) == bytes(4) for p in objects))
            camera.remote.write_memory(request_address, bytes(4)); advance(.5)
            cycle_mode(0); cycle_mode(1); capture('clean-native-restored')
            check('clean-diagnostic-restores-all-owned-masks', all(camera.remote.memory(p + 4, 36) == saved
                  for p, saved in zip(descriptors, original_masks)))
        elif args.view == 'battery-auto':
            # Battery context_visible() depends on native UI ownership, font,
            # output and glyph visibility, not RAW/ISP buffers. Preserve sensor
            # health as an observation; this isolated overlay fixture does not
            # establish sensor/ISP functionality or real capture readiness.
            camera.refresh_device_evidence()
            result['battery_scope'] = dict(native_ui_overlay_only=True,
                sensor_pipeline_verified=False,
                incoming_bar_inputs_supplied=bar_fixture is not None,
                device_observation=dict(camera.device_evidence or {}),
                health=ui.capture_health(camera.remote, camera.device_evidence or {}))
            def automatic_word(name):
                return int.from_bytes(camera.remote.memory(base + module['symbols']['z7_battery_' + name], 4), 'little')
            def automatic_visible():
                object_pointer = automatic_word('object')
                return bool(object_pointer and int.from_bytes(camera.remote.memory(object_pointer + 40, 4), 'little'))
            def enable(value):
                camera.remote.write_memory(base + module['symbols']['z7_battery_enabled'], struct.pack('<I', value))
            def foreground_glyph():
                control = 0xa1824a14 + 48
                pointer = int.from_bytes(camera.remote.memory(control + 36, 4), 'little')
                if not pointer: return None
                words = struct.unpack('<25I', camera.remote.memory(pointer, 100))
                return words[2] if (camera.remote.memory(control + 1, 1) == b'\1' and
                    words[1] == 4 and words[3] == 0 and words[10] == 1 and
                    words[4:6] == (2 | 396 << 16, 62 | 428 << 16) and
                    words[18:20] == (0xa201e3b4, 0x10384969) and
                    words[2] in (0x1120, 0x1122, 0x1124, 0x1126, 0x1128)) else None
            def request_icon(label, bar=1):
                packet = checkpoint()
                result['battery_icon_fixture'].setdefault('requests', []).append(dict(label=label, bar=bar))
                if bar_fixture:
                    camera.remote.enable_battery_bar(bar)
                else:
                    camera.remote.write_memory(0xa201d4d0 + 0x1aa, bytes([bar]))
                for i in (0, 1): camera.remote.write_memory(0xa1824a14 + i * 48, b'\1\1')
                # Match settings-battery: no checkpoint after supplying a
                # paused request, since native tasks may overwrite it.
                camera.call(packet, 'Native battery renderer, labeled GUI request: ' + label, 0x102f40a0, bytes(32), [])
                result['battery_icon_fixture'].setdefault('request_observations', []).append(dict(
                    label=label, snapshot_bar=camera.remote.memory(0xa201d4d0 + 0x1aa, 1).hex(),
                    eligible_foreground=foreground_glyph()))
            capture('automatic-native-context')
            check('no-native-battery-icon-means-no-overlay', automatic_word('object') == 0 and automatic_word('samples') == 0)
            if args.battery_icon_fixture:
                enable(0)
                result['battery_icon_fixture'] = dict(scope='Labeled supplied native control visibility requests; native widget renderer initializes icon',
                    original_controls=[camera.remote.memory(0xa1824a14 + i * 48, 2).hex() for i in (0, 1)],
                    original_bar=camera.remote.memory(0xa201d4d0 + 0x1aa, 1).hex(), supplied_bar=1,
                    percentage_supplied=False)
                for attempt in range(3):
                    request_icon('stock baseline ' + str(attempt + 1))
                    baseline_name = 'automatic-stock-icon-baseline' + ('-' + str(attempt) if attempt else '')
                    capture(baseline_name)
                    if foreground_glyph() is not None: break
                check('baseline-retains-eligible-native-battery-glyph', foreground_glyph() is not None)
                check('battery-baseline-is-photo-lcd-with-no-native-menu',
                      camera.remote.memory(0xa18237c6, 1) == b'\0' and
                      camera.remote.memory(0xa201d4d0 + 0x40, 1) == b'\0' and not pages())
                result['battery_icon_fixture']['baseline_glyph'] = foreground_glyph()
                stock_icon = Image.open(io.BytesIO(camera.png)).convert('RGB')
                check('supplied-request-reaches-native-icon', camera.remote.memory(0xa1824a14 + 49, 1) == b'\1')
                enable(1)
                for _ in range(30):
                    advance(.3)
                    if automatic_word('paints'): break
                capture('automatic-percent')
                check('eligible-native-icon-automatically-shows-percentage', automatic_word('object') != 0 and automatic_word('paints') > 0 and automatic_word('samples') > 0)
                shown = Image.open(io.BytesIO(camera.png)).convert('RGB')
                box = (2, 552, 112, 622)
                check('automatic-percent-changes-native-icon-region', shown.crop(box).tobytes() != stock_icon.crop(box).tobytes())
                if combined:
                    native('Combined module golden grid choice', base + module['symbols']['golden'], [])
                    native('Native grid visibility with percentage active', 0x10377236, [1])
                    capture('combined-golden-grid-and-percent')
                    descriptor = struct.unpack('<hhIHHhhIHHHHBBH', camera.remote.memory(0xa2020c2c, 32))
                    registers = struct.unpack('<7I', camera.remote.memory(0x20145600, 28))
                    picture = Image.open(io.BytesIO(camera.png)).convert('RGB')
                    x, y = registers[1] & 65535, registers[0] >> 16 & 16383
                    dy, dx = registers[4] & 65535, registers[4] >> 16
                    color = (registers[6] >> 16 & 255, registers[6] >> 8 & 255, registers[6] & 255)
                    points = [(picture.width // 2 + 37, y + i * dy) for i in range(2)] + [(x + i * dx, 300) for i in range(2)]
                    check('combined-grid-and-battery-coexist-with-native-pixels', descriptor[4] == descriptor[9] == 2 and
                          all(picture.getpixel(p) == color for p in points) and camera.remote.memory(automatic_word('object') + 40, 4) != bytes(4))
                    native('Native grid Off after combined observation', 0x104f5592, [])
                enable(0)
                for _ in range(30):
                    advance(.3)
                    if camera.remote.memory(automatic_word('object') + 40, 4) == bytes(4): break
                capture('automatic-stock-icon-restored')
                restored = Image.open(io.BytesIO(camera.png)).convert('RGB')
                check('automatic-disable-restores-stock-icon-region', restored.crop(box).tobytes() == stock_icon.crop(box).tobytes())
                result['automatic_battery'] = dict(native_sample=automatic_word('percent'), samples=automatic_word('samples'),
                    paints=automatic_word('paints'), supplied_percentage=False, hardware_telemetry=False,
                    full_frame_restored=restored.tobytes() == stock_icon.tobytes())
                result['battery_icon_fixture']['active_objects'] = [dict(
                    pointer=hex(int.from_bytes(camera.remote.memory(0xa1824a14 + i * 48 + 36, 4), 'little')),
                    record=camera.remote.memory(int.from_bytes(camera.remote.memory(0xa1824a14 + i * 48 + 36, 4), 'little'), 96).hex()) for i in (0, 1)]
                request_icon('adapter exclusion', bar=0)
                count = automatic_word('samples'); enable(1)
                capture('automatic-adapter-excluded')
                check('adapter-glyph-never-enables-percentage', automatic_word('samples') == count and
                      camera.remote.memory(automatic_word('object') + 40, 4) == bytes(4))
                if args.battery_lifecycle:
                    request_icon('before native MENU')
                    for _ in range(30):
                        advance(.3)
                        if automatic_word('object') and camera.remote.memory(automatic_word('object') + 40, 4) != bytes(4): break
                    capture('automatic-before-menu')
                    check('automatic-percentage-active-before-native-menu', automatic_word('object') and
                          camera.remote.memory(automatic_word('object') + 40, 4) != bytes(4))
                    key('menu', lambda: bool(pages()))
                    capture('automatic-native-menu')
                    check('native-menu-hides-owned-percentage', not automatic_word('object') or
                          camera.remote.memory(automatic_word('object') + 40, 4) == bytes(4))
                    count = automatic_word('samples')
                    for _ in range(5): advance(.3)
                    check('native-menu-performs-no-battery-sampling', automatic_word('samples') == count)
                    key('menu', lambda: not pages())
                    capture('automatic-native-menu-return')
                    request_icon('after native MENU return')
                    for _ in range(30):
                        advance(.3)
                        if automatic_word('object') and camera.remote.memory(automatic_word('object') + 40, 4) != bytes(4): break
                    capture('automatic-after-menu-eligible-request')
                    check('native-menu-return-recovers-owned-percentage-when-eligible', automatic_word('object') and
                          camera.remote.memory(automatic_word('object') + 40, 4) != bytes(4))
                    if args.battery_playback:
                        result['playback_fixture_scope'] = 'No emulated memory card; native PLAY error path, not image playback'
                        camera.key(checkpoint(), 'play')
                        capture('automatic-native-empty-card-playback')
                        result['empty_card_playback'] = dict(
                            pages=pages(), ui_output=camera.remote.memory(0xa18237c6, 1).hex(),
                            snapshot_mode=camera.remote.memory(0xa201d4d0 + 0x40, 1).hex(),
                            owned_object=hex(automatic_word('object')), owned_visible=automatic_visible())
                        check('native-empty-card-playback-hides-owned-percentage', not automatic_visible())
                        count = automatic_word('samples')
                        for _ in range(5): advance(.3)
                        check('native-empty-card-playback-performs-no-battery-sampling', automatic_word('samples') == count)
                        camera.key(checkpoint(), 'play')
                        capture('automatic-native-empty-card-playback-return')
                        request_icon('after native empty-card PLAY return')
                        for _ in range(30):
                            advance(.3)
                            if automatic_word('object') and camera.remote.memory(automatic_word('object') + 40, 4) != bytes(4): break
                        capture('automatic-after-playback-eligible-request')
                        check('native-playback-return-recovers-owned-percentage-when-eligible', automatic_word('object') and
                              camera.remote.memory(automatic_word('object') + 40, 4) != bytes(4))
        elif args.view == 'battery':
            symbols = module['symbols']
            def trial_word(name):
                return int.from_bytes(camera.remote.memory(base + symbols['z7_battery_trial_' + name], 4), 'little')
            check('battery-trial-is-initially-inactive', trial_word('phase') == 0 and trial_word('object') == 0)
            capture('battery-module-inactive')
            baseline = Image.open(io.BytesIO(camera.png)).convert('RGB')
            camera.remote.write_memory(base + symbols['z7_battery_trial_phase'], struct.pack('<I', 1))
            for _ in range(20):
                advance(.4)
                if trial_word('paints') or trial_word('error'):
                    break
            native_sample = module['kind'] == 'original-Z7-battery-native-sample-diagnostic'
            capture('battery-module-native-sample' if native_sample else 'battery-module-supplied-63')
            check('module-creates-and-paints-owned-native-object', trial_word('object') != 0 and trial_word('paints') > 0 and trial_word('error') == 0)
            shown = Image.open(io.BytesIO(camera.png)).convert('RGB')
            box = (2, 552, 112, 622)
            check('module-native-text-changes-region', shown.crop(box).tobytes() != baseline.crop(box).tobytes())
            camera.remote.write_memory(base + symbols['z7_battery_trial_phase'], struct.pack('<I', 2))
            for _ in range(20):
                advance(.4)
                if trial_word('phase') == 3 or trial_word('error'):
                    break
            capture('battery-module-retired')
            retired = Image.open(io.BytesIO(camera.png)).convert('RGB')
            result['battery_module_trial'] = dict(supplied_percent=None if native_sample else 63, hardware_telemetry=False,
                native_snapshot_sample=trial_word('percent') if native_sample else None,
                native_sample_valid=trial_word('sample_valid') if native_sample else None,
                phase=trial_word('phase'), paints=trial_word('paints'), error=trial_word('error'))
            check('module-retires-on-native-paint-path', trial_word('phase') == 3 and trial_word('error') == 0)
            check('module-retirement-restores-region', retired.crop(box).tobytes() == baseline.crop(box).tobytes())
        elif args.view == 'inspect':
            gui = query('Native live GUI context', 0x102f2b84, [])
            if not 0xa1800000 <= gui <= 0xbfffffc0 or gui % 4:
                raise ValueError('Unexpected native GUI context pointer')
            result['gui_context'] = dict(pointer=hex(gui), prefix=camera.remote.memory(gui, 64).hex())
            save()
            pool = int.from_bytes(camera.remote.memory(gui + 0x24, 4), 'little')
            if not 0xa1800000 <= pool <= 0xbfffffe0 or pool % 4:
                raise ValueError('Unexpected native GUI pool pointer')
            header = camera.remote.memory(pool, 16)
            result['gui_pool_header'] = dict(pointer=hex(pool), bytes=header.hex())
            save()
            total, _, regular, _ = struct.unpack('<4H', header[:8])
            slots = int.from_bytes(header[8:12], 'little')
            if not 0 < regular <= total <= 4096 or not 0xa1800000 <= slots <= 0xc0000000 - total * 4 or slots % 4:
                raise ValueError('Unexpected native GUI pool shape')
            records = struct.unpack('<' + 'I' * total, camera.remote.memory(slots, total * 4))
            occupied = [dict(slot=i, object=hex(p), prefix=camera.remote.memory(p, 96).hex())
                        for i, p in enumerate(records[:regular]) if p]
            result['gui_pool'] = dict(pointer=hex(pool), header=header.hex(), total=total, regular=regular,
                free_regular=[i for i, p in enumerate(records[:regular]) if not p], occupied=occupied,
                global_class_pools=camera.remote.memory(0xa181c770, 32).hex(),
                main_paint_lists=camera.remote.memory(0xa201e3b4, 16).hex(),
                dynamic_label_registry=camera.remote.memory(0xa2019e78, 12 * 300).hex())
            save()
            capture('native-pool-inspection')
            check('native-gui-pool-inspected', bool(occupied))
            result['native_battery_snapshot'] = camera.remote.memory(0xa235aee4, 56).hex()
            result['native_ui_state_1030d3ca'] = query('Native UI state 1030D3CA, semantics under investigation', 0x1030d3ca, [])
            result['native_battery_controls'] = camera.remote.memory(0xa1824a14, 480).hex()
            if args.battery_text_trial:
                baseline = Image.open(io.BytesIO(camera.png)).convert('RGB')
                slot, label = 1199, 299
                label_address = 0xa2019e78 + label * 12
                label_record = struct.unpack('<3I', camera.remote.memory(label_address, 12))
                check('trial-slot-and-label-currently-unused', regular == 1200 and not records[slot] and
                      label_record[0] == 0 and label_record[1] != 0)
                object_pointer = query('Allocate diagnostic regular object', 0x103fcf0e, [pool, 0, slot])
                check('trial-native-pool-owns-allocation', object_pointer != 0 and
                      int.from_bytes(camera.remote.memory(slots + slot * 4, 4), 'little') == object_pointer)
                def store(offset, value):
                    camera.remote.write_memory(object_pointer + offset, struct.pack('<I', value))
                store(0, 0x7a40); store(4, 2); store(8, label); store(12, 2)
                store(0x10, 10 | (400 << 16)); store(0x14, 70 | (424 << 16))
                store(0x18, 0); store(0x28, 0); store(0x2c, 1)
                store(0x34, 0x1000); store(0x38, 1); store(0x3c, 0x1000); store(0x40, 0x2ed)
                store(0x48, 0xa201e3b4)
                store(0x98, 10 | (400 << 16)); store(0x9c, 70 | (424 << 16))
                camera.call(checkpoint(), 'Set diagnostic label, supplied 63 percent', 0x103fbb5c,
                            b'63%\0' + bytes(28), [('scratch', 0), label, 0])
                native('Initialize diagnostic native HUD text object', 0x10384d82, [object_pointer])
                native('Append diagnostic object to native paint list', 0x103faeba, [0xa201e3b4, object_pointer])
                native('Show diagnostic text', 0x103fb32e, [object_pointer, 1])
                native('Request native text repaint', 0x103fb302, [0xa201e3b4, 1])
                capture('battery-text-supplied-63')
                shown = Image.open(io.BytesIO(camera.png)).convert('RGB')
                box = (14, 568, 100, 604)
                changed = sum(a != b for a, b in zip(baseline.crop(box).getdata(), shown.crop(box).getdata()))
                result['battery_text_trial'] = dict(supplied_percent=63, hardware_telemetry=False,
                    slot=slot, label=label, object=hex(object_pointer), changed_pixels=changed,
                    object_prefix=camera.remote.memory(object_pointer, 96).hex())
                check('trial-text-produces-native-pixels', changed > 10)
                native('Hide diagnostic text', 0x103fb32e, [object_pointer, 0])
                native('Request native restoration', 0x103fb302, [0xa201e3b4, 1])
                capture('battery-text-hidden')
                hidden = Image.open(io.BytesIO(camera.png)).convert('RGB')
                result['battery_text_trial']['native_hide_alone_restores_region'] = hidden.crop(box).tobytes() == baseline.crop(box).tobytes()
                check('trial-hidden-text-restores-region', hidden.crop(box).tobytes() == baseline.crop(box).tobytes())
        elif args.view == 'menu':
            check('native-menu-initial-page', on_page(0x13))
            key('left', lambda: on_page(1)); row(1, 3)
            key('right', lambda: on_page(0x125)); row(0x125, 4)
            key('right', lambda: on_page(0x127)); row(0x127, 28)
            key('right', lambda: on_page(0x153))
            capture('00-menu-initial')
            for index, (name, stored, _) in enumerate(LAYOUTS):
                row(0x153, index)
                key('right', lambda: on_page(0x127))
                key('right', lambda: on_page(0x153))
                step = capture(name)
                check(name + '-native-key-selection-and-focus', step['stored_grid'] == stored and step['pages'][-1]['row'] == index)
        else:
            native('Native grid Off', 0x104f5592, [])
            capture('00-off')
            off_picture = Image.open(io.BytesIO(camera.png)).convert('RGB')
            points = []
            for name, stored, count in LAYOUTS[:-1]:
                native('Module grid choice ' + name, base + module['symbols'][name], [])
                native('Native grid visibility update', 0x10377236, [1])
                step = capture(name)
                check(name + '-native-counts-and-enabled', step['descriptor'][4] == count and step['descriptor'][9] == count and step['enable'] == 1)
                picture = Image.open(io.BytesIO(camera.png)).convert('RGB')
                r = step['registers']
                x, y = r[1] & 65535, (r[0] >> 16) & 16383
                dy, dx = r[4] & 65535, r[4] >> 16
                color = ((r[6] >> 16) & 255, (r[6] >> 8) & 255, r[6] & 255)
                samples = [(picture.width // 2 + 37, y + i * dy) for i in range(count)]
                samples += [(x + i * dx, 300) for i in range(count)]
                check(name + '-native-grid-pixels', all(picture.getpixel(p) == color for p in samples))
                points.extend(samples)
            native('Native grid Off', 0x104f5592, [])
            step = capture('off-restored')
            check('off-clears-grid-plane', step['enable'] == 0)
            restored = Image.open(io.BytesIO(camera.png)).convert('RGB')
            check('off-restores-sampled-scene-pixels', all(restored.getpixel(p) == off_picture.getpixel(p) for p in points))
            for _ in range(8):
                if camera.remote.memory(0xa201d4d0 + 0x18a, 1) == b'\3':
                    break
                camera.key(checkpoint(), 'disp')
                advance(.7)
            capture('histogram-horizon')
            control = int.from_bytes(camera.remote.memory(0xa1827404 + 44, 4), 'little')
            result['histogram_diagnostics'] = dict(
                shooting_kind=camera.remote.memory(0xa201d308 + 0x10, 1).hex(),
                snapshot_mode=camera.remote.memory(0xa201d4d0 + 0x18a, 1).hex(),
                auxiliary_gate=camera.remote.memory(0xa201f698 + 0x1f, 1).hex(),
                control=hex(control), controls=camera.remote.memory(control, 96).hex(),
                masks=camera.remote.memory(0xa1827404 + 4, 36).hex(),
                eligibility=query('Native histogram eligibility', 0x103ebb6c, []),
                exposure_option=query('Native property 102C', 0x104065a4, [0x102c]),
                alternate_option=query('Native property 138D', 0x104065a4, [0x138d]),
                output_exclusion=query('Native gate 12', 0x103ea09e, [12]))
            native('Native histogram visibility refresh', 0x1036d57c, [])
            result['histogram_diagnostics']['after_native_refresh'] = camera.remote.memory(control, 2).hex()
            capture('histogram-horizon-refreshed')
            if args.histogram_context_fixture:
                original_context = camera.remote.memory(0xa201d308 + 0x10, 1)
                result['histogram_context_fixture'] = dict(address='0xa201d318', original=original_context.hex(),
                    supplied='01', derivation='Native visibility routine 0x1036d57c permits the histogram in context 1')
                camera.remote.write_memory(0xa201d308 + 0x10, b'\1')
                native('Native histogram update with supplied context', 0x1036d57c, [])
                result['histogram_context_fixture']['immediate_control'] = camera.remote.memory(control, 2).hex()
            if args.trace_histogram_writes or args.trace_histogram_context:
                watch_address = 0xa201d318 if args.trace_histogram_context else control + 1
                watch = f'2,{watch_address:x},1'
                if camera.remote.command('Z' + watch) != 'OK':
                    raise RuntimeError('Cannot observe histogram control writes')
                try:
                    observations = result.setdefault('histogram_context_writes' if args.trace_histogram_context else 'histogram_control_writes', [])
                    for _ in range(12):
                        camera.remote.send('c'); camera.running = True
                        stopped = camera.receive_stop()
                        regs = camera.remote.registers()
                        if camera.remote.command('z' + watch) != 'OK':
                            raise RuntimeError('Cannot single-step observed histogram write')
                        stopped_thread = stopped.split('thread:')[1].split(';')[0]
                        if camera.remote.command('Hc' + stopped_thread) != 'OK':
                            raise RuntimeError('Cannot select histogram writer CPU')
                        camera.remote.send('s'); camera.running = True
                        stepped = camera.receive_stop()
                        if camera.remote.command('Hc-1') != 'OK':
                            raise RuntimeError('Cannot restore native SMP resume')
                        if camera.remote.command('Z' + watch) != 'OK':
                            raise RuntimeError('Cannot resume histogram write observation')
                        observations.append(dict(stop=stopped, registers=regs,
                            stepped=stepped,
                            control=camera.remote.memory(control, 2).hex(),
                            context=camera.remote.memory(0xa201d308 + 0x10, 1).hex(),
                            mode=camera.remote.memory(0xa201d4d0 + 0x18a, 1).hex()))
                        save()
                        if camera.remote.memory(watch_address, 1) == b'\0':
                            break
                finally:
                    if camera.remote.command('z' + watch) != 'OK':
                        raise RuntimeError('Cannot remove histogram control watchpoint')
            if args.histogram_context_fixture:
                capture('histogram-horizon-context-fixture')
            save()
            check('native-horizon-page-with-histogram-visible', camera.remote.memory(0xa201d4d0 + 0x18a, 1) == b'\3' and
                  camera.remote.memory(control + 1, 1) == b'\1')
            if args.histogram_context_fixture:
                camera.remote.write_memory(0xa201d308 + 0x10, original_context)
                native('Restore original histogram context visibility', 0x1036d57c, [])
                check('restored-original-histogram-context', camera.remote.memory(0xa201d308 + 0x10, 1) == original_context)
        check('same-live-module-retained', state()[12] == base and state()[10] == 8 and camera.proc.poll() is None)
        result['passed'] = True
    except Exception as error:
        result.update(passed=False, error=repr(error))
        raise
    finally:
        watchdog.cancel()
        if bar_fixture:
            result['battery_bar_inputs'] = dict(events=bar_fixture.events, stops=bar_fixture.stops,
                source_sha256=hashlib.sha256((output / 'battery-bar-fixture-source.py').read_bytes()).hexdigest(),
                original_conversion_and_renderer_execute=True, percentage_or_pixels_supplied=False,
                physical_telemetry_verified=False)
        if sample_fixture:
            result['histogram_sample_fixture'] = dict(sample_sha256=sample_fixture.sha256,
                events=sample_fixture.events, scope='Exact owned module buffer/caller only; getter return and bins supplied; no event completion')
        result.update(session=camera.stamp, filesystem_events=fixture.events)
        camera.close_guest()
        save()
    print(json.dumps(dict(passed=True, checks=len(result['checks']), frames=len(result['steps']))))


if __name__ == '__main__':
    main()
