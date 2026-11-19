/* SPDX-License-Identifier: MIT; module-hook ownership/publication diagnostic. */
#include "module.h"
#include "display.h"

volatile uint32_t z7_display_probe_mask;
volatile uint32_t z7_display_probe_calls;
static const struct z7_module_api *saved_api;
static struct z7_display_hooks bad;
static uint16_t invalid_grid[48];

static void after_paint(void) { ++z7_display_probe_calls; }
static const uint16_t *grid_source(const uint16_t *native)
{
    (void)native;
    return invalid_grid; /* Owned storage with invalid zero counts: fallback. */
}
static const struct z7_display_hooks hooks = {
    Z7_DISPLAY_ABI, sizeof(hooks), grid_source, 0, 0, 0, 0, after_paint
};
uint32_t z7_display_probe_late_register(void)
{
    return saved_api->register_display(&hooks);
}
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi != Z7_MODULE_ABI || api->target != Z7_MODULE_TARGET ||
        api->size < sizeof(*api) || !api->register_display) return 1;
    saved_api = api;
    uint32_t stack_words[8];
    for (uint32_t i = 0; i < 8; ++i) ((volatile uint32_t *)stack_words)[i] = 0;
    stack_words[0] = Z7_DISPLAY_ABI;
    stack_words[1] = sizeof(hooks);
    if (!api->register_display((const struct z7_display_hooks *)stack_words)) z7_display_probe_mask |= 1;
    bad.abi = 2;
    bad.size = sizeof(bad);
    if (!api->register_display(&bad)) z7_display_probe_mask |= 2;
    bad.abi = Z7_DISPLAY_ABI;
    bad.size = 0;
    if (!api->register_display(&bad)) z7_display_probe_mask |= 4;
    bad.size = sizeof(bad);
    bad.after_paint = (void (*)(void))(uintptr_t)0x100202b5u;
    if (!api->register_display(&bad)) z7_display_probe_mask |= 8;
    bad.after_paint = (void (*)(void))((uintptr_t)after_paint & ~(uintptr_t)1);
    if (!api->register_display(&bad)) z7_display_probe_mask |= 16;
    bad.after_paint = (void (*)(void))((uintptr_t)&z7_display_probe_calls | 1u);
    if (!api->register_display(&bad)) z7_display_probe_mask |= 32;
    if (api->register_display(&hooks)) z7_display_probe_mask |= 64;
    if (!api->register_display(&hooks)) z7_display_probe_mask |= 128;
#ifdef Z7_DISPLAY_PROBE_FAIL
    return 1;
#else
    return z7_display_probe_mask == 255 ? 0 : 1;
#endif
}
