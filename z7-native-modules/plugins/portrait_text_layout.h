/* SPDX-License-Identifier: MIT. Independent original-Z7 C3.80 menu text reflow.
 * Derived from JKWTCN portrait_menu.c at50a22b24c50619cffa646dac386e8334659f475a,
 * copyright (c) 2026 JKWTCN. Caller owns page/target/execution admission.
 * Menu symbols only; no live widgets, input or bitmap/task lifetime closure.
 */
#ifndef Z7_PORTRAIT_TEXT_LAYOUT_H
#define Z7_PORTRAIT_TEXT_LAYOUT_H
#include "portrait_bands.h"
#include "portrait_symbols.h"
struct z7_portrait_text_transform;
static uint32_t z7_portrait_text_plan(const uint32_t *,const int32_t *,uint32_t,
                                     void *,struct z7_portrait_text_transform *);
static uint32_t z7_portrait_text_background(uint32_t,void *);
static void z7_portrait_text_symbols_begin(uint32_t *,const struct z7_portrait_text_transform *,
                                          uint32_t,void *,struct z7_portrait_symbol_scope *);
#define Z7_PORTRAIT_TEXT_PLAN z7_portrait_text_plan
#define Z7_PORTRAIT_TEXT_BACKGROUND z7_portrait_text_background
#define Z7_PORTRAIT_TEXT_SYMBOLS_BEGIN z7_portrait_text_symbols_begin
#include "portrait_text.h"
#undef Z7_PORTRAIT_TEXT_PLAN
#undef Z7_PORTRAIT_TEXT_BACKGROUND
#undef Z7_PORTRAIT_TEXT_SYMBOLS_BEGIN
struct z7_portrait_text_page {
    uint32_t page,orientation;
    struct z7_portrait_bands *bands;
};
static void z7_portrait_text_symbols_begin(uint32_t *context,const struct z7_portrait_text_transform *t,
    uint32_t descriptor,void *argument,struct z7_portrait_symbol_scope *scope)
{
    scope->slot=0;
    if (!argument) return;
    const struct z7_portrait_text_page *p=argument;
    uint32_t hint=t->sx==57344 && t->sy==57344;
    uint32_t dial=p->page==Z7_LAYOUT_DIAL && t->sx==43691 && t->sy==43691;
    if (!hint && !dial && p->page!=Z7_LAYOUT_SETTING && p->page!=Z7_LAYOUT_EXTERNAL) return;
    struct z7_portrait_symbol_config config={descriptor,t->orientation,t->sx,t->sy,
        hint ? 660 : dial ? 283 : p->page==Z7_LAYOUT_SETTING ? 235 : 394,dial ? 440 : 720};
    z7_portrait_symbol_begin((uint32_t)(uintptr_t)context,&config,scope);
}
/* Native34 paints its backing rectangle before the glyph callback. Suppress
 * this stock-position rectangle for footer/dial descriptors only, then restore
 * the producer's color word before acknowledgement (synchronous owner only). */
static uint32_t z7_portrait_text_background(uint32_t descriptor,void *argument)
{
    if (!argument) return 0;
    const struct z7_portrait_text_page *p=argument;
    const volatile uint16_t *d=(void *)(uintptr_t)descriptor;
    int32_t top=480-d[0x64/2],bottom=480-d[0x60/2];
    return bottom>top && ((top>=418 && bottom>426 && bottom<=484) ||
        (p->page==Z7_LAYOUT_DIAL && top>=44 && bottom<=280));
}
/* Returns stock0, transform1, or suppress2. Query callbacks bypass this planner.
 * Compute in int64 before bounds checks; overflowing native32 positions are
 * rejected rather than treated as wrapped screen coordinates. */
