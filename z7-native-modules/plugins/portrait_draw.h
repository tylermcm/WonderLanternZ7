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

/* Dispatch one or two caller-selected portrait boxes. Native rectangle payloads use
 * bottom-origin y, image payloads use packed top-origin exclusive corners.
 * Original-Z7 images have angle at word15, NOT pinned Z7II word16.
 * The local message/payload remain live throughout original dispatch. Original
 * producer acknowledgement follows the final dispatch return, exactly once. Admission
 * failure changes neither the original message nor its source payload.
 */
__attribute__((target("hwdiv")))
static uint32_t z7_portrait_strip19_box(struct z7_portrait_box *dest,int32_t sw,int32_t sh,uint32_t angle)
{
    if (sw<=0 || sh<=0 || sw>720 || sh>480) return 0;
    if (angle==90 || angle==270) {
        int32_t width=(dest->w*sw+sh/2)/sh,height=(dest->h*sh+sw/2)/sw;
        if (width<1) width=1;
        if (height<1) height=1;
        int32_t half=(width+height)/2;
        if (angle==90) {dest->x+=height-half;dest->y+=dest->h-half;}
        else {dest->x+=dest->w-half;dest->y+=width-half;}
        dest->w=width;dest->h=height;
    }
    return dest->w<=720 && dest->h<=480 && dest->x>=INT16_MIN && dest->y>=INT16_MIN &&
        dest->x+dest->w<=INT16_MAX && dest->y+dest->h<=INT16_MAX;
}
static uint32_t z7_portrait_draw_boxes_ex(volatile uint32_t *message,
    const struct z7_portrait_box *boxes, uint32_t count, uint32_t orientation,uint32_t strip)
{
    struct z7_portrait_box destinations[2];
    if (!z7_portrait_native_words((uint32_t)(uintptr_t)message,7) ||
        !boxes || !count || count>2 || message[3] != 0x1042eadfu) return 0;
    /* Validate the whole batch before the first native draw or acknowledgement. */
    for (uint32_t i=0;i<count;++i)
        if (!z7_portrait_box_to_lcd(boxes+i,orientation,destinations+i)) return 0;
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
        if (strip) {
            payload[9]=0; /* Original image19/1A clear-enable field. */
            if (command==0x19) {
                int32_t sw=(int16_t)source[5]-(int16_t)source[4];
                int32_t sh=(int16_t)(source[5]>>16)-(int16_t)(source[4]>>16);
                /* Native auxiliary mode14 is not admitted by this strip path. */
                if (source[14]) return 0;
                for (uint32_t i=0;i<count;++i)
                    if (!z7_portrait_strip19_box(destinations+i,sw,sh,angle)) return 0;
            }
        }
        payload[0]=0;
        payload[15]=(payload[15]&0xffff0000u) | angle;
    }
    for (uint32_t i=0;i<7;++i) local[i]=message[i];
    if (command==0x1c) local[4]=0x4201001au;
    local[3]=(uint32_t)(uintptr_t)z7_portrait_defer_completion;
    local[5]=(uint32_t)(uintptr_t)payload;
    for (uint32_t i=0;i<count;++i) {
        const struct z7_portrait_box *dest=destinations+i;
        if (image) {
            payload[6]=(uint16_t)dest->x | ((uint32_t)(uint16_t)dest->y<<16);
            payload[7]=(uint16_t)(dest->x+dest->w) | ((uint32_t)(uint16_t)(dest->y+dest->h)<<16);
        } else {
            payload[0]=(uint32_t)dest->x;
            payload[1]=(uint32_t)(480-dest->y-dest->h);
            payload[2]=(uint32_t)dest->w;
            payload[3]=(uint32_t)dest->h;
        }
        ((void (*)(const uint32_t *))(uintptr_t)0x10372391u)(local);
    }
    message[6]=local[6];
    ((void (*)(uint32_t,uint32_t))(uintptr_t)0x1042eadfu)(0x42010062u,local[6]);
    return 1;
}
static inline uint32_t z7_portrait_draw_boxes(volatile uint32_t *message,
    const struct z7_portrait_box *boxes,uint32_t count,uint32_t orientation)
{ return z7_portrait_draw_boxes_ex(message,boxes,count,orientation,0); }
static inline uint32_t z7_portrait_draw_box(volatile uint32_t *message,
                                   const struct z7_portrait_box *box, uint32_t orientation)
{ return z7_portrait_draw_boxes(message,box,1,orientation); }
static inline uint32_t z7_portrait_draw_strip_box(volatile uint32_t *message,
    const struct z7_portrait_box *box,uint32_t orientation)
{ return z7_portrait_draw_boxes_ex(message,box,1,orientation,1); }
static inline uint32_t z7_portrait_consume_draw(volatile uint32_t *message)
{
    if (!z7_portrait_native_words((uint32_t)(uintptr_t)message,7) || message[3]!=0x1042eadfu) return 0;
    message[6]=0;
    ((void (*)(uint32_t,uint32_t))(uintptr_t)0x1042eadfu)(0x42010062u,0);
    return 1;
}
#endif
