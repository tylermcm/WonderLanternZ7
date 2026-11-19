/* SPDX-License-Identifier: MIT; independent original-Z7 C 3.80 sample policy.
 * The native snapshot contract and bar fallback are documented in
 * Z7_BATTERY_DISPLAY_RESEARCH.md. Caller schedules sampling on its own task.
 * No hardware telemetry or controller-transition validation is implied.
 */
#ifndef Z7_BATTERY_SAMPLE_H
#define Z7_BATTERY_SAMPLE_H
#include <stdint.h>
static uint32_t battery_direct_sample(volatile uint32_t *percent)
{
    const volatile uint32_t *fallback = (const volatile uint32_t *)(uintptr_t)0xa18b4de8u;
    if (!percent || *fallback) return 0;
    _Alignas(4) uint32_t snapshot[14];
    ((void (*)(uint32_t *))(uintptr_t)0x10437685u)(snapshot);
    uint32_t kind = snapshot[1] & 255u;
    if (*fallback || snapshot[0] != 1 || !kind || kind > 6 || snapshot[6] > 100) return 0;
    *percent = snapshot[6];
    return 1;
}
#endif
