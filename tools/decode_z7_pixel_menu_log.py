"""Decode independent Z7 pixel-menu v4/v5 logs (MIT); reads files only."""
import argparse
import json
import struct
from pathlib import Path


def decode(data):
    if len(data)<8:raise ValueError('truncated pixel log')
    magic,version=struct.unpack_from('<2I',data)
    if version==4:words,capacity,keys=46,512,32
    elif version==5:words,capacity,keys=329,4608,288
    else:raise ValueError('unsupported pixel log version')
    if len(data)!=words*4+capacity*56:raise ValueError('expected a complete pixel-menu log')
    header=struct.unpack_from('<'+'I'*words,data)
    if magic!=0x564d5637 or header[2]>capacity or header[12]>keys:
        raise ValueError('invalid pixel-menu log header')
    names={0:'armed',1:'move_sent',2:'move_ack',3:'move_followed',4:'centre_sent',5:'centre_ack',6:'centre_followed',
           7:'normal_again',8:'timed_out',9:'gave_up',10:'done',11:'restore_sent',12:'restore_callback',13:'restored',
           18:'hold_lost',19:'series_complete',20:'position_missed',22:'fired',23:'refused',24:'frame_failed',
           25:'touched_or_cancelled',26:'button_not_freed',27:'slot_busy',30:'unexpected_or_repeated_file_key'}
    entries=[]
    for n in range(header[2]):
        offset=words*4+n*56
        tick,phase,poll,status=struct.unpack_from('<IBBH',data,offset)
        if version==5:poll=struct.unpack_from('<H',data,offset+50)[0]
        telemetry=data[offset+8:offset+50]
        entry=dict(tick=tick,phase=phase,poll=poll,status=status)
        if phase in (1,3,4,5,6) and not status:
            entry.update(state=telemetry[34],target=struct.unpack_from('<3h',telemetry),measured=struct.unpack_from('<3h',telemetry,36))
        entries.append(entry)
    result=dict(version=version,flags=[name for bit,name in names.items() if header[3]&(1<<bit)],
                frames=header[12],file_keys=list(header[14:14+header[12]]),entries_used=header[2],
                sends=header[4],refused=header[5],timeouts=header[6],entries=entries)
    if version==5:
        if any(not key for key in result['file_keys']) or len(set(result['file_keys']))!=len(result['file_keys']):
            raise ValueError('invalid or repeated file keys')
        count,shots,complete=header[302:305]
        if not 1<=count<=9 or shots not in (4,8,16,32) or complete>count or not complete*shots<=header[12]<=count*shots:
            raise ValueError('invalid exposure group metadata')
        offsets=struct.unpack_from('<9i',data,305*4)
        result['groups']=[dict(index=g,ev_sixths=offsets[g],complete=g<complete,
                               file_keys=result['file_keys'][g*shots:(g+1)*shots]) for g in range(count)]
        result['exposure']=dict(saved=list(header[314:320]),last_applied=list(header[320:326]),
                                restore_pending=header[326],job_error=header[327],setup_error=header[328],
                                keys=['mode','Auto ISO','ISO (Sv24)','aperture (Av24)','shutter special mode','shutter (Tv24)'])
        for name in ('saved','last_applied'):
            if result['exposure'][name][5]&0x80000000:result['exposure'][name][5]-=1<<32
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('log',type=Path);p.add_argument('--output',type=Path)
    a=p.parse_args();result=decode(a.log.read_bytes())
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='entries'}))


if __name__=='__main__':main()
