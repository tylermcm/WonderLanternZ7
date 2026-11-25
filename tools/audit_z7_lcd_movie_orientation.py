"""Cumulative API72 display + movie orientation startup integration (MIT).

Compiled initialization/menu/worker and movie shadows execute. File/GUI/kernel,
pose, cache services and incoming mux idle state are supplied. Physical task
quiescence, native scheduling and camera behavior remain unverified.
"""
import argparse,hashlib,json
from pathlib import Path
from audit_z7_movie_shadows import MovieFixture,SLOT,CONTROL
from audit_z7_combined_display import CombinedFixture
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output

class CumulativeFixture(MovieFixture,CombinedFixture):
    pass


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256'] and hashlib.sha256(packet).hexdigest()==m['module_sha256']
    assert m['configuration']['movie_orientation'] and m['configuration']['photo_highlights']
    checks=[]
    def check(n,good):
        assert good,n
        checks.append(n)
    for case in ('idle','recording','active-task','uninitialized-task','pending-open','pending-close','foreign-callback','foreign-control'):
        f=CumulativeFixture(raw,h,packet,m);f.record_code_cache=True
        f.write(0xa181503c,0)  # Supplied initialized idle state, not ROM state3.
        if case=='recording':f.write(CONTROL,1)
        if case=='active-task':f.write(0xa181503c,1)
        if case=='uninitialized-task':f.write(0xa181503c,3)
        if case=='pending-open':f.write(CONTROL+0x50,1)
        if case=='pending-close':f.write(CONTROL+0x64,1)
        if case=='foreign-callback':f.write(SLOT,0x1027e799)
        if case=='foreign-control':f.write(0xa1815030,0)
        original=f.read(SLOT)
        f.load()
        check(case+'-display-initialization-succeeds',f.words()[10]==8)
        check(case+'-menu-and-display-hooks-published',f.words()[23]==1 and f.words()[41]==1)
        installed=f.value('z7_movie_installed')
        check(case+'-movie-guard-result',installed==int(case=='idle'))
        if installed:
            callback=f.read(SLOT)
            check('movie-published-pointer-owned-by-module',f.base<=callback<f.base+m['image_bytes']+m['bss_bytes'])
            check('movie-all-code-buffers-cleaned',len(f.cache_cleans)==3)
            before=f.opens;f.call(callback,1)
            check('cumulative-published-movie-open-wrapper-runs',f.opens==before+1)
            f.action(1,5)
            check('cumulative-highlight-menu-still-opens',f.value('z7_settings_view')==4)
            check('cumulative-highlight-default-remains-off',f.preferences()[11:]==(0,1))
        else:
            check(case+'-native-callback-preserved',f.read(SLOT)==original and not f.cache_cleans)
        check(case+'-initialization-does-not-write-settings',not any(e[0] in ('create','write') for e in f.file_events))
    result=dict(passed=True,count=len(checks),checks=checks,module_sha256=m['module_sha256'],
        api_minimum=72,physical_task_quiescence_verified=False,camera_access=False,
        incoming_mux_state_supplied=True,cache_clean_services_supplied=True,scope=__doc__)
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
