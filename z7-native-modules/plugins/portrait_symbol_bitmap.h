/* SPDX-License-Identifier: MIT. Independent original-Z7 C3.80 bitmap helper.
 * Derived from JKWTCN portrait_menu.c at50a22b24c50619cffa646dac386e8334659f475a,
 * copyright (c) 2026 JKWTCN. Caller supplies a valid native asset and serializes
 * execution; no graphics-task/bitmap-lock lifetime guarantee is provided here.
 */
#ifndef Z7_PORTRAIT_SYMBOL_BITMAP_H
#define Z7_PORTRAIT_SYMBOL_BITMAP_H
#include <stdint.h>
struct z7_portrait_symbol_bitmap {
    uint32_t width,height,depth,format,attributes[3],palette,bytes,stride,source[3];
};
static void z7_portrait_symbol_reader_release(uint32_t reader[3])
{
    ((void (*)(uint32_t *,uint32_t *,uint32_t *))(uintptr_t)0x10373b41u)(reader,reader+1,reader+2);
}
/* Returns the allocation base, not its128-byte-aligned pixel pointer. Native
 * pixel decode consumes/releases its reader. Failure before decode releases
 * the reader here; the caller releases a returned allocation after rendering. */
static uint32_t z7_portrait_symbol_bitmap_decode(uint32_t asset,uint32_t length,
    struct z7_portrait_symbol_bitmap *info)
{
    if (!asset || !length || !info) return 0;
    volatile uint32_t *fields=(volatile uint32_t *)info;
    for (uint32_t i=0;i<sizeof(*info)/4;++i) fields[i]=0;
    uint32_t reader[3]={0},allocation=0;
    ((void (*)(uint32_t *))(uintptr_t)0x104313d1u)(reader);
    if (!reader[0]) return 0;
    ((void (*)(uint32_t,uint32_t,uint32_t *,struct z7_portrait_symbol_bitmap *,uint32_t))
        (uintptr_t)0x10431279u)(asset,length,reader,info,0);
    if (!info->width || info->width>480 || !info->height || info->height>480 ||
        !info->stride || !info->bytes || info->bytes>128*1024 || info->stride>info->bytes ||
        (uint64_t)info->stride*info->height>info->bytes) {
        z7_portrait_symbol_reader_release(reader);return 0;
    }
    allocation=((uint32_t (*)(uint32_t))(uintptr_t)0x10431071u)(info->bytes+127);
    if (!allocation) {z7_portrait_symbol_reader_release(reader);return 0;}
    uint32_t output[2]={(allocation+127)&~127u,info->bytes};
    if (!((uint32_t (*)(uint32_t *,struct z7_portrait_symbol_bitmap *,const uint32_t *))
        (uintptr_t)0x104311f5u)(reader,info,output)) {
        ((void (*)(uint32_t))(uintptr_t)0x1016fe4bu)(allocation);return 0;
    }
    return allocation;
}
#endif
