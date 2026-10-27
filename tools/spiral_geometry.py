"""Independent Fibonacci quarter-circle geometry for composition-overlay research.

Generated coordinates only; no camera images or third-party artwork. A Fibonacci
spiral approximates a golden logarithmic spiral; the two are not exactly equal.
"""
import math


def fibonacci_arcs():
    """Tile a 144x89 rectangle with 89,55,...,1,1 squares, outer to inner."""
    x0, y0, x1, y1 = 0, 0, 144, 89
    arcs = []
    for index, radius in enumerate((89, 55, 34, 21, 13, 8, 5, 3, 2, 1, 1)):
        direction = index % 4
        if direction == 0:
            center, angle = (x0 + radius, y0 + radius), math.pi
            x0 += radius
        elif direction == 1:
            center, angle = (x0, y0 + radius), -math.pi / 2
            y0 += radius
        elif direction == 2:
            center, angle = (x1 - radius, y0), 0
            x1 -= radius
        else:
            center, angle = (x1, y1 - radius), math.pi / 2
            y1 -= radius
        arcs.append((center[0], center[1], radius, angle, angle + math.pi / 2))
    return arcs


def spiral_points(width=720, height=480, margin=12, mirror_x=False, mirror_y=False):
    """Uniformly scale the circular arcs, keeping their shape and frame bounds."""
    if width <= 2 * margin or height <= 2 * margin or margin < 0:
        raise ValueError('Overlay needs positive interior dimensions')
    scale = min((width - 1 - 2 * margin) / 144, (height - 1 - 2 * margin) / 89)
    ox, oy = ((width - 1) - 144 * scale) / 2, ((height - 1) - 89 * scale) / 2
    points = []
    for cx, cy, radius, start, end in fibonacci_arcs():
        # At most half a source pixel along an arc chord; tangent joins stay
        # continuous and no aspect-ratio stretching turns circles into ellipses.
        segments = max(8, math.ceil(radius * scale * math.pi))
        for step in range(segments + 1):
            angle = start + (end - start) * step / segments
            x, y = ox + scale * (cx + radius * math.cos(angle)), oy + scale * (cy + radius * math.sin(angle))
            points.append((width - 1 - x if mirror_x else x,
                           height - 1 - y if mirror_y else y))
    return points


def overlay_png(width=720, height=480, mirror_x=False, mirror_y=False):
    """Procedural RGBA asset for original guest PNG decode/GPU drawing."""
    import io
    from PIL import Image, ImageDraw
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    ImageDraw.Draw(image).line(spiral_points(width, height, mirror_x=mirror_x, mirror_y=mirror_y),
                              fill=(255, 208, 64, 255), width=2, joint='curve')
    stream = io.BytesIO()
    image.save(stream, format='PNG')
    return image, stream.getvalue()
