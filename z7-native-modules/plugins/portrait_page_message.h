/* SPDX-License-Identifier: MIT. Independent original-Z7 page draw adaptation.
 * Derived from JKWTCN portrait_menu.c, pinned50a22b24c50619cffa646dac386e8334659f475a,
 * copyright (c) 2026 JKWTCN. Explicit caller-admitted page/orientation only.
 * No footer/text/input/transition ownership or native external-app binding.
 */
#ifndef Z7_PORTRAIT_PAGE_MESSAGE_H
#define Z7_PORTRAIT_PAGE_MESSAGE_H
#include "portrait_grid_message.h"
enum z7_portrait_layout_page {
    Z7_LAYOUT_GRID=1,Z7_LAYOUT_DIAL,Z7_LAYOUT_SETTING,Z7_LAYOUT_EXTERNAL
};
static uint32_t z7_portrait_page_scale(const struct z7_portrait_box *stock,
    uint32_t page,struct z7_portrait_box *out)
{
    if (!out || !z7_portrait_box_fits(stock,720,480) ||
        (page!=Z7_LAYOUT_DIAL && page!=Z7_LAYOUT_SETTING && page!=Z7_LAYOUT_EXTERNAL)) return 0;
    if (page==Z7_LAYOUT_DIAL && (stock->y<44 || stock->y+stock->h>280)) return 0;
    int32_t left=(int32_t)(((int64_t)stock->x*43691)>>16);
    int32_t right=(int32_t)(((int64_t)(stock->x+stock->w)*43691)>>16);
    int32_t top=stock->y,bottom=stock->y+stock->h;
    if (page!=Z7_LAYOUT_SETTING) {
        top=(int32_t)(((int64_t)top*43691)>>16);
        bottom=(int32_t)(((int64_t)bottom*43691)>>16);
    }
    int32_t shift=page==Z7_LAYOUT_DIAL ? 254 : page==Z7_LAYOUT_SETTING ? 235 : 394;
    struct z7_portrait_box result={left,top+shift,right>left ? right-left : 1,bottom>top ? bottom-top : 1};
    if (!z7_portrait_box_fits(&result,480,720)) return 0;
    *out=result;return 1;
}
static uint32_t z7_portrait_page_message(volatile uint32_t *message,uint32_t page,uint32_t orientation)
{
    if (page==Z7_LAYOUT_GRID) return z7_portrait_grid_message(message,orientation);
    struct z7_portrait_draw_source source;
    if ((orientation!=1 && orientation!=2) || !z7_portrait_message_source(message,&source)) return 0;
    if (page!=Z7_LAYOUT_DIAL && page!=Z7_LAYOUT_SETTING && page!=Z7_LAYOUT_EXTERNAL) return 0;
    struct z7_portrait_box stock=source.box,dest;
    if (!source.image && stock.w==720 && stock.h==480) return 0;
    if (page==Z7_LAYOUT_DIAL) {
        /* A top tile edge can overlap the dial strip by two pixels. */
        uint32_t edge=!source.image && stock.y>=278 && stock.h<=2 && stock.w>=118 && stock.w<=123;
        if (edge || stock.y<44 || stock.y+stock.h>280)
            return z7_portrait_grid_message(message,orientation);
    }
    if (source.image) {
        if (stock.w>=600 && stock.h>=400) return 0;
        uint32_t angle=source.angle==360 ? 0 : source.angle;
        if (angle>270 || angle%90 || (angle && page==Z7_LAYOUT_SETTING))
            return page==Z7_LAYOUT_DIAL ? z7_portrait_consume_draw(message) : 0;
    }
    if (!z7_portrait_page_scale(&stock,page,&dest))
        return page==Z7_LAYOUT_DIAL ? z7_portrait_consume_draw(message) : 0;
    if (page==Z7_LAYOUT_DIAL) {
        uint32_t handled=z7_portrait_draw_strip_box(message,&dest,orientation);
        return handled ? handled : z7_portrait_consume_draw(message);
    }
    return z7_portrait_draw_box(message,&dest,orientation);
}
#endif
