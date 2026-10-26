"""Automatically show/dismiss a splash in isolated assisted stock QEMU boots.

The host observes a native initialization guard, arms a one-shot and draws
before the first ordinary scene is rendered. This is a lifecycle experiment,
not an installed firmware hook. The host does not patch guest instructions or
write framebuffer pixels.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
import threading
import time

from PIL import Image

from probe_splash_display import (
    ROOT, STOCK_SHA, CHECKPOINT, splash_asset, draw_native, ui, probe,
)

GUARD = 0xA1822D68
UI_INIT_ENTRY, RESOURCE_INIT, CLEAR_GUARD = 0x102697F4, 0x103F9C0A, 0x1026984A
OBSERVE = {UI_INIT_ENTRY, RESOURCE_INIT, CLEAR_GUARD}
FIRST_RENDER = 0x10430256


class StartupCamera(ui.Camera):
    """Observe original startup calls; keep one-shot policy explicitly host-side."""
    def __init__(self, output):
        super().__init__(0, profile='menu')
        self.output, self.events = output, []
        self.pending = False
        self.resource_entries = self.presentations = self.postboot_keys = 0
        self.boot_keys = []
        self.first_frame_callback = None
        self.first_frame_pending = self.first_frame_captured = False
        self.boot_returned = False
        self.phase = 'boot'

    def observe(self, registers, guard, source):
        pc = int(registers['r15'], 16)
        if pc not in OBSERVE:
            return
        self.events.append(dict(phase=self.phase, pc=hex(pc), guard=guard, source=source))
        (self.output / 'startup-events.json').write_text(json.dumps(self.events, indent=2), encoding='utf-8')
        if pc == RESOURCE_INIT:
            self.resource_entries += 1
        # Arm only after original resource initialization has returned, before
        # the native instruction consumes its own guard. The outer initializer
        # also runs on MENU re-entry and is not a boot-only trigger.
        if pc == CLEAR_GUARD and guard == 1 and self.presentations == 0:
            self.pending = True

    def run_to(self, address):
        assert not self.running
        pending = OBSERVE | {address}
        for pc in pending:
            assert self.remote.command(f'Z1,{pc:x},2') == 'OK'
        while True:
            self.remote.send('c')
            self.running = True
            packet = self.receive_stop()
            registers = self.remote.registers()
            pc = int(registers['r15'], 16)
            self.observe(registers, int.from_bytes(self.remote.memory(GUARD, 4), 'little'), 'run-to')
            if pc == address:
                break
            if pc not in pending:
                raise RuntimeError('Unexpected startup observation stop')
            assert self.remote.command(f'z1,{pc:x},2') == 'OK'
            pending.remove(pc)
        for pc in pending:
            self.remote.command(f'z1,{pc:x},2')
        return packet

    def fixture(self, packet, function, payload, args):
        previous = list(probe.TRACE_CALL)
        probe.TRACE_CALL = sorted(set(previous) | OBSERVE)
        try:
            result = probe.call_fixture(self.remote, packet, function, payload, args)
        finally:
            probe.TRACE_CALL = previous
        for event in result['trace']:
            registers = event['registers']
            guard = None
            # At the initializer/clear sites R6 is the native controller base.
            if int(registers['r15'], 16) in {RESOURCE_INIT, CLEAR_GUARD}:
                if int(registers['r6'], 16) == GUARD - 0x10 and 'r6' in event['memory']:
                    guard = struct.unpack_from('<I', bytes.fromhex(event['memory']['r6']), 0x10)[0]
            self.observe(registers, guard, 'native-call-trace')
        self.audit(dict(kind='startup-native-call', result=result))
        return 'T05thread:' + result['return_cpu'] + ';', result

    def call(self, packet, name, function, payload, arguments):
        return self.fixture(packet, function, payload, arguments)[0]

    def key(self, packet, name):
        if self.boot_returned:
            self.postboot_keys += 1
        else:
            self.boot_keys.append(name)
        packet = super().key(packet, name)
        if not self.boot_returned and name == 'menu' and self.first_frame_callback:
            self.first_frame_pending = True
        return packet

    def continue_guest(self):
        if self.first_frame_pending:
            self.first_frame_pending = False
            packet = self.run_to(FIRST_RENDER)
            self.first_frame_captured = True
            self.first_frame_callback(packet)
        return super().continue_guest()


def one_boot(output, hold_seconds):
    output.mkdir()
    camera = StartupCamera(output)
    checks = []

    def check(name, passed):
        checks.append(dict(name=name, passed=bool(passed)))

    def frame(name=None):
        camera.refresh()
        if name:
            (output / name).write_bytes(camera.png)
        return Image.open(io.BytesIO(camera.png)).convert('RGB').tobytes()

    def checkpoint():
        camera.pause()
        return camera.run_to(CHECKPOINT)

    def key(name):
        camera.phase = 'key-' + name
        if not camera.running:
            camera.continue_guest()
        time.sleep(.15)
        packet = checkpoint()
        camera.key(packet, name)
        camera.continue_guest()
        time.sleep(.15)
        packet = checkpoint()
        packet, result = camera.fixture(packet, 0x1017081E, bytes(8), [1000])
        if int(result['return_r0'], 16) != 0:
            raise RuntimeError('Native task delay failed')
        return packet

    def stop_owned():
        if camera.proc and camera.proc.poll() is None:
            camera.proc.terminate()

    watchdog = threading.Timer(120, stop_owned)
    watchdog.daemon = True
    watchdog.start()
    image, encoded = splash_asset()
    shown, held_seconds, held_frames = None, 0, []

    def first_scene(packet):
        nonlocal shown, held_seconds
        camera.phase = 'pre-scene-startup'
        before = frame('01-before-first-scene.png')
        check('pre-splash-display-is-black', not any(before))
        check('first-render-intercepted-before-normal-scene', camera.first_frame_captured)
        check('one-ui-init-entry-before-first-display',
              sum(e['pc'] == hex(UI_INIT_ENTRY) for e in camera.events) == 1)
        check('native-resource-initializer-once', camera.resource_entries == 1)
        check('native-init-consumes-guard', int.from_bytes(camera.remote.memory(GUARD, 4), 'little') == 0)
        check('host-one-shot-armed-by-native-init', camera.pending)
        check('no-postboot-navigation-before-splash', camera.postboot_keys == 0)
        if not camera.pending:
            raise RuntimeError('Cold-start initialization did not arm the diagnostic')
        camera.phase = 'splash'
        camera.pending = False
        camera.presentations += 1
        (output / 'original-test-asset.png').write_bytes(encoded)
        packet, _ = draw_native(camera, packet, encoded, camera.fixture, check)
        shown = frame('02-automatic-splash.png')
        check('automatic-full-lcd-exact-pixels', shown == image.tobytes())
        # Delay the original rendering task using native OS sleeps. Other guest
        # tasks run; the interrupted normal scene cannot overwrite the splash.
        started = time.monotonic()
        delay_ok = True
        while time.monotonic() - started < hold_seconds:
            packet, result = camera.fixture(packet, 0x1017081E, bytes(8), [100])
            delay_ok &= int(result['return_r0'], 16) == 0
            held_frames.append(frame() == image.tobytes())
        held_seconds = time.monotonic() - started
        check('native-task-delays-complete', delay_ok)
        check('splash-survives-running-guest-hold', bool(held_frames) and all(held_frames))
        check('bounded-host-hold-completes', hold_seconds <= held_seconds < hold_seconds + 3)
        camera.phase = 'automatic-dismissal'
        # Restore the black backing surface through stock PNG/GPU code before
        # resuming its interrupted first draw, so no splash fragments remain.
        clear = io.BytesIO()
        Image.new('RGB', image.size, (0, 0, 0)).save(clear, format='PNG')
        packet, _ = draw_native(camera, packet, clear.getvalue(), camera.fixture, check)
        check('native-black-backing-restored', frame('03-native-backing-restored.png') == before)
        camera.phase = 'resuming-first-scene'

    camera.first_frame_callback = first_scene
    try:
        # The existing MENU fixture schedules the native first scene. Intercept
        # its first rendering call while the visible surface is still black.
        camera.boot(enter_menu=True, announce_ready=False)
        camera.boot_returned = True
        previous, stable = None, 0
        deadline = time.monotonic() + 40
        while time.monotonic() < deadline:
            pixels = frame()
            stable = stable + 1 if pixels == previous and sum(pixels) > 1_000_000 and pixels != shown else 0
            if stable >= 3:
                break
            previous = pixels
            time.sleep(.15)
        else:
            raise TimeoutError('Native first scene did not finish after the splash')
        packet = checkpoint()
        baseline = frame('04-first-scene-after-splash.png')
        check('normal-menu-appears-after-splash', baseline != shown and any(baseline))
        # The native help-icon backing changes after its first focus cycle.
        # Sample the exact comparison scene in the same established focus state.
        key('left')
        key('right')
        baseline = frame('05-established-menu-scene.png')
        key('left')
        focused = frame('06-native-tab-focus.png')
        check('native-menu-focus-navigation-changes-scene', focused != baseline)
        key('right')
        restored = frame('07-native-scene-restored.png')
        check('post-splash-menu-navigation-restores-scene', restored == baseline)
        for index, name in enumerate(['menu', 'menu', 'left', 'right', 'down', 'up']):
            key(name)
            pixels = frame(f'08-{index}-{name}.png')
            check(f'guard-remains-consumed-after-{index}-{name}',
                  int.from_bytes(camera.remote.memory(GUARD, 4), 'little') == 0)
            check(f'no-splash-after-{index}-{name}', pixels != shown)
        check('native-resource-init-not-reentered', camera.resource_entries == 1)
        check('outer-ui-init-reentered-without-resource-reinit',
              sum(e['pc'] == hex(UI_INIT_ENTRY) for e in camera.events) > 1)
        check('single-presentation-no-rearm', camera.presentations == 1 and not camera.pending)
        camera.continue_guest()
        check('normal-guest-running-after-cycle', camera.monitor.command('query-status')['running'])
        return dict(checks=checks, passed=all(c['passed'] for c in checks),
                    native_startup_events=camera.events,
                    image_size=list(image.size), encoded_png_bytes=len(encoded),
                    lcd_rgb_sha256=hashlib.sha256(shown).hexdigest(),
                    boot_key_actions=list(camera.boot_keys), first_visible_scene='splash',
                    presentations=camera.presentations, held_frames=len(held_frames),
                    host_hold_seconds=round(held_seconds, 3))
    finally:
        if probe.ACTIVE_FIXTURE is not None:
            (output / 'incomplete-call.json').write_text(json.dumps(probe.ACTIVE_FIXTURE, indent=2), encoding='utf-8')
        probe.TRACE_CALL = []
        watchdog.cancel()
        camera.close_guest()


def run(stock, output, boots=2, hold_seconds=2):
    if hashlib.sha256(stock.read_bytes()).hexdigest() != STOCK_SHA:
        raise ValueError('Requires the pinned original Z7 C 3.80 MAIN')
    output = output.resolve()
    output.relative_to((ROOT / '.private').resolve())
    if output.exists():
        raise ValueError('Preserve earlier evidence: use a new private output directory')
    output.mkdir(parents=True)
    ui.FIRMWARE = stock.resolve()
    ui.FIRMWARE_REPORT = ui.STOCK_CONTAINER = None
    runs = []
    for index in range(boots):
        result = one_boot(output / f'boot-{index + 1}', hold_seconds)
        runs.append(result)
        print(json.dumps(dict(boot=index + 1, passed=result['passed'],
                              checks=len(result['checks']), presentations=result['presentations'])), flush=True)
    report = dict(schema=1, diagnostic_hle=True, stock_main_sha256=STOCK_SHA,
                  evidence_checks_passed=all(r['passed'] for r in runs), runs=runs,
                  native_guard=hex(GUARD), ui_initializer=hex(UI_INIT_ENTRY),
                  post_resource_arm_observation=hex(CLEAR_GUARD),
                  firmware_built=False, candidate_cleared=False,
                  limitations=[
                      'One-shot scheduling and timed dismissal are host-side emulator policy; no installed firmware hook.',
                      'Native guard/init observed in assisted cold boot and menu exit/re-entry; physical wake/reinitialization semantics unknown.',
                      'Boot uses existing synthetic power/system state and MENU setup. Its first render is intercepted before visible menu pixels; live-view startup is not tested.',
                      'Timeout uses host monotonic seconds with native render-task delays and a native black-image cleanup, not a production firmware lifecycle handler.',
                      'No camera/card access, EVF switching, update acceptance or recovery evidence.',
                  ])
    (output / 'summary.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--boots', type=int, choices=(1, 2), default=2)
    parser.add_argument('--hold-seconds', type=float, default=2)
    args = parser.parse_args()
    if not 0.5 <= args.hold_seconds <= 5:
        parser.error('Use a bounded hold between 0.5 and 5 seconds')
    report = run(args.stock, args.output, args.boots, args.hold_seconds)
    raise SystemExit(not report['evidence_checks_passed'])
