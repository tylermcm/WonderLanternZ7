/* SPDX-License-Identifier: MIT. Independent original-Z7 C3.80 lens sampling.
 * Original native focal PTP path1034231A reads1C01 via103FE85E and scales by10
 * for hundredths of mm. The native lens producer1016342E publishes tenths.
 * GUI/output lifetime, formatting and scheduling belong to the caller.
 */
#ifndef Z7_FOCAL_SAMPLE_H
#define Z7_FOCAL_SAMPLE_H
#include <stdint.h>
static uint32_t focal_direct_sample(volatile uint32_t *tenths)
{
    if (!tenths) return 0;
    uint32_t (*get)(uint32_t) = (uint32_t (*)(uint32_t))(uintptr_t)0x103fe85fu;
    uint32_t type = get(0x1c14u);
    if (type != 1u && type != 3u) return 0;
    uint32_t value = get(0x1c01u);
    if (!value || value == 0xffffffffu || get(0x1c14u) != type) return 0;
    *tenths = value;
    return 1;
}
#endif
