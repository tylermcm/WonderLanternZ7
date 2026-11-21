/* SPDX-License-Identifier: MIT. Independent original-Z7 C3.80 target lookup.
 * Read-only admission for LCD-sized logical targets; the wrapper selects2. Caller must establish
 * graphics-task ownership, page policy and allocation lifetime separately.
 */
#ifndef Z7_PORTRAIT_TARGET_H
#define Z7_PORTRAIT_TARGET_H
#include <stdint.h>
static uint32_t z7_portrait_lcd_target_index(uint32_t logical)
{
    if (logical>=33) return 0;
    volatile const uint32_t *registry=(void *)(uintptr_t)0xa180ad84u;
    volatile const uint32_t *outputs=(void *)(uintptr_t)0xa1821394u;
    uint32_t table=registry[1], selected=*(volatile const uint8_t *)registry;
    if ((*outputs&7u)!=1 || selected==255 || (table&3u) ||
        table<0xa1800000u || table>0xb0000000u-33u*20u) return 0;
    volatile const uint32_t *record=(void *)(uintptr_t)(table+logical*20u);
    uint32_t saved[5];
    for (uint32_t i=0;i<5;++i) saved[i]=record[i];
    if (!saved[0] || (saved[1]&255u)!=selected || (saved[1]>>16)!=720 ||
        (saved[2]&65535u)!=480) return 0;
    uint32_t matches=0;
    for (uint32_t i=0;i<33;++i)
        matches+=*(volatile const uint8_t *)(uintptr_t)(table+i*20u+4u)==selected;
    if (matches!=1 || ((uint32_t (*)(void))(uintptr_t)0x10414757u)()!=logical) return 0;
    /* Detect changes observed across the native lookup. This does not lock or
     * pin the registry, and cannot exclude ABA or later native changes. */
    if (registry[1]!=table || *(volatile const uint8_t *)registry!=selected ||
        (*outputs&7u)!=1) return 0;
    for (uint32_t i=0;i<5;++i) if (record[i]!=saved[i]) return 0;
    return 1;
}
static inline uint32_t z7_portrait_lcd_target(void)
{ return z7_portrait_lcd_target_index(2); }
#endif
