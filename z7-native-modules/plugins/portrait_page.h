/* SPDX-License-Identifier: MIT. Independent original-Z7 i-menu page binding.
 * Informed by JKWTCN portrait_menu.c, pinned50a22b24c50619cffa646dac386e8334659f475a,
 * copyright (c) 2026 JKWTCN. See NOTICE.md. Page classification alone does not
 * admit drawing: caller must fence pending native requests, validate
 * scene/output/target and own graphics execution and descriptor lifetime.
 */
#ifndef Z7_PORTRAIT_PAGE_H
#define Z7_PORTRAIT_PAGE_H
#include <stdint.h>
#include "portrait_takeover.h"
enum z7_portrait_imenu_page {
    Z7_PORTRAIT_OTHER, Z7_PORTRAIT_GRID, Z7_PORTRAIT_DIAL, Z7_PORTRAIT_SETTING
};
static uint32_t z7_portrait_imenu_page(void)
{
    volatile const uint8_t *app=(void *)(uintptr_t)0xa1829af4u;
    volatile const uint32_t *roots=(void *)(uintptr_t)0xa20207bcu;
    volatile const uint8_t *state=(void *)(uintptr_t)0xa18298b8u;
    if (z7_portrait_native_takeover() || *app!=3 || roots[3]!=0xa1829970u) return Z7_PORTRAIT_OTHER;
    uint32_t mode=((uint32_t (*)(void))(uintptr_t)0x10385b6bu)();
    uint32_t variant=((uint32_t (*)(void))(uintptr_t)0x10385b73u)();
    if (z7_portrait_native_takeover() || *app!=3 || roots[3]!=0xa1829970u || state[0]!=mode || state[1]!=variant)
        return Z7_PORTRAIT_OTHER;
    if (mode==3) return Z7_PORTRAIT_GRID;
    if (variant==0 || variant==0x29) {
        if (mode==0) return Z7_PORTRAIT_GRID;
        if (mode==2) return Z7_PORTRAIT_DIAL;
    }
    return mode<=2 ? Z7_PORTRAIT_SETTING : Z7_PORTRAIT_OTHER;
}
#endif
