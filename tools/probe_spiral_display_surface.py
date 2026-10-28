"""Exercise the original Z7 EVF-sized bitmap and PNG code in assisted QEMU.

This supplies the active grid display ID in emulator RAM and calls the draw
entry explicitly. It is not a native eye-sensor switch or EVF scanout test.
No descriptor, registry, pixel buffer or firmware code is written by the host.
"""
import argparse
import hashlib
import json
import struct
import threading
from pathlib import Path
from PIL import Image

from build_spiral_lifecycle import ROOT, validate_candidate
from probe_grid_firmware import GridCamera, CHECKPOINT
from spiral_geometry import spiral_points
import interactive as ui
from cmos_config import active_manifest, active_ingress
import probe


def run(build, output):
    output = output.resolve()
    output.relative_to((ROOT / '.private').resolve())
    if output.exists() or output == (ROOT / '.private').resolve():
        raise ValueError('Use a new private output subdirectory')
    output.mkdir(parents=True)
    ui.FIRMWARE = build / 'spiral.emulator.main.bin'
    ui.FIRMWARE_REPORT = build / 'spiral.emulator.json'
    ui.STOCK_CONTAINER = ROOT / '.private/stock/Z_7_0380.bin'
    ui.validate_firmware = validate_candidate
    report = json.loads(ui.FIRMWARE_REPORT.read_text())
    assert report['preset'] == 'grid-spiral-display-lifecycle-emulator-only'
    camera = GridCamera(0, profile='shooting', capture_control_test=True,
        raw_source=active_manifest('native0'), exmcu_no_lens=True,
        tg_periodic_test=True, tg_paired_test=True, raw_ingress_test=active_ingress(),
        isp_boundary_test=True, orientation_fixture=0, keep_awake=True, photo_liveview=True)
    result = dict(schema=1, checks=[], calls=[], scope=__doc__.strip(),
        main_payload_sha256=report['main_payload_sha256'], camera_access=False,
        card_access=False, evf_scanout_verified=False, supplied_grid_display_id=4)

    def save():
        (output / 'result.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')

    def check(name, passed):
        result['checks'].append(dict(name=name, passed=bool(passed)))
        save()
        if not passed:
            raise AssertionError(name)

    def call(address, args=()):
        if camera.running:
            camera.pause()
        packet = camera.run_to(CHECKPOINT)
        entry = probe.call_fixture(camera.remote, packet, address, bytes(32), args)
        result['calls'].append(entry)
        save()
        return int(entry['return_r0'], 16)

    watchdog = threading.Timer(700, lambda: camera.proc.terminate()
        if camera.proc and camera.proc.poll() is None else None)
    watchdog.daemon = True
    watchdog.start()
    original_grid = None
    try:
        print('Booting native EVF bitmap diagnostic', flush=True)
        camera.boot_shooting()
        call(int(report['features']['grid']['functions']['golden'], 16))
        descriptor = call(0x10433B80, [1, 4, 0])
        native = camera.remote.memory(descriptor, 64)
        width, height = struct.unpack_from('<HH', native, 8)
        buffer = struct.unpack_from('<I', native, 0x24)[0]
        result['native_descriptor'] = dict(address=hex(descriptor), data=native.hex())
        check('native-evf-shape', (width, height) == (1280, 960) and buffer != 0)
        check('native-evf-bitmap-setup', call(0x10434378, [1, 4, 0]) == 1)
        table = int.from_bytes(camera.remote.memory(0xA180AD88, 4), 'little')
        records = camera.remote.memory(table, 660)
        result['registry_after_native_setup'] = records.hex()
        matches = [i for i in range(33) if struct.unpack_from('<I', records, i*20)[0] == buffer
            and records[i*20+4] != 255 and struct.unpack_from('<HH', records, i*20+6) == (width, height)]
        check('unique-native-evf-registration', len(matches) == 1)
        check('native-rgba-registry-format', struct.unpack_from('<I', records, matches[0]*20+12)[0] == 0)
        current = call(0x10414756)
        # Capture curve points outside the entire LCD-sized rectangle. These
        # are byte comparisons of native memory, never host-rendered pixels.
        # Native RGBA bitmap row zero is the bottom of the image. LCD scanout
        # performs the presentation transform; this is a raw-memory check.
        points = list(dict.fromkeys((round(x), height-1-round(y))
            for x, y in spiral_points(width, height)
            if x > 730 or height-1-y > 490))[::8]
        def samples():
            # Native registry format 0 and the emulator GPU contract use four
            # RGBA bytes per pixel, not RGB565 halfwords.
            return [camera.remote.memory(buffer + (y*width+x)*4, 4).hex() for x, y in points]
        before = samples()
        original_grid = camera.remote.memory(0xA1829E44, 4)
        check('supplied-grid-display-id', camera.remote.command('Ma1829e44,4:04000000') == 'OK')
        check('evf-draw-entry-return', call(int(report['features']['spiral_probe']['draw'], 16)) == 1)
        after = samples()
        pixels = camera.remote.memory(buffer, width*height*4)
        (output / 'native-evf-rgba.bin').write_bytes(pixels)
        # A direct view of guest memory, with no composition or overlay added.
        Image.frombytes('RGBA', (width, height), pixels).save(output / 'native-evf-rgba.png')
        result['native_bitmap_sha256'] = hashlib.sha256(pixels).hexdigest()
        result['samples'] = [dict(x=x, y=y, before=a, after=b) for (x, y), a, b in zip(points, before, after)]
        check('native-pixels-change-beyond-lcd-bounds', sum(a != b for a, b in zip(before, after)) > 20)
        check('native-gray-pixels-beyond-lcd-bounds', sum(b == 'd8d8d8ff' for b in after) > 20)
        check('native-current-target-restored', call(0x10414756) == current)
        result.update(all_passed=True, session=camera.stamp)
        save()
        print(json.dumps(dict(all_passed=True, checks=len(result['checks']))), flush=True)
    except Exception as error:
        result.update(all_passed=False, error=repr(error), session=camera.stamp)
        save()
        raise
    finally:
        if original_grid is not None and camera.proc and camera.proc.poll() is None:
            camera.remote.command('Ma1829e44,4:'+original_grid.hex())
        watchdog.cancel()
        camera.close_guest()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.build.resolve(), args.output)
