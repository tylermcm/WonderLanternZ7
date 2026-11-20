"""Independently verify Other OFF preserves the six separate native readouts.

SPDX-License-Identifier: MIT. Some ordinary control boxes overlap ISO. Recheck
the immutable captured RGB against one complete native reference per frame,
including those overlap regions and shared warnings. No composed references.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from PIL import Image, ImageChops
from build_z7_module_host import ROOT
from display_pixel_geometry import control_scanout_box

CORE=(10,11,15,5,51,2)


def verify(evidence):
    result=json.loads((evidence/'result.json').read_text())
    if not result.get('passed') or not result.get('information_scope',{}).get('other_group_tested'):
        raise ValueError('Successful Other-information evidence required')
    steps={s['name']:s for s in result['steps']};pictures={}
    def picture(name):
        if name not in pictures:
            raw=(evidence/(name+'.png')).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=steps[name]['frame_sha256']:raise AssertionError('Capture fingerprint: '+name)
            pictures[name]=Image.open(evidence/(name+'.png')).convert('RGB')
        return pictures[name]
    def boxes(step,widgets,image):
        regions=[]
        for widget in widgets:
            for raw in step['information_controls'][str(widget)]:
                rect=struct.unpack_from('<4h',bytes.fromhex(raw),10)
                if rect[0]<rect[2] and rect[1]<rect[3]:regions.append(control_scanout_box(rect,image.size))
        return regions
    cases=[]
    for membership in result['information_pixel_membership']:
        if membership['frame']!='information-other-off':continue
        step=steps[membership['frame']];image=picture(step['name'])
        if bytes.fromhex(step['information_native_snapshot'])[0x193]!=0:
            raise ValueError('This whole-core overlap check is scoped to ordinary operation193=0')
        targets=membership['widget']
        if not isinstance(targets,list):raise ValueError('Other target set required')
        target_boxes=boxes(step,targets,image)
        warnings=result.get('other_warning_pixels',{}).get('widgets',[])
        if not warnings:raise AssertionError('No shared warning present in fixture')
        protected_boxes=boxes(step,(*CORE,*warnings),image)
        matches=[]
        for candidate in membership['matches']:
            reference=steps[candidate['reference']]
            if reference['information_formats']!=step['information_formats']:continue
            baseline=picture(reference['name'])
            difference=ImageChops.difference(image,baseline)
            changed=difference.getbbox()
            if not changed:continue
            outside=difference.copy()
            for box in target_boxes:outside.paste((0,0,0),box)
            if outside.getbbox() is not None:continue
            if all(image.crop(box).tobytes()==baseline.crop(box).tobytes() for box in protected_boxes):
                matches.append(dict(reference=reference['name'],difference_bounds=changed))
        if not matches:raise AssertionError('Other OFF changed core readout/warning pixels, including overlapping native boxes')
        cases.append(dict(frame=step['name'],same_complete_native_reference_matches=matches,
            protected_core_widgets=list(CORE),protected_warning_widgets=warnings,passed=True))
    if not cases:raise AssertionError('Other OFF capture missing')
    return dict(passed=True,cases=cases,module_sha256=result['module_sha256'],
        capture_fingerprints_verified=True,overlapping_other_boxes_do_not_exempt_core_or_warning_pixels=True,
        native_operation193=0,composed_reference=False,camera_access=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evidence',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();evidence=args.evidence.resolve();output=args.output.resolve()
    if not evidence.is_relative_to(ROOT/'.private') or not output.is_relative_to(ROOT/'.private') or output.exists():
        p.error('Existing private evidence and a new private output required')
    result=verify(evidence);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,cases=len(result['cases']),core_widgets=len(CORE))))


if __name__=='__main__':main()
