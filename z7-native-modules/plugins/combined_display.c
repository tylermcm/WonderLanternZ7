/* SPDX-License-Identifier: MIT
 * Independent original-Z7 combined display entrypoint. Included components
 * retain their JKWTCN/WonderLanternZ7 MIT notices and native interface scope.
 */
#include "module.h"
#include "display.h"
#ifdef Z7_HIGHLIGHT_CONTEXT_PROBE
#include "highlight.h"
#ifdef Z7_HIGHLIGHT_PARAMETERS_PROBE
#include "parameters.h"
#endif
#ifdef Z7_HIGHLIGHT_FRAME_PROBE
#include "frame_permission.h"
#endif
static void highlight_gui_publish(void);
#endif
#ifdef Z7_SETTINGS_PERSISTENCE
#include "worker.h"
#endif
#ifdef Z7_INFORMATION_APP_PROBE
#include "information.h"
#include "information_transition.h"
struct z7_information_transition z7_information_ledger;
volatile uint32_t z7_information_suspended, z7_information_pending, z7_information_target;
volatile uint32_t z7_information_entries, z7_information_returns, z7_information_errors;
static uint32_t information_saved, information_previous;
static uint32_t information_preset_cycle(void);
static uint32_t information_native_cycle(void);
static void information_sync_preset(void);
static void information_before_update(void);
static void information_after_gui(void);
static uint32_t information_components_blocked(void)
{
    return z7_information_suspended || z7_information_ledger.phase != IT_IDLE ||
        *(volatile uint8_t *)(uintptr_t)0xa1829af4u != 0;
}
#define Z7_INFORMATION_CONFIG_BLOCKED information_components_blocked()
#else
#define Z7_INFORMATION_CONFIG_BLOCKED (z7_menu_settings.enabled_pages & 16u)
#endif
#ifdef Z7_SETTINGS_READOUT_PROBE
#include "update.h"
#endif
#ifdef Z7_SETTINGS_DISP_PROBE
#include "disp.h"
#endif
#ifdef Z7_HISTOGRAM_EXTRA_PROBE
#include "gui.h"
static uint32_t histogram_before(void);
#endif
#ifdef Z7_FOCAL_OVERLAY_PROBE
static uint32_t focal_before_update(void);
static void focal_note_update(uint32_t changed);
#endif

/* Component initializers prepare owned data through a local staging API. Only
 * this entrypoint registers with the host and commits native scalar masks.
 */
#define z7_main battery_initialize
#define hooks battery_hooks
#include "battery_percent.c"
#undef hooks
#undef z7_main
#define Z7_GRID_DEFER_MASKS 1
#define z7_main grid_initialize
#define hooks grid_hooks
#include "grids_histogram.c"
#undef hooks
#undef z7_main
#undef Z7_GRID_DEFER_MASKS
#ifdef Z7_SETTINGS_MENU_PROBE
#include "../examples/settings_menu_policy.h"
#endif
#ifdef Z7_HISTOGRAM_EXTRA_PROBE
#include "../examples/display_histogram_policy.h"
#endif
#ifdef Z7_FOCAL_OVERLAY_PROBE
#include "../examples/display_focal_policy.h"
static void focal_combined_after_gui(void)
{
    histogram_after_gui();
    focal_after_gui();
#ifdef Z7_INFORMATION_APP_PROBE
    information_after_gui();
#endif
#ifdef Z7_HIGHLIGHT_CONTEXT_PROBE
    highlight_gui_publish();
#endif
}
#endif
#ifdef Z7_INFORMATION_APP_PROBE
#include "../examples/display_information_policy.h"
#endif
#ifdef Z7_SETTINGS_PERSISTENCE
#include "../examples/display_persistence_policy.h"
#endif
#ifdef Z7_HIGHLIGHT_CONTEXT_PROBE
#include "../examples/display_highlight_context_policy.h"
#endif

#ifdef Z7_CLEAN_DISPLAY_PROBE
#include "../examples/clean_display_policy.h"
#ifdef Z7_DISP_KEY_PROBE
#define Z7_COMBINED_BEFORE disp_key_before
#else
#define Z7_COMBINED_BEFORE clean_before
#endif
#else
#ifdef Z7_SETTINGS_MENU_PROBE
#define Z7_COMBINED_BEFORE sm_before
#else
#define Z7_COMBINED_BEFORE before
#endif
#endif

static const struct z7_display_hooks *pending_grid, *pending_battery;
static const struct z7_grid_menu *pending_menu;
static uint32_t stage_display(const struct z7_display_hooks *h)
{
    if (h == &grid_hooks && !pending_grid) { pending_grid = h; return 1; }
    if (h == &battery_hooks && !pending_battery) { pending_battery = h; return 1; }
    return 0;
}
static uint32_t stage_menu(const struct z7_grid_menu *m)
{
    if (m != &menu || pending_menu) return 0;
    pending_menu = m;
    return 1;
}
static const struct z7_module_api staging = {
    Z7_MODULE_ABI, sizeof(staging), Z7_MODULE_TARGET, stage_display, stage_menu
};
static const struct z7_display_hooks combined_hooks = {
    Z7_DISPLAY_ABI, sizeof(combined_hooks), grid_source, grid_geometry,
    scalar_value, histogram_gate, Z7_COMBINED_BEFORE, after
};
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi != Z7_MODULE_ABI || api->target != Z7_MODULE_TARGET ||
        api->size < sizeof(*api) || !api->register_display || !api->register_grid_menu) return 1;
