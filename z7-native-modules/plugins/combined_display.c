/* SPDX-License-Identifier: MIT
 * Independent original-Z7 combined display entrypoint. Included components
 * retain their JKWTCN/WonderLanternZ7 MIT notices and native interface scope.
 */
#include "module.h"
#include "display.h"

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
    scalar_value, histogram_gate, before, after
};
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi != Z7_MODULE_ABI || api->target != Z7_MODULE_TARGET ||
        api->size < sizeof(*api) || !api->register_display || !api->register_grid_menu) return 1;
    if (battery_initialize(&staging) || grid_initialize(&staging) ||
        pending_grid != &grid_hooks || pending_battery != &battery_hooks || pending_menu != &menu) return 1;
    if (!api->register_display(&combined_hooks) || !api->register_grid_menu(pending_menu)) return 1;
    /* No failing operation follows these native scalar stores. Host readiness
     * and native menu pointer publication still follow successful return.
     */
    Z7_GRID_COMMIT_MASKS();
    return 0;
}
