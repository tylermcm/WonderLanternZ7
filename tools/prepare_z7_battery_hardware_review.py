"""Freeze the exact battery-only SD candidate for owner review (MIT).

Private output only. No firmware generation, card access or test authorization.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from build_z7_module import ROOT
from prepare_flash_review import require_private_output

EXPECTED='89358992419867380781bafae7a1624f4d51955b3920127718f6daba9318ea23'
HOST='7d7356e7775db90483ed9fe5598f401afb7fb8498a7b42bd71900db849d7f057'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('module','host','policy','boundary','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT):
        raise ValueError('Checkpoint source before freezing review')
    checkpoint=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    packet=(a.module/'Z7APP.BIN').read_bytes()
    module=json.loads((a.module/'module.json').read_text(encoding='utf-8'))
    host=json.loads((a.host/'module-host.emulator.json').read_text(encoding='utf-8'))
    policy=json.loads(a.policy.read_text(encoding='utf-8'))
    boundary=json.loads(a.boundary.read_text(encoding='utf-8'))
    assert digest(packet)==module['module_sha256']==EXPECTED and len(packet)==2824
    assert module['kind']=='original-Z7-battery-percent-module'
    assert module['configuration']['battery_percent_enabled']
    assert host['main_payload_sha256']==HOST
    assert digest((a.host/'module-host.emulator.main.bin').read_bytes())==HOST
    for name,sha in module['source_inputs_sha256'].items():
        assert digest((ROOT/name).read_bytes())==sha,name
    assert policy['passed'] and all(c['passed'] for c in policy['checks'])
    assert policy['module_sha256']==boundary['module_sha256']==EXPECTED
    assert policy['main_sha256']==boundary['host_main_sha256']==HOST
    assert boundary['source_sha256']==digest((ROOT/'tools/audit_z7_battery_checkpoint.py').read_bytes())
    assert boundary['native_load_status']==8 and boundary['init_native_ram_store_count']==0
    for name in ('only_before_after_paint_registered','custom_menu_dispatch_grid_and_key_unchanged',
                 'early_host_not_ready_noop','missing_hud_pool_noop'):
        assert boundary[name],name
    assert not boundary['settings_io_linked'] and not boundary['worker_linked']
    checkpoint_evidence=ROOT/'evidence/20261121-battery-hardware-checkpoint.json'
    checks=json.loads(checkpoint_evidence.read_text(encoding='utf-8'))
    assert checks['module_sha256']==EXPECTED and checks['root_tests_passed']
    assert checks['ownership_hardening_withdrawn_and_reverted']
    files={'Z7APP.BIN':packet,'module.json':(a.module/'module.json').read_bytes(),
           'battery-policy.json':a.policy.read_bytes(),'startup-boundary.json':a.boundary.read_bytes(),
           'ASSESSMENT.md':(ROOT/'BATTERY_HARDWARE_TEST_ASSESSMENT.md').read_bytes(),
           'CHECKS.json':checkpoint_evidence.read_bytes(),
           'SOURCE_MANIFEST.json':(ROOT/'SOURCE_MANIFEST.json').read_bytes()}
    review=dict(schema=1,scope='One battery-only SD startup/GUI test on existing host',
                source_checkpoint=checkpoint,module_sha256=EXPECTED,module_bytes=len(packet),
                host_main_sha256=HOST,policy_checks=len(policy['checks']),
                ready_for_owner_review=True,stage_authorized=False,hardware_test_authorized=False,
                hardware_verified=False,firmware_image_generated=False,card_written=False,
                full_lcd_release_withdrawn=True,
                files={n:dict(bytes=len(data),sha256=digest(data)) for n,data in files.items()})
    files['review.json']=(json.dumps(review,indent=2)+'\n').encode()
    out.mkdir(parents=True,exist_ok=False)
    for name,data in files.items():
        with (out/name).open('xb') as f:f.write(data)
        assert (out/name).read_bytes()==data
    print(json.dumps(dict(output=str(out),source_checkpoint=checkpoint,
                          module_sha256=EXPECTED,files_verified=len(files),
                          stage_authorized=False,hardware_test_authorized=False)))


if __name__=='__main__':main()
