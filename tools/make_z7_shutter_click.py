"""Write a deterministic synthetic shutter click as SHUTTER1.WAV (MIT).

Two short decaying noise transients (opening and closing curtain) 45 ms apart,
48 kHz 16-bit mono, 0.12 s, peak about -3 dBFS. Generated from a fixed
pseudo-random sequence, so the bytes are the same on every run; no recorded
sound and no third-party audio. Short enough that a burst frame finds the
sound service idle again. Stdlib only. Output must be a new file under .private.
"""
import argparse,hashlib,json,math,struct
from pathlib import Path
from prepare_flash_review import require_private_output

RATE=48000
LENGTH=0.12
PEAK=0.7
CLICKS=((0.000,1.0,0.006),(0.045,0.75,0.009))  # (start s, gain, decay s)


def noise():
    state=0x2545F491
    while True:
        state^=(state<<13)&0xffffffff;state^=state>>17;state^=(state<<5)&0xffffffff
        yield (state&0xffff)/32768.0-1.0


def samples():
    n=int(RATE*LENGTH);out=[0.0]*n;source=noise()
    for start,gain,decay in CLICKS:
        first=int(start*RATE);previous=0.0
        for i in range(int(decay*8*RATE)):
            t=i/RATE
            raw=next(source)
            previous=0.55*previous+0.45*raw  # gentle low-pass for a duller click
            body=0.35*math.sin(2*math.pi*180*t)*math.exp(-t/(decay*2))
            v=gain*math.exp(-t/decay)*(previous+body)
            if first+i<n:out[first+i]+=v
    fade=int(0.004*RATE)
    for i in range(fade):out[n-1-i]*=i/fade
    scale=PEAK/max(abs(v) for v in out)
    return [int(round(v*scale*32767)) for v in out]


def wav(values):
    data=struct.pack('<%dh'%len(values),*values)
    fmt=struct.pack('<HHIIHH',1,1,RATE,RATE*2,2,16)
    body=b'WAVE'+b'fmt '+struct.pack('<I',len(fmt))+fmt+b'data'+struct.pack('<I',len(data))+data
    return b'RIFF'+struct.pack('<I',len(body))+body


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True,help='New private directory')
    a=p.parse_args();out=require_private_output(a.output)
    if out.exists():p.error('Choose a new private output directory')
    values=samples();blob=wav(values);again=wav(samples())
    assert blob==again
    out.mkdir(parents=True);(out/'SHUTTER1.WAV').write_bytes(blob)
    meta=dict(kind='synthetic-shutter-click',rate=RATE,channels=1,bits=16,seconds=LENGTH,frames=len(values),
              bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest(),peak=max(abs(v) for v in values),reproducible=True)
    (out/'clip.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(meta))


if __name__=='__main__':main()
