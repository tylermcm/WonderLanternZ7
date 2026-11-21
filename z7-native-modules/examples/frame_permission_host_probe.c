/* SPDX-License-Identifier: MIT. Optional consumption callback host fixture. */
#include "frame_permission.h"
#define z7_main parameter_initialize
#include "parameters_host_probe.c"
#undef z7_main
static const struct z7_module_frame_permission_api *frame_saved;
volatile uint32_t z7_fp_mask, z7_fp_calls, z7_fp_frame, z7_fp_native, z7_fp_decision;
static uint32_t permission(const void *frame, uint32_t native)
{
    ++z7_fp_calls; z7_fp_frame = (uint32_t)(uintptr_t)frame; z7_fp_native = native;
    return z7_fp_decision;
}
uint32_t z7_fp_late(void) { return frame_saved->register_frame_permission(permission); }
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->size < sizeof(*frame_saved)) return 1;
    frame_saved = (const struct z7_module_frame_permission_api *)api;
    if (!frame_saved->register_frame_permission) return 1;
    if (!frame_saved->register_frame_permission(permission)) z7_fp_mask |= 1;
    if (parameter_initialize(api)) return 1;
    if (!frame_saved->register_frame_permission(0)) z7_fp_mask |= 2;
    if (!frame_saved->register_frame_permission((void *)((uintptr_t)permission & ~(uintptr_t)1))) z7_fp_mask |= 4;
    if (!frame_saved->register_frame_permission((void *)((uintptr_t)&z7_fp_calls | 1))) z7_fp_mask |= 8;
    if (!frame_saved->register_frame_permission((void *)(uintptr_t)0x102fd647u)) z7_fp_mask |= 16;
    if (frame_saved->register_frame_permission(permission)) z7_fp_mask |= 32;
    if (!frame_saved->register_frame_permission(permission)) z7_fp_mask |= 64;
#ifdef Z7_FRAME_INIT_FAIL
    return 1;
#else
    return z7_fp_mask == 127 ? 0 : 1;
#endif
}
