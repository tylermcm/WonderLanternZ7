"""Build private progress or hardened read-only restore checkpoints (MIT)."""
import argparse
import hashlib
import json
from pathlib import Path
from build_z7_module import ROOT,build
from build_z7_module_host import ZIG
from grid_restore_record import encode
from prepare_flash_review import require_private_output


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--variant',choices=('progress','restore-readonly'),required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=require_private_output(a.output)
    restore=a.variant=='restore-readonly'
    relative='plugins/grid_restore_readonly_checkpoint.c' if restore else 'plugins/worker_progress_checkpoint.c'
    source=ROOT/'z7-native-modules'/relative;functions={};again_functions={}
    packet,meta=build(source,zig=ZIG.resolve(),function_details=functions)
    again,other=build(source,zig=ZIG.resolve(),function_details=again_functions)
    assert packet==again and meta==other and functions==again_functions
    files=[relative,'plugins/battery_grid_menu_checkpoint.c','plugins/battery_percent.c','plugins/battery_sample.h','plugins/grids_histogram.c',
           'sdk/module.h','sdk/display.h','sdk/module.ld','sdk/worker.h','sdk/information.h','sdk/gui.h','sdk/disp.h','sdk/update.h']
    if restore:files+=['plugins/grid_restore_record.h','plugins/settings_files.c','plugins/settings_files.h','plugins/settings_storage.h','plugins/display_settings.h']
    report=dict(meta,kind='original-Z7-grid-restore-readonly-checkpoint' if restore else 'original-Z7-worker-progress-checkpoint',
                checkpoint_revision=2 if restore else 1,module_sha256=hashlib.sha256(packet).hexdigest(),file_bytes=len(packet),api_minimum_bytes=44,
                function_details=functions,configuration=dict(battery_percent_enabled=True,worker_registration_enabled=True),
                source_inputs_sha256={str(Path('z7-native-modules')/n).replace('\\','/'):hashlib.sha256((ROOT/'z7-native-modules'/n).read_bytes()).hexdigest() for n in files},
                reproducible=True,do_not_stage=True,hardware_test_authorized=False,firmware_image=False,
                scope='One read-only seed restore; GUI-owned selection latch; no atomic RMW' if restore else 'Visible saturating worker counter in Off menu label; no file I/O',
                required_host='Owner-tested task-owned worker guard; EG f479950ea8188f1de337719bda34dc3765f397c97d79759349ec21566d58f140',
                camera_writes=False)
    out.mkdir(parents=True)
    (out/'Z7APP.BIN').write_bytes(packet)
    (out/'module.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    if restore:(out/'Z7GRID.DAT').write_bytes(encode(5))
    print(json.dumps(dict(variant=a.variant,bytes=len(packet),sha256=report['module_sha256'],functions=len(functions),reproducible=True)))


if __name__=='__main__':main()
