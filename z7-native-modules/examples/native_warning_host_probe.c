/* SPDX-License-Identifier: MIT. API72 registration and availability fixture. */
#include "native_warning_transaction.h"
#define z7_main parameter_initialize
#include "parameters_host_probe.c"
#undef z7_main
static const struct z7_module_native_warning_api *native_saved;
volatile uint32_t z7_nf_mask;
static uint32_t permission(const void *p, uint32_t native)
{ (void)p; (void)native; return 0; }
uint32_t z7_nf_late(void) { return native_saved->enable_native_warning_transactions(); }
uint32_t z7_nf_available(void) { return native_saved->owned_warning_available(); }
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->size < sizeof(*native_saved)) return 1;
    native_saved = (const struct z7_module_native_warning_api *)api;
    if (!native_saved->enable_native_warning_transactions || !native_saved->owned_warning_available) return 1;
    if (!native_saved->enable_native_warning_transactions()) z7_nf_mask |= 1;
    if (parameter_initialize(api) || !native_saved->owned.cached.frame.register_frame_permission(permission) ||
        !native_saved->owned.cached.register_cached_frame_permission(permission)) return 1;
    if (!native_saved->enable_native_warning_transactions()) z7_nf_mask |= 2;
    if (!native_saved->owned.enable_owned_frame_coordination()) return 1;
    if (native_saved->enable_native_warning_transactions()) z7_nf_mask |= 4;
    if (!native_saved->enable_native_warning_transactions()) z7_nf_mask |= 8;
    if (native_saved->owned_warning_available()) z7_nf_mask |= 16;
#ifdef Z7_NATIVE_WARNING_INIT_FAIL
    return 1;
#else
    return z7_nf_mask == 31 ? 0 : 1;
#endif
}
