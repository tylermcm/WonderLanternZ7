"""Observe firmware-owned spiral painting and menu transitions in assisted QEMU.

Choice handlers and native visibility updates are diagnostic inputs. The host
never invokes the spiral drawing entry, uploads its asset, or writes UI pixels.
All screenshots, traces and firmware remain private. No camera/card access.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import threading
import time

from PIL import Image
from build_spiral_lifecycle import ROOT, validate_candidate
from probe_grid_firmware import GridCamera, CHECKPOINT
import interactive as ui
from cmos_config import active_ingress, active_manifest
import probe


def classify_pixels(im):
    """Distinguish the native curve color from Nikon's yellow menu highlight.

    The original (255,208,64) asset is observed as (255,208,65) through this
    assisted QEMU display conversion. Broad 'gold' thresholds also count the
    sidebar's (252,215,37) fill and cannot establish a leftover spiral.
    """
    data = list(im.getdata())
    return dict(scene=sum(r > 200 and g > 240 and b < 40 for r, g, b in data),
                curve=sum(r >= 250 and 206 <= g <= 210 and 62 <= b <= 67
                          for r, g, b in data))


def run(build, output):
    output = output.resolve()
    output.relative_to((ROOT / '.private').resolve())
    if output == (ROOT / '.private').resolve() or output.exists():
        raise ValueError('Use a new private output subdirectory')
    ui.FIRMWARE = build / 'spiral.emulator.main.bin'
    ui.FIRMWARE_REPORT = build / 'spiral.emulator.json'
    ui.STOCK_CONTAINER = ROOT / '.private/stock/Z_7_0380.bin'
    ui.validate_firmware = validate_candidate
    report = json.loads(ui.FIRMWARE_REPORT.read_text())
    output.mkdir(parents=True)
    camera = GridCamera(0, profile='shooting', capture_control_test=True,
        raw_source=active_manifest('native0'), exmcu_no_lens=True,
        tg_periodic_test=True, tg_paired_test=True, raw_ingress_test=active_ingress(),
        isp_boundary_test=True, orientation_fixture=0, keep_awake=True, photo_liveview=True)
    result = dict(schema=1, main_payload_sha256=report['main_payload_sha256'],
                  checks=[], frames=[], diagnostic_calls=[], camera_access=False,
                  card_access=False, host_spiral_draw_calls=0, installation_cleared=False)

    def save():
        (output / 'result.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')

    def check(name, passed):
        result['checks'].append(dict(name=name, passed=bool(passed)))
        save()
        if not passed:
            raise AssertionError(name)

    def checkpoint():
        if camera.running:
            camera.pause()
        return camera.run_to(CHECKPOINT)

    def advance(seconds=1):
        camera.continue_guest()
        time.sleep(seconds)
        return checkpoint()

    def native(address, arguments=()):
        value = probe.call_fixture(camera.remote, checkpoint(), address, bytes(32), arguments)
        result['diagnostic_calls'].append(value)
        save()
        return value

    def picture():
        camera.refresh()
        return Image.open(io.BytesIO(camera.png)).convert('RGB')

    def pixels():
        return classify_pixels(picture())

    def capture(name):
        measured = pixels()
        (output / (name+'.png')).write_bytes(camera.png)
        result['frames'].append(dict(name=name, sha256=hashlib.sha256(camera.png).hexdigest(),
            **measured, grid_value=int.from_bytes(camera.remote.memory(0xA24F182C, 4), 'little'),
            grid_state=camera.remote.memory(0xA1829E40, 20).hex(),
            surface_registry=camera.remote.memory(0xA180AD84, 12).hex()))
        save()
        print(name, measured, flush=True)
        return measured

    def wait_for(predicate, seconds=75):
        deadline = time.monotonic()+seconds
        while time.monotonic() < deadline:
            advance(1.5)
            if predicate(pixels()):
                return True
        return False

    def key(name):
        camera.key(checkpoint(), name)
        advance(2)

    def menu():
        key('menu')
        check('menu-opened', wait_for(lambda p:p['scene'] < 1000, 40))

    def leave_menu():
        for _ in range(2):
            key('menu')
            if wait_for(lambda p:p['scene'] > 10000, 30):
                return
        raise AssertionError('native-menu-did-not-return-to-live-scene')

    def terminate():
        if camera.proc and camera.proc.poll() is None:
            camera.proc.terminate()

    watchdog = threading.Timer(1200, terminate)
    watchdog.daemon = True
    watchdog.start()
    try:
        print('Booting automatic spiral candidate', flush=True)
        camera.boot_shooting()
        functions = report['features']['grid']['functions']
        # Native choice/plane updates are supplied test inputs, not draw calls.
        native(int(functions['golden'], 16))
        native(0x10377236, [1])
        check('live-scene-ready', wait_for(lambda p:p['scene'] > 10000))
        check('spiral-appears-without-host-draw-call', wait_for(lambda p:p['curve'] > 1000))
        capture('00-automatic-golden-spiral')
        advance(5)
        check('automatic-spiral-remains-visible', capture('01-resumed')['curve'] > 1000)
        for cycle in range(2):
            menu()
            check(f'menu-{cycle}-has-no-spiral', capture(f'02-menu-{cycle}')['curve'] < 200)
            leave_menu()
            check(f'spiral-returns-automatically-{cycle}', wait_for(lambda p:p['curve'] > 1000))
            capture(f'03-returned-{cycle}')
        # Setting changes in an actual camera are made while the menu owns the
        # surface. Invoke the exact choice handler there, then leave normally.
        for name, value, address in (
                ('thirds', 2, int(functions['thirds'], 16)),
                ('golden', 3, int(functions['golden'], 16)),
                ('off', 0, 0x104F5592)):
            menu()
            native(address)
            leave_menu()
            check(name+'-stored-value', int.from_bytes(camera.remote.memory(0xA24F182C, 4), 'little') == value)
            if value == 3:
                check('golden-reappears-after-choice', wait_for(lambda p:p['curve'] > 1000))
            else:
                advance(3)
                check(name+'-has-no-stale-spiral', pixels()['curve'] < 200)
            capture('04-choice-'+name)
        result.update(all_passed=True,
            scope=__doc__.strip(), session=camera.stamp,
            limits=['No separate spiral menu entry.', 'Direct live-view erase/DISP/EVF/crop/hardware cost not certified.'])
        save()
        print(json.dumps(dict(checks=len(result['checks']), all_passed=True)), flush=True)
        return result
    except Exception as error:
        result.update(all_passed=False, error=repr(error), session=camera.stamp)
        save()
        raise
    finally:
        watchdog.cancel()
        camera.close_guest()


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    run(args.build.resolve(), args.output)
