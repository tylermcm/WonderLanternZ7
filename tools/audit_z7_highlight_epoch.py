"""Execute epoch publication and full persistent-profile context observation.

SPDX-License-Identifier: MIT. Explicit task interleavings and incoming native
RAM, filesystem/UI/surface boundaries supplied. No warning parameters/flags
written, no visible highlights, native transaction or physical scheduling proof.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_R0
from audit_splash_image import NativePNG, STOCK_SHA, MEM, STACK, STOP
from audit_z7_highlight_submission import enter, returned
from audit_z7_display_persistence import PersistenceFixture
from audit_z7_settings_files import PATHS
from audit_z7_settings_storage import record
from build_z7_module import ROOT, HEADER, build
from build_z7_module_host import STATE, ZIG

CODE, NATIVE, FRAME = MEM + 0x20000, 0xa2500000, MEM + 0x10000


def ledger_audit(stock, packet, metadata, check):
    f = NativePNG(stock)
    image = bytearray(packet[HEADER:HEADER + metadata['image_bytes']])
    for off in metadata['relocations']:
        struct.pack_into('<I', image, off, struct.unpack_from('<I', image, off)[0] + CODE)
    f.u.mem_write(CODE, bytes(image) + bytes(metadata['bss_bytes']))
    symbols = metadata['symbols']
    pub, inp, out = (CODE + symbols['z7_he_' + n] for n in ('publication', 'input', 'output'))
    def word(p): return int.from_bytes(f.u.mem_read(p, 4), 'little')
    def write(p, v): f.u.mem_write(p, struct.pack('<I', v))
    def call(n): return f.call(CODE + symbols['z7_he_' + n])
    check('compiled-view-layout-has-all-twelve-publication-words', word(CODE + symbols['z7_he_view_words']) == 12)
    f.u.mem_write(out, b'\xa5' * 52)
    check('uninitialized-epoch-never-publishes-output', call('read') == 0 and bytes(f.u.mem_read(out, 52)) == b'\xa5' * 52)
    check('first-complete-publication-gets-nonzero-epoch', call('publish') == 1 and call('read') == 1 and word(out) == 1)
    for index in range(12):
        write(inp + index * 4, index + 7)
        check(f'view-field{index}-change-advances-epoch-and-publishes-whole-view', call('publish') == 1 and
              call('read') == 1 and word(out) == index + 2 and bytes(f.u.mem_read(out + 4, 48)) == bytes(f.u.mem_read(inp, 48)))
        check(f'view-field{index}-unchanged-gui-tick-keeps-epoch', call('publish') == 1 and word(pub + 4) == index + 2)
    write(pub, word(pub) | 1)
    before = bytes(f.u.mem_read(pub, 60))
    f.u.mem_write(out, b'\xa5' * 52)
    check('reentrant-writer-and-reader-return-without-spinning-or-partial-output', call('publish') == call('read') == 0 and
          bytes(f.u.mem_read(pub, 60)) == before and bytes(f.u.mem_read(out, 52)) == b'\xa5' * 52)
    write(pub, 0xfffffffe)
    write(inp, 123)
    check('sequence-wrap-keeps-new-nonzero-epoch-and-complete-view', call('publish') == 1 and word(pub) == 0 and
          call('read') == 1 and word(out) == 14 and word(out + 4) == 123)

    # Pause the reader after its first published-word load, run the compiled
    # GUI publisher on a separate emulated stack, then resume the old reader.
    pending = [False]
    def observe(u, access, address, size, value, context): pending[0] = True
    def pause(u, address, size, context):
        if pending[0]:
            pending[0] = False
            u.emu_stop()
    hook = f.u.hook_add(UC_HOOK_MEM_READ, observe, begin=pub + 12, end=pub + 15)
    code_hook = f.u.hook_add(UC_HOOK_CODE, pause)
    f.u.ctl_remove_cache(CODE, CODE + len(image))
    guards = enter(f, CODE + symbols['z7_he_read'], (), STACK)
    context = f.u.context_save()
    prior_sequence = word(pub)
    check('reader-reaches-explicit-mid-snapshot-interleaving', f.u.reg_read(UC_ARM_REG_PC) != STOP)
    f.u.hook_del(hook); f.u.hook_del(code_hook)
    f.u.ctl_remove_cache(CODE, CODE + len(image))
    new = tuple(100 + i for i in range(12))
    f.u.mem_write(inp, struct.pack('<12I', *new))
    writer_guards = enter(f, CODE + symbols['z7_he_publish'], (), STACK - 0x10000)
    check('interleaved-compiled-writer-preserves-independent-stack', returned(f, STACK - 0x10000, writer_guards) and f.u.reg_read(UC_ARM_REG_R0) == 1)
    # Supply the same sequence value to model its32-bit wrap while the reader
    # was suspended. The independently monotonic epoch must still reject the
    # old epoch/partially read view. No billions-of-publishes timing claimed.
    write(pub, prior_sequence)
    f.u.context_restore(context)
    f.u.emu_start(f.u.reg_read(UC_ARM_REG_PC) | 1, STOP, timeout=10000000, count=10000000)
    check('resumed-reader-retries-to-complete-new-epoch-even-when-sequence-repeats', returned(f, STACK, guards) and f.u.reg_read(UC_ARM_REG_R0) == 1 and
          word(out) == 15 and bytes(f.u.mem_read(out + 4, 48)) == struct.pack('<12I', *new))
    write(pub + 4, 0xffffffff)
    check('unchanged-last-epoch-remains-readable', call('publish') == 1 and call('read') == 1 and word(out) == 0xffffffff)
    write(inp, 200)
    f.u.mem_write(out, b'\xa5' * 52)
    check('epoch-exhaustion-permanently-parks-instead-of-recycling-queued-identity', call('publish') == 0 and word(pub + 8) == 1 and
          call('read') == 0 and bytes(f.u.mem_read(out, 52)) == b'\xa5' * 52 and call('publish') == 0)


class EpochProfileFixture(PersistenceFixture):
    def __init__(self, raw, host, packet, files):
        super().__init__(raw, host, packet, files)
        self.u.mem_map(NATIVE, 0x4000)
        self.u.mem_map(0xa1d68000, 0x1000)
        self.epoch_startup = []
        self.native_source_frames = []
        self.write(0xa180a588, NATIVE)
        self.write(NATIVE + 8, NATIVE + 0x1000)
        self.u.mem_write(NATIVE + 0x1000, bytes(self.u.mem_read(0x1062a5b8, 16)))
        self.write(NATIVE + 12, NATIVE + 0x1100)
        self.u.mem_write(NATIVE + 0x1100, bytes(self.u.mem_read(0x1062a5c8, 16)))
        self.write(NATIVE + 0x228, 1)
        self.u.mem_write(0xa180a568, b'\0')
        self.u.mem_write(0xa1d68e54, b'\3')
        self.write(0xa24e1e00, 0)
        self.write(0xa181c764, 1)
        self.write(0xa181f91c, 0xa2c41000)
        self.u.mem_write(0xa2c41000, struct.pack('<4I', 4, 1, 0, 0xa2c42000))

    def hook(self, u, address, size, context):
        if address == 0x1023b9d0:
            self.native_source_frames.append(u.reg_read(UC_ARM_REG_R0))
            self.ret(1)  # Surface/frame apply boundary; original route executes.
            return
        if address == 0x1027beae and hasattr(self, 'epoch_startup'):
            p = u.reg_read(UC_ARM_REG_R0)
            if bytes(u.mem_read(p + 0x9c, 1)) == b'\5' and self.words()[19]:
                path = self.cstring(int.from_bytes(u.mem_read(p + 16, 4), 'little'))
                if path in PATHS:
                    self.epoch_startup.append((self.words()[23], all(self.words()[53:58]), self.words()[50]))
        super().hook(u, address, size, context)


def profile_audit(raw, host, packet, module, check):
    configured = (1, 15, 9, 0, 4, 8, 255, 0, 0, 255)
    f = EpochProfileFixture(raw, host, packet, {PATHS[0]: record(configured, 1)})
    status = f.call(host['symbols']['z7_module_load_once'], STATE)
    f.base = f.words()[12]
    f.setword(40, status)
    symbols = module['symbols']
    f.focal_object_global = f.base + symbols['z7_focal_object']
    f.focal_renderer = f.base + symbols['focal_painter']
    def addr(n): return f.base + symbols[n]
    def value(n): return f.read(addr(n))
    def epoch(): return value('z7_highlight_gui_epoch')
    def source(output=0): return f.call(0x1034866e, output, FRAME)
    def worker(): f.call(host['symbols']['z7_module_worker_tick'])
    def gui():
        # Existing after-GUI fixture supplies native delta-snapshot completion;
        # actual focal/histogram module callbacks remain composed and execute.
        f.u.mem_write(0xa201d80c, bytes(f.u.mem_read(0xa201d4d0, 0x33c)))
        f.call(host['symbols']['z7_display_after_gui_update'])
    check('full-api48-profile-registers-context-hooks-and-worker-before-startup-io', status == 8 and
          f.epoch_startup == [(0, True, 1), (0, True, 1)] and module['api_minimum_bytes'] == 48)
    check('startup-context-stays-unpublished-until-gui-tick', epoch() == 0 and source() == 1 and value('z7_highlight_source_epoch') == 0)
    f.call(host['symbols']['z7_display_before_update'])
    before = list(f.file_events)
    gui()
    check('actual-full-profile-gui-callback-publishes-enabled-photo-preset-context', epoch() == 1 and value('z7_base_active') == 1)
    worker()
    check('actual-worker-observes-published-epoch-without-extra-file-io', value('z7_highlight_worker_epoch') == 1 and value('z7_highlight_worker_eligible') == 1 and f.file_events == before)
    frame = bytes(f.u.mem_read(FRAME, 0x4b8))
    check('actual-source-hook-observes-epoch-with-caller-frame-left-native', source() == 1 and value('z7_highlight_source_epoch') == 1 and bytes(f.u.mem_read(FRAME, 0x4b8)) == frame)
    gui()
    check('unchanged-gui-refresh-keeps-queued-epoch-stable', epoch() == 1)
    for next_preset in (1, 2, 3, 0):
        check(f'actual-native-disp-cycle-reaches-preset{next_preset}',
              f.call(host['symbols']['z7_display_disp_cycle']) == 0x100 and value('z7_readout_preset') == next_preset)
        source(); worker()
        check(f'preset{next_preset}-rejects-old-epoch-even-after-round-trip',
              value('z7_highlight_source_epoch') == value('z7_highlight_worker_epoch') == 0)
    gui()
    check('preset-round-trip-publishes-new-generation-instead-of-reusing-old-epoch', epoch() == 2)
    for name, address, bad, byte in (
        ('mode', 0xa24e1e00, 1, False), ('output-kind', 0xa181c764, 2, False),
        ('selector', 0xa180a568, 1, True), ('service', 0xa1d68e54, 2, True),
        ('menu', 0xa2c41008, 1, False), ('app', 0xa1829af4, 13, True)):
        old = bytes(f.u.mem_read(address, 1 if byte else 4))
        f.u.mem_write(address, bytes([bad]) if byte else struct.pack('<I', bad))
        worker()
        source()
        check(name + '-change-rejects-old-epoch-before-another-gui-publication', value('z7_highlight_worker_epoch') == value('z7_highlight_source_epoch') == 0)
        f.u.mem_write(address, old)
    # Execute original compiled menu action, not a synthetic revision update.
    f.write(addr('z7_settings_view'), 1)
    f.write(addr('z7_settings_preset'), 0)
    f.u.mem_write(0xa1833548 + 22, struct.pack('<2H', 5, 0))
    f.call(addr('sm_activate'))
    check('native-menu-highlight-toggle-publishes-new-settings-revision', value('z7_settings_revision') == 2)
    source(); worker()
    check('menu-edit-invalidates-old-publication-immediately', value('z7_highlight_source_epoch') == value('z7_highlight_worker_epoch') == 0)
    gui()
    check('next-gui-publishes-disabled-highlight-epoch', epoch() == 3 and f.read(addr('z7_highlight_publication') + 12 + 9 * 4) == 0)
    source()
    check('disabled-component-remains-native-and-unclaimed', value('z7_highlight_source_epoch') == 0 and bytes(f.u.mem_read(FRAME, 0x4b8)) == frame)
    # Exhaustion must disable source/worker observation even if raw state and
    # settings happen to return to an old matching value later.
    f.write(addr('z7_highlight_publication') + 8, 1)
    source(); worker()
    check('halted-ledger-rejects-source-and-worker', value('z7_highlight_source_epoch') == value('z7_highlight_worker_epoch') == 0)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--module', type=Path, required=True)
    p.add_argument('--legacy-build', type=Path, required=True, help='API44 host for early-rejection validation')
    p.add_argument('--stock-main', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists(): p.error('Choose a new private output directory')
    stock = a.stock_main.read_bytes()
    if hashlib.sha256(stock).hexdigest() != STOCK_SHA: p.error('Exact stock main required')
    raw = (a.build / 'module-host.emulator.main.bin').read_bytes()
    host = json.loads((a.build / 'module-host.emulator.json').read_text())
    packet = (a.module / 'Z7APP.BIN').read_bytes()
    module = json.loads((a.module / 'module.json').read_text())
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        p.error('Host/module fingerprint mismatch')
    out.mkdir(parents=True)
    probe, metadata = build(ROOT / 'z7-native-modules/examples/highlight_epoch_probe.c', zig=ZIG)
    (out / 'probe.BIN').write_bytes(probe)
    (out / 'probe.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8', newline='\n')
    checks = []
    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good: raise AssertionError(name)
    ledger_audit(stock, probe, metadata, check)
    profile_audit(raw, host, packet, module, check)
    legacy = json.loads((a.legacy_build / 'module-host.emulator.json').read_text())
    f = PersistenceFixture((a.legacy_build / 'module-host.emulator.main.bin').read_bytes(), legacy, packet)
    check('api44-host-rejects-context-profile-before-menu-or-settings-io',
          f.call(legacy['symbols']['z7_module_load_once'], STATE) == 7 and not f.live and
          not any(event[0] in ('open', 'create', 'write') for event in f.file_events) and
          bytes(f.u.mem_read(0xa1833548, 44)) == bytes(44))
    result = dict(passed=True, checks=checks, host_sha256=host['main_payload_sha256'], module_sha256=module['module_sha256'],
        compiled_ledger_and_full_persistent_profile_callbacks_execute=True,
        filesystem_ui_frame_apply_and_explicit_scheduling_supplied=True,
        native_parameter_submission_or_foreign_parameter_interception_implemented=False,
        frame_permission_writes_or_warning_pixels=False, epoch_recycling=False, camera_card_access=False)
    result['source_sha256'] = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
        'tools/audit_z7_highlight_epoch.py', 'z7-native-modules/plugins/highlight_epoch.h',
        'z7-native-modules/examples/highlight_epoch_probe.c', 'z7-native-modules/examples/display_highlight_context_policy.h')}
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(checks))))


if __name__ == '__main__': main()
