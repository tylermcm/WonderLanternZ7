"""Build matched worker-disabled/enabled SD controls, private only (MIT)."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from build_z7_module import ROOT,HEADER,build,seal
from build_z7_module_host import ZIG
from prepare_flash_review import require_private_output


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--zig',type=Path,default=ZIG)
    a=p.parse_args();out=require_private_output(a.output)
    source=ROOT/'z7-native-modules/plugins/worker_registration_pair.c'
    packet,meta=build(source,zig=a.zig.resolve());again,other=build(source,zig=a.zig.resolve())
    assert packet==again and meta==other
    offset=meta['symbols']['worker_pair_enabled']
    assert offset%4==0 and offset not in meta['relocations'] and offset+4<=meta['image_bytes']
    assert struct.unpack_from('<I',packet,HEADER+offset)[0]==1
    disabled=bytearray(packet);struct.pack_into('<I',disabled,HEADER+offset,0);disabled=seal(disabled)
    allowed=set(range(32,36))|set(range(HEADER+offset,HEADER+offset+4))
    assert all(x==y or i in allowed for i,(x,y) in enumerate(zip(packet,disabled)))
    assert not any(n.startswith(('restore_','z7_settings_','persistence_')) for n in meta['symbols'])
    files=['plugins/worker_registration_pair.c','plugins/battery_grid_menu_checkpoint.c','plugins/battery_percent.c','plugins/battery_sample.h','plugins/grids_histogram.c','sdk/module.h','sdk/display.h','sdk/module.ld','sdk/worker.h','sdk/information.h','sdk/gui.h','sdk/disp.h','sdk/update.h']
    inputs={str(Path('z7-native-modules')/n).replace('\\','/'):hashlib.sha256((ROOT/'z7-native-modules'/n).read_bytes()).hexdigest() for n in files}
    out.mkdir(parents=True,exist_ok=False);hashes={}
    for name,data,enabled in (('disabled',disabled,False),('enabled',packet,True)):
        folder=out/name;folder.mkdir();digest=hashlib.sha256(data).hexdigest();hashes[name]=digest
        report=dict(meta,kind='original-Z7-worker-registration-pair',module_sha256=digest,file_bytes=len(data),
                    source_inputs_sha256=inputs,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    configuration=dict(battery_percent_enabled=True,worker_registration_enabled=enabled),
                    do_not_stage=True,hardware_test_authorized=False,firmware_image=False,
                    experiment='A disabled control first; B adds only return-only worker registration',
                    matched_pair=True,repair_claimed=False)
        (folder/'Z7APP.BIN').write_bytes(data)
        (folder/'module.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
        assert (folder/'Z7APP.BIN').read_bytes()==data
    pair=dict(schema=1,module_bytes=len(packet),flag_image_offset=offset,hashes=hashes,
              only_flag_and_crc_differ=True,image_bss_entry_relocations_identical=True,reproducible=True,
              no_file_io=True,no_selection_atomic_added=True,stage_authorized=False)
    (out/'pair.json').write_text(json.dumps(pair,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(pair))


if __name__=='__main__':main()
