"""Native-menu save and fresh-guest reload of two modeled Z7 journal files.

SPDX-License-Identifier: MIT. Assisted QEMU with explicit module/settings file
HLE; no physical card/camera, staging, native filesystem or durability claim.
Only native keys edit settings; no model/revision/callback/pixel stores supplied.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
import threading

from PIL import Image
from build_z7_module_host import ROOT, STATE, validate_candidate
from probe_z7_module_host import HostCamera, ui
from module_file_fixture import ModuleFileRemote
from settings_file_fixture import SettingsFileFixture
from audit_z7_settings_storage import valid


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--module', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--seed-directory', type=Path, help='Inspect one fresh guest using prior private slot files; not a two-boot acceptance run')
    a = p.parse_args()
    output = a.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists():
        p.error('Choose a new private evidence directory')
    host = json.loads((a.build / 'module-host.emulator.json').read_text(encoding='utf-8'))
    module = json.loads((a.module / 'module.json').read_text(encoding='utf-8'))
    packet = (a.module / 'Z7APP.BIN').read_bytes()
    if module['kind'] != 'original-Z7-display-persistence-diagnostic' or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        p.error('Exact persistent full profile required')
    output.mkdir(parents=True)
    for name in ('probe_z7_persistence.py', 'settings_file_fixture.py', 'module_file_fixture.py'):
        (output / (Path(name).stem + '-source.py')).write_bytes(Path(__file__).with_name(name).read_bytes())
    ui.FIRMWARE = a.build / 'module-host.emulator.main.bin'
    ui.FIRMWARE_REPORT = a.build / 'module-host.emulator.json'
    ui.STOCK_CONTAINER = ROOT / '.private/stock/Z_7_0380.bin'
    ui.validate_firmware = validate_candidate
    result = dict(passed=False, checks=[], phases=[], main_sha256=host['main_payload_sha256'], module_sha256=module['module_sha256'],
                  assisted_qemu=True, modeled_filesystem=True, native_menu_keys=True, model_revision_or_pixel_stores=False,
                  physical_card=False, camera_access=False, shutdown_flush_verified=False)

    def save():
        (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')

    def check(name, good):
        result['checks'].append(dict(name=name, passed=bool(good)))
        save()
        if not good: raise AssertionError(name)

    def boot_phase(name, files):
        directory = output / name
        directory.mkdir()
        phase = dict(name=name, steps=[], seed_files={str(k): hashlib.sha256(v).hexdigest() for k, v in files.items()})
        result['phases'].append(phase)
        class RecordingFixture(SettingsFileFixture):
            def request(self, remote, pointer):
                try:
                    return super().request(remote, pointer)
                finally:
                    (directory / 'filesystem-events.json').write_text(json.dumps(dict(
                        events=self.events, module_finished=self.module_finished, service_finished=self.finished,
                        live_handles=list(map(hex, self.handles)), file_lengths={str(k): len(v) for k, v in self.files.items()}), indent=2) + '\n', encoding='utf-8', newline='\n')
        fixture = RecordingFixture(packet, files)
        class BoundRemote(ModuleFileRemote):
            def __init__(self, port): super().__init__(port, fixture)
        ui.Remote = BoundRemote
        HostCamera.module_fixture = fixture
        HostCamera.module_result_address = host['symbols']['z7_module_result']
        HostCamera.module_waited = False
        camera = HostCamera(0, profile='menu')
        def stop():
            if camera.proc and camera.proc.poll() is None: camera.proc.terminate()
        watchdog = threading.Timer(900, stop)
        watchdog.daemon = True
        watchdog.start()
        symbols = module['symbols']
        base = 0

        def checkpoint():
            if camera.running: camera.pause()
            return camera.run_to(0x100531bc)

        def wait_native(duration=300):
            # Let the actual menu task run; calling delay ON that task starves
            # its own queued repaint work. Pump filesystem stops while another
            # host thread requests a bounded stop, serialized with file RPCs.
            if camera.running: raise RuntimeError('Expected a paused free-run boundary')
            camera.remote.fixture_stop_requested = False
            timer = threading.Timer(duration / 1000, camera.remote.request_fixture_stop)
            timer.daemon = True
            camera.remote.send('c'); camera.running = True
            timer.start()
            try:
                camera.receive_stop()
            finally:
                timer.cancel(); timer.join(1)
                camera.remote.fixture_stop_requested = False

        def word(name):
            return int.from_bytes(camera.remote.memory(base + symbols[name], 4), 'little')

        def settings(): return list(struct.unpack('<10I', camera.remote.memory(base + symbols['z7_menu_settings'], 40)))

        def pages():
            pointer = int.from_bytes(camera.remote.memory(0xa181f91c, 4), 'little')
            stride, capacity, count, data = struct.unpack('<4I', camera.remote.memory(pointer, 16))
            if not 0 <= count <= min(capacity, 20) or not 4 <= stride <= 1024:
                raise RuntimeError('Unexpected native menu stack')
            rows = []
            for i in range(count):
                page = int.from_bytes(camera.remote.memory(data + i * stride, 4), 'little')
                kind = int.from_bytes(camera.remote.memory(page, 4), 'little') >> 16
                rows.append(dict(page=kind, row=sum(struct.unpack('<2H', camera.remote.memory(page + 22, 4)))))
            return rows

        def on_page(number):
            stack = pages()
            return bool(stack) and stack[-1]['page'] == number

        def key(key_name, predicate):
            for _ in range(3):
                wait_native(200)
                camera.key(checkpoint(), key_name)
                for _ in range(12):
                    wait_native(300)
                    if predicate(): return
            raise RuntimeError('Native key did not reach expected state: ' + key_name)

        def row(page, target):
            if not on_page(page): raise RuntimeError('Wrong page for row navigation')
            for _ in range(60):
                current = pages()[-1]['row']
                if current == target: return
                following = current + (1 if current < target else -1)
                key('down' if current < target else 'up', lambda: on_page(page) and pages()[-1]['row'] == following)
            raise RuntimeError('Native row limit exceeded')

        def widgets():
            pool = int.from_bytes(camera.remote.memory(0xa1833548 + 36, 4), 'little')
            if not pool: return [], ['pool-unavailable']
            offset = int.from_bytes(camera.remote.memory(pool + 4, 2), 'little')
            labels, values = struct.unpack('<2I', camera.remote.memory(pool + 8, 8))
            phase['native_pool'] = dict(pointer=hex(pool), label_array_offset=offset, labels=hex(labels), values=hex(values))
            # Original103FCF0E uses the pool-wide offset, not menu row count.
            if offset != 1200: raise RuntimeError('Unexpected original-Z7 label-array offset: ' + str(offset))
            rows, pending = [], []
            for row_number in range(7):
                nodes = []
                for column, cell in enumerate((labels + (offset + row_number) * 4, values + row_number * 28)):
                    node = int.from_bytes(camera.remote.memory(cell, 4), 'little')
                    data = list(struct.unpack('<25I', camera.remote.memory(node, 100))) if node else []
                    font = data[24] if data else 0
                    font_state = list(struct.unpack('<56I', camera.remote.memory(font, 224))) if font else []
                    nodes.append(dict(pointer=hex(node), words=data, font=hex(font), font_words=font_state))
                    if not data or data[17]: pending.append([row_number, column])
                rows.append(nodes)
            return rows, pending

        def capture(label):
            target = result.get('reference_backgrounds', {}).get(label) if name == 'restart' else None
            attempts = []
            for attempt in range(30):
                wait_native(700 if not attempt else (100, 70, 130, 210)[attempt % 4])
                widget_rows, pending = widgets()
                observation = dict(attempt=attempt, pending_widgets=pending)
                attempts.append(observation)
                phase.setdefault('capture_readiness', {})[label] = attempts
                save()
                if pending: continue
                camera.refresh()
                image = Image.open(io.BytesIO(camera.png)).convert('RGB')
                selected = pages()[-1]['row']
                color = list(image.getpixel((100, 64 + selected * 52)))
                observation.update(selected_row=selected, native_selection_rgb=color, sha256=hashlib.sha256(camera.png).hexdigest())
                # Preserve every ready native candidate; select a matching native
                # pulse phase, never a tolerance, mask or rewritten screenshot.
                (directory / (label + '-candidate' + str(attempt) + '.png')).write_bytes(camera.png)
                save()
                if target is not None and color != target: continue
                break
            else:
                raise RuntimeError('Native menu did not reach matching clean paint/pulse state: ' + label)
            (directory / (label + '.png')).write_bytes(camera.png)
            if name == 'first' and label.endswith('-comparison'):
                result.setdefault('reference_backgrounds', {})[label] = color
            phase['steps'].append(dict(name=label, sha256=hashlib.sha256(camera.png).hexdigest(), pages=pages(), model=settings(), widget_rows=widget_rows,
                                       native_selection_rgb=color, revision=word('z7_settings_revision'), saved_revision=word('z7_persistence_saved_revision'),
                                       result=word('z7_persistence_result'), saves=word('z7_persistence_saves')))
            save()

        def wait_saved():
            for _ in range(40):
                wait_native(500)
                if word('z7_persistence_saved_revision') == word('z7_settings_revision') and word('z7_persistence_result') in (5, 6):
                    check(name + '-worker-acknowledges-current-menu-revision-' + str(word('z7_settings_revision')), not fixture.handles)
                    return
            raise RuntimeError('Background settings save did not settle')

        try:
            camera.boot(announce_ready=False)
            checkpoint()
            state = struct.unpack('<64I', camera.remote.memory(STATE, 256))
            base = state[12]
            check(name + '-full-module-loaded-with-persistent-file-service', state[10] == 8 and base and fixture.module_finished and camera.remote.fixture_enabled and not fixture.finished)
            check(name + '-startup-settings-ready-without-retained-handle', word('z7_persistence_ready') == 1 and camera.remote.memory(base + symbols['z7_persistence_files'] + 4, 4) == b'\xff' * 4)
            phase['startup_model'] = settings()
            phase['process_id'] = camera.proc.pid
            if name == 'first':
                check('fresh-files-use-defaults-without-creating-journal', settings() == [0, 15, 1, 0, 5, 10, 127, 7, 0, 127] and fixture.files == {})
            else:
                check('fresh-guest-restores-prior-menu-edits-before-navigation', settings() == result['expected_model'] and not word('z7_settings_revision') and not any(e.get('component') == 'settings' and e['operation'] in ('write', 'create') for e in fixture.events))
            key('left', lambda: on_page(1)); row(1, 3)
            key('right', lambda: on_page(0x125)); row(0x125, 4)
            key('right', lambda: on_page(0x127)); row(0x127, 28)
            key('right', lambda: on_page(0x153)); row(0x153, 6)
            key('right', lambda: on_page(0))
            capture('root-initial')
            if name == 'first':
                row(0, 0); key('right', lambda: settings()[0] == 1); wait_saved()
                capture('master-saved')
                row(0, 6); key('right', lambda: settings()[0] == 3); wait_saved()
                check('two-completed-native-menu-saves-create-both-journal-slots', set(fixture.files) == {0, 1} and all(valid(data) for data in fixture.files.values()))
            row(0, 1); key('right', lambda: word('z7_settings_view') == 1)
            row(0, 2)
            if name == 'first':
                key('right', lambda: settings()[2] == 0); wait_saved()
            capture('standard-grid-off')
            row(0, 1); key('right', lambda: word('z7_settings_view') == 2)
            row(0, 0)
            if name == 'first':
                key('right', lambda: settings()[6] == 126); wait_saved()
            capture('information-shutter-off')
            key('left', lambda: word('z7_settings_view') == 1)
            key('left', lambda: word('z7_settings_view') == 0)
            row(0, 0); capture('root-saved')
            check(name + '-menu-model-and-battery-setting-consistent', settings() == [3, 15, 0, 0, 5, 10, 126, 7, 0, 127] and word('z7_battery_enabled') == 1)
            if name == 'first': result['expected_model'] = settings()
            # Edited controls retain native selection/activation presentation.
            # Compare both guests after the SAME fresh page entry, final model
            # and navigation-only history, preserving all earlier raw captures.
            key('left', lambda: on_page(0x153))
            key('right', lambda: on_page(0))
            row(0, 0); capture('root-comparison')
            row(0, 1); key('right', lambda: word('z7_settings_view') == 1)
            row(0, 2); capture('standard-comparison')
            row(0, 1); key('right', lambda: word('z7_settings_view') == 2)
            row(0, 0); capture('information-comparison')
            check(name + '-comparison-frames-share-complete-final-model', all(s['model'] == result['expected_model'] for s in phase['steps'] if s['name'].endswith('-comparison')))
            phase['final_model'] = settings()
            phase['filesystem_events'] = fixture.events
            phase['dispatch_stops'] = camera.remote.dispatch_stops
            check(name + '-all-records-valid-and-owned-handles-closed', len(fixture.files) == 2 and all(valid(data) for data in fixture.files.values()) and not fixture.handles)
            for slot, data in fixture.files.items(): (directory / ('slot' + str(slot) + '.dat')).write_bytes(data)
            phase['final_files'] = {str(k): hashlib.sha256(v).hexdigest() for k, v in fixture.files.items()}
            return dict(fixture.files)
        finally:
            watchdog.cancel()
            phase['session'] = camera.stamp
            camera.close_guest()
            if fixture.module_finished and not fixture.handles: fixture.retire()
            save()

    try:
        if a.seed_directory:
            seed = a.seed_directory.resolve()
            if not seed.is_relative_to(ROOT / '.private'): raise ValueError('Seed files must remain private')
            files = {i: (seed / ('slot' + str(i) + '.dat')).read_bytes() for i in (0, 1)}
            if not all(valid(data) for data in files.values()): raise ValueError('Exact valid journal seed files required')
            distance = (struct.unpack_from('<I', files[1], 8)[0] - struct.unpack_from('<I', files[0], 8)[0]) & 0xffffffff
            if distance == 0x80000000: raise ValueError('Ambiguous seed generation')
            selected = int(bool(distance and distance < 0x80000000))
            result['expected_model'] = list(struct.unpack_from('<10I', files[selected], 32))
            result['single_inspection_only'] = True
            boot_phase('restart', files)
        else:
            saved = boot_phase('first', {})
            restored = boot_phase('restart', saved)
            check('restart-uses-a-distinct-fresh-guest-process', result['phases'][0]['process_id'] != result['phases'][1]['process_id'])
            check('restart-only-reads-journal-without-rewriting-it', saved == restored)
            for name in ('standard-comparison', 'information-comparison', 'root-comparison'):
                first = Image.open(output / 'first' / (name + '.png')).convert('RGB')
                second = Image.open(output / 'restart' / (name + '.png')).convert('RGB')
                crop = (78, 62, 697, 422)
                check(name + '-fixed-native-menu-region-identical-after-restart', first.size == second.size == (720, 480) and first.crop(crop).tobytes() == second.crop(crop).tobytes())
        result['passed'] = True
    except Exception as error:
        result['error'] = repr(error)
        raise
    finally:
        save()
    print(json.dumps(dict(passed=True, checks=len(result['checks']), phases=len(result['phases']), frames=sum(len(p['steps']) for p in result['phases']))))


if __name__ == '__main__': main()
