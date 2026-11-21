/* SPDX-License-Identifier: MIT. Independent original-Z7 API84 portrait diagnostic.
 * Incomplete port: menu text placement; no inline symbols/input, pending-request fence or live
 * task/lifetime proof. Emulator only; not a release or installation candidate.
 */
#include "module.h"
#include "graphics.h"
#include "../plugins/portrait_layout.h"
#include "../plugins/portrait_bands.h"
#include "../plugins/portrait_text_layout.h"
#include "../plugins/portrait_page.h"
#include "../plugins/portrait_target.h"
#include "../plugins/orientation_sample.h"
volatile uint32_t z7_portrait_grid_received,z7_portrait_grid_handled;
struct z7_portrait_layout z7_portrait_grid_layout;
struct z7_portrait_bands z7_portrait_grid_bands;
static uint32_t portrait_grid_callback(volatile uint32_t *message)
{
    ++z7_portrait_grid_received;
    uint32_t orientation=4,page=z7_portrait_imenu_page();
    volatile const uint8_t *scene=(void *)(uintptr_t)0xa201d4d0u;
    volatile const uint32_t *outputs=(void *)(uintptr_t)0xa1821394u;
    if (*scene || page==Z7_PORTRAIT_OTHER || (*outputs&7u)!=1) {
        z7_portrait_layout_reset(&z7_portrait_grid_layout);
        z7_portrait_bands_forget(&z7_portrait_grid_bands);return 0;
    }
    if (!z7_portrait_lcd_target()) {
        if (z7_portrait_lcd_target_index(1)) z7_portrait_bands_observe_clear(&z7_portrait_grid_bands,message);
        return 0;
    }
    z7_orientation_sample(&orientation); /* Unknown leaves the entry in landscape. */
    uint32_t after=z7_portrait_imenu_page();
    if (*scene || after!=page || (*outputs&7u)!=1) {
        if (*scene || after==Z7_PORTRAIT_OTHER || (*outputs&7u)!=1) {
            z7_portrait_layout_reset(&z7_portrait_grid_layout);
            z7_portrait_bands_forget(&z7_portrait_grid_bands);
        }
        return 0;
    }
    if (!z7_portrait_lcd_target()) return 0;
    uint32_t layout_page=page==Z7_PORTRAIT_GRID ? Z7_LAYOUT_GRID :
        page==Z7_PORTRAIT_DIAL ? Z7_LAYOUT_DIAL : Z7_LAYOUT_SETTING;
    uint32_t layout=z7_portrait_layout_choose(&z7_portrait_grid_layout,message,layout_page,orientation);
    z7_portrait_bands_before(&z7_portrait_grid_bands,message,layout_page,layout);
    if (layout!=1 && layout!=2) return 0;
    uint32_t handled=z7_portrait_text_page_draw(message,layout_page,layout,&z7_portrait_grid_bands);
    if (!handled) handled=z7_portrait_page_message(message,layout_page,layout);
    z7_portrait_grid_handled+=handled;
    return handled;
}
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET || api->size<84) return 1;
    const struct z7_module_graphics_api *graphics=(const void *)api;
    return !graphics->register_graphics || !graphics->register_graphics(portrait_grid_callback);
}
