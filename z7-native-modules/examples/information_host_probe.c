/* SPDX-License-Identifier: MIT. Owned information-host instruction diagnostic.
 * Application-byte writes below simulate a callback leaving the app only in
 * the instruction fixture. This is not the custom information-page feature.
 */
#include "information.h"
#define W(a) (*(volatile uint32_t *)(uintptr_t)(a))
volatile uint32_t z7_info_probe_cycle_mask, z7_info_probe_update_mask, z7_info_probe_api_bytes;
volatile uint32_t z7_info_probe_cycles, z7_info_probe_updates, z7_info_probe_result;
volatile uint32_t z7_info_probe_recurse_cycle, z7_info_probe_cycle_dispatch;
volatile uint32_t z7_info_probe_recurse_update, z7_info_probe_leave;
static const struct z7_module_information_api *saved;
static uint32_t cycle(void)
{
    ++z7_info_probe_cycles;
    if (z7_info_probe_recurse_cycle) {
        z7_info_probe_recurse_cycle = 0;
        ((uint32_t (*)(void))(uintptr_t)z7_info_probe_cycle_dispatch)();
    }
    return z7_info_probe_result;
}
static void update(void)
{
    ++z7_info_probe_updates;
    if (z7_info_probe_recurse_update) {
        z7_info_probe_recurse_update = 0;
        ((void (*)(void))(uintptr_t)W(0xa182d188u))();
    }
    if (z7_info_probe_leave) *(volatile uint8_t *)(uintptr_t)0xa1829af4u = 0;
}
uint32_t z7_info_probe_late_cycle(void) { return saved->register_information_cycle(cycle); }
uint32_t z7_info_probe_late_update(void) { return saved->register_before_information_update(update); }
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi != Z7_MODULE_ABI || api->target != Z7_MODULE_TARGET ||
        api->size < sizeof(struct z7_module_information_api)) return 1;
    saved = (const struct z7_module_information_api *)api;
    z7_info_probe_api_bytes = api->size;
    if (!saved->register_information_cycle || !saved->register_before_information_update) return 1;
    if (!saved->register_information_cycle(0)) z7_info_probe_cycle_mask |= 1;
    if (!saved->register_information_cycle((uint32_t (*)(void))(uintptr_t)0x102fd647u)) z7_info_probe_cycle_mask |= 2;
    if (!saved->register_information_cycle((uint32_t (*)(void))((uintptr_t)cycle & ~(uintptr_t)1))) z7_info_probe_cycle_mask |= 4;
    if (!saved->register_information_cycle((uint32_t (*)(void))((uintptr_t)&z7_info_probe_cycles | 1))) z7_info_probe_cycle_mask |= 8;
    if (saved->register_information_cycle(cycle)) z7_info_probe_cycle_mask |= 16;
    if (!saved->register_information_cycle(cycle)) z7_info_probe_cycle_mask |= 32;
    if (!saved->register_before_information_update(0)) z7_info_probe_update_mask |= 1;
    if (!saved->register_before_information_update((void (*)(void))(uintptr_t)0x102fda09u)) z7_info_probe_update_mask |= 2;
    if (!saved->register_before_information_update((void (*)(void))((uintptr_t)update & ~(uintptr_t)1))) z7_info_probe_update_mask |= 4;
    if (!saved->register_before_information_update((void (*)(void))((uintptr_t)&z7_info_probe_updates | 1))) z7_info_probe_update_mask |= 8;
    if (saved->register_before_information_update(update)) z7_info_probe_update_mask |= 16;
    if (!saved->register_before_information_update(update)) z7_info_probe_update_mask |= 32;
#ifdef Z7_INFORMATION_PROBE_FAIL
    return 1;
#else
    return z7_info_probe_cycle_mask == 63 && z7_info_probe_update_mask == 63 ? 0 : 1;
#endif
}
