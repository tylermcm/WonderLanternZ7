# SPDX-License-Identifier: LicenseRef-Wonder-Lantern-Community
"""Independent Z7-only splash experiment; excluded from installation presets.

Reserve state at native monotonic-workspace initialization, arm after resource
setup and consume atomically at the observed first full-screen clear boundary.
All addresses/instruction guards are from the pinned original Z7 C 3.80.
"""
import hashlib
import struct

from ..assembly import assemble, constant, invoke, jump
from ..plan import Plan
from ..platform import z7_380 as platform

STATE, STATE_BYTES = 0xA9700000, 64
CURSOR = 0xA18FD738
MAGIC = 0x53504C31
GUARD = 0xA5A5A5A5
HEAP_SITE, ARM_SITE, RENDER_SITE = 0x101E3DA0, 0x10269842, 0x1042F152
FIRST_RENDER_CALLER = 0x104FFB19
FIELDS = dict(magic=0, phase=4, shown=8, delay_result=12, armed=16,
              initialized=20, recursive_skips=24, render_entries=28,
              caller_lr=32, original_argument=36, completed=40, guards=48)
EXPECTED = {
    HEAP_SITE: bytes.fromhex('504933480860bde8104005e7'),
    ARM_SITE: bytes.fromhex('90f191fc90f1e0f93561'),
    RENDER_SITE: bytes.fromhex('30b591b0044600250f95'),
}


def tail(address):
    return f'.balign 4; ldr.w pc,[pc,#0]; .word {address | 1};'


