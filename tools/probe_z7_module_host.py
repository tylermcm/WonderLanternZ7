"""Boot the independently rebuilt module host in isolated assisted QEMU.

SPDX-License-Identifier: MIT. Optional file service is explicitly modeled; this
emulator supplies no physical card. Firmware, logs and frames remain private.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import threading
import time

from build_z7_module_host import ROOT, STATE, MAGIC, validate_candidate

sys.path.insert(0, str(ROOT / 'z7-qemu/tools'))
import interactive as ui


class HostCamera(ui.Camera):
    module_fixture = None
    module_result_address = None
    module_waited = False

    def continue_guest(self):
        if self.module_fixture and not self.module_waited:
            state = struct.unpack('<64I', self.remote.memory(STATE, 256))
            if state[10] in (0, 1) and state[17] < 100:
                self.run_to(self.module_result_address & ~1)
            self.module_waited = True
            if self.remote.fixture_enabled and not getattr(self.module_fixture, 'module_finished', False):
                state = struct.unpack('<64I', self.remote.memory(STATE, 256))
                raise RuntimeError('Module filesystem fixture did not retire: ' + repr(dict(
                    state=state[:19], events=self.module_fixture.events,
                    opened=self.module_fixture.opened, closed=self.module_fixture.closed)))
        return super().continue_guest()

    def update(self, **values):
        super().update(**values)
        if values.get('message'):
            print(values['message'], flush=True)

    def run_to(self, address):
        self.remote.sock.settimeout(180)
        if self.module_fixture:
            self.remote.refresh_fixture_breakpoint()
        return super().run_to(address)

    def call(self, packet, name, function, payload, arguments):
        self.remote.sock.settimeout(180)
        if self.module_fixture:
            self.remote.refresh_fixture_breakpoint()
        return super().call(packet, name, function, payload, arguments)


def bind_module_fixture(output, packet, host_report):
    """Configure one explicit immutable module file for a fresh guest."""
    from module_file_fixture import ModuleFileFixture, ModuleFileRemote
    class RecordingModuleFileFixture(ModuleFileFixture):
        def request(self, remote, pointer):
            try:
                return super().request(remote, pointer)
            finally:
                (output / 'filesystem-events.json').write_text(json.dumps(dict(
                    events=self.events, position=self.position, opened=self.opened,
                    closed=self.closed, finished=self.finished), indent=2) + '\n', encoding='utf-8')
    fixture = RecordingModuleFileFixture(packet)
    class BoundModuleRemote(ModuleFileRemote):
        def __init__(self, port):
            super().__init__(port, fixture)
    ui.Remote = BoundModuleRemote
    HostCamera.module_fixture = fixture
    HostCamera.module_result_address = host_report['symbols']['z7_module_result']
    HostCamera.module_waited = False
    return fixture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--module', type=Path, help='Explicit read-only diagnostic file service; not a physical card')
    parser.add_argument('--probe-marker', action='store_true', help='Verify the C probe marker in its first BSS word')
    parser.add_argument('--worker-probe-report', type=Path, help='Verify the bounded worker diagnostic counter during free running')
    args = parser.parse_args()
    worker_report = None
    if args.worker_probe_report:
        if not args.module or args.probe_marker:
            parser.error('Worker report requires --module and cannot use --probe-marker')
        worker_report = json.loads(args.worker_probe_report.read_text(encoding='utf-8'))
        if worker_report.get('kind') != 'original-Z7-resident-worker-diagnostic' or worker_report.get('module_sha256') != hashlib.sha256(args.module.read_bytes()).hexdigest():
            parser.error('Exact worker diagnostic module/report required')
        offset = worker_report['symbols']['z7_worker_calls']
        if offset % 4 or not worker_report['image_bytes'] <= offset <= worker_report['image_bytes'] + worker_report['bss_bytes'] - 4:
            parser.error('Worker counter must be an owned BSS word')
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists():
        parser.error('Choose a new private directory')
    output.mkdir(parents=True)
    ui.FIRMWARE = args.build / 'module-host.emulator.main.bin'
    ui.FIRMWARE_REPORT = args.build / 'module-host.emulator.json'
    ui.STOCK_CONTAINER = ROOT / '.private/stock/Z_7_0380.bin'
    ui.validate_firmware = validate_candidate
    module_fixture = None
    if args.module:
        module_fixture = bind_module_fixture(output, args.module.read_bytes(), json.loads(ui.FIRMWARE_REPORT.read_text()))
    camera = HostCamera(0, profile='menu')
    result = dict(checks=[], observations=[], assisted_qemu=True, camera_access=False,
                  physical_card=False, module_loaded=False)
    def save():
        (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    def check(name, passed):
        result['checks'].append(dict(name=name, passed=bool(passed)))
        save()
        if not passed:
            raise AssertionError(name)
    def snapshot(name):
        if camera.running:
            camera.pause()
        words = struct.unpack('<64I', camera.remote.memory(STATE, 256))
        result['observations'].append(dict(name=name, state=list(words)))
        save()
        return words
    def stop():
        if camera.proc and camera.proc.poll() is None:
            camera.proc.terminate()
    watchdog = threading.Timer(300, stop)
    watchdog.daemon = True
    watchdog.start()
    try:
        camera.boot()
        pid = camera.proc.pid
        words = snapshot('after-boot')
        check('native-workspace-state-initialized', words[8] == MAGIC and words[60:] == (0xa5a5a5a5,) * 4)
        check('native-kernel-created-and-started-task', 0 < words[0] < 0x80000000 and words[9] == 2)
        for index in range(60):
            if words[10] not in (0, 1) or words[17] >= 100:
                break
            camera.continue_guest()
            time.sleep(1)
            words = snapshot('wait-' + str(index + 1))
        if module_fixture:
            check('module-loaded-on-native-task', words[10] == 8 and words[17] == 1 and words[16] == 0)
            check('native-heap-retains-executable-module', words[12] % 64 == 0 and words[12] >= words[13] > 0xa1800000 and words[14] > 0)
            check('modeled-read-close-completed', module_fixture.finished and module_fixture.position == len(module_fixture.packet))
            if args.probe_marker:
                image_size = struct.unpack_from('<I', module_fixture.packet, 16)[0]
                marker = int.from_bytes(camera.remote.memory(words[12] + image_size, 4), 'little')
                check('compiled-c-initializer-marker-in-native-heap', marker == 0x5a703801)
            result.update(module_loaded=True, modeled_filesystem=True,
                          module_sha256=hashlib.sha256(module_fixture.packet).hexdigest(),
                          filesystem_events=module_fixture.events)
            if worker_report:
                check('worker-only-registration-published', words[49] & 1 and words[50] == 1 and words[51] == 0 and
                      words[52] == worker_report['image_bytes'] and words[22:24] == (0, 0))
                counter_address = words[12] + worker_report['symbols']['z7_worker_calls']
                initial = int.from_bytes(camera.remote.memory(counter_address, 4), 'little')
                samples = [initial]
                for attempt in range(6):
                    camera.continue_guest()
                    time.sleep(2)
                    snapshot('worker-progress-' + str(attempt + 1))
                    samples.append(int.from_bytes(camera.remote.memory(counter_address, 4), 'little'))
                    if samples[-1] >= initial + 2:
                        break
                result['worker_counter_samples'] = samples
                result['worker_delay_argument'] = 1000
                check('native-resident-worker-advances-without-paint-or-host-counter-writes', samples[-1] >= initial + 2 and all(a <= b for a, b in zip(samples, samples[1:])))
                words = snapshot('worker-settled')
                check('worker-returns-and-releases-running-guard', words[51] == 0 and words[10] == 8)
        else:
            check('bounded-missing-module-worker-completed', words[10] == 1 and words[17] == 100)
            check('missing-module-retains-no-code-image', words[12] == 0 and words[13] == 0)
        camera.continue_guest()
        time.sleep(2)
        camera.refresh()
        check('native-menu-frame-available', bool(camera.png))
        (output / 'menu.png').write_bytes(camera.png)
        result['menu_frame_sha256'] = hashlib.sha256(camera.png).hexdigest()
        camera.pause()
        packet = camera.run_to(0x100531bc)
        camera.key(packet, 'menu')
        camera.continue_guest()
        time.sleep(2)
        after = snapshot('after-menu-key')
        check('same-session-state-retained-after-menu-input', camera.proc.pid == pid and after == words)
        check('guest-alive', camera.proc.poll() is None)
        result['passed'] = True
    except Exception as error:
        result['passed'] = False
        result['error'] = repr(error)
        if module_fixture:
            result['filesystem_events'] = module_fixture.events
        if camera.remote and not camera.running:
            try:
                snapshot('failure')
            except Exception as snapshot_error:
                result['snapshot_error'] = repr(snapshot_error)
        save()
        raise
    finally:
        watchdog.cancel()
        result['session_directory'] = str(camera.directory)
        if module_fixture and camera.remote:
            result['filesystem_dispatch_stops'] = camera.remote.dispatch_stops
            result['filesystem_breakpoint_refreshes'] = camera.remote.breakpoint_refreshes
        try:
            camera.close_guest()
        finally:
            save()
    print(json.dumps(dict(passed=result['passed'], checks=len(result['checks']), output=str(output))))


if __name__ == '__main__':
    main()
