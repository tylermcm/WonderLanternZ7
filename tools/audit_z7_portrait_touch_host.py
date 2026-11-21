"""Loaded portrait touch mapping through API92 into the original Z7 queue (MIT).

Executes graphics orientation latch, native page getters, touch transform and
original producer. Supplies native state, rendering and kernel services. No
full input/graphics task exclusion, pending-screen closure or physical proof.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import struct

from audit_z7_portrait_navigation_host import PortraitNavigationFixture
from audit_z7_portrait_input import OFFSETS, point_reference
from audit_z7_touch_host import touch_queue_boundary, EVENT, NATIVE_STATE, RING, STRIDE
from audit_splash_image import STACK
from build_z7_module import build
from build_z7_module_host import ROOT, STATE, ZIG


class PortraitTouchFixture(PortraitNavigationFixture):
    def __init__(self, raw, report, packet, metadata):
        super().__init__(raw, report, packet, metadata)
        self.u.mem_map(0xa2000000, 0x10000)
        self.u.mem_map(0xa1f90000, 0x10000)
        self.depth = 0
        self.admission = 1
        self.original_result = None
        self.original_events = []

    def touch_var(self, name):
        return self.words()[12] + self.metadata['symbols']['z7_portrait_touch_' + name]

    def hook(self, u, address, size, context):
        if touch_queue_boundary(self, u, address):
            return
        super().hook(u, address, size, context)

    def touch(self, point=(512, 341), kind=1, pressed=1):
        self.u.mem_write(NATIVE_STATE, bytes(0x34))
        self.write(NATIVE_STATE + 8, 1)
        self.u.mem_write(RING, bytes(16 * STRIDE))
        packet = bytearray(range(60))
        packet[8:10] = bytes([pressed, kind])
        for index, offset in enumerate(OFFSETS):
            struct.pack_into('<2h', packet, offset, *(point if index % 2 == 0 else (0, 0)))
        self.u.mem_write(EVENT, bytes(packet))
        self.original_events.clear()
        before = self.read(self.touch_var('handled'))
        result = self.call(0x103319d8, EVENT)
        return result, self.read(self.touch_var('handled')) - before, bytes(packet)


def audit(raw, host, packet, metadata):
    f = PortraitTouchFixture(raw, host, packet, metadata)
    checks = []

    def check(name, good):
        assert good, name
        checks.append(name)

    loaded = f.call(host['symbols']['z7_module_load_once'], STATE)
    f.setword(40, loaded)
    check('loaded-graphics-navigation-touch-registrations', loaded == 8 and
          [f.read(STATE + o) for o in (364, 388, 408)] == [1, 1, 1])
    f.call(host['symbols']['z7_module_worker_tick'])
    points = ((0, 0), (1024, 682), (512, 341), (100, 400), (1000, 100), (-4, -4))
    cases = 0
    for variant, orientation, kind, pressed, point in itertools.product(
            (0, 1, 2), (1, 2), range(1, 9), (0, 1), points):
        # Native variants0/1/2 are grid/settings/dial respectively.
        page = (1, 3, 2)[variant]
        f.nav_setup(orientation)
        f.u.mem_write(0xa18298b8, bytes([variant, 0]))
        result, handled, original = f.touch(point, kind, pressed)
        expected = bytearray(original)
        for index, offset in enumerate(OFFSETS):
            pair = struct.unpack_from('<2h', original, offset)
            if not index or pair != (0, 0):
                struct.pack_into('<2h', expected, offset, *point_reference(pair, page, orientation))
        check(f'case{cases}-maps-once-before-native-producer', result == handled == len(f.original_events) == 1 and
              f.original_events[0][0] != EVENT and f.original_events[0][1] == bytes(expected))
        check(f'case{cases}-preserves-caller-and-running-guard', bytes(f.u.mem_read(EVENT, 60)) == original and
              f.read(STATE + 412) == 0 and f.depth == 0)
        struct.pack_into('<I', expected, 0, 1)
        f.u.mem_write(EVENT, bytes([0xee]) * 60)
        f.u.mem_write(STACK - 0x600, bytes([0xdd]) * 0x600)
        check(f'case{cases}-native-copy-outlives-host-callback-stack', bytes(f.u.mem_read(RING, STRIDE)) == bytes(expected) + bytes(STRIDE - 60))
        cases += 1
    for label, location, data in (
        ('native-menu', 0xa182ed2c, b'\1'), ('native-play', 0xa183de04, b'\1'),
        ('foreign-app', 0xa1829af4, b'\0'), ('foreign-scene', 0xa201d4d0, b'\1'),
        ('nonlcd-output', 0xa1821394, struct.pack('<I', 2)),
        ('unknown-layout', None, 0), ('landscape-layout', None, 3),
    ):
        f.nav_setup()
        if location is None:
            f.write(f.variable('layout'), data)
        else:
            f.u.mem_write(location, data)
        result, handled, original = f.touch()
        check(label + '-original-packet-delegated', result == 1 and handled == 0 and f.original_events == [(EVENT, original)])
    f.nav_setup(prime=False)
    result, handled, original = f.touch()
    check('touch-before-graphics-latch-delegates', handled == 0 and f.original_events == [(EVENT, original)])
    for location, data in ((0xa201d4d0, b'\1'), (0xa18298b8, b'\2\0'),
                           (0xa1821394, struct.pack('<I', 2)),
                           (0xa1815c6c, struct.pack('<I', 3))):
        f.nav_setup()
        f.nav_mutation = (location, data)
        result, handled, original = f.touch()
        check(f'observed-context-change{location}-discards-copy', handled == 0 and f.original_events == [(EVENT, original)])
    for label, location, data in (
        ('initial-manager', 0xa1815c6c, struct.pack('<I', 0)),
        ('start-pending-manager', 0xa1815c6c, struct.pack('<I', 1)),
        ('stop-pending-manager', 0xa1815c6c, struct.pack('<I', 3)),
        ('unknown-manager', 0xa1815c6c, struct.pack('<I', 255)),
        ('invalid-current-program', 0xa1815c64, b'\5'),
        ('pending-next-program', 0xa1815c65, b'\1'),
        ('manager-not-ready', 0xa1815c54, bytes(4)),
        ('foreign-program-object', 0xa1815c74 + 36, struct.pack('<I', 0xa182ecb8)),
    ):
        f.nav_setup()
        f.u.mem_write(location, data)
        result, handled, original = f.touch()
        check(label + '-touch-retains-native-packet', handled == 0 and f.original_events == [(EVENT, original)])
        result, handled = f.navigate(0)
        check(label + '-navigation-delegates', handled == 0 and f.nav_stock == [0])
        check(label + '-graphics-delegates-and-resets-latch', f.dispatch(box=(0,280,720,146)) == 0 and f.read(f.variable('layout')) == 0)
    return dict(schema=1, passed=True, checks=len(checks), check_names=checks,
                portrait_touch_cases=cases, api_bytes=92,
                loader_graphics_latch_native_page_getters_mapping_producer_and_queue_execute=True,
                supplied_boundaries=['filesystem/kernel/allocator', 'scene/page/output/orientation state', 'render backends', 'wake/time', 'profile data', 'queue admission'],
                observed_program_transition_guard_cases=8,
                limits=['Observed program transitions only; no full task or pending-screen fencing', 'No real touch acquisition, native consumer concurrency, pixels or complete boot', 'No camera/card access, installation or recovery proof'],
                installation_candidate=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('host', 'report', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists():
        parser.error('Choose a new private output directory')
    raw, host = args.host.read_bytes(), json.loads(args.report.read_text())
    assert hashlib.sha256(raw).hexdigest() == host['main_payload_sha256'] and host['api_bytes'] == 92
    source = ROOT / 'z7-native-modules/examples/portrait_touch_host_probe.c'
    packet, metadata = build(source, zig=ZIG)
    again, other = build(source, zig=ZIG)
    assert packet == again and metadata == other
    result = audit(raw, host, packet, metadata)
    # The loaded diagnostic includes the complete portrait graphics stack.
    names = ['tools/' + n + '.py' for n in ('audit_z7_portrait_touch_host', 'audit_z7_portrait_navigation_host',
             'audit_z7_portrait_grid_host', 'audit_z7_portrait_input', 'audit_z7_touch_host', 'audit_z7_native_touch_queue',
             'audit_z7_module_host', 'audit_z7_information_native', 'audit_splash_image', 'build_z7_module',
             'build_z7_module_host', 'audit_z7_portrait_draw', 'audit_z7_portrait_grid_message',
             'audit_z7_portrait_page_message', 'audit_z7_portrait_text')]
    names += ['z7-native-modules/examples/' + n + '.c' for n in ('portrait_touch_host_probe', 'portrait_grid_host_probe')]
    names += [str(p.relative_to(ROOT)).replace('\\', '/') for p in (ROOT/'z7-native-modules/plugins').glob('*.h')]
    result.update(host_sha256=host['main_payload_sha256'], probe_sha256=hashlib.sha256(packet).hexdigest(),
                  probe_bytes=len(packet), image_bytes=metadata['image_bytes'], bss_bytes=metadata['bss_bytes'],
                  relocations=len(metadata['relocations']), reproducible_probe=True,
                  source_sha256={**host['source_files'], **{n: hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names}})
    out.mkdir(parents=True)
    (out/'probe.BIN').write_bytes(packet)
    (out/'probe.json').write_text(json.dumps(metadata, indent=2)+'\n', encoding='utf-8')
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('check_names', 'source_sha256')}))


if __name__ == '__main__':
    main()
