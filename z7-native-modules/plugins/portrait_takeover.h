/* SPDX-License-Identifier: MIT. Independent original-Z7 native task guard.
 * Observation only: no task lock, allocation pin or pending-request fence.
 */
#ifndef Z7_PORTRAIT_TAKEOVER_H
#define Z7_PORTRAIT_TAKEOVER_H
#include <stdint.h>
static uint32_t z7_portrait_native_takeover(void)
{
    uint32_t menu=((uint32_t (*)(void))(uintptr_t)0x1048b0e5u)();
    uint32_t play=((uint32_t (*)(void))(uintptr_t)0x105006e5u)();
    if (menu!=0xa182ecb8u || play!=0xa183dd90u) return 1;
    volatile const uint32_t *m=(void *)(uintptr_t)menu, *p=(void *)(uintptr_t)play;
    if (m[0x38/4]!=0x1048b143u || m[0x3c/4]!=0x1048b18bu ||
        p[0x38/4]!=0x1050072fu || p[0x3c/4]!=0x10500747u) return 1;
    uint32_t a=((uint32_t (*)(uint32_t))(uintptr_t)0x10465021u)(menu);
    uint32_t b=((uint32_t (*)(uint32_t))(uintptr_t)0x10465021u)(play);
    /* Native states1..3 own transitions/work; stock inactive state is4.
     * State0 is initial. Unknown states reject rather than indexing callbacks. */
    if ((a!=0 && a!=4) || (b!=0 && b!=4)) return 1;
    return *(volatile const uint8_t *)(uintptr_t)(menu+0x74u)!=a ||
        *(volatile const uint8_t *)(uintptr_t)(play+0x74u)!=b ||
        m[0x38/4]!=0x1048b143u || m[0x3c/4]!=0x1048b18bu ||
        p[0x38/4]!=0x1050072fu || p[0x3c/4]!=0x10500747u;
}
#endif
