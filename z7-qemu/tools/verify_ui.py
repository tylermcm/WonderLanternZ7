# SPDX-License-Identifier: GPL-2.0-or-later
"""Exercise the running local photo UI and save real QEMU screenshots.

This uses the same authenticated local actions as the UI. Native MENU
roundtrips must return actual processed pixels in the same QEMU session.
"""
import argparse
import io
import json
from pathlib import Path
import re
import time
from urllib.request import Request, urlopen
from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent/'.local/ui-verification'
URL = 'http://127.0.0.1:8787'


def get(path):
    with urlopen(URL+path, timeout=8) as r: return r.read()


def state(): return json.loads(get('/api/status'))


def main():
    global URL, OUT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--menu',action='store_true',help='Verify three native MENU roundtrips')
    parser.add_argument('--url',default=URL,help='Running local WonderLantern UI URL')
    parser.add_argument('--output',type=Path,default=OUT)
    args=parser.parse_args()
    URL=args.url.rstrip('/')
    OUT=args.output.resolve()
    if not URL.startswith('http://127.0.0.1:'):
        parser.error('Verification is limited to a local UI')
    if OUT.exists():
        parser.error('Use a new --output directory to preserve earlier verification')
    OUT.mkdir(parents=True)
    report = {'url': URL, 'checks': [], 'screenshots_are_qemu_output': True}
    def check(name, value):
        report['checks'].append({'name': name, 'passed': bool(value)})
        assert value, name
    def wait(condition, timeout=60):
        start=time.monotonic()
        while time.monotonic()-start < timeout:
            s=state()
            if s['phase']=='error': raise RuntimeError(s['error'])
            if condition(s): return s
            time.sleep(.5)
        raise TimeoutError(str(s))
    def screenshot(name): (OUT/name).write_bytes(get('/api/frame'))
    try:
        s=wait(lambda s:s['phase']=='running' and s.get('device_evidence',{}).get('processed_buffer_scanned'),240)
        report['session']=s['session']; report['initial_state']=s
        print('Photo UI ready: '+s['session'],flush=True)
        check('native0_source_dimensions',s['raw_input']['width']==2780 and s['raw_input']['height']==932)
        check('native0_actual_dma',s['raw_input']['guest_frames_transferred']>0)
        check('functional_isp_completed',s['device_evidence']['isp_batches']>0)
        check('native_processed_source_scanned',s['device_evidence']['processed_buffer_scanned'])
        initial_image=Image.open(io.BytesIO(get('/api/frame'))).convert('RGB')
        region=(140,260,880,570)
        reference=initial_image.crop(region)
        check('photo_has_scene_detail',max(ImageStat.Stat(reference).stddev)>15)
        red_pixels=sum(1 for r,g,b in initial_image.crop((110,45,190,120)).getdata()
                       if r>180 and r>g*2 and r>b*2)
        check('native_no_card_icon_red',red_pixels>20)
        def matches_scene():
            current=Image.open(io.BytesIO(get('/api/frame'))).convert('RGB').crop(region)
            return max(ImageStat.Stat(ImageChops.difference(current,reference)).rms)<3
        token=re.search(r"const token='([^']+)'",get('/').decode()).group(1)
        def action(action,key=None):
            request=Request(URL+'/api/action',data=json.dumps(dict(action=action,key=key)).encode(),
                headers={'Content-Type':'application/json','X-Z7-Token':token})
            with urlopen(request,timeout=8) as r: item=json.load(r)
            return wait(lambda s:s['completed_action']>=item['id'] and not s['busy'])
        paused=action('pause'); screenshot('paused-viewfinder.png')
        check('pause_acknowledged',paused['phase']=='paused')
        time.sleep(.8)
        later=state()
        check('paused_image_stable',later['frame_sha256']==paused['frame_sha256'])
        check('paused_dma_stable',later['device_evidence']['raw_batches']==paused['device_evidence']['raw_batches'])
        resumed=action('resume')
        check('resume_acknowledged',resumed['phase']=='running')
        progressed=wait(lambda s:s['device_evidence']['isp_batches']>paused['device_evidence']['isp_batches'])
        check('resume_processing_continues',progressed['device_evidence']['raw_batches']>paused['device_evidence']['raw_batches'])
        print('Pause/resume passed',flush=True)
        if args.menu:
            for cycle in range(1,4):
                print(f'Checking native MENU roundtrip {cycle}',flush=True)
                menu=action('key','menu')
                wait(lambda s:not matches_scene(),30)
                time.sleep(2)
                screenshot(f'menu-{cycle}.png')
                check(f'menu_{cycle}_visible',not matches_scene())
                before=state()['device_evidence']['isp_batches']
                # MENU can first move focus from an item to the sidebar.
                # Two presses at most are needed to close that native page.
                returned=None
                for attempt in range(2):
                    action('key','menu')
                    try:
                        returned=wait(lambda s:s['device_evidence']['isp_batches']>before+5
                                      and matches_scene(),12)
                        break
                    except TimeoutError:
                        pass
                check(f'menu_{cycle}_returned_processed_photo',returned is not None)
                check(f'menu_{cycle}_same_session',returned['session']==report['session'])
                screenshot(f'returned-viewfinder-{cycle}.png')
        screenshot('viewfinder.png')
        report['final_state']=state()
        check('returned_to_running_guest',report['final_state']['phase']=='running')
        report['menu_exercised']=args.menu
        report['menu_visual_verification']='three returns match reference scene ROI; continued ISP batches' if args.menu else 'not exercised'
    except Exception as error:
        report['error']=repr(error)
    (OUT/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'checks':len(report['checks']),'error':report.get('error')},ensure_ascii=False),flush=True)
    return int('error' in report)

if __name__=='__main__': raise SystemExit(main())
