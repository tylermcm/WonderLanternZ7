"""Loaded resident API92 touch callback and original producer audit (MIT).

Loader, registration, detour/trampoline, producer and queue copies execute.
Filesystem/kernel/allocator, wake/time, profile data and queue admission are
supplied. No page/task/consumer lifetime, physical driver, boot or flash proof.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0
from audit_z7_module_host import HostFixture
from audit_z7_native_touch_queue import STATE as NATIVE_STATE, RING, STRIDE, LOCK
from audit_splash_image import MEM, STACK
from build_z7_module import build
from build_z7_module_host import ROOT, STATE, CURSOR, ZIG

EVENT = 0xa2005000


def touch_queue_boundary(f, u, address):
    arg = u.reg_read(UC_ARM_REG_R0)
    original = f.report.get('touch_bridge', {}).get('original')
    if original and address == (int(original, 16) & ~1):
        f.original_events.append((arg, bytes(u.mem_read(arg, 60)) if f.original_result is None else None))
        if f.original_result is not None:
            f.ret(f.original_result)
            return True
    if address in (0x101641fa, 0x101641dc):
        assert arg == LOCK
        f.depth += 1 if address == 0x101641fa else -1
        assert f.depth in (0, 1)
        f.ret(0)
        return True
    if address in (0x1040772e, 0x103e8ed6):
        f.ret(0)
        return True
    if address == 0x101f50cc:
        u.mem_write(arg, bytes(8))
        f.ret(0)
        return True
    if address == 0x101ea092:
        assert f.depth == 1
        f.ret(f.admission)
        return True
    return False


class TouchHostFixture(HostFixture):
    def __init__(self, raw, report, packet, metadata):
        super().__init__(raw, report, packet)
        self.metadata = metadata
        self.native_call_timeout_us = 0
        self.u.mem_map(0xa2000000, 0x30000)
        self.u.mem_map(0xa1f90000, 0x10000)
        self.depth = 0
        self.admission = 1
        self.original_events = []
        self.original_result = None
        self.loaded_base = 0

    def read(self, address):
        return int.from_bytes(self.u.mem_read(address, 4), 'little')

    def write(self, address, value):
        self.u.mem_write(address, struct.pack('<I', value & 0xffffffff))

    def var(self, name):
        return (self.loaded_base or self.words()[12]) + self.metadata['symbols']['z7_touch_probe_' + name]

    def load(self):
        result = self.call(self.report['symbols']['z7_module_load_once'], STATE)
        self.setword(40, result)
        if result == 8:
            self.loaded_base = self.words()[12]
        return result

    def hook(self, u, address, size, context):
        if touch_queue_boundary(self, u, address):
            return
        super().hook(u, address, size, context)

    def dispatch(self, mode=0, index=0, kind=1, pressed=1, blocked=False):
        self.write(self.var('mode'), mode)
        self.u.mem_write(NATIVE_STATE, bytes(0x34))
        self.u.mem_write(NATIVE_STATE, bytes([index, index]))
        self.write(NATIVE_STATE + 8, 1)
        if blocked:
            self.write(NATIVE_STATE + 0xc, 1)
        self.u.mem_write(RING, bytes([0xcc]) * (16 * STRIDE))
        event = bytearray(range(60))
        event[8:10] = bytes([pressed, kind])
        self.u.mem_write(EVENT, bytes(event))
        before = self.read(self.var('calls'))
        self.original_events.clear()
        result = self.call(0x103319d8, EVENT)
        return result, self.read(self.var('calls')) - before, bytes(event)


def audit(raw, host, packet, metadata, failed, failed_meta, old_raw, old_host):
    checks = []

    def check(name, good):
        assert good, name
        checks.append(name)

    f = TouchHostFixture(raw, host, packet, metadata)
    check('loader-registers-touch-and-retains-one-module', f.load() == 8 and len(f.live) == 1)
    check('api92-registered-once', [f.read(f.var(n)) for n in ('api_size', 'registered', 'duplicate')] == [92, 1, 0])
    native_slots = bytes(f.u.mem_read(0xa1f910ac, 12))
    for mode, index, kind, pressed in itertools.product((0, 1, 2), range(16), range(1, 9), (0, 1)):
        result, calls, event = f.dispatch(mode, index, kind, pressed)
        expected = bytearray(event)
        if mode == 1:
            struct.pack_into('<I', expected, 20, struct.unpack_from('<I', expected, 20)[0] ^ 0x12340000)
        label = f'mode{mode}-index{index}-kind{kind}-press{pressed}'
        check(label + '-original-once-callback-once-result', result == calls == len(f.original_events) == 1)
        check(label + '-original-input-selected', f.original_events[0][1] == bytes(expected) and
              ((f.original_events[0][0] == EVENT) == (mode != 1)))
        struct.pack_into('<I', expected, 0, 1)
        entry = RING + STRIDE * index
        check(label + '-native-ring-copy', bytes(f.u.mem_read(entry, STRIDE)) == bytes(expected) + bytes(STRIDE - 60))
        check(label + '-caller-and-running-guard-preserved', bytes(f.u.mem_read(EVENT, 60)) == event and
              f.read(STATE + 412) == 0 and f.depth == 0)
        f.u.mem_write(EVENT, bytes([0xee]) * 60)
        f.u.mem_write(STACK - 0x400, bytes([0xdd]) * 0x400)
        check(label + '-host-copy-stack-lifetime', bytes(f.u.mem_read(entry, STRIDE)) == bytes(expected) + bytes(STRIDE - 60))
    for mode in (0, 1, 2):
        result, calls, event = f.dispatch(mode, blocked=True)
        check(f'blocked-mode{mode}-native-zero-result-preserved', result == 0 and calls == len(f.original_events) == 1 and f.read(STATE + 412) == 0)
        f.admission = 0
        result, calls, event = f.dispatch(mode)
        cancellation = bytearray(STRIDE)
        struct.pack_into('<I', cancellation, 0, 1)
        cancellation[9] = 9
        check(f'failed-admission-mode{mode}-native-one-result-and-cancellations', result == calls == len(f.original_events) == 1 and
              bytes(f.u.mem_read(RING, STRIDE)) == bytes(cancellation) and
              bytes(f.u.mem_read(RING + 15 * STRIDE, STRIDE)) == bytes(cancellation) and f.call(0x1033332e) == 0)
        f.admission = 1
    result, calls, event = f.dispatch(3)
    check('recursive-entry-delegates-without-second-callback', result == 1 and calls == 1 and len(f.original_events) == 2 and f.read(STATE + 412) == 0)
    result, calls, event = f.dispatch(4)
    check('late-registration-rejected', result == calls == 1 and f.read(f.var('late')) == 0)
    for offset, value in ((32, 0), (40, 7), (48, 0), (52, 0), (76, 1), (92, 0), (404, 0),
                          (404, f.words()[12] + metadata['image_bytes'] + 1), (408, 0), (412, 1), (416, 0), (420, 0)):
        saved = f.read(STATE + offset)
        f.setword(offset, value)
        result, calls, event = f.dispatch(1)
        check(f'invalid-state-field{offset}-delegates-original-once', result == 1 and calls == 0 and f.original_events == [(EVENT, event)])
        f.setword(offset, saved)
    for kind, pressed in ((0, 1), (9, 1), (10, 1), (255, 1), (10, 0)):
        result, calls, event = f.dispatch(1, kind=kind, pressed=pressed)
        check(f'unsupported-kind{kind}-press{pressed}-native-only', calls == 0 and len(f.original_events) == 1 and f.original_events[0] == (EVENT, event))
        if kind == 10 and not pressed:
            changed = bytearray(event)
            changed[9] = 9
            check('native-kind10-release-side-effect-preserved', bytes(f.u.mem_read(EVENT, 60)) == bytes(changed))
    f.original_result = 0x97531246
    f.write(f.var('mode'), 1)
    for pointer in (0, MEM + 0x10000, EVENT + 1, 0xbfffffc8, 0xfffffffc):
        before = f.read(f.var('calls'))
        f.original_events.clear()
        check(f'invalid-span{pointer}-only-original-boundary', f.call(0x103319d8, pointer) == f.original_result and
              f.read(f.var('calls')) == before and f.original_events == [(pointer, None)])
    check('native-driver-slots-untouched', bytes(f.u.mem_read(0xa1f910ac, 12)) == native_slots)
    f = TouchHostFixture(raw, host, failed, failed_meta)
    check('failed-init-clears-touch-before-free', f.load() == 7 and not f.live and not any(f.read(STATE + o) for o in (48, 52, 92, 404, 408, 412)))
    f.original_result = 0x789abcde
    check('failed-init-still-delegates-original', f.call(0x103319d8, EVENT) == f.original_result)
    f = TouchHostFixture(old_raw, old_host, packet, metadata)
    check('api88-rejects-touch-module-before-publication', f.load() == 7 and not f.live and f.read(STATE + 48) == 0)
    f = TouchHostFixture(raw, host, packet, metadata)
    f.u.mem_write(STATE, bytes([0x6b]) * 424)
    check('cold-original-result-preserved', f.call(0x101e3d94) == STATE)
    check('cold424-state448-reservation-and-touch-guards', f.read(CURSOR) == STATE + 448 and
          [f.read(STATE + o) for o in (404, 408, 412)] == [0, 0, 0] and
          [f.read(STATE + o) for o in (416, 420)] == [0xa5a5a5a5] * 2)
    check('cold-continuation-registers-and-flags-preserved', f.heap_observation == dict(r0=STATE, r1=CURSOR, r2=0x22334455, r3=0x66778899, flags=0xf8000000))
    return dict(schema=1, passed=True, checks=len(checks), check_names=checks,
                api_bytes=92, state_bytes=424, reserved_bytes=448, admitted_cases=768,
                loader_detour_trampoline_producer_native_queue_and_cold_execute=True,
                supplied_boundaries=['filesystem/kernel/allocator', 'wake/time', 'profile data', 'queue admission', 'original producer return only for invalid-span fixtures'],
                limits=['Diagnostic transform, no portrait page/output/task admission', 'No driver task initialization, consumer concurrency or complete boot', 'No camera/card access, installation or recovery proof'],
                installation_candidate=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('host', 'report', 'old-host', 'old-report', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists():
        parser.error('Choose a new private output directory')
    raw, old_raw = args.host.read_bytes(), args.old_host.read_bytes()
    host, old = json.loads(args.report.read_text()), json.loads(args.old_report.read_text())
    assert hashlib.sha256(raw).hexdigest() == host['main_payload_sha256'] and host['api_bytes'] == 92
    assert hashlib.sha256(old_raw).hexdigest() == old['main_payload_sha256'] and old['api_bytes'] == 88
    source = ROOT / 'z7-native-modules/examples/touch_host_probe.c'
    packet, metadata = build(source, zig=ZIG)
    again, other = build(source, zig=ZIG)
    assert packet == again and metadata == other
    failed, failed_meta = build(ROOT / 'z7-native-modules/examples/touch_host_fail_probe.c', zig=ZIG)
    result = audit(raw, host, packet, metadata, failed, failed_meta, old_raw, old)
    names = ('tools/audit_z7_touch_host.py', 'tools/audit_z7_module_host.py', 'tools/audit_z7_native_touch_queue.py',
             'tools/audit_splash_image.py', 'tools/build_z7_module.py', 'tools/build_z7_module_host.py',
             'z7-native-modules/examples/touch_host_probe.c', 'z7-native-modules/examples/touch_host_fail_probe.c')
    result.update(host_sha256=host['main_payload_sha256'], probe_sha256=hashlib.sha256(packet).hexdigest(),
                  probe_bytes=len(packet), image_bytes=metadata['image_bytes'], bss_bytes=metadata['bss_bytes'],
                  relocations=len(metadata['relocations']), reproducible_probe=True,
                  source_sha256={**host['source_files'], **{n: hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names}})
    out.mkdir(parents=True)
    (out / 'probe.BIN').write_bytes(packet)
    (out / 'failed-probe.BIN').write_bytes(failed)
    (out / 'probe.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('check_names', 'source_sha256')}))


if __name__ == '__main__':
    main()
