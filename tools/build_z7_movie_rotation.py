"""Build the private prepare-only original-Z7 movie shadow module (MIT)."""
import argparse,hashlib,json,re
from pathlib import Path
from build_z7_module import ROOT,SDK,build
from build_z7_module_host import ZIG
from prepare_flash_review import require_private_output


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    if out.exists():p.error('Choose a new private output directory')
    source=ROOT/'z7-native-modules/plugins/movie_rotation_module.c'
    packet,m=build(source,zig=ZIG);again,second=build(source,zig=ZIG)
    assert packet==again and m==second
    inputs={};pending=[source,SDK/'module.ld']
    while pending:
        path=pending.pop().resolve();name=path.relative_to(ROOT).as_posix()
        if name in inputs:continue
        inputs[name]=hashlib.sha256(path.read_bytes()).hexdigest()
        for include in re.findall(r'^\s*#\s*include\s+"([^"]+)"',path.read_text(),re.M):
            pending.append(next(q for q in (path.parent/include,SDK/include) if q.is_file()))
    m.update(module_sha256=hashlib.sha256(packet).hexdigest(),file_bytes=len(packet),
        reproducible=True,source_inputs_sha256=inputs,kind='original-Z7-movie-shadow-prepare-only',
        do_not_stage=True,hardware_test_authorized=False,callback_installed=False,
        explicit_offline_publication_operation=7,physical_task_quiescence_verified=False,
        native_open_split_track_services_verified=False,complete_native_task_verified=False)
    out.mkdir(parents=True);(out/'Z7APP.BIN').write_bytes(packet)
    (out/'module.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(bytes=len(packet),sha256=m['module_sha256'],reproducible=True,prepare_only=True)))


if __name__=='__main__':main()
