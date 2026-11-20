/* SPDX-License-Identifier: MIT. Original-Z7 DISP-cycle host API diagnostic. */
#include "disp.h"
volatile uint32_t z7_cycle_probe_mask, z7_cycle_probe_calls, z7_cycle_probe_result = 0x100;
static const struct z7_module_disp_api *saved;
static uint32_t cycle(void) { ++z7_cycle_probe_calls; return z7_cycle_probe_result; }
uint32_t z7_cycle_probe_late_register(void) { return saved->register_disp_cycle(cycle); }
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi != Z7_MODULE_ABI || api->target != Z7_MODULE_TARGET ||
        api->size < sizeof(struct z7_module_disp_api)) return 1;
    saved = (const struct z7_module_disp_api *)api;
    if (!saved->register_disp_cycle) return 1;
    if (!saved->register_disp_cycle(0)) z7_cycle_probe_mask |= 1;
    if (!saved->register_disp_cycle((uint32_t (*)(void))(uintptr_t)0x1037061du)) z7_cycle_probe_mask |= 2;
    if (!saved->register_disp_cycle((uint32_t (*)(void))((uintptr_t)cycle & ~(uintptr_t)1))) z7_cycle_probe_mask |= 4;
    if (!saved->register_disp_cycle((uint32_t (*)(void))((uintptr_t)&z7_cycle_probe_calls | 1))) z7_cycle_probe_mask |= 8;
    if (saved->register_disp_cycle(cycle)) z7_cycle_probe_mask |= 16;
    if (!saved->register_disp_cycle(cycle)) z7_cycle_probe_mask |= 32;
#ifdef Z7_CYCLE_PROBE_FAIL
    return 1;
#else
    return z7_cycle_probe_mask == 63 ? 0 : 1;
#endif
}
