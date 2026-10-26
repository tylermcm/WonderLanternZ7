"""Execute installed grid journal hooks against isolated synthetic flash banks.

Original Z7 journal/default/property instructions and appended ARM hooks execute.
OS, allocation and flash-controller boundaries are supplied. Fresh instances
carry only flash bytes. This is not physical-camera or full QEMU boot evidence.
"""
import argparse
import gc
import json
from pathlib import Path
import struct
import zlib

from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_SP, UC_ARM_REG_PC, UC_ARM_REG_R4
from trace_settings_storage import SettingsFixture, MEM, HEADER, SCHEMA, GRID_VALUE, JOURNAL_BANKS, JOURNAL_BYTES
from audit_splash_image import STACK, STOP
from build_grid_firmware import validate_candidate
from z30_extensions.features import settings_z7 as s
from z30_extensions.features.grid_z7 import HEAP_SITE, CURSOR

ALLOC = MEM + 0x80000


class PowerCut(Exception):
    pass


def damage_record(u):
    needle = struct.pack('<3I', 89, 16, s.RECORD_MAGIC)
    found = []
    for base in JOURNAL_BANKS:
        data = bytes(u.mem_read(base, JOURNAL_BYTES))
        position = data.find(needle)
        while position >= 0:
            found.append(base + position + 8 + 12)
            position = data.find(needle, position + 1)
    if not found:
        raise AssertionError('No extension record for CRC fault injection')
    for address in found:
        u.mem_write(address, bytes([u.mem_read(address, 1)[0] ^ 1]))


class PersistentGrid(SettingsFixture):
    def __init__(self, image, report, journal=None, failure=None, allocation_failure=False):
        super().__init__(image, journal=journal, failure=failure)
        self.u.mem_map(s.STATE, 4096)
        self.sf = {key: int(v, 16) for key, v in report['features']['settings']['functions'].items()}
        self.gf = {key: int(v, 16) for key, v in report['features']['grid']['functions'].items()}
        self.live_allocation, self.allocation_failure = False, allocation_failure
        self.freed, self.property_writes = 0, []
        self.change_during_free = False
        self.corrupt_on_verify, self.cut_after, self.program_count = False, None, 0
        for address in (0x1016FE38, 0x1016FE4A, 0x101E3BB8, 0x104065B0, 0x101F447A):
            self.u.hook_add(UC_HOOK_CODE, self.extra_hook, begin=address, end=address)
        self.u.hook_add(UC_HOOK_CODE, self.verification_hook, begin=self.sf['original_load'], end=self.sf['original_load'])

    def hook(self, u, address, size, context):
        super().hook(u, address, size, context)
        if address == 0x101AE3F0:
            self.program_count += 1
            if self.cut_after == self.program_count:
                raise PowerCut('Stopped immediately after a supplied program boundary')

    def verification_hook(self, u, address, size, context):
        if self.corrupt_on_verify and u.reg_read(UC_ARM_REG_R1) == ALLOC + 40:
            damage_record(u)
            self.corrupt_on_verify = False

    def extra_hook(self, u, address, size, context):
        r0, r1 = u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)
        if address == 0x1016FE38:
            if r0 != s.ALLOCATION or r1 != 0 or self.live_allocation:
                raise AssertionError('Unexpected persistence allocation')
            if self.allocation_failure:
                self.ret(0)
            else:
                self.live_allocation = True
                u.mem_write(ALLOC - 16, bytes([0x5A]) * (s.ALLOCATION + 32))
                self.ret(ALLOC)
        elif address == 0x1016FE4A:
            if r0 != ALLOC or not self.live_allocation:
                raise AssertionError('Invalid persistence free')
            if bytes(u.mem_read(ALLOC - 16, 16)) != bytes([0x5A]) * 16 or bytes(u.mem_read(ALLOC + s.ALLOCATION, 16)) != bytes([0x5A]) * 16:
                raise AssertionError('Persistence allocation canary changed')
            self.live_allocation = False
            self.freed += 1
            if self.change_during_free:
                u.mem_write(s.STATE + 4, struct.pack('<I', 1 - self.word(s.STATE + 4)))
                u.mem_write(s.STATE + 32, struct.pack('<I', self.word(s.STATE + 32) + 1))
            self.ret(0)
        elif address == 0x104065B0:
            if r0 != 0x102D or r1 not in (0, 1):
                raise AssertionError('Native visibility property ceased to be boolean')
            self.property_writes.append((r0, r1))
            u.mem_write(GRID_VALUE, struct.pack('<I', r1))
            self.ret(1)
        elif address == 0x101F447A:
            if r0 not in (0x11, 0x28):
                raise AssertionError('Unexpected secondary startup dataset')
            self.ret(0)
        else:
            self.ret(r0)

    def cold(self):
        self.u.mem_write(STACK, struct.pack('<2I', 0x12345678, STOP | 1))
        self.u.reg_write(UC_ARM_REG_SP, STACK)
        self.u.emu_start(HEAP_SITE | 1, STOP, count=20000)
        if (self.u.reg_read(UC_ARM_REG_PC) != STOP or self.u.reg_read(UC_ARM_REG_SP) != STACK + 8
                or self.u.reg_read(UC_ARM_REG_R4) != 0x12345678 or self.word(CURSOR) != s.STATE + s.STATE_BYTES):
            raise AssertionError('Cold reservation ABI failed')

    def initialize(self):
        self.cold()
        self.call(0x10091CAC)
        self.call(0x100709CA)

    def load(self):
        args, descriptor = self.schema()
        return self.call(s.LOAD, 15, args, descriptor)

    def native_payloads(self):
        return [bytes(self.u.mem_read(self.word(SCHEMA + i * 12), self.word(SCHEMA + i * 12 + 4))) for i in range(89)]


