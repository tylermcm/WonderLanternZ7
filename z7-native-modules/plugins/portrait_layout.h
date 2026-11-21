/* SPDX-License-Identifier: MIT. Independent original-Z7 menu orientation latch.
 * Derived from JKWTCN portrait_menu.c, pinned50a22b24c50619cffa646dac386e8334659f475a,
 * copyright (c) 2026 JKWTCN. Graphics caller owns entry/exit admission.
 * No band clearing, task exclusion, external-page binding or input remap here.
 */
#ifndef Z7_PORTRAIT_LAYOUT_H
#define Z7_PORTRAIT_LAYOUT_H
#include "portrait_page_message.h"
struct z7_portrait_layout { uint32_t orientation; }; /* 0 waiting,1/2 portrait,3 landscape. */
static inline void z7_portrait_layout_reset(struct z7_portrait_layout *state)
{ if (state) __atomic_store_n(&state->orientation,0,__ATOMIC_RELEASE); }
static uint32_t z7_portrait_layout_choose(struct z7_portrait_layout *state,
    volatile const uint32_t *message,uint32_t page,uint32_t sampled)
{
    if (!state) return 0;
    if (page!=Z7_LAYOUT_GRID && page!=Z7_LAYOUT_DIAL && page!=Z7_LAYOUT_SETTING && page!=Z7_LAYOUT_EXTERNAL) {
        z7_portrait_layout_reset(state);return 0;
    }
    uint32_t current=__atomic_load_n(&state->orientation,__ATOMIC_ACQUIRE);
    if (current) return current<=3 ? current : 0;
    uint32_t trigger=page==Z7_LAYOUT_SETTING;
    struct z7_portrait_draw_source source;
    if (!trigger && z7_portrait_message_source(message,&source)) {
        struct z7_portrait_box b=source.box;
        trigger=(page==Z7_LAYOUT_GRID || page==Z7_LAYOUT_DIAL) && (source.command==0x13 || source.command==0x17) &&
            b.x==0 && b.y==280 && b.w==720 && b.h==146;
        trigger|=page==Z7_LAYOUT_GRID && source.command==0x17 &&
            b.x==88 && b.y==228 && b.w==544 && b.h==44;
        uint32_t edge=!source.image && b.y>=278 && b.h<=2 && b.w>=118 && b.w<=123;
        trigger|=page==Z7_LAYOUT_DIAL && b.y>=44 && b.y+b.h<=280 && !edge;
    }
    if (!trigger) return 0;
    uint32_t chosen=sampled==1 || sampled==2 ? sampled : 3;
    __atomic_store_n(&state->orientation,chosen,__ATOMIC_RELEASE);
    return chosen;
}
#endif
