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
    parser.add_argument('--view', choices=('menu', 'live'), required=True)
    parser.add_argument('--histogram-context-fixture', action='store_true',
                        help='Explicitly supply native histogram context 1; not a camera-derived observation')
    parser.add_argument('--trace-histogram-writes', action='store_true', help='Record bounded native histogram control watchpoints')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.histogram_context_fixture and args.view != 'live':
        parser.error('Histogram context fixture requires live view')
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
        check('module-loaded-and-callbacks-committed', state()[10] == 8 and state()[23] == 1 and fixture.finished)
        for _ in range(20):
            if state()[35]:
                break
            advance()
        check('grid-menu-published-on-gui-path', state()[35] == 1)
        base = state()[12]
        if args.view == 'menu':
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
            if args.trace_histogram_writes:
                watch = f'2,{control + 1:x},1'
                if camera.remote.command('Z' + watch) != 'OK':
                    raise RuntimeError('Cannot observe histogram control writes')
                try:
                    observations = result.setdefault('histogram_control_writes', [])
                    for _ in range(12):
                        camera.remote.send('c'); camera.running = True
                        stopped = camera.receive_stop()
                        regs = camera.remote.registers()
                        if camera.remote.command('z' + watch) != 'OK':
                            raise RuntimeError('Cannot single-step observed histogram write')
                        camera.remote.send('s'); camera.running = True
                        stepped = camera.receive_stop()
                        if camera.remote.command('Z' + watch) != 'OK':
                            raise RuntimeError('Cannot resume histogram write observation')
                        observations.append(dict(stop=stopped, registers=regs,
                            stepped=stepped,
                            control=camera.remote.memory(control, 2).hex(),
                            context=camera.remote.memory(0xa201d308 + 0x10, 1).hex(),
                            mode=camera.remote.memory(0xa201d4d0 + 0x18a, 1).hex()))
                        save()
                        if camera.remote.memory(control + 1, 1) == b'\0':
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
