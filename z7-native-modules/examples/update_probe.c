/* SPDX-License-Identifier: MIT. Optional update API ownership diagnostic. */
#include "update.h"
volatile uint32_t z7_update_probe_mask, z7_update_probe_calls;
static const struct z7_module_update_api *saved;
static void update(void) { ++z7_update_probe_calls; }
uint32_t z7_update_probe_late_register(void)
{
    return saved->register_before_update(update);
}
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi != Z7_MODULE_ABI || api->target != Z7_MODULE_TARGET ||
        api->size < sizeof(struct z7_module_update_api)) return 1;
    saved = (const struct z7_module_update_api *)api;
    if (!saved->register_before_update) return 1;
    if (!saved->register_before_update(0)) z7_update_probe_mask |= 1;
    if (!saved->register_before_update((void (*)(void))(uintptr_t)0x1036b10du)) z7_update_probe_mask |= 2;
    if (!saved->register_before_update((void (*)(void))((uintptr_t)update & ~(uintptr_t)1))) z7_update_probe_mask |= 4;
    if (!saved->register_before_update((void (*)(void))((uintptr_t)&z7_update_probe_calls | 1))) z7_update_probe_mask |= 8;
    if (saved->register_before_update(update)) z7_update_probe_mask |= 16;
    if (!saved->register_before_update(update)) z7_update_probe_mask |= 32;
#ifdef Z7_UPDATE_PROBE_FAIL
    return 1;
#else
    return z7_update_probe_mask == 63 ? 0 : 1;
#endif
}
