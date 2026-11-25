"""Turn a shutter-sound field-test log (Z7TRIG.DAT) into verdicts (MIT).

Answers the session's three questions from the card log alone:
  1. Did the chime play? (queued / started / rejected / finished counters)
  2. Which callback event is one-per-photo? (candidate ranking by distinct photo
     records, see read_z7_trigger_log.candidates)
  3. Does the camera report pose 3 for the upside-down photo? (EXIF pose log)
Read-only; pass a copied file. --json for machine output.
"""
import argparse,json
from pathlib import Path
from read_z7_trigger_log import parse,candidates


def chime(sound):
    if not sound:return 'not a field-test log'
    if not sound['wav_loaded']:return 'SHUTTER1.WAV was not loaded (missing or not 48 kHz 16-bit, at most 1 s)'
    if not sound['installed']:return 'WAV loaded but the playback intercept was not installed'
    if sound['preview']=='not yet':return 'log ended before the preview tick (power-off too early?)'
    if sound['preview']!='queued':return f"preview not queued: {sound['preview']}"
    if sound['finished']:return 'played to the end: the SD-module playback path works'
    if sound['rejects']:return 'queued but rejected at start (speaker/second check or a setter refused)'
    if sound['starts']:return 'started (DMA programmed) but no finish event was logged'
    return 'queued but the start handler never ran'


def exif(log):
    poses=[int(e['event'],16)&0xffff for e in log['ring'] if e['slot']=='exif-orientation-pose']
    if not log.get('sound') or not log['sound'].get('exif_orientation_installed'):return poses,'EXIF component not installed'
    if not poses:return poses,'no photo went through the Orientation writer'
    if 3 in poses:return poses,'camera reports pose 3: upside-down photos get Orientation 3'
    return poses,'no pose 3 seen: an upside-down photo was recorded with another pose (roll angles needed)'


def analyze(blob,photos):
    log=parse(blob)
    ranked=candidates(log,photos) if photos is not None else []
    matches=[c for c in ranked if c['matches_photos']]
    poses,exif_verdict=exif(log)
    if photos is None:trigger='pass --photos N to rank trigger candidates'
    elif len(matches)==1:trigger=f"{matches[0]['event']} on {matches[0]['callback']} matches {photos} photos"
    elif matches:trigger=f'{len(matches)} candidates match {photos} photos; check their timing against the session'
    else:trigger=f'no event matched {photos} distinct photo records'
    return dict(chime=chime(log['sound']),trigger=trigger,exif=exif_verdict,exif_poses=poses,candidates=ranked,
                silent_markers=[int(e['event'],16)&0xffff for e in log['ring'] if e['slot']=='silent-photography-0x576'],
                ring_lost=log['ring_lost'],ticks=log['ticks'],sound=log['sound'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('log',type=Path)
    p.add_argument('--photos',type=int,help='Photos taken (field test: 1 + 1 + burst + 1 upside down)')
    p.add_argument('--json',action='store_true')
    a=p.parse_args();r=analyze(a.log.read_bytes(),a.photos)
    if a.json:print(json.dumps(r,indent=2));return
    print('Chime:  ',r['chime']);print('Trigger:',r['trigger']);print('EXIF:   ',r['exif'],r['exif_poses'])
    if r['ring_lost']:print(f"note: {r['ring_lost']} older events fell out of the 128-entry ring")
    for c in r['candidates'][:6]:
        print(('  MATCH ' if c['matches_photos'] else '        ')+f"{c['callback']:<32} {c['event']} count={c['count']} records={c['distinct_records']}")


if __name__=='__main__':main()
