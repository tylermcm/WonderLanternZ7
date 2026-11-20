"""Execute the compiled resident-worker API and the actual loader task loop.

SPDX-License-Identifier: MIT. Native file/task wrappers and module instructions
execute with supplied kernel/filesystem/heap boundaries and immediate delays.
No real card, settings save, scheduling interval or shutdown behavior claimed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC
from audit_splash_image import STACK, STOP, STOCK_SHA
from audit_z7_module_host import HostFixture
from build_z7_module_host import ROOT, STATE


class WorkerFixture(HostFixture):
    worker_loop = False

    def hook(self, u, address, size, context):
        if self.worker_loop and address == 0x1017081e:
            delay = u.reg_read(UC_ARM_REG_R0)
            self.events.append(('delay', delay))
            if delay == 1000:
                self.tick_observations.append((self.result_seen, self.words()[10], self.calls()))
                if len(self.tick_observations) == 3:
                    u.emu_stop()
                    return
            self.ret(0)
            return
        super().hook(u, address, size, context)

    def calls(self):
        base = getattr(self, 'probe_base', self.words()[12])
        return self.value('z7_worker_calls') if base else 0

    def value(self, name):
        return int.from_bytes(self.u.mem_read(getattr(self, 'probe_base', self.words()[12]) + self.module_symbols[name], 4), 'little')

    def configure(self, name, value):
        self.u.mem_write(self.words()[12] + self.module_symbols[name], struct.pack('<I', value))


def audit(raw, host, stock, modules, legacy):
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(stock).hexdigest() != STOCK_SHA:
        raise ValueError('Exact host and original stock fingerprints required')
    checks = []

    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good:
            raise AssertionError(name)

    def fixture(name='worker-success', image=raw, report=host, case='success'):
        packet = (modules / (name + '.BIN')).read_bytes()
        f = WorkerFixture(image, report, packet, case)
        metadata = json.loads((modules / (name + '.json')).read_text(encoding='utf-8'))
        metadata['packet_sha256'] = hashlib.sha256(packet).hexdigest()
        f.module_symbols = metadata['symbols']
        return f, metadata

    tick = host['symbols']['z7_module_worker_tick']
    f, module = fixture()
    status = f.call(host['symbols']['z7_module_load_once'], STATE)
    base = f.words()[12]
    f.probe_base = base
    check('worker-only-module-loads-with-api44', status == 8 and f.value('z7_worker_api_bytes') == 44)
    check('registration-null-foreign-even-bss-duplicate-rejected', f.value('z7_worker_registration_mask') == 63)
    check('initialization-does-not-call-worker', f.calls() == 0)
    check('worker-only-module-does-not-publish-display-hooks', f.words()[22:24] == (0, 0))
    check('resident-image-bounds-published', f.words()[52] == module['image_bytes'] and f.words()[52] < f.words()[14])
    check('late-registration-rejected', f.call(base + module['symbols']['z7_worker_late']) == 0)
    f.call(tick)
    check('unpublished-load-status-suppresses-tick', f.calls() == 0)
    f.setword(40, 8)
    f.call(tick)
    check('successful-resident-tick-once', f.calls() == 1 and f.words()[51] == 0)
    f.configure('z7_worker_dispatch', tick)
    f.configure('z7_worker_recurse', 1)
    f.call(tick)
    check('nested-worker-dispatch-suppressed-and-guard-released', f.calls() == 2 and not f.value('z7_worker_recurse') and not f.words()[51])
    for name, offset, value in (
        ('bad-magic', 32, 0), ('bad-guard', 240, 0), ('not-loaded', 40, 7),
        ('no-image', 48, 0), ('no-allocation', 52, 0), ('loading', 76, base),
        ('unregistered', 200, 0), ('null-callback', 196, 0),
        ('even-callback', 196, f.words()[49] & ~1), ('foreign-callback', 196, 0x102fd647),
        ('bss-callback', 196, base + module['image_bytes'] + 1),
        ('past-end', 196, base + module['image_bytes'] + module['bss_bytes'] + 1),
        ('empty-code', 208, 0), ('oversize-code', 208, f.words()[14] + 1),
        ('already-running', 204, 1)):
        saved, before = f.words()[offset // 4], f.calls()
        f.setword(offset, value)
        expected_state = bytes(f.u.mem_read(STATE, 256))
        f.call(tick)
        check(name + '-skips-callback', f.calls() == before)
        check(name + '-preserves-state', bytes(f.u.mem_read(STATE, 256)) == expected_state)
        f.setword(offset, saved)
    # A failed initializer must retire staged callback pointers before freeing.
    failed, _ = fixture('worker-failure')
    check('failed-initializer-rejected', failed.call(host['symbols']['z7_module_load_once'], STATE) == 7)
    check('failed-initializer-clears-worker-and-code-bounds', failed.words()[49:53] == (0, 0, 0, 0) and not failed.live)
    failed.setword(40, 8)
    failed.call(tick)
    check('failed-init-cannot-dispatch-freed-image', not failed.words()[12] and not failed.words()[51])
    # Execute the actual unbounded worker, stopping at the third resident delay.
    for name, case, expected_status, expected_calls in (
        ('worker-success', 'success', 8, (0, 1, 2)),
        ('worker-failure', 'success', 7, (0, 0, 0)),
        ('worker-success', 'missing', 1, (0, 0, 0))):
        g, _ = fixture(name, case=case)
        g.worker_loop, g.tick_observations = True, []
        g.u.reg_write(UC_ARM_REG_R0, STATE)
        g.u.reg_write(UC_ARM_REG_SP, STACK)
        g.u.reg_write(UC_ARM_REG_LR, STOP | 1)
        g.u.emu_start(host['symbols']['z7_module_worker'] | 1, STOP, timeout=30000000, count=10000000)
        prefix = name + '-' + case
        check(prefix + '-original-loop-delay-before-callback', tuple(g.tick_observations) == tuple((True, expected_status, c) for c in expected_calls))
        check(prefix + '-three-resident-delays', sum(e == ('delay', 1000) for e in g.events) == 3)
        check(prefix + '-callback-completes-with-guard-released', not g.words()[51])
        check(prefix + '-host-guards-preserved', g.words()[60:] == (0xa5a5a5a5,) * 4)
    old = json.loads((legacy / 'module-host.emulator.json').read_text(encoding='utf-8'))
    oldraw = (legacy / 'module-host.emulator.main.bin').read_bytes()
    if hashlib.sha256(oldraw).hexdigest() != old['main_payload_sha256']:
        raise ValueError('Legacy host fingerprint mismatch')
    g, _ = fixture(image=oldraw, report=old)
    check('api40-host-rejects-api44-module-before-registration', g.call(old['symbols']['z7_module_load_once'], STATE) == 7 and not g.live)
    return dict(passed=True, checks=checks, api_bytes=44, state_bytes=256,
                main_sha256=host['main_payload_sha256'], module_sha256=module['packet_sha256'],
                actual_worker_loop_executed=True, settings_persistence_implemented=False,
                supplied_boundaries=['Filesystem dispatcher', 'Kernel/task services', 'Allocator', 'Immediate delay return'],
                camera_access=False, card_access=False, hardware_timing_verified=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--modules', type=Path, required=True)
    p.add_argument('--legacy-build', type=Path, required=True)
    p.add_argument('--stock-main', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists():
        p.error('Choose a new private evidence path')
    result = audit((a.build / 'module-host.emulator.main.bin').read_bytes(),
                   json.loads((a.build / 'module-host.emulator.json').read_text(encoding='utf-8')),
                   a.stock_main.read_bytes(), a.modules, a.legacy_build)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__':
    main()
