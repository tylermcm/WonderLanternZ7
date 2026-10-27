"""Native PNG/GPU diagnostic over the verified golden grid in assisted QEMU.

Default mode supplies a procedural PNG through guest heap. Compiled mode calls
the independently built ROM entry with its immutable PNG, selects the native UI
surface and restores the prior target. No framebuffer writes, host screenshot
overlay, automatic firmware hook or card I/O.
This tests the drawing path only, not automatic overlay refresh/erase behavior.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import threading
import time

from PIL import Image
from build_grid_firmware import ROOT, validate_candidate
from probe_grid_firmware import GridCamera, CHECKPOINT
from probe_splash_display import draw_native
from spiral_geometry import overlay_png

sys.path.insert(0, str(ROOT / 'z7-qemu/tools'))
import interactive as ui
import probe
from cmos_config import active_ingress, active_manifest


def run(build, output, compiled=False):
    output = output.resolve()
    output.relative_to((ROOT / '.private').resolve())
    if output == (ROOT / '.private').resolve() or output.exists():
        raise ValueError('Use a new private output subdirectory')
    prefix = 'spiral' if compiled else 'grid'
    ui.FIRMWARE, ui.FIRMWARE_REPORT = [build / (prefix + '.emulator.' + ext) for ext in ('main.bin', 'json')]
    ui.STOCK_CONTAINER = ROOT / '.private/stock/Z_7_0380.bin'
    if compiled:
        from build_spiral_probe import validate_candidate as validate_spiral
        ui.validate_firmware = validate_spiral
    else:
        ui.validate_firmware = validate_candidate
    report = json.loads(ui.FIRMWARE_REPORT.read_text())
    if report['preset'] != ('grid-spiral-draw-emulator-only' if compiled else 'grid-layouts-emulator-only'):
        raise ValueError('Requires the independently verified additional-grid candidate')
    output.mkdir(parents=True)
    camera = GridCamera(0, profile='shooting', capture_control_test=True,
        raw_source=active_manifest('native0'), exmcu_no_lens=True,
        tg_periodic_test=True, tg_paired_test=True, raw_ingress_test=active_ingress(),
        isp_boundary_test=True, orientation_fixture=0, keep_awake=True, photo_liveview=True)
    result = dict(schema=1, main_payload_sha256=report['main_payload_sha256'],
                  checks=[], frames=[], camera_access=False, card_access=False,
                  automatic_redraw=False, firmware_built=compiled, installation_cleared=False)
    calls = []
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
    def advance(seconds=1):
        camera.continue_guest()
        time.sleep(seconds)
        return checkpoint()
    def native(packet, address, payload, arguments):
        camera.remote.sock.settimeout(180)
        value = probe.call_fixture(camera.remote, packet, address, payload, arguments)
        calls.append(value)
        (output / 'native-calls.json').write_text(json.dumps(calls, indent=2), encoding='utf-8')
        return 'T05thread:' + value['return_cpu'] + ';', value
    def capture(name):
        camera.refresh()
        (output / (name + '.png')).write_bytes(camera.png)
        result['frames'].append(dict(name=name, sha256=hashlib.sha256(camera.png).hexdigest()))
        save()
        return Image.open(io.BytesIO(camera.png)).convert('RGB')
    def terminate():
        if camera.proc and camera.proc.poll() is None:
            camera.proc.terminate()
    watchdog = threading.Timer(900, terminate)
    watchdog.daemon = True
    watchdog.start()
    try:
        camera.boot_shooting()
        functions = report['features']['grid']['functions']
        # boot_shooting returns before the live-view pipeline and native grid
        # plane necessarily finish initialization. Readiness needs real pixels,
        # not just the returned callback or a nonzero stored choice.
        deadline = time.monotonic() + 180
        ready = False
        while time.monotonic() < deadline:
            packet, _ = native(checkpoint(), int(functions['golden'], 16), bytes(32), [])
            packet, _ = native(packet, 0x10377236, bytes(32), [1])
            packet = advance(1.5)
            camera.refresh()
            picture = Image.open(io.BytesIO(camera.png)).convert('RGB')
            descriptor = struct.unpack('<hhIHHhhIHHHHBBH', camera.remote.memory(0xA2020C2C, 32))
            registers = struct.unpack('<7I', camera.remote.memory(0x20145600, 28))
            x, y = registers[1] & 65535, (registers[0] >> 16) & 16383
            color = tuple((registers[6] >> shift) & 255 for shift in (16, 8, 0))
            points = [(picture.width // 2 + 37, y), (x, 300)]
            if ((descriptor[4], descriptor[9]) == (2, 2) and color == (216, 216, 216)
                    and all(0 <= px < picture.width and 0 <= py < picture.height
                            and picture.getpixel((px, py)) == color for px, py in points)
                    and sum(r > 200 and g > 200 and b < 40 for r, g, b in picture.getdata()) > 10000):
                ready = True
                break
        check('live-pattern-and-golden-lines-visibly-ready', ready)
        baseline = capture('00-golden-grid')
        asset, encoded = overlay_png()
        (output / 'procedural-spiral-rgba.png').write_bytes(encoded)
        result.update(asset_sha256=hashlib.sha256(encoded).hexdigest(), asset_bytes=len(encoded))
        if compiled:
            registry = camera.remote.memory(0xA180AD84, 12)
            table = int.from_bytes(registry[4:8], 'little')
            entries = [camera.remote.memory(table + i * 20, 20).hex() for i in range(33)]
            (output / 'native-surface-registry.json').write_text(
                json.dumps(dict(registry=registry.hex(), entries=entries), indent=2), encoding='utf-8')
            previous_trace = probe.TRACE_CALL
            probe.TRACE_CALL = [0x10413FF4, 0x10414756, 0x104146A8, 0x10431738, 0x10413FFA]
            packet, called = native(packet, int(report['features']['spiral_probe']['draw'], 16), bytes(32), [])
            probe.TRACE_CALL = previous_trace
            check('compiled-ui-draw-entry-completed', int(called['return_r0'], 16) == 1)
            observed = {int(event['registers']['r15'], 16) for event in called['trace']}
            check('native-lock-select-draw-and-unlock-observed',
                  {0x10413FF4, 0x10414756, 0x104146A8, 0x10431738, 0x10413FFA} <= observed)
            check('native-ui-target-restored', camera.remote.memory(0xA180AD84, 1) == registry[:1])
        else:
            packet, observed = draw_native(camera, packet, encoded, native, check)
        capture('01-native-draw-submitted')
        # Submission does not establish presentation. Resume native tasks and
        # wait for the curve's own color to reach LCD pixels.
        deadline = time.monotonic() + 90
        curve_pixels = 0
        while time.monotonic() < deadline:
            advance(1)
            camera.refresh()
            shown = Image.open(io.BytesIO(camera.png)).convert('RGB')
            curve_pixels = sum(r >= 220 and 160 <= g <= 235 and b <= 110
                               for r, g, b in shown.getdata())
            if curve_pixels > 1000:
                break
        check('native-spiral-color-visible-in-lcd', curve_pixels > 1000)
        shown = capture('02-golden-with-spiral')
        result['curve_pixels'] = curve_pixels
        result['drawn_size'] = list(shown.size)
        # Native logical 720x480 coordinates may map onto the 1024x682 live
        # surface. Measure changed pixels and preserved areas without inventing
        # a host transform or injecting a composited screenshot.
        before, after = baseline.tobytes(), shown.tobytes()
        changed = sum(before[i:i+3] != after[i:i+3] for i in range(0, len(before), 3))
        result['changed_pixels'] = changed
        check('transparent-overlay-changes-bounded-small-region', 100 < changed < shown.width * shown.height // 20)
        check('native-grid-scalar-remains-golden', int.from_bytes(camera.remote.memory(0xA24F182C, 4), 'little') == 3)
        check('straight-grid-lines-still-visible',
              all(shown.getpixel(point) == color for point in points))
        advance(2)
        later = capture('03-after-native-resume')
        later_curve_pixels = sum(r >= 220 and 160 <= g <= 235 and b <= 110
                                 for r, g, b in later.getdata())
        result['curve_pixels_after_two_seconds'] = later_curve_pixels
        check('spiral-still-visible-after-two-seconds', later_curve_pixels > 1000)
        result.update(all_passed=True, session=camera.stamp,
                      scope='Diagnostic native PNG decode/GPU drawing over live golden grid. Compiled mode stores asset and drawing entry in independently verified ROM. Automatic refresh and removal are not established.')
        save()
        print(json.dumps(dict(checks=len(result['checks']), all_passed=True, changed_pixels=changed)), flush=True)
        return result
    except Exception as error:
        result.update(all_passed=False, error=repr(error))
        save()
        raise
    finally:
        if probe.ACTIVE_FIXTURE is not None:
            (output / 'incomplete-call.json').write_text(json.dumps(probe.ACTIVE_FIXTURE, indent=2), encoding='utf-8')
        probe.TRACE_CALL = []
        watchdog.cancel()
        camera.close_guest()


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--compiled', action='store_true', help='Call the guarded UI-surface draw entry and immutable ROM asset')
    args = p.parse_args()
    run(args.build.resolve(), args.output, args.compiled)
