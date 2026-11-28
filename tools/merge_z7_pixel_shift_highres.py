"""Independent 16/32-shot half-pixel raw interlacing (MIT).

Called by merge_z7_pixel_shift.py. Accumulation is disk-backed and exports
in strips so a 180 MP image does not require keeping every NEF in memory.
Hardware calibration of the Z7's half-step positions is still pending.
"""
import json
import struct
from pathlib import Path
import numpy as np
import rawpy
from PIL import Image
from merge_z7_pixel_shift import load, illumination_levels, illumination_gains, illumination_field, expand_field, translate_plane


def interlace_scaled(acc, counts, lin, pattern, shift, quantized, margin, gains, field=None, scale=2):
    """Interlace each CFA lattice on the doubled output coordinate grid."""
    my, mx = margin
    dx, dy = quantized
    stride = 2 * scale
    for sy, sx in np.ndindex(2, 2):
        code = int(pattern[sy, sx]); channel = 1 if code == 3 else code
        ox = (scale * sx - dx - scale * mx) % stride
        oy = (scale * sy - dy - scale * my) % stride
        plane = lin[sy::2, sx::2]
        plane = plane * (expand_field(field[channel], plane.shape) if field is not None else gains[channel])
        plane = translate_plane(plane, (shift[0] - dx / scale) / 2, (shift[1] - dy / scale) / 2)
        x0 = (scale * mx + ox + dx - scale * sx) // stride
        y0 = (scale * my + oy + dy - scale * sy) // stride
        target = acc[oy::stride, ox::stride, channel]
        target += plane[y0:y0 + target.shape[0], x0:x0 + target.shape[1]]
        counts[oy, ox, channel] += 1


def write_rows(path, shape, rows):
    """Baseline uncompressed RGB16 TIFF, streaming rows (less than 4 GiB)."""
    h, w, _ = shape
    size = h * w * 6
    if size + 140 >= 2**32:
        raise ValueError('image needs BigTIFF')
    entries = [(256,4,1,w),(257,4,1,h),(258,3,3,134),(259,3,1,1),(262,3,1,2),
               (273,4,1,140),(277,3,1,3),(278,4,1,h),(279,4,1,size),(284,3,1,1)]
    header = bytearray(b'II*\0' + struct.pack('<IH',8,len(entries)))
    for tag, typ, n, val in entries:
        header += struct.pack('<HHIHH',tag,typ,n,val,0) if typ==3 and n==1 else struct.pack('<HHII',tag,typ,n,val)
    header += struct.pack('<I3H',0,16,16,16)
    with Path(path).open('wb') as f:
        f.write(header)
        written = 0
        for row in rows:
            data = np.ascontiguousarray(row, dtype='<u2').tobytes()
            written += len(data); f.write(data)
        if written != size:
            raise ValueError('TIFF row count does not match dimensions')