def audit(stock, image, report):
    checks, scenarios = [], []
    def check(name, passed):
        checks.append(dict(name=name, passed=bool(passed)))
    f = PersistentGrid(image, report)
    f.initialize()
    check('cold-reserves-owned-table-without-overlap', f.word(s.OWN_TABLE + 89 * 12) == s.RECORD
          and f.word(s.OWN_TABLE + 89 * 12 + 4) == 16)
    for data in (b'', b'123456789', struct.pack('<3I', s.RECORD_MAGIC, 1, 1)):
        f.u.mem_write(MEM + 0x5000, data)
        check('compiled-crc-' + str(len(data)), f.call(f.sf['crc'], MEM + 0x5000, len(data)) == zlib.crc32(data))
    f.call(f.gf['thirds'])
    check('selection-only-marks-dirty-and-keeps-native-boolean', f.word(s.STATE + 4) == 1
          and f.word(s.STATE + 8) == 1 and f.property_writes == [(0x102D, 1)] and not f.operations)
    before = f.native_payloads()
    descriptor_before = bytes(f.u.mem_read(0xA20A6CB0, 16))
    logical_before = f.record(15)[2:4]
    saved = f.call(0x1011764A, 1)
    check('normal-native-save-caller-runs-verified-hook', saved == 1 and f.word(s.STATE + 12) == 5)
    check('verified-save-clears-dirty-and-unlocks', f.word(s.STATE + 8) == 0 and f.word(s.STATE + 40) == 0)
    check('verification-does-not-change-any-native-live-payload', f.native_payloads() == before)
    check('verification-restores-native-global-descriptor-and-logical-view',
          bytes(f.u.mem_read(0xA20A6CB0, 16)) == descriptor_before and f.record(15)[2:4] == logical_before)
    check('verification-frees-exact-allocation', f.freed == 1 and not f.live_allocation)
    journal = f.journal()
    scenarios.append(dict(name='save-thirds', result=saved, operations=len(f.operations)))
    del f
    gc.collect()
    f = PersistentGrid(image, report, journal)
    f.initialize()
    check('fresh-ram-starts-fourths', f.word(s.STATE + 4) == 0)
    loaded = f.load()
    check('installed-load-hook-restores-thirds-from-flash-only', loaded == 1 and f.word(s.STATE + 4) == 1
          and f.word(s.STATE + 12) == 1 and f.word(s.STATE + 8) == 0)
    check('cold-load-restores-all-native-payloads', f.native_payloads() == before)
    check('startup-load-does-not-write', not f.operations)
    f.call(f.gf['fourths'])
    saved = f.call(0x1011764A, 1)
    check('second-choice-save-is-verified', saved == 1 and f.word(s.STATE + 8) == 0)
    fourths = f.journal()
    del f
    gc.collect()
    f = PersistentGrid(image, report, fourths)
    f.initialize()
    check('second-fresh-instance-restores-fourths', f.load() == 1 and f.word(s.STATE + 4) == 0)
    f.call(f.gf['thirds'])
    f.change_during_free = True
    check('changed-generation-retains-dirty-despite-verified-snapshot', f.call(0x1011764A, 1) == 1
          and f.word(s.STATE + 8) == 1 and f.word(s.STATE + 4) == 0)
    f.change_during_free = False
    rollback = f.call(f.sf['rollback'])
    check('compiled-original-format-conversion-verifies', rollback == 1 and f.word(s.STATE + 36) == 1
          and f.word(s.STATE + 12) == 6)
    rollback_image, rollback_payloads = f.journal(), f.native_payloads()
    del f
    gc.collect()
    original = SettingsFixture(stock, journal=rollback_image)
    original.call(0x10091CAC)
    original.call(0x100709CA)
    args, descriptor = original.schema()
    check('converted-journal-loads-with-unmodified-stock-code', original.call(0x101AEBAE, 15, args, descriptor) == 1)
    check('conversion-preserves-every-native-record', [bytes(original.u.mem_read(original.word(SCHEMA + i * 12), original.word(SCHEMA + i * 12 + 4))) for i in range(89)] == rollback_payloads)
    del original
    gc.collect()
    f = PersistentGrid(image, report, rollback_image)
    f.initialize()
    check('modified-reboot-keeps-converted-stock-format', f.load() == 1
          and f.word(s.STATE + 36) == 1 and f.word(s.STATE + 4) == 0
          and f.word(s.STATE + 8) == 0 and not f.operations)
    check('normal-save-after-conversion-keeps-stock-schema', f.call(0x1011764A, 1) == 1
          and f.word(s.STATE + 36) == 1)
    again = f.journal()
    f.call(f.gf['fourths'])
    check('explicit-same-choice-reenables-persistence-after-conversion',
          f.word(s.STATE + 36) == 0 and f.word(s.STATE + 8) == 1)
    del f
    gc.collect()
    original = SettingsFixture(stock, journal=again)
    original.call(0x10091CAC)
    original.call(0x100709CA)
    args, descriptor = original.schema()
    check('stock-loader-still-accepts-after-modified-reboot-and-save',
          original.call(s.LOAD, 15, args, descriptor) == 1)
    del original
    gc.collect()
    # The actual native startup caller reaches the compiled descriptor/load
    # hooks before proceeding to its original default/migration helper.
    f = PersistentGrid(image, report, journal)
    f.initialize()
    f.call(0x10117594)
    check('native-startup-caller-restores-choice-before-return', f.word(s.STATE + 4) == 1
          and f.word(s.STATE + 44) == 1 and f.word(s.STATE + 12) == 1)
    f.call(0x100709CA)
    check('native-default-reset-also-resets-extension', f.word(s.STATE + 4) == 0
          and f.word(s.STATE + 8) == 1)
    del f
    gc.collect()
    f = PersistentGrid(image, report, journal)
    f.initialize()
    damage_record(f.u)
    check('bad-extension-crc-defaults-without-failing-native-load', f.load() == 1
          and f.word(s.STATE + 4) == 0 and f.word(s.STATE + 12) == 3 and f.word(s.STATE + 8) == 1)
    check('bad-extension-crc-preserves-native-settings', f.native_payloads() == before and not f.operations)
    del f
    gc.collect()
    f = PersistentGrid(image, report)
    f.initialize()
    f.call(f.gf['thirds'])
    f.corrupt_on_verify = True
    unchanged = f.native_payloads()
    check('readback-corruption-is-rejected', f.call(0x1011764A, 1) == 0
          and f.word(s.STATE + 8) == 1 and f.word(s.STATE + 12) == 4)
    check('failed-readback-never-overwrites-live-settings', f.native_payloads() == unchanged
          and not f.live_allocation and f.word(s.STATE + 40) == 0)
    del f
    gc.collect()
    # Produce a genuine stock-format starting store, then exercise installed
    # migration and interruption while adding the extension for the first time.
    original = SettingsFixture(stock)
    original.call(0x10091CAC)
    original.call(0x100709CA)
    original.u.mem_write(GRID_VALUE, struct.pack('<I', 1))
    args, descriptor = original.schema()
    original.call(0x101AEC44, 15, args, descriptor)
    stock_journal = original.journal()
    del original
    gc.collect()
    f = PersistentGrid(image, report, stock_journal)
    f.initialize()
    check('installed-migration-loads-stock-without-resetting-native', f.load() == 1
          and f.word(GRID_VALUE) == 1 and f.word(s.STATE + 12) == 6
          and f.word(s.STATE + 36) == 1 and f.word(s.STATE + 8) == 0)
    migration_native = f.native_payloads()
    f.call(f.gf['thirds'])
    check('installed-migration-first-save-is-verified', f.call(0x1011764A, 1) == 1)
    migrated = f.journal()
    total_programs = f.program_count
    del f
    gc.collect()
    f = PersistentGrid(image, report, migrated)
    f.initialize()
    check('installed-migration-survives-fresh-instance', f.load() == 1
          and f.word(s.STATE + 4) == 1 and f.native_payloads() == migration_native)
    del f
    gc.collect()
    for cut in (1, 2, 3, total_programs - 2, total_programs - 1, total_programs):
        f = PersistentGrid(image, report, stock_journal)
        f.initialize()
        f.load()
        f.call(f.gf['thirds'])
        f.cut_after = cut
        interrupted = False
        try:
            f.call(0x1011764A, 1)
        except PowerCut:
            interrupted = True
        interrupted_image = f.journal()
        check(f'power-cut-{cut}-reaches-program-boundary', interrupted)
        del f
        gc.collect()
        f = PersistentGrid(image, report, interrupted_image)
        f.initialize()
        loaded = f.load()
        check(f'power-cut-{cut}-preserves-native-settings-in-fresh-instance', loaded == 1
              and f.native_payloads() == migration_native)
        check(f'power-cut-{cut}-choice-is-valid-old-or-committed', f.word(s.STATE + 4) in (0, 1)
              and (cut != total_programs or f.word(s.STATE + 4) == 1))
        del f
        gc.collect()
    for name, failure, alloc_fail in (('program', 'program', False), ('allocation', None, True)):
        f = PersistentGrid(image, report, failure=failure, allocation_failure=alloc_fail)
        f.initialize()
        f.call(f.gf['thirds'])
        check(name + '-failure-is-not-verified-success', f.call(0x1011764A, 1) == 0)
        check(name + '-failure-retains-dirty-unlocks-and-frees', f.word(s.STATE + 8) == 1
              and f.word(s.STATE + 40) == 0 and not f.live_allocation)
        if alloc_fail:
            check('allocation-failure-never-starts-flash-write', not f.operations)
        del f
        gc.collect()
    f = PersistentGrid(image, report, journal)
    f.initialize()
    f.load()
    f.u.mem_write(s.STATE + 40, struct.pack('<I', 1))
    check('busy-save-does-not-write-or-release-another-owner', f.call(0x1011764A, 1) == 0
          and not f.operations and f.word(s.STATE + 40) == 1)
    del f
    gc.collect()
    # Damage must not silently route a native-format save into an extended
    # journal. Nor may a corrupt destination table become a native load target.
    for name, address, value in (
        ('missing-magic', s.STATE, 0), ('invalid-mode', s.STATE + 36, 2),
        ('native-pointer', s.OWN_TABLE + 12, 0xDEADBEEF),
        ('native-length', s.OWN_TABLE + 16, 0xFFFFFFFF),
        ('owned-pointer', s.OWN_TABLE + 89 * 12, s.STATE),
        ('owned-length', s.OWN_TABLE + 89 * 12 + 4, 32),
    ):
        f = PersistentGrid(image, report, journal)
        f.initialize()
        f.u.mem_write(address, struct.pack('<I', value))
        state_before = bytes(f.u.mem_read(s.STATE, s.STATE_BYTES))
        live_before = f.native_payloads()
        check(name + '-load-rejects-without-changing-live-settings', f.load() == 0
              and f.native_payloads() == live_before)
        check(name + '-save-rejects-without-writing-or-touching-workspace',
              f.call(0x1011764A, 1) == 0 and not f.operations
              and bytes(f.u.mem_read(s.STATE, s.STATE_BYTES)) == state_before)
        del f
        gc.collect()
    for offset, value in ((0, 89), (4, SCHEMA), (8, 8), (12, HEADER)):
        f = PersistentGrid(image, report, journal)
        f.initialize()
        f.load()
        args, descriptor = f.schema()
        f.u.mem_write(descriptor + offset, struct.pack('<I', value))
        check(f'save-rejects-corrupt-descriptor-field-{offset}',
              f.call(s.SAVE, 15, args, descriptor) == 0 and not f.operations
              and not f.live_allocation and f.word(s.STATE + 40) == 0)
        del f
        gc.collect()
    f = PersistentGrid(image, report, journal, failure='program')
    f.initialize()
    f.load()
    check('failed-stock-conversion-restores-extended-mode', f.call(f.sf['rollback']) == 0
          and f.word(s.STATE + 36) == 0 and f.word(s.STATE + 8) == 1
          and f.word(s.STATE + 40) == 0 and not f.live_allocation)
    del f
    gc.collect()
    return dict(schema=1, checks=checks, scenarios=scenarios,
        main_payload_sha256=report['main_payload_sha256'], all_passed=all(c['passed'] for c in checks),
        scope=__doc__.strip(), camera_access=False, card_access=False,
        supplied_boundaries=['OS and model token', 'workspace and checked scratch allocation',
                             'flash erase/program in Unicorn memory', 'native UI visibility setter',
                             'secondary startup dataset reads'],
        full_qemu_cold_boot=False, physical_durability=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--container', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    main_path, report_path = (args.build / ('grid.emulator.' + ext) for ext in ('main.bin', 'json'))
    validate_candidate(main_path, report_path, args.container)
    report = json.loads(report_path.read_text())
    if 'settings' not in report['features']:
        parser.error('Requires persistent emulator candidate')
    result = audit(args.stock.read_bytes(), main_path.read_bytes(), report)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(checks=len(result['checks']), all_passed=result['all_passed'])))
    if not result['all_passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
