"""Merge a 4-, 8-, 16- or 32-frame Z7 pixel-shift set (MIT).

Input: the four NEFs of a series taken at the Bayer corners (the module's
(0,0), (20,0), (20,18), (0,18) steps = image shifts of about (0,0), (-1,0),
(-1,+1), (0,+1) px). The fractional shift of each frame is measured on its raw
colour planes (tools/measure_z7_raw_shift.py) unless given with --shifts.

For each pixel of the first frame, the scene point it saw is found in every
frame at p + d_k, where that frame's colour filter has a different colour.
Together the four frames give one R, two G and one B sample per pixel, so
the merged image needs no demosaicing. Small geometric errors are corrected
by interpolating within each same-colour plane. Coarse spatial illumination
matching removes phase stripes from lighting changes between exposures.
16-shot half-pixel sets fill a doubled resolution RGB lattice; 32 shots
repeat that lattice and average it. These modes need camera calibration.
Output, all in --output:
  - merged.tif: 16-bit linear-to-sRGB-gamma RGB TIFF, full resolution;
  - single.tif: the first frame converted by LibRaw (AHD demosaic), the
    same colour pipeline, for comparison;
  - compare-*.png: crops of single vs merged side by side (2x enlarged).
Camera white balance and LibRaw's camera-to-sRGB matrix; the merge's
per-channel level is matched to LibRaw's own conversion; one exposure scale. The sensor orientation is kept (no EXIF rotation). Reads NEFs only.
"""
import argparse, json, struct
from pathlib import Path
import numpy as np
import rawpy
from PIL import Image

NAMES = {0: 'R', 1: 'G', 2: 'B', 3: 'G'}


def write_tiff16(path, rgb):
    """Minimal baseline TIFF writer: uncompressed 16-bit RGB, one strip."""
    h, w, _ = rgb.shape
    data = np.ascontiguousarray(rgb.astype('<u2')).tobytes()
    entries = [(256, 4, 1, w), (257, 4, 1, h), (258, 3, 3, None), (259, 3, 1, 1), (262, 3, 1, 2),
               (273, 4, 1, None), (277, 3, 1, 3), (278, 4, 1, h), (279, 4, 1, len(data)), (284, 3, 1, 1)]
    ifd_off = 8
    n = len(entries)
    extra_off = ifd_off + 2 + 12 * n + 4
    bps_off = extra_off
    data_off = bps_off + 6
    out = bytearray(b'II*\x00' + struct.pack('<I', ifd_off) + struct.pack('<H', n))
    for tag, typ, cnt, val in entries:
        if tag == 258: val = bps_off
        if tag == 273: val = data_off
        if typ == 3 and cnt == 1:
            out += struct.pack('<HHIHH', tag, typ, cnt, val, 0)
        else:
            out += struct.pack('<HHII', tag, typ, cnt, val)
    out += struct.pack('<I', 0) + struct.pack('<3H', 16, 16, 16)
    Path(path).write_bytes(bytes(out) + data)


def load(path):
    r = rawpy.imread(str(path))
    raw = r.raw_image_visible.astype(np.float32)
    black = np.array(r.black_level_per_channel, np.float32)
    pat = np.array(r.raw_pattern)
    blk = np.zeros_like(raw)
    for y in range(2):
        for x in range(2):
            blk[y::2, x::2] = black[pat[y, x]]
    lin = np.clip((raw - blk) / (float(r.white_level) - black.mean()), 0, None)
    # Camera -> sRGB as LibRaw builds it: cam_rgb = cam_xyz . xyz_rgb, rows normalised, inverted.
    xyz_rgb = np.array([[0.412453, 0.357580, 0.180423], [0.212671, 0.715160, 0.072169], [0.019334, 0.119193, 0.950227]])
    cam_rgb = np.array(r.rgb_xyz_matrix, np.float64)[:3, :3] @ xyz_rgb
    cam_rgb /= cam_rgb.sum(axis=1, keepdims=True)
    sizes = r.sizes
    my, mx = max(8, sizes.crop_top_margin), max(8, sizes.crop_left_margin)
    info = dict(pattern=pat, wb=np.array(r.camera_whitebalance[:3], np.float32), cam=np.linalg.inv(cam_rgb).astype(np.float32),
                crop_margin=(my, mx), crop_size=(raw.shape[0]-2*my,raw.shape[1]-2*mx))
    return r, lin, info


