/* SPDX-License-Identifier: MIT. Independent original-Z7 C3.80 navigation binding.
 * Derived from JKWTCN portrait_menu.c at50a22b24c50619cffa646dac386e8334659f475a,
 * copyright (c) 2026 JKWTCN. Caller owns input task/page/layout/output admission.
 * No input hook, native screen fence, selector lifetime or touch callback here.
 */
#ifndef Z7_PORTRAIT_NAVIGATION_H
#define Z7_PORTRAIT_NAVIGATION_H
#include "portrait_input.h"
enum { Z7_PORTRAIT_NAV_MODES=17 };
static uint32_t z7_portrait_navigation(uint32_t direction,uint32_t page,uint32_t orientation)
{
    uint32_t mode=*(volatile const uint8_t *)(uintptr_t)0xa182df80u;
    if (mode>=Z7_PORTRAIT_NAV_MODES) return 0;
    /* Immutable original initializer:17 pairs of mode ID and callback. The
     * mutable RAM function slots are at A182DF88+8*mode. Never copy18 Z7II rows. */
    uint32_t function=*(const uint32_t *)(uintptr_t)(0x11eca19cu+8*mode);
    uint32_t (*stock)(uint32_t)=(void *)(uintptr_t)function;
    if ((orientation!=1 && orientation!=2) || direction>=4) return stock(direction);
    if (page==Z7_CONTROL_SETTING) return stock(z7_portrait_input_direction(direction,orientation));
    if (page!=Z7_CONTROL_GRID || *(volatile const uint8_t *)(uintptr_t)0xa18298b8u || mode ||
        *(volatile const uint32_t *)(uintptr_t)0xa2023318u!=12) return stock(direction);
    uint32_t current=((uint32_t (*)(void))(uintptr_t)0x103dd559u)();
    if (current>=12) return stock(direction);
    uint32_t target=current;
    for (uint32_t i=0;i<4;++i) {
        target=z7_portrait_input_next(target,direction,orientation);
        if (target==current) break;
        uint32_t item[2];
        ((void (*)(uint32_t *,uint32_t))(uintptr_t)0x103dde3bu)(item,target);
        if (!item[0]) break;
    }
    *(volatile uint32_t *)(uintptr_t)0xa202331cu=target;
    ((void (*)(uint32_t))(uintptr_t)0x103dde4bu)(target);
    return 0;
}
#endif
