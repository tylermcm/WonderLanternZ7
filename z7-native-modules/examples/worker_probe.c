/* SPDX-License-Identifier: MIT. Resident-worker instruction diagnostic only. */
#include "worker.h"
volatile uint32_t z7_worker_calls, z7_worker_api_bytes, z7_worker_registration_mask;
volatile uint32_t z7_worker_dispatch, z7_worker_recurse;
static const struct z7_module_worker_api *saved;
static void tick(void)
{
    ++z7_worker_calls;
    if (z7_worker_recurse) {
        z7_worker_recurse = 0;
        ((void (*)(void))(uintptr_t)z7_worker_dispatch)();
    }
}
uint32_t z7_worker_late(void) { return saved->register_worker(tick); }
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi != Z7_MODULE_ABI || api->target != Z7_MODULE_TARGET ||
        api->size < sizeof(struct z7_module_worker_api)) return 1;
    saved = (const struct z7_module_worker_api *)api;
    z7_worker_api_bytes = api->size;
    if (!saved->register_worker) return 1;
    if (!saved->register_worker(0)) z7_worker_registration_mask |= 1;
    if (!saved->register_worker((void (*)(void))(uintptr_t)0x102fd647u)) z7_worker_registration_mask |= 2;
    if (!saved->register_worker((void (*)(void))((uintptr_t)tick & ~(uintptr_t)1))) z7_worker_registration_mask |= 4;
    if (!saved->register_worker((void (*)(void))((uintptr_t)&z7_worker_calls | 1))) z7_worker_registration_mask |= 8;
    if (saved->register_worker(tick)) z7_worker_registration_mask |= 16;
    if (!saved->register_worker(tick)) z7_worker_registration_mask |= 32;
#ifdef Z7_WORKER_PROBE_FAIL
    return 1;
#else
    return z7_worker_registration_mask == 63 ? 0 : 1;
#endif
}
