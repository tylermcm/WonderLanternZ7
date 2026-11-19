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

from PIL import Image
from build_z7_module_host import ROOT, STATE, validate_candidate
from probe_z7_module_host import HostCamera, bind_module_fixture, ui
from cmos_config import active_manifest, active_ingress

LAYOUTS = [('fourths', 1, 3), ('thirds', 2, 2), ('golden', 3, 2), ('center', 4, 1), ('dense', 5, 5), ('off', 0, 0)]


class DisplayCamera(HostCamera):
    def call(self, packet, name, function, payload, arguments):
        if name == 'Waiting for the native display':
            arguments = [100]
        return super().call(packet, name, function, payload, arguments)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--module', type=Path, required=True)
    parser.add_argument('--view', choices=('menu', 'live', 'inspect', 'battery', 'battery-auto'), required=True)
    parser.add_argument('--battery-icon-fixture', action='store_true', help='Supply one native icon visibility request for the automatic GUI test')
    parser.add_argument('--battery-lifecycle', action='store_true', help='Also exercise native MENU entry/return with the automatic overlay')
    parser.add_argument('--histogram-context-fixture', action='store_true',
                        help='Explicitly supply native histogram context 1; not a camera-derived observation')
    parser.add_argument('--trace-histogram-writes', action='store_true', help='Record bounded native histogram control watchpoints')
    parser.add_argument('--trace-histogram-context', action='store_true', help='Observe native context producer instead of widget stores')
    parser.add_argument('--battery-text-trial', action='store_true', help='Diagnostic native text object with supplied 63 percent; inspect view only')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.histogram_context_fixture and args.view != 'live':
        parser.error('Histogram context fixture requires live view')
    if args.battery_text_trial and args.view != 'inspect':
        parser.error('Battery text trial requires inspect view')
    if args.battery_icon_fixture and args.view != 'battery-auto':
        parser.error('Battery icon fixture requires battery-auto view')
    if args.battery_lifecycle and not (args.view == 'battery-auto' and args.battery_icon_fixture):
        parser.error('Battery lifecycle requires battery-auto with its explicit icon fixture')
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists():
        parser.error('Choose a new private evidence directory')
    output.mkdir(parents=True)
    ui.FIRMWARE = args.build / 'module-host.emulator.main.bin'
    ui.FIRMWARE_REPORT = args.build / 'module-host.emulator.json'
    ui.STOCK_CONTAINER = ROOT / '.private/stock/Z_7_0380.bin'
    ui.validate_firmware = validate_candidate
    host = json.loads(ui.FIRMWARE_REPORT.read_text())
    module = json.loads((args.module / 'module.json').read_text())
    packet = (args.module / 'Z7APP.BIN').read_bytes()
    if hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Module fingerprint mismatch')
    fixture = bind_module_fixture(output, packet, host)
    options = {} if args.view == 'menu' else dict(capture_control_test=True,
        raw_source=active_manifest('native0'), exmcu_no_lens=True, tg_periodic_test=True,
        tg_paired_test=True, raw_ingress_test=active_ingress(), isp_boundary_test=True,
        orientation_fixture=0, keep_awake=True, photo_liveview=True)
    camera = DisplayCamera(0, profile='menu' if args.view == 'menu' else 'shooting', **options)
    result = dict(view=args.view, checks=[], steps=[], module_sha256=module['module_sha256'],
        main_sha256=host['main_payload_sha256'], modeled_module_file=True, camera_access=False, physical_card=False,
        supplied_histogram_context=args.histogram_context_fixture)
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
    def capture(name):
        advance(1)
        camera.refresh()
        (output / (name + '.png')).write_bytes(camera.png)
        stored = int.from_bytes(camera.remote.memory(0xa24f182c, 4), 'little')
        step = dict(name=name, stored_grid=stored, frame_sha256=hashlib.sha256(camera.png).hexdigest(), pages=pages())
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
    def query(name, fn, arguments):
        observed = ui.call_fixture(camera.remote, checkpoint(), fn, bytes(32), arguments)
        result.setdefault('native_queries', []).append(dict(name=name, function=hex(fn), arguments=arguments,
                                                          return_r0=observed['return_r0']))
        save()
        return int(observed['return_r0'], 16)
    def stop():
        if camera.proc and camera.proc.poll() is None:
            camera.proc.terminate()
    watchdog = threading.Timer(1200, stop)
    watchdog.daemon = True
    watchdog.start()
    try:
        camera.boot(announce_ready=False) if args.view == 'menu' else camera.boot_shooting()
        checkpoint()
        if args.view != 'menu':
            result['histogram_source_state'] = dict(
                viewport_flag=camera.remote.memory(0xa2367974 + 0x28, 1).hex(),
                native_driver_state=camera.remote.memory(0xa188d70c, 3).hex(),
                normalized_maximum=camera.remote.memory(0xa201d33c, 4).hex())
        check('module-loaded-and-callbacks-committed', state()[10] == 8 and state()[23] == 1 and fixture.finished)
        combined = module['kind'] == 'original-Z7-combined-display-module'
        if args.view not in ('battery', 'battery-auto') or combined:
            for _ in range(20):
                if state()[35]:
                    break
                advance()
            check('grid-menu-published-on-gui-path', state()[35] == 1)
        base = state()[12]
        if args.view == 'battery-auto':
            def automatic_word(name):
                return int.from_bytes(camera.remote.memory(base + module['symbols']['z7_battery_' + name], 4), 'little')
            def enable(value):
                camera.remote.write_memory(base + module['symbols']['z7_battery_enabled'], struct.pack('<I', value))
            capture('automatic-native-context')
            check('no-native-battery-icon-means-no-overlay', automatic_word('object') == 0 and automatic_word('samples') == 0)
            if args.battery_icon_fixture:
                enable(0)
                result['battery_icon_fixture'] = dict(scope='One supplied native control visibility request; native widget renderer initializes icon',
                    original_controls=[camera.remote.memory(0xa1824a14 + i * 48, 2).hex() for i in (0, 1)],
                    original_bar=camera.remote.memory(0xa201d4d0 + 0x1aa, 1).hex(), supplied_bar=1,
                    percentage_supplied=False)
                camera.remote.write_memory(0xa201d4d0 + 0x1aa, b'\1')
                for i in (0, 1): camera.remote.write_memory(0xa1824a14 + i * 48, b'\1\1')
                native('Native stock battery widget renderer after supplied visibility request', 0x102f40a0, [])
                capture('automatic-stock-icon-baseline')
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
                camera.remote.write_memory(0xa201d4d0 + 0x1aa, b'\0')
                native('Native adapter glyph for exclusion check', 0x102f40a0, [])
                count = automatic_word('samples'); enable(1)
                capture('automatic-adapter-excluded')
                check('adapter-glyph-never-enables-percentage', automatic_word('samples') == count and
                      camera.remote.memory(automatic_word('object') + 40, 4) == bytes(4))
                if args.battery_lifecycle:
                    def request_icon(label):
                        result['battery_icon_fixture'].setdefault('additional_requests', []).append(label)
                        camera.remote.write_memory(0xa201d4d0 + 0x1aa, b'\1')
                        for i in (0, 1): camera.remote.write_memory(0xa1824a14 + i * 48, b'\1\1')
                        native('Native battery renderer, one GUI request: ' + label, 0x102f40a0, [])
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
        result.update(session=camera.stamp, filesystem_events=fixture.events)
        camera.close_guest()
        save()
    print(json.dumps(dict(passed=True, checks=len(result['checks']), frames=len(result['steps']))))


if __name__ == '__main__':
    main()
