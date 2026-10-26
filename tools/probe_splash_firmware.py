"""Boot the actual splash MAIN in assisted QEMU; observe pixels via QMP only.

Uses the existing stock boot/power/MENU fixtures. There is no host splash
controller, image upload, rendering interception or lifecycle-state write.
Firmware and all frames remain private; the summary contains source evidence.
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
from probe_splash_display import ROOT, CHECKPOINT, ui, probe, splash_asset
from build_splash_firmware import validate_candidate
from z30_extensions.features.splash_z7 import STATE, CURSOR, MAGIC, GUARD, FIRST_RENDER_CALLER

BaseQMP = ui.QMP


class SerializedQMP(BaseQMP):
    def __init__(self, port):
        self.command_lock = threading.RLock()
        super().__init__(port)

    def command(self, name, arguments=None):
        with self.command_lock:
            return super().command(name, arguments)


class ObservedCamera(ui.Camera):
    """Add screenshot observation only; inherit all boot/control behavior."""
    def __init__(self, output):
        super().__init__(0, profile='menu')
        self.output = output
        self.stop_observing = threading.Event()
        self.observer = None
        self.frames, self.observer_errors = [], []
        self.last_frame_change = time.monotonic()

    def observe(self):
        previous = None
        started = time.monotonic()
        ppm = self.output / 'observer.ppm'
        try:
            while not self.stop_observing.is_set():
                self.monitor.command('screendump', {'filename': str(ppm)})
                w, h, pixels = ui.ppm_pixels(ppm.read_bytes())
                digest = hashlib.sha256(pixels).hexdigest()
                if digest != previous:
                    name = f'observed-{len(self.frames):03d}.png'
                    (self.output / name).write_bytes(ui.rgb_png(w, h, pixels))
                    self.frames.append(dict(file=name, seconds=round(time.monotonic() - started, 4),
                                            rgb_sha256=digest, black=not any(pixels)))
                    self.last_frame_change = time.monotonic()
                    previous = digest
                self.stop_observing.wait(.025)
        except Exception as exc:
            self.observer_errors.append(repr(exc))

    def run_to(self, address):
        if self.observer is None:
            self.observer = threading.Thread(target=self.observe, daemon=True)
            self.observer.start()
        return super().run_to(address)

    def stop_observer(self):
        self.stop_observing.set()
        if self.observer:
            self.observer.join(6)


def one_boot(output):
    output.mkdir()
    camera = ObservedCamera(output)
    checks = []
    expected = hashlib.sha256(splash_asset()[0].tobytes()).hexdigest()

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

    def state():
        return list(struct.unpack('<16I', camera.remote.memory(STATE, 64)))

    def key(name):
        if not camera.running:
            camera.continue_guest()
        time.sleep(.15)
        packet = checkpoint()
        camera.key(packet, name)
        camera.continue_guest()
        earliest_settle = time.monotonic() + 1.8
        time.sleep(.25)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if time.monotonic() >= earliest_settle and time.monotonic() - camera.last_frame_change > 1.5:
                break
            time.sleep(.1)
        else:
            raise TimeoutError('Native menu redraw did not settle after ' + name)
        return checkpoint()

    def stop_owned():
        if camera.proc and camera.proc.poll() is None:
            camera.proc.terminate()

    watchdog = threading.Timer(180, stop_owned)
    watchdog.daemon = True
    watchdog.start()
    try:
        camera.boot(enter_menu=True, announce_ready=False)
        # Wait on observed scene completion, not an assumed three-second boot.
        # PNG decode and rendering wall time vary under instrumented TCG.
        deadline = time.monotonic() + 50
        while time.monotonic() < deadline:
            frames = list(camera.frames)
            if (any(f['rgb_sha256'] == expected for f in frames) and frames
                    and not frames[-1]['black'] and frames[-1]['rgb_sha256'] != expected
                    and time.monotonic() - camera.last_frame_change > 1.5):
                break
            time.sleep(.1)
        else:
            raise TimeoutError('Firmware splash/native scene did not finish')
        packet = checkpoint()
        first_state = state()
        baseline = frame('native-menu-after-firmware-splash.png')
        nonblack = [f for f in camera.frames if not f['black']]
        splash_frames = [f for f in camera.frames if f['rgb_sha256'] == expected]
        check('capture-starts-black', bool(camera.frames) and camera.frames[0]['black'])
        check('first-observed-nonblack-is-exact-splash', bool(nonblack) and nonblack[0]['rgb_sha256'] == expected)
        check('native-menu-follows-splash', bool(nonblack) and nonblack[-1]['rgb_sha256'] != expected
              and any(baseline))
        check('firmware-state-valid', first_state[0] == MAGIC)
        check('firmware-one-presentation-completed', first_state[1:6] == [3, 1, 0, 1, 1]
              and first_state[10] == 1)
        check('firmware-render-boundary-observed', first_state[7] >= 1)
        check('firmware-first-caller-recorded', first_state[8] == FIRST_RENDER_CALLER)
        check('firmware-state-guards-intact', first_state[12:] == [GUARD] * 4)
        cursor = struct.unpack('<I', camera.remote.memory(CURSOR, 4))[0]
        check('native-workspace-reservation-retained', cursor >= STATE + 64 and cursor < 0xAC400000)
        key('left')
        key('right')
        established = frame('established-menu.png')
        key('left')
        focused = frame('tab-focus.png')
        check('native-navigation-responds', focused != established)
        key('right')
        check('native-navigation-restores-scene', frame('restored-menu.png') == established)
        for index, name in enumerate(('menu', 'menu', 'left', 'right', 'down', 'up')):
            key(name)
            words = state()
            check(f'no-rearm-after-{index}-{name}', words[1] == 3 and words[2] == 1 and words[10] == 1)
            check(f'guards-after-{index}-{name}', words[12:] == [GUARD] * 4)
        final_state = state()
        camera.continue_guest()
        check('guest-running-after-navigation', camera.monitor.command('query-status')['running'])
        camera.stop_observer()
        check('screenshot-observer-clean', not camera.observer_errors and not camera.observer.is_alive())
        check('one-observed-splash-through-navigation',
              sum(f['rgb_sha256'] == expected for f in camera.frames) == 1)
        # Changed frames record the start/end of the hold, without host delays
        # inside the firmware task. This is QEMU wall time, not camera timing.
        hold = None
        if splash_frames:
            shown = splash_frames[0]
            after = [f for f in camera.frames if f['seconds'] > shown['seconds']
                     and f['rgb_sha256'] != expected]
            if after:
                hold = round(after[0]['seconds'] - shown['seconds'], 4)
        check('firmware-hold-bounded-in-qemu', hold is not None and .1 < hold < 10)
        return dict(checks=checks, passed=all(c['passed'] for c in checks),
                    initial_state=first_state, final_state=final_state,
                    native_workspace_cursor=hex(cursor), observed_changed_frames=len(camera.frames),
                    first_nonblack_rgb_sha256=nonblack[0]['rgb_sha256'] if nonblack else None,
                    expected_splash_rgb_sha256=expected, qemu_wall_hold_seconds=hold,
                    host_splash_controller=False, firmware_lifecycle=True)
    finally:
        camera.stop_observer()
        (output / 'frames.json').write_text(json.dumps(camera.frames, indent=2), encoding='utf-8')
        (output / 'checks.json').write_text(json.dumps(checks, indent=2), encoding='utf-8')
        if probe.ACTIVE_FIXTURE is not None:
            (output / 'incomplete-call.json').write_text(json.dumps(probe.ACTIVE_FIXTURE, indent=2), encoding='utf-8')
        watchdog.cancel()
        camera.close_guest()


def run(candidate, report_path, stock, output, boots=2):
    identity = validate_candidate(candidate, report_path, stock)
    output = output.resolve()
    output.relative_to((ROOT / '.private').resolve())
    output.mkdir(parents=True, exist_ok=False)
    # Only this isolated experiment selects this stricter full-rebuild validator.
    # Normal firmware presets and installation validation are unchanged.
    ui.validate_firmware = validate_candidate
    ui.FIRMWARE, ui.FIRMWARE_REPORT, ui.STOCK_CONTAINER = candidate.resolve(), report_path.resolve(), stock.resolve()
    ui.QMP = SerializedQMP
    runs = []
    for index in range(boots):
        result = one_boot(output / f'boot-{index + 1}')
        runs.append(result)
        print(json.dumps(dict(boot=index + 1, passed=result['passed'], checks=len(result['checks']),
                              firmware_lifecycle=True)), flush=True)
        (output / 'runs.json').write_text(json.dumps(runs, indent=2), encoding='utf-8')
    summary = dict(schema=1, main_sha256=identity['sha256'], runs=runs,
        passed=all(r['passed'] for r in runs), firmware_built=True, firmware_lifecycle=True,
        host_splash_controller=False, candidate_cleared=False, camera_verified=False,
        limitations=['Assisted QEMU boot/power/system/MENU setup remains necessary.',
                     'QEMU GUI surface is tested; physical LCD/EVF/wake and live-view startup are unverified.',
                     'Frame polling observes sampled order, not every physical scanout.',
                     'No update package, card staging, camera access, recovery or installation clearance.'])
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    return summary


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--stock', type=Path, default=ROOT / '.private/stock/Z_7_0380.bin')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--boots', type=int, choices=(1, 2), default=2)
    a = p.parse_args()
    result = run(a.candidate, a.report, a.stock, a.output, a.boots)
    raise SystemExit(not result['passed'])
