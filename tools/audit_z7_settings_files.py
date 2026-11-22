"""Execute original-Z7 settings file wrappers, cache lines and journal recovery.

SPDX-License-Identifier: MIT. Filesystem dispatcher, sector buffers and selected
path-resolution services are supplied. No card, durable flush or complete FAT
implementation is claimed. Original directory-end and open-mode paths execute.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP
from audit_splash_image import MEM, STACK, STOCK_SHA
from audit_z7_module_host import HostFixture
from audit_z7_settings_storage import DEFAULTS, record
from build_z7_module_host import ROOT, STATE

PATHS = ('A:\\Z7CFG0.DAT', 'A:\\Z7CFG1.DAT')
NOT_FOUND, ERROR = 0x80000010, 0x80000041


class FilesFixture(HostFixture):
    file_paths = PATHS
    files_enabled = False
    allow_module_loader = False
    derivation = None

    def hook(self, u, address, size, context):
        if self.derivation == 'directory' and address == 0x10255b28:
            self.sector_reads.append((u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)))
            u.mem_write(u.reg_read(UC_ARM_REG_R2), struct.pack('<I', MEM + 0x30000))
            self.ret(self.sector_result)
            return
        if self.derivation == 'directory' and address == 0x10264e0a:
            self.ret(0)  # Supplied nonmatching name for the exhausted-root case.
            return
        if self.derivation == 'open':
            if address == 0x10276278:
                sp = u.reg_read(UC_ARM_REG_SP)
                fifth, sixth = struct.unpack('<2I', u.mem_read(sp, 8))
                for pointer, value in ((u.reg_read(UC_ARM_REG_R2), MEM + 0x100),
                                       (u.reg_read(UC_ARM_REG_R3), 0), (fifth, 5), (sixth, MEM + 0x2000)):
                    u.mem_write(pointer, struct.pack('<I', value))
                self.ret(0)
                return
            if address in (0x10277488, 0x102776fa):
                self.lookup_calls.append(address)
                self.ret(self.lookup_result)
                return
            if address == 0x10263dd0:
                self.truncations.append(tuple(u.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)))
                self.ret(0)
                return
        if self.files_enabled:
            if address in (0x101e9f38, 0x101e9f76):
                event = ('clean' if address == 0x101e9f38 else 'invalidate', u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1))
                self.cache_operations.append(event)
                self.file_events.append(event)
            if address in (0x101e9f5c, 0x101e9f9a):
                self.file_cache_lines.append(('clean' if address == 0x101e9f5c else 'invalidate', u.reg_read(UC_ARM_REG_R2)))
            if address == 0x1027beae:
                p = u.reg_read(UC_ARM_REG_R0)
                words = struct.unpack('<42I', u.mem_read(p, 168))
                op = bytes(u.mem_read(p + 0x9c, 1))[0]
                if self.allow_module_loader and op == 16:
                    super().hook(u, address, size, context)
                    return
                result = 0
                if op in (5, 13):
                    path = self.cstring(words[4])
                    if path not in self.file_paths:
                        if self.allow_module_loader and op == 5 and path == 'A:\\Z7APP.BIN':
                            super().hook(u, address, size, context)
                            return
                        raise AssertionError('Adapter accessed an unowned file')
                    self.allow_module_loader = False
                    if op == 5 and words[5:7] != (0, 0):
                        raise AssertionError('Settings read must be read-only')
                    if op == 13 and words[6] != 0:
                        raise AssertionError('Unexpected native create mode')
                    self.file_events.append(('open' if op == 5 else 'create', path))
                    result = self.faults.get('open' if op == 5 else 'create', 0)
                    if not result:
                        if op == 5 and path not in self.files:
                            result = NOT_FOUND
                        else:
                            result = self.next_fd
                            self.next_fd += 1
                            self.handles[result] = [path, 0, op == 13]
                            if op == 13:
                                self.files[path] = b''
                elif op in (8, 9):
                    fd, pointer, capacity, actual = words[7], words[10], words[11], words[12]
                    if fd not in self.handles and self.allow_module_loader and op == 8:
                        super().hook(u, address, size, context)
                        return
                    if fd not in self.handles or pointer % 64 or capacity != (81 if op == 8 else 80):
                        raise AssertionError('Wrong native direct-buffer signature')
                    path, position, writable = self.handles[fd]
                    if bool(op == 9) != writable:
                        raise AssertionError('Wrong handle permissions')
                    if op == 8:
                        data = self.files[path][position:position + capacity]
                        if data:
                            u.mem_write(pointer, data)
                        count = len(data)
                        result = self.faults.get('read', 0)
                    else:
                        count = self.write_prefix
                        self.files[path] += bytes(u.mem_read(pointer, count))
                        result = self.faults.get('write', 0)
                    self.handles[fd][1] += count
                    count = self.faults.get('actual', count)
                    u.mem_write(actual, struct.pack('<I', count))
                    self.file_events.append(('read' if op == 8 else 'write', path, capacity, count, pointer))
                elif op == 6:
                    fd = words[7]
                    if fd not in self.handles:
                        if self.allow_module_loader:
                            super().hook(u, address, size, context)
                            return
                        raise AssertionError('Stale or duplicate close')
                    self.file_events.append(('close', fd))
                    result = self.faults.get('close', 0)
                    if not result:
                        del self.handles[fd]
                else:
                    raise AssertionError('Unexpected settings filesystem opcode ' + hex(op))
                self.ret(result)
                return
        super().hook(u, address, size, context)


def audit(raw, host, stock, packet, module):
    if hashlib.sha256(stock).hexdigest() != STOCK_SHA or hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Exact original stock/host/module required')
    for a, b in ((0x10255d16, 0x10255e26), (0x10277f78, 0x1027812a), (0x1027bfa2, 0x1027c102), (0x101e9f38, 0x101e9fb0)):
        if raw[a - 0x10020000:b - 0x10020000] != stock[a - 0x10020000:b - 0x10020000]:
            raise ValueError('Native contract code was modified')
    checks = []

    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good:
            raise AssertionError(name)

    # Bind the absent status to actual FAT root end/exhaustion instructions.
    d = FilesFixture(raw, host, b'')
    d.derivation, d.sector_result = 'directory', 0
    volume = 0xa29e0f80
    d.u.mem_write(volume + 0x40, struct.pack('<H', 16))
    d.u.mem_write(volume + 0x45, b'\1')
    d.u.mem_write(volume + 0x60, struct.pack('<I', 100))
    for name, first_bytes, sector_result, expected in (
        ('empty-directory', bytes(512), 0, NOT_FOUND),
        ('exhausted-directory', b''.join(b'\xe5' + bytes(31) for _ in range(16)), 0, NOT_FOUND),
        ('sector-read-error', bytes(512), ERROR, ERROR)):
        d.sector_reads, d.sector_result = [], sector_result
        d.u.mem_write(MEM + 0x30000, first_bytes)
        d.u.mem_write(STACK, bytes(8))  # Existing-entry search; optional descriptor null.
        check('original-root-' + name, d.call(0x10255d16, 0, MEM + 0x100, MEM + 0x400, 0) == expected and d.sector_reads == [(0, 100)])
    d.derivation = 'open'
    d.u.mem_write(volume + 0x3a, b'\1')
    for flags, missing in ((0, False), (0x301, False), (0, True)):
        d.u.mem_write(MEM + 0x2000, bytes(0x200))
        d.u.mem_write(MEM + 0x2000 + 0x38, struct.pack('<Q', 64))
        d.lookup_calls, d.truncations = [], []
        d.lookup_result = NOT_FOUND if missing else 0
        if flags:
            result = d.call(0x1023f146, MEM + 0x100, 0)
        else:
            result = d.call(0x10277f78, MEM + 0x100, 0, 0)
        if missing:
            check('original-read-open-propagates-directory-missing-status', result == NOT_FOUND and not d.truncations)
        elif flags:
            check('original-create-forces301-and-truncates-only-writable-descriptor', result == 5 and len(d.truncations) == 1 and bytes(d.u.mem_read(MEM + 0x2002, 1)) == b'\x26' and bytes(d.u.mem_read(MEM + 0x2038, 8)) == bytes(8))
        else:
            check('original-read-open-never-truncates', result == 5 and not d.truncations and bytes(d.u.mem_read(MEM + 0x2002, 1)) == b'\1' and bytes(d.u.mem_read(MEM + 0x2038, 8)) == struct.pack('<Q', 64))

    f = FilesFixture(raw, host, packet)
    check('native-files-diagnostic-loads', f.call(host['symbols']['z7_module_load_once'], STATE) == 8)
    base, symbols = f.words()[12], module['symbols']
    ptr = lambda name: base + symbols['z7_files_probe_' + name]
    call = lambda name, *args: f.call(base + symbols[name], *args)
    state = lambda: struct.unpack('<5I', f.u.mem_read(ptr('state'), 20))

    def reset(files=None, faults=None, prefix=80):
        # Fresh instruction-fixture boot state; never a production close retry.
        f.files_enabled = False
        f.u.mem_write(base + module['image_bytes'], bytes(module['bss_bytes']))
        call('z7_settings_files_init', ptr('state'))
        call('z7_settings_defaults', ptr('model'))
        f.u.mem_write(ptr('record'), b'\xa5' * 80)
        f.files, f.faults = dict(files or {}), dict(faults or {})
        f.handles, f.next_fd, f.write_prefix = {}, 0, prefix
        f.file_events, f.file_cache_lines, f.cache_operations = [], [], []
        f.files_enabled = True

    read = lambda slot: call('z7_settings_files_read', ptr('state'), slot, ptr('record'))
    write = lambda slot: call('z7_settings_files_write', ptr('state'), slot, ptr('record'))
    before = record(DEFAULTS, 5)
    edited = (3, 31, 15, 2, 4, 8, 255, 0, 5, 128)
    for slot in (0, 1):
        for length in (0, 1, 79, 80, 81, 160):
            data = (before * 2)[:length]
            reset({PATHS[slot]: data})
            check(f'slot{slot}-read-length{length}', read(slot) == (0 if length == 80 else 3) and bytes(f.u.mem_read(ptr('record'), 80)) == (data if length == 80 else b'\xa5' * 80) and not f.handles)
        reset()
        check(f'slot{slot}-confirmed-missing-has-no-close-or-read', read(slot) == 1 and f.file_events == [('open', PATHS[slot])] and state()[2] == NOT_FOUND)
        for operation in ('open', 'read', 'close'):
            reset({PATHS[slot]: before}, {operation: ERROR})
            check(f'slot{slot}-{operation}-error-does-not-publish-record', read(slot) == 2 and bytes(f.u.mem_read(ptr('record'), 80)) == b'\xa5' * 80 and state()[2] == ERROR)
            if operation == 'close':
                prior = list(f.file_events)
                check(f'slot{slot}-uncertain-read-close-parks-all-io', state()[1] == 0 and read(slot ^ 1) == 2 and write(slot) == 2 and f.file_events == prior)
                check(f'slot{slot}-reinit-cannot-discard-retained-fd', call('z7_settings_files_init', ptr('state')) == 0 and state()[1] == 0)
        for prefix in range(81):
            reset({PATHS[slot ^ 1]: before, PATHS[slot]: b'old'}, prefix=prefix)
            f.u.mem_write(ptr('record'), record(edited, 6))
            check(f'slot{slot}-write-prefix{prefix}', write(slot) == (0 if prefix == 80 else 2) and f.files[PATHS[slot ^ 1]] == before and f.files[PATHS[slot]] == record(edited, 6)[:prefix] and not f.handles)
        for operation in ('create', 'write', 'close'):
            reset({PATHS[slot ^ 1]: before}, {operation: ERROR})
            check(f'slot{slot}-{operation}-write-error-preserves-peer', write(slot) == 2 and f.files[PATHS[slot ^ 1]] == before and state()[2] == ERROR)
            if operation == 'close':
                prior = list(f.file_events)
                check(f'slot{slot}-uncertain-write-close-parks-all-io', write(slot ^ 1) == 2 and read(slot) == 2 and state()[1] == 0 and f.file_events == prior)
    reset({PATHS[0]: before})
    check('native-read-cache-helper-counts-and-order', read(0) == 0 and [x[0:1] + x[2:] for x in f.cache_operations] == [('invalidate', 81), ('invalidate', 81)] and [e[0] for e in f.file_events] == ['open', 'invalidate', 'read', 'invalidate', 'close'])
    buffer = f.cache_operations[0][1]
    check('native-read-invalidation-stays-in-owned192bytes', f.file_cache_lines == [('invalidate', buffer + offset) for _ in range(2) for offset in (0, 64, 128)])
    reset(); f.u.mem_write(ptr('record'), before)
    check('native-write-cleans-before-fs-write', write(0) == 0 and f.cache_operations[0][0::2] == ('clean', 80) and [e[0] for e in f.file_events] == ['create', 'clean', 'write', 'close'])
    buffer = f.cache_operations[0][1]
    check('native-write-clean-stays-in-owned192bytes', f.file_cache_lines == [('clean', buffer + offset) for offset in (0, 64, 128)])
    reset({PATHS[0]: before}, {'actual': 0xffffffff})
    check('impossible-read-count-fails-before-publication', read(0) == 2 and bytes(f.u.mem_read(ptr('record'), 80)) == b'\xa5' * 80)
    reset({PATHS[0]: before}); prior = list(f.file_events)
    check('bad-slot-and-null-record-perform-no-filesystem-operation', read(2) == 2 and write(2) == 2 and call('z7_settings_files_read', ptr('state'), 0, 0) == 2 and call('z7_settings_files_write', 0, 0, ptr('record')) == 2 and f.file_events == prior)

    # Actual compiled journal calls the original native wrappers on this model.
    reset()
    check('native-journal-missing-load-defaults', call('z7_files_probe_load') == 1 and f.files == {})
    check('native-journal-initial-save-readback', call('z7_files_probe_save') == 5 and f.files[PATHS[0]] == record(DEFAULTS, 0) and not f.handles)
    f.u.mem_write(ptr('model'), struct.pack('<10I', *edited))
    check('native-journal-second-save-retains-first-slot', call('z7_files_probe_save') == 5 and f.files[PATHS[0]] == record(DEFAULTS, 0) and f.files[PATHS[1]] == record(edited, 1))
    prior = dict(f.files)
    previous_events = len(f.file_events)
    check('native-journal-unchanged-save-does-not-create-or-write', call('z7_files_probe_save') == 6 and f.files == prior and not any(e[0] in ('create', 'write') for e in f.file_events[previous_events:]))
    reset({PATHS[0]: before}, prefix=31)
    f.u.mem_write(ptr('model'), struct.pack('<10I', *edited))
    check('native-journal-short-write-keeps-old-record', call('z7_files_probe_save') == 2 and f.files[PATHS[0]] == before)
    f.u.mem_write(ptr('model'), bytes(40))
    check('native-journal-reloads-peer-after-short-file', call('z7_files_probe_load') == 0 and bytes(f.u.mem_read(ptr('model'), 40)) == struct.pack('<10I', *DEFAULTS))
    reset({PATHS[0]: before}, {'open': ERROR})
    check('native-journal-card-error-never-creates-files', call('z7_files_probe_load') == 2 and call('z7_files_probe_save') == 2 and f.files == {PATHS[0]: before} and all(e[0] == 'open' for e in f.file_events))
    check('host-guards-preserved', f.words()[60:] == (0xa5a5a5a5,) * 4)
    return dict(passed=True, checks=checks, main_sha256=host['main_payload_sha256'], module_sha256=module['module_sha256'],
                original_missing_directory_status=hex(NOT_FOUND), original_directory_and_open_mode_instructions_execute=True,
                actual_native_file_wrappers_and_cache_line_instructions_execute=True, cache_line_bytes=64, staging_bytes=192,
                source_settings_payload_bytes=64, journal_record_bytes=80, read_capacity=81,
                supplied_boundaries=['Loader filesystem/kernel/heap', 'Settings filesystem dispatcher', 'FAT root sector buffer', 'Selected path-resolution, name-comparison and truncation services'],
                worker_menu_integration=False, physical_card_access=False, camera_access=False, physical_cache_or_durability_verified=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--module', type=Path, required=True)
    p.add_argument('--stock-main', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists():
        p.error('Choose a new private output')
    result = audit((a.build / 'module-host.emulator.main.bin').read_bytes(), json.loads((a.build / 'module-host.emulator.json').read_text(encoding='utf-8')),
                   a.stock_main.read_bytes(), (a.module / 'Z7APP.BIN').read_bytes(), json.loads((a.module / 'module.json').read_text(encoding='utf-8')))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__':
    main()
