/* SPDX-License-Identifier: MIT. Offline policy probe, not a camera module. */
#include "module.h"
#include "../plugins/af_shortcut_policy.h"
struct z7_af_shortcut_policy z7_af_policy;
uint32_t z7_af_shortcut_operation(uint32_t op,uint32_t a,uint32_t b,uint32_t c)
{
    switch(op) {
    case 0:z7_af_shortcut_reset(&z7_af_policy);return 1;
    case 1:return z7_af_shortcut_assign(&z7_af_policy,a,b);
    case 2:z7_af_shortcut_capture(&z7_af_policy,a,b);return 0;
    case 3:return z7_af_shortcut_take(&z7_af_policy,a,b,c&31u,c>>5);
    default:return 0;
    }
}
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET || api->size<12) return 1;
    z7_af_shortcut_reset(&z7_af_policy);return 0;
}
