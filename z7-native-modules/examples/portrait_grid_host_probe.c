/* SPDX-License-Identifier: MIT. Independent original-Z7 API84 grid diagnostic.
 * Incomplete portrait port: no footer/text/input, pending-request fence or live
 * task/lifetime proof. Emulator only; not a release or installation candidate.
 */
#include "module.h"
#include "graphics.h"
#include "../plugins/portrait_grid_message.h"
#include "../plugins/portrait_page.h"
#include "../plugins/portrait_target.h"
#include "../plugins/orientation_sample.h"
volatile uint32_t z7_portrait_grid_received,z7_portrait_grid_handled;
static uint32_t portrait_grid_callback(volatile uint32_t *message)
{
    ++z7_portrait_grid_received;
    uint32_t orientation;
    volatile const uint8_t *scene=(void *)(uintptr_t)0xa201d4d0u;
    if (*scene || z7_portrait_imenu_page()!=Z7_PORTRAIT_GRID || !z7_portrait_lcd_target() ||
        !z7_orientation_sample(&orientation) || (orientation!=1 && orientation!=2)) return 0;
    if (*scene || z7_portrait_imenu_page()!=Z7_PORTRAIT_GRID || !z7_portrait_lcd_target()) return 0;
    uint32_t handled=z7_portrait_grid_message(message,orientation);
    z7_portrait_grid_handled+=handled;
    return handled;
}
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET || api->size<84) return 1;
    const struct z7_module_graphics_api *graphics=(const void *)api;
    return !graphics->register_graphics || !graphics->register_graphics(portrait_grid_callback);
}
