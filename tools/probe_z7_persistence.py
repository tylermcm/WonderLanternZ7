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
    p.add_argument('--save-error', action='store_true', help='Supply an owned create error, verify live retry status, then allow retry and restart')
    p.add_argument('--startup-error', action='store_true', help='Supply owned read-open errors at startup, then inspect blocked-save menus using private seed files')
    a = p.parse_args()
    if a.startup_error and (not a.seed_directory or a.save_error): p.error('--startup-error requires --seed-directory and excludes --save-error')
    output = a.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists():
        p.error('Choose a new private evidence directory')
    host = json.loads((a.build / 'module-host.emulator.json').read_text(encoding='utf-8'))
    module = json.loads((a.module / 'module.json').read_text(encoding='utf-8'))
    packet = (a.module / 'Z7APP.BIN').read_bytes()
    lcd_release = module['kind'] == 'original-Z7-LCD-first-release-candidate'
    exposure_component = 0 if lcd_release else 10
    battery_row = 5 if lcd_release else 6
    if module['kind'] not in ('original-Z7-display-persistence-diagnostic','original-Z7-LCD-first-release-candidate') or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
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
                  physical_card=False, camera_access=False, shutdown_flush_verified=False, lcd_first_release=lcd_release)

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
        fixture.fail_open = a.startup_error
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
                # Stock pages may skip unavailable rows. Owned settings rows remain
                # an exact one-row assertion; record and follow native stock focus.
                key('down' if current < target else 'up', lambda: on_page(page) and
                    (pages()[-1]['row'] == following if page == 0 else pages()[-1]['row'] != current))
                phase.setdefault('row_navigation', []).append(dict(page=page, previous=current, observed=pages()[-1]['row'], target=target))
                save()
            raise RuntimeError('Native row limit exceeded')

        def check_row_limit(count, label):
            row(0, count - 1)
            wait_native(200)
            camera.key(checkpoint(), 'down')
            wait_native(500)
            observed = pages()[-1]['row']
            check(name + '-' + label + '-native-focus-stays-in-active-rows', observed < count)
            phase.setdefault('row_limits', []).append(dict(menu=label, count=count, observed_after_down=observed))
            save()

        def widgets():
            pool = int.from_bytes(camera.remote.memory(0xa1833548 + 36, 4), 'little')
            if not pool: return [], ['pool-unavailable']
            offset = int.from_bytes(camera.remote.memory(pool + 4, 2), 'little')
            labels, values = struct.unpack('<2I', camera.remote.memory(pool + 8, 8))
            phase['native_pool'] = dict(pointer=hex(pool), label_array_offset=offset, labels=hex(labels), values=hex(values))
            # Original103FCF0E uses the pool-wide offset, not menu row count.
            if offset != 1200: raise RuntimeError('Unexpected original-Z7 label-array offset: ' + str(offset))
            rows, pending = [], []
            row_count = int.from_bytes(camera.remote.memory(base + symbols['sm_meta'] + 20, 2), 'little') if lcd_release else 7
            if not 1 <= row_count <= 7: raise RuntimeError('Invalid active menu count')
            for row_number in range(row_count):
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

        def header_node():
            def readword(address): return int.from_bytes(camera.remote.memory(address, 4), 'little')
            component = readword(0xa1833548 + 12)
            if not fixture.ram(component, 0xb0): raise RuntimeError('Invalid native menu component')
            first, tail, count = struct.unpack('<3I', camera.remote.memory(component + 0x9c, 12))
            if not 0 < count <= 256: raise RuntimeError('Unexpected native component child count')
            cursor, seen = first, set()
            for _ in range(count):
                if cursor in seen or not fixture.ram(cursor, 12): raise RuntimeError('Invalid native child-list cursor')
                seen.add(cursor)
                previous, following, child = struct.unpack('<3I', camera.remote.memory(cursor, 12))
                if not fixture.ram(child, 100): raise RuntimeError('Invalid native child object')
                words = list(struct.unpack('<25I', camera.remote.memory(child, 100)))
                if words[0] == 0x203: return dict(pointer=hex(child), words=words)
                cursor = following
            raise RuntimeError('Native header child not found')

        def header_observation():
            if 'sm_title' not in symbols: return None
            length, pointer, kind = struct.unpack('<3I', camera.remote.memory(0xa2019e78 + 230 * 12, 12))
            if not 0 < length < 50 or kind: raise RuntimeError('Invalid native title record')
            return dict(title=camera.remote.memory(pointer, length).decode('ascii'),
                menu_state=camera.remote.memory(0xa182ed2c, 1).hex(),
                menu_dispatch=camera.remote.memory(0xa182ed34, 4).hex(),
                event_flag=camera.remote.memory(0xa181f910, 4).hex(),
                header_node=header_node(),
                diagnostics={key: word(key) for key in ('sm_save_status', 'persistence_state', 'z7_menu_status_events', 'z7_menu_status_paints', 'z7_menu_status_notifications') if key in symbols})

        def capture(label, expected_suffix=None):
            if expected_suffix is None:
                expected_suffix = ': Defaults' if name == 'first' and label == 'root-initial' else ': Saved'
            target = result.get('reference_backgrounds', {}).get(label) if name == 'restart' else None
            attempts = []
            for attempt in range(30):
                wait_native(700 if not attempt else (100, 70, 130, 210)[attempt % 4])
                widget_rows, pending = widgets()
                observation = dict(attempt=attempt, pending_widgets=pending)
                attempts.append(observation)
                phase.setdefault('capture_readiness', {})[label] = attempts
                save()
                if pending:
                    if attempt == 29:
                        camera.refresh()
                        (directory / (label + '-pending-failure.png')).write_bytes(camera.png)
                        observation['widget_rows'] = widget_rows
                        save()
                    continue
                camera.refresh()
                image = Image.open(io.BytesIO(camera.png)).convert('RGB')
                selected = pages()[-1]['row']
                color = list(image.getpixel((100, 64 + selected * 52)))
                observation.update(selected_row=selected, native_selection_rgb=color, sha256=hashlib.sha256(camera.png).hexdigest())
                # Preserve every ready native candidate; select a matching native
                # pulse phase, never a tolerance, mask or rewritten screenshot.
                (directory / (label + '-candidate' + str(attempt) + '.png')).write_bytes(camera.png)
                header = header_observation()
                observation['header'] = header
                save()
                # Worker publication and queued menu paint are asynchronous.
                # Preserve stale candidates and wait within the same bounded
                # paint window; never navigate or rewrite the title to settle it.
                if header and (not header['title'].endswith(expected_suffix) or header['header_node']['words'][17]): continue
                if target is not None and color != target: continue
                break
            else:
                raise RuntimeError('Native menu did not reach matching clean paint/pulse state: ' + label)
            (directory / (label + '.png')).write_bytes(camera.png)
            if name == 'first' and label.endswith('-comparison'):
                result.setdefault('reference_backgrounds', {})[label] = color
            title = header['title'] if header else None
            if header:
                phase.setdefault('header_observations', {})[label] = header
                check(name + '-' + label + '-native-header-status-current', title.endswith(expected_suffix))
            phase['steps'].append(dict(name=label, title=title, sha256=hashlib.sha256(camera.png).hexdigest(), pages=pages(), model=settings(), widget_rows=widget_rows,
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

        def open_owned_menu():
            key('left', lambda: on_page(1)); row(1, 3)
            key('right', lambda: on_page(0x125)); row(0x125, 4)
            key('right', lambda: on_page(0x127)); row(0x127, 28)
            key('right', lambda: on_page(0x153)); row(0x153, 6)
            key('right', lambda: on_page(0))

        try:
            camera.boot(announce_ready=False)
            checkpoint()
            state = struct.unpack('<64I', camera.remote.memory(STATE, 256))
            base = state[12]
            check(name + '-full-module-loaded-with-persistent-file-service', state[10] == 8 and base and fixture.module_finished and camera.remote.fixture_enabled and not fixture.finished)
            if a.startup_error:
                phase['process_id'] = camera.proc.pid
                phase['startup_model'] = settings()
                check('startup-open-error-keeps-resident-module-with-volatile-defaults',
                    word('z7_persistence_ready') == 0 and word('z7_persistence_result') == 2 and
                    settings() == [0, 15, 1, 0, 5, exposure_component, 127, 7, 0, 127] and fixture.files == files and not fixture.handles)
                fixture.fail_open = False
                open_owned_menu()
                capture('blocked-root', ': Restart to save')
                before_events = list(fixture.events)
                row(0, 0); key('right', lambda: settings()[0] == 1)
                for _ in range(8): wait_native(1000)
                check('startup-error-remains-latched-after-error-clears-and-native-menu-edit',
                    fixture.events == before_events and fixture.files == files and not fixture.handles and
                    not word('z7_persistence_ready') and not word('z7_persistence_attempts') and
                    word('z7_settings_revision') != word('z7_persistence_saved_revision'))
                capture('blocked-root-edited', ': Restart to save')
                row(0, 3); key('right', lambda: word('z7_settings_view') == 1 and word('z7_settings_preset') == 2)
                capture('blocked-composition', ': Restart to save')
                row(0, 1); key('right', lambda: word('z7_settings_view') == 2)
                capture('blocked-information', ': Restart to save')
                phase['final_model'] = settings()
                phase['filesystem_events'] = fixture.events
                phase['final_files'] = {str(k): hashlib.sha256(v).hexdigest() for k, v in fixture.files.items()}
                check('blocked-phase-preserves-both-original-journals-without-retained-handle', fixture.files == files and not fixture.handles)
                return dict(fixture.files)
            check(name + '-startup-settings-ready-without-retained-handle', word('z7_persistence_ready') == 1 and camera.remote.memory(base + symbols['z7_persistence_files'] + 4, 4) == b'\xff' * 4)
            phase['startup_model'] = settings()
            phase['process_id'] = camera.proc.pid
            if name == 'first':
                check('fresh-files-use-defaults-without-creating-journal', settings() == [0, 15, 1, 0, 5, exposure_component, 127, 7, 0, 127] and fixture.files == {})
            else:
                check('fresh-guest-restores-prior-menu-edits-before-navigation', settings() == result['expected_model'] and not word('z7_settings_revision') and not any(e.get('component') == 'settings' and e['operation'] in ('write', 'create') for e in fixture.events))
            open_owned_menu()
            capture('root-initial')
            if lcd_release: check(name + '-root-compact-count', int.from_bytes(camera.remote.memory(base + symbols['sm_meta'] + 20, 2), 'little') == 6)
            if lcd_release: check_row_limit(6, 'root'); row(0, 0)
            if name == 'first':
                row(0, 0); key('right', lambda: settings()[0] == 1); wait_saved()
                capture('master-saved')
                row(0, battery_row)
                if a.save_error:
                    original_files = dict(fixture.files)
                    fixture.fail_create = True
                key('right', lambda: settings()[0] == 3)
                if a.save_error:
                    for _ in range(40):
                        wait_native(500)
                        if word('z7_persistence_errors'): break
                    else: raise RuntimeError('Injected create error was not observed by worker')
                    check('save-failure-retains-dirty-revision-and-original-record',
                        fixture.files == original_files and not fixture.handles and
                        word('z7_settings_revision') != word('z7_persistence_saved_revision'))
                    capture('save-retry', ': Save retry')
                    fixture.fail_create = False
                wait_saved()
                check('two-completed-native-menu-saves-create-both-journal-slots', set(fixture.files) == {0, 1} and all(valid(data) for data in fixture.files.values()))
            row(0, 1); key('right', lambda: word('z7_settings_view') == 1)
            if lcd_release:
                check(name + '-preset-compact-count', int.from_bytes(camera.remote.memory(base + symbols['sm_meta'] + 20, 2), 'little') == 5)
                if name == 'first':
                    row(0, 3); key('right', lambda: settings()[2] == 5)
                    row(0, 4); key('right', lambda: settings()[2] == 1)
                    check('native-compact-reset-keeps-unsupported-components-off', all(not x & 10 for x in settings()[2:6]))
                    wait_saved()
                capture('compact-preset')
                check_row_limit(5, 'preset')
            row(0, 2)
            if name == 'first':
                key('right', lambda: settings()[2] == 0); wait_saved()
            capture('standard-grid-off')
            row(0, 1); key('right', lambda: word('z7_settings_view') == 2)
            row(0, 0)
            if name == 'first':
                key('right', lambda: settings()[6] == 126); wait_saved()
            capture('information-shutter-off')
            if lcd_release:
                row(0, 6); key('right', lambda: word('z7_settings_view') == 3)
                check(name + '-extra-compact-count', int.from_bytes(camera.remote.memory(base + symbols['sm_meta'] + 20, 2), 'little') == 3)
                if name == 'first':
                    row(0, 1); key('right', lambda: settings()[6] == 254); wait_saved()
                capture('compact-extra')
                check_row_limit(3, 'extra')
                row(0, 2); key('right', lambda: word('z7_settings_view') == 2)
                check(name + '-extra-back-restores-seven-information-rows', int.from_bytes(camera.remote.memory(base + symbols['sm_meta'] + 20, 2), 'little') == 7)
            key('left', lambda: word('z7_settings_view') == 1)
            key('left', lambda: word('z7_settings_view') == 0)
            row(0, 0); capture('root-saved')
            check(name + '-menu-model-and-battery-setting-consistent', settings() == [3, 15, 0, 0, 5, exposure_component, 254 if lcd_release else 126, 7, 0, 127] and word('z7_battery_enabled') == 1)
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
            restored = boot_phase('blocked' if a.startup_error else 'restart', files)
            if a.startup_error: check('blocked-inspection-never-rewrites-seeded-journal', restored == files)
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
