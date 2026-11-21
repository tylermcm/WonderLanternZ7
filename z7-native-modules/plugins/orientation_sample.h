/* SPDX-License-Identifier: MIT. Independent original-Z7 C3.80 orientation read.
 * Executes the original read-only API; never selects an override or models IMU.
 * Unknown4 and out-of-range native values leave caller output unchanged.
 */
#ifndef Z7_ORIENTATION_SAMPLE_H
#define Z7_ORIENTATION_SAMPLE_H
#include <stdint.h>
static uint32_t z7_orientation_sample(uint32_t *out)
{
    if (!out) return 0;
    uint32_t value = ((uint32_t (*)(void))(uintptr_t)0x101b331bu)();
    if (value > 3) return 0;
    *out = value; return 1;
}
#endif
