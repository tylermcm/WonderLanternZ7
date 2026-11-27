"""Measure the image shift between the photos of a pixel-shift series (MIT).

For each NEF (or JPEG) given, takes the largest embedded JPEG preview (Nikon
stores a full-size one), converts it to grey, and measures its translation
against the first photo by phase correlation, refined by upsampled
cross-correlation (1/50 px), in a central window. For a working Z7 series (corners (0,0), (21,0), (21,18),
(0,18) steps) the photos should differ by about one pixel per step from the
first: (0,0), (1,0), (1,1), (0,1) in sign-dependent directions. Preview JPEGs
are full resolution but compressed, so expect a few hundredths of a pixel of
noise. Reads files only; writes a JSON report if --output is given.
"""
import argparse, io, json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image


def tiff_jpegs(data):
    """Yield (offset, length) of every JPEG referenced by a TIFF/NEF's IFDs."""
    order = '<' if data[:2] == b'II' else '>'
    if data[2:4] not in (b'*\0', b'\0*'):
        raise ValueError('not a TIFF/NEF file')
    seen, todo, found = set(), [struct.unpack_from(order + 'I', data, 4)[0]], []
    while todo:
        off = todo.pop()
        if not off or off in seen or off + 2 > len(data):
            continue
        seen.add(off)
        n = struct.unpack_from(order + 'H', data, off)[0]
        tags = {}
        for i in range(n):
            tag, typ, count, value = struct.unpack_from(order + 'HHII', data, off + 2 + 12 * i)
            if typ == 3 and count == 1:
                value = struct.unpack_from(order + 'H', data, off + 2 + 12 * i + 8)[0]
            tags[tag] = (typ, count, value)
            if tag == 0x14a:  # SubIFDs
                if count == 1:
                    todo.append(value)
                else:
                    todo.extend(struct.unpack_from(order + '%dI' % count, data, value))
        if 0x201 in tags and 0x202 in tags:
            found.append((tags[0x201][2], tags[0x202][2]))
        nxt = off + 2 + 12 * n
        if nxt + 4 <= len(data):
            todo.append(struct.unpack_from(order + 'I', data, nxt)[0])
    return found


def load_grey(path):
    data = Path(path).read_bytes()
    if data[:2] == b'\xff\xd8':
        img = Image.open(io.BytesIO(data))
    else:
        jpegs = [(o, l) for o, l in tiff_jpegs(data) if data[o:o + 2] == b'\xff\xd8']
        if not jpegs:
            raise ValueError(f'{path}: no embedded JPEG preview')
        o, l = max(jpegs, key=lambda j: j[1])
        img = Image.open(io.BytesIO(data[o:o + l]))
    return np.asarray(img.convert('L'), dtype=np.float64)


def window(img, size):
    h, w = img.shape
    s = min(size, h, w) // 2 * 2
    y, x = (h - s) // 2, (w - s) // 2
    crop = img[y:y + s, x:x + s]
    crop = crop - crop.mean()
    han = np.outer(np.hanning(s), np.hanning(s))
    return crop * han


def phase_shift(a, b):
    """Translation (dx, dy) that maps a onto b, sub-pixel."""
    fa, fb = np.fft.fft2(a), np.fft.fft2(b)
    r = fb * np.conj(fa)
    r /= np.abs(r) + 1e-12
    c = np.fft.ifft2(r).real
    py, px = np.unravel_index(np.argmax(c), c.shape)
    def fit(m1, z, p1):
        d = m1 - 2 * z + p1
        return 0.0 if d == 0 else 0.5 * (m1 - p1) / d
    h, w = c.shape
    dy = py + fit(c[(py - 1) % h, px], c[py, px], c[(py + 1) % h, px])
    dx = px + fit(c[py, (px - 1) % w], c[py, px], c[py, (px + 1) % w])
    if dy > h / 2: dy -= h
    if dx > w / 2: dx -= w
    return float(dx), float(dy), float(c[py, px])


def refine_shift(a, b, dx, dy, factor=50, span=1.5):
    """Upsampled cross-correlation around (dx, dy) (matrix-multiply DFT,
    Guizar-Sicairos et al. 2008): accurate to 1/factor px, no parabolic bias."""
    fa, fb = np.fft.fft2(a), np.fft.fft2(b)
    r = fb * np.conj(fa)
    r /= np.abs(r) + 1e-12
    h, w = r.shape
    n = int(np.ceil(span * factor)) * 2 + 1
    ox, oy = np.arange(n) / factor - span + dx, np.arange(n) / factor - span + dy
    ky, kx = np.fft.fftfreq(h), np.fft.fftfreq(w)
    ey = np.exp(2j * np.pi * np.outer(oy, ky))
    ex = np.exp(2j * np.pi * np.outer(kx, ox))
    c = (ey @ r @ ex).real
    iy, ix = np.unravel_index(np.argmax(c), c.shape)
    return float(ox[ix]), float(oy[iy])


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('photos', nargs='+', type=Path)
    p.add_argument('--window', type=int, default=2048, help='central square window in pixels')
    p.add_argument('--output', type=Path)
    a = p.parse_args(argv)
    base = window(load_grey(a.photos[0]), a.window)
    rows = []
    for i, f in enumerate(a.photos):
        if i == 0:
            dx, dy, peak = 0.0, 0.0, 1.0
        else:
            other = window(load_grey(f), a.window)
            dx, dy, peak = phase_shift(base, other)
            dx, dy = refine_shift(base, other, round(dx), round(dy))
        rows.append(dict(photo=f.name, dx=round(dx, 3), dy=round(dy, 3), peak=round(peak, 4)))
        print(f'{f.name}: dx {dx:+.3f} px, dy {dy:+.3f} px (peak {peak:.3f})')
    if a.output:
        a.output.write_text(json.dumps(dict(window=a.window, photos=rows), indent=2) + '\n', encoding='utf-8')
    return rows


if __name__ == '__main__':
    main()
