"""Measure the shift between pixel-shift NEFs on their raw colour planes (MIT).

Reads each NEF's raw Bayer data with rawpy (LibRaw), splits it into the four
colour planes (R, G, G2, B; each sampled every second pixel, so a planes is
uniformly sampled and free of colour-filter mixing), and measures each frame's
translation against the first frame per plane, by phase correlation refined
with upsampled cross-correlation, over a grid of textured tiles (median of the
better half). Results are in full-resolution pixels (plane shift x 2).

Notes from the Z7 runs (PIXEL_SHIFT_RESEARCH.md):
  - multi-pixel shifts (e.g. 4 px) read back within about 0.2-0.5 px, and
    all four planes agree within about 0.1 px;
  - one-pixel shifts are half a sample on each plane, where the plane is
    aliased: treat sub-pixel results as indicative, compare frames against
    their neighbours, and expect a small bias toward whole plane samples.
Needs: pip install rawpy. Reads files only.
"""
import argparse, json
from pathlib import Path
import numpy as np
import rawpy
from measure_z7_pixel_shift import phase_shift, refine_shift

NAMES = {0: 'R', 1: 'G', 2: 'B', 3: 'G2'}


def planes(path):
    with rawpy.imread(str(path)) as r:
        a = r.raw_image_visible.astype(np.float32)
        pat = r.raw_pattern
    return {NAMES[int(pat[y][x])]: a[y::2, x::2] for y in range(2) for x in range(2)}


def measure(files, tile=512, grid=(5, 7)):
    data = [planes(f) for f in files]
    han = np.outer(np.hanning(tile), np.hanning(tile))
    out = {}
    for name in ('R', 'G', 'G2', 'B'):
        h, w = data[0][name].shape
        rows = []
        for k in range(1, len(files)):
            r = []
            for ty in range(grid[0]):
                for tx in range(grid[1]):
                    y0 = int((h - tile) * ty / (grid[0] - 1)); x0 = int((w - tile) * tx / (grid[1] - 1))
                    b = data[0][name][y0:y0 + tile, x0:x0 + tile]
                    if b.std() < 20:
                        continue
                    o = data[k][name][y0:y0 + tile, x0:x0 + tile]
                    B = (b - b.mean()) * han; O = (o - o.mean()) * han
                    dx, dy, pk = phase_shift(B, O)
                    dx, dy = refine_shift(B, O, round(dx), round(dy))
                    r.append((dx, dy, pk))
            a = np.array(r)
            g = a[a[:, 2] >= np.median(a[:, 2])]
            rows.append(dict(photo=Path(files[k]).name, dx=round(2 * float(np.median(g[:, 0])), 2), dy=round(2 * float(np.median(g[:, 1])), 2),
                             iqr_x=round(2 * float(np.subtract(*np.percentile(g[:, 0], [75, 25]))), 2),
                             iqr_y=round(2 * float(np.subtract(*np.percentile(g[:, 1], [75, 25]))), 2), tiles=int(len(g))))
        out[name] = rows
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('photos', nargs='+', type=Path)
    p.add_argument('--output', type=Path)
    a = p.parse_args(argv)
    res = measure(a.photos)
    for name, rows in res.items():
        print(name.ljust(2), '  '.join('%s (%+.2f, %+.2f) iqr %.2f/%.2f' % (r['photo'], r['dx'], r['dy'], r['iqr_x'], r['iqr_y']) for r in rows))
    if a.output:
        a.output.write_text(json.dumps(dict(reference=a.photos[0].name, planes=res), indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
