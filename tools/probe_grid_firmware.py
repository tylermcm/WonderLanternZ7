"""Observe a verified grid candidate in isolated assisted QEMU.

Menu mode uses native key events. Live mode invokes the compiled choice handlers
and original visibility update as diagnostic inputs; it does not change tables,
state fields, drawing functions or pixel buffers from the host. All frames/logs
remain private. Neither mode is physical-camera or installation verification.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import sys
import threading
import time

from PIL import Image
from build_grid_firmware import ROOT, validate_candidate

sys.path.insert(0, str(ROOT / 'z7-qemu/tools'))
import interactive as ui
from cmos_config import active_ingress, active_manifest

CHECKPOINT = 0x100531BC


class GridCamera(ui.Camera):
    def run_to(self, address):
        self.remote.sock.settimeout(180)
        return super().run_to(address)

    def call(self, packet, name, function, payload, arguments):
        # Existing 5000-unit startup paint wait can exceed the host timeout.
        # Subsequent QMP frames, rather than this delay, establish observations.
        if name == 'Waiting for the native display':
            arguments = [100]
        self.remote.sock.settimeout(180)
        return super().call(packet, name, function, payload, arguments)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--view', choices=('menu', 'live'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.relative_to((ROOT / '.private').resolve())
    output.mkdir(parents=True, exist_ok=False)
    ui.FIRMWARE = args.build / 'grid.emulator.main.bin'
    ui.FIRMWARE_REPORT = args.build / 'grid.emulator.json'
    ui.STOCK_CONTAINER = ROOT / '.private/stock/Z_7_0380.bin'
    ui.validate_firmware = validate_candidate
    report = json.loads(ui.FIRMWARE_REPORT.read_text())
    functions = {key: int(value, 16) for key, value in report['features']['grid']['functions'].items()}
    native_choice = 'grid_native' in report['features']
    expanded = report['preset'] == 'grid-layouts-emulator-only'
    layouts = report['features']['grid'].get('layouts', [])
    options = {} if args.view == 'menu' else dict(capture_control_test=True,
        raw_source=active_manifest('native0'), exmcu_no_lens=True,
        tg_periodic_test=True, tg_paired_test=True, raw_ingress_test=active_ingress(),
        isp_boundary_test=True, orientation_fixture=0, keep_awake=True, photo_liveview=True)
    camera = GridCamera(0, profile='menu' if args.view == 'menu' else 'shooting', **options)
    result = dict(view=args.view, main_payload_sha256=report['main_payload_sha256'],
                  steps=[], checks=[], camera_access=False, diagnostic_inputs=True)
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
        return camera.run_to(CHECKPOINT)
    def advance(seconds=.4):
        if not camera.running:
            camera.continue_guest()
        time.sleep(seconds)
        return checkpoint()
    def pages():
        pointer = int.from_bytes(camera.remote.memory(0xA181F91C, 4), 'little')
        stride, capacity, count, data = struct.unpack('<4I', camera.remote.memory(pointer, 16))
        if not (0 <= count <= min(capacity, 20) and 4 <= stride <= 1024):
            raise ValueError('Unexpected native page-list shape')
        path = []
        for index in range(count):
            page = int.from_bytes(camera.remote.memory(data + index * stride, 4), 'little')
            word = int.from_bytes(camera.remote.memory(page, 4), 'little')
            a, b = struct.unpack('<2H', camera.remote.memory(page + 22, 4))
            path.append(dict(page=word >> 16, row=a + b))
        return path
    def wait_for(predicate):
        for _ in range(16):
            if predicate():
                return True
            advance()
        return False
    def key(name, predicate):
        # A repeated button may still be held in virtual time. Reissue only
        # while the exact intended page/row transition has not occurred.
        for _ in range(3):
            advance(.2)
            camera.key(checkpoint(), name)
            advance(.6)
            if wait_for(predicate):
                return
        raise RuntimeError('Native key did not reach expected state: ' + name)
    def on_page(page):
        path = pages()
        return bool(path) and path[-1]['page'] == page
    def row(page, target):
        check('row-navigation-page-' + hex(page), on_page(page))
        for _ in range(60):
            current = pages()[-1]['row']
            if current == target:
                return
            following = current + (1 if current < target else -1)
            key('down' if current < target else 'up',
                lambda: on_page(page) and pages()[-1]['row'] == following)
        raise RuntimeError('Native row not reached')
    def capture(name):
        advance(1.5)
        camera.refresh()
        (output / (name + '.png')).write_bytes(camera.png)
        stored = None
        if native_choice:
            stored = int.from_bytes(camera.remote.memory(0xA24F182C, 4), 'little')
            state = (None, int(stored == 2))
        else:
            state = struct.unpack('<2I', camera.remote.memory(0xA9700000, 8))
        step = dict(name=name, state=list(state), pages=pages(),
                    frame_sha256=hashlib.sha256(camera.png).hexdigest())
        if native_choice:
            step['stored_grid_value'] = stored
        if args.view == 'live':
            descriptor = struct.unpack('<hhIHHhhIHHHHBBH', camera.remote.memory(0xA2020C2C, 32))
            registers = [int.from_bytes(camera.remote.memory(0x20145600 + 4*i, 4), 'little') for i in range(7)]
            log = camera.live_log.read_text(errors='replace')
            enables = re.findall(r'Z7_GRID_ENABLE instance=1 value=(\d)', log)
            step.update(descriptor=list(descriptor), registers=registers,
                        enable=int(enables[-1]) if enables else None)
        result['steps'].append(step)
        save()
        print(name, 'choice', state[1], flush=True)
        return step
    def native(name, address, arguments):
        camera.call(checkpoint(), name, address, bytes(32), arguments)
    def terminate():
        if camera.proc and camera.proc.poll() is None:
            camera.proc.terminate()
    watchdog = threading.Timer(900, terminate)
    watchdog.daemon = True
    watchdog.start()
    try:
        if args.view == 'menu':
            camera.boot(announce_ready=False)
            checkpoint()
            check('native-menu-ready', wait_for(lambda: on_page(0x13)))
            key('left', lambda: on_page(1))
            row(1, 3)
            key('right', lambda: on_page(0x125))
            row(0x125, 4)
            key('right', lambda: on_page(0x127))
            row(0x127, 28)
            key('right', lambda: on_page(0x153))
            capture('00-default-off')
            menu_choices = ([(layout['function'], i, int(layout['stored_value'] == 2))
                             for i, layout in enumerate(layouts)] if expanded else
                            [('thirds', 1, 1), ('fourths', 0, 0), ('off', 2, 0)])
            for name, target, choice in menu_choices:
                row(0x153, target)
                key('right', lambda: on_page(0x127))
                key('right', lambda: on_page(0x153))
                step = capture(name)
                check(name + '-retains-choice-and-native-focus',
                      step['state'][1] == choice and step['pages'][-1]['row'] == target)
                if expanded:
                    check(name + '-stores-exact-layout-value',
                          step['stored_grid_value'] == layouts[target]['stored_value'])
        else:
            camera.boot_shooting()
            checkpoint()
            native('Native grid Off', 0x104F5592, [])
            capture('00-off')
            original_picture = Image.open(io.BytesIO(camera.png)).convert('RGB')
            grid_points = []
            live_choices = ([(layout['function'], layout['line_count']) for layout in layouts[:-1]]
                            if expanded else [('thirds', 2), ('fourths', 3)])
            for name, count in live_choices:
                native('Compiled grid choice: ' + name, functions[name], [])
                native('Native grid visibility update', 0x10377236, [1])
                step = capture(name)
                check(name + '-native-counts-and-enable', step['descriptor'][4] == count
                      and step['descriptor'][9] == count and step['enable'] == 1)
                picture = Image.open(io.BytesIO(camera.png)).convert('RGB')
                r = step['registers']
                x, y = r[1] & 65535, (r[0] >> 16) & 16383
                expected_color = ((r[6] >> 16) & 255, (r[6] >> 8) & 255, r[6] & 255)
                dy, dx = r[4] & 65535, r[4] >> 16
                points = [(picture.width // 2 + 37, y + i * dy) for i in range(count)]
                points += [(x + i * dx, 300) for i in range(count)]
                grid_points.extend(points)
                check(name + '-horizontal-and-vertical-pixels',
                      all(picture.getpixel(point) == expected_color for point in points))
                if name == 'golden':
                    d = step['descriptor']
                    check('golden-two-lines-mirror-at-phi-positions',
                          abs(d[3] / d[7] - .236068) < .005
                          and abs(d[8] / d[2] - .236068) < .005)
            native('Native grid Off', 0x104F5592, [])
            step = capture('off-restored')
            check('native-off-disables-plane', step['enable'] == 0)
            restored_picture = Image.open(io.BytesIO(camera.png)).convert('RGB')
            check('native-off-restores-scene-pixels', all(
                restored_picture.getpixel(point) == original_picture.getpixel(point)
                for point in grid_points))
        result['all_passed'] = True
    except Exception as error:
        result.update(all_passed=False, error=repr(error))
        raise
    finally:
        watchdog.cancel()
        camera.close_guest()
        result['session'] = camera.stamp
        save()


if __name__ == '__main__':
    main()
