# SPDX-License-Identifier: LicenseRef-Wonder-Lantern-Community
"""Independent Z7 UI-surface drawing diagnostic; no lifecycle hook installed."""
import hashlib
import struct

from ..assembly import assemble, constant, invoke


def configure(plan, png):
    if (png[:8] != b'\x89PNG\r\n\x1a\n' or len(png) > 65536
            or png[16:29] != struct.pack('>II', 720, 480) + bytes([8, 6, 0, 0, 0])):
        raise ValueError('Requires bounded 720x480 RGBA8 PNG')
    im = plan.image
    for address, expected in (
            (0x10413FF4, 'fd48'), (0x10413FFA, 'fc48'),
            (0x10414756, '3f49'), (0x104146A8, '30b589b00546'),
            (0x10431738, 'f0b585b01d460e46')):
        guard = bytes.fromhex(expected)
        if im.read(address, len(guard)) != guard:
            raise ValueError(f'Unexpected original Z7 graphics entry {address:#x}')
    asset = plan.alloc(png)
    draw = plan.alloc(bytes(512))
    c, call = constant, invoke
    plan.put(draw, assemble(f'''
        push.w {{r4-r10,lr}}; sub sp,#64; movs r8,#0;
        {c('r0', 0xA24F182C)} ldr r0,[r0]; cmp r0,#3; bne finish;
        {call(0x10413FF4)}
        {c('r0', 0xA180AD84)} ldrb r1,[r0]; cmp r1,#255; beq unlock;
        ldr r4,[r0,#4]; cmp r4,#0; beq unlock;
        {call(0x10414756)} mov r7,r0; movs r6,#0; mvn r5,#0;
        search: add r1,r6,r6,lsl #2; add r1,r4,r1,lsl #2; ldr r0,[r1];
        {c('r2', 0xB045F200)} cmp r0,r2; bne next;
        ldrb r0,[r1,#4]; cmp r0,#255; beq next;
        ldrh r0,[r1,#6]; {c('r2', 720)} cmp r0,r2; bne next;
        ldrh r0,[r1,#8]; cmp r0,#480; bne next;
        cmn r5,#1; bne unlock; mov r5,r6;
        next: adds r6,#1; cmp r6,#33; blo search;
        cmn r5,#1; beq unlock; mov r0,r5; {call(0x104146A8)}
        cmp r0,#1; bne restore;
        mov r9,sp; movs r10,#16; movs r0,#0;
        zero: str r0,[r9],#4; subs r10,#1; bne zero;
        {c('r0', asset)} str r0,[sp]; {c('r0', len(png))} str r0,[sp,#4];
        movs r0,#0; movs r1,#0; mov r2,sp; add r3,sp,#48;
        {call(0x10431738)} movs r8,#1;
        restore: mov r0,r7; {call(0x104146A8)} cmp r0,#1; beq unlock; movs r8,#0;
        unlock: {call(0x10413FFA)}
        finish: mov r0,r8; add sp,#64; pop.w {{r4-r10,pc}};
    ''', draw, 512))
    plan.features['spiral_probe'] = dict(draw=hex(draw), png=hex(asset), png_bytes=len(png),
        png_sha256=hashlib.sha256(png).hexdigest(), ui_surface='0xB045F200',
        registry='0xA180AD84', guarded_grid_value=3, native_mutex='0x10413FF4/0x10413FFA',
        native_target_query='0x10414756', native_target_select='0x104146A8',
        native_png_draw='0x10431738', automatic_redraw=False, camera_verified=False,
        limitations=['Explicit diagnostic entry only; no startup or redraw hook.',
                     'UI surface address and 720x480 shape are guarded lab assumptions.',
                     'Display/crop/EVF changes, cleanup, lifetime and concurrency need validation.'])
