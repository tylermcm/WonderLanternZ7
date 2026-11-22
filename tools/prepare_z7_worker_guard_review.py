"""Freeze a private worker-host update assessment; no card/camera access (MIT)."""
import argparse
import binascii
import hashlib
import json
from pathlib import Path
from build_z7_module import ROOT
from prepare_flash_review import (inspect_container,reviewed_candidate,storage_descriptor,
                                 probe_header,probe_filename,require_private_output)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','pair','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    raw=(ROOT/'.private/stock/Z_7_0380.bin').read_bytes();stock,container=inspect_container(raw)
    candidate,h=reviewed_candidate(a.host,'lcd-first-release',raw,stock)
    old=(ROOT/'.private/builds/20261121-lcd-core-host-01/module-host.emulator.eg.bin').read_bytes()
    sha=lambda b:hashlib.sha256(b).hexdigest()
    assert sha(old)=='fa709dba7eb7a9addc8bd5b90f839edd578cfb6d4bb0df87a1cd8cb4a7beaa4d' and binascii.crc_hqx(old,0)==0
    assert sha(candidate)==h['sha256'] and binascii.crc_hqx(candidate,0)==0
    capacity=storage_descriptor(stock);assert len(candidate)<=capacity
    checks=[]
    for name,data in (('stock',stock),('candidate',candidate),('previous-host',old)):
        for extended in (0,1):
            assert probe_header(stock,data,capacity,extended_version=extended)['result']==1
            checks.append(name+'-header-'+str(extended))
    assert probe_header(stock,stock,capacity,reported_size=capacity+1)['result']==11;checks.append('oversize-rejected')
    assert probe_header(stock,stock[:40],capacity)['result']==13;checks.append('short-header-rejected')
    for name,expected in (('EG161080.BIN',True),('eg161080.bin',True),('EG16100380.BIN',False),('EG162080.BIN',False),('EG161080.BIN.extra',False),('EG1610.BIN',False)):
        assert probe_filename(stock,name)==expected;checks.append('filename-'+name)
    gates={}
    for name in ('loader','worker','display'):
        path=ROOT/f'.private/evidence/20261122-worker-task-full-{name}-01.json'
        r=json.loads(path.read_text());assert r['passed']
        assert r.get('main_sha256',r.get('main_payload_sha256'))==h['main_payload_sha256']
        gates[name]=dict(sha256=sha(path.read_bytes()),checks=len(r['checks']))
    path=ROOT/'.private/evidence/20261122-worker-task-integration-01.json';integration=json.loads(path.read_text())
    assert integration['passed'] and integration['host_main_sha256']==h['main_payload_sha256']
    gates['pair-integration']=dict(sha256=sha(path.read_bytes()),results=integration['results'])
    files={'host-only/EG161080.BIN':candidate,'previous-host/EG161080.BIN':old,
           'stock-module/EG161080.BIN':stock,'stock-container/Z_7_0380.bin':raw,
           'host-only/host.json':(a.host/'module-host.emulator.json').read_bytes(),
           'assessment.md':(ROOT/'WORKER_GUARD_HOST_ASSESSMENT.md').read_bytes()}
    for name in ('disabled','enabled'):
        for file in ('Z7APP.BIN','module.json'):
            files[f'controls/{name}/{file}']=(a.pair/name/file).read_bytes()
        assert sha(files[f'controls/{name}/Z7APP.BIN'])==integration['results'][name]['module_sha256']
    report=dict(schema=1,purpose='Exact offline review; no staging or flash authorization',
                model='Original Nikon Z7',firmware_base='C 3.80',host_sha256=sha(candidate),main_sha256=h['main_payload_sha256'],
                host_bytes=len(candidate),host_code_sha256=h['host_sha256'],host_code_bytes=h['host_bytes'],
                previous_host_sha256=sha(old),stock_container_sha256=sha(raw),container=container,
                descriptor_capacity=capacity,eg_crc_zero=True,independently_rebuilt=True,
                software_gates=gates,native_admission_checks=checks,
                first_stage='EG161080.BIN only; every SD module disabled; no active Z7APP.BIN',
                subsequent_controls_require_owner_results=True,
                stage_authorized=False,flash_authorized=False,installation_cleared=False,
                card_written=False,physical_fix_verified=False,installed_image_readback=False,
                recovery_physically_verified=False,
                limits=['Header/name probes supply native I/O/property boundaries; no complete updater or flash writer executed',
                        'Prior host update accepted and normal no-card boot observed; exact new update acceptance/boot unknown',
                        'Normal-menu reflash inputs preserved; no verified recovery if camera cannot boot or reach updater',
                        'Guard change does not establish safety of module atomics, restores or persistence',
                        'No unsupported camera modes or deferred release features added'],
                files={n:dict(bytes=len(b),sha256=sha(b)) for n,b in files.items()})
    out.mkdir(parents=True)
    for n,b in files.items():
        path=out/n;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as f:f.write(b)
        assert path.read_bytes()==b
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(host_sha256=sha(candidate),host_bytes=len(candidate),native_checks=len(checks),stage_authorized=False,flash_authorized=False)))


if __name__=='__main__':main()
