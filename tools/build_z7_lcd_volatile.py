"""Build private LCD checkpoints, without camera/card access (MIT)."""
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
    profiles=p.add_mutually_exclusive_group()
    profiles.add_argument('--persistent',action='store_true',help='Build the v1 display-preference journal trial; grid layout stays in RAM')
    profiles.add_argument('--startup-grid',action='store_true',help='Build the persistence comparison with initial grid invalidation limited to actual deltas')
    profiles.add_argument('--grid-persistence',action='store_true',help='Save grid shape in separate Z7DSP v3 preference journals; legacy Z7CFG is read-only fallback')
    profiles.add_argument('--settings-root',action='store_true',help='Experimental separate Display settings entry in Custom Settings overview, with v3 persistence')
    profiles.add_argument('--settings-category',action='store_true',help='Experimental colored h category for the separate Display settings entry')
    a=p.parse_args();out=require_private_output(a.output)
    settings_root=a.settings_root or a.settings_category
    grid_persistence=a.grid_persistence or settings_root
    startup=a.startup_grid or grid_persistence
    persistent=a.persistent or startup
    source=ROOT/'z7-native-modules/plugins'/('lcd_settings_category_checkpoint.c' if a.settings_category else 'lcd_settings_root_checkpoint.c' if settings_root else 'lcd_grid_persistence_checkpoint.c' if grid_persistence else 'lcd_startup_grid_checkpoint.c' if startup else 'lcd_persistence_checkpoint.c' if persistent else 'lcd_volatile_checkpoint.c');functions={};other_functions={}
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
    if persistent:
        assert all(n in meta['symbols'] for n in ('persistence_worker','persistence_prepare','z7_settings_files_write'))
    else:
        assert not any(n.startswith(('persistence_','z7_persistence_','z7_settings_files_')) for n in meta['symbols'])
    meta.update(kind='original-Z7-LCD-settings-root-checkpoint' if settings_root else 'original-Z7-LCD-grid-persistence-checkpoint' if grid_persistence else 'original-Z7-LCD-startup-grid-checkpoint' if startup else 'original-Z7-LCD-persistence-checkpoint' if persistent else 'original-Z7-LCD-volatile-checkpoint',module_sha256=hashlib.sha256(packet).hexdigest(),file_bytes=len(packet),
                source_inputs_sha256=inputs,function_details=functions,api_minimum_bytes=44,reproducible=True,
                dependency_scope='Conservative recursive quoted includes, including inactive conditional dependencies',
                do_not_stage=True,hardware_test_authorized=False,firmware_image=False,
                configuration=dict(persistent_settings=persistent,worker_registration_enabled=persistent,initial_grid_delta_only=startup,grid_layout_persistence=grid_persistence,settings_root_entry=settings_root,settings_category_entry=a.settings_category),
                scope=('LCD preferences including grid shape, separate Z7DSP slots/v3 payload; legacy Z7CFG read-only fallback' if grid_persistence else 'Four compact LCD DISP presets, native grid/horizon/info groups/battery/focal; v1 preference journal, RAM-only grid layout' if persistent else 'Four compact LCD DISP presets, native grid/horizon/info groups/battery/focal; all preferences volatile'))
    out.mkdir(parents=True)
    (out/'Z7APP.BIN').write_bytes(packet)
    (out/'module.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(bytes=len(packet),sha256=meta['module_sha256'],functions=len(functions),reproducible=True)))


if __name__=='__main__':main()
