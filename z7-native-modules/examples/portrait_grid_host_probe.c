/* SPDX-License-Identifier: MIT. Independent original-Z7 API84 portrait diagnostic.
 * Incomplete port: menu text/symbol placement; no input, pending-request fence or live
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
#ifdef Z7_PORTRAIT_NAVIGATION_DIAGNOSTIC
#include "navigation.h"
#include "../plugins/portrait_navigation.h"
volatile uint32_t z7_portrait_nav_received,z7_portrait_nav_handled;
#endif
#ifdef Z7_PORTRAIT_TOUCH_DIAGNOSTIC
#include "touch.h"
volatile uint32_t z7_portrait_touch_received,z7_portrait_touch_handled;
#endif
#ifdef Z7_PORTRAIT_TOUCH_DIAGNOSTIC
#include "../plugins/portrait_program.h"
static uint32_t portrait_observed_page(void)
{
    if (!z7_portrait_program_stable()) return Z7_PORTRAIT_OTHER;
    uint32_t page=z7_portrait_imenu_page();
    return z7_portrait_program_stable() ? page : Z7_PORTRAIT_OTHER;
}
#else
#define portrait_observed_page z7_portrait_imenu_page
#endif
volatile uint32_t z7_portrait_grid_received,z7_portrait_grid_handled;
struct z7_portrait_layout z7_portrait_grid_layout;
struct z7_portrait_bands z7_portrait_grid_bands;
#ifdef Z7_PORTRAIT_NAVIGATION_DIAGNOSTIC
static uint32_t portrait_navigation_callback(uint32_t direction,uint32_t *result)
{
    ++z7_portrait_nav_received;
    uint32_t page=portrait_observed_page();
    volatile const uint8_t *scene=(void *)(uintptr_t)0xa201d4d0u;
    volatile const uint32_t *outputs=(void *)(uintptr_t)0xa1821394u;
    uint32_t layout=__atomic_load_n(&z7_portrait_grid_layout.orientation,__ATOMIC_ACQUIRE);
    if (*scene || (*outputs&7u)!=1 || (layout!=1 && layout!=2) ||
        (page!=Z7_PORTRAIT_GRID && page!=Z7_PORTRAIT_SETTING) || !result) return 0;
    uint32_t after=portrait_observed_page();
    if (after!=page || *scene || (*outputs&7u)!=1 ||
        __atomic_load_n(&z7_portrait_grid_layout.orientation,__ATOMIC_ACQUIRE)!=layout) return 0;
    *result=z7_portrait_navigation(direction,page==Z7_PORTRAIT_GRID ? Z7_CONTROL_GRID : Z7_CONTROL_SETTING,layout);
    ++z7_portrait_nav_handled;return 1;
}
#endif
#ifdef Z7_PORTRAIT_TOUCH_DIAGNOSTIC
static uint32_t portrait_touch_callback(const uint32_t *event,uint32_t *copy)
{
    ++z7_portrait_touch_received;
    uint32_t page=portrait_observed_page();
    volatile const uint8_t *scene=(void *)(uintptr_t)0xa201d4d0u;
    volatile const uint32_t *outputs=(void *)(uintptr_t)0xa1821394u;
    uint32_t layout=__atomic_load_n(&z7_portrait_grid_layout.orientation,__ATOMIC_ACQUIRE);
    if (*scene || (*outputs&7u)!=1 || (layout!=1 && layout!=2) ||
        (page!=Z7_PORTRAIT_GRID && page!=Z7_PORTRAIT_DIAL && page!=Z7_PORTRAIT_SETTING)) return 0;
    uint32_t control=page==Z7_PORTRAIT_GRID ? Z7_CONTROL_GRID :
        page==Z7_PORTRAIT_DIAL ? Z7_CONTROL_DIAL : Z7_CONTROL_SETTING;
    if (!z7_portrait_input_event(event,copy,control,layout)) return 0;
    if (portrait_observed_page()!=page || *scene || (*outputs&7u)!=1 ||
        __atomic_load_n(&z7_portrait_grid_layout.orientation,__ATOMIC_ACQUIRE)!=layout) return 0;
    ++z7_portrait_touch_handled;return 1;
}
#endif
static uint32_t portrait_grid_callback(volatile uint32_t *message)
{
    ++z7_portrait_grid_received;
    uint32_t orientation=4,page=portrait_observed_page();
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
    uint32_t after=portrait_observed_page();
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
    if (!api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET ||
#ifdef Z7_PORTRAIT_TOUCH_DIAGNOSTIC
        api->size<92
#elif defined(Z7_PORTRAIT_NAVIGATION_DIAGNOSTIC)
        api->size<88
#else
        api->size<84
#endif
        ) return 1;
    const struct z7_module_graphics_api *graphics=(const void *)api;
#ifdef Z7_PORTRAIT_NAVIGATION_DIAGNOSTIC
    const struct z7_module_navigation_api *nav=(const void *)api;
    if (!graphics->register_graphics || !graphics->register_graphics(portrait_grid_callback)) return 1;
#ifdef Z7_PORTRAIT_TOUCH_DIAGNOSTIC
    if (!nav->register_navigation || !nav->register_navigation(portrait_navigation_callback)) return 1;
    const struct z7_module_touch_api *touch=(const void *)api;
    return !touch->register_touch || !touch->register_touch(portrait_touch_callback);
#else
    return !nav->register_navigation || !nav->register_navigation(portrait_navigation_callback);
#endif
#else
    return !graphics->register_graphics || !graphics->register_graphics(portrait_grid_callback);
#endif
}
