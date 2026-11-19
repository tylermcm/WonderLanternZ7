"""Validate owned display registration and absent-module native fallbacks.

SPDX-License-Identifier: MIT. Compiled Thumb host/module and original Z7 geometry
and scalar instructions execute. File/kernel/heap/UI boundaries remain supplied.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1
from audit_z7_module_host import HostFixture
from audit_grid_geometry import GridFixture, DESCRIPTOR
from audit_grid_native_value import NativeValueGrid
from audit_splash_image import MEM, STOCK_SHA
from build_z7_module_host import ROOT, STATE, MAGIC, DISPLAY_PRESET


class DisplayFixture(HostFixture):
    def hook(self, u, address, size, context):
        if address == 0x103fa97c:
            self.ret(1)
        elif address == 0x10295822:
            self.ret(0x11223344)
        else:
            super().hook(u, address, size, context)


def audit(raw, host, stock, modules):
    if host['preset'] != DISPLAY_PRESET or hashlib.sha256(raw).hexdigest() != host['main_payload_sha256']:
        raise ValueError('Requires exact display-host candidate')
    if hashlib.sha256(stock).hexdigest() != STOCK_SHA:
        raise ValueError('Requires exact original Z7 MAIN')
    checks = []
    def check(name, passed):
        checks.append(dict(name=name, passed=bool(passed)))
        if not passed:
            raise AssertionError(name)
    def load(kind):
        packet = (modules / (kind + '.BIN')).read_bytes()
        meta = json.loads((modules / (kind + '.json')).read_text())
        f = DisplayFixture(raw, host, packet)
        status = f.call(host['symbols']['z7_module_load_once'], STATE)
        return f, meta, status
    success, module, status = load('success')
    check('owned-hook-registration-succeeds', status == 8 and success.words()[22:24] == (1, 1))
    base = success.words()[12]
    symbols = module['symbols']
    word = lambda offset: int.from_bytes(success.u.mem_read(base + offset, 4), 'little')
    check('all-eight-registration-contracts-executed', word(symbols['z7_display_probe_mask']) == 255)
    check('initializer-does-not-run-paint-callback', word(symbols['z7_display_probe_calls']) == 0)
    success.call(host['symbols']['z7_display_after_paint'])
    check('committed-callback-runs-module-code', word(symbols['z7_display_probe_calls']) == 1)
    check('post-init-registration-rejected', success.call(base + symbols['z7_display_probe_late_register']) == 0)
    success.setword(92, 0)
    success.call(host['symbols']['z7_display_after_paint'])
    check('publication-flag-gates-callback-execution', word(symbols['z7_display_probe_calls']) == 1)
    success.setword(92, 1)
    check('invalid-owned-grid-table-falls-back', success.call(host['symbols']['z7_display_grid_source']) == 0x1064fd90)
    grid = base + symbols['invalid_grid']
    for i in range(3):
        for off in (10, 22):
            success.u.mem_write(grid + i * 32 + off, struct.pack('<H', 3))
    check('valid-owned-grid-table-admitted', success.call(host['symbols']['z7_display_grid_source']) == grid)
    success.u.mem_write(grid + 22, struct.pack('<H', 9))
    check('excessive-grid-count-falls-back', success.call(host['symbols']['z7_display_grid_source']) == 0x1064fd90)
    before = word(symbols['z7_display_probe_calls'])
    check('native-paint-return-and-stack-preserved', success.call(0x103fcc44, 0x12345678, 3) == 0x11223344)
    check('paint-bridge-calls-committed-module-once', word(symbols['z7_display_probe_calls']) == before + 1)
    failed, _, failed_status = load('failure')
    check('failed-init-publishes-no-hooks-and-frees-image', failed_status == 7 and
          not failed.live and failed.words()[12:14] == (0, 0) and failed.words()[19:32] == (0,) * 13)
    failed.call(host['symbols']['z7_display_after_paint'])
    check('failed-module-paint-path-remains-stock', failed.call(host['symbols']['z7_display_grid_source']) == 0x1064fd90)

    # Exact geometry comparison through both new bridge windows, no module.
    for viewport in ((0, 0, 720, 480), (20, 40, 700, 440), (0, 0, 640, 426)):
        a, b = GridFixture(raw, viewport, 0), GridFixture(stock, viewport, 0)
        a.u.mem_map(STATE, 4096)
        for mode in range(3):
            for crop in (0, 1, 2, 4, 8):
                a.crop = b.crop = crop
                a.call(0x10376da0, mode)
                b.call(0x10376da0, mode)
                check(f'no-module-native-geometry-{viewport}-{mode}-{crop}',
                      bytes(a.u.mem_read(DESCRIPTOR, 32)) == bytes(b.u.mem_read(DESCRIPTOR, 32)))

    # The same native indexed-property catalogue used by the earlier saved-grid
    # audit; no synthetic property getter substitutes for the original tables.
    a, b = NativeValueGrid(raw), NativeValueGrid(stock)
    a.u.mem_map(STATE, 4096)
    a.initialize(); b.initialize()
    keys = []
    for group in range(72):
        address = 0x114d8d9c + group * 28
        if b.word(address):
            _, count = struct.unpack('<HH', b.u.mem_read(address + 12, 4))
            if count > 256:
                raise ValueError('Unexpected indexed-property catalogue')
            keys.extend((group << 8) | i for i in range(count))
    keys += [0xffffffff, 0xffff, 0]
    same = flags = True
    for key in keys:
        ar, br = a.scalar(key, MEM), b.scalar(key, MEM)
        same &= ar == br and a.word(MEM) == b.word(MEM)
        flags &= a.scalar_flags == b.scalar_flags
    check('no-module-native-scalar-catalogue-differential', same)
    check('no-module-native-scalar-nzcvq-differential', flags)
    for state in range(256):
        check('no-module-histogram-state-' + str(state),
              failed.call(host['symbols']['z7_display_histogram_gate'], state) == int(state == 2))
    return dict(passed=True, checks=checks, scalar_reads_per_image=len(keys),
        scope='Owned display API and native no-module geometry/scalar fallbacks; supplied file/kernel/heap/UI boundaries',
        main_sha256=host['main_payload_sha256'], camera_access=False, card_access=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--modules', type=Path, required=True)
    parser.add_argument('--stock', type=Path, default=ROOT / '.private/builds/20261021-laptop-01/stock-main.bin')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists():
        parser.error('Choose a new private evidence path')
    raw = (args.build / 'module-host.emulator.main.bin').read_bytes()
    host = json.loads((args.build / 'module-host.emulator.json').read_text())
    result = audit(raw, host, args.stock.read_bytes(), args.modules)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(passed=True, checks=len(result['checks']), scalar_reads_per_image=result['scalar_reads_per_image'])))


if __name__ == '__main__':
    main()
