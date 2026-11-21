"""Execute compiled nonblocking lane ownership, including interrupted publish.

SPDX-License-Identifier: MIT. No native bridge uses this primitive yet. These
checks prove neither the original stale-frame fix nor physical lock ordering.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_R0
from audit_splash_image import NativePNG, STOCK_SHA, MEM, STACK, STOP
from audit_z7_highlight_submission import enter, returned
from build_z7_module import ROOT, HEADER, build
from build_z7_module_host import ZIG

CODE = MEM + 0x20000


def audit(stock, packet, metadata):
    if hashlib.sha256(stock).hexdigest() != STOCK_SHA:
        raise ValueError('Exact stock main required')
    f = NativePNG(stock)
    image = bytearray(packet[HEADER:HEADER + metadata['image_bytes']])
    for off in metadata['relocations']:
        struct.pack_into('<I', image, off, struct.unpack_from('<I', image, off)[0] + CODE)
    f.u.mem_write(CODE, bytes(image) + bytes(metadata['bss_bytes']))
    symbols = metadata['symbols']
    lane = CODE + symbols['z7_lane']
    def words(): return struct.unpack('<2I', f.u.mem_read(lane, 8))
    def call(name, *args): return f.call(CODE + symbols['z7_lane_' + name], *args)
    checks = []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    owner, other = 0xa251f000, 0xa2507000
    check('cold-lane-is-idle-and-unowned', words() == (0, 0))
    check('invalid-role-and-zero-owner-never-change-lane',
          all(call('enter', role, identity) == 0 for role, identity in
              ((0, owner), (3, owner), (0xffffffff, owner), (1, 0), (2, 0))) and words() == (0, 0))
    frame = call('enter', 1, owner)
    check('frame-admission-publishes-token-and-owner', frame == 1 and words() == (frame, owner) and call('owns', frame, owner) == 1)
    check('frame-rejects-both-roles-including-same-owner-reentry',
          all(call('enter', role, identity) == 0 for role in (1, 2) for identity in (owner, other)) and words() == (frame, owner))
    check('wrong-owner-or-role-cannot-release-live-frame',
          call('leave', frame, other) == call('leave', frame + 1, owner) == call('owns', frame, other) == 0 and words() == (frame, owner))
    check('frame-release-clears-owner-and-advances-generation', call('leave', frame, owner) == 1 and words() == (4, 0))
    parameter = call('enter', 2, other)
    check('parameter-admission-rejects-frames-and-parameters', parameter == 6 and call('owns', parameter, other) == 1 and
          call('enter', 1, owner) == call('enter', 2, other) == 0 and words() == (parameter, other))
    check('stale-frame-release-cannot-open-parameter-lane', call('leave', frame, owner) == 0 and words() == (parameter, other))
    check('parameter-release-advances-generation', call('leave', parameter, other) == 1 and words() == (8, 0))
    second = call('enter', 1, owner)
    check('same-owner-address-cannot-recycle-old-token', second == 9 and call('leave', frame, owner) == call('owns', frame, owner) == 0 and
          words() == (second, owner) and call('leave', second, owner) == 1)

    def interrupted(name, args, phase_name, at_owner=False):
        pending, paused = [False], [False]
        def observe(u, access, address, size, value, context):
            if ((at_owner and address == lane + 4) or
                    (not at_owner and address == lane and value & 3 == 3)):
                pending[0] = True
        def pause(u, address, size, context):
            if pending[0]:
                pending[0] = False; paused[0] = True; u.emu_stop()
        write_hook = f.u.hook_add(UC_HOOK_MEM_WRITE, observe, begin=lane, end=lane + 7)
        code_hook = f.u.hook_add(UC_HOOK_CODE, pause)
        f.u.ctl_remove_cache(CODE, CODE + len(image))
        guards = enter(f, CODE + symbols['z7_lane_' + name], args, STACK)
        saved = f.u.context_save(); mid = words()
        check(phase_name + '-pauses-in-transition', paused[0] and f.u.reg_read(UC_ARM_REG_PC) != STOP and mid[0] & 3 == 3)
        f.u.hook_del(write_hook); f.u.hook_del(code_hook)
        f.u.ctl_remove_cache(CODE, CODE + len(image))
        def concurrent(n, *a):
            guards2 = enter(f, CODE + symbols['z7_lane_' + n], a, STACK - 0x10000)
            check(phase_name + '-concurrent-' + n + '-preserves-stack', returned(f, STACK - 0x10000, guards2))
            return f.u.reg_read(UC_ARM_REG_R0)
        check(phase_name + '-rejects-new-frame', concurrent('enter', 1, other) == 0 and words() == mid)
        check(phase_name + '-rejects-new-parameters', concurrent('enter', 2, other) == 0 and words() == mid)
        check(phase_name + '-does-not-authorize-incomplete-owner', concurrent('owns', (mid[0] & ~3) | 1, owner) == 0 and words() == mid)
        check(phase_name + '-cannot-be-released-by-contender', concurrent('leave', (mid[0] & ~3) | 1, owner) == 0 and words() == mid)
        f.u.context_restore(saved)
        f.u.emu_start(f.u.reg_read(UC_ARM_REG_PC) | 1, STOP, timeout=10000000, count=10000000)
        check(phase_name + '-resumes-with-original-stack-and-callee-registers', returned(f, STACK, guards))
        return f.u.reg_read(UC_ARM_REG_R0)

    token = interrupted('enter', (1, owner), 'admission')
    check('interrupted-admission-finishes-with-authorized-owner', words() == (token, owner) and call('owns', token, owner) == 1)
    check('interrupted-release-finishes-idle', interrupted('leave', (token, owner), 'release') == 1 and words() == (16, 0))
    token = interrupted('enter', (1, owner), 'owner-published-before-admission', at_owner=True)
    check('owner-publication-resumes-with-authorized-owner', words() == (token, owner) and call('owns', token, owner) == 1)
    check('cleared-owner-does-not-reopen-lane-before-release-commit',
          interrupted('leave', (token, owner), 'owner-cleared-before-release', at_owner=True) == 1 and words() == (20, 0))
    f.u.mem_write(lane, struct.pack('<2I', 0xfffffff8, 0))
    last = call('enter', 2, other)
    check('last-generation-admits-and-releases-without-wrap', last == 0xfffffffa and call('leave', last, other) == 1 and words() == (0xfffffffc, 0))
    check('exhausted-lane-cannot-recycle-any-token', call('enter', 1, owner) == call('enter', 2, other) ==
          call('leave', last, other) == call('leave', frame, owner) == 0 and words() == (0xfffffffc, 0))
    return dict(passed=True, checks=checks, compiled_thumb_atomic_ownership_executed=True,
                separate_stacks_and_interruption_schedule_supplied=True,
                primitive_connected_to_native_bridges=False, stale_native_frame_fixed=False,
                physical_scheduler_lock_order_or_engine_lifetime_proven=False, camera_card_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); out = a.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists(): p.error('Choose a new private output directory')
    packet, metadata = build(ROOT / 'z7-native-modules/examples/highlight_lane_probe.c', zig=ZIG)
    result = audit(a.stock_main.read_bytes(), packet, metadata)
    result['probe_sha256'] = hashlib.sha256(packet).hexdigest()
    result['source_sha256'] = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
        'tools/audit_z7_highlight_lane.py', 'z7-native-modules/examples/highlight_lane_probe.c',
        'z7-native-modules/host/highlight_lane.h')}
    out.mkdir(parents=True)
    (out / 'probe.BIN').write_bytes(packet)
    (out / 'probe.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8', newline='\n')
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__': main()
