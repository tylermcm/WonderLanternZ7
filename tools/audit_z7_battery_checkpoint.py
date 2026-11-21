"""Battery-only startup/activation boundary on the exact installed host (MIT).

Kernel/filesystem, incoming GUI/telemetry and selected rendering services are
supplied. No hardware acceptance, durable write or recovery proof is claimed.
"""
import argparse
import hashlib
import json
from pathlib import Path

from unicorn import UC_HOOK_MEM_WRITE
from audit_z7_battery_percent import AutomaticFixture
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output


def audit(raw,host,packet,module):
    if hashlib.sha256(raw).hexdigest()!=host['main_payload_sha256']:
        raise ValueError('Host mismatch')
    if hashlib.sha256(packet).hexdigest()!=module['module_sha256']:
        raise ValueError('Module mismatch')
    assert module['configuration']['battery_percent_enabled']
    assert not any(n.startswith(('sm_','persistence_','z7_settings_','preset_','focal_')) for n in module['symbols'])
    f=AutomaticFixture(raw,host,packet)
    # These installed-host locations must never be changed by this candidate.
    watched=(0xa1833548,0xa182ed34,0xa1836f8c,0xa1829b0c)
    snapshots={a:bytes(f.u.mem_read(a,44 if a in (0xa1833548,0xa1836f8c) else 4)) for a in watched}
    native_stores=[]
    def write(u,access,address,size,value,context):
        if not STATE<=address<STATE+host['state_bytes']:
            native_stores.append((hex(address),size))
    handle=f.u.hook_add(UC_HOOK_MEM_WRITE,write,begin=0xa1800000,end=0xbfffffff)
    status=f.call(host['symbols']['z7_module_load_once'],STATE)
    f.u.hook_del(handle)
    assert status==8 and not native_stores
    assert not f.getter_calls and not f.labels and not f.list_calls
    words=f.words();base=words[12]
    assert words[22:24]==(1,1)
    assert words[24:26]==(1,32) and words[26:30]==(0,)*4 and words[30] and words[31]
    assert words[32:52]==(0,)*20
    assert all(bytes(f.u.mem_read(a,len(data)))==data for a,data in snapshots.items())
    # Explicit early-state input, not a full scheduler/preemption simulation.
    f.setword(92,0)
    f.call(host['symbols']['z7_display_before_paint'])
    f.call(host['symbols']['z7_display_after_paint'])
    assert not f.getter_calls and not f.labels and not f.list_calls
    f.setword(92,1)
    # Missing HUD pool must be a no-op, with no battery-getter wait.
    old=bytes(f.u.mem_read(0xa201e3ac,4));f.u.mem_write(0xa201e3ac,bytes(4))
    f.call(host['symbols']['z7_display_before_paint'])
    f.call(host['symbols']['z7_display_after_paint'])
    assert not f.getter_calls and not f.labels and not f.list_calls
    f.u.mem_write(0xa201e3ac,old)
    f.call(host['symbols']['z7_display_before_paint'])
    f.call(host['symbols']['z7_display_after_paint'])
    assert f.labels==[('63%',299)] and f.getter_calls==1 and len(f.list_calls)==1
    assert all(bytes(f.u.mem_read(a,len(data)))==data for a,data in snapshots.items())
    assert int.from_bytes(f.u.mem_read(base+module['symbols']['z7_battery_samples'],4),'little')==1
    return dict(native_load_status=status,init_native_ram_store_count=len(native_stores),
                init_getter_or_render_calls=0,only_before_after_paint_registered=True,
                custom_menu_dispatch_grid_and_key_unchanged=True,
                early_host_not_ready_noop=True,missing_hud_pool_noop=True,
                eligible_gui_percent_label='63%',eligible_gui_getter_calls=1,
                settings_io_linked=False,worker_linked=False,card_written=False,
                hardware_verified=False,physical_battery_accuracy_verified=False,
                limits=['Host ready=0 is supplied explicitly, not a complete scheduler model',
                        'GUI pool, battery snapshot/mutex and selected render services supplied',
                        'Physical cold startup, camera control responsiveness and recovery unverified'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('host','module','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    host=json.loads((a.host/'module-host.emulator.json').read_text(encoding='utf-8'))
    module=json.loads((a.module/'module.json').read_text(encoding='utf-8'))
    report=audit((a.host/'module-host.emulator.main.bin').read_bytes(),host,(a.module/'Z7APP.BIN').read_bytes(),module)
    report.update(module_sha256=module['module_sha256'],host_main_sha256=host['main_payload_sha256'],
                  source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':main()
