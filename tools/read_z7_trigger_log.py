"""Decode A:\\Z7TRIG.DAT written by the shutter-sound trigger probe module (MIT).

Prints per-callback event counts and the time-ordered ring (worker ticks), with
Silent photography (property 0x576) changes. Reads v1 logs (128-entry wrapping
ring) and v2 logs (512-entry non-wrapping ring, capture events capped at 24 per
kind, display-update stamps). Read-only; pass a copied file.
"""
import argparse,json,struct
from pathlib import Path

MAGIC,VERSION,SLOTS,EVENTS,RING=0x47495254,2,3,24,512
SIZE=128+SLOTS*EVENTS*8+RING*20
V1_RING=128;V1_SIZE=64+SLOTS*EVENTS*8+V1_RING*16
PER_EVENT=24
SLOT_NAMES=('capture-controller-0xA18D1BD8','capture-consumer-0xA18D1BDC','still-file-0xA18D2750','silent-photography-0x576',
            'exif-orientation-pose','af-shortcut','playback-rotation')


def parse(blob):
    v1=len(blob)==V1_SIZE
    if len(blob) not in (SIZE,V1_SIZE):raise ValueError(f'expected {SIZE} or {V1_SIZE} bytes, got {len(blob)}')
    head=struct.unpack_from('<32I' if not v1 else '<16I',blob,0)
    magic,version,size,sequence,ticks,mask,silent,dropped=head[:8]
    if magic!=MAGIC or version!=(1 if v1 else VERSION) or size!=len(blob):raise ValueError('not a Z7TRIG v1/v2 log')
    calls=list(head[8:11]);ring_next,writes=head[11],head[12]
    sound=None
    if head[13]>>24&1:  # field-test module: sound counters in reserved words
        sound=dict(preview={0:'not yet',1:'queued',2:'refused (service busy)',4:'no clip installed'}.get(head[13]&0xff,head[13]&0xff),
                   installed=bool(head[13]>>8&0xff),wav_loaded=bool(head[13]>>16&1),
                   starts=head[14]&0xffff,rejects=head[14]>>16,finished=head[15]&0xffff,native_passthrough=head[15]>>16,
                   exif_orientation_installed=bool(head[13]>>25&1))
        if head[13]>>26&1:sound['preview']='none (capture-trigger test, no boot chime)'
    extra=None
    if not v1:
        extra=dict(stamp=head[16],ring_dropped=head[17],capped=head[18],exif_writes=head[19],exif_inverted=head[20],playback_reports=head[21])
        if head[13]>>26&1:  # capture-trigger test module: trigger counters
            extra.update(trigger_seen=head[22],trigger_silent=head[23],trigger_queued=head[24],trigger_busy=head[25])
    counts_at=64 if v1 else 128;ring_at=counts_at+SLOTS*EVENTS*8
    counts=[]
    for s_ in range(SLOTS):
        row={}
        for i in range(EVENTS):
            event,count=struct.unpack_from('<2I',blob,counts_at+(s_*EVENTS+i)*8)
            if event or count:row[f'0x{event:08X}']=count
        counts.append(row)
    ring=[]
    if v1:
        entries=[struct.unpack_from('<4I',blob,ring_at+16*i)+(0,) for i in range(V1_RING)]
        first=max(0,ring_next-V1_RING);indices=range(first,ring_next)
    else:
        entries=[struct.unpack_from('<5I',blob,ring_at+20*i) for i in range(RING)]
        first=0;indices=range(min(ring_next,RING))
    for n in indices:
        event,tick_slot,w0,w1,stamp=entries[n%len(entries)]
        ring.append(dict(index=n,tick=tick_slot>>8,stamp=stamp,slot=SLOT_NAMES[tick_slot&0xff] if (tick_slot&0xff)<len(SLOT_NAMES) else tick_slot&0xff,
                         event=f'0x{event:08X}',word0=f'0x{w0:08X}',word1=f'0x{w1:08X}'))
    return dict(version=1 if v1 else 2,sequence=sequence,writes=writes,ticks=ticks,installed_mask=mask,
                installed=[SLOT_NAMES[i] for i in range(SLOTS) if mask>>i&1],silent_photography=silent,
                dropped_event_kinds=dropped,calls=dict(zip(SLOT_NAMES,calls)),counts=dict(zip(SLOT_NAMES,counts)),
                ring_total=ring_next,ring_lost=first if v1 else max(0,ring_next-RING),ring=ring,sound=sound,extra=extra)


def candidates(log,photos):
    """Rank (callback, event) pairs as trigger candidates for a session with a
    known number of photos. A candidate matches when its exact total count (v2
    counts are never capped) or its distinct packet records (kind bits ignored,
    as the still-file policy does) equal the photo count. When the log has EXIF
    writer entries (one per saved photo), near_photos counts how many of the
    candidate's logged stamps fall within WINDOW display updates before one."""
    WINDOW=120
    photo_stamps=[e['stamp'] for e in log['ring'] if e['slot']=='exif-orientation-pose' and e['stamp']]
    rows={}
    for e in log['ring']:
        if e['slot'] in ('silent-photography-0x576','exif-orientation-pose','af-shortcut','playback-rotation'):continue
        k=(e['slot'],e['event']);r=rows.setdefault(k,dict(callback=e['slot'],event=e['event'],count=0,records=set(),ticks=[],stamps=[]))
        r['count']+=1;r['records'].add(int(e['word0'],16)&0x7fffffe0);r['ticks'].append(e['tick']);r['stamps'].append(e['stamp'])
    for slot,row in log['counts'].items():
        for event in row:
            rows.setdefault((slot,event),dict(callback=slot,event=event,count=0,records=set(),ticks=[],stamps=[]))
    out=[]
    for (slot,event),r in rows.items():
        total=log['counts'].get(slot,{}).get(event,r['count'])
        records=len(r['records']-{0})
        clusters=1+sum(1 for a,b in zip(r['ticks'],r['ticks'][1:]) if b-a>2) if r['ticks'] else 0
        near=sum(1 for t in r['stamps'] if t and any(0<=p-t<=WINDOW for p in photo_stamps))
        match=photos is not None and (total==photos or records==photos)
        out.append(dict(callback=r['callback'],event=r['event'],count=r['count'],total=total,distinct_records=records,
                        clusters=clusters,near_photos=near,matches_photos=match))
    return sorted(out,key=lambda r:(not r['matches_photos'],abs(r['total']-(photos or 0)),r['callback'],r['event']))


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
    if r['extra']:print('v2:',', '.join(f'{k}={v}' for k,v in r['extra'].items()))
    for e in r['ring']:print(f"t={e['tick']:5d} u={e['stamp']:7d} {e['slot']:<34} {e['event']} {e['word0']} {e['word1']}")
    for c in r.get('candidates',[]):
        print(('MATCH ' if c['matches_photos'] else '      ')+f"{c['callback']:<34} {c['event']} total={c['total']} records={c['distinct_records']} near_photos={c['near_photos']}")


if __name__=='__main__':main()
