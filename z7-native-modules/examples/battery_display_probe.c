/* SPDX-License-Identifier: MIT
 * Original-Z7 GUI-lifetime diagnostic. The transparent rectangle preparation
 * follows JKWTCN's MIT battery painter, adapted to independently mapped Z7 APIs.
 * Copyright (c) 2026 JKWTCN; WonderLanternZ7 contributors.
 * Default supplied text is 63%; the explicit native-sample variant reads the
 * original getter. Neither establishes hardware telemetry. No persistent settings.
 */
#include "module.h"
#include "display.h"
#include <stdint.h>
#ifdef Z7_BATTERY_USE_NATIVE_SAMPLE
#include "../plugins/battery_sample.h"
volatile uint32_t z7_battery_trial_sample_valid;
volatile uint32_t z7_battery_trial_percent = 0xffffffffu;
#endif
#define W(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define F(a,r,...) ((r (*)(__VA_ARGS__))(uintptr_t)(a))
volatile uint32_t z7_battery_trial_phase, z7_battery_trial_object;
volatile uint32_t z7_battery_trial_paints, z7_battery_trial_error;
static uint32_t owner_pool;
static uint32_t ram(uint32_t p, uint32_t n)
{
    return !(p & 3) && p >= 0xa1800000u && n < 0x100000u && p <= 0xc0000000u - n;
}
static uint32_t pool(void)
{
    uint32_t context = W(0xa18237d0u);
    if (context != 0xa201e388u) return 0;
    uint32_t p = W(context + 0x24);
    if (!ram(p, 16) || *(volatile uint16_t *)(uintptr_t)p != 1340 ||
        *(volatile uint16_t *)(uintptr_t)(p + 4) != 1200 || !ram(W(p + 8), 1340 * 4)) return 0;
    return p;
}
static uint32_t owned(void)
{
    uint32_t p = pool(), object = z7_battery_trial_object;
    return p && p == owner_pool && ram(object, 284) && W(W(p + 8) + 1199 * 4) == object && W(object) == 0x7a40;
}
static uint32_t painter(uint32_t object, uint32_t next, uint32_t c, uint32_t d)
{
    if (!owned() || object != z7_battery_trial_object) { z7_battery_trial_error = 3; return 0; }
    ++z7_battery_trial_paints;
    uint32_t rectangle[24];
    for (uint32_t i = 0; i < 24; ++i) rectangle[i] = W(object + i * 4);
    rectangle[1] = rectangle[3] = 6;
    rectangle[2] = 0;
    /* The native outlined glyph extends beyond the requested text layout box.
     * Reserve and retire the entire diagnostic area, including that padding.
     */
    rectangle[4] = 2 | (392u << 16);
    rectangle[5] = 78 | (436u << 16);
    rectangle[13] = 2; /* Verified native direct RGBA color descriptor. */
    rectangle[14] = 0;
    rectangle[17] = 1;
    F(0x10433913u, uint32_t, uint32_t *, uint32_t, uint32_t, uint32_t)(rectangle, next, c, d);
    if (z7_battery_trial_phase == 2) {
        W(object + 0x28) = W(object + 0x44) = 0;
        z7_battery_trial_phase = 3;
        return 1;
    }
    return F(0x10384969u, uint32_t, uint32_t, uint32_t, uint32_t, uint32_t)(object, next, c, d);
}
static void before(void)
{
    if (owned() && z7_battery_trial_phase == 2) {
        W(z7_battery_trial_object + 0x44) = 1;
        W(0xa201e3b4u + 0x44) = 1;
    }
}
static void after(void)
{
    if (z7_battery_trial_phase != 1 || z7_battery_trial_object || z7_battery_trial_error) return;
    uint32_t p = pool();
    if (!p) return;
    const char *text = "63%";
#ifdef Z7_BATTERY_USE_NATIVE_SAMPLE
    uint32_t percent;
    if (!battery_direct_sample(&percent)) { z7_battery_trial_error = 4; return; }
    z7_battery_trial_sample_valid = 1;
    z7_battery_trial_percent = percent;
    char label[8];
    uint32_t n = 0;
    if (percent == 100) label[n++] = '1';
    if (percent >= 10) label[n++] = (char)('0' + (percent / 10) % 10);
    label[n++] = (char)('0' + percent % 10);
    label[n++] = '%'; label[n] = 0;
    text = label;
#endif
    if (W(W(p + 8) + 1199 * 4) || W(0xa2019e78u + 299 * 12) || !W(0xa2019e78u + 299 * 12 + 4)) {
        z7_battery_trial_error = 1; return;
    }
    const volatile uint32_t *availability = (const volatile uint32_t *)(uintptr_t)W(0xa181c77cu);
    if (!ram((uint32_t)(uintptr_t)availability, 1200 * 4)) { z7_battery_trial_error = 2; return; }
    uint32_t free = 0;
    for (uint32_t i = 0; i < 1200; ++i) if (!availability[i]) { free = 1; break; }
    if (!free) { z7_battery_trial_error = 2; return; }
    uint32_t object = F(0x103fcf0fu, uint32_t, uint32_t, uint32_t, uint32_t)(p, 0, 1199);
    if (!ram(object, 284)) { z7_battery_trial_error = 2; return; }
    owner_pool = p; z7_battery_trial_object = object;
    W(object) = 0x7a40; W(object + 4) = 2; W(object + 8) = 299; W(object + 12) = 2;
    W(object + 0x10) = 10 | (400u << 16); W(object + 0x14) = 70 | (424u << 16);
    W(object + 0x18) = 0; W(object + 0x28) = 0; W(object + 0x2c) = 1;
    W(object + 0x34) = W(object + 0x3c) = 0x1000;
    W(object + 0x38) = 1; W(object + 0x40) = 0x2ed; W(object + 0x48) = 0xa201e3b4u;
    W(object + 0x98) = W(object + 0x10); W(object + 0x9c) = W(object + 0x14);
    F(0x103fbb5du, void, const char *, uint32_t, uint32_t)(text, 299, 0);
    F(0x10384d83u, void, uint32_t)(object);
    F(0x10384e03u, uint32_t, uint32_t, uint32_t)(object, 1);
    W(object + 0x4c) = (uint32_t)(uintptr_t)painter;
    F(0x103faebbu, uint32_t, uint32_t, uint32_t)(0xa201e3b4u, object);
    F(0x103fb32fu, uint32_t, uint32_t, uint32_t)(object, 1);
    W(object + 0x44) = W(0xa201e3b4u + 0x44) = 1;
}
static const struct z7_display_hooks hooks = {Z7_DISPLAY_ABI, sizeof(hooks), 0, 0, 0, 0, before, after};
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi != Z7_MODULE_ABI || api->size < 16 || api->target != Z7_MODULE_TARGET ||
        !api->register_display || W(0x1064d610u + 18 * 4) != 0xa1824bf4u ||
        *(volatile uint16_t *)(uintptr_t)0xa181c770u != 1200 ||
        *(volatile uint16_t *)(uintptr_t)0xa181c774u != 284) return 1;
    return api->register_display(&hooks) ? 0 : 1;
}
