"""Loaded portrait touch through all original Z7 driver/application paths (MIT).

Runs original registration/fanout/state/program dispatch, resident API92 transform
and native queue copy together. Active OS/device/program/UI states and services
are supplied. No physical event acquisition or task/pending-screen exclusion.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1
from audit_z7_portrait_touch_host import PortraitTouchFixture
from audit_z7_native_touch_driver import SLOTS, READY, DRIVER_LOCK, OBJECT, ACTIVE, PROGRAMS, PATH, GETTERS, HANDLERS
from audit_z7_portrait_input import OFFSETS, point_reference
from audit_z7_touch_host import EVENT, NATIVE_STATE, RING, STRIDE
from audit_splash_image import STACK
from build_z7_module import build
from build_z7_module_host import ROOT, STATE, ZIG


class PortraitDriverFixture(PortraitTouchFixture):
    def __init__(self, raw, report, packet, metadata):
        self.driver_depth = 0
        self.driver_events = []
        self.driver_active = False
        super().__init__(raw, report, packet, metadata)

    def hook(self, u, address, size, context):
        if self.driver_active:
            arg = u.reg_read(UC_ARM_REG_R0)
            if address in (0x10170944, 0x1017093e):
                assert arg == DRIVER_LOCK
                self.driver_depth += 1 if address == 0x10170944 else -1
                assert self.driver_depth in (0, 1)
                self.driver_events.append(('lock' if address == 0x10170944 else 'unlock', arg))
                self.ret(0)
                return
            if address in PATH or address | 1 in HANDLERS:
                assert self.driver_depth == 1
                self.driver_events.append(('native', address, arg))
            if address in (0x1015b746, 0x1015b74a, 0x10406474, 0x104064cc, 0x103661bc):
                assert self.driver_depth == 1
                self.driver_events.append(('service', address, arg, u.reg_read(UC_ARM_REG_R1)))
                if address == 0x104064cc:
                    assert u.reg_read(UC_ARM_REG_R1) == 2
                self.ret(0x77 if address == 0x10406474 else 0)
                return
        super().hook(u, address, size, context)


def audit(raw, host, packet, metadata):
    f = PortraitDriverFixture(raw, host, packet, metadata)
    checks = []

    def check(name, good):
        assert good, name
        checks.append(name)

    loaded = f.call(host['symbols']['z7_module_load_once'], STATE)
    f.setword(40, loaded)
    check('module-loaded', loaded == 8)
    f.call(host['symbols']['z7_module_worker_tick'])
    check('native-object-and-state-identities', f.read(OBJECT + 0xd0) == 0x10058b23 and f.read(ACTIVE + 0xc) == 0x10090641)
    f.write(READY, 1)
    check('original-driver-callback-registers', f.call(0x1020d3d4, 0, f.read(OBJECT + 0xd0)) == 0)
    slots = bytes(f.u.mem_read(SLOTS, 12))
    f.write(OBJECT + 0x134, ACTIVE)
    f.write(PROGRAMS - 0x10, 1)
    cases = 0
    for program, orientation, variant, disposition in itertools.product(range(5), (1, 2), range(3), ('mapped', 'foreign', 'blocked', 'admission-failed')):
        f.nav_setup(orientation)
        f.u.mem_write(0xa18298b8, bytes([variant, 0]))
        if disposition == 'foreign':
            f.u.mem_write(0xa201d4d0, b'\1')
        obj = f.call(GETTERS[program])
        check(f'case{cases}-native-program-handler', f.read(obj + 0x50) == HANDLERS[program])
        f.write(PROGRAMS + 0x10 + 12 * program, obj)
        f.u.mem_write(PROGRAMS, bytes([program]))
        f.u.mem_write(NATIVE_STATE, bytes(0x34))
        f.write(NATIVE_STATE + 8, 1)
        if disposition == 'blocked':
            f.write(NATIVE_STATE + 0xc, 1)
        f.admission = int(disposition != 'admission-failed')
        f.u.mem_write(RING, bytes(16 * STRIDE))
        event = bytearray(range(60))
        event[8:10] = b'\x01\x01'
        for index, offset in enumerate(OFFSETS):
            struct.pack_into('<2h', event, offset, *((512, 341) if index % 2 == 0 else (0, 0)))
        f.u.mem_write(EVENT, bytes(event))
        f.driver_events.clear()
        f.original_events.clear()
        before = f.read(f.touch_var('handled'))
        f.driver_active = True
        result = f.call(0x1020c2d4, 0, EVENT)
        f.driver_active = False
        visited = [e[1] for e in f.driver_events if e[0] == 'native']
        expected_path = list(PATH[:-1]) + [HANDLERS[program] & ~1, PATH[-1]]
        check(f'case{cases}-complete-native-chain', visited[:len(expected_path)] == expected_path and
              all(address == 0x1008fdc0 for address in visited[len(expected_path):]))
        check(f'case{cases}-fanout-return-locks-and-running-flag', result == 0 and f.depth == f.driver_depth == f.read(STATE + 412) == 0)
        expected = bytearray(event)
        mapped = disposition != 'foreign'
        if mapped:
            for index, offset in enumerate(OFFSETS):
                pair = struct.unpack_from('<2h', event, offset)
                if not index or pair != (0, 0):
                    struct.pack_into('<2h', expected, offset, *point_reference(pair, (1, 3, 2)[variant], orientation))
        check(f'case{cases}-original-producer-once-selected-packet', len(f.original_events) == 1 and
              f.original_events[0][1] == bytes(expected) and (f.original_events[0][0] != EVENT) == mapped)
        check(f'case{cases}-module-admission-and-source-preserved', f.read(f.touch_var('handled')) - before == int(mapped) and bytes(f.u.mem_read(EVENT, 60)) == bytes(event))
        check(f'case{cases}-wake-follows-native-result', sum(e[:2] == ('service', 0x104064cc) for e in f.driver_events) == int(disposition != 'blocked'))
        f.u.mem_write(EVENT, bytes([0xee]) * 60)
        f.u.mem_write(STACK - 0x800, bytes([0xdd]) * 0x800)
        if disposition in ('mapped', 'foreign'):
            struct.pack_into('<I', expected, 0, 1)
            check(f'case{cases}-native-copy-survives-complete-driver-return', bytes(f.u.mem_read(RING, STRIDE)) == bytes(expected) + bytes(STRIDE - 60) and f.call(0x1033332e) == 1)
        elif disposition == 'blocked':
            check(f'case{cases}-native-rejection-keeps-ring-empty', bytes(f.u.mem_read(RING, 16 * STRIDE)) == bytes(16 * STRIDE))
        else:
            cancellation = bytearray(STRIDE)
            struct.pack_into('<I', cancellation, 0, 1)
            cancellation[9] = 9
            check(f'case{cases}-native-cancellation-retained', bytes(f.u.mem_read(RING, STRIDE)) == bytes(cancellation) and
                  bytes(f.u.mem_read(RING + 15 * STRIDE, STRIDE)) == bytes(cancellation) and f.call(0x1033332e) == 0)
        check(f'case{cases}-driver-slots-preserved', bytes(f.u.mem_read(SLOTS, 12)) == slots)
        cases += 1
    return dict(schema=1, passed=True, checks=len(checks), check_names=checks, native_driver_module_cases=cases,
                native_programs=5, portrait_pages=3, orientations=2,
                original_driver_dispatch_loaded_portrait_bridge_and_native_producer_execute_together=True,
                supplied_boundaries=['active device/program/UI/scene/output/orientation state', 'filesystem/kernel/allocator', 'render backends', 'driver and queue locks', 'wake/time/profile data', 'queue admission result', 'program3 maintenance'],
                limits=['Failed admission is supplied; no actual full-ring consumer scheduling', 'No real driver event acquisition, task initialization or task/pending-screen exclusion', 'No camera boot, physical touch, installation or recovery proof'],
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
    source = ROOT/'z7-native-modules/examples/portrait_touch_host_probe.c'
    packet, metadata = build(source, zig=ZIG)
    again, other = build(source, zig=ZIG)
    assert packet == again and metadata == other
    result = audit(raw, host, packet, metadata)
    # Enumerate the loaded-portrait dependencies, hashing their current sources.
    prior = json.loads((ROOT/'evidence/20261121-portrait-touch-host.json').read_text())
    source_map = {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in prior['source_sha256']}
    source_map['z7-native-modules/plugins/portrait_program.h'] = hashlib.sha256((ROOT/'z7-native-modules/plugins/portrait_program.h').read_bytes()).hexdigest()
    for name in ('tools/audit_z7_portrait_touch_driver.py', 'tools/audit_z7_native_touch_driver.py'):
        source_map[name] = hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    for name, digest in source_map.items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest, name
    result.update(host_sha256=host['main_payload_sha256'], probe_sha256=hashlib.sha256(packet).hexdigest(),
                  probe_bytes=len(packet), reproducible_probe=True, source_sha256=source_map)
    out.mkdir(parents=True)
    (out/'probe.BIN').write_bytes(packet)
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('check_names', 'source_sha256')}))


if __name__ == '__main__':
    main()
