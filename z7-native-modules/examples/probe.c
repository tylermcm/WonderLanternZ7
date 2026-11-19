/* SPDX-License-Identifier: MIT */
#include "module.h"
/* A probe with relocated pointers into both initialized data and zeroed BSS.
 * It exports no camera hooks and performs no device operations.
 */
static volatile uint32_t result;
static const uint32_t marker = 0x5a703801u;
static volatile uint32_t * volatile result_pointer = &result;
static const uint32_t * volatile marker_pointer = &marker;
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi != Z7_MODULE_ABI || api->size < sizeof(*api) ||
        api->target != Z7_MODULE_TARGET || *result_pointer)
        return 1;
    *result_pointer = *marker_pointer;
    return 0;
}
