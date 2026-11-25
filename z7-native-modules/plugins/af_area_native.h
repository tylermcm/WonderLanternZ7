/* SPDX-License-Identifier: MIT.
 * Original-Z7 C 3.80 photo AF-area mode read/write with availability checks.
 * Property 0x568 (AF-area) and 0x567 (focus mode) and their values were measured
 * in Nikon's own Photo shooting menu (AF_SHORTCUT_RESEARCH.md). Nikon's setter
 * 0x104065B0 stores and notifies but accepts any value, including modes the menu
 * greys out, so every rule the menu enforces is enforced here first.
 * GUI-context callers only; one call per press. No persistence, no input hook.
 */
#ifndef Z7_AF_AREA_NATIVE_H
#define Z7_AF_AREA_NATIVE_H
#include <stdint.h>

enum {
    AF_PROP_AREA=0x568u, AF_PROP_FOCUS=0x567u,
    AF_GET=0x104065a5u, AF_SET=0x104065b1u,
    AF_FOCUS_S=1u, AF_FOCUS_C=2u,
    AF_AREA_PINPOINT=0u, AF_AREA_SINGLE=1u, AF_AREA_DYNAMIC=2u,
    AF_AREA_WIDE_S=3u, AF_AREA_WIDE_L=4u, AF_AREA_AUTO=6u
};
enum z7_af_apply_result { AF_APPLY_REFUSED=0, AF_APPLY_SET=1, AF_APPLY_ALREADY=2, AF_APPLY_FAILED=3 };

static uint32_t z7_af_get(uint32_t key) { return ((uint32_t (*)(uint32_t))(uintptr_t)AF_GET)(key); }

/* Bit n set when area value n may be selected now. Unknown focus modes
 * (including manual focus, not yet measured) allow nothing. */
static uint32_t z7_af_area_available(void)
{
    uint32_t focus=z7_af_get(AF_PROP_FOCUS);
    uint32_t common=(1u<<AF_AREA_SINGLE)|(1u<<AF_AREA_WIDE_S)|(1u<<AF_AREA_WIDE_L)|(1u<<AF_AREA_AUTO);
    if (focus==AF_FOCUS_S) return common|(1u<<AF_AREA_PINPOINT);
    if (focus==AF_FOCUS_C) return common|(1u<<AF_AREA_DYNAMIC);
    return 0;
}

static uint32_t z7_af_area_apply(uint32_t area)
{
    if (area>31u || !(z7_af_area_available()&(1u<<area))) return AF_APPLY_REFUSED;
    if (z7_af_get(AF_PROP_AREA)==area) return AF_APPLY_ALREADY;
    uint32_t ok=((uint32_t (*)(uint32_t,uint32_t))(uintptr_t)AF_SET)(AF_PROP_AREA,area);
    return ok==1u && z7_af_get(AF_PROP_AREA)==area ? AF_APPLY_SET : AF_APPLY_FAILED;
}

static uint32_t z7_af_area_matches(void)
{
    const volatile uint32_t *get=(const volatile uint32_t *)(uintptr_t)(AF_GET-1u);
    const volatile uint32_t *set=(const volatile uint32_t *)(uintptr_t)(AF_SET-1u);
    return get[0]==0xbf03f5ceu && set[0]==0xbe1df5cfu;  /* b.w 0x101D53AE / b.w 0x101D61EE */
}
#endif
