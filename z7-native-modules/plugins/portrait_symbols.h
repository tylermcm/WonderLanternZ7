/* SPDX-License-Identifier: MIT. Independent original-Z7 C3.80 symbol rotation.
 * Derived from JKWTCN portrait_menu.c at50a22b24c50619cffa646dac386e8334659f475a,
 * copyright (c) 2026 JKWTCN. Caller owns serialized graphics execution and
 * native asset validity. Bitmap mutex/task/output lifetime remain unproved.
 */
#ifndef Z7_PORTRAIT_SYMBOLS_H
#define Z7_PORTRAIT_SYMBOLS_H
#include "portrait_geometry.h"
#include "portrait_symbol_bitmap.h"
struct z7_portrait_symbol_config {
    uint32_t descriptor,orientation;
    int32_t sx,sy,top,bottom;
};
struct z7_portrait_symbol_scope {
    uint32_t table[5];
    volatile uint32_t *slot;
    uint32_t provider;
    struct z7_portrait_symbol_config config;
    const struct z7_portrait_symbol_config *previous;
};
static const struct z7_portrait_symbol_config *z7_portrait_symbol_current;
static void z7_portrait_symbol_defer(uint32_t code,uint32_t result)
{ (void)code;(void)result; }
static uint32_t z7_portrait_symbol_span(uint32_t address,uint32_t bytes)
{ return !(address&3u) && address>=0xa1800000u && address<=0xb0000000u-bytes; }
static uint32_t z7_portrait_symbol_draw(const uint32_t *glyph,uint32_t capacity,
                                       uint32_t *attributes,uint32_t descriptor)
{
    (void)capacity;(void)attributes;
    const struct z7_portrait_symbol_config *p=z7_portrait_symbol_current;
    if (!p || descriptor!=p->descriptor || !glyph || !glyph[0] || !glyph[2]) return 0;
    volatile const uint8_t *d=(void *)(uintptr_t)descriptor;
    uint32_t code=glyph[1],asset=0,length=0;
    if (code>=0xe700u && code<=0xe702u && d[0x7eu+8*(code-0xe700u)]==1) {
        uint32_t override=*(volatile const uint32_t *)(d+0x80+8*(code-0xe700u));
        ((void (*)(uint32_t,uint32_t *,uint32_t *))(uintptr_t)0x104bbaebu)(override,&length,&asset);
    } else ((void (*)(uint32_t,uint32_t *,uint32_t *))(uintptr_t)0x104bbae5u)(code,&length,&asset);
    if (!asset || !length) return 0;
    uint32_t context=*(volatile const uint32_t *)(d+0x94);
    int32_t metrics[4];
    if (((uint32_t (*)(uint32_t,int32_t *))(uintptr_t)0x10476e29u)(context,metrics)) return 0;
    int64_t ascent=(int64_t)*(volatile const uint16_t *)(d+0xa)*((int64_t)metrics[1]-metrics[2])/2;
    if (ascent<INT32_MIN || ascent>INT32_MAX) return 0;
    struct z7_portrait_symbol_bitmap info;
    uint32_t allocation=z7_portrait_symbol_bitmap_decode(asset,length,&info);
    if (!allocation) return 0;
    const int32_t *m=(void *)(uintptr_t)glyph[2];
    int64_t x=m[5],baseline=m[2];
    if (p->orientation==1) {x=(int64_t)480*65536-x;baseline=(int64_t)720*65536-baseline;}
    int64_t top=baseline-((((int64_t)info.height*32768+ascent)*p->sy)>>16);
    struct z7_portrait_box box={(int32_t)(x>>16),(int32_t)(top>>16),
        (int32_t)(((int64_t)info.width*p->sx)>>16),(int32_t)(((int64_t)info.height*p->sy)>>16)},dest;
    if (box.y>=p->top && z7_portrait_box_fits(&box,480,p->bottom) &&
        z7_portrait_box_to_lcd(&box,p->orientation,&dest)) {
        uint32_t kind[5]={info.depth,info.format,info.palette,0,0};
        ((void (*)(uint32_t *))(uintptr_t)0x10431197u)(kind);
        static const uint8_t formats[]={0,1,5,7,9,10};
        if (kind[3]<sizeof(formats)) {
            uint32_t image[24];
            for (uint32_t i=0;i<24;++i) ((volatile uint32_t *)image)[i]=0;
            image[1]=formats[kind[3]];image[2]=(allocation+127)&~127u;
            image[5]=info.width|(info.height<<16);
            image[6]=(uint32_t)dest.x|((uint32_t)dest.y<<16);
            image[7]=(uint32_t)(dest.x+dest.w)|((uint32_t)(dest.y+dest.h)<<16);
            image[8]=*(volatile const uint32_t *)(d+0x28);image[14]=kind[4];
            image[15]=p->orientation==2 ? 90 : 270;
            image[19]=(info.width+15)&~15u;image[20]=(info.height+7)&~7u;
            /* Use the verified24-word message ABI. The stock dispatcher packs
             * angle/flags and removes source word18 for native image1A. */
            uint32_t local[7]={0,0,0,(uint32_t)(uintptr_t)z7_portrait_symbol_defer,
                0x4201001au,(uint32_t)(uintptr_t)image,0};
            ((void (*)(const uint32_t *))(uintptr_t)0x10372391u)(local);
            ((void (*)(void))(uintptr_t)0x1042eb0fu)();
            ((uint32_t (*)(uint32_t,uint32_t))(uintptr_t)0x10477043u)(context,image[8]);
        }
    }
    ((void (*)(uint32_t))(uintptr_t)0x1016fe4bu)(allocation);
    return 0;
}
static uint32_t z7_portrait_symbol_begin(uint32_t context,const struct z7_portrait_symbol_config *config,
                                        struct z7_portrait_symbol_scope *scope)
{
    if (!scope) return 0;
    scope->slot=0;
    if (!config || (config->orientation!=1 && config->orientation!=2) ||
        config->sx<=0 || config->sx>0x20000 || config->sy<=0 || config->sy>0x20000 ||
        config->top<0 || config->top>=config->bottom || config->bottom>720 ||
        !z7_portrait_symbol_span(config->descriptor,0xc8) || !z7_portrait_symbol_span(context,0x4604)) return 0;
    uint32_t state=*(volatile const uint32_t *)(uintptr_t)(context+0x45d8);
    if (!z7_portrait_symbol_span(state,0xbc) || *(volatile const uint32_t *)(uintptr_t)(state+0xb4)!=1) return 0;
    uint32_t provider=*(volatile const uint32_t *)(uintptr_t)(state+0xb8);
    if (!z7_portrait_symbol_span(provider,20)) return 0;
    const volatile uint32_t *source=(void *)(uintptr_t)provider;
    if (source[2]!=0x104bb461u || source[3]!=0x104bb605u || source[4]!=config->descriptor) return 0;
    for (uint32_t i=0;i<5;++i) scope->table[i]=source[i];
    scope->provider=provider;scope->config=*config;scope->previous=z7_portrait_symbol_current;
    scope->table[3]=(uint32_t)(uintptr_t)z7_portrait_symbol_draw;
    scope->slot=(void *)(uintptr_t)(state+0xb8);
    z7_portrait_symbol_current=&scope->config;
    *scope->slot=(uint32_t)(uintptr_t)scope->table;
    return 1;
}
static void z7_portrait_symbol_end(struct z7_portrait_symbol_scope *scope)
{
    if (!scope || !scope->slot) return;
    if (*scope->slot==(uint32_t)(uintptr_t)scope->table) *scope->slot=scope->provider;
    if (z7_portrait_symbol_current==&scope->config) z7_portrait_symbol_current=scope->previous;
    scope->slot=0;
}
#endif
