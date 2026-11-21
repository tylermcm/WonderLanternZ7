/* SPDX-License-Identifier: MIT. API64 lifecycle/registration fixture. */
#include "owned_frame_coordination.h"
#define z7_main parameter_initialize
#include "parameters_host_probe.c"
#undef z7_main
static const struct z7_module_owned_frame_api *owned_frame_saved;
volatile uint32_t z7_of_mask;
static uint32_t permission(const void *frame, uint32_t native)
{ (void)frame; (void)native; return 0; }
uint32_t z7_of_late(void) { return owned_frame_saved->enable_owned_frame_coordination(); }
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->size < sizeof(*owned_frame_saved)) return 1;
    owned_frame_saved = (const struct z7_module_owned_frame_api *)api;
    if (!owned_frame_saved->enable_owned_frame_coordination) return 1;
    if (!owned_frame_saved->enable_owned_frame_coordination()) z7_of_mask |= 1;
    if (parameter_initialize(api) || !owned_frame_saved->cached.frame.register_frame_permission(permission)) return 1;
    if (!owned_frame_saved->enable_owned_frame_coordination()) z7_of_mask |= 2;
    if (!owned_frame_saved->cached.register_cached_frame_permission(permission)) return 1;
    if (owned_frame_saved->enable_owned_frame_coordination()) z7_of_mask |= 4;
    if (!owned_frame_saved->enable_owned_frame_coordination()) z7_of_mask |= 8;
#ifdef Z7_OWNED_COORD_INIT_FAIL
    return 1;
#else
    return z7_of_mask == 15 ? 0 : 1;
#endif
}
