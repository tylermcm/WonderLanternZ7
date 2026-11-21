/* SPDX-License-Identifier: MIT.
 * Derived from JKWTCN/z7ii-extensions portrait_menu.c at
 *50a22b24c50619cffa646dac386e8334659f475a (copyright2026 JKWTCN).
 * Independent Z7 bounded transforms; no firmware addresses or native hooks.
 */
#ifndef Z7_PORTRAIT_GEOMETRY_H
#define Z7_PORTRAIT_GEOMETRY_H
#include <stdint.h>
struct z7_portrait_box { int32_t x, y, w, h; };
static uint32_t z7_portrait_box_fits(const struct z7_portrait_box *b, int32_t width, int32_t height)
{
    return b && b->x >= 0 && b->y >= 0 && b->w > 0 && b->h > 0 &&
        b->w <= width && b->h <= height && b->x <= width - b->w && b->y <= height - b->h;
}
/* Portrait logical canvas480x720; LCD destination canvas720x480. Native values
 *1 and2 select opposite quarter turns. Landscape0/inverted3 are NOT rotated by
 * this portrait-only policy. Failure leaves the caller-owned output unchanged.
 */
static uint32_t z7_portrait_box_from_lcd(const struct z7_portrait_box *in, uint32_t orientation,
                                       struct z7_portrait_box *out)
{
    if (!out || !z7_portrait_box_fits(in,720,480) || (orientation != 1 && orientation != 2)) return 0;
    struct z7_portrait_box b = orientation == 2 ?
        (struct z7_portrait_box){480-in->y-in->h,in->x,in->h,in->w} :
        (struct z7_portrait_box){in->y,720-in->x-in->w,in->h,in->w};
    *out = b; return 1;
}
static uint32_t z7_portrait_box_to_lcd(const struct z7_portrait_box *in, uint32_t orientation,
                                     struct z7_portrait_box *out)
{
    if (!out || !z7_portrait_box_fits(in,480,720) || (orientation != 1 && orientation != 2)) return 0;
    struct z7_portrait_box b = orientation == 2 ?
        (struct z7_portrait_box){in->y,480-in->x-in->w,in->h,in->w} :
        (struct z7_portrait_box){720-in->y-in->h,in->x,in->h,in->w};
    *out = b; return 1;
}
#endif
