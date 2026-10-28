# SPDX-License-Identifier: LicenseRef-Wonder-Lantern-Community
"""Independent Z7 UI-surface drawing diagnostic; no lifecycle hook installed."""
import hashlib
import struct

from ..assembly import assemble, constant, invoke


def configure(plan, png, follow_display=False, evf_png=None):
    if (png[:8] != b'\x89PNG\r\n\x1a\n' or len(png) > 65536
            or png[16:29] != struct.pack('>II', 720, 480) + bytes([8, 6, 0, 0, 0])):
        raise ValueError('Requires bounded 720x480 RGBA8 PNG')
    if follow_display:
        if (evf_png is None or evf_png[:8] != b'\x89PNG\r\n\x1a\n' or len(evf_png) > 65536
                or evf_png[16:29] != struct.pack('>II', 1280, 960) + bytes([8, 6, 0, 0, 0])):
            raise ValueError('Requires bounded 1280x960 RGBA8 EVF PNG')
        return configure_display(plan, png, evf_png)
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


def configure_display(plan, png, evf_png):
    """Use the active native LCD/EVF UI descriptor, never a guessed buffer."""
    im = plan.image
    for address, expected in (
            (0x10413FF4, 'fd48'), (0x10413FFA, 'fc48'),
            (0x10414756, '3f49'), (0x104146A8, '30b589b00546'),
            (0x10431738, 'f0b585b01d460e46'), (0x10433B80, '30b5032a')):
        guard = bytes.fromhex(expected)
        if im.read(address, len(guard)) != guard:
            raise ValueError(f'Unexpected original Z7 display graphics entry {address:#x}')
    asset = plan.alloc(png)
    evf_asset = plan.alloc(evf_png)
    draw = plan.alloc(bytes(1024))
    c, call = constant, invoke
    plan.put(draw, assemble(f'''
        push.w {{r4-r11,r12,lr}}; sub sp,#80; movs r8,#0;
        {c('r0', 0xA24F182C)} ldr r0,[r0]; cmp r0,#3; bne finish;
        {call(0x10413FF4)}
        {c('r0', 0xA1829E40)} ldr r1,[r0,#4];
        cmp r1,#1; beq accepted; cmp r1,#4; bne unlock;
        accepted: str r1,[sp,#68]; movs r0,#1; movs r2,#0; {call(0x10433B80)}
        cmp r0,#0; beq unlock;
        ldr r9,[r0,#0x24]; cmp r9,#0; beq unlock;
        ldr r10,[r0,#8]; ldr r1,[sp,#68]; cmp r1,#4; beq evf;
        {c('r1', (480 << 16) | 720)} cmp r10,r1; bne unlock;
        {c('r11', asset)} {c('r1', len(png))} str r1,[sp,#64]; b registry;
        evf: {c('r1', (960 << 16) | 1280)} cmp r10,r1; bne unlock;
        {c('r11', evf_asset)} {c('r1', len(evf_png))} str r1,[sp,#64];
        registry:
        {c('r0', 0xA180AD84)} ldrb r1,[r0]; cmp r1,#255; beq unlock;
        ldr r4,[r0,#4]; cmp r4,#0; beq unlock;
        {call(0x10414756)} mov r7,r0; movs r6,#0; mvn r5,#0;
        search: add r1,r6,r6,lsl #2; add r1,r4,r1,lsl #2; ldr r0,[r1];
        cmp r0,r9; bne next;
        ldrb r0,[r1,#4]; cmp r0,#255; beq next;
        ldrh r0,[r1,#6]; uxth r2,r10; cmp r0,r2; bne next;
        ldrh r0,[r1,#8]; lsr r2,r10,#16; cmp r0,r2; bne next;
        cmn r5,#1; bne unlock; mov r5,r6;
        next: adds r6,#1; cmp r6,#33; blo search;
        cmn r5,#1; beq unlock; mov r0,r5; {call(0x104146A8)}
        cmp r0,#1; bne restore;
        mov r10,sp; movs r6,#16; movs r0,#0;
        zero: str r0,[r10],#4; subs r6,#1; bne zero;
        str r11,[sp]; ldr r0,[sp,#64]; str r0,[sp,#4];
        movs r0,#0; movs r1,#0; mov r2,sp; add r3,sp,#48;
        {call(0x10431738)} movs r8,#1;
        restore: mov r0,r7; {call(0x104146A8)} cmp r0,#1; beq unlock; movs r8,#0;
        unlock: {call(0x10413FFA)}
        finish: mov r0,r8; add sp,#80; pop.w {{r4-r11,r12,pc}};
    ''', draw, 1024))
    plan.features['spiral_probe'] = dict(draw=hex(draw), png=hex(asset), png_bytes=len(png),
        png_sha256=hashlib.sha256(png).hexdigest(), ui_surface='Native active-display UI descriptor +0x24',
        registry='0xA180AD84', guarded_grid_value=3, native_mutex='0x10413FF4/0x10413FFA',
        native_target_query='0x10414756', native_target_select='0x104146A8',
        native_png_draw='0x10431738', native_ui_descriptor='0x10433B80', native_ui_component=1,
        accepted_display_ids=[1, 4], dimensions=[720, 480], color_rgba=[216, 216, 216, 255],
        evf_png=hex(evf_asset), evf_png_bytes=len(evf_png), evf_dimensions=[1280, 960],
        evf_png_sha256=hashlib.sha256(evf_png).hexdigest(),
        automatic_redraw=False, camera_verified=False,
        limitations=['Native active-display descriptor and existing registered surface are required.',
                     'Unregistered, null, ambiguous or mismatched LCD/EVF dimensions refuse drawing.',
                     'Physical EVF drawing, transitions, cleanup and performance need validation.'])