static uint32_t z7_portrait_text_plan(const uint32_t *m,const int32_t *origin,
    uint32_t descriptor,void *argument,struct z7_portrait_text_transform *out)
{
    if (!argument) return 1; /* Explicit fixed-transform compatibility entry. */
    const struct z7_portrait_text_page *p=argument;
    if (p->page<Z7_LAYOUT_GRID || p->page>Z7_LAYOUT_EXTERNAL ||
        (p->orientation!=1 && p->orientation!=2)) return 0;
    const volatile uint16_t *d=(void *)(uintptr_t)descriptor;
    uint32_t grid=p->page==Z7_LAYOUT_GRID || p->page==Z7_LAYOUT_DIAL;
    int32_t top=480-d[0x64/2],bottom=480-d[0x60/2];
    uint32_t hint=top>=418 && bottom>top && bottom>426 && bottom<=484;
    uint32_t child_hint=!grid && hint;
    hint=grid && hint;
    if (!m[0] || !m[4] || m[0]>0x20000u || m[4]>0x20000u || m[1] || m[3])
        return hint || child_hint ? 2 : 0;
    int64_t x=((((int64_t)origin[0]*(int32_t)m[0])>>16)+(int32_t)m[2])>>16;
    int64_t y=480-(((((int64_t)origin[1]*(int32_t)m[4])>>16)+(int32_t)m[5])>>16);
    int32_t w=(int32_t)(((int64_t)(d[0xac/2] ? d[0xac/2] : d[8/2])*m[0])>>16);
    int32_t h=(int32_t)(((int64_t)(d[0xae/2] ? d[0xae/2] : d[0xa/2])*m[4])>>16);
    hint=hint || (grid && y>426);
    child_hint=child_hint || (!grid && y>426);
    if (x<0 || x>=720 || y<0 || y>480 || (!child_hint && (w<=0 || w>720 || h<=0 || h>480)))
        return hint || child_hint ? 2 : 0;
    int32_t anchor=(int32_t)y,sx=65536,sy=65536,dx=0,dy=0;
    struct z7_portrait_box stock={(int32_t)x,(int32_t)y,w,h},dest;
    if (grid && d[0x5e/2]>=88 && d[0x62/2]<=632 && d[0x62/2]>d[0x5e/2] &&
        top>=208 && bottom<=280 && bottom>top) anchor=bottom<280 ? bottom : 279;
    uint32_t dial=0;
    if (hint) {
        dest=(struct z7_portrait_box){(int32_t)x,(int32_t)y-h,w,h};
        if (!z7_portrait_footer_box(&dest,0,&dest)) return 2;
        sx=sy=57344;dx=-211*65536;dy=295*65536;
    } else if (child_hint) {
        sx=43691;sy=p->page==Z7_LAYOUT_SETTING ? 65536 : 43691;
        dy=(p->page==Z7_LAYOUT_SETTING ? 235 : 394)*65536;
    } else {
        stock.y=z7_portrait_grid_clamp(anchor-h,0,480-h);
        if (grid && anchor>=218 && anchor<280 && h<=72)
            stock.y=z7_portrait_grid_clamp(stock.y,208,280-h);
        dest=stock;
        if (p->page==Z7_LAYOUT_SETTING || p->page==Z7_LAYOUT_EXTERNAL ||
            (p->page==Z7_LAYOUT_DIAL && stock.y>=44 && stock.y+h<=280)) {
            if (!z7_portrait_page_scale(&stock,p->page,&dest)) return 0;
            sx=43691;sy=p->page==Z7_LAYOUT_SETTING ? 65536 : 43691;
            dial=p->page==Z7_LAYOUT_DIAL;
        } else if (stock.y>=208 && stock.y+h<=280) {
            if (w>480) {dest.x=0;dest.w=480;}
            else dest.x=z7_portrait_grid_clamp(stock.x-120,0,480-w);
            dest.y+=162;
        } else if (!z7_portrait_grid_relocate(&dest,0)) return 0;
        if (!z7_portrait_box_fits(&dest,480,720)) return 0;
        dx=dest.x*65536-(int32_t)x*sx;
        dy=dest.y*65536-stock.y*sy;
    }
    *out=(struct z7_portrait_text_transform){p->orientation,sx,sy,dx,dy};
    if (hint || dial) z7_portrait_bands_begin(p->bands,hint,p->orientation);
    return 1;
}
static uint32_t z7_portrait_text_page_draw(volatile uint32_t *message,uint32_t page,
    uint32_t orientation,struct z7_portrait_bands *bands)
{
    if (page<Z7_LAYOUT_GRID || page>Z7_LAYOUT_EXTERNAL || (orientation!=1 && orientation!=2)) return 0;
    struct z7_portrait_text_page context={page,orientation,bands};
    const struct z7_portrait_text_transform initial={orientation,65536,65536,0,0};
    return z7_portrait_text_draw_planned(message,&initial,&context);
}
#endif
