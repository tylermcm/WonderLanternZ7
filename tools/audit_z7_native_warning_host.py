"""Execute API72 registration, guard, terminal slot and activation lifetimes.

SPDX-License-Identifier: MIT. Native host helpers execute with supplied memory
and kernel/filesystem services. No physical concurrency or installation proof.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from audit_z7_parameters import ParameterHostFixture, NATIVE, PACKET
from audit_splash_image import STOCK_SHA
from build_z7_module import ROOT, build
from build_z7_module_host import STATE, CURSOR, ZIG


class NativeHostFixture(ParameterHostFixture):
    def __init__(self, *args):
        super().__init__(*args)
        self.u.mem_write(0xa1d68e54, b'\x03')
        self.u.mem_write(0xa180a568, b'\x00')


def audit(raw, host, probe, metadata, failed, failed_metadata):
    checks = []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    f = NativeHostFixture(raw, host, probe, metadata)
    f.write(STATE - 4, 0xc3c3c3c3); f.write(STATE + 336, 0xc3c3c3c3)
    check('cold336-reservation384-preserves-neighbors-and-native-allocator',
          f.call(0x101e3d94) == STATE and f.read(CURSOR) == STATE + 384 and
          f.read(STATE - 4) == f.read(STATE + 336) == 0xc3c3c3c3 and
          all(f.read(STATE + o) == 0xa5a5a5a5 for o in (316, 320, 328, 332)) and
          f.call(0x101e3dac, 1) == STATE + 384)
    f = NativeHostFixture(raw, host, probe, metadata)
    check('activation-requires-prerequisites-owned-enable-and-is-init-only', f.load() == 8 and
          f.read(f.address('z7_nf_mask')) == 31 and f.call(f.address('z7_nf_late')) == 0 and
          f.call(f.address('z7_nf_available')) == 1 and f.read(STATE + 304) == f.read(STATE + 324) == 1)
    gate_enter, gate_leave = (host['symbols']['z7_native_gate_' + n] for n in ('enter', 'leave'))
    parameter_enter, parameter_leave = (host['symbols']['z7_native_parameter_' + n] for n in ('enter', 'leave'))
    completing = host['symbols']['z7_native_parameter_completing']
    slot, other_slot, owner = NATIVE + 0x4400, NATIVE + 0x4420, 0xa251e000
    f.u.mem_write(PACKET, struct.pack('<7I', 0, 0, 0, 0, 0x42060007, NATIVE + 0x2100, 0))
    for off in (328, 332):
        f.write(STATE + off, 0)
        check(f'new-guard{off}-refuses-host-admission-and-owned-availability',
              f.call(gate_enter, owner, 0x1023babd) == f.call(f.address('z7_nf_available')) == 0)
        f.write(STATE + off, 0xa5a5a5a5)
    token = f.call(parameter_enter, PACKET, slot)
    check('foreign-parameter-owns-bridge-local-slot', token & 3 == 2 and f.read(STATE + 312) == slot and
          f.read(slot) == token and f.read(slot + 4) == PACKET)
    check('module-gate-borrows-parameter-span-while-native-frame-is-rejected',
          f.call(gate_enter, owner, f.address('z7_main') | 1) == 0 and
          f.call(gate_enter, owner, 0x1023babd) == 0xffffffff and f.read(STATE + 308) == token)
    f.call(completing, PACKET, other_slot)
    check('unrelated-completion-slot-cannot-release-foreign-owner', f.read(STATE + 308) == token and f.read(slot) == token)
    f.call(completing, PACKET, slot)
    check('completion-retires-slot-before-publishing-free-lane', f.read(slot) == 0 and f.read(STATE + 308) & 3 == 0 and f.read(STATE + 312) == 0)
    gate_token = f.call(gate_enter, owner, 0x1023babd)
    f.call(parameter_leave, slot)
    check('retired-foreign-slot-cannot-release-later-gate', gate_token & 3 == 1 and f.read(STATE + 308) == gate_token)
    f.call(gate_leave, owner, gate_token)
    for phase in (0, 5):
        f.u.mem_write(0xa1d68e54, bytes([phase]))
        before = f.read(STATE + 308)
        check(f'outside-identified-service{phase}-keeps-native-dispatch-without-lane',
              f.call(parameter_enter, PACKET, slot) == 0 and f.read(slot) == 0 and f.read(STATE + 308) == before)
    f.u.mem_write(0xa1d68e54, b'\x03'); f.u.mem_write(0xa180a568, b'\x01')
    check('wrong-selector-keeps-native-dispatch-without-foreign-lane',
          f.call(parameter_enter, PACKET, slot) == 0 and f.read(slot) == 0)
    f.u.mem_write(0xa180a568, b'\x00')
    f.write(STATE + 308, 0xfffffff0)
    check('near-exhaustion-query-disables-owned-eligibility', f.call(f.address('z7_nf_available')) == 0)
    f.write(STATE + 308, 0xfffffffc)
    for i in range(2):
        token = f.call(parameter_enter, PACKET, slot)
        check(f'terminal-parameter-{i}-uses-slot-without-counter-wrap', token == 0xfffffffe and f.read(slot) == token)
        f.call(completing, PACKET, slot)
        gate_token = f.call(gate_enter, owner, 0x1023babd)
        f.call(parameter_leave, slot)
        check(f'terminal-retired-slot-{i}-cannot-release-new-gate', gate_token == 0xfffffffd and f.read(STATE + 308) == gate_token)
        f.call(gate_leave, owner, gate_token)
        check(f'terminal-gate-{i}-returns-to-closed-generation-idle', f.read(STATE + 308) == 0xfffffffc and f.read(STATE + 312) == 0)
    f = NativeHostFixture(raw, host, failed, failed_metadata)
    check('failed-init-clears-both-activation-flags-and-resident-callbacks', f.load() == 7 and
          f.read(STATE + 304) == f.read(STATE + 324) == f.read(STATE + 48) == f.read(STATE + 52) == 0 and
          all(f.read(STATE + off) == 0 for off in (212, 216, 220, 224, 228, 256, 272, 288)))
    f = NativeHostFixture(raw, host, probe, metadata)
    token = f.call(gate_enter, owner, 0x1023babd)
    check('preactivation-gate-token-blocks-init-without-being-reset', token & 3 == 1 and f.load() == 7 and f.read(STATE + 308) == token)
    f.call(gate_leave, owner, token); f.position = 0
    check('activation-retries-after-prior-gate-retires', f.load() == 8 and f.read(STATE + 324) == 1 and f.read(STATE + 308) & 3 == 0)
    return dict(passed=True, checks=checks, compiled_host_helpers_execute=True, camera_card_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True); p.add_argument('--stock-main', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); out = a.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists(): p.error('Choose a new private output directory')
    if hashlib.sha256(a.stock_main.read_bytes()).hexdigest() != STOCK_SHA: p.error('Exact stock main required')
    host = json.loads((a.build / 'module-host.emulator.json').read_text(encoding='utf-8'))
    raw = (a.build / 'module-host.emulator.main.bin').read_bytes()
    if not host.get('native_warning_transaction_hooks') or hashlib.sha256(raw).hexdigest() != host['main_payload_sha256']:
        p.error('Exact API72 host required')
    source = ROOT / 'z7-native-modules/examples/native_warning_host_probe.c'
    packet, metadata = build(source, zig=ZIG); out.mkdir(parents=True)
    failed_source = out / 'failed.c'
    failed_source.write_text('#define Z7_NATIVE_WARNING_INIT_FAIL 1\n#include "' + source.as_posix() + '"\n', encoding='utf-8', newline='\n')
    failed, failed_metadata = build(failed_source, zig=ZIG)
    result = audit(raw, host, packet, metadata, failed, failed_metadata)
    result.update(host_sha256=host['main_payload_sha256'], probe_sha256=hashlib.sha256(packet).hexdigest())
    names = {*host['source_files'], 'tools/audit_z7_native_warning_host.py', 'tools/audit_z7_module_host.py', 'z7-native-modules/examples/native_warning_host_probe.c'}
    result['source_sha256'] = {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in sorted(names)}
    (out / 'probe.BIN').write_bytes(packet); (out / 'failed.BIN').write_bytes(failed)
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__': main()
