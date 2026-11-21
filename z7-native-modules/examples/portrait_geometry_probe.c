/* SPDX-License-Identifier: MIT. Native sampling/portrait geometry diagnostic. */
#include "module.h"
#include "../plugins/portrait_geometry.h"
#include "../plugins/orientation_sample.h"
uint32_t z7_portrait_probe_operation(uint32_t operation, uint32_t orientation,
                                    const struct z7_portrait_box *in, struct z7_portrait_box *out)
{
    if (operation == 0) return z7_orientation_sample((uint32_t *)out);
    if (operation == 1) return z7_portrait_box_from_lcd(in,orientation,out);
    if (operation == 2) return z7_portrait_box_to_lcd(in,orientation,out);
    return 0;
}
uint32_t z7_main(const struct z7_module_api *api)
{ return !api || api->abi != Z7_MODULE_ABI || api->target != Z7_MODULE_TARGET || api->size < 12; }
