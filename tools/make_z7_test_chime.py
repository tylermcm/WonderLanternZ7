"""Write the deterministic shutter-sound smoke-test clip SHUTTER1.WAV (MIT).

A rising two-note chime (C6 then G6), 48 kHz 16-bit mono, 0.45 s, peak about
-6 dBFS. It is deliberately unlike any Nikon beep or the mechanical shutter, so
hearing it on the camera can only mean the module played it. Stdlib only; the
same bytes on every run. Output must be a new file under .private.
"""
import argparse,hashlib,json,math,struct
from pathlib import Path
from prepare_flash_review import require_private_output

RATE=48000
NOTES=((1046.50,0.000,0.200),(1567.98,0.150,0.300))  # (Hz, start s, length s)
LENGTH=0.45
PEAK=0.5


def samples():
    n=int(RATE*LENGTH);out=[0.0]*n
    for freq,start,length in NOTES:
        first=int(start*RATE)
        for i in range(int(length*RATE)):
            t=i/RATE
            envelope=min(1.0,t/0.004)*math.exp(-t/(length*0.35))
            tone=math.sin(2*math.pi*freq*t)+0.25*math.sin(4*math.pi*freq*t)
            if first+i<n:out[first+i]+=envelope*tone
    fade=int(0.010*RATE)
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
    values=samples();blob=wav(values)
    assert blob==wav(samples())
    out.mkdir(parents=True);(out/'SHUTTER1.WAV').write_bytes(blob)
    meta=dict(file='SHUTTER1.WAV',bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest(),rate=RATE,channels=1,bits=16,
              frames=len(values),seconds=len(values)/RATE,peak=max(abs(v) for v in values),notes_hz=[n[0] for n in NOTES])
    (out/'clip.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(meta))


if __name__=='__main__':main()
