"""Trace stock Z7 settings and logical storage in isolated Unicorn memory.

No patched firmware, camera/card access or host-backed flash device. The original
property writer, packed snapshot updater, storage initializer and logical block
save/load execute. Flash erase/program and OS locks are supplied boundaries.
This does not establish a safe persistent slot for independent extensions.
"""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import struct

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_CPU_ARM_CORTEX_A15
from audit_splash_image import NativePNG, MEM, STOCK_SHA, BASE

RECORDS, METADATA = 0xA1880B00, 0xA18806B4
GRID_VALUE, SNAPSHOT = 0xA24F182C, 0xA20A6D48
FLASH, FLASH_BYTES = 0x132C0000, 0x20000
JOURNAL_BANKS = (0x12E00000, 0x131E0000)
JOURNAL_BYTES = 0x40000
HEADER, SCHEMA = 0xA24E2C4C, 0xA18C2190
STORES = ((FLASH, FLASH_BYTES),) + tuple((a, JOURNAL_BYTES) for a in JOURNAL_BANKS)


class SettingsFixture(NativePNG):
    def __init__(self, raw, flash=None, failure=None, journal=None):
        # Selective boundaries keep native copy/default loops uninstrumented.
        # NativePNG's call/ret helpers still enforce stack/callee-saved ABI.
        self.u = u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_A15)
        u.mem_map(BASE, (len(raw) + 4095) & ~4095)
        u.mem_write(BASE, raw)
        u.mem_map(0xA1800000, 0x110000)
        u.mem_write(0xA1800000, raw[0x11E9C214 - BASE:0x11E9C214 - BASE + 0x101200])
        u.mem_map(MEM, 0x400000)
        for address in (0x101E3DAC, 0x101BB404, 0x101F2514, 0x10170944,
                        0x1017093E, 0x10170BE8, 0x10170BF6, 0x101ADA80,
                        0x101ADAA2, 0x101AE430, 0x101AE3F0):
            u.hook_add(UC_HOOK_CODE, self.hook, begin=address, end=address)
        self.u.mem_map(0xA2000000, 0x1000000)
        self.u.mem_map(FLASH, FLASH_BYTES)
        self.u.mem_write(FLASH, flash if flash is not None else b'\xff' * FLASH_BYTES)
        for index, address in enumerate(JOURNAL_BANKS):
            self.u.mem_map(address, JOURNAL_BYTES)
            self.u.mem_write(address, journal[index] if journal else b'\xff' * JOURNAL_BYTES)
        self.failure = failure
        self.operations, self.locks = [], []

    def word(self, address):
        return struct.unpack('<I', self.u.mem_read(address, 4))[0]

    def record(self, number):
        return struct.unpack('<7I', self.u.mem_read(RECORDS + number * 28, 28))

    def hook(self, u, address, size, context):
        r0, r1, r2 = (u.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2))
        if address == 0x101E3DAC:
            if r0 != 0x380000:
                raise AssertionError('Unexpected native storage workspace size')
            self.ret(0xA2800000)
        elif address == 0x101BB404:
            if r0 != 0x152:
                raise AssertionError('Unexpected initialization model key')
            self.ret(0x50010000)
        elif address == 0x101F2514:
            u.mem_write(r1, struct.pack('<H', 0x152))
            self.ret(0)
        elif address in (0x10170944, 0x1017093E, 0x10170BE8, 0x10170BF6):
            self.locks.append((hex(address), hex(r0)))
            self.ret(0)
        elif address == 0x101ADA80:
            self.ret(0)  # OS context guard, not the storage selection/writer.
        elif address == 0x101ADAA2:
            if r0:
                raise AssertionError('Unexpected OS context restoration')
            self.ret(0)
        elif address == 0x101AE430:
            start, length = 0x10000000 + r0 * 0x20000, r1 * 0x20000
            if not any(base <= start and start + length <= base + count for base, count in STORES):
                raise AssertionError('Erase escaped the synthetic storage regions')
            self.operations.append(dict(kind='erase', address=hex(start), bytes=length))
            if self.failure != 'erase':
                u.mem_write(start, b'\xff' * length)
            self.ret(int(self.failure == 'erase'))
        elif address == 0x101AE3F0:
            length = r2 * 2  # Native wrapper converts byte count to halfwords.
            if not any(base <= r0 and r0 + length <= base + count for base, count in STORES):
                raise AssertionError('Program escaped the synthetic storage regions')
            self.operations.append(dict(kind='program', address=hex(r0), bytes=length))
            if self.failure != 'program':
                before = bytes(u.mem_read(r0, length))
                data = bytes(u.mem_read(r1, length))
                if any((old & new) != new for old, new in zip(before, data)):
                    raise AssertionError('Program attempted a zero-to-one flash transition')
                u.mem_write(r0, data)
            self.ret(int(self.failure == 'program'))
        else:
            raise AssertionError('Unexpected supplied boundary')

    def schema(self, extra=False):
        self.call(0x100709EA, MEM + 4)
        self.u.mem_write(MEM, struct.pack('<I', HEADER))
        self.call(0x10070A16, MEM + 0x20)
        if extra:
            # Experimental supplied schema only; no firmware edits. Keep all
            # native IDs and record sizes, append one independently owned ID.
            table, state = MEM + 0x1000, MEM + 0x2000
            self.u.mem_write(table, bytes(self.u.mem_read(SCHEMA, 89 * 12))
                             + struct.pack('<3I', state, 16, 0))
            self.u.mem_write(state, struct.pack('<4I', 0x47524431, 1, 0, 0))
            self.u.mem_write(MEM + 0x20, struct.pack('<4I', 90, table, 7, HEADER + 4))
        return MEM, MEM + 0x20

    def journal(self):
        return [bytes(self.u.mem_read(address, JOURNAL_BYTES)) for address in JOURNAL_BANKS]


