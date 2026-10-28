"""Observe the gray LCD curve's upper arc, excluding unrelated gray UI.

The analysis mask is used only to count matching screenshot pixels. It is never
uploaded to the guest or composited into a screenshot. The lower curve is checked
visually, not classified by this color-bar-specific detector. This is not EVF scanout
verification; native EVF descriptors and supplied-boundary instruction tests are
recorded separately.
"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw
import probe_spiral_lifecycle as lifecycle
from spiral_geometry import spiral_points


def classify_gray(im):
    sx, sy = im.width / 720, im.height / 480
    points = [(x*sx, y*sy) for x, y in spiral_points()]
    mask = Image.new('1', im.size)
    ImageDraw.Draw(mask).line(points, fill=1, width=8, joint='curve')
    # The upper color bars have no gray background. Lower gradient bands and
    # straight grid intersections otherwise resemble an absent gray curve.
    draw = ImageDraw.Draw(mask)
    draw.rectangle((0, int(im.height * .48), im.width, im.height), fill=0)
    for ratio in (1/3, 2/3, .38196601125, .61803398875):
        x, y = round(im.width * ratio), round(im.height * ratio)
        draw.rectangle((x-4, 0, x+4, im.height), fill=0)
        draw.rectangle((0, y-4, im.width, y+4), fill=0)
    data = list(im.getdata())
    return dict(scene=sum(r > 200 and g > 240 and b < 40 for r, g, b in data),
                curve=sum(214 <= r <= 218 and 214 <= g <= 218 and 214 <= b <= 218
                          for (r, g, b), expected in zip(data, mask.getdata()) if expected))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    lifecycle.classify_pixels = classify_gray
    result = lifecycle.run(args.build.resolve(), args.output)
