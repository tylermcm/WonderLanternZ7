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
    profiles.add_argument('--settings-label-refresh',action='store_true',help='Repair cold/stale name labels for the h Display settings entry on the GUI task')
    profiles.add_argument('--histogram-presets',action='store_true',help='Add guarded live histogram controls to all four saved LCD presets')
    profiles.add_argument('--movie-battery',action='store_true',help='Experimental movie LCD battery percentage, retaining histogram presets and exact native icon guards')
    profiles.add_argument('--information-page',action='store_true',help='Add an opt-in native full Information display to the saved LCD DISP cycle, retaining movie battery/histogram work')
    profiles.add_argument('--photo-highlights',action='store_true',help='Offline API72 highlight integration with combined v4 settings in separate Z7EXT journals; requires a new reviewed host')
    profiles.add_argument('--shutter-sound',action='store_true',help='Installed settings-label LCD configuration plus shutter sound in Silent photography with a volume row and the Z7SND.DAT level file')
    profiles.add_argument('--shutter-sound-9',action='store_true',help='Shutter-sound LCD build with volume OFF/1-9 (tone fixed at 31)')
    profiles.add_argument('--shutter-sound-exif',action='store_true',help='Shutter-sound OFF/1-9 LCD build plus the upside-down photo EXIF Orientation 3 fix')
    profiles.add_argument('--inverted-playback',action='store_true',help='EXPERIMENTAL: sound+EXIF LCD build plus upside-down photo playback')
    profiles.add_argument('--sound-folder',action='store_true',help='Sound+EXIF LCD build with a Shutter sound page choosing from SHUTTER1.WAV and SHUTTER/SOUND01-10.WAV')
    profiles.add_argument('--folder-playback',action='store_true',help='EXPERIMENTAL: sound-folder LCD build plus upside-down photo playback')
    profiles.add_argument('--vr-probe',action='store_true',help='EXPERIMENTAL: everyday folder+playback LCD build plus a read-only VR telemetry probe (pixel-shift research)')
    profiles.add_argument('--vr-move',action='store_true',help='EXPERIMENTAL: everyday folder+playback LCD build plus the VR one-move test (moves the sensor once per boot; pixel-shift step 2)')
    profiles.add_argument('--vr-restore',action='store_true',help='EXPERIMENTAL: the VR one-move test plus Nikon D2 restore afterwards (pixel-shift step 2b)')
    profiles.add_argument('--pixel-series',action='store_true',help='EXPERIMENTAL: pixel-shift series dry run (you take four photos; the sensor steps one Bayer position after each; pixel-shift step 3a)')
    profiles.add_argument('--pixel-release',action='store_true',help='EXPERIMENTAL: module-fired pixel-shift series (the module releases the shutter four times; pixel-shift step 3b)')
    profiles.add_argument('--pixel-probe',action='store_true',help='EXPERIMENTAL: pixel-shift geometry probe (one module-fired frame per command variant, then restore variants; step 3c)')
    profiles.add_argument('--pixel-calib',action='store_true',help='EXPERIMENTAL: pixel-shift calibration run (nine module-fired frames at larger steps, repeated references; step 3d)')
    profiles.add_argument('--pixel-shift',action='store_true',help='EXPERIMENTAL: first real Z7 pixel-shift series (4 module-fired frames, calibrated x 20 / y 18 steps, settle delays, D2 apply restore)')
    profiles.add_argument('--af-buttons',action='store_true',help='everyday folder+playback LCD build plus AF-area buttons (Extras page)')
    profiles.add_argument('--sound-lab',action='store_true',help='EXPERIMENTAL: shutter-sound build whose volume row also offers levels 8/9 and driver tone values')
    profiles.add_argument('--movie-orientation',action='store_true',help='Offline cumulative API72 build with guarded movie orientation publication; task quiescence and hardware unverified')
    a=p.parse_args();out=require_private_output(a.output)
    photo_highlights=a.photo_highlights or a.movie_orientation
    information_page=a.information_page or photo_highlights
    movie_battery=a.movie_battery or information_page
    histogram_presets=a.histogram_presets or movie_battery
    label_refresh=a.settings_label_refresh or histogram_presets or a.shutter_sound or a.sound_lab or a.shutter_sound_9 or a.shutter_sound_exif or a.inverted_playback or a.sound_folder or a.folder_playback or a.vr_probe or a.vr_move or a.vr_restore or a.pixel_series or a.pixel_release or a.pixel_probe or a.pixel_calib or a.pixel_shift or a.af_buttons
    settings_category=a.settings_category or label_refresh
    settings_root=a.settings_root or settings_category
    grid_persistence=a.grid_persistence or settings_root
    startup=a.startup_grid or grid_persistence
    persistent=a.persistent or startup
    source=ROOT/'z7-native-modules/plugins'/('lcd_movie_orientation_checkpoint.c' if a.movie_orientation else 'lcd_sound_lab_checkpoint.c' if a.sound_lab else 'lcd_vr_probe_checkpoint.c' if a.vr_probe else 'lcd_vr_move_checkpoint.c' if a.vr_move else 'lcd_vr_restore_checkpoint.c' if a.vr_restore else 'lcd_pixel_series_checkpoint.c' if a.pixel_series else 'lcd_pixel_release_checkpoint.c' if a.pixel_release else 'lcd_pixel_probe_checkpoint.c' if a.pixel_probe else 'lcd_pixel_calib_checkpoint.c' if a.pixel_calib else 'lcd_pixel_shift_checkpoint.c' if a.pixel_shift else 'lcd_af_buttons_checkpoint.c' if a.af_buttons else 'lcd_folder_playback_checkpoint.c' if a.folder_playback else 'lcd_inverted_playback_checkpoint.c' if a.inverted_playback else 'lcd_sound_folder_checkpoint.c' if a.sound_folder else 'lcd_shutter_sound_exif_checkpoint.c' if a.shutter_sound_exif else 'lcd_shutter_sound9_checkpoint.c' if a.shutter_sound_9 else 'lcd_shutter_sound_checkpoint.c' if a.shutter_sound else 'lcd_highlights_checkpoint.c' if photo_highlights else 'lcd_information_checkpoint.c' if information_page else 'lcd_movie_battery_checkpoint.c' if movie_battery else 'lcd_histogram_checkpoint.c' if histogram_presets else 'lcd_settings_label_checkpoint.c' if label_refresh else 'lcd_settings_category_checkpoint.c' if settings_category else 'lcd_settings_root_checkpoint.c' if settings_root else 'lcd_grid_persistence_checkpoint.c' if grid_persistence else 'lcd_startup_grid_checkpoint.c' if startup else 'lcd_persistence_checkpoint.c' if persistent else 'lcd_volatile_checkpoint.c');functions={};other_functions={}
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
        assert all(n in meta['symbols'] for n in ('highlight_combined_worker' if photo_highlights else 'persistence_worker','persistence_prepare','z7_settings_files_write'))
    else:
        assert not any(n.startswith(('persistence_','z7_persistence_','z7_settings_files_')) for n in meta['symbols'])
    meta.update(kind='original-Z7-LCD-settings-root-checkpoint' if settings_root else 'original-Z7-LCD-grid-persistence-checkpoint' if grid_persistence else 'original-Z7-LCD-startup-grid-checkpoint' if startup else 'original-Z7-LCD-persistence-checkpoint' if persistent else 'original-Z7-LCD-volatile-checkpoint',module_sha256=hashlib.sha256(packet).hexdigest(),file_bytes=len(packet),
                source_inputs_sha256=inputs,function_details=functions,api_minimum_bytes=72 if photo_highlights else 44,reproducible=True,
                dependency_scope='Conservative recursive quoted includes, including inactive conditional dependencies',
                do_not_stage=True,hardware_test_authorized=False,firmware_image=False,
                configuration=dict(persistent_settings=persistent,worker_registration_enabled=persistent,initial_grid_delta_only=startup,grid_layout_persistence=grid_persistence,settings_root_entry=settings_root,settings_category_entry=settings_category,settings_label_refresh=label_refresh,histogram_presets=histogram_presets,movie_battery=movie_battery,information_page=information_page,photo_highlights=photo_highlights,combined_preferences=photo_highlights,movie_orientation=a.movie_orientation,shutter_sound=a.shutter_sound or a.sound_lab or a.shutter_sound_9 or a.shutter_sound_exif or a.inverted_playback or a.sound_folder or a.folder_playback or a.vr_probe or a.vr_move or a.vr_restore or a.pixel_series or a.pixel_release or a.pixel_probe or a.pixel_calib or a.pixel_shift or a.af_buttons,sound_lab=a.sound_lab,sound_levels=9 if (a.shutter_sound_9 or a.shutter_sound_exif or a.inverted_playback or a.sound_folder or a.folder_playback or a.vr_probe or a.vr_move or a.vr_restore or a.pixel_series or a.pixel_release or a.pixel_probe or a.pixel_calib or a.pixel_shift or a.af_buttons) else 7 if a.shutter_sound else None,exif_orientation=a.shutter_sound_exif or a.inverted_playback or a.sound_folder or a.folder_playback or a.vr_probe or a.vr_move or a.vr_restore or a.pixel_series or a.pixel_release or a.pixel_probe or a.pixel_calib or a.pixel_shift or a.af_buttons,inverted_playback=a.inverted_playback or a.folder_playback or a.vr_probe or a.vr_move or a.vr_restore or a.pixel_series or a.pixel_release or a.pixel_probe or a.pixel_calib or a.pixel_shift or a.af_buttons,sound_folder=a.sound_folder or a.folder_playback or a.vr_probe or a.vr_move or a.vr_restore or a.pixel_series or a.pixel_release or a.pixel_probe or a.pixel_calib or a.pixel_shift or a.af_buttons,vr_probe=a.vr_probe,vr_move=a.vr_move or a.vr_restore or a.pixel_series or a.pixel_release or a.pixel_probe or a.pixel_calib or a.pixel_shift,vr_restore=a.vr_restore or a.pixel_series or a.pixel_release or a.pixel_probe or a.pixel_calib or a.pixel_shift,pixel_series=a.pixel_series or a.pixel_release or a.pixel_probe or a.pixel_calib or a.pixel_shift,pixel_release=a.pixel_release or a.pixel_probe or a.pixel_calib or a.pixel_shift,pixel_probe=a.pixel_probe or a.pixel_calib,pixel_calib=a.pixel_calib,pixel_shift=a.pixel_shift,af_buttons=a.af_buttons),
                scope=('Combined LCD highlights/grid/page v4 preferences in separate Z7EXT slots; DSP/CFG read-only fallback; guarded offline movie publication' if a.movie_orientation else 'Combined LCD highlights/grid/page v4 preferences in separate Z7EXT slots; DSP/CFG read-only fallback' if photo_highlights else 'LCD preferences including grid shape, separate Z7DSP slots/v3 payload; legacy Z7CFG read-only fallback' if grid_persistence else 'Four compact LCD DISP presets, native grid/horizon/info groups/battery/focal; v1 preference journal, RAM-only grid layout' if persistent else 'Four compact LCD DISP presets, native grid/horizon/info groups/battery/focal; all preferences volatile'))
    out.mkdir(parents=True)
    (out/'Z7APP.BIN').write_bytes(packet)
    (out/'module.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(bytes=len(packet),sha256=meta['module_sha256'],functions=len(functions),reproducible=True)))


if __name__=='__main__':main()