def illumination_levels(lin, pattern, block=32):
    """Robust same-colour patch levels, before white balance or tone mapping.

    Large patches suppress the sub-pixel scene displacement and raw noise.
    Keep the spatial samples: taking ratios before the median avoids bias
    from a changed crop, dark pixels, or one moving/bright object.
    """
    h, w = lin.shape
    out = []
    for channel in range(3):
        patches = []
        for y, x in np.ndindex(2, 2):
            if NAMES[int(pattern[y, x])] != 'RGB'[channel]:
                continue
            a = lin[y::2, x::2]
            ph, pw = a.shape[0] // block, a.shape[1] // block
            a = a[:ph * block, :pw * block]
            patches.append(a.reshape(ph, block, pw, block).mean(axis=(1, 3)))
        out.append(np.mean(patches, axis=0))
    return np.asarray(out)


def illumination_gains(reference, other):
    gains = []
    for ref, cur in zip(reference, other):
        valid = (ref > 0.005) & (cur > 0.005) & (ref < 0.8) & (cur < 0.8)
        if valid.sum() < 16:
            raise ValueError('not enough unclipped, illuminated patches to match exposures')
        gain = float(np.median(ref[valid] / cur[valid]))
        if not 0.7 < gain < 1.4:
            raise ValueError('illumination changed too much for a pixel-shift merge')
        gains.append(gain)
    return gains


def illumination_field(reference, other, global_gains):
    """Slow spatial illumination changes, e.g. rolling shutter under LEDs.

    A global exposure ratio cannot remove bands whose brightness varies down
    the frame. Fit only coarse same-colour patch ratios, then smooth them;
    never estimate a separate correction for individual raw pixels.
    """
    fields = []
    for ref, cur, gain in zip(reference, other, global_gains):
        valid = (ref > .005) & (cur > .005) & (ref < .8) & (cur < .8)
        ratio = np.full_like(ref, gain)
        ratio[valid] = np.clip(ref[valid] / cur[valid], .5, 2.)
        # Binomial smoothing of log gains, with edge replication.
        ratio = np.log(ratio)
        for _ in range(2):
            for axis in (0, 1):
                pad = [(0, 0), (0, 0)]
                pad[axis] = (1, 1)
                q = np.pad(ratio, pad, mode='edge')
                ratio = (np.take(q, range(ratio.shape[axis]), axis=axis) +
                         2 * np.take(q, range(1, ratio.shape[axis] + 1), axis=axis) +
                         np.take(q, range(2, ratio.shape[axis] + 2), axis=axis)) / 4
        fields.append(np.exp(ratio))
    return np.asarray(fields)


def expand_field(field, shape, block=32):
    """Bilinear gain field evaluated at colour-plane sample positions."""
    h, w = shape
    y = np.clip((np.arange(h) + .5) / block - .5, 0, field.shape[0] - 1)
    x = np.clip((np.arange(w) + .5) / block - .5, 0, field.shape[1] - 1)
    yi, xi = y.astype(int), x.astype(int)
    yf, xf = (y - yi).astype(np.float32), (x - xi).astype(np.float32)
    rows = field[:, xi] * (1 - xf) + field[:, np.minimum(xi + 1, field.shape[1] - 1)] * xf
    return rows[yi] * (1 - yf[:, None]) + rows[np.minimum(yi + 1, field.shape[0] - 1)] * yf[:, None]


