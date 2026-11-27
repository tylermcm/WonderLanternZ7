"""Merge a four-frame Z7 pixel-shift set into one full-colour image (MIT).

Input: the four NEFs of a series taken at the Bayer corners (the module's
(0,0), (20,0), (20,18), (0,18) steps = image shifts of about (0,0), (-1,0),
(-1,+1), (0,+1) px). The integer shift of each frame is measured on its raw
colour planes (tools/measure_z7_raw_shift.py) unless given with --shifts.

For each pixel of the first frame, the scene point it saw is found in every
frame at p + d_k, where that frame's colour filter has a different colour.
Together the four frames give one R, two G and one B sample per pixel, so
the merged image needs no demosaicing (no colour interpolation, no colour
moire). Output, all in --output:
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
    info = dict(pattern=pat, wb=np.array(r.camera_whitebalance[:3], np.float32), cam=np.linalg.inv(cam_rgb).astype(np.float32))
    return r, lin, info


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('photos', nargs=4, type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--shifts', help='integer image shifts "dx,dy;dx,dy;dx,dy" for frames 2-4 (default: measured)')
    a = p.parse_args(argv)
    a.output.mkdir(parents=True, exist_ok=True)
    if a.shifts:
        d = [(0, 0)] + [tuple(int(v) for v in s.split(',')) for s in a.shifts.split(';')]
        measured = None
    else:
        from measure_z7_raw_shift import measure
        res = measure(a.photos)
        med = [np.median([[row[k]['dx'], row[k]['dy']] for row in res.values()], axis=0) for k in range(3)]
        measured = [[float(v) for v in m] for m in med]
        d = [(0, 0)] + [(int(round(m[0])), int(round(m[1]))) for m in med]
    frames = [load(f) for f in a.photos]
    pat = frames[0][2]['pattern']
    h, w = frames[0][1].shape
    m = 2
    acc = np.zeros((h - 2 * m, w - 2 * m, 3), np.float32)
    yy, xx = np.mgrid[m:h - m, m:w - m]
    for k, (r, lin, info) in enumerate(frames):
        dx, dy = d[k]
        sy, sx = yy + dy, xx + dx
        colour = pat[sy % 2, sx % 2]
        vals = lin[sy, sx]
        for c, ch in ((0, 0), (1, 1), (2, 2), (3, 1)):
            mask = colour == c
            acc[..., ch][mask] += vals[mask]
    # Each pixel gets R once, G twice, B once when the four shifts cover the 2x2 phases.
    phases = {(dx % 2, dy % 2) for dx, dy in d}
    if len(phases) != 4:
        raise SystemExit('the four frames do not cover the four colour-filter phases: %s' % (d,))
    acc[..., 1] *= 0.5
    # Reference: LibRaw's own conversion of the first frame (AHD demosaic, camera WB,
    # sRGB primaries, linear). The merge uses the same WB and matrix; its per-channel
    # level is then matched to the reference so the comparison shows detail, not tint.
    single = frames[0][0].postprocess(demosaic_algorithm=rawpy.DemosaicAlgorithm.AHD, gamma=(1, 1), no_auto_bright=True,
                                      output_bps=16, use_camera_wb=True, output_color=rawpy.ColorSpace.sRGB,
                                      user_flip=0).astype(np.float32) / 65535.0
    sh, sw = single.shape[:2]
    s_lin = single[m:m + acc.shape[0], m:m + acc.shape[1]] if (sh, sw) == (h, w) else single[:acc.shape[0], :acc.shape[1]]
    info = frames[0][2]
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
                  outputs=['merged.tif', 'single.tif'] + crops)
    (a.output / 'merge.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
