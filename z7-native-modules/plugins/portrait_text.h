/* SPDX-License-Identifier: MIT.
 * Independent original-Z7 C3.80 adaptation of pinned JKWTCN portrait_menu.c,
 * 50a22b24c50619cffa646dac386e8334659f475a, copyright (c) 2026 JKWTCN.
 * Caller owns graphics execution and admits LCD/page policy. No installed hook,
 * descriptor reflow or bitmap-symbol provider interception is supplied here.
 */
#ifndef Z7_PORTRAIT_TEXT_H
#define Z7_PORTRAIT_TEXT_H
#include <stdint.h>
struct z7_portrait_text_transform {
    uint32_t orientation;
    int32_t sx, sy, dx, dy; /* 16.16 scale and portrait translation. */
};
struct z7_portrait_text_state {
    uint32_t busy, context;
    struct z7_portrait_text_transform transform;
};
static struct z7_portrait_text_state z7_portrait_text_state;
static uint32_t z7_portrait_text_span(uint32_t address, uint32_t bytes)
{
    return !(address&3u) && address>=0xa1800000u && bytes<=0x4604u &&
        address<=0xb0000000u-bytes;
}
static int64_t z7_portrait_text_product(int32_t a,int32_t b)
{ return ((int64_t)a*b)>>16; }
static uint32_t z7_portrait_text_render(uint32_t *context,void *options,
                                       const int32_t *origin,void *metrics,void *bounds)
{
    uint32_t (*render)(uint32_t *,void *,const int32_t *,void *,void *)=
        (void *)(uintptr_t)0x10539575u;
    if (!origin || metrics || bounds || !z7_portrait_text_state.busy ||
        (uint32_t)(uintptr_t)context!=z7_portrait_text_state.context)
        return render(context,options,origin,metrics,bounds);
    uint32_t *matrix=context+0x34/4;
    if (!matrix[0] || !matrix[4] || matrix[0]>0x20000u || matrix[4]>0x20000u || matrix[1] || matrix[3])
        return render(context,options,origin,metrics,bounds);
    const struct z7_portrait_text_transform *t=&z7_portrait_text_state.transform;
    int64_t ax=z7_portrait_text_product((int32_t)matrix[0],t->sx);
    int64_t ay=z7_portrait_text_product((int32_t)matrix[4],t->sy);
    int64_t tx=(int64_t)t->dx+z7_portrait_text_product((int32_t)matrix[2],t->sx);
    int64_t ty=(int64_t)t->dy+(int64_t)480*t->sy-z7_portrait_text_product((int32_t)matrix[5],t->sy);
    int64_t x=t->orientation==2 ? ty : (int64_t)720*65536-ty;
    int64_t y=t->orientation==2 ? tx : (int64_t)480*65536-tx;
    if (ax<=0 || ay<=0 || ax>0x20000 || ay>0x20000 || x<INT32_MIN || x>INT32_MAX || y<INT32_MIN || y>INT32_MAX)
        return render(context,options,origin,metrics,bounds);
    uint32_t saved[7];
    for (uint32_t i=0;i<7;++i) saved[i]=matrix[i];
    matrix[0]=matrix[4]=matrix[6]=0;
    matrix[1]=(uint32_t)(t->orientation==2 ? -ay : ay);
    matrix[2]=(uint32_t)x;
    matrix[3]=(uint32_t)(t->orientation==2 ? ax : -ax);
    matrix[5]=(uint32_t)y;
    uint32_t result=render(context,options,origin,metrics,bounds);
    for (uint32_t i=0;i<7;++i) matrix[i]=saved[i];
    return result;
}
static void z7_portrait_text_defer(uint32_t code,uint32_t result)
{ (void)code; (void)result; }
static uint32_t z7_portrait_text_draw(volatile uint32_t *message,
                                    const struct z7_portrait_text_transform *transform)
{
    if (!transform || (transform->orientation!=1 && transform->orientation!=2) ||
        transform->sx<=0 || transform->sx>0x20000 || transform->sy<=0 || transform->sy>0x20000 ||
        transform->dx< -720*65536 || transform->dx>720*65536 ||
        transform->dy< -720*65536 || transform->dy>720*65536 ||
        !z7_portrait_text_span((uint32_t)(uintptr_t)message,28) || message[3]!=0x104ba383u) return 0;
    uint32_t command=message[4]-0x42010000u;
    if (command!=0x34 && command!=0x37 && command!=0x38) return 0;
    if (!z7_portrait_text_span(message[5],command==0x38 ? 12 : 8)) return 0;
    uint32_t descriptor=*(const volatile uint32_t *)(uintptr_t)message[5];
    uint32_t context=*(const volatile uint32_t *)(uintptr_t)0xa180ad98u;
    if (!z7_portrait_text_span(descriptor,0xc8) || !z7_portrait_text_span(context,0x4604) ||
        *(const volatile uint32_t *)(uintptr_t)(descriptor+0x94)!=context ||
        *(const volatile uint32_t *)(uintptr_t)(context+0x45b4)!=0x11b6e120u ||
        *(const uint32_t *)(uintptr_t)0x11b6e13cu!=0x10539575u) return 0;
    uint32_t glyph_state=*(const volatile uint32_t *)(uintptr_t)(context+0x45d8);
    if (!z7_portrait_text_span(glyph_state,0x1bc)) return 0;
    /* Stock initialization publishes the table before allocating its state.
     * A table match alone does not establish even basic glyph readiness. */
    const volatile uint32_t *glyph=(const volatile uint32_t *)(uintptr_t)glyph_state;
    if (!z7_portrait_text_span(glyph[0x1ac/4],4) || !z7_portrait_text_span(glyph[0x18c/4],4) ||
        !z7_portrait_text_span(glyph[0x19c/4],4) || !z7_portrait_text_span(glyph[0x178/4],4)) return 0;
    if (__atomic_exchange_n(&z7_portrait_text_state.busy,1,__ATOMIC_ACQUIRE)) return 0;
    uint32_t table[8],local[7];
    for (uint32_t i=0;i<8;++i) table[i]=((const uint32_t *)(uintptr_t)0x11b6e120u)[i];
    for (uint32_t i=0;i<7;++i) local[i]=message[i];
    z7_portrait_text_state.context=context;
    z7_portrait_text_state.transform=*transform;
    table[7]=(uint32_t)(uintptr_t)z7_portrait_text_render;
    local[3]=(uint32_t)(uintptr_t)z7_portrait_text_defer;
    volatile uint32_t *provider=(volatile uint32_t *)(uintptr_t)(context+0x45b4);
    *provider=(uint32_t)(uintptr_t)table;
    ((void (*)(const uint32_t *))(uintptr_t)0x10372391u)(local);
    /* Do not overwrite a replacement published by another owner. */
    if (*provider==(uint32_t)(uintptr_t)table) *provider=0x11b6e120u;
    z7_portrait_text_state.context=0;
    __atomic_store_n(&z7_portrait_text_state.busy,0,__ATOMIC_RELEASE);
    message[6]=local[6];
    ((void (*)(uint32_t,uint32_t))(uintptr_t)0x104ba383u)(0x42010063u,local[6]);
    return 1;
}
#endif
