/* SPDX-License-Identifier: MIT
 * Independent original-Z7 incremental SD checkpoint. Reuses the battery
 * component with its existing MIT notices. Only the stock On grid becomes
 * thirds on the photo LCD; no menu, scalar, dispatcher or settings publication.
 */
#define z7_main checkpoint_battery_initialize
#define hooks checkpoint_battery_hooks
#include "battery_percent.c"
#undef hooks
#undef z7_main

static uint16_t checkpoint_thirds[48];
static const struct z7_display_hooks *checkpoint_staged_battery;

static uint32_t checkpoint_stage_display(const struct z7_display_hooks *candidate)
{
    if (candidate != &checkpoint_battery_hooks || checkpoint_staged_battery) return 0;
    checkpoint_staged_battery = candidate;
    return 1;
}
static const struct z7_module_api checkpoint_staging = {
    Z7_MODULE_ABI, sizeof(checkpoint_staging), Z7_MODULE_TARGET,
    checkpoint_stage_display, 0
};
static const uint16_t *checkpoint_grid_source(const uint16_t *native)
{
    if ((uintptr_t)native != 0x1064fd90u || W(0xa24f182cu) != 1 ||
        B(0xa18237c6u) || B(0xa201d510u)) return native;
    return checkpoint_thirds;
}
static const struct z7_display_hooks checkpoint_hooks = {
    Z7_DISPLAY_ABI, sizeof(checkpoint_hooks), checkpoint_grid_source,
    0, 0, 0, before, after
};
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi != Z7_MODULE_ABI || api->target != Z7_MODULE_TARGET ||
        api->size < 16 || !api->register_display) return 1;
    const uint16_t *native = (const uint16_t *)(uintptr_t)0x1064fd90u;
    for (uint32_t row = 0; row < 3; ++row)
        if (native[row * 16 + 5] != 3 || native[row * 16 + 11] != 3) return 1;
    for (uint32_t i = 0; i < 48; ++i) checkpoint_thirds[i] = native[i];
    for (uint32_t row = 0; row < 3; ++row)
        checkpoint_thirds[row * 16 + 5] = checkpoint_thirds[row * 16 + 11] = 2;
    if (checkpoint_battery_initialize(&checkpoint_staging) ||
        checkpoint_staged_battery != &checkpoint_battery_hooks) return 1;
    return api->register_display(&checkpoint_hooks) ? 0 : 1;
}
