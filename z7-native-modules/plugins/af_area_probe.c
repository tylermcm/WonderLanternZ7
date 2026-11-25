/* SPDX-License-Identifier: MIT.
 * Offline audit seam for af_area_native.h. Not a camera module: it installs
 * nothing and exposes only a callable operation for the Unicorn audit.
 */
#include "module.h"
#include "af_area_native.h"

uint32_t z7_af_operation(uint32_t op, uint32_t a)
{
    switch (op) {
    case 1: return z7_af_area_available();
    case 2: return z7_af_area_apply(a);
    case 3: return z7_af_area_matches();
    default: return 0;
    }
}

uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET || api->size<12) return 1;
    return z7_af_area_matches() ? 0 : 1;
}