def audit(raw):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA:
        raise ValueError('Requires pinned original Z7 C 3.80 MAIN')
    checks, observations = [], {}
    def check(name, passed):
        checks.append(dict(name=name, passed=bool(passed)))
    f = SettingsFixture(raw)
    f.call(0x10091CAC)
    parent, member = f.record(0x11), f.record(0x13)
    check('native-storage-initializer-binds-member-to-parent-buffer',
          parent[3] == 0x1FFFC and member[2] == parent[2] + 0xA100
          and member[3] == 0x100 and member[5:] == (0x11, 0x11))
    observations['logical_member'] = dict(id='0x13', parent='0x11',
        parent_bytes=parent[3], member_offset='0xA100', member_bytes=member[3],
        physical_bank=hex(FLASH))
    for value in (0, 1, 2, 0xFFFFFFFF):
        prior = bytes(f.u.mem_read(GRID_VALUE - 4, 12))
        result = f.call(0x100704FA, 0x102D, value, MEM)
        after = bytes(f.u.mem_read(GRID_VALUE - 4, 12))
        check(f'native-grid-scalar-writer-accepts-{value}', result == 1
              and f.word(GRID_VALUE) == value
              and after[:4] == prior[:4] and after[8:] == prior[8:])
    observations['grid_range'] = 'Raw scalar storage accepts 32-bit values; stock menu/display consumers supply or require 0/1. Writer is not an enum validator.'
    f.u.mem_write(SNAPSHOT, b'\x5a' * 0x384)
    f.call(0x100B9E6C, SNAPSHOT, 0x102D, 1)
    snapshot = bytes(f.u.mem_read(SNAPSHOT, 0x384))
    check('packed-snapshot-grid-is-one-byte-at-29c',
          snapshot == b'\x5a' * 0x29C + b'\x01' + b'\x5a' * (0x384 - 0x29D))
    f.call(0x100B9E6C, SNAPSHOT, 0xFFFF, 1)
    check('packed-snapshot-unknown-id-is-ignored', bytes(f.u.mem_read(SNAPSHOT, 0x384)) == snapshot)
    check('packed-snapshot-alone-did-not-program-flash', not f.operations)
    observations['snapshot'] = dict(table='0xA18C25D0', entries=452,
        grid_entry=324, offset='0x29C', width=1,
        caution='This RAM snapshot update is not itself a persistent commit.')

    # Exercise the native member save path with entirely synthetic data. Using
    # the member's existing pointer is the original shared-parent-buffer API.
    payload = bytes((index * 37 + 11) & 255 for index in range(parent[3]))
    f.u.mem_write(parent[2], payload)
    result = f.call(0x101AEA60, 0x13, member[2], member[3])
    flash = bytes(f.u.mem_read(FLASH, FLASH_BYTES))
    check('native-member-save-reports-success-with-supplied-flash-boundary', result == 1)
    check('native-member-save-programs-entire-parent-not-one-member',
          f.operations == [dict(kind='erase', address=hex(FLASH), bytes=FLASH_BYTES),
                           dict(kind='program', address=hex(FLASH), bytes=parent[3]),
                           dict(kind='program', address=hex(FLASH + parent[3]), bytes=4)]
          and flash[:parent[3]] == payload
          and flash[parent[3]:] == bytes(f.u.mem_read(0xA1880698, 4)))
    observations['save_operations'] = f.operations.copy()
    del f
    gc.collect()
    # Fresh emulator instance: no carried-over RAM. Native loading must copy
    # the stored parent to the new workspace before the member becomes visible.
    f = SettingsFixture(raw, flash=flash)
    f.call(0x10091CAC)
    restored_parent, restored_member = f.record(0x11), f.record(0x13)
    result = f.call(0x101AE952, 0x13)
    check('native-member-load-in-fresh-instance-reports-success', result == 1)
    check('native-member-load-restores-entire-parent-payload',
          bytes(f.u.mem_read(restored_parent[2], parent[3])) == payload)
    check('native-member-view-restores-synthetic-member-data',
          bytes(f.u.mem_read(restored_member[2], 0x100)) == payload[0xA100:0xA200])
    check('native-load-does-not-erase-or-program', not f.operations)
    del f
    gc.collect()
    for failure in ('erase', 'program'):
        f = SettingsFixture(raw, failure=failure)
        f.call(0x10091CAC)
        parent, member = f.record(0x11), f.record(0x13)
        f.u.mem_write(parent[2], payload)
        result = f.call(0x101AEA60, 0x13, member[2], member[3])
        check(f'native-save-{failure}-failure-is-not-success', result == 0)
        check(f'native-save-{failure}-retries-are-bounded',
              len(f.operations) <= 13 and 1 <= len(f.operations))
        observations[failure + '_failure_operations'] = f.operations.copy()
        del f
        gc.collect()
    journal_checks, journal_observations = audit_journal(raw)
    checks.extend(journal_checks)
    observations['main_settings_journal'] = journal_observations
    return dict(schema=1, stock_main_sha256=STOCK_SHA, checks=checks,
        observations=observations, all_passed=all(c['passed'] for c in checks),
        scope='Original instructions with synthetic RAM and supplied in-memory flash boundaries; logical-record and main-settings journal round trips in fresh Unicorn instances. Extra record and migration descriptors are supplied test inputs, not installed firmware hooks. No grid-choice persistence implementation, complete camera shutdown/reboot, flash controller, endurance, update acceptance or recovery validation.',
        supplied_boundaries=['workspace allocation', 'model token', 'OS locks/context',
                             'flash erase/program into isolated Unicorn memory'],
        camera_access=False, card_access=False, firmware_export=False)


