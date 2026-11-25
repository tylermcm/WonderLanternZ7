/* SPDX-License-Identifier: MIT.
 * Offline audit seam for af_shortcut_runtime.h. Not a camera module: it installs
 * nothing; the audit drives the runtime through z7_af_shortcut_operation.
 */
#include "module.h"
#include "af_shortcut_runtime.h"

static struct z7_af_runtime z7_af_rt;

uint32_t z7_af_shortcut_operation(uint32_t op, uint32_t a, uint32_t b, uint32_t c)
{
    switch (op) {
    case 1: return z7_af_shortcut_assign(&z7_af_rt.policy,a,b);
    case 2: return z7_af_runtime_step(&z7_af_rt,a,b,c);
    case 3: return z7_af_buttons_now();
    case 4: return z7_af_rt.applied|(z7_af_rt.refused<<8)|(z7_af_rt.last<<16);
    default: return 0;
    }
}

uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET || api->size<12) return 1;
    z7_af_shortcut_reset(&z7_af_rt.policy);
    return z7_af_area_matches() ? 0 : 1;
}
