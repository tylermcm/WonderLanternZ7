/* SPDX-License-Identifier: MIT.
 * Original-Z7 C 3.80 AF-area shortcut runtime: GUI-task polling of Nikon's
 * switch-state words, press edges into af_shortcut_policy.h, and the validated
 * AF-area write of af_area_native.h. Design follows JKWTCN's MIT AF shortcut
 * (press edge captured, applied once in GUI context); bindings are independent.
 *
 * Nikon's switch object 0xA1F90AA0 (returned by 0x101B4A60) holds one 0x14-byte
 * group per switch word: +0 current, +4 previous, +8 changed, +0xC pressed,
 * +0x10 released (edge routine 0x101AE622). Group words: SW0 0xA1F90AA4,
 * SW1 0xA1F90AB8, SW2 0xA1F90ACC. Pressing through Nikon's AutoOperation path in
 * assisted QEMU set Fn1 (SW0 0x4000), AF-ON (SW0 0x200000), the sub-selector
 * center (SW2 0x8000), Fn2 (SW2 0x4000) and the movie button (SW1 0x2000) while
 * held (Fn2 and movie only from the shooting screen; the menu masks them). Polling at GUI rate can miss a press shorter than
 * one GUI update; that bound is measured on the camera, not assumed.
 */
#ifndef Z7_AF_SHORTCUT_RUNTIME_H
#define Z7_AF_SHORTCUT_RUNTIME_H
#include "af_shortcut_policy.h"
#include "af_area_native.h"

enum { AF_SW0=0xa1f90aa4u, AF_SW1=0xa1f90ab8u, AF_SW2=0xa1f90accu };
enum { AF_BUTTON_FN1=0, AF_BUTTON_AF_ON=1, AF_BUTTON_FN2=2, AF_BUTTON_SS_CENTER=3, AF_BUTTON_MOVIE=4 };
static const uint32_t z7_af_button_word[Z7_AF_BUTTONS]={AF_SW0,AF_SW0,AF_SW2,AF_SW2,AF_SW1};
static const uint32_t z7_af_button_mask[Z7_AF_BUTTONS]={0x4000u,0x200000u,0x4000u,0x8000u,0x2000u};
#define Z7_AF_VERIFIED_BUTTONS 0x1fu

/* f2 Custom control assignment properties, measured by changing each in Nikon's
 * menu in assisted QEMU: Fn1 0x1048, Fn2 0x104C, AF-ON 0x1050, sub-selector center
 * 0x1054, movie record 0x1057. One shared function enum; None = 0. */
static const uint32_t z7_af_button_property[Z7_AF_BUTTONS]={0x1048u,0x1050u,0x104cu,0x1054u,0x1057u};
#define AF_ASSIGN_NONE 0u

/* Buttons whose native f2 assignment is None: only these may act. */
static uint32_t z7_af_native_none_buttons(void)
{
    uint32_t none=0;
    for (uint32_t i=0;i<Z7_AF_BUTTONS;++i)
        if (z7_af_button_property[i] && z7_af_get(z7_af_button_property[i])==AF_ASSIGN_NONE) none|=1u<<i;
    return none;
}

/* Z7 logical targets: target = AF-area value + 1 for the six measured modes. */
#define Z7_AF_TARGET_AREA(t) ((t)-1u)
#define Z7_AF_Z7_TARGETS ((1u<<0)|(1u<<1)|(1u<<2)|(1u<<3)|(1u<<4)|(1u<<6))

struct z7_af_runtime {
    struct z7_af_shortcut_policy policy;
    uint32_t previous, applied, refused, last;
};

static uint32_t z7_af_buttons_now(void)
{
    uint32_t now=0;
    for (uint32_t i=0;i<Z7_AF_BUTTONS;++i)
        if ((Z7_AF_VERIFIED_BUTTONS>>i&1u) &&
            (*(const volatile uint32_t *)(uintptr_t)z7_af_button_word[i]&z7_af_button_mask[i])) now|=1u<<i;
    return now;
}

/* GUI task, once per update. Returns the apply result of a taken press, or 0. */
static uint32_t z7_af_runtime_step(struct z7_af_runtime *r, uint32_t photo_context,
                                   uint32_t busy, uint32_t native_none_buttons)
{
    uint32_t now=z7_af_buttons_now();
    uint32_t edges=now&~r->previous;
    r->previous=now;
    z7_af_shortcut_capture(&r->policy,photo_context,edges);
    uint32_t available=z7_af_area_available()&Z7_AF_Z7_TARGETS;  /* bit (target-1) == bit area */
    uint32_t taken=z7_af_shortcut_take(&r->policy,photo_context,busy,native_none_buttons&Z7_AF_VERIFIED_BUTTONS,available);
    if (!taken) return 0;
    uint32_t result=z7_af_area_apply(Z7_AF_TARGET_AREA(taken&0xffu));
    r->last=taken;
    if (result==AF_APPLY_SET || result==AF_APPLY_ALREADY) ++r->applied; else ++r->refused;
    return result;
}
#endif
