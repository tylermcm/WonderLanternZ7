/* SPDX-License-Identifier: MIT. API80 SDK and host snapshot diagnostic only. */
#include "native_cache.h"
static const struct z7_module_native_cache_api *cache_api;
uint32_t z7_cache_probe_api[3];
uint32_t z7_cache_probe_operation(uint32_t operation, uint32_t output, struct z7_native_cache_snapshot *snapshot)
{
    if (!cache_api) return 0;
    if (operation == 1) return cache_api->native_cache_snapshot(output, snapshot);
    if (operation == 2) return cache_api->native_cache_snapshot_valid(output, snapshot);
    return 0;
}
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi != Z7_MODULE_ABI || api->target != Z7_MODULE_TARGET || api->size < 80) return 1;
    cache_api = (const struct z7_module_native_cache_api *)api;
    z7_cache_probe_api[0] = api->size;
    z7_cache_probe_api[1] = (uint32_t)(uintptr_t)cache_api->native_cache_snapshot;
    z7_cache_probe_api[2] = (uint32_t)(uintptr_t)cache_api->native_cache_snapshot_valid;
    return 0;
}
