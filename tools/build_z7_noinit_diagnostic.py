# SPDX-License-Identifier: MIT
"""Private, same-layout SD diagnostic: skip module initialization entirely.

Not camera firmware or a repair. Changes only the entry's first four bytes and
packet CRC. No card write/installation is authorized by this tool. Existing
component licenses/notices apply to the unchanged copied module body.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from build_z7_module import ABI, HEADER, MAGIC, TARGET, pack_module, seal
from prepare_flash_review import ROOT, require_private_output

RETURN_ZERO = bytes.fromhex('00207047')  # movs r0,#0; bx lr


def disable_entry(packet, expected_sha256):
    packet = bytes(packet)
    if hashlib.sha256(packet).hexdigest() != expected_sha256 or len(packet) < HEADER:
        raise ValueError('Exact source module required')
    fields = struct.unpack_from('<4s15I', packet)
    magic, abi, target, size, image_size, bss, entry, count = fields[:8]
    if (magic, abi, target, size) != (MAGIC, ABI, TARGET, len(packet)) or size != HEADER+image_size+4*count:
        raise ValueError('Unsupported source header')
    image = packet[HEADER:HEADER+image_size]
    relocs = list(struct.unpack_from('<'+'I'*count, packet, HEADER+image_size))
    if pack_module(image, bss, entry, relocs) != packet:
        raise ValueError('Source header, CRC or relocations not canonical')
    if entry+4 > image_size or any(entry < off+4 and off < entry+4 for off in relocs):
        raise ValueError('Entry patch overlaps relocation or image boundary')
    changed = bytearray(packet)
    changed[HEADER+entry:HEADER+entry+4] = RETURN_ZERO
    changed = seal(changed)
    allowed = set(range(32,36)) | set(range(HEADER+entry,HEADER+entry+4))
    if any(a != b and i not in allowed for i,(a,b) in enumerate(zip(packet,changed))):
        raise AssertionError('Unexpected packet mutation')
    return changed, dict(entry_offset=entry,image_bytes=image_size,bss_bytes=bss,
                         relocations=relocs,file_bytes=size)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('module','build','output'): p.add_argument('--'+name,type=Path,required=True)
    a = p.parse_args()
    output = require_private_output(a.output)
    source = json.loads((a.module/'module.json').read_text())
    if source['kind'] != 'original-Z7-LCD-first-release-candidate':
        raise ValueError('Requires the quarantined LCD profile, not arbitrary firmware')
    packet, layout = disable_entry((a.module/'Z7APP.BIN').read_bytes(),source['module_sha256'])
    for key in ('entry_offset','image_bytes','bss_bytes','relocations','file_bytes'):
        if layout[key] != source[key]: raise ValueError('Source metadata mismatch: '+key)
    from audit_z7_module_host import HostFixture
    from build_z7_module_host import STATE
    raw = (a.build/'module-host.emulator.main.bin').read_bytes()
    host = json.loads((a.build/'module-host.emulator.json').read_text())
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256']:
        raise ValueError('Exact host required')
    fixture = HostFixture(raw,host,packet)
    status = fixture.call(host['symbols']['z7_module_load_once'],STATE)
    words = fixture.words()
    assert status == 8 and words[12] and words[13]
    assert not any(words[22:51]), 'Diagnostic registered callbacks or published UI hooks'
    reads = fixture.read_count
    assert fixture.call(host['symbols']['z7_module_load_once'],STATE) == 10
    assert fixture.read_count == reads, 'Loaded module was unexpectedly reloaded'
    report = dict(kind='original-Z7-entry-disabled-diagnostic',**layout,
                  source_module_sha256=source['module_sha256'],
                  module_sha256=hashlib.sha256(packet).hexdigest(),
                  host_main_sha256=host['main_payload_sha256'],
                  entry_returns_zero=True,display_and_worker_registration=False,
                  native_loader_instruction_check_passed=True,native_load_status=status,
                  same_file_size_image_bss_and_relocations=True,
                  emulator_only=True,hardware_trial_authorized=False,do_not_stage=True,
                  camera_firmware_image=False,repair_claimed=False,
                  limits=['Filesystem/kernel/allocator boundaries supplied; no real card startup proof',
                          'Same byte count/layout does not prove identical card timing',
                          'Installed host remains unchanged; no hardware test authorized'],
                  source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    output.mkdir(parents=True)
    (output/'Z7APP.BIN').write_bytes(packet)
    (output/'diagnostic.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:report[k] for k in ('kind','module_sha256','native_load_status','display_and_worker_registration','do_not_stage')}))


if __name__ == '__main__': main()
