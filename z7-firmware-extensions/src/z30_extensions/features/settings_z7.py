# SPDX-License-Identifier: LicenseRef-Wonder-Lantern-Community
"""Independent original Z7 C 3.80 journal integration; emulator-only prototype.

Own record 89, explicit old-format migration/rollback, CRC32 and snapshot/readback
verification. Never included in ordinary presets. No camera installation claim.
"""
import struct
import zlib

from ..assembly import assemble, constant, invoke, jump

STATE, MAGIC, STATE_BYTES = 0xA9700000, 0x47524431, 0x500
SCHEMA, HEADER, OWN_TABLE = 0xA18C2190, 0xA24E2C4C, STATE + 64
RECORD, RECORD_MAGIC = STATE + 16, 0x31534C57
NATIVE_BYTES, COUNT = 0x154CC, 89
PAYLOAD = 64 + 90 * 24
VERIFY_PAYLOAD = PAYLOAD + NATIVE_BYTES + 16
ALLOCATION = VERIFY_PAYLOAD + NATIVE_BYTES + 16
LOAD, SAVE, DESCRIPTOR, RESET = 0x101AEBAE, 0x101AEC44, 0x10070A16, 0x100709CA
EXPECTED = {
    LOAD: bytes.fromhex('f0b5012817468db00d460646'),
    SAVE: bytes.fromhex('f0b5012815468db00e460746'),
    DESCRIPTOR: bytes.fromhex('10b5204c07221d49091dd4e90034'),
    RESET: bytes.fromhex('10b5fff7e5fefff707ff'),
}


def tail(address):
    return f'.balign 4; ldr.w pc,[pc,#0]; .word {address | 1};'


