/* SPDX-License-Identifier: MIT. Independent native lens-source diagnostic.
 * Samples only; no text, native visibility, event or property stores.
 */
#include "module.h"
#include "../plugins/focal_sample.h"
volatile uint32_t z7_focal_sample_valid;
volatile uint32_t z7_focal_sample_tenths = 0xffffffffu;
void z7_focal_resample(void)
{
    z7_focal_sample_tenths = 0xffffffffu;
    z7_focal_sample_valid = focal_direct_sample(&z7_focal_sample_tenths);
}
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi != Z7_MODULE_ABI || api->size < 12 || api->target != Z7_MODULE_TARGET) return 1;
    z7_focal_resample();
    return 0;
}
