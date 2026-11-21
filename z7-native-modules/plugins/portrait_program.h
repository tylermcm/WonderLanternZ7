/* SPDX-License-Identifier: MIT. Independent original-Z7 program observation.
 * Native1008FCD8 idles in2, awaits start in1 and stop in3. This detects observed
 * transitions, not a lock, ABA exclusion or every queued native UI request. */
#ifndef Z7_PORTRAIT_PROGRAM_H
#define Z7_PORTRAIT_PROGRAM_H
#include <stdint.h>
static uint32_t z7_portrait_program_stable(void)
{
    volatile const uint8_t *registry=(void *)(uintptr_t)0xa1815c64u;
    volatile const uint32_t *state=(void *)(uintptr_t)0xa1815c6cu;
    static const uint32_t objects[]={0xa1822d74u,0xa182ecb8u,0xa183dd90u,0xa1822e70u,0xa183d924u};
    uint32_t current=registry[0];
    if (*state!=2 || current>=5 || registry[1]!=5) return 0;
    uint32_t object=((uint32_t (*)(void))(uintptr_t)0x1008fdc1u)();
    return object==objects[current] && *state==2 && registry[0]==current && registry[1]==5;
}
#endif
