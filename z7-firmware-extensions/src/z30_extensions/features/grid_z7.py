# SPDX-License-Identifier: LicenseRef-Wonder-Lantern-Community
"""Independent Z7 C 3.80 selectable-grid experiment, emulator only.

Native d9 becomes 4x4 / 3x3 / Off. The default keeps a separate RAM choice;
native_choice uses the existing grid scalar. extra_grids adds optional golden,
center and dense layouts, with independent emulator-only candidate identity.
The previous three-row modes retain their exact binary output and reports.
This standalone experiment must not be composed with the splash state hook.
"""
import struct

from ..assembly import assemble, constant, invoke, jump
from ..plan import Plan
from ..platform import z7_380 as platform

STATE, STATE_BYTES, MAGIC = 0xA9700000, 64, 0x47524431
CURSOR, HEAP_SITE = 0xA18FD738, 0x101E3DA0
TABLE, GEOMETRY_SITE = 0x1064FD90, 0x10376E90
PAGE, OBJECT = 0x153, 0xA1836F8C
THIRDS_ID = 0x7A30
HEAP_EXPECTED = bytes.fromhex('504933480860bde8104005e7')
GEOMETRY_EXPECTED = bytes.fromhex('f74800eb461778898146401c')


def tail(address):
    return f'.balign 4; ldr.w pc,[pc,#0]; .word {address | 1};'


