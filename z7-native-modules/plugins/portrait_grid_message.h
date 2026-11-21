/* SPDX-License-Identifier: MIT. Independent original-Z7 C3.80 adaptation of
 * JKWTCN portrait_menu.c at 50a22b24c50619cffa646dac386e8334659f475a,
 * copyright (c) 2026 JKWTCN. Caller admits GRID page, output, task and lifetime.
 * Tile/border/backdrop/title path only; footer, dial, text and input unfinished.
 */
#ifndef Z7_PORTRAIT_GRID_MESSAGE_H
#define Z7_PORTRAIT_GRID_MESSAGE_H
#include "portrait_grid.h"
#include "portrait_draw.h"
struct z7_portrait_draw_source {
    struct z7_portrait_box box;
    uint32_t command,image,angle;
    int32_t source_width,source_height;
};
/* Failure leaves output, native message and payload unchanged. */
static uint32_t z7_portrait_message_source(volatile const uint32_t *message,
                                          struct z7_portrait_draw_source *out)
{
    if (!out || !z7_portrait_native_words((uint32_t)(uintptr_t)message,7) ||
        message[3]!=0x1042eadfu) return 0;
    uint32_t command=message[4]-0x42010000u,words;
    switch (command) {
    case 0x13:words=8;break;
    case 0x16:words=7;break;
    case 0x17:words=6;break;
    case 0x19:case 0x1c:words=18;break;
    case 0x1a:words=24;break;
    default:return 0;
    }
    if (!z7_portrait_native_words(message[5],words)) return 0;
    volatile const uint32_t *s=(void *)(uintptr_t)message[5];
    struct z7_portrait_draw_source result={.command=command,.image=command>=0x19};
    if (result.image) {
        if (s[0]>1) return 0;
        result.source_width=(int16_t)s[5]-(int16_t)s[4];
        result.source_height=(int16_t)(s[5]>>16)-(int16_t)(s[4]>>16);
        if (command==0x1c) {
            result.box.x=(int32_t)s[6]>>16;result.box.y=(int32_t)s[7]>>16;
            result.box.w=((int32_t)s[8]>>16)-result.box.x;
            result.box.h=((int32_t)s[9]>>16)-result.box.y;
        } else {
            result.box.x=(int16_t)s[6];result.box.y=(int16_t)(s[6]>>16);
            result.box.w=(int16_t)s[7]-result.box.x;
            result.box.h=(int16_t)(s[7]>>16)-result.box.y;
            result.angle=s[15]&65535u; /* Original-Z7 angle, not Z7II word16. */
        }
        if (s[0]==1) {result.box.w=result.source_width;result.box.h=result.source_height;}
    } else {
        int32_t x=(int32_t)s[0],y=(int32_t)s[1],w=(int32_t)s[2],h=(int32_t)s[3];
        if (x<0 || x>720 || y< -4 || y>=480 || w<=0 || w>720 || h<=0 || h>480) return 0;
        result.box=(struct z7_portrait_box){x,480-y-h,w,h};
    }
    if (!z7_portrait_box_fits(&result.box,724,484)) return 0;
    *out=result;return 1;
}
static uint32_t z7_portrait_grid_content(struct z7_portrait_box *box,uint32_t image)
{
    if (box->y>=208 && box->y+box->h<=280) {
        if (box->w>480) {box->x=0;box->w=480;}
        else box->x=z7_portrait_grid_clamp(box->x-120,0,480-box->w);
        box->y+=162;return 1;
    }
    return z7_portrait_grid_relocate(box,image);
}
static uint32_t z7_portrait_grid_message(volatile uint32_t *message,uint32_t orientation)
{
    struct z7_portrait_draw_source source;
    if ((orientation!=1 && orientation!=2) || !z7_portrait_message_source(message,&source)) return 0;
    struct z7_portrait_box stock=source.box,boxes[2];uint32_t count=0;
    if (source.image) {
        /* Preserve stock preview/surface copies and pre-rotated tile images. */
        if ((source.angle && source.angle!=360) ||
            (stock.w>=600 && stock.h>=400) ||
            (stock.y>=280 && (source.source_width>240 || source.source_height>146))) return 0;
        boxes[0]=stock;
        count=z7_portrait_grid_content(boxes,1);
    } else if ((source.command==0x13 || source.command==0x17) &&
        stock.x==0 && stock.y==280 && stock.w==720 && stock.h==146) {
        boxes[0]=(struct z7_portrait_box){0,440,480,219};count=1;
    } else if (source.command==0x17 && stock.x==88 && stock.y==228 && stock.w==544 && stock.h==44) {
        boxes[0]=(struct z7_portrait_box){0,370,480,70};count=1;
        if (!z7_portrait_box_from_lcd(&stock,orientation,boxes+1)) return 0;
        int32_t bottom=z7_portrait_grid_clamp(boxes[1].y+boxes[1].h,0,370);
        boxes[1].h=bottom-boxes[1].y;
        if (boxes[1].h>0) count=2;
    } else {
        count=z7_portrait_grid_edge(&stock,boxes);
        if (!count) {
            boxes[0]=stock;
            count=z7_portrait_grid_content(boxes,0);
        }
    }
    return count ? z7_portrait_draw_boxes(message,boxes,count,orientation) : 0;
}
#endif
