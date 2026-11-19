"""Execute the disabled-by-default clean-DISP diagnostic through the native host.

SPDX-License-Identifier: MIT. GUI page/output/control objects are supplied;
compiled module/host and native visibility setters execute. No pixel proof.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from audit_z7_battery_percent import AutomaticFixture
from build_z7_module_host import ROOT, STATE


def audit(raw, host, packet, module):
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256'] or hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Host/module fingerprint mismatch')
    f = AutomaticFixture(raw, host, packet)
    if f.call(host['symbols']['z7_module_load_once'], STATE) != 8: raise AssertionError('load')
    base = f.words()[12]
    def setword(name, value): f.u.mem_write(base + module['symbols'][name], struct.pack('<I', value))
    def word(name): return int.from_bytes(f.u.mem_read(base + module['symbols'][name], 4), 'little')
    def before(): f.call(host['symbols']['z7_display_before_paint'])
    setword('z7_battery_enabled', 0)
    f.u.mem_write(0xa181f91c, struct.pack('<I', 0xa2c41000))
    f.u.mem_write(0xa2c41000, struct.pack('<4I', 4, 4, 0, 0xa2c42000))
    f.u.mem_write(0xa201d4d0 + 0x18a, b'\1')
    descriptors = [int.from_bytes(f.u.mem_read(0x1064d610 + i * 4, 4), 'little') for i in range(61)]
    original = [bytes(f.u.mem_read(p + 4, 36)) for p in descriptors]
    objects = []
    for i in range(4):
        p = 0xa1fb0000 + i * 512; objects.append(p)
        f.u.mem_write(p, bytes(284))
        for off, value in ((4, 4), (40, 1), (72, 0xa201e3b4), (76, 0x10384969)):
            f.u.mem_write(p + off, struct.pack('<I', value))
        f.u.mem_write(0xa1824684 + (i + 1) * 48 + 36, struct.pack('<I', p))
    checks = []
    def check(name, passed):
        checks.append(dict(name=name, passed=bool(passed)))
        if not passed: raise AssertionError(name)
    def masks(): return [bytes(f.u.mem_read(p + 4, 36)) for p in descriptors]
    def visibility(): return [int.from_bytes(f.u.mem_read(p + 40, 4), 'little') for p in objects]
    before(); check('default-disabled-leaves-native-masks-and-brackets', masks() == original and visibility() == [1] * 4)
    setword('z7_clean_request', 1); before()
    expected = [struct.pack('<9I', *(v & ~0x22222 for v in struct.unpack('<9I', b))) for b in original]
    check('requested-clears-only-simplified-mask-bits', masks() == expected and word('z7_clean_active') == 1)
    check('original-visibility-setter-hides-four-brackets', visibility() == [0] * 4)
    before(); check('repeated-paint-preserves-initial-restoration-snapshot', masks() == expected)
    setword('z7_clean_request', 0); before()
    check('disable-restores-all-masks-and-four-native-visible-states', masks() == original and visibility() == [1] * 4)
    for name, address, value in [('menu', 0xa2c41008, b'\1\0\0\0'), ('evf', 0xa18237c6, b'\2'), ('movie', 0xa201d510, b'\1')]:
        setword('z7_clean_request', 1); before()
        f.u.mem_write(address, value); before()
        check(name + '-restores-masks-and-brackets', masks() == original and visibility() == [1] * 4)
        f.u.mem_write(address, bytes(len(value)))
    setword('z7_clean_request', 2); before()
    check('unknown-request-does-not-activate', masks() == original and not word('z7_clean_active'))
    setword('z7_clean_request', 1); before()
    f.u.mem_write(descriptors[0] + 4, struct.pack('<I', 0x12345678))
    setword('z7_clean_request', 0); before()
    check('foreign-mask-write-not-overwritten-on-restore', bytes(f.u.mem_read(descriptors[0] + 4, 4)) == struct.pack('<I', 0x12345678))
    f.u.mem_write(descriptors[0] + 4, original[0][:4])
    old_binding = bytes(f.u.mem_read(0x1064d610 + 60 * 4, 4))
    f.u.mem_write(0x1064d610 + 60 * 4, struct.pack('<I', 0x100))
    setword('z7_clean_request', 1); before()
    check('invalid-final-descriptor-rejects-before-any-mask-store', masks() == original and not word('z7_clean_active'))
    f.u.mem_write(0x1064d610 + 60 * 4, old_binding)
    # A foreign painter at the known control slot must not be hidden.
    f.u.mem_write(objects[0] + 76, struct.pack('<I', 0x100202b5)); before()
    check('foreign-bracket-painter-is-not-hidden', visibility()[0] == 1 and visibility()[1:] == [0] * 3)
    setword('z7_clean_request', 0); before()
    check('foreign-bracket-exclusion-does-not-break-mask-restoration', masks() == original)
    return dict(passed=True, checks=checks, module_sha256=module['module_sha256'], main_sha256=host['main_payload_sha256'],
                actual_pixels_verified=False, camera_access=False, supplied_boundaries=['GUI/control/page/output state', 'Loader services'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--module', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists(): parser.error('Choose a new private output')
    result = audit((args.build / 'module-host.emulator.main.bin').read_bytes(),
                   json.loads((args.build / 'module-host.emulator.json').read_text()),
                   (args.module / 'Z7APP.BIN').read_bytes(), json.loads((args.module / 'module.json').read_text()))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__': main()
