"""Execute native menu wake/dispatch and owned save-status refresh.

SPDX-License-Identifier: MIT. Kernel event delivery, empty input queue, incoming
GUI state and text/paint services are supplied. Original event flag wrapper,
menu state dispatcher and empty-queue handler execute. No physical camera proof.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1
from audit_z7_display_persistence import PersistenceFixture
from build_z7_module_host import ROOT, STATE

MENU, SLOT, EVENT_FLAG, PAGE = 0xa182ecb8, 0xa182ed34, 0xa181f910, 0xa1833548


class MenuStatusFixture(PersistenceFixture):
    def __init__(self, *args):
        super().__init__(*args)
        self.notifications, self.delegates, self.queue_polls = [], [], 0
        self.results[0x10332e56] = 0  # Explicit empty native input queue.

    def hook(self, u, address, size, context):
        if address == 0x10170be8:
            self.notifications.append((u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)))
            self.ret(0)
            return
        if address == 0x1048bffc:
            self.delegates.append((u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)))
        if address == 0x10332e56:
            self.queue_polls += 1
        super().hook(u, address, size, context)


def audit(raw, host, packet, module):
    assert hashlib.sha256(raw).hexdigest() == host['main_payload_sha256']
    assert hashlib.sha256(packet).hexdigest() == module['module_sha256']
    checks, symbols = [], module['symbols']

    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good:
            raise AssertionError(name)

    def word(f, address):
        return int.from_bytes(f.u.mem_read(address, 4), 'little')

    def put(f, address, value):
        f.u.mem_write(address, struct.pack('<I', value))

    def load(foreign_slot=False):
        f = MenuStatusFixture(raw, host, packet)
        if module.get('configuration',{}).get('grid_layout_persistence'):
            f.file_paths += ('A:\\Z7DSP0.DAT','A:\\Z7DSP1.DAT')
        if foreign_slot:
            put(f, SLOT, 0xdeadbeef)
        status = f.call(host['symbols']['z7_module_load_once'], STATE)
        f.base = f.words()[12]
        f.setword(40, status)  # Original loader task publishes load_once result.
        return f, status

    def call(f, name, *args):
        return f.call(f.base + symbols[name], *args)

    def title(f):
        return [text for slot, text in f.menu_labels if slot == 230][-1]

    f, status = load()
    check('init-publishes-owned-menu-dispatch-after-success', status == 8 and word(f, SLOT) == f.base + symbols['sm_menu_dispatch'])
    # Explicit incoming native GUI state, no synthetic user input or model edit.
    f.u.mem_write(MENU + 0x74, b'\1')
    put(f, PAGE + 12, 0xa2948000)
    put(f, 0xa2c41000 + 8, 1)
    put(f, 0xa2c42000, PAGE)
    put(f, EVENT_FLAG, 0xa200da78)
    call(f, 'sm_render', PAGE)
    check('initial-menu-title-defaults-without-notification', title(f) == 'Display: Defaults' and not f.notifications)
    put(f, PAGE + 20, 0)  # Native row0, using only the real menu activation adapter.
    call(f, 'sm_activate')
    check('actual-menu-action-shows-unsaved', title(f) == 'Display: Unsaved')
    labels = list(f.menu_labels)
    for _ in range(4):
        f.call(host['symbols']['z7_module_worker_tick'])
    check('worker-only-notifies-original-event-flag-without-label-writes', f.menu_labels == labels and f.notifications == [(0xa200da78, 2)] * 2)
    check('worker-save-acknowledges-real-menu-revision', word(f, f.base + symbols['z7_persistence_saved_revision']) == word(f, f.base + symbols['z7_settings_revision']) == 2)
    scratch = 0xa2949000
    put(f, scratch, 0)
    # Native event3 processes an empty queue before the wrapper refreshes text.
    native_result = f.call(0x1048bffc, 3, scratch)
    f.delegates.clear()
    polls = f.queue_polls
    result = f.call(0x1046503c, MENU, 3, scratch)
    check('original-menu-dispatch-and-empty-queue-handler-execute', f.delegates == [(3, scratch)] and f.queue_polls == polls + 1)
    check('queued-menu-refresh-updates-saved-title-preserving-native-result', title(f) == 'Display: Saved' and result == native_result)
    labels = list(f.menu_labels)
    f.call(0x1046503c, MENU, 3, scratch)
    check('unchanged-status-does-not-rewrite-native-labels', f.menu_labels == labels)

    # Dirty again, then close the owned page before its worker completes.
    call(f, 'sm_activate')
    labels, notifications = list(f.menu_labels), list(f.notifications)
    put(f, 0xa2c42000, PAGE + 42 * 44)
    for _ in range(4):
        f.call(host['symbols']['z7_module_worker_tick'])
    check('worker-never-wakes-a-different-focused-menu-page', f.notifications == notifications)
    f.call(0x1046503c, MENU, 3, scratch)
    check('other-focused-page-is-never-repainted-by-status-wrapper', f.menu_labels == labels)

    put(f, 0xa2c42000, PAGE)
    for name, address, value in [('foreign-slot', SLOT, 0x1048bffd), ('closed-stack', 0xa2c41000 + 8, 0), ('no-event-handle', EVENT_FLAG, 0)]:
        old = word(f, address)
        put(f, address, value)
        notifications = list(f.notifications)
        f.call(host['symbols']['z7_module_worker_tick'])
        check(name + '-blocks-worker-notification', f.notifications == notifications)
        put(f, address, old)
    f.u.mem_write(MENU + 0x74, b'\0')
    notifications = list(f.notifications)
    f.call(host['symbols']['z7_module_worker_tick'])
    call(f, 'sm_menu_dispatch', 3, scratch)
    check('inactive-menu-state-retains-native-delegation-without-paint-or-notify', f.menu_labels == labels and f.notifications == notifications)

    foreign, status = load(True)
    check('foreign-dispatch-slot-rejects-initializer-before-file-io', status == 7 and word(foreign, SLOT) == 0xdeadbeef and not any(e[0] in ('open', 'create', 'read', 'write', 'close') for e in foreign.file_events) and not foreign.live)
    return dict(passed=True, checks=checks, module_sha256=module['module_sha256'], main_sha256=host['main_payload_sha256'],
                original_event_flag_wrapper_executes=True, original_menu_state_dispatcher_executes=True,
                original_empty_queue_handler_executes=True, supplied_boundaries=['Kernel event flag delivery', 'Empty input queue', 'Incoming native GUI state', 'Text and paint services'],
                actual_pixels=False, physical_card=False, camera_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--module', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists():
        p.error('Choose a new private output')
    result = audit((a.build / 'module-host.emulator.main.bin').read_bytes(), json.loads((a.build / 'module-host.emulator.json').read_text(encoding='utf-8')),
                   (a.module / 'Z7APP.BIN').read_bytes(), json.loads((a.module / 'module.json').read_text(encoding='utf-8')))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__':
    main()
