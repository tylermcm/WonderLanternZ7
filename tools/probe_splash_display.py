"""Present an original PNG through stock Z7 code in an isolated assisted QEMU.

Diagnostic guest calls only: no firmware patch, startup hook, camera or card.
Raw call traces and LCD frames must remain in a new directory under .private/.
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

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'z7-qemu/tools'))
import interactive as ui
import probe

STOCK_SHA = 'e6df1764323fb1c287159dd3ce1c84ac93c72b96ba6eb09c070295c093fecbff'
CHECKPOINT = 0x100531BC
DRAW_PNG = 0x10431738
NATIVE_PATH = (0x104310B4, 0x104313D0, 0x10431278,
               0x104311F4, 0x10430256, 0x1042EB0E)


def splash_asset():
    """Original fixed RGB test card; no firmware artwork or external files."""
    image = Image.new('RGB', (720, 480), (8, 18, 26))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((60, 90, 659, 389), radius=16,
                           outline=(30, 210, 190), width=4)
    for xy, text, size, color in [
        ((360, 165), 'WONDERLANTERN', 44, (230, 250, 250)),
        ((360, 240), 'Z7', 64, (30, 210, 190)),
        ((360, 325), 'NATIVE PNG / EMULATOR TEST', 22, (170, 190, 200)),
    ]:
        draw.text(xy, text, font=ImageFont.load_default(size=size),
                  fill=color, anchor='mm')
    encoded = io.BytesIO()
    image.save(encoded, format='PNG')
    return image, encoded.getvalue()


def draw_native(camera, packet, encoded, native, check):
    """Render heap-backed encoded data with a small guarded call descriptor.

    ``native`` records diagnostic calls; ``check`` collects bounded evidence.
    The original wrapper waits for drawing before its decoded storage is freed.
    """
    packet, allocation = native(packet, 0x1016FE38, bytes(8), [len(encoded) + 32, 0])
    encoded_base = int(allocation['return_r0'], 16)
    if not 0xA1800000 <= encoded_base < 0xAC000000:
        raise RuntimeError('Original heap allocator did not return guest RAM')
    guarded_png = b'L' * 16 + encoded + b'R' * 16
    for offset in range(0, len(guarded_png), 1024):
        chunk = guarded_png[offset:offset + 1024]
        assert camera.remote.command(f'M{encoded_base + offset:x},{len(chunk):x}:' + chunk.hex()) == 'OK'
    payload = bytearray(80)
    saved_registers = camera.remote.command('g')
    scratch = (struct.unpack_from('<I', bytes.fromhex(saved_registers), 52)[0]
               - len(payload) - 7) & ~7
    previous_scratch = camera.remote.memory(scratch, len(payload))
    struct.pack_into('<II', payload, 0, encoded_base + 16, len(encoded))
    payload[-16:] = b'G' * 16
    previous_trace = list(probe.TRACE_CALL)
    probe.TRACE_CALL = sorted(set(previous_trace) | set(NATIVE_PATH))
    packet, render = native(packet, DRAW_PNG, payload,
                            [0, 0, ('scratch', 0), ('scratch', 48)])
    probe.TRACE_CALL = previous_trace
    check('caller-register-context-restored', camera.remote.command('g') == saved_registers)
    check('caller-scratch-restored', camera.remote.memory(scratch, len(payload)) == previous_scratch)
    returned = bytes.fromhex(render['output'])
    check('encoded-png-and-heap-guards-unchanged',
          camera.remote.memory(encoded_base, len(guarded_png)) == guarded_png)
    check('descriptor-trailing-guard-intact', returned[-16:] == payload[-16:])
    observed = {int(event['registers']['r15'], 16) for event in render['trace']}
    check('native-header-decoder-and-gpu-path-observed', set(NATIVE_PATH) <= observed)
    packet, _ = native(packet, 0x1016FE4A, bytes(8), [encoded_base])
    return packet, observed


def run(stock, output):
    if hashlib.sha256(stock.read_bytes()).hexdigest() != STOCK_SHA:
        raise ValueError('Requires the pinned original Z7 C 3.80 MAIN')
    output = output.resolve()
    output.relative_to((ROOT / '.private').resolve())
    if output == (ROOT / '.private').resolve() or output.exists():
        raise ValueError('Use a new subdirectory under .private/')
    output.mkdir(parents=True)
    ui.FIRMWARE = stock.resolve()
    ui.FIRMWARE_REPORT = ui.STOCK_CONTAINER = None
    camera = ui.Camera(0, profile='menu')
    checks, calls = [], []

    def check(name, passed):
        checks.append(dict(name=name, passed=bool(passed)))

    def stop_owned_guest():
        if camera.proc and camera.proc.poll() is None:
            camera.proc.terminate()

    watchdog = threading.Timer(120, stop_owned_guest)
    watchdog.daemon = True
    watchdog.start()

    def native(packet, function, payload, args):
        result = probe.call_fixture(camera.remote, packet, function, payload, args)
        calls.append(result)
        (output / 'native-calls.json').write_text(json.dumps(calls, indent=2), encoding='utf-8')
        return 'T05thread:' + result['return_cpu'] + ';', result

    def settle(packet):
        packet, result = native(packet, 0x1017081E, bytes(8), [1000])
        check('native-task-delay-success', int(result['return_r0'], 16) == 0)
        return packet

    def key(name):
        # Let the caller's original task execute between AutoOperation inputs,
        # matching the interactive worker rather than chaining at a saved PC.
        if not camera.running:
            camera.continue_guest()
        time.sleep(.15)
        camera.pause()
        packet = camera.run_to(CHECKPOINT)
        packet = camera.key(packet, name)
        camera.continue_guest()
        time.sleep(.15)
        camera.pause()
        return settle(camera.run_to(CHECKPOINT))

    def frame(name):
        camera.refresh()
        (output / name).write_bytes(camera.png)
        image = Image.open(io.BytesIO(camera.png)).convert('RGB')
        return image.tobytes()

    def wait_for_menu():
        # boot() returns before the asynchronous native menu has finished.
        # Observe a nonblank, stable LCD instead of drawing into an unready GPU.
        deadline = time.monotonic() + 40
        previous, stable = None, 0
        while time.monotonic() < deadline:
            camera.refresh()
            pixels = Image.open(io.BytesIO(camera.png)).convert('RGB').tobytes()
            populated = sum(pixels) > 1_000_000
            stable = stable + 1 if populated and pixels == previous else 0
            if stable >= 3:
                return
            previous = pixels
            time.sleep(.15)
        raise TimeoutError('Native menu did not become visibly stable')

    try:
        camera.boot(enter_menu=True, announce_ready=False)
        wait_for_menu()
        camera.pause()
        packet = camera.run_to(CHECKPOINT)
        packet = key('left')
        expected_menu = frame('00-expected-tab-focus.png')
        packet = key('right')
        baseline = frame('01-menu.png')
        image, encoded = splash_asset()
        (output / 'original-test-asset.png').write_bytes(encoded)
        packet, observed = draw_native(camera, packet, encoded, native, check)
        shown = frame('02-splash.png')
        check('full-lcd-exact-source-rgb-match', shown == image.tobytes())
        check('splash-differs-from-native-menu', shown != baseline)
        # The exact same native tab-focus scene was sampled before the splash.
        packet = key('left')
        restored = frame('04-menu-restored.png')
        check('native-menu-restored-exactly', restored == expected_menu)
        packet = key('right')
        navigated = frame('05-menu-navigation.png')
        check('menu-navigation-after-dismissal', navigated != restored and navigated != shown)
        camera.continue_guest()
        check('guest-resumes-running', camera.monitor.command('query-status')['running'])
        result = dict(schema=1, diagnostic_hle=True, stock_main_sha256=STOCK_SHA,
                      qemu_binary_sha256=json.loads(ui.BUILD_MANIFEST.read_text())['binary_sha256'],
                      checks=checks, evidence_checks_passed=all(c['passed'] for c in checks),
                      image_size=list(image.size), encoded_png_bytes=len(encoded),
                      source_rgb_sha256=hashlib.sha256(image.tobytes()).hexdigest(),
                      lcd_rgb_sha256=hashlib.sha256(shown).hexdigest(),
                      native_interfaces=dict(draw_wrapper=hex(DRAW_PNG),
                                             observed=[hex(a) for a in NATIVE_PATH if a in observed]),
                      firmware_built=False, candidate_cleared=False,
                      limitations=[
                          'Assisted stock guest; runtime PNG data and native diagnostic calls supplied by host.',
                          'Full LCD pixels verified against source; no host screen overlay or framebuffer pixel writes.',
                          'MENU redraw dismissal tested; no production timeout/key handler or once-per-power-on hook.',
                          'No physical camera timing, wake suppression, EVF switching, firmware update or recovery test.',
                      ])
        (output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        return result
    finally:
        if probe.ACTIVE_FIXTURE is not None:
            (output / 'incomplete-call.json').write_text(
                json.dumps(probe.ACTIVE_FIXTURE, indent=2), encoding='utf-8')
        probe.TRACE_CALL = []
        watchdog.cancel()
        camera.close_guest()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.stock, args.output)
    print(json.dumps(dict(passed=result['evidence_checks_passed'], checks=len(result['checks']),
                          output=str(args.output), candidate_cleared=False)))
    raise SystemExit(not result['evidence_checks_passed'])
