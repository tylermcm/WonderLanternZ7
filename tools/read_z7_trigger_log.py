"""Decode A:\\Z7TRIG.DAT written by the shutter-sound trigger probe module (MIT).

Prints per-callback event counts and the time-ordered ring (worker ticks), with
Silent photography (property 0x576) changes. Read-only; pass a copied file.
"""
import argparse,json,struct
from pathlib import Path

MAGIC,VERSION,SLOTS,EVENTS,RING=0x47495254,1,3,24,128
SIZE=64+SLOTS*EVENTS*8+RING*16
SLOT_NAMES=('capture-controller-0xA18D1BD8','capture-consumer-0xA18D1BDC','still-file-0xA18D2750','silent-photography-0x576',
            'exif-orientation-pose','af-shortcut','playback-rotation')


def parse(blob):
    if len(blob)!=SIZE:raise ValueError(f'expected {SIZE} bytes, got {len(blob)}')
    head=struct.unpack_from('<16I',blob,0)
    magic,version,size,sequence,ticks,mask,silent,dropped=head[:8]
    if magic!=MAGIC or version!=VERSION or size!=SIZE:raise ValueError('not a Z7TRIG v1 log')
    calls=list(head[8:11]);ring_next,writes=head[11],head[12]
    sound=None
    if head[13]>>24&1:  # field-test module: sound counters in reserved words
        sound=dict(preview={0:'not yet',1:'queued',2:'refused (service busy)',4:'no clip installed'}.get(head[13]&0xff,head[13]&0xff),
                   installed=bool(head[13]>>8&0xff),wav_loaded=bool(head[13]>>16&1),
                   starts=head[14]&0xffff,rejects=head[14]>>16,finished=head[15]&0xffff,native_passthrough=head[15]>>16,
                   exif_orientation_installed=bool(head[13]>>25&1))
    counts=[]
    for s in range(SLOTS):
        row={}
        for i in range(EVENTS):
            event,count=struct.unpack_from('<2I',blob,64+(s*EVENTS+i)*8)
            if event or count:row[f'0x{event:08X}']=count
        counts.append(row)
    entries=[struct.unpack_from('<4I',blob,64+SLOTS*EVENTS*8+16*i) for i in range(RING)]
    first=max(0,ring_next-RING)
    ring=[]
    for n in range(first,ring_next):
        event,tick_slot,w0,w1=entries[n%RING]
        ring.append(dict(index=n,tick=tick_slot>>8,slot=SLOT_NAMES[tick_slot&0xff] if (tick_slot&0xff)<len(SLOT_NAMES) else tick_slot&0xff,
                         event=f'0x{event:08X}',word0=f'0x{w0:08X}',word1=f'0x{w1:08X}'))
    return dict(sequence=sequence,writes=writes,ticks=ticks,installed_mask=mask,
                installed=[SLOT_NAMES[i] for i in range(SLOTS) if mask>>i&1],silent_photography=silent,
                dropped_event_kinds=dropped,calls=dict(zip(SLOT_NAMES,calls)),counts=dict(zip(SLOT_NAMES,counts)),
                ring_total=ring_next,ring_lost=first,ring=ring,sound=sound)


def candidates(log,photos):
    """Rank (callback, event) pairs as trigger candidates for a session with a
    known number of photos. A candidate's distinct packet records (kind bits
    ignored, as the still-file policy does) should equal the photo count, and it
    must not fire in ticks without a photo, which only the owner's notes can say."""
    rows={}
    for e in log['ring']:
        if e['slot'] in ('silent-photography-0x576','exif-orientation-pose','af-shortcut','playback-rotation'):continue
        k=(e['slot'],e['event']);r=rows.setdefault(k,dict(callback=e['slot'],event=e['event'],count=0,records=set(),ticks=[]))
        r['count']+=1;r['records'].add(int(e['word0'],16)&0x7fffffe0);r['ticks'].append(e['tick'])
    out=[]
    for r in rows.values():
        clusters=1+sum(1 for a,b in zip(r['ticks'],r['ticks'][1:]) if b-a>2)
        out.append(dict(callback=r['callback'],event=r['event'],count=r['count'],distinct_records=len(r['records']-{0}),
                        clusters=clusters,matches_photos=photos is not None and len(r['records']-{0})==photos))
    return sorted(out,key=lambda r:(not r['matches_photos'],abs(r['distinct_records']-(photos or 0)),r['callback'],r['event']))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('log',type=Path)
    p.add_argument('--json',action='store_true')
    p.add_argument('--photos',type=int,help='Photos taken in the session, to rank trigger candidates')
    a=p.parse_args();r=parse(a.log.read_bytes())
    if a.photos is not None:r['candidates']=candidates(r,a.photos)
    if a.json:print(json.dumps(r,indent=2));return
    print(f"log #{r['sequence']} after {r['ticks']} worker ticks; installed: {', '.join(r['installed']) or 'none'}")
    if r['sound']:print('sound:',', '.join(f'{k}={v}' for k,v in r['sound'].items()))
    poses=[int(e['event'],16)&0xffff for e in r['ring'] if e['slot']=='exif-orientation-pose']
    if poses:print('exif poses written (3 = upside down):',poses)
    for name,row in r['counts'].items():
        print(f'{name}: {r["calls"][name]} calls',' '.join(f'{e}x{c}' for e,c in row.items()))
    for e in r['ring']:print(f"t={e['tick']:5d} {e['slot']:<34} {e['event']} {e['word0']} {e['word1']}")
    for c in r.get('candidates',[]):
        print(('MATCH ' if c['matches_photos'] else '      ')+f"{c['callback']:<34} {c['event']} count={c['count']} records={c['distinct_records']} clusters={c['clusters']}")


if __name__=='__main__':main()
