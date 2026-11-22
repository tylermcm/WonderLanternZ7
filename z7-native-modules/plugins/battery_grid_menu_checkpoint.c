/* SPDX-License-Identifier: MIT
 * Independent incremental original-Z7 checkpoint. Included battery/grid
 * components retain their licenses/notices. Native grid page only; no custom
 * settings page, dispatcher, histogram masks, storage or worker.
 */
#define z7_main checkpoint_battery_initialize
#define hooks checkpoint_battery_hooks
#include "battery_percent.c"
#undef hooks
#undef z7_main
#define Z7_GRID_DEFER_MASKS 1
#define Z7_GRID_VOLATILE_CHECKPOINT 1
#define z7_main checkpoint_grid_initialize
#define hooks checkpoint_grid_hooks
#include "grids_histogram.c"
#undef hooks
#undef z7_main
#undef Z7_GRID_VOLATILE_CHECKPOINT
#undef Z7_GRID_DEFER_MASKS

static uint32_t checkpoint_battery_staged, checkpoint_grid_staged, checkpoint_menu_staged;
static uint32_t checkpoint_stage_display(const struct z7_display_hooks *candidate)
{
    if (candidate == &checkpoint_battery_hooks && !checkpoint_battery_staged) {
        checkpoint_battery_staged = 1; return 1;
    }
    if (candidate == &checkpoint_grid_hooks && !checkpoint_grid_staged) {
        checkpoint_grid_staged = 1; return 1;
    }
    return 0;
}
static uint32_t checkpoint_stage_menu(const struct z7_grid_menu *candidate)
{
    if (candidate != &menu || checkpoint_menu_staged) return 0;
    checkpoint_menu_staged = 1; return 1;
}
static const struct z7_module_api checkpoint_staging = {
    Z7_MODULE_ABI, sizeof(checkpoint_staging), Z7_MODULE_TARGET,
    checkpoint_stage_display, checkpoint_stage_menu
};
static const struct z7_display_hooks checkpoint_hooks = {
    Z7_DISPLAY_ABI, sizeof(checkpoint_hooks), grid_source, grid_geometry,
    0, 0, before, after
};
#ifndef Z7_GRID_MENU_CHECKPOINT_ENTRY
#define Z7_GRID_MENU_CHECKPOINT_ENTRY z7_main
#endif
uint32_t Z7_GRID_MENU_CHECKPOINT_ENTRY(const struct z7_module_api *api)
{
    if (!api || api->abi != Z7_MODULE_ABI || api->target != Z7_MODULE_TARGET ||
        api->size < sizeof(*api) || !api->register_display || !api->register_grid_menu) return 1;
    if (checkpoint_battery_initialize(&checkpoint_staging) ||
        checkpoint_grid_initialize(&checkpoint_staging) || !checkpoint_battery_staged ||
        !checkpoint_grid_staged || !checkpoint_menu_staged) return 1;
    return api->register_display(&checkpoint_hooks) && api->register_grid_menu(&menu) ? 0 : 1;
}
