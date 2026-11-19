/* SPDX-License-Identifier: MIT. Compiled settings model diagnostic, no native UI.
 */
#include "module.h"
#include "../plugins/display_settings.c"
struct z7_display_settings z7_settings_model;
uint8_t z7_settings_input[64], z7_settings_output[64];
volatile uint32_t z7_settings_command;
__attribute__((noinline)) uint32_t z7_settings_operation(uint32_t operation, uint32_t a, uint32_t b, uint32_t c)
{
    switch (operation) {
    case 0: z7_settings_defaults(&z7_settings_model); return 1;
    case 1: return z7_settings_encode(&z7_settings_model, z7_settings_output, a);
    case 2: return z7_settings_decode(z7_settings_input, a, &z7_settings_model);
    case 3: return z7_settings_page(&z7_settings_model, a, b);
    case 4: return z7_settings_reset(&z7_settings_model, a);
    case 5: return z7_settings_next(&z7_settings_model, a);
    case 6: return z7_settings_information(&z7_settings_model, a, b, c);
    case 7: return z7_settings_component(&z7_settings_model, a, b, c);
    case 8: return z7_settings_flag(&z7_settings_model, a, b);
    default: return 0;
    }
}
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi != Z7_MODULE_ABI || api->size < 12 || api->target != Z7_MODULE_TARGET) return 1;
    return z7_settings_operation(z7_settings_command, 0, 0, 0) == 1 ? 0 : 1;
}