def translate_plane(plane, dx, dy, radius=3):
    """Sample at (x+dx,y+dy) with separable Lanczos, within ONE CFA plane.

    Shifting a Bayer mosaic directly mixes red, green and blue. The small
    residual translation belongs on each uniformly sampled colour plane.
    The caller crops off the interpolation boundary.
    """
    result = plane
    for axis, delta in ((1, dx), (0, dy)):
        if abs(delta) < 1e-8:
            continue
        offsets = np.arange(-radius + 1, radius + 1)
        weights = np.sinc(delta - offsets) * np.sinc((delta - offsets) / radius)
        weights /= weights.sum()
        shifted = np.zeros_like(result)
        for offset, weight in zip(offsets, weights):
            # roll(-offset)[i] = result[i+offset]. Wrapped edges are cropped.
            shifted += np.roll(result, -int(offset), axis=axis) * np.float32(weight)
        result = shifted
    return result


def interlace(acc, lin, pattern, shift, integer_shift, margin, gains, field=None):
    """Place registered same-colour samples without demosaicing the frames."""
    dx, dy = integer_shift
    my, mx = (margin, margin) if np.isscalar(margin) else margin
    rx, ry = shift[0] - dx, shift[1] - dy
    H, W = acc.shape[:2]
    for oy, ox in np.ndindex(2, 2):
        sy, sx = (my + oy + dy) % 2, (mx + ox + dx) % 2
        code = int(pattern[sy, sx])
        channel = 1 if code == 3 else code
        plane = lin[sy::2, sx::2]
        if field is not None:
            plane = plane * expand_field(field[channel], plane.shape)
        else:
            plane = plane * gains[channel]
        plane = translate_plane(plane, rx / 2, ry / 2)
        y0, x0 = (my + oy + dy - sy) // 2, (mx + ox + dx - sx) // 2
        target = acc[oy:H:2, ox:W:2, channel]
        target += plane[y0:y0 + target.shape[0], x0:x0 + target.shape[1]]


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('photos', nargs='+', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--shifts', help='image shifts "dx,dy;dx,dy;dx,dy" for frames 2-4; fractional values allowed')
    p.add_argument('--shift-report', type=Path, help='reuse a measure_z7_raw_shift.py JSON report for these exact files')
    p.add_argument('--alignment', choices=('subpixel', 'integer'), default='subpixel')
    p.add_argument('--photometric', choices=('local', 'match', 'none'), default='local', help='coarse spatial illumination matching (default: local); match uses global ratios only')
    a = p.parse_args(argv)
    if len(a.photos) not in (4,8,16,32):
        p.error('supply one complete 4-, 8-, 16- or 32-shot series')
    a.output.mkdir(parents=True, exist_ok=True)
    if a.shifts and a.shift_report:
        p.error('choose --shifts or --shift-report')
    if len(a.photos)>=16:
        from merge_z7_pixel_shift_highres import run
        return run(a,p)
    if a.shifts:
        measured = [tuple(float(v) for v in s.split(',')) for s in a.shifts.split(';')]
        if len(measured) != len(a.photos)-1 or any(len(v) != 2 for v in measured):
            p.error('--shifts needs one dx,dy pair for every non-reference frame')
    else:
        if a.shift_report:
            saved = json.loads(a.shift_report.read_text(encoding='utf-8'))
            if saved['reference'] != a.photos[0].name or any([r['photo'] for r in rows] != [f.name for f in a.photos[1:]] for rows in saved['planes'].values()):
                p.error('shift report does not match the input order')
            res = saved['planes']
        else:
            from measure_z7_raw_shift import measure
            res = measure(a.photos)
        med = [np.median([[row[k]['dx'], row[k]['dy']] for row in res.values()], axis=0) for k in range(len(a.photos)-1)]
        measured = [[float(v) for v in m] for m in med]
    if not np.isfinite(measured).all():
        p.error('non-finite image shift')
    d = [(0, 0)] + [(int(round(v[0])), int(round(v[1]))) for v in measured]
    if any(max(abs(v[0] - q[0]), abs(v[1] - q[1])) > 0.35 for v, q in zip(measured, d[1:])) or any(max(abs(x), abs(y)) > 1 for x, y in d):
        p.error('this is not a settled one-pixel Bayer-corner set; inspect the capture instead of forcing a merge')
    phases=[(dx%2,dy%2) for dx,dy in d]
    if len(set(phases))!=4 or any(phases.count(v)!=len(d)//4 for v in set(phases)):
        p.error('the frames must cover the four colour-filter phases equally')
    first, lin, info = load(a.photos[0])
    pat = info['pattern']
    h, w = lin.shape
    ref_levels = illumination_levels(lin, pat)
    # Six raw pixels cover the three-plane-sample interpolation support.
    my,mx = info['crop_margin']
    acc = np.zeros((*info['crop_size'], 3), np.float32)
    frame_gains = []
    for k, photo in enumerate(a.photos):
        r, current, meta = (first, lin, info) if k == 0 else load(photo)
        try:
            if current.shape != (h, w) or not np.array_equal(meta['pattern'], pat):
                p.error('all frames must have the same raw dimensions and CFA pattern')
            levels = illumination_levels(current, pat)
            gains = illumination_gains(ref_levels, levels) if a.photometric != 'none' else [1., 1., 1.]
            field = illumination_field(ref_levels, levels, gains) if a.photometric == 'local' else None
            frame_gains.append(gains)
            shift = [(0., 0.)] + measured
            interlace(acc, current, pat, shift[k] if a.alignment == 'subpixel' else d[k], d[k], (my,mx), gains, field)
        finally:
            if k:
                r.close()
        if k:
            del current
    acc[..., 1] *= 0.5
    acc /= len(a.photos)//4
    # Reference: LibRaw's own conversion of the first frame (AHD demosaic, camera WB,
    # sRGB primaries, linear). The merge uses the same WB and matrix; its per-channel
    # level is then matched to the reference so the comparison shows detail, not tint.
    single = first.postprocess(demosaic_algorithm=rawpy.DemosaicAlgorithm.AHD, gamma=(1, 1), no_auto_bright=True,
                                      output_bps=16, use_camera_wb=True, output_color=rawpy.ColorSpace.sRGB,
                                      user_flip=0).astype(np.float32) / 65535.0
    sh, sw = single.shape[:2]
    s_lin = single[my:my + acc.shape[0], mx:mx + acc.shape[1]] if (sh, sw) == (h, w) else single[:acc.shape[0], :acc.shape[1]]
    first.close()
    del lin
    merged_lin = (acc * (info['wb'] / info['wb'][1])[None, None, :]) @ info['cam'].T
    gains = [float(np.median(s_lin[..., c]) / max(np.median(merged_lin[..., c]), 1e-9)) for c in range(3)]
    merged_lin *= np.array(gains, np.float32)[None, None, :]
    scale = 0.9 / max(float(np.percentile(s_lin, 99.5)), 1e-6)
    def srgb(x):
        x = np.clip(x * scale, 0, 1)
        return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)
    merged = srgb(merged_lin)
    single_out = srgb(s_lin)
    write_tiff16(a.output / 'merged.tif', np.round(merged * 65535))
    write_tiff16(a.output / 'single.tif', np.round(single_out * 65535))
    H, W = merged.shape[:2]
    crops = []
    for name, (fy, fx) in (('centre', (0.5, 0.5)), ('upper-left', (0.3, 0.3)), ('lower-right', (0.7, 0.7))):
        cy, cx = int(H * fy), int(W * fx)
        c = (slice(cy - 150, cy + 150), slice(cx - 200, cx + 200))
        pair = np.concatenate([single_out[c], np.ones((300, 8, 3)), merged[c]], axis=1)
        img = Image.fromarray(np.round(pair * 255).astype(np.uint8)).resize((pair.shape[1] * 2, pair.shape[0] * 2), Image.NEAREST)
        out = a.output / ('compare-%s.png' % name)
        img.save(out)
        crops.append(out.name)
    report = dict(photos=[f.name for f in a.photos], measured_shifts=measured, integer_shifts=d, size=[W, H],
                  alignment=a.alignment, photometric=a.photometric, frame_gains=frame_gains, crop_margin=[my,mx],
                  outputs=['merged.tif', 'single.tif'] + crops)
    (a.output / 'merge.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
