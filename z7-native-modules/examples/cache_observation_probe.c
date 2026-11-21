/* SPDX-License-Identifier: MIT. Compiled cache observation diagnostic only. */
#include "module.h"
#include "../plugins/cache_observation.h"
uint32_t z7_cache_operation(uint32_t op, struct z7_cache_observation *p, uint32_t token, uint32_t *out)
{
    switch (op) {
    case 1: return z7_cache_observation_begin(p);
    case 2: z7_cache_observation_end(p, token); return 1;
    case 3: return z7_cache_observation_ticket(p, out);
    case 4: return z7_cache_observation_valid(p, token);
    default: return 0;
    }
}
uint32_t z7_main(const struct z7_module_api *api)
{ return !api || api->abi != Z7_MODULE_ABI || api->target != Z7_MODULE_TARGET || api->size < 12; }
