"""Own an isolated QEMU guest and probe native sound-page entry with abort capture.

This is assisted diagnostic execution, not physical-camera validation. It never
connects to the browser demo, installs firmware, writes a card or supplies fake
device completions. Actual QMP screenshots and any saved fault context stay local.
"""
import argparse
import io
import json
from pathlib import Path
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'z7-qemu/tools'))
import interactive as ui
import probe
from cmos_config import active_ingress, active_manifest
from PIL import Image, ImageChops, ImageStat


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--preset', choices=('full', 'shutter-sound'), default='full')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--exercise', action='store_true', help='Exercise no-file submenu actions and back navigation')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    report_path = args.build / (args.preset + '.json')
    build_report = json.loads(report_path.read_text())
    functions = {key: int(value, 16) for key, value in
                 build_report['features']['shutter_sound']['functions'].items()}
    ui.FIRMWARE = (args.build / (args.preset + '.main.bin')).resolve()
    ui.FIRMWARE_REPORT = report_path.resolve()
    ui.STOCK_CONTAINER = ROOT / '.private/stock/Z_7_0380.bin'
    camera = ui.Camera(0, profile='shooting', capture_control_test=True,
                       raw_source=active_manifest('native0'), exmcu_no_lens=True,
                       tg_periodic_test=True, tg_paired_test=True,
                       raw_ingress_test=active_ingress(), isp_boundary_test=True,
                       orientation_fixture=0, keep_awake=True, photo_liveview=True)
    result = {'preset': args.preset, 'session': camera.stamp, 'steps': [], 'checks': [],
              'camera_access': False, 'diagnostic_native_calls': True}
    destination = args.output / 'result.json'

    def save():
        destination.write_text(json.dumps(result, indent=2) + '\n')

    def screenshot(name):
        camera.refresh()
        (args.output / (name + '.png')).write_bytes(camera.png)

    def check_title(name):
        # Exclude the native back icon at the right. A dynamic page title must
        # produce actual white text pixels in the otherwise black header.
        picture = Image.open(io.BytesIO(camera.png)).convert('RGB')
        white = sum(1 for r, g, b in picture.crop((105, 0, 890, 72)).getdata()
                    if min(r, g, b) > 180)
        passed = white > 200
        result['checks'].append({'name': name, 'passed': passed, 'white_header_pixels': white})
        save()
        if not passed:
            raise AssertionError(name + ': missing rendered title')

    def capture_abort(registers):
        data = camera.remote.memory(int(registers['r1'], 16), 72)
        words = struct.unpack_from('<17I', data)
        result['abort'] = {'kind': int(registers['r0'], 16),
                           'registers': [hex(value) for value in words[:16]],
                           'pc': hex(words[15]), 'lr': hex(words[14]),
                           'cpsr': hex(words[16])}

    def page_state():
        def words(address, count):
            return struct.unpack('<' + 'I' * count, camera.remote.memory(address, count * 4))
        # Mirror native current-page getter 0x104061EC and its list helper;
        # no injected call or change to menu state is needed for these reads.
        current_list, = words(0xA181F91C, 1)
        stride, capacity, count, data = words(current_list, 4)
        if not (0 < count <= capacity and 4 <= stride <= 1024):
            raise RuntimeError('Unexpected native page list: ' + str((stride, capacity, count, data)))
        page, = words(data + stride * (count - 1), 1)
        page_word, = words(page, 1)
        parent, = words(page + 4, 1)
        row_a, row_b = struct.unpack('<2H', camera.remote.memory(page + 22, 4))
        observation = {'page': hex(page), 'page_id': hex(page_word >> 16),
                       'kind': page_word & 0xFFFF, 'row': row_a + row_b, 'parent': hex(parent)}
        state, = words(0xA1833558, 1)
        if state:
            busy, enabled, length, selected, pending, status, magic = words(state + 32, 7)
            observation['sound'] = dict(address=hex(state), magic=hex(magic), busy=busy,
                enabled=enabled, length=length, selected=selected, pending=pending, result=status)
        return observation

    def check_page(name, expected, row=None, status=None):
        observed = page_state()
        passed = observed['kind'] == 2 and int(observed['page_id'], 16) == expected
        if row is not None:
            passed = passed and observed['row'] == row
        if expected in (0x1C5A, 0x1C5B, 0x1C5C):
            sound = observed.get('sound', {})
            offset = {0x1C5A: 64, 0x1C5B: 0x36E40, 0x1C5C: 0x36E6C}[expected]
            passed = (passed and sound.get('magic') == '0x5a33534e'
                      and observed['parent'] == '0xa1833574'
                      and int(observed['page'], 16) == int(sound.get('address', '0'), 16) + offset
                      and sound.get('busy') == sound.get('enabled') == sound.get('length') == 0)
            if status is not None:
                passed = passed and sound.get('result') == status
        result['checks'].append({'name': name, 'passed': passed, 'observed': observed})
        save()
        if not passed:
            raise AssertionError(name + ': ' + str(observed))

    def settle(seconds=1):
        # Let the real main task dispatch the queued event. Injecting a sleep
        # call into that task would defer its own menu event processing.
        assert camera.remote.command('Z1,100545ec,2') == 'OK'
        # Send exactly one continue. A fault can reach the reporter before a
        # QMP query observes running, so inspect the stop instead of requiring
        # a transient running acknowledgement.
        camera.remote.send('c')
        camera.running = True
        time.sleep(seconds)
        if camera.monitor.command('query-status')['running']:
            camera.pause()
        else:
            camera.receive_stop()
        registers = camera.remote.registers()
        if int(registers['r15'], 16) == 0x100545EC:
            capture_abort(registers)
            raise RuntimeError('Native abort reporter reached during menu event dispatch')
        # Keep the reporter breakpoint active through the return to task idle.
        packet = camera.run_to(0x100531BC)
        camera.remote.command('z1,100545ec,2')
        return packet

    def key(packet, name):
        probe.TRACE_CALL[:] = [0x100545EC]
        probe.TRACE_CALL.extend(functions[key] & ~1 for key in ('open', 'ensure', 'labels'))
        packet = camera.key(packet, name)
        packet = settle()
        result['steps'].append({'name': 'native-key-' + name, 'returned': True})
        save()
        print('Completed native key: ' + name, flush=True)
        return packet

    try:
        camera.boot_shooting()
        result['boot_state'] = camera.snapshot()
        screenshot('shooting')
        scene_region = (140, 260, 880, 570)
        reference_scene = Image.open(io.BytesIO(camera.png)).convert('RGB').crop(scene_region)
        save()
        camera.pause()
        packet = camera.run_to(0x100531BC)
        packet = key(packet, 'menu')
        screenshot('menu')
        packet = key(packet, 'left')
        packet = key(packet, 'left')
        for unused in range(4):
            packet = key(packet, 'down')
        packet = key(packet, 'right')
        packet = key(packet, 'up')
        check_page('Setup sound row selected', 0x19B, row=35)
        screenshot('setup')
        packet = key(packet, 'ok')
        check_page('Sound page opens', 0x1C5A, row=0, status=0)
        screenshot('sound')
        check_title('Sound title renders')
        if args.exercise:
            packet = key(packet, 'ok')
            check_page('Enabled choices open', 0x1C5C, row=0, status=0)
            screenshot('enabled-off')
            check_title('Enabled title renders')
            packet = key(packet, 'ok')
            check_page('OFF returns to sound page', 0x1C5A, row=0, status=0)
            packet = key(packet, 'ok')
            packet = key(packet, 'down')
            packet = key(packet, 'ok')
            check_page('ON without a file reports missing file', 0x1C5C, row=1, status=1)
            screenshot('enabled-missing-file')
            packet = key(packet, 'left')
            check_page('Enabled back returns to sound page', 0x1C5A)
            packet = key(packet, 'down')
            packet = key(packet, 'ok')
            check_page('File choices open', 0x1C5B, row=0, status=0)
            screenshot('files')
            check_title('File title renders')
            packet = key(packet, 'down')
            packet = key(packet, 'ok')
            check_page('Missing file remains in choices', 0x1C5B, row=1, status=1)
            screenshot('file-missing')
            packet = key(packet, 'left')
            packet = key(packet, 'down')
            packet = key(packet, 'ok')
            check_page('Preview without a file reports missing file', 0x1C5A, row=2, status=1)
            screenshot('preview-missing')
            packet = key(packet, 'down')
            packet = key(packet, 'ok')
            check_page('Reload without a file reports missing file', 0x1C5A, row=3, status=1)
            screenshot('reload-missing')
            packet = key(packet, 'left')
            check_page('Sound back returns to Setup', 0x19B, row=35)
            packet = key(packet, 'ok')
            check_page('Sound page reopens with retained selection', 0x1C5A, row=3, status=1)
            screenshot('sound-reopened')
            packet = key(packet, 'left')
            check_page('Reopened sound page returns to Setup', 0x19B, row=35)
            returned = False
            for unused in range(2):
                packet = key(packet, 'menu')
                # The menu event and first processed frame are asynchronous.
                # Allow the same bounded recovery time as the HTTP UI test,
                # before deciding another MENU press is actually needed.
                until = time.monotonic() + 12
                while time.monotonic() < until:
                    camera.refresh()
                    scene = Image.open(io.BytesIO(camera.png)).convert('RGB').crop(scene_region)
                    scene_rms = max(ImageStat.Stat(ImageChops.difference(scene, reference_scene)).rms)
                    if scene_rms < 3:
                        returned = True
                        break
                    packet = settle(.5)
                if returned:
                    break
            screenshot('shooting-returned')
            result['checks'].append({'name': 'Custom menu returns to processed live view',
                'passed': returned and camera.device_evidence['isp_batches'] > result['boot_state']['device_evidence']['isp_batches'],
                'scene_rms': scene_rms,
                'initial_isp_batches': result['boot_state']['device_evidence']['isp_batches'],
                'final_isp_batches': camera.device_evidence['isp_batches']})
            if not result['checks'][-1]['passed']:
                raise AssertionError('Custom menu did not return to progressing processed live view')
        result['completed'] = True
        result['final_state'] = camera.snapshot()
    except Exception as error:
        result.update(completed=False, error=repr(error),
                      incomplete_call=probe.ACTIVE_FIXTURE)
        try:
            if not camera.monitor.command('query-status')['running']:
                if camera.running:
                    camera.receive_stop()
                registers = camera.remote.registers()
                if int(registers['r15'], 16) == 0x100545EC:
                    capture_abort(registers)
        except Exception as capture_error:
            result['abort_capture_error'] = repr(capture_error)
        fixture = probe.ACTIVE_FIXTURE or {}
        for event in fixture.get('trace', []):
            if int(event['registers']['r15'], 16) == 0x100545EC:
                data = bytes.fromhex(event['memory'].get('r1', ''))
                if len(data) >= 68:
                    words = struct.unpack_from('<17I', data)
                    result['abort'] = {'kind': int(event['registers']['r0'], 16),
                                       'registers': [hex(value) for value in words[:16]],
                                       'pc': hex(words[15]), 'lr': hex(words[14]),
                                       'cpsr': hex(words[16])}
    finally:
        probe.TRACE_CALL.clear()
        save()
        camera.close_guest()
    print(json.dumps({'completed': result.get('completed'), 'error': result.get('error'),
                      'abort': result.get('abort'), 'result': str(destination)}, indent=2))
    return int(not result.get('completed'))


if __name__ == '__main__':
    raise SystemExit(main())
