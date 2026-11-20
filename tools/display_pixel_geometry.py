"""Original-Z7 ordinary HUD control rectangles in captured scanout pixels.

SPDX-License-Identifier: MIT. Ordinary image/text controls use top-down native
720x480 layout coordinates. The histogram low-level rectangle service has a
different bottom-up convention; use its separately scoped fixture transform.
"""
import math


def control_scanout_box(rectangle, size):
    x1, y1, x2, y2 = rectangle
    width, height = size
    if not (0 <= x1 < x2 <= 720 and 0 <= y1 < y2 <= 480 and width > 0 and height > 0):
        raise ValueError('Bounded nonempty native HUD rectangle and scanout required')
    return (math.floor(x1 * width / 720), math.floor(y1 * height / 480),
            math.ceil(x2 * width / 720), math.ceil(y2 * height / 480))
