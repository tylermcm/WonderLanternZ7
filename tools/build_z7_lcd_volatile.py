"""Build a private storage-free LCD profile, without camera/card access (MIT)."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from build_z7_module import ROOT,SDK,build
from build_z7_module_host import ZIG
from prepare_flash_review import require_private_output


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    source=ROOT/'z7-native-modules/plugins/lcd_volatile_checkpoint.c';functions={};other_functions={}
    packet,meta=build(source,zig=ZIG.resolve(),function_details=functions)
    again,other=build(source,zig=ZIG.resolve(),function_details=other_functions)
    assert packet==again and meta==other and functions==other_functions
    inputs={};pending=[source,SDK/'module.ld']
    while pending:
        path=pending.pop().resolve();name=path.relative_to(ROOT).as_posix()
        if name in inputs:continue
        assert path.is_relative_to(ROOT/'z7-native-modules')
        inputs[name]=hashlib.sha256(path.read_bytes()).hexdigest()
        for include in re.findall(r'^\s*#\s*include\s+"([^"]+)"',path.read_text(encoding='utf-8'),re.M):
            choices=[(path.parent/include).resolve(),(SDK/include).resolve()]
            match=next((p for p in choices if p.is_file()),None)
            assert match is not None,(name,include)
            pending.append(match)
    assert not any(n.startswith(('persistence_','z7_persistence_','z7_settings_files_')) for n in meta['symbols'])
    meta.update(kind='original-Z7-LCD-volatile-checkpoint',module_sha256=hashlib.sha256(packet).hexdigest(),file_bytes=len(packet),
                source_inputs_sha256=inputs,function_details=functions,api_minimum_bytes=44,reproducible=True,
                dependency_scope='Conservative recursive quoted includes, including inactive conditional dependencies',
                do_not_stage=True,hardware_test_authorized=False,firmware_image=False,
                configuration=dict(persistent_settings=False,worker_registration_enabled=False),
                scope='Four compact LCD DISP presets, native grid/horizon/info groups/battery/focal; all preferences volatile')
    out.mkdir(parents=True)
    (out/'Z7APP.BIN').write_bytes(packet)
    (out/'module.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(bytes=len(packet),sha256=meta['module_sha256'],functions=len(functions),reproducible=True)))


if __name__=='__main__':main()
