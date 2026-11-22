"""Rebuild and scan exact ELF function ranges for exclusive ops (MIT)."""
import argparse
import hashlib
import json
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
from build_z7_module import ROOT,HEADER,build
from build_z7_module_host import ZIG
from prepare_flash_review import require_private_output


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('module','source','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    packet=(a.module/'Z7APP.BIN').read_bytes();meta=json.loads((a.module/'module.json').read_text())
    assert hashlib.sha256(packet).hexdigest()==meta['module_sha256']
    for n,digest in meta['source_inputs_sha256'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==digest
    details={};rebuilt,m=build(a.source.resolve(),zig=ZIG.resolve(),function_details=details)
    assert rebuilt==packet
    assert all(m[k]==meta[k] for k in ('symbols','entry_offset','image_bytes','bss_bytes','relocations'))
    cs=Cs(CS_ARCH_ARM,CS_MODE_THUMB);cs.skipdata=True;instructions=0;barriers=0
    for name,fn in details.items():
        start=fn['address']&~1;size=fn['bytes'];assert start+size<=meta['image_bytes']
        code=list(cs.disasm(packet[HEADER+start:HEADER+start+size],start))
        assert sum(i.size for i in code)==size,name
        bad=[dict(address=hex(i.address),opcode=i.mnemonic) for i in code if i.mnemonic.startswith(('ldrex','strex','clrex'))]
        assert not bad,(name,bad)
        instructions+=len(code);barriers+=sum(i.mnemonic=='dmb' for i in code)
    report=dict(passed=True,module_sha256=meta['module_sha256'],compiled_functions=len(details),decoded_instructions=instructions,dmb_instructions=barriers,
                function_bounds_from_elf=True,independently_rebuilt=True,exclusive_instructions=0,
                source=a.source.as_posix(),card_written=False,hardware_tested=False,
                limits=['Only module-owned function ranges; literal pools may be decoded within compiler function extents',
                        'Called native firmware functions and other modules are outside this scan',
                        'No proof of physical memory attributes or scheduler/memory ordering'])
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':main()