def build(source, persistent=False, native_choice=False, extra_grids=False):
    if persistent and native_choice:
        raise ValueError('Choose one grid storage experiment')
    if extra_grids and not native_choice:
        raise ValueError('Extra grids require the existing native scalar mode')
    plan = Plan(source, platform)
    im = plan.image
    if (im.read(HEAP_SITE, 12) != HEAP_EXPECTED
            or im.read(GEOMETRY_SITE, 12) != GEOMETRY_EXPECTED
            or im.words(0x101E3EE4, 2) != (CURSOR, 0xAC400000)
            or im.words(0x101E3E70, 1)[0] != STATE):
        raise ValueError('Unexpected Z7 workspace or grid instruction window')
    obj = im.words(OBJECT, 11)
    meta = list(im.words(obj[10], 7))
    callbacks = im.words(obj[4], 5)
    if (obj[0] != (PAGE << 16) | 2 or callbacks[0] != 0x104EFA6B
            or callbacks[2] != 0x1040525F or meta[5] != 0x20002):
        raise ValueError('Unexpected original Z7 grid page')
    original_controls = im.read(meta[3], 56)
    if (struct.unpack_from('<I', original_controls, 24)[0] != 0x1901
            or struct.unpack_from('<I', original_controls, 52)[0] != 0x1902):
        raise ValueError('Unexpected Z7 On/Off grid controls')
    used = set()
    for index in range(0x1000):
        try:
            page = im.words(0xA1833548 + index * 44, 11)
            if page[0] != (index << 16) | 2:
                continue
            header = im.words(page[10], 7)
            for row in range(header[5] & 65535):
                used.add(im.words(header[3] + row * 28 + 24, 1)[0] & 65535)
        except (ValueError, struct.error):
            continue
    independent_ids = (THIRDS_ID, 0x7A31, 0x7A32, 0x7A33) if extra_grids else (THIRDS_ID,)
    if any(control in used for control in independent_ids):
        raise ValueError('Independent grid control ID collides with stock')
    thirds = bytearray(im.read(TABLE, 96))
    for record in range(3):
        for offset in (10, 22):
            position = record * 32 + offset
            if struct.unpack_from('<H', thirds, position)[0] != 3:
                raise ValueError('Original grid count differs from three')
            struct.pack_into('<H', thirds, position, 2)
    thirds_table = plan.alloc(thirds)
    sizes = dict(cold=192 if not persistent else 256, geometry=128, enter=384,
                 fourths=64 if not persistent else 96, thirds=64 if not persistent else 96)
    choices = [('fourths', '4x4 grid', 0x1901, 1, 3),
               ('thirds', '3x3 grid', THIRDS_ID, 2, 2)]
    if extra_grids:
        choices += [('golden', 'Golden ratio', 0x7A31, 3, 2),
                    ('center', 'Center cross', 0x7A32, 4, 1),
                    ('dense', '6x6 grid', 0x7A33, 5, 5)]
        sizes.update(geometry=256, enter=768, golden=64, center=64, dense=64)
    choices += [('off', 'Off', 0x1902, 0, 3)]
    row_count = len(choices)
    functions = {name: plan.alloc(bytes(size)) for name, size in sizes.items()}
    texts = [plan.alloc(choice[1].encode('ascii') + b'\0') for choice in choices]
    c, call = constant, invoke
    code = {}
    code['cold'] = f"""
        push {{r2,r3}}; {c('r2', STATE)} movs r3,#0;
        str r3,[r2,#4]; str r3,[r2,#8]; str r3,[r2,#12];
        str r3,[r2,#16]; str r3,[r2,#20]; str r3,[r2,#24]; str r3,[r2,#28];
        str r3,[r2,#32]; str r3,[r2,#36]; str r3,[r2,#40]; str r3,[r2,#44];
        str r3,[r2,#48]; str r3,[r2,#52]; str r3,[r2,#56]; str r3,[r2,#60];
        dmb sy; {c('r3', MAGIC)} str r3,[r2]; pop {{r2,r3}};
        {c('r1', CURSOR)} {c('r0', STATE + STATE_BYTES)} str r0,[r1];
        {c('r0', STATE)} pop.w {{r4,lr}}; {tail(0x101E3BB8)}
    """
    # The native builder snapshots one immutable table pointer. Selection is
    # one aligned 32-bit store; its six counts never change under a reader.
    code['geometry'] = f"""
        push {{r1,r2}}; {c('r0', TABLE)} {c('r1', STATE)} ldr r2,[r1];
        {c('r1', MAGIC)} cmp r2,r1; bne chosen;
        {c('r1', STATE)} ldr r2,[r1,#4]; cmp r2,#1; bne chosen;
        {c('r0', thirds_table)}
        chosen: pop {{r1,r2}}; add.w r7,r0,r6,lsl #5;
        ldrh r0,[r7,#10]; mov r9,r0; adds r0,r0,#1;
        {tail(GEOMETRY_SITE + 12)}
    """
    for name, choice in (('fourths', 0), ('thirds', 1)):
        code[name] = f"""
            push {{r0-r3}}; {c('r0', STATE)} ldr r1,[r0];
            {c('r2', MAGIC)} cmp r1,r2; bne unchanged;
            movs r1,#{choice}; str r1,[r0,#4]; dmb sy;
            unchanged: pop {{r0-r3}}; {tail(0x104F5588)}
        """
    labels = ''.join(f"{c('r0', text)} movs r1,#{39 + i}; movs r2,#0; {call(0x103FBB5C)}"
                     for i, text in enumerate(texts))
    code['enter'] = f"""
        push {{r4-r8,lr}}; mov r4,r0; {labels}
        ldr r5,[r4,#36]; movs r6,#0;
        rows: cmp r5,#0; beq select; mov r0,r5; movs r1,#1; mov r2,r6;
        {call(0x103FCF0E)} add r1,r6,#39; {call(0x103FB344)}
        adds r6,#1; cmp r6,#{row_count}; blo rows;
        select: {c('r0', 0x102D)} {call(0x104065A4)}
        {c('r1', 0x1902)} cmp r0,#1; bne mark;
        {c('r1', 0x1901)} {c('r0', STATE)} ldr r2,[r0];
        {c('r3', MAGIC)} cmp r2,r3; bne mark;
        ldr r2,[r0,#4]; cmp r2,#1; bne mark; {c('r1', THIRDS_ID)}
        mark: mov r7,r1; {call(0x10405F00)} cmp r0,#1; beq current;
        mov r0,r4; mov r1,r7; {call(0x10402BC2)}
        current: mov r0,r4; mov r1,r7; movs r2,#1; {call(0x10404CD8)}
        movs r0,#0; pop {{r4-r8,pc}};
    """
    if persistent:
        from .settings_z7 import configure
        configure(plan, functions, code)
    if native_choice:
        from .grid_native_z7 import configure
        configure(plan, functions, code, thirds_table, choices=choices if extra_grids else None)
    for name, text in code.items():
        plan.put(functions[name], assemble(text, functions[name], sizes[name]))
    dispatch = im.words(meta[4], 2)
    maps = []
    for name, _, _, _, _ in choices[:-1]:
        events = bytearray(im.read(dispatch[0], 17 * 16))
        activation_count = 0
        for index in range(17):
            event, fn, predicate, destination = struct.unpack_from('<4I', events, index * 16)
            if event in (0x239, 0x25F):
                if (fn, predicate, destination) != (0x104F5589, 0, 0x3A1):
                    raise ValueError('Unexpected native grid activation contract')
                struct.pack_into('<I', events, index * 16 + 4, functions[name] | 1)
                activation_count += 1
        if activation_count != 2:
            raise ValueError('Missing native grid activation events')
        maps.append(plan.alloc(events))
    controls = bytearray(original_controls[:28] * (row_count - 1) + original_controls[28:])
    for index, (_, _, control_id, _, _) in enumerate(choices):
        struct.pack_into('<I', controls, index * 28, 39 + index)
        # Mark labels as dynamic slots. The stock 0x1000 flag would interpret
        # 39..41 as unrelated translated Nikon resource IDs on every redraw.
        struct.pack_into('<I', controls, index * 28 + 16, 0x1209)
        struct.pack_into('<I', controls, index * 28 + 24, control_id)
    control_table = plan.alloc(controls)
    dispatch_table = plan.alloc(struct.pack(f'<{row_count}I', *maps, dispatch[1]))
    boxes, labels_rect, values = [], [], []
    for y in ((96, 148, 200, 252, 304, 356) if extra_grids else (110, 214, 318)):
        boxes.extend((72, y, 702, y + 48))
        labels_rect.extend((150, y + 4, 690, y + 44))
        values.extend((690, y, 696, y + 48))
    rectangles = [plan.alloc(struct.pack(f'<{row_count * 4}h', *rect)) for rect in (boxes, labels_rect, values)]
    geometry = plan.alloc(struct.pack('<4I', row_count, *rectangles))
    meta[1], meta[3], meta[4], meta[5] = geometry, control_table, dispatch_table, row_count | (row_count << 16)
    metadata = plan.alloc(struct.pack('<7I', *meta))
    plan.edit(OBJECT + 40, struct.pack('<I', metadata), 'Independent Z7 grid page metadata')
    plan.edit(obj[4], struct.pack('<I', functions['enter'] | 1), 'Independent grid page constructor')
    if not native_choice:
        plan.edit(HEAP_SITE, jump(HEAP_SITE, functions['cold'], 12), 'Reserve grid choice state', HEAP_EXPECTED)
    plan.edit(GEOMETRY_SITE, jump(GEOMETRY_SITE, functions['geometry'], 12),
              'Select immutable native grid table', GEOMETRY_EXPECTED)
    plan.features['grid'] = dict(functions={key: hex(value) for key, value in functions.items()},
        state=hex(STATE), state_bytes=STATE_BYTES, magic=hex(MAGIC),
        table=hex(TABLE), thirds_table=hex(thirds_table), page=hex(PAGE),
        object=hex(OBJECT), metadata=hex(metadata), geometry=hex(geometry),
        controls=hex(control_table), dispatch=hex(dispatch_table),
        control_ids=[0x1901, THIRDS_ID, 0x1902],
        choices=['4x4', '3x3', 'Off'], native_property='0x102D',
        choice_persistence='RAM only; resets to 4x4 on cold startup',
        composition='Standalone only; shares workspace-init boundary with splash experiment')
    if persistent:
        plan.features['grid'].update(state_bytes=0x500,
            choice_persistence='Native journal record 89; emulator-only with migration and verified saves')
    if native_choice:
        plan.features['grid'].update(state=None, state_bytes=0,
            choice_persistence='Existing native grid scalar; emulator-only third-value experiment',
            off_behavior='Off stores 0; choosing 3x3 again stores 2',
            composition='Standalone experiment; no custom workspace or journal hooks')
    if extra_grids:
        plan.features['grid'].update(control_ids=[choice[2] for choice in choices],
            choices=[choice[1] for choice in choices],
            layouts=[dict(function=name, label=label, control_id=control,
                          stored_value=value, line_count=count)
                     for name, label, control, value, count in choices],
            choice_persistence='Existing native grid scalar; additional-value emulator experiment')
    eg, report = plan.finish()
    preset = ('grid-layouts-emulator-only' if extra_grids else
              'grid-native-value-emulator-only' if native_choice else
              'grid-persistent-emulator-only' if persistent else 'grid-emulator-only')
    report.update(preset=preset, emulator_only=True)
    return eg, report
