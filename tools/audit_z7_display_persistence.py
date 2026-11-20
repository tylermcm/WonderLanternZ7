"""Execute full display initialization, native menu edits and worker saves.

SPDX-License-Identifier: MIT. Filesystem/kernel/UI boundaries are supplied.
Original file wrappers/cache instructions and compiled menu/worker code execute.
No complete native scheduler, physical card or shutdown-flush proof claimed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn import UC_HOOK_MEM_READ
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC
from audit_splash_image import MEM, STACK, STOP, ARGUMENTS, SAVED
from audit_z7_display_information import DisplayInformationFixture
from audit_z7_settings_files import FilesFixture, PATHS, ERROR
from audit_z7_settings_storage import DEFAULTS, record
from build_z7_module_host import ROOT, STATE


class PersistenceFixture(FilesFixture, DisplayInformationFixture):
    def __init__(self, raw, host, packet, files=None, faults=None):
        super().__init__(raw, host, packet)
        self.files, self.faults = dict(files or {}), dict(faults or {})
        self.handles, self.next_fd, self.write_prefix = {}, 0, 80
        self.file_events, self.file_cache_lines, self.cache_operations = [], [], []
        self.files_enabled, self.allow_module_loader = True, True
        self.startup_publication = []
        self.menu_labels = []
        self.pause_on_write = False
        self.paused_reason = None

    def hook(self, u, address, size, context):
        if address == 0x103fbb5c and 230 <= u.reg_read(UC_ARM_REG_R1) < 245:
            self.menu_labels.append((u.reg_read(UC_ARM_REG_R1), self.cstring(u.reg_read(UC_ARM_REG_R0))))
        if self.files_enabled and address == 0x1027beae:
            p = u.reg_read(UC_ARM_REG_R0)
            op = bytes(u.mem_read(p + 0x9c, 1))[0]
            if op == 9 and self.pause_on_write:
                self.pause_on_write = False
                self.paused_reason = 'write'
                u.emu_stop()
                return
            if op == 5:
                path = self.cstring(int.from_bytes(u.mem_read(p + 16, 4), 'little'))
                if path in PATHS and self.words()[19]:
                    self.startup_publication.append((self.words()[23], int.from_bytes(u.mem_read(0xa1833548, 4), 'little'), self.words()[50]))
        super().hook(u, address, size, context)


def audit(raw, host, packet, module, legacy):
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Exact host/module required')
    symbols, checks = module['symbols'], []

    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good:
            raise AssertionError(name)

    def load(files=None, faults=None, foreign=False):
        f = PersistenceFixture(raw, host, packet, files, faults)
        if foreign:
            f.u.mem_write(0xa1833548, struct.pack('<I', 0xdeadbeef))
        status = f.call(host['symbols']['z7_module_load_once'], STATE)
        f.base = f.words()[12]
        f.setword(40, status)
        return f, status

    def word(f, name):
        return int.from_bytes(f.u.mem_read(f.base + symbols[name], 4), 'little')

    def setword(f, name, value):
        f.u.mem_write(f.base + symbols[name], struct.pack('<I', value))

    def model(f):
        return tuple(struct.unpack('<10I', f.u.mem_read(f.base + symbols['z7_menu_settings'], 40)))

    def tick(f, count=1):
        labels = (list(f.labels), list(f.menu_labels))
        for _ in range(count):
            f.call(host['symbols']['z7_module_worker_tick'])
        check('worker-ticks-' + str(len(checks)) + '-never-touch-native-labels', (f.labels, f.menu_labels) == labels)

    def title(f, expected):
        before = list(f.file_events)
        f.call(f.base + symbols['sm_render'], 0xa1833548)
        text = [text for slot, text in f.menu_labels if slot == 230][-1]
        check('menu-title-' + str(len(checks)) + '-' + expected, text == expected and f.file_events == before)


    def action(f, row):
        f.u.mem_write(0xa1833548 + 22, struct.pack('<2H', row, 0))
        before = list(f.file_events)
        f.call(f.base + symbols['sm_activate'])
        check('menu-action-' + str(len(checks)) + '-performs-no-file-io', f.file_events == before)

    def paused_worker_edit(f, row, reason):
        # Explicit instruction-fixture task preemption. The actual native menu
        # adapter runs on a distinct emulated stack, then the worker resumes at
        # its saved PC/registers; no synthetic model/revision stores implement it.
        def enter(address, sp):
            for register in ARGUMENTS:
                f.u.reg_write(register, 0)
            guards = {register: 0x52520000 + i for i, register in enumerate(SAVED)}
            for register, value in guards.items():
                f.u.reg_write(register, value)
            f.u.reg_write(UC_ARM_REG_SP, sp)
            f.u.reg_write(UC_ARM_REG_LR, STOP | 1)
            f.u.emu_start(address | 1, STOP, timeout=30000000, count=10000000)
            return guards

        f.paused_reason = None
        guards = enter(host['symbols']['z7_module_worker_tick'], STACK)
        check('worker-preempted-at-' + reason, f.paused_reason == reason and f.u.reg_read(UC_ARM_REG_PC) != STOP and f.words()[51] == 1)
        worker_context = f.u.context_save()
        f.u.mem_write(0xa1833548 + 22, struct.pack('<2H', row, 0))
        before = list(f.file_events)
        menu_guards = enter(f.base + symbols['sm_activate'], STACK - 0x10000)
        check('preempting-menu-' + reason + '-uses-separate-stack-without-io', f.u.reg_read(UC_ARM_REG_PC) == STOP and f.u.reg_read(UC_ARM_REG_SP) == STACK - 0x10000 and all(f.u.reg_read(r) == v for r, v in menu_guards.items()) and f.file_events == before)
        check('menu-during-' + reason + '-shows-correct-save-state', [text for slot, text in f.menu_labels if slot == 230][-1].endswith(': Saving' if reason == 'write' else ': Unsaved'))
        f.u.context_restore(worker_context)
        f.u.emu_start(f.u.reg_read(UC_ARM_REG_PC) | 1, STOP, timeout=30000000, count=10000000)
        check('worker-resumes-after-' + reason + '-with-original-abi', f.u.reg_read(UC_ARM_REG_PC) == STOP and f.u.reg_read(UC_ARM_REG_SP) == STACK and all(f.u.reg_read(r) == v for r, v in guards.items()) and f.words()[51] == 0)

    configured = (3, 31, 15, 2, 4, 8, 255, 0, 5, 128)
    f, status = load({PATHS[0]: record(DEFAULTS, 5), PATHS[1]: record(configured, 6)})
    check('full-api44-profile-loads-all-existing-hooks-and-worker', status == 8 and f.words()[23] == f.words()[39] == f.words()[41] == f.words()[44] == f.words()[46] == f.words()[50] == 1)
    check('startup-loads-newest-model-before-first-menu-publication', model(f) == configured and f.startup_publication == [(0, 0, 1), (0, 0, 1)])
    check('startup-battery-flag-follows-loaded-preference', word(f, 'z7_battery_enabled') == 1 and word(f, 'z7_persistence_ready') == 1)
    check('startup-read-only-and-current-revision-clean', not any(e[0] in ('create', 'write') for e in f.file_events) and word(f, 'z7_settings_revision') == word(f, 'z7_persistence_saved_revision') == 0)
    title(f, 'Display: Saved')
    before = list(f.file_events); tick(f, 8)
    check('unchanged-startup-model-never-autosaves', f.file_events == before and not word(f, 'z7_persistence_attempts'))

    f, status = load()
    check('confirmed-missing-slots-enable-persistence-with-defaults', status == 8 and model(f) == DEFAULTS and word(f, 'z7_persistence_result') == 1 and word(f, 'z7_persistence_ready') == 1)
    title(f, 'Display: Defaults')
    action(f, 1)
    title(f, 'Standard: Defaults')
    check('submenu-navigation-does-not-dirty-settings', word(f, 'z7_settings_revision') == 0 and word(f, 'z7_settings_view') == 1)
    f.call(f.base + symbols['sm_back_event'])
    action(f, 0)
    check('native-menu-publishes-even-revision-and-master-change', model(f)[0] == 1 and word(f, 'z7_settings_revision') == 2)
    title(f, 'Display: Unsaved')
    before = list(f.file_events); tick(f, 3)
    check('three-quiet-observation-ticks-do-not-write', f.file_events == before and not word(f, 'z7_persistence_attempts'))
    tick(f)
    title(f, 'Display: Saved')
    saved_model = model(f)
    check('fourth-worker-tick-saves-menu-settings-through-native-files', word(f, 'z7_persistence_saves') == 1 and word(f, 'z7_persistence_attempts') == 1 and word(f, 'z7_persistence_saved_revision') == 2 and f.files == {PATHS[0]: record(saved_model, 0)})
    before = list(f.file_events); tick(f, 6)
    check('saved-menu-revision-does-not-write-again', f.file_events == before)
    action(f, 6)
    check('battery-menu-setting-publishes-model-and-renderer-flag', model(f)[0] == 3 and word(f, 'z7_battery_enabled') == 1 and word(f, 'z7_settings_revision') == 4)
    tick(f, 4)
    check('next-menu-save-alternates-and-keeps-previous-valid-slot', f.files[PATHS[0]] == record(saved_model, 0) and f.files[PATHS[1]] == record(model(f), 1) and word(f, 'z7_persistence_saves') == 2)
    persisted = dict(f.files)
    restarted, status = load(persisted)
    check('fresh-module-initializer-restores-native-menu-edit', status == 8 and model(restarted) == model(f) and word(restarted, 'z7_battery_enabled') == 1 and word(restarted, 'z7_persistence_saved_revision') == 0)

    f, status = load({PATHS[0]: record(DEFAULTS, 2)})
    action(f, 0)
    f.faults['create'] = ERROR
    tick(f, 4)
    check('save-error-remains-dirty-and-preserves-original', word(f, 'z7_persistence_errors') == 1 and word(f, 'z7_persistence_saved_revision') == 0 and f.files[PATHS[0]] == record(DEFAULTS, 2))
    title(f, 'Display: Save retry')
    before = list(f.file_events)
    del f.faults['create']; tick(f, 5)
    check('transient-save-error-backs-off-five-worker-ticks', f.file_events == before)
    tick(f)
    title(f, 'Display: Saved')
    check('retry-saves-current-dirty-settings', word(f, 'z7_persistence_saves') == 1 and word(f, 'z7_persistence_saved_revision') == 2 and f.files[PATHS[1]] == record(model(f), 3))
    action(f, 6)
    setword(f, 'z7_settings_revision', 5)
    before = list(f.file_events); tick(f, 4)
    check('odd-writer-revision-defers-bounded-snapshot-without-io', f.file_events == before and word(f, 'z7_persistence_attempts') == 2)
    setword(f, 'z7_settings_revision', 4)
    tick(f, 4)
    check('released-writer-revision-can-save-next-complete-model', word(f, 'z7_persistence_saved_revision') == 4 and f.files[PATHS[0]] == record(model(f), 4))

    for fault in ('open', 'read', 'close'):
        files = {PATHS[0]: record(configured, 1)}
        f, status = load(files, {fault: ERROR})
        check('startup-' + fault + '-failure-keeps-module-resident-with-defaults', status == 8 and f.base and model(f) == DEFAULTS and not word(f, 'z7_persistence_ready') and word(f, 'z7_persistence_result') == 2)
        title(f, 'Display: Restart to save')
        action(f, 0)
        title(f, 'Display: Restart to save')
        before = list(f.file_events); tick(f, 12)
        check('startup-' + fault + '-failure-never-overwrites-unread-settings', f.file_events == before and f.files == files and not word(f, 'z7_persistence_saved_revision'))
        if fault == 'close':
            check('startup-uncertain-close-retains-descriptor-and-module', word(f, 'z7_persistence_files') == 0x3146535a and int.from_bytes(f.u.mem_read(f.base + symbols['z7_persistence_files'] + 4, 4), 'little') == 0 and bool(f.live))
    f, status = load({PATHS[0]: record(DEFAULTS, 2)})
    action(f, 0)
    f.faults['close'] = ERROR
    tick(f, 4)
    title(f, 'Display: Restart to save')
    before = list(f.file_events); tick(f, 8)
    check('save-close-latch-blocks-retries-and-keeps-dirty-revision', f.file_events == before and word(f, 'z7_settings_revision') != word(f, 'z7_persistence_saved_revision'))
    g, status = load({PATHS[0]: record(configured, 0)})
    action(g, 1)  # Standard submenu; reset changes both components/information.
    pause_snapshot = [True]
    def interrupt_snapshot(u, access, address, size, value, context):
        if pause_snapshot[0]:
            pause_snapshot[0] = False
            g.paused_reason = 'snapshot'
            u.emu_stop()
    data_address = g.base + symbols['z7_menu_settings'] + 12
    memory_hook = g.u.hook_add(UC_HOOK_MEM_READ, interrupt_snapshot, begin=data_address, end=data_address + 3)
    paused_worker_edit(g, 6, 'snapshot')
    g.u.hook_del(memory_hook)
    check('snapshot-retry-observes-actual-menu-two-field-reset', model(g)[2] == 1 and model(g)[6] == 127 and word(g, 'z7_settings_revision') == word(g, 'persistence_observed') == 2 and not word(g, 'z7_persistence_attempts'))
    tick(g, 3)
    check('reset-save-contains-complete-new-snapshot', g.files[PATHS[1]] == record(model(g), 1) and word(g, 'z7_persistence_saved_revision') == 2)
    g.call(g.base + symbols['sm_back_event'])
    action(g, 0)
    older_snapshot = model(g)
    tick(g, 3)
    g.pause_on_write = True
    paused_worker_edit(g, 6, 'write')
    check('menu-edit-during-io-is-not-marked-saved-with-old-snapshot', word(g, 'z7_persistence_saved_revision') == 4 and word(g, 'z7_settings_revision') == 6 and model(g) != older_snapshot and g.files[PATHS[0]] == record(older_snapshot, 2))
    tick(g, 4)
    check('subsequent-worker-saves-newer-menu-edit-and-retains-prior', word(g, 'z7_persistence_saved_revision') == 6 and g.files[PATHS[1]] == record(model(g), 3) and g.files[PATHS[0]] == record(older_snapshot, 2))
    f, status = load(foreign=True)
    check('foreign-native-menu-prevents-init-and-all-settings-io', status == 7 and not f.live and not any(e[0] in ('open', 'create', 'write') for e in f.file_events) and bytes(f.u.mem_read(0xa1833548, 4)) == struct.pack('<I', 0xdeadbeef))
    old = json.loads((legacy / 'module-host.emulator.json').read_text(encoding='utf-8'))
    f = PersistenceFixture((legacy / 'module-host.emulator.main.bin').read_bytes(), old, packet)
    check('api40-host-rejects-persistence-before-menu-or-file-preparation', f.call(old['symbols']['z7_module_load_once'], STATE) == 7 and not f.live and not any(e[0] in ('open', 'create', 'write') for e in f.file_events) and bytes(f.u.mem_read(0xa1833548, 44)) == bytes(44))
    return dict(passed=True, checks=checks, main_sha256=host['main_payload_sha256'], module_sha256=module['module_sha256'],
                full_focal_other_histogram_information_profile=True, worker_api_bytes=44, startup_loading_implemented=True,
                actual_menu_edits_and_worker_saves_execute=True, atomic_snapshot_instructions_execute=True,
                actual_menu_preempts_worker_on_separate_emulated_stack=True,
                supplied_boundaries=['Module/settings filesystem dispatcher', 'Kernel/heap/UI services', 'Incoming application state', 'Odd revision models interrupted writer'],
                actual_parallel_scheduler_verified=False, actual_pixels=False, physical_card_access=False, camera_access=False,
                shutdown_flush_implemented=False, physical_cache_or_durability_verified=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--module', type=Path, required=True)
    p.add_argument('--legacy-build', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists():
        p.error('Choose a new private output')
    result = audit((a.build / 'module-host.emulator.main.bin').read_bytes(), json.loads((a.build / 'module-host.emulator.json').read_text(encoding='utf-8')),
                   (a.module / 'Z7APP.BIN').read_bytes(), json.loads((a.module / 'module.json').read_text(encoding='utf-8')), a.legacy_build)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__':
    main()
