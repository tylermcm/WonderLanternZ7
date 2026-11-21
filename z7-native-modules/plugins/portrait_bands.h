/* SPDX-License-Identifier: MIT. Independent original-Z7 reserved portrait bands.
 * Derived from JKWTCN portrait_menu.c at50a22b24c50619cffa646dac386e8334659f475a,
 * copyright (c) 2026 JKWTCN. Caller owns graphics execution/LCD/page admission.
 * Observed ownership only; no unobserved transition or task-lifetime guarantee.
 */
#ifndef Z7_PORTRAIT_BANDS_H
#define Z7_PORTRAIT_BANDS_H
#include "portrait_page_message.h"
struct z7_portrait_bands { uint32_t footer_orientation,footer_dirty,dial_orientation; };
static inline void z7_portrait_bands_forget(struct z7_portrait_bands *s)
{ if (s) s->footer_orientation=s->footer_dirty=s->dial_orientation=0; }
static uint32_t z7_portrait_clear_band(uint32_t footer,uint32_t orientation)
{
    struct z7_portrait_box band=footer ? (struct z7_portrait_box){0,660,480,60} :
        (struct z7_portrait_box){0,283,480,157},dest;
    if (!z7_portrait_box_to_lcd(&band,orientation,&dest)) return 0;
    uint32_t args[7]={(uint32_t)dest.x,(uint32_t)(480-dest.y-dest.h),
        (uint32_t)dest.w,(uint32_t)dest.h,0,0,0};
    /* Original synchronous clear body; no message completion/event signal. */
    ((void (*)(const uint32_t *))(uintptr_t)0x1042f5a9u)(args);
    return 1;
}
static void z7_portrait_bands_begin(struct z7_portrait_bands *s,uint32_t footer,uint32_t orientation)
{
    if (!s || (orientation!=1 && orientation!=2)) return;
    uint32_t *owned=footer ? &s->footer_orientation : &s->dial_orientation;
    if (*owned==orientation && (!footer || !s->footer_dirty)) return;
    if (*owned && *owned!=orientation) z7_portrait_clear_band(footer,*owned);
    z7_portrait_clear_band(footer,orientation);*owned=orientation;
    if (footer) s->footer_dirty=0;
}
static inline void z7_portrait_bands_observe_clear(struct z7_portrait_bands *s,
                                                 volatile const uint32_t *message)
{
    struct z7_portrait_draw_source source;
    if (s && z7_portrait_message_source(message,&source) && source.command==0x17 &&
        source.box.x==0 && source.box.y==0 && source.box.w==720 && source.box.h==480)
        s->footer_dirty=1;
}
static void z7_portrait_bands_before(struct z7_portrait_bands *s,volatile const uint32_t *message,
                                    uint32_t page,uint32_t orientation)
{
    if (!s) return;
    if (page<Z7_LAYOUT_GRID || page>Z7_LAYOUT_EXTERNAL) {z7_portrait_bands_forget(s);return;}
    uint32_t grid=page==Z7_LAYOUT_GRID || page==Z7_LAYOUT_DIAL;
    if (!grid && s->footer_orientation) {
        z7_portrait_clear_band(1,s->footer_orientation);s->footer_orientation=s->footer_dirty=0;
    }
    if (page!=Z7_LAYOUT_DIAL && s->dial_orientation) {
        z7_portrait_clear_band(0,s->dial_orientation);s->dial_orientation=0;
    }
    if (orientation!=1 && orientation!=2) return;
    struct z7_portrait_draw_source source;
    if (!z7_portrait_message_source(message,&source)) return;
    struct z7_portrait_box b=source.box,dest;
    if (grid && ((!source.image && b.w==720 && b.h==480) ||
        (source.image && b.w>=600 && b.h>=400))) s->footer_dirty=1;
    uint32_t footer=grid && z7_portrait_is_hint(&b);
    uint32_t edge=!source.image && b.y>=278 && b.h<=2 && b.w>=118 && b.w<=123;
    uint32_t dial=page==Z7_LAYOUT_DIAL && b.y>=44 && b.y+b.h<=280 && !edge;
    if (!footer && !dial) return;
    if (source.image) {
        uint32_t angle=source.angle==360 ? 0 : source.angle;
        volatile const uint32_t *payload=(void *)(uintptr_t)message[5];
        if (angle>270 || angle%90 || (source.command==0x1c && (payload[16] || payload[17])) ||
            (source.command==0x19 && (payload[14] || source.source_width<=0 || source.source_width>720 ||
                                    source.source_height<=0 || source.source_height>480))) return;
    }
    if (footer) {
        if (!z7_portrait_footer_box(&b,source.command,&dest)) return;
        z7_portrait_bands_begin(s,1,orientation);
    } else {
        if (!z7_portrait_page_scale(&b,Z7_LAYOUT_DIAL,&dest)) return;
        z7_portrait_bands_begin(s,0,orientation);
    }
}
#endif