def configure(plan, grid_functions, grid_code):
    im = plan.image
    # Exact source hash is also enforced by Plan/StockImage. These independent
    # contracts prevent a relocated/misidentified native entry from being used.
    for site, expected in EXPECTED.items():
        if im.read(site, len(expected)) != expected:
            raise ValueError(f'Unexpected Z7 settings entry at {site:#x}: {im.read(site, len(expected)).hex()}')
    if im.words(0x114E5224, 2) != (89, SCHEMA):
        raise ValueError('Unexpected original settings schema')
    schema = im.read(SCHEMA, COUNT * 12)
    entries = [struct.unpack_from('<3I', schema, index * 12) for index in range(COUNT)]
    if sum(entry[1] for entry in entries) != NATIVE_BYTES or entries[49][:2] != (0xA24F1778, 0x240):
        raise ValueError('Unexpected settings record sizes')
    rom_schema = plan.alloc(schema)
    sizes = dict(crc=128, record=96, defaults=128, descriptor=128, guard=192,
                 load=640, save=1024, snapshot=512, rollback=192, reset=128,
                 original_load=64, original_save=64)
    f = {key: plan.alloc(bytes(size)) for key, size in sizes.items()}
    c, call = constant, invoke
    own = lambda name: call(f[name])
    copy = lambda: invoke(0x10170AD4, thumb=False)
    code = {}
    code['crc'] = f"""
        push {{r4,lr}}; mvn r2,#0; {c('r4', 0xEDB88320)}
        byte_loop: cmp r1,#0; beq crc_done; ldrb r3,[r0],#1; eors r2,r3;
        movs r3,#8;
        bit_loop: lsrs r2,r2,#1; bcc no_xor; eors r2,r4;
        no_xor: subs r3,#1; bne bit_loop; subs r1,#1; b byte_loop;
        crc_done: mvn r0,r2; pop {{r4,pc}};
    """
    code['record'] = f"""
        push {{r4,lr}}; mov r4,r0; {c('r2', RECORD_MAGIC)} str r2,[r4];
        movs r2,#1; str r2,[r4,#4]; str r1,[r4,#8]; movs r1,#12;
        {own('crc')} str r0,[r4,#12]; pop {{r4,pc}};
    """
    code['defaults'] = f"""
        push {{r4,lr}}; {c('r4', STATE)} movs r0,#0; str r0,[r4,#4];
        str r0,[r4,#36]; movs r0,#1; str r0,[r4,#8]; str r0,[r4,#44];
        ldr r0,[r4,#32]; adds r0,#1; str r0,[r4,#32];
        add r0,r4,#16; movs r1,#0; {own('record')} pop {{r4,pc}};
    """
    code['descriptor'] = f"""
        push {{r4,lr}}; {c('r1', SCHEMA)} movs r3,#89; {c('r4', STATE)}
        ldr r2,[r4]; {c('r12', MAGIC)} cmp r2,r12; bne descriptor_done;
        ldr r2,[r4,#36]; cmp r2,#0; bne descriptor_done;
        {c('r1', OWN_TABLE)} movs r3,#90;
        descriptor_done: str r3,[r0]; str r1,[r0,#4]; movs r2,#7;
        str r2,[r0,#8]; {c('r1', HEADER + 4)} str r1,[r0,#12]; pop {{r4,pc}};
    """
    # A magic word alone cannot authorize a mutable table of load destinations.
    # The native loader writes flash-source caches into each triple's third
    # word; only destination pointers and lengths are immutable contracts.
    code['guard'] = f"""
        push {{r4-r6,lr}}; {c('r4', STATE)} ldr r0,[r4]; {c('r1', MAGIC)}
        cmp r0,r1; bne guard_bad; ldr r0,[r4,#36]; cmp r0,#1; bhi guard_bad;
        {c('r0', OWN_TABLE)} {c('r1', rom_schema)} movs r2,#89;
        guard_pair: ldrd r3,r4,[r0]; ldrd r5,r6,[r1]; cmp r3,r5; bne guard_bad;
        cmp r4,r6; bne guard_bad; adds r0,#12; adds r1,#12;
        subs r2,#1; bne guard_pair;
        {c('r0', OWN_TABLE + COUNT * 12)} ldr r1,[r0]; {c('r2', RECORD)}
        cmp r1,r2; bne guard_bad; ldr r1,[r0,#4]; cmp r1,#16; bne guard_bad;
        movs r0,#1; pop {{r4-r6,pc}};
        guard_bad: movs r0,#0; pop {{r4-r6,pc}};
    """
    for name, site, args in (('original_load', LOAD, 'mov r7,r2; sub sp,#52; mov r5,r1; mov r6,r0;'),
                             ('original_save', SAVE, 'mov r5,r2; sub sp,#52; mov r6,r1; mov r7,r0;')):
        code[name] = f'push {{r4-r7,lr}}; cmp r0,#1; {args} {tail(site + 12)}'
    code['load'] = f"""
        cmp r0,#15; bne load_passthrough;
        push {{r4-r8,lr}}; sub sp,#16; mov r4,r0; mov r5,r1; mov r6,r2;
        {c('r7', STATE)} {own('guard')} cmp r0,#1; bne load_rejected;
        ldr r0,[r5]; {c('r1', HEADER)} cmp r0,r1; bne load_failed;
        ldr r0,[r5,#4]; {c('r1', NATIVE_BYTES)} cmp r0,r1; bne load_failed;
        mov r0,sp; {own('descriptor')}
        mov r0,r4; mov r1,r5; mov r2,sp;
        {own('original_load')} cmp r0,#1; beq load_validate;
        movs r0,#89; str r0,[sp]; {c('r0', SCHEMA)} str r0,[sp,#4];
        movs r0,#7; str r0,[sp,#8]; {c('r0', HEADER + 4)} str r0,[sp,#12];
        mov r0,r4; mov r1,r5; mov r2,sp; {own('original_load')}
        cmp r0,#1; bne load_failed;
        movs r0,#0; str r0,[r7,#4]; str r0,[r7,#8];
        movs r0,#1; str r0,[r7,#36];
        movs r0,#6; str r0,[r7,#12]; b load_good;
        load_validate: ldr r0,[r7,#36]; cmp r0,#0; bne load_stock;
        ldr r0,[r7,#16]; {c('r1', RECORD_MAGIC)} cmp r0,r1; bne load_invalid;
        ldr r0,[r7,#20]; cmp r0,#1; bne load_invalid;
        ldr r8,[r7,#24]; cmp r8,#1; bhi load_invalid;
        add r0,r7,#16; movs r1,#12; {own('crc')}
        ldr r1,[r7,#28]; cmp r0,r1; bne load_invalid;
        str r8,[r7,#4]; movs r0,#0; str r0,[r7,#8];
        movs r0,#1; str r0,[r7,#12]; b load_good;
        load_invalid: {own('defaults')} movs r0,#3; str r0,[r7,#12]; b load_good;
        load_stock: movs r0,#6; str r0,[r7,#12];
        load_good: movs r0,#1; dmb sy; str r0,[r7,#44]; b load_return;
        load_failed: movs r0,#4; str r0,[r7,#12]; movs r0,#0; str r0,[r7,#44];
        b load_return;
        load_rejected: movs r0,#0;
        load_return: add sp,#16; pop {{r4-r8,pc}};
        load_passthrough: {tail(f['original_load'])}
    """
    # Fixed ROM schema supplies all original source pointers/lengths; native
    # flash-source caches and external descriptors never become copy sizes.
    code['snapshot'] = f"""
        push {{r4-r11,lr}}; sub sp,#4; mov r11,r0; mov r9,r1; mov r10,r2;
        {c('r4', rom_schema)} add r5,r11,#64; {c('r0', 64 + 90 * 12)} add r6,r11,r0;
        {c('r0', PAYLOAD)} add r7,r11,r0;
        {c('r0', VERIFY_PAYLOAD)} add r8,r11,r0; movs r0,#89; str r0,[sp];
        snapshot_loop: ldr r1,[r4]; ldr r2,[r4,#4]; str r7,[r5]; str r2,[r5,#4];
        str r8,[r6]; str r2,[r6,#4]; movs r0,#0; str r0,[r5,#8]; str r0,[r6,#8];
        mov r0,r7; {copy()} ldr r0,[r4,#4]; add r7,r7,r0; add r8,r8,r0;
        adds r4,#12; adds r5,#12; adds r6,#12; ldr r0,[sp]; subs r0,#1;
        str r0,[sp]; bne snapshot_loop;
        cmp r9,#90; bne snapshot_descriptors;
        str r7,[r5]; str r8,[r6]; movs r0,#16; str r0,[r5,#4]; str r0,[r6,#4];
        movs r0,#0; str r0,[r5,#8]; str r0,[r6,#8];
        mov r0,r7; mov r1,r10; {own('record')}
        snapshot_descriptors: str r9,[r11]; str r9,[r11,#16];
        add r0,r11,#64; str r0,[r11,#4];
        {c('r0', 64 + 90 * 12)} add r0,r11,r0; str r0,[r11,#20];
        movs r0,#7; str r0,[r11,#8]; str r0,[r11,#24];
        {c('r0', PAYLOAD)} add r0,r11,r0; str r0,[r11,#32]; adds r0,#4; str r0,[r11,#12];
        {c('r0', VERIFY_PAYLOAD)} add r0,r11,r0; str r0,[r11,#40]; adds r0,#4; str r0,[r11,#28];
        {c('r0', NATIVE_BYTES)} cmp r9,#90; bne snapshot_length; adds r0,#16;
        snapshot_length: str r0,[r11,#36]; str r0,[r11,#44];
        add sp,#4; pop {{r4-r11,pc}};
    """
    code['save'] = f"""
        cmp r0,#15; bne save_passthrough;
        push {{r4-r11,lr}}; sub sp,#100; {c('r8', STATE)} mov r6,r1; mov r7,r2;
        movs r4,#0; str r4,[sp,#72]; {own('guard')} cmp r0,#1; bne save_exit;
        ldr r0,[r8,#44]; cmp r0,#1; bne save_exit;
        movs r3,#8; add r0,r8,#40;
        lock_retry: ldrex r1,[r0]; cmp r1,#0; bne save_busy;
        movs r2,#1; strex r1,r2,[r0]; cmp r1,#0; beq save_locked;
        subs r3,#1; bne lock_retry;
        save_busy: clrex; b save_exit;
        save_locked: dmb sy; ldr r9,[r7]; ldr r0,[r8,#36]; cmp r0,#0; bne stock_count;
        cmp r9,#90; bne save_fail; b count_ok;
        stock_count: cmp r0,#1; bne save_fail; cmp r9,#89; bne save_fail;
        count_ok: ldr r0,[r7,#8]; cmp r0,#7; bne save_fail;
        ldr r0,[r7,#12]; {c('r1', HEADER + 4)} cmp r0,r1; bne save_fail;
        {c('r1', SCHEMA)} cmp r9,#89; beq table_ready; {c('r1', OWN_TABLE)}
        table_ready: ldr r0,[r7,#4]; cmp r0,r1; bne save_fail;
        ldr r0,[r6]; {c('r1', HEADER)} cmp r0,r1; bne save_fail;
        ldr r0,[r6,#4]; {c('r1', NATIVE_BYTES)} cmp r0,r1; bne save_fail;
        ldr r11,[r8,#32]; ldr r5,[r8,#4]; cmp r5,#1; bhi save_fail;
        {c('r0', ALLOCATION)} movs r1,#0; {call(0x1016FE38)} movs r10,r0; beq save_fail;
        mov r1,r9; mov r2,r5; {own('snapshot')}
        {c('r0', 0xA1880B00 + 15 * 28 + 8)} ldrd r1,r2,[r0]; strd r1,r2,[sp];
        {c('r1', 0xA20A6CB0)} add r0,sp,#8; movs r2,#16; {copy()}
        movs r0,#15; add r1,r10,#32; mov r2,r10; {own('original_save')}
        str r0,[sp,#72]; movs r0,#15; add r1,r10,#40; add r2,r10,#16;
        {own('original_load')} cmp r0,#1; bne verify_bad;
        ldr r0,[r10,#32]; ldr r1,[r10,#40]; ldr r2,[r10,#36]; {call(0x101F239C)}
        cmp r0,#0; bne verify_bad; ldr r0,[sp,#72]; cmp r0,#1; bne verify_bad;
        movs r4,#1; b verify_cleanup;
        verify_bad: movs r4,#0;
        verify_cleanup: {c('r0', 0xA1880B00 + 15 * 28 + 8)} ldrd r1,r2,[sp]; strd r1,r2,[r0];
        {c('r0', 0xA20A6CB0)} add r1,sp,#8; movs r2,#16; {copy()}
        mov r0,r10; {call(0x1016FE4A)} cmp r4,#1; bne save_fail;
        movs r0,#5; str r0,[r8,#12]; ldr r0,[r8,#32]; cmp r0,r11; bne save_unlock;
        movs r0,#0; str r0,[r8,#8]; b save_unlock;
        save_fail: movs r4,#0; movs r0,#1; str r0,[r8,#8]; movs r0,#4; str r0,[r8,#12];
        save_unlock: movs r0,#0; dmb sy; str r0,[r8,#40];
        save_exit: mov r0,r4; add sp,#100; pop {{r4-r11,pc}};
        save_passthrough: {tail(f['original_save'])}
    """
    code['rollback'] = f"""
        push {{r4-r6,lr}}; {c('r4', STATE)} {own('guard')} cmp r0,#1; bne rollback_bad;
        ldr r5,[r4,#36];
        movs r0,#1; str r0,[r4,#36]; {call(0x1011764A)} cmp r0,#1; bne rollback_failed;
        movs r1,#0; str r1,[r4,#4]; movs r1,#6; str r1,[r4,#12]; pop {{r4-r6,pc}};
        rollback_failed: str r5,[r4,#36];
        rollback_bad: movs r0,#0; pop {{r4-r6,pc}};
    """
    code['reset'] = f"""
        push {{r4,lr}}; {c('r0', STATE)} ldr r0,[r0]; {c('r1', MAGIC)} cmp r0,r1; bne reset_stock;
        {own('defaults')} reset_stock: {call(0x1007079A)} {call(0x100707E2)} {tail(RESET + 10)}
    """
    default_crc = zlib.crc32(struct.pack('<3I', RECORD_MAGIC, 1, 0))
    grid_code['cold'] = f"""
        push {{r2,r3}}; {c('r2', STATE)} {c('r0', STATE + STATE_BYTES)} movs r3,#0;
        cold_zero: str r3,[r2],#4; cmp r2,r0; blo cold_zero;
        {c('r0', rom_schema)} {c('r1', OWN_TABLE)} {c('r2', COUNT * 3)}
        cold_table: ldr r3,[r0],#4; str r3,[r1],#4; subs r2,#1; bne cold_table;
        {c('r3', RECORD)} str r3,[r1]; movs r3,#16; str r3,[r1,#4];
        {c('r2', RECORD)} {c('r3', RECORD_MAGIC)} str r3,[r2];
        movs r3,#1; str r3,[r2,#4]; {c('r3', default_crc)} str r3,[r2,#12];
        {c('r2', STATE)} {c('r3', MAGIC)} dmb sy; str r3,[r2]; pop {{r2,r3}};
        {c('r1', 0xA18FD738)} {c('r0', STATE + STATE_BYTES)} str r0,[r1];
        {c('r0', STATE)} pop.w {{r4,lr}}; {tail(0x101E3BB8)}
    """
    for name, choice in (('fourths', 0), ('thirds', 1)):
        grid_code[name] = f"""
            push {{r0-r3}}; {c('r0', STATE)} ldr r1,[r0]; {c('r2', MAGIC)} cmp r1,r2; bne unchanged;
            ldr r1,[r0,#36]; cmp r1,#0; bne changed;
            ldr r1,[r0,#4]; cmp r1,#{choice}; beq unchanged;
            changed: movs r1,#0; str r1,[r0,#36];
            movs r1,#{choice}; str r1,[r0,#4]; movs r1,#1; str r1,[r0,#8];
            ldr r1,[r0,#32]; adds r1,#1; str r1,[r0,#32]; dmb sy;
            unchanged: pop {{r0-r3}}; {tail(0x104F5588)}
        """
    for name, source in code.items():
        plan.put(f[name], assemble(source, f[name], sizes[name]))
    for site, name in ((LOAD, 'load'), (SAVE, 'save'), (DESCRIPTOR, 'descriptor'), (RESET, 'reset')):
        expected = EXPECTED[site]
        plan.edit(site, jump(site, f[name], len(expected)), 'Independent grid journal ' + name, expected)
    plan.features['settings'] = dict(functions={k: hex(v) for k, v in f.items()},
        state=hex(STATE), state_bytes=STATE_BYTES, owned_table=hex(OWN_TABLE),
        record=hex(RECORD), record_magic=hex(RECORD_MAGIC), version=1, crc='IEEE CRC32 over first 12 bytes',
        native_records=89, extended_records=90, allocation_bytes=ALLOCATION,
        expected_payload_offset=PAYLOAD, verify_payload_offset=VERIFY_PAYLOAD,
        status_codes={'unloaded': 0, 'loaded': 1, 'migrated': 2, 'invalid_record': 3,
                      'save_failed': 4, 'verified': 5, 'stock_format_ready': 6},
        limitations=['Emulator only; no physical installation clearance.',
                     'Rollback entry is diagnostic; no camera menu/updater integration yet.',
                     'Original-format boot remains original until an explicit grid choice enables the extension.',
                     'Normal native worker policy controls when saving occurs.',
                     'Power-loss recovery and concurrency require independent validation.'])
