/* SPDX-License-Identifier: MIT. Derived from JKWTCN portrait_menu.c at
 * 50a22b24c50619cffa646dac386e8334659f475a, copyright (c) 2026 JKWTCN.
 * Independent original-Z7 footer geometry; no band ownership or transition latch.
 */
#ifndef Z7_PORTRAIT_FOOTER_H
#define Z7_PORTRAIT_FOOTER_H
#include "portrait_geometry.h"
static uint32_t z7_portrait_is_hint(const struct z7_portrait_box *stock)
{
    return z7_portrait_box_fits(stock,724,484) && stock->y>=418 && stock->y+stock->h>426;
}
static uint32_t z7_portrait_footer_box(const struct z7_portrait_box *stock,
                                     uint32_t command,struct z7_portrait_box *out)
{
    if (!out || !z7_portrait_is_hint(stock)) return 0;
    struct z7_portrait_box box=*stock;
    uint32_t full_width=box.x==0 && box.w==720 && (command==0x13 || command==0x17);
    if (box.x<242 && !full_width) {
        if (command!=0x17 || box.x+box.w<=242) return 0;
        box.w-=242-box.x;box.x=242;
    }
    int32_t left=box.x*57344>>16,right=(box.x+box.w)*57344>>16;
    int32_t top=box.y*57344>>16,bottom=(box.y+box.h)*57344>>16;
    struct z7_portrait_box result={left-211,top+295,right>left ? right-left : 1,bottom>top ? bottom-top : 1};
    if (full_width) {result.x=0;result.w=480;}
    if (result.y<660 || !z7_portrait_box_fits(&result,480,720)) return 0;
    *out=result;return 1;
}
#endif