def run(a, parser):
    files = a.photos
    if a.alignment != 'subpixel':
        parser.error('16/32-shot half-step sets require --alignment subpixel')
    if a.shifts:
        shifts = [(0.,0.)] + [tuple(float(v) for v in s.split(',')) for s in a.shifts.split(';')]
    else:
        if a.shift_report:
            saved = json.loads(a.shift_report.read_text(encoding='utf-8'))
            if saved['reference'] != files[0].name or any([r['photo'] for r in rows] != [f.name for f in files[1:]] for rows in saved['planes'].values()):
                parser.error('shift report does not match the input order')
            res = saved['planes']
        else:
            from measure_z7_raw_shift import measure
            res = measure(files)
        shifts = [(0.,0.)] + [tuple(np.median([[r[k]['dx'],r[k]['dy']] for r in res.values()],axis=0)) for k in range(len(files)-1)]
    if len(shifts) != len(files) or any(len(v)!=2 for v in shifts) or not np.isfinite(shifts).all():
        parser.error('one finite dx,dy pair is required for every non-reference frame')
    quantized = [(int(round(x*2)),int(round(y*2))) for x,y in shifts]
    if any(max(abs(x-qx/2),abs(y-qy/2)) > .20 or max(abs(x),abs(y)) > 1.75 for (x,y),(qx,qy) in zip(shifts,quantized)):
        parser.error('half-step set has excessive position errors; inspect the capture')
    phases = [(x%4,y%4) for x,y in quantized]
    if len(set(phases))!=16 or any(phases.count(p)!=len(files)//16 for p in set(phases)):
        parser.error('16/32 shots must cover all sixteen half-step colour phases equally')
    first, lin, info = load(files[0]); h,w=lin.shape
    my,mx=info['crop_margin']; ch,cw=info['crop_size']
    shape=(ch*2,cw*2,3)
    work=a.output/'accumulator.work'
    if work.exists():
        parser.error('output contains an accumulator from an earlier run; choose a fresh output folder')
    counts=np.zeros((4,4,3),np.uint16)
    acc=np.memmap(work,mode='w+',dtype=np.float32,shape=shape)
    acc[:]=0
    ref_levels=illumination_levels(lin,info['pattern']); frame_gains=[]
    for k,photo in enumerate(files):
        r,current,meta=(first,lin,info) if not k else load(photo)
        try:
            if current.shape!=(h,w) or not np.array_equal(info['pattern'],meta['pattern']):
                parser.error('raw dimensions and CFA pattern must match')
            levels=illumination_levels(current,meta['pattern'])
            gains=illumination_gains(ref_levels,levels) if a.photometric!='none' else [1.,1.,1.]
            field=illumination_field(ref_levels,levels,gains) if a.photometric=='local' else None
            interlace_scaled(acc,counts,current,meta['pattern'],shifts[k],quantized[k],(my,mx),gains,field)
            frame_gains.append(gains)
        finally:
            if k:r.close()
        if k:del current
        print('interlaced %d/%d' % (k+1,len(files)),flush=True)
    if (counts==0).any():
        raise ValueError('incomplete output colour lattice')
    for y in range(0,shape[0],64):
        tile=acc[y:y+64]
        tile/=counts[np.arange(y,y+len(tile))[:,None]%4,np.arange(shape[1])[None,:]%4]
    single=first.postprocess(demosaic_algorithm=rawpy.DemosaicAlgorithm.AHD,gamma=(1,1),no_auto_bright=True,
                             output_bps=16,use_camera_wb=True,output_color=rawpy.ColorSpace.sRGB,user_flip=0)
    first.close();del lin
    if single.shape[:2]==(h,w):single=single[my:my+ch,mx:mx+cw]
    if single.shape[:2]!=(ch,cw):raise ValueError('LibRaw reference crop does not match')
    wb=info['wb']/info['wb'][1]
    sample=(acc[::8,::8]*wb)@info['cam'].T
    reference=single[::4,::4].astype(np.float32)/65535
    colour_gains=np.array([np.median(reference[...,c])/max(np.median(sample[...,c]),1e-9) for c in range(3)],np.float32)
    exposure=.9/max(float(np.percentile(reference,99.5)),1e-6)
    def tone(x):
        x=np.clip(x*exposure,0,1)
        return np.where(x<=.0031308,12.92*x,1.055*x**(1/2.4)-.055)
    def convert(x):return tone(((x*wb)@info['cam'].T)*colour_gains)
    def rows():
        for y in range(0,shape[0],64):yield np.round(convert(acc[y:y+64])*65535).astype(np.uint16)
    write_rows(a.output/'merged.tif',shape,rows())
    write_rows(a.output/'single.tif',single.shape,(np.round(tone(single[y:y+64].astype(np.float32)/65535)*65535).astype(np.uint16) for y in range(0,ch,64)))
    preview=Image.fromarray(np.round(convert(acc[::8,::8])*255).astype(np.uint8))
    preview.save(a.output/'preview.png')
    acc.flush()
    # Windows keeps the file locked while even a small memmap view survives.
    # No accumulator/view is used after export; release the mapping explicitly.
    acc._mmap.close()
    del acc
    work.unlink()
    report=dict(photos=[p.name for p in files],measured_shifts=shifts,half_pixel_grid_shifts=quantized,
                size=[shape[1],shape[0]],scale=2,frame_gains=frame_gains,photometric=a.photometric,
                alignment='same-colour subpixel',crop_margin=[my,mx],
                outputs=['merged.tif','single.tif','preview.png'],hardware_half_steps_verified=False)
    (a.output/'merge.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))
