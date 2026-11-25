"""Build the private original-Z7 shutter-sound trigger-probe module (MIT).

No camera access, no firmware image. The module plays no sound; it counts three
capture-notification callbacks and logs them to A:\\Z7TRIG.DAT.
--field-test builds the combined field-test module (probe plus one chime preview
on resident-worker tick 8).
"""
import argparse,hashlib,json,re
from pathlib import Path
from build_z7_module import ROOT,SDK,build
from build_z7_module_host import ZIG
from prepare_flash_review import require_private_output


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--field-test',action='store_true')
    a=p.parse_args();out=require_private_output(a.output)
    if out.exists():p.error('Choose a new private output directory')
    source=ROOT/'z7-native-modules/plugins'/('shutter_sound_field_test.c' if a.field_test else 'shutter_trigger_probe.c')
    functions,again_functions={},{}
    packet,m=build(source,zig=ZIG.resolve(),function_details=functions)
    again,second=build(source,zig=ZIG.resolve(),function_details=again_functions)
    assert packet==again and m==second and functions==again_functions
    inputs={};pending=[source,SDK/'module.ld']
    while pending:
        path=pending.pop().resolve();rel=path.relative_to(ROOT).as_posix()
        if rel in inputs:continue
        inputs[rel]=hashlib.sha256(path.read_bytes()).hexdigest()
        for include in re.findall(r'^\s*#\s*include\s+"([^"]+)"',path.read_text(encoding='utf-8'),re.M):
            pending.append(next(q for q in (path.parent/include,SDK/include) if q.is_file()))
    m.update(module_sha256=hashlib.sha256(packet).hexdigest(),file_bytes=len(packet),reproducible=True,
        source_inputs_sha256=inputs,function_details=functions,kind='original-Z7-shutter-sound-field-test' if a.field_test else 'original-Z7-shutter-trigger-probe',
        plays_sound=a.field_test,boot_preview=a.field_test,photo_trigger=False,log_file='A:\\Z7TRIG.DAT',settings_writes=False,
        do_not_stage=True,hardware_test_authorized=False,firmware_image=False)
    out.mkdir(parents=True);(out/'Z7APP.BIN').write_bytes(packet)
    (out/'module.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(bytes=len(packet),sha256=m['module_sha256'],reproducible=True)))


if __name__=='__main__':main()
