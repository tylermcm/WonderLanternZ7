/* SPDX-License-Identifier: MIT; native-snapshot instruction diagnostic. */
#include "module.h"
#include "../plugins/battery_sample.h"
volatile uint32_t z7_battery_sample_valid;
volatile uint32_t z7_battery_sample_percent = 0xffffffffu;
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi != Z7_MODULE_ABI || api->size < 12 || api->target != Z7_MODULE_TARGET) return 1;
    z7_battery_sample_valid = battery_direct_sample(&z7_battery_sample_percent);
    return 0;
}