#ifdef Z7_SETTINGS_PERSISTENCE
    const struct z7_module_worker_api *worker_api = (const struct z7_module_worker_api *)api;
    if (api->size < sizeof(*worker_api) || !worker_api->register_worker) return 1;
#endif
#ifdef Z7_HIGHLIGHT_CONTEXT_PROBE
    const struct z7_module_highlight_api *highlight_api = (const struct z7_module_highlight_api *)api;
    if (api->size < sizeof(*highlight_api) || !highlight_api->register_highlight) return 1;
#endif
#ifdef Z7_HIGHLIGHT_PARAMETERS_PROBE
    const struct z7_module_parameters_api *parameter_api = (const struct z7_module_parameters_api *)api;
    if (api->size < sizeof(*parameter_api) || !parameter_api->register_parameters) return 1;
#endif
#ifdef Z7_HIGHLIGHT_FRAME_PROBE
    const struct z7_module_frame_permission_api *frame_api = (const struct z7_module_frame_permission_api *)api;
    if (api->size < sizeof(*frame_api) || !frame_api->register_frame_permission) return 1;
#endif
#ifdef Z7_SETTINGS_READOUT_PROBE
    const struct z7_module_update_api *update_api = (const struct z7_module_update_api *)api;
    if (api->size < sizeof(*update_api) || !update_api->register_before_update) return 1;
#endif
#ifdef Z7_SETTINGS_DISP_PROBE
    const struct z7_module_disp_api *disp_api = (const struct z7_module_disp_api *)api;
    if (api->size < sizeof(*disp_api) || !disp_api->register_disp_cycle) return 1;
#endif
#ifdef Z7_DISP_KEY_PROBE
    if (W(0xa1829b0cu) != 0x1030da57u) return 1;
#endif
#ifdef Z7_HISTOGRAM_EXTRA_PROBE
    const struct z7_module_gui_api *gui_api = (const struct z7_module_gui_api *)api;
    if (api->size < sizeof(*gui_api) || !gui_api->register_after_gui_update) return 1;
#endif
#ifdef Z7_INFORMATION_APP_PROBE
    const struct z7_module_information_api *information_api = (const struct z7_module_information_api *)api;
    if (api->size < sizeof(*information_api) || !information_api->register_information_cycle ||
        !information_api->register_before_information_update) return 1;
#endif
#ifdef Z7_SETTINGS_MENU_PROBE
    if (!sm_prepare()) return 1;
#endif
    if (battery_initialize(&staging) || grid_initialize(&staging) ||
        pending_grid != &grid_hooks || pending_battery != &battery_hooks || pending_menu != &menu) return 1;
    if (!api->register_display(&combined_hooks) || !api->register_grid_menu(pending_menu)) return 1;
#ifdef Z7_SETTINGS_READOUT_PROBE
    if (!update_api->register_before_update(readouts_before)) return 1;
#endif
#ifdef Z7_SETTINGS_DISP_PROBE
    if (!disp_api->register_disp_cycle(preset_cycle)) return 1;
#endif
#ifdef Z7_INFORMATION_APP_PROBE
    if (!information_api->register_information_cycle(information_native_cycle) ||
        !information_api->register_before_information_update(information_before_update)) return 1;
#endif
#ifdef Z7_HISTOGRAM_EXTRA_PROBE
#ifdef Z7_FOCAL_OVERLAY_PROBE
    if (!gui_api->register_after_gui_update(focal_combined_after_gui)) return 1;
#else
    if (!gui_api->register_after_gui_update(histogram_after_gui)) return 1;
#endif
#endif
#ifdef Z7_SETTINGS_PERSISTENCE
#ifdef Z7_HIGHLIGHT_CONTEXT_PROBE
    if (!highlight_api->register_highlight(&highlight_hooks) ||
        !worker_api->register_worker(highlight_combined_worker)) return 1;
#ifdef Z7_HIGHLIGHT_PARAMETERS_PROBE
    if (!parameter_api->register_parameters(highlight_native_parameters)) return 1;
#endif
#ifdef Z7_HIGHLIGHT_FRAME_PROBE
    if (!frame_api->register_frame_permission(highlight_frame_permission)) return 1;
#endif
#else
    if (!worker_api->register_worker(persistence_worker)) return 1;
#endif
    persistence_prepare();
#endif
    /* No failing operation follows these native scalar stores. Host readiness
     * and native menu pointer publication still follow successful return.
     */
#ifndef Z7_HISTOGRAM_EXTRA_PROBE
    Z7_GRID_COMMIT_MASKS();
#endif
#ifdef Z7_SETTINGS_MENU_PROBE
    sm_publish();
#endif
#ifdef Z7_DISP_KEY_PROBE
    __asm__ volatile("dmb sy" ::: "memory");
    W(0xa1829b0cu) = (uint32_t)(uintptr_t)clean_key;
#endif
    return 0;
}
