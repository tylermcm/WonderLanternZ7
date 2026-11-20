"""Execute compiled RAM context reads after original source routing.

SPDX-License-Identifier: MIT. RAM contents and explicit read interleavings are
supplied. No native transaction, physical frame fence or epoch producer claimed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn import UC_HOOK_MEM_READ, UC_HOOK_CODE
from audit_splash_image import MEM, STOCK_SHA
from audit_z7_highlight_output import OutputFixture, SOURCE_SELECT, LIST, REAR_TAG, EVF_TAG, MODE
from build_z7_module import ROOT, HEADER, build
from build_z7_module_host import ZIG

CODE, NATIVE, REAR, EVF = MEM + 0x20000, 0xa2500000, 0xa2501000, 0xa2501100


def audit(raw, packet, metadata):
    if hashlib.sha256(raw).hexdigest() != STOCK_SHA:
        raise ValueError('Exact private original-Z7 C3.80 main required')
    f = OutputFixture(raw)
    f.u.mem_map(NATIVE, 0x4000)
    f.u.mem_map(0xa1d68000, 0x1000)
    image = bytearray(packet[HEADER:HEADER + metadata['image_bytes']])
    for off in metadata['relocations']:
        struct.pack_into('<I', image, off, struct.unpack_from('<I', image, off)[0] + CODE)
    f.u.mem_write(CODE, bytes(image) + bytes(metadata['bss_bytes']))
    symbols = metadata['symbols']
    out = CODE + symbols['z7_hc_result']
    checks = []

    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good:
            raise AssertionError(name)

    def reset(selector=0):
        f.write(0xa180a588, NATIVE)
        f.write(MODE, 0)
        f.write(0xa181c764, 1 if selector == 0 else 2)
        f.u.mem_write(0xa180a568, bytes([selector]))
        f.u.mem_write(0xa1d68e54, b'\3')
        f.write(NATIVE + 0x228, 1)
        f.u.mem_write(REAR, bytes(f.u.mem_read(REAR_TAG, 16)))
        f.u.mem_write(EVF, bytes(f.u.mem_read(EVF_TAG, 16)))
        f.write(LIST, REAR)
        f.write(LIST + 16, EVF)
        f.call(SOURCE_SELECT, LIST, 0, 0)
        f.call(SOURCE_SELECT, LIST, 0, 2)
        f.u.mem_write(out, b'\xa5' * 28)

    read = lambda: f.call(CODE + symbols['z7_hc_read'])
    for selector in (0, 1):
        for mode in (0, 1, 2, 0xffffffff):
            reset(selector)
            f.write(MODE, mode)
            check(f'route{selector}-mode{mode:x}-compiled-reader-matches-native-ram-state', read() == 1 and
                  bytes(f.u.mem_read(out, 28)) == struct.pack('<7I', mode, 1 if selector == 0 else 2,
                    selector, NATIVE, REAR if selector == 0 else EVF, 1, 3))
    for name, address, value, byte in (
        ('null-state', 0xa180a588, 0, False), ('unaligned-state', 0xa180a588, NATIVE + 1, False),
        ('state-range-overflow', 0xa180a588, 0xfffffffc, False),
        ('unsupported-selector', 0xa180a568, 2, True), ('null-source', NATIVE + 8, 0, False),
        ('unaligned-source', NATIVE + 8, REAR + 1, False),
        ('opposite-source-tag', NATIVE + 8, EVF, False), ('tag-final-byte-mismatch', REAR + 12, 1, False)):
        reset()
        if byte:
            f.u.mem_write(address, bytes([value]))
        else:
            f.write(address, value)
        check(name + '-returns-failure-without-partial-output', read() == 0 and bytes(f.u.mem_read(out, 28)) == b'\xa5' * 28)
    reset()
    for live, cached in ((0, 1), (1, 0)):
        f.write(MODE, live)
        f.write(0xa201f47c, cached)
        check(f'live-mode{live}-does-not-use-stale-gui-cache{cached}', read() == 1 and f.read(out) == live)
    reset()
    f.write(LIST, 0)
    f.write(LIST + 16, 0)
    f.call(SOURCE_SELECT, LIST, 0, 0)
    check('native-no-match-stale-mirror-does-not-establish-context', f.read(0xa180a534) == REAR and
          f.read(NATIVE + 8) == 0 and read() == 0 and bytes(f.u.mem_read(out, 28)) == b'\xa5' * 28)
    reset()
    # Mid-read state changes are explicit scheduling inputs. Apply the write
    # at the NEXT instruction after a load, so that load has completed with
    # its original value. Writing from a memory-read hook can affect the very
    # load being observed, which would not model a between-load transition.
    count, pending = [0], [False]
    def once(u, access, address, size, value, context):
        count[0] += 1
        if count[0] == 1:
            pending[0] = True
    def change_once(u, address, size, context):
        if pending[0]:
            pending[0] = False
            f.write(MODE, 1)
    hook = f.u.hook_add(UC_HOOK_MEM_READ, once, begin=MODE, end=MODE + 3)
    code_hook = f.u.hook_add(UC_HOOK_CODE, change_once)
    f.u.ctl_remove_cache(CODE, CODE + len(image))
    once_result = read()
    observed_once = (once_result, f.read(out), count[0])
    check('mode-transition-retries-and-never-publishes-first-stale-sample', observed_once == (1, 1, 4))
    f.u.hook_del(hook)
    f.u.hook_del(code_hook)
    f.u.ctl_remove_cache(CODE, CODE + len(image))
    reset()
    count[0] = 0
    def churn(u, access, address, size, value, context):
        count[0] += 1
        if count[0] % 2:
            pending[0] = True
    def change_each(u, address, size, context):
        if pending[0]:
            pending[0] = False
            f.write(MODE, ((count[0] + 1) // 2) & 1)
    hook = f.u.hook_add(UC_HOOK_MEM_READ, churn, begin=MODE, end=MODE + 3)
    code_hook = f.u.hook_add(UC_HOOK_CODE, change_each)
    f.u.ctl_remove_cache(CODE, CODE + len(image))
    check('continuous-transitions-stop-after-three-attempts-with-output-unchanged', read() == 0 and
          count[0] == 6 and bytes(f.u.mem_read(out, 28)) == b'\xa5' * 28)
    f.u.hook_del(hook)
    f.u.hook_del(code_hook)
    f.u.ctl_remove_cache(CODE, CODE + len(image))
    for name, address, value, byte, index in (
        ('output-kind', 0xa181c764, 2, False, 1), ('selector', 0xa180a568, 1, True, 2),
        ('state-pointer', 0xa180a588, NATIVE + 0x2000, False, 3),
        ('source-pointer', NATIVE + 8, NATIVE + 0x1200, False, 4),
        ('readiness', NATIVE + 0x228, 0, False, 5), ('service', 0xa1d68e54, 4, True, 6)):
        reset()
        f.u.mem_write(NATIVE + 0x2000, bytes(f.u.mem_read(NATIVE, 0x22c)))
        f.u.mem_write(NATIVE + 0x1200, bytes(f.u.mem_read(REAR_TAG, 16)))
        count[0], pending[0] = 0, False
        def observe(u, access, location, size, before, context):
            count[0] += 1
            if count[0] == 1:
                pending[0] = True
        def change(u, pc, size, context):
            if pending[0]:
                pending[0] = False
                if byte:
                    f.u.mem_write(address, bytes([value]))
                else:
                    f.write(address, value)
        hook = f.u.hook_add(UC_HOOK_MEM_READ, observe, begin=address, end=address + (0 if byte else 3))
        code_hook = f.u.hook_add(UC_HOOK_CODE, change)
        f.u.ctl_remove_cache(CODE, CODE + len(image))
        check(name + '-transition-retries-without-publishing-the-first-sample',
              read() == 1 and f.read(out + index * 4) == value and count[0] == 4)
        f.u.hook_del(hook)
        f.u.hook_del(code_hook)
        f.u.ctl_remove_cache(CODE, CODE + len(image))
    check('null-destination-rejected', f.call(CODE + symbols['z7_hc_null']) == 0)
    return dict(passed=True, checks=checks, stock_main_sha256=STOCK_SHA,
                compiled_ram_reader_and_native_source_routing_execute=True,
                input_ram_and_read_interleavings_supplied=True, reader_attempt_bound=3,
                native_transaction_or_aba_detection=False, shared_epoch_publication_implemented=False,
                photo_mode_output_eligibility_or_ui_preset_policy_implemented=False,
                full_profile_preference_connected=False, warning_pixels=False, physical_camera_or_card_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists():
        p.error('Choose a new private output directory')
    out.mkdir(parents=True)
    packet, metadata = build(ROOT / 'z7-native-modules/examples/highlight_context_probe.c', zig=ZIG)
    (out / 'probe.BIN').write_bytes(packet)
    (out / 'probe.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8', newline='\n')
    result = audit(a.stock_main.read_bytes(), packet, metadata)
    result['source_sha256'] = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
        'tools/audit_z7_highlight_context.py', 'tools/audit_z7_highlight_output.py',
        'z7-native-modules/examples/highlight_context_probe.c', 'z7-native-modules/plugins/highlight_context.h')}
    result['probe_sha256'] = hashlib.sha256(packet).hexdigest()
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__':
    main()