def build(source, splash_png, black_png, hold_ms=2000):
    if hold_ms != 2000:
        raise ValueError('Only the reviewed native delay argument 2000 is supported')
    # StockImage pins the complete EG, CRC and SCATTER mapping before edits.
    plan = Plan(source, platform)
    im = plan.image
    # Verify original branch destinations as well as the surrounding window.
    # Require whole, pinned instruction windows before replacing any bytes.
    heap_expected = EXPECTED[HEAP_SITE]
    arm_expected = EXPECTED[ARM_SITE]
    if (im.read(HEAP_SITE - 12, 2) != bytes.fromhex('3248')
            or im.words(0x101E3EE4, 2) != (CURSOR, 0xAC400000)
            or im.words(0x101E3E70, 1)[0] != STATE
            or any(im.read(site, len(expected)) != expected for site, expected in EXPECTED.items())):
        raise ValueError('Unexpected native Z7 workspace or rendering layout')
    for png in (splash_png, black_png):
        if (not isinstance(png, bytes) or len(png) > 65536
                or png[:8] != b'\x89PNG\r\n\x1a\n'
                or png[16:24] != struct.pack('>II', 720, 480)
                or png[24:29] != bytes([8, 2, 0, 0, 0])):
            raise ValueError('Requires bounded 720x480 RGB8 non-interlaced PNG assets')
    sizes = dict(cold=256, arm=256, render=768, draw=256)
    functions = {name: plan.alloc(bytes(size)) for name, size in sizes.items()}
    splash_address = plan.alloc(splash_png)
    black_address = plan.alloc(black_png)
    c, call = constant, invoke
    code = {}
    # Original initializer creates its mutex immediately before this site.
    # Its first monotonic allocation starts after our explicitly reserved block.
    code['cold'] = f"""
        push {{r2,r3}};
        {c('r2', STATE)} movs r3,#0;
        str r3,[r2,#0]; str r3,[r2,#4]; str r3,[r2,#8]; str r3,[r2,#12];
        str r3,[r2,#16]; str r3,[r2,#24]; str r3,[r2,#28]; str r3,[r2,#32];
        str r3,[r2,#36]; str r3,[r2,#40]; str r3,[r2,#44];
        movs r3,#1; str r3,[r2,#20];
        {c('r3', GUARD)} str r3,[r2,#48]; str r3,[r2,#52]; str r3,[r2,#56]; str r3,[r2,#60];
        dmb sy; {c('r3', MAGIC)} str r3,[r2];
        pop {{r2,r3}};
        {c('r1', CURSOR)} {c('r0', STATE + STATE_BYTES)} str r0,[r1];
        {c('r0', STATE)} pop.w {{r4,lr}}; {tail(0x101E3BB8)}
    """
    code['arm'] = f"""
        push {{r4,lr}};
        {call(0x103FA168)} {call(0x103F9C0A)}
        push {{r0-r3}};
        {c('r0', STATE)} ldr r1,[r0]; {c('r2', MAGIC)} cmp r1,r2; bne arm_done;
        add r0,r0,#4;
        arm_retry: ldrex r1,[r0]; cmp r1,#0; bne arm_clear;
        movs r1,#1; strex r2,r1,[r0]; cmp r2,#0; bne arm_retry;
        dmb sy; str r1,[r0,#12]; b arm_done;
        arm_clear: clrex;
        arm_done: pop {{r0-r3}}; pop {{r4,lr}};
        str r5,[r6,#0x10]; {tail(0x1026984C)}
    """
    # Small stack descriptor only; encoded PNGs are immutable appended ROM data.
    code['draw'] = f"""
        push {{r4-r7,lr}}; sub sp,#68;
        mov r4,r0; mov r5,r1; mov r6,sp; movs r7,#16; movs r0,#0;
        zero: str r0,[r6],#4; subs r7,r7,#1; bne zero;
        str r4,[sp]; str r5,[sp,#4];
        movs r0,#0; movs r1,#0; mov r2,sp; add r3,sp,#48;
        {call(0x10431738)} add sp,#68; pop {{r4-r7,pc}};
    """
    code['render'] = f"""
        push.w {{r0-r12,lr}}; mrs r0,apsr; push {{r0,r1}};
        {c('r4', STATE)} ldr r0,[r4]; {c('r1', MAGIC)} cmp r0,r1; bne resume;
        ldr r0,[r4,#28]; adds r0,r0,#1; str r0,[r4,#28];
        ldr r0,[r4,#4]; cmp r0,#2; bne check_arm;
        ldr r0,[r4,#24]; adds r0,r0,#1; str r0,[r4,#24]; b resume;
        check_arm: cmp r0,#1; bne resume;
        ldr r0,[sp,#60]; {c('r1', FIRST_RENDER_CALLER)} cmp r0,r1; bne resume;
        ldr r2,[sp,#8]; ldr r0,[r2]; cmp r0,#0; bne resume;
        ldr r0,[r2,#4]; cmp r0,#0; bne resume;
        ldr r0,[r2,#8]; cmp r0,#720; bne resume;
        ldr r0,[r2,#12]; cmp r0,#480; bne resume;
        ldr r0,[r2,#16]; cmp r0,#255; bne resume;
        add r5,r4,#4;
        consume: ldrex r0,[r5]; cmp r0,#1; bne cancel;
        movs r0,#2; strex r1,r0,[r5]; cmp r1,#0; bne consume;
        dmb sy; movs r0,#1; str r0,[r4,#8];
        ldr r0,[sp,#60]; str r0,[r4,#32]; ldr r0,[sp,#8]; str r0,[r4,#36];
        {c('r0', splash_address)} {c('r1', len(splash_png))} {call(functions['draw'])}
        {c('r0', hold_ms)} {call(0x1017081E)} str r0,[r4,#12];
        {c('r0', black_address)} {c('r1', len(black_png))} {call(functions['draw'])}
        ldr r0,[r4,#12]; cmp r0,#0; bne failed;
        movs r0,#1; str r0,[r4,#40]; movs r0,#3; b finish;
        failed: movs r0,#4;
        finish: dmb sy; str r0,[r4,#4]; b resume;
        cancel: clrex;
        resume: pop {{r0,r1}}; msr APSR_nzcvq,r0; pop.w {{r0-r12,lr}};
        push {{r4,r5,lr}}; sub sp,#0x44; mov r4,r0; movs r5,#0; str r5,[sp,#0x3c];
        {tail(RENDER_SITE + 10)}
    """
    actual_sizes = {}
    for name, text in code.items():
        blob = assemble(text, functions[name], sizes[name])
        plan.put(functions[name], blob)
        actual_sizes[name] = len(blob)
    plan.edit(HEAP_SITE, jump(HEAP_SITE, functions['cold'], 12),
              'Reserve independent splash state at native workspace initialization', expected=heap_expected)
    plan.edit(ARM_SITE, jump(ARM_SITE, functions['arm'], 10),
              'Arm after original guarded Z7 resource setup', expected=arm_expected)
    plan.edit(RENDER_SITE, jump(RENDER_SITE, functions['render'], 10),
              'Consume splash one-shot before the first native full-screen clear', expected=EXPECTED[RENDER_SITE])
    plan.features['splash_experiment'] = dict(
        independent=True, emulator_only=True, state=hex(STATE), state_bytes=STATE_BYTES,
        state_fields=FIELDS, state_magic=hex(MAGIC), state_guard=hex(GUARD),
        workspace_cursor=hex(CURSOR), reserved_cursor_start=hex(STATE + STATE_BYTES),
        functions={k: hex(v) for k, v in functions.items()}, code_sizes=actual_sizes,
        splash_png=hex(splash_address), splash_png_bytes=len(splash_png),
        splash_png_sha256=hashlib.sha256(splash_png).hexdigest(),
        black_png=hex(black_address), black_png_bytes=len(black_png),
        hold_native_delay_argument=hold_ms, accepted_caller=hex(FIRST_RENDER_CALLER),
        accepted_clear=[0, 0, 720, 480, 255],
        initialization_site=hex(HEAP_SITE), arm_site=hex(ARM_SITE), render_site=hex(RENDER_SITE))
    output, report = plan.finish()
    report.update(preset='splash-emulator-only', emulator_only=True, candidate_cleared=False,
                  firmware_lifecycle=True, camera_verified=False)
    report['limitations'] += [
        'Experimental native workspace reservation and hooks have not been physically tested.',
        'Native delay unit/timing, LCD/EVF and physical wake semantics are not cleared.',
        'Stock PNG allocation/assertion failure behavior is retained; low-memory robustness is unverified.',
        'No installation/recovery clearance; do not stage this emulator experiment on a camera card.',
    ]
    return output, report
