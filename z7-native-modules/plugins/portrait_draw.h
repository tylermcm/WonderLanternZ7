/* SPDX-License-Identifier: MIT.
 * Independent original-Z7 C3.80 synchronous draw adapter, informed by
 * JKWTCN portrait_menu.c at 50a22b24c50619cffa646dac386e8334659f475a,
 * copyright (c) 2026 JKWTCN. See NOTICE.md and PORTRAIT_RESEARCH.md.
 * Caller owns the graphics task and admits the LCD context/layout. This helper
 * does not install a hook, choose a layout, reflow text or remap input.
 */
#ifndef Z7_PORTRAIT_DRAW_H
#define Z7_PORTRAIT_DRAW_H
#include "portrait_geometry.h"
static uint32_t z7_portrait_native_words(uint32_t address, uint32_t words)
{
    return !(address & 3u) && address >= 0xa1800000u && words <= 24u &&
        address <= 0xb0000000u - words * 4u;
}
static void z7_portrait_defer_completion(uint32_t code, uint32_t result)
{ (void)code; (void)result; }

/* Dispatch a caller-selected portrait box. Native rectangle payloads use
 * bottom-origin y, image payloads use packed top-origin exclusive corners.
 * Original-Z7 images have angle at word15, NOT pinned Z7II word16.
 * The local message/payload remain live throughout original dispatch. Original
 * producer acknowledgement follows dispatch return, exactly once. Admission
 * failure changes neither the original message nor its source payload.
 */
static uint32_t z7_portrait_draw_box(volatile uint32_t *message,
                                   const struct z7_portrait_box *box, uint32_t orientation)
{
    struct z7_portrait_box dest;
    if (!z7_portrait_native_words((uint32_t)(uintptr_t)message,7) ||
        !z7_portrait_box_to_lcd(box,orientation,&dest) || message[3] != 0x1042eadfu) return 0;
    uint32_t command=message[4]-0x42010000u, words;
    switch (command) {
    case 0x13: words=8; break;
    case 0x16: words=7; break;
    case 0x17: words=6; break;
    case 0x19: words=18; break;
    case 0x1a: words=24; break;
    case 0x1c: words=18; break;
    default: return 0;
    }
    if (!z7_portrait_native_words(message[5],words)) return 0;
    const volatile uint32_t *source=(const volatile uint32_t *)(uintptr_t)message[5];
    uint32_t payload[24], local[7], image=command==0x19 || command==0x1a || command==0x1c;
    if (image) {
        uint32_t angle=command==0x1c ? 0 : source[15]&0xffffu;
        if (source[0]>1 || angle>360 || angle%90) return 0;
        if (command==0x1c && (source[16] || source[17])) return 0;
    }
    if (command==0x1c) {
        /* Native fixed-point1C has no angle or clear field. Adapt its
         * original-Z7 flags/pitch fields to the rotatable1A layout. */
        for (uint32_t i=0;i<24;++i) payload[i]=0;
        for (uint32_t i=0;i<6;++i) payload[i]=source[i];
        payload[8]=0xffffffffu;
        payload[11]=source[10];
        payload[16]=source[11]; payload[17]=source[12];
        payload[19]=source[13]; payload[20]=source[14]; payload[21]=source[15];
    } else {
        for (uint32_t i=0;i<words;++i) payload[i]=source[i];
    }
    if (image) {
        uint32_t angle=(payload[15]&0xffffu)+(orientation==2 ? 90u : 270u);
        angle%=360u;
        payload[0]=0;
        payload[6]=(uint32_t)dest.x | ((uint32_t)dest.y<<16);
        payload[7]=(uint32_t)(dest.x+dest.w) | ((uint32_t)(dest.y+dest.h)<<16);
        payload[15]=(payload[15]&0xffff0000u) | angle;
    } else {
        payload[0]=(uint32_t)dest.x;
        payload[1]=(uint32_t)(480-dest.y-dest.h);
        payload[2]=(uint32_t)dest.w;
        payload[3]=(uint32_t)dest.h;
    }
    for (uint32_t i=0;i<7;++i) local[i]=message[i];
    if (command==0x1c) local[4]=0x4201001au;
    local[3]=(uint32_t)(uintptr_t)z7_portrait_defer_completion;
    local[5]=(uint32_t)(uintptr_t)payload;
    ((void (*)(const uint32_t *))(uintptr_t)0x10372391u)(local);
    message[6]=local[6];
    ((void (*)(uint32_t,uint32_t))(uintptr_t)0x1042eadfu)(0x42010062u,local[6]);
    return 1;
}
#endif
