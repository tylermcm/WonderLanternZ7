/* SPDX-License-Identifier: MIT. Independent original-Z7 after-GUI diagnostic. */
#include "gui.h"
#define W(a) (*(volatile uint32_t *)(uintptr_t)(a))
volatile uint32_t z7_gui_probe_mask, z7_gui_probe_calls, z7_gui_probe_busy_samples;
volatile uint32_t z7_gui_probe_last_busy, z7_gui_probe_recurse;
static const struct z7_module_gui_api *saved;
static void update(void)
{
    ++z7_gui_probe_calls;
    z7_gui_probe_last_busy = W(0xa1821370u + 0x34);
    if (z7_gui_probe_last_busy) ++z7_gui_probe_busy_samples;
    if (z7_gui_probe_recurse) {
        z7_gui_probe_recurse = 0;
        ((void (*)(void))(uintptr_t)W(0xa1829b14u))();
    }
}
uint32_t z7_gui_probe_late_register(void) { return saved->register_after_gui_update(update); }
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi != Z7_MODULE_ABI || api->target != Z7_MODULE_TARGET ||
        api->size < sizeof(struct z7_module_gui_api)) return 1;
    saved = (const struct z7_module_gui_api *)api;
    if (!saved->register_after_gui_update) return 1;
    if (!saved->register_after_gui_update(0)) z7_gui_probe_mask |= 1;
    if (!saved->register_after_gui_update((void (*)(void))(uintptr_t)0x1030db43u)) z7_gui_probe_mask |= 2;
    if (!saved->register_after_gui_update((void (*)(void))((uintptr_t)update & ~(uintptr_t)1))) z7_gui_probe_mask |= 4;
    if (!saved->register_after_gui_update((void (*)(void))((uintptr_t)&z7_gui_probe_calls | 1))) z7_gui_probe_mask |= 8;
    if (saved->register_after_gui_update(update)) z7_gui_probe_mask |= 16;
    if (!saved->register_after_gui_update(update)) z7_gui_probe_mask |= 32;
#ifdef Z7_GUI_PROBE_FAIL
    return 1;
#else
    return z7_gui_probe_mask == 63 ? 0 : 1;
#endif
}
