/* SPDX-License-Identifier: MIT. Cached primary API registration fixture. */
#include "cached_frame_permission.h"
#define z7_main parameter_initialize
#include "parameters_host_probe.c"
#undef z7_main
static const struct z7_module_cached_frame_api *cached_saved;
volatile uint32_t z7_cf_mask, z7_cf_calls, z7_cf_fields, z7_cf_native, z7_cf_decision;
static uint32_t primary_permission(const void *frame, uint32_t native)
{ (void)frame; (void)native; return 0; }
static uint32_t cached_permission(const void *fields, uint32_t native)
{
    ++z7_cf_calls; z7_cf_fields = (uint32_t)(uintptr_t)fields; z7_cf_native = native;
    return z7_cf_decision;
}
uint32_t z7_cf_late(void) { return cached_saved->register_cached_frame_permission(cached_permission); }
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->size < sizeof(*cached_saved)) return 1;
    cached_saved = (const struct z7_module_cached_frame_api *)api;
    if (!cached_saved->register_cached_frame_permission) return 1;
    if (!cached_saved->register_cached_frame_permission(cached_permission)) z7_cf_mask |= 1;
    if (parameter_initialize(api) || !cached_saved->frame.register_frame_permission(primary_permission)) return 1;
    if (!cached_saved->register_cached_frame_permission(0)) z7_cf_mask |= 2;
    if (!cached_saved->register_cached_frame_permission((void *)((uintptr_t)cached_permission & ~(uintptr_t)1))) z7_cf_mask |= 4;
    if (!cached_saved->register_cached_frame_permission((void *)((uintptr_t)&z7_cf_calls | 1))) z7_cf_mask |= 8;
    if (!cached_saved->register_cached_frame_permission((void *)(uintptr_t)0x102fd647u)) z7_cf_mask |= 16;
    if (cached_saved->register_cached_frame_permission(cached_permission)) z7_cf_mask |= 32;
    if (!cached_saved->register_cached_frame_permission(cached_permission)) z7_cf_mask |= 64;
#ifdef Z7_CACHED_INIT_FAIL
    return 1;
#else
    return z7_cf_mask == 127 ? 0 : 1;
#endif
}
