# SPDX-License-Identifier: LicenseRef-Wonder-Lantern-Community
"""Independent Z7 third-value grid research; no installation clearance.

Store 0=Off, 1=4x4, 2=3x3 in Nikon's existing 32-bit grid scalar. Normalize
only 2 to boolean On at the native scalar-get API. Owned geometry/menu code
reads the stored value directly. The original 89-record storage format and
native setter/save/reset policy remain intact. Off forgets the previous type.
Stock code loads the scalar and treats 2 as Off in its audited menu/display
consumers; this is a selected-consumer result, not exhaustive compatibility.
"""
from ..assembly import assemble, constant, invoke, jump

RAW, GETTER = 0xA24F182C, 0x10070234
EXPECTED = bytes.fromhex('38b50c4600212160')


def tail(address):
    return f'.balign 4; ldr.w pc,[pc,#0]; .word {address | 1};'


def configure(plan, grid_functions, code, thirds_table):
    im = plan.image
    if im.read(GETTER, 8) != EXPECTED:
        raise ValueError('Unexpected original Z7 scalar getter')
    # Native property index is recovered through its group descriptor and
    # validated by instruction tests. Pin its type and actual storage pointer.
    descriptor = im.words(0x114D30CC, 4)
    if descriptor[0] != 7 or descriptor[2] != RAW:
        raise ValueError('Unexpected original grid scalar descriptor')
    original = plan.alloc(bytes(64))
    reader = plan.alloc(bytes(160))
    c, call = constant, invoke
    plan.put(original, assemble(f'''
        push {{r3-r5,lr}}; mov r4,r1; movs r1,#0; str r1,[r4];
        {tail(GETTER + 8)}
    ''', original, 64))
    plan.put(reader, assemble(f'''
        push {{r4-r8,lr}}; mov r4,r0; mov r5,r1; {call(original)}
        mrs r7,apsr; mov r6,r0; {c('r0', 0x102D)} cmp r4,r0; bne unchanged;
        cmp r6,#1; bne unchanged; ldr r0,[r5]; cmp r0,#2; bne unchanged;
        movs r0,#1; str r0,[r5];
        unchanged: mov r0,r6; msr APSR_nzcvq,r7; pop {{r4-r8,pc}};
    ''', reader, 160))
    plan.edit(GETTER, jump(GETTER, reader, 8), 'Normalize native grid third value at scalar reads', EXPECTED)
    code['geometry'] = f'''
        push {{r1,r2}}; {c('r0', 0x1064FD90)} {c('r1', RAW)} ldr r2,[r1];
        cmp r2,#2; bne chosen; {c('r0', thirds_table)}
        chosen: pop {{r1,r2}}; add.w r7,r0,r6,lsl #5;
        ldrh r0,[r7,#10]; mov r9,r0; adds r0,r0,#1;
        {tail(0x10376E9C)}
    '''
    code['fourths'] = tail(0x104F5588)
    code['thirds'] = f'movs r1,#2; {c("r0", 0x102D)} {tail(0x104065B0)}'
    start, end = code['enter'].index('select:'), code['enter'].index('mark:')
    selection = f'''
        select: {c('r0', RAW)} ldr r0,[r0]; {c('r1', 0x1902)}
        cmp r0,#1; beq fourths; cmp r0,#2; bne mark;
        {c('r1', 0x7A30)} b mark;
        fourths: {c('r1', 0x1901)}
    '''
    code['enter'] = code['enter'][:start] + selection + code['enter'][end:]
    # No RAM choice or custom heap reservation is used by this experiment.
    del code['cold']
    grid_functions.pop('cold')
    plan.features['grid_native'] = dict(raw_scalar=hex(RAW), property='0x102D',
        getter=hex(GETTER), reader=hex(reader), original_getter=hex(original),
        stored_values={'Off': 0, '4x4': 1, '3x3': 2}, native_read_value_for_3x3=1,
        native_records=89, custom_journal_hooks=False, custom_workspace=False,
        limitations=['Emulator-only experiment; physical installation not cleared.',
                     'Stock selected menu/display consumers treat stored 2 as Off.',
                     'Generic property consumers, user presets and shutdown need validation.',
                     'Off resets the stored choice; no independent last-type memory.'])