def audit_journal(raw):
    checks, observations = [], {}
    def check(name, passed):
        checks.append(dict(name=name, passed=bool(passed)))
    def fixture(journal=None, extra=False, failure=None):
        f = SettingsFixture(raw, journal=journal, failure=failure)
        f.call(0x10091CAC)
        f.call(0x100709CA)
        args, descriptor = f.schema(extra)
        return f, args, descriptor
    def native_records(f):
        return [bytes(f.u.mem_read(f.word(SCHEMA + index * 12),
                                  f.word(SCHEMA + index * 12 + 4))) for index in range(89)]
    images = {}
    for extra in (False, True):
        label = 'extended' if extra else 'stock'
        f, args, descriptor = fixture(extra=extra)
        f.call(0x100704FA, 0x102D, 1, MEM + 0x3000)
        before = native_records(f)
        result = f.call(0x101AEC44, 0x0F, args, descriptor)
        check(label + '-journal-save-returns-one', result == 1)
        check(label + '-journal-writes-stay-in-native-journal-regions',
              bool(f.operations) and all(any(base <= int(op['address'], 16)
                  and int(op['address'], 16) + op['bytes'] <= base + JOURNAL_BYTES
                  for base in JOURNAL_BANKS) for op in f.operations))
        images[extra] = f.journal()
        observations[label + '_save'] = dict(operations=len(f.operations),
            erased_regions=[op for op in f.operations if op['kind'] == 'erase'],
            last_programs=f.operations[-2:])
        del f
        gc.collect()
        f, args, descriptor = fixture(images[extra], extra)
        if extra:
            f.u.mem_write(MEM + 0x2000, bytes(16))
        result = f.call(0x101AEBAE, 0x0F, args, descriptor)
        check(label + '-journal-fresh-instance-load-succeeds', result == 1)
        check(label + '-journal-restores-all-89-native-records', native_records(f) == before)
        check(label + '-journal-restores-native-grid-enabled', f.word(GRID_VALUE) == 1)
        if extra:
            check('extended-journal-restores-supplied-custom-record',
                  bytes(f.u.mem_read(MEM + 0x2000, 16)) == struct.pack('<4I', 0x47524431, 1, 0, 0))
        check(label + '-journal-load-does-not-write', not f.operations)
        del f
        gc.collect()
    for saved_extra, loading_extra in ((False, True), (True, False)):
        f, args, descriptor = fixture(images[saved_extra], loading_extra)
        result = f.call(0x101AEBAE, 0x0F, args, descriptor)
        name = 'old-settings-with-added-record' if loading_extra else 'extended-settings-with-stock-loader'
        check(name + '-is-rejected', result == 0)
        check(name + '-does-not-program-flash', not f.operations)
        observations[name] = dict(native_result=result,
            consequence='Caller 0x10117594 passes failure to 0x1007099A, which can reset native settings. Bare schema replacement lacks compatibility; explicit conversions are tested separately below.')
        del f
        gc.collect()
    # Retry the original schema before Nikon's startup reset-on-failure path.
    # This is a supplied-descriptor experiment, not an installed migration hook.
    f, args, descriptor = fixture(images[False], True)
    first = f.call(0x101AEBAE, 0x0F, args, descriptor)
    args, original_descriptor = f.schema(False)
    fallback = f.call(0x101AEBAE, 0x0F, args, original_descriptor)
    before = native_records(f)
    args, descriptor = f.schema(True)
    saved = f.call(0x101AEC44, 0x0F, args, descriptor)
    migrated = f.journal()
    check('supplied-migration-falls-back-before-native-startup-reset', first == 0 and fallback == 1)
    check('supplied-migration-keeps-native-grid-enabled', f.word(GRID_VALUE) == 1)
    check('supplied-migration-save-reports-one', saved == 1)
    del f
    gc.collect()
    f, args, descriptor = fixture(migrated, True)
    f.u.mem_write(MEM + 0x2000, bytes(16))
    loaded = f.call(0x101AEBAE, 0x0F, args, descriptor)
    check('supplied-migration-reloads-native-and-custom-records', loaded == 1
          and native_records(f) == before
          and bytes(f.u.mem_read(MEM + 0x2000, 16)) == struct.pack('<4I', 0x47524431, 1, 0, 0))
    observations['supplied_migration'] = dict(extended_load=first, original_schema_retry=fallback,
        extended_save=saved, fresh_extended_reload=loaded,
        installed_firmware_hook=False, stock_without_conversion_rejected=True)
    # Convert a loaded extended journal back to the original schema, then ask
    # a new stock-schema instance to select/load the resulting flash banks.
    # Merely booting stock against the extended image was rejected above.
    args, descriptor = f.schema(False)
    rollback_saved = f.call(0x101AEC44, 0x0F, args, descriptor)
    rollback_image = f.journal()
    del f
    gc.collect()
    f, args, descriptor = fixture(rollback_image)
    rollback_loaded = f.call(0x101AEBAE, 0x0F, args, descriptor)
    check('supplied-rollback-writes-original-schema', rollback_saved == 1)
    check('supplied-rollback-loads-in-fresh-stock-schema-instance', rollback_loaded == 1)
    check('supplied-rollback-preserves-all-89-native-records', native_records(f) == before)
    observations['supplied_rollback_conversion'] = dict(save_result=rollback_saved,
        stock_schema_reload=rollback_loaded,
        native_records_preserved=native_records(f) == before,
        installed_firmware_hook=False,
        caution='Explicit conversion must run while extended-schema code can still read the store. This is not camera updater/recovery validation.')
    del f
    gc.collect()
    f, args, descriptor = fixture(failure='program')
    result = f.call(0x101AEC44, 0x0F, args, descriptor)
    check('journal-wrapper-reports-one-despite-program-failure', result == 1)
    check('journal-first-write-failure-has-bounded-low-level-retries', len(f.operations) == 4)
    failed_image = f.journal()
    observations['program_failure'] = dict(native_wrapper_result=result,
        operations=f.operations.copy(),
        caution='0x10091974 discards 0x10091848 result; return status alone cannot prove durability.')
    del f
    gc.collect()
    f, args, descriptor = fixture(failed_image)
    check('journal-failed-save-does-not-load-as-valid', f.call(0x101AEBAE, 0x0F, args, descriptor) == 0)
    del f
    gc.collect()
    observations.update(logical_id='0x0F', native_records=89,
        journal_banks=[hex(v) for v in JOURNAL_BANKS], bytes_per_bank=JOURNAL_BYTES,
        grid_record=49, grid_record_bytes=0x240, grid_offset_within_record='0xB4',
        added_record_is_supplied_test_schema_only=True)
    return checks, observations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.stock.read_bytes())
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(checks=len(result['checks']), all_passed=result['all_passed'])))
    if not result['all_passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
