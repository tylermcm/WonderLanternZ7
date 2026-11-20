/* SPDX-License-Identifier: MIT
 * Original-Z7 C 3.80 battery overlay. Transparent native rectangle preparation
 * adapts JKWTCN's MIT battery painter; native contracts were derived separately.
 * Copyright (c) 2026 JKWTCN; WonderLanternZ7 contributors.
 */
#include "module.h"
#include "display.h"
#include "battery_sample.h"
#include <stdint.h>
#define W(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define B(a) (*(volatile uint8_t *)(uintptr_t)(a))
#define F(a,r,...) ((r (*)(__VA_ARGS__))(uintptr_t)(a))
#ifndef Z7_BATTERY_DEFAULT_ENABLED
#define Z7_BATTERY_DEFAULT_ENABLED 1
#endif
volatile uint32_t z7_battery_enabled = Z7_BATTERY_DEFAULT_ENABLED;
volatile uint32_t z7_battery_object, z7_battery_percent = 0xffffffffu;
volatile uint32_t z7_battery_samples, z7_battery_paints, z7_battery_status;
static uint32_t owner_pool, label_buffer, label_font, sampled, attempted, remaining, visible, retire;
static char owned_text[8];
static uint32_t ram(uint32_t p, uint32_t n)
{
    return !(p & 3) && p >= 0xa1800000u && n <= 0x100000u && p <= 0xc0000000u - n;
}
static uint32_t pool(void)
{
    if (W(0xa18237d0u) != 0xa201e388u) return 0;
    uint32_t p = W(0xa201e3acu);
    if (!ram(p, 16) || *(volatile uint16_t *)(uintptr_t)p != 1340 ||
        *(volatile uint16_t *)(uintptr_t)(p + 4) != 1200 || !ram(W(p + 8), 5360)) return 0;
    return p;
}
static uint32_t owned(void)
{
    uint32_t p = pool(), o = z7_battery_object;
    return p && p == owner_pool && ram(o, 284) && W(W(p + 8) + 1199 * 4) == o &&
        W(o) == 0x7a40 && W(o + 0x48) == 0xa201e3b4u;
}
static uint32_t label_owned(void)
{
    uint32_t p = W(0xa2019e78u + 299 * 12 + 4);
    if (!label_buffer) return !W(0xa2019e78u + 299 * 12) && ram(p & ~3u, 56);
    if (p != label_buffer) return 0;
    for (uint32_t i = 0; i < sizeof(owned_text); ++i) {
        uint8_t c = *(volatile uint8_t *)(uintptr_t)(p + i);
        if (c != (uint8_t)owned_text[i]) return 0;
        if (!c) return W(0xa2019e78u + 299 * 12) == i && W(0xa2019e78u + 299 * 12 + 8) == label_font;
    }
    return 0;
}
static uint32_t native_icon_base(uint32_t control, uint32_t object)
{
    if (B(control + 1) != 1 || !ram(object, 96) || !W(object + 0x28) ||
        W(object + 0x48) != 0xa201e3b4u || W(object + 0x10) != (2 | (396u << 16)) ||
        W(object + 0x14) != (62 | (428u << 16))) return 0;
    uint32_t paint = W(object + 0x4c);
    return paint == 0x10384969u || paint == 0x10433913u;
}
static uint32_t native_icon(uint32_t control, uint32_t object)
{
    /* Original table 1064D182/18E maps battery bars to 1120..1129.
     * The 112A/B pair is a plug/adapter glyph, observed in the emulator.
     */
    return native_icon_base(control, object) && W(object + 0x4c) == 0x10384969u &&
        *(volatile uint16_t *)(uintptr_t)(object + 4) == 4 && !W(object + 12) &&
        W(object + 8) >= 0x1120u && W(object + 8) <= 0x1128u && !(W(object + 8) & 1);
}
static uint32_t context_visible(void)
{
    /* LCD photo only. Existing native control visibility keeps warning and
     * page/output exclusions with the stock battery updater.
     */
#ifdef Z7_INFORMATION_APP_PROBE
    if (information_components_blocked()) return 0;
#endif
    if (z7_battery_enabled != 1 || B(0xa18237c6u) || B(0xa201d4d0u + 0x40) ||
        W(0xa18b4de8u) || !pool()) return 0;
    uint32_t font = B(0xa18237e8u + 19 * 2);
    if (font > 110 || !B(0xa182158cu + font * 16 + 1) || B(0xa182158cu + font * 16 + 1) > 24) return 0;
    uint32_t pages = W(0xa181f91cu);
    if (pages && (!ram(pages, 16) || W(pages + 8))) return 0;
    for (uint32_t i = 0; i < 10; ++i) {
        uint32_t control = 0xa1824a14u + i * 48;
        uint32_t object = W(control + 36);
        if (native_icon(control, object)) return 1;
    }
    return 0;
}
static void rectangle(uint32_t object, uint32_t next, uint32_t c, uint32_t d,
                      uint32_t first, uint32_t last, uint32_t color)
{
    uint32_t shape[24];
    for (uint32_t i = 0; i < 24; ++i) shape[i] = W(object + 4 * i);
    shape[1] = shape[3] = 6; shape[2] = 0;
    shape[4] = first; shape[5] = last; shape[13] = 2; shape[14] = color; shape[17] = 1;
    if (color == 0xffffffffu) for (uint32_t i = 0; i < 10; ++i) {
        uint32_t control = 0xa1824a14u + i * 48, icon = W(control + 36);
        if (native_icon(control, icon)) { shape[13] = W(icon + 0x34); shape[14] = W(icon + 0x38); break; }
    }
    F(0x10433913u, uint32_t, uint32_t *, uint32_t, uint32_t, uint32_t)(shape, next, c, d);
}
static void restore_icons(uint32_t next, uint32_t c, uint32_t d)
{
    for (uint32_t i = 0; i < 10; ++i) {
        uint32_t control = 0xa1824a14u + i * 48, o = W(control + 36);
        if (!native_icon_base(control, o)) continue;
        uint32_t paint = W(o + 0x4c), dirty = W(o + 0x44);
        if (paint != 0x10384969u && paint != 0x10433913u) continue;
        W(o + 0x44) = 1;
        ((uint32_t (*)(uint32_t, uint32_t, uint32_t, uint32_t))(uintptr_t)paint)(o, next, c, d);
        W(o + 0x44) = dirty;
    }
}
static uint32_t painter(uint32_t object, uint32_t next, uint32_t c, uint32_t d)
{
    if (!owned() || object != z7_battery_object) return 0;
    ++z7_battery_paints;
    if (!context_visible() || !label_owned()) { visible = 0; retire = 1; }
    rectangle(object, next, c, d, 2 | (392u << 16), 78 | (436u << 16), 0);
    if (retire || !visible) {
        W(object + 0x28) = W(object + 0x44) = 0;
        restore_icons(next, c, d);
        retire = 0;
        return 1;
    }
    /* Match the independently observed native battery silhouette. */
    rectangle(object, next, c, d, 8 | (398u << 16), 60 | (426u << 16), 0xffffffffu);
    rectangle(object, next, c, d, 10 | (400u << 16), 58 | (424u << 16), 0);
    rectangle(object, next, c, d, 3 | (405u << 16), 8 | (419u << 16), 0xffffffffu);
    rectangle(object, next, c, d, 5 | (407u << 16), 8 | (417u << 16), 0);
    for (uint32_t i = 0; i < 10; ++i) {
        uint32_t control = 0xa1824a14u + i * 48, icon = W(control + 36);
        if (native_icon(control, icon)) {
            W(object + 0x34) = W(icon + 0x34); W(object + 0x38) = W(icon + 0x38); break;
        }
    }
    return F(0x10384969u, uint32_t, uint32_t, uint32_t, uint32_t, uint32_t)(object, next, c, d);
}
static void before(void)
{
    if (z7_battery_object && !owned()) {
        z7_battery_object = 0; owner_pool = 0; sampled = attempted = remaining = visible = retire = 0;
        uint32_t buffer = W(0xa2019e78u + 299 * 12 + 4);
        if (!W(0xa2019e78u + 299 * 12) && ram(buffer & ~3u, 56) && !B(buffer)) {
            label_buffer = 0; owned_text[0] = 0;
        }
    }
    uint32_t desired = context_visible() && label_owned();
    if (!desired) { sampled = attempted = remaining = 0; }
    else if (!attempted || !remaining) {
        uint32_t percent;
        ++z7_battery_samples;
        sampled = battery_direct_sample(&percent);
        attempted = 1;
        if (sampled) z7_battery_percent = percent;
        remaining = 15;
    } else --remaining;
    desired = desired && sampled;
    if (owned()) {
        if (!desired && visible) {
            retire = 1;
            F(0x103fb32fu, uint32_t, uint32_t, uint32_t)(z7_battery_object, 0);
        }
        if (retire || desired) {
            W(z7_battery_object + 0x44) = 1;
            W(0xa201e3b4u + 0x44) = 1;
        }
    }
    visible = desired;
}
static uint32_t create_ready(uint32_t p)
{
    if (!p) return 0;
    if (W(W(p + 8) + 1199 * 4)) return 0;
    uint32_t flags = W(0xa181c77cu), free = 0;
    if (!ram(flags, 4800)) return 0;
    for (uint32_t i = 0; i < 1200; ++i) if (!W(flags + i * 4)) { free = 1; break; }
    return free;
}
static uint32_t create(uint32_t p)
{
    if (!create_ready(p)) return 0;
    uint32_t o = F(0x103fcf0fu, uint32_t, uint32_t, uint32_t, uint32_t)(p, 0, 1199);
    if (!ram(o, 284)) return 0;
    owner_pool = p; z7_battery_object = o;
    W(o) = 0x7a40; W(o + 4) = 2; W(o + 8) = 299; W(o + 12) = 2;
    W(o + 0x10) = 10 | (400u << 16); W(o + 0x14) = 70 | (424u << 16);
    W(o + 0x18) = W(o + 0x28) = 0; W(o + 0x2c) = 1;
    W(o + 0x34) = W(o + 0x3c) = 0x1000; W(o + 0x38) = 1;
    W(o + 0x40) = 0x2ed; W(o + 0x48) = 0xa201e3b4u;
    W(o + 0x98) = W(o + 0x10); W(o + 0x9c) = W(o + 0x14);
    F(0x10384d83u, void, uint32_t)(o);
    F(0x10384e03u, uint32_t, uint32_t, uint32_t)(o, 1);
    W(o + 0x4c) = (uint32_t)(uintptr_t)painter;
    F(0x103faebbu, uint32_t, uint32_t, uint32_t)(0xa201e3b4u, o);
    return o;
}
static void after(void)
{
    if (!visible || !context_visible() || !label_owned()) return;
    if (!owned() && !create_ready(pool())) { z7_battery_status = 1; return; }
    uint32_t n = 0, value = z7_battery_percent;
    char text[8];
    if (value == 100) text[n++] = '1';
    if (value >= 10) text[n++] = (char)('0' + value / 10 % 10);
    text[n++] = (char)('0' + value % 10); text[n++] = '%'; text[n] = 0;
    uint32_t font = B(0xa18237e8u + 19 * 2);
    uint32_t changed = !label_buffer || label_font != font;
    for (uint32_t i = 0; i <= n; ++i) if (owned_text[i] != text[i]) changed = 1;
    if (changed) {
        F(0x103fbb5du, void, const char *, uint32_t, uint32_t)(text, 299, font);
        label_buffer = W(0xa2019e78u + 299 * 12 + 4);
        label_font = font;
        for (uint32_t i = 0; i <= n; ++i) owned_text[i] = text[i];
    }
    uint32_t o = owned() ? z7_battery_object : create(pool());
    if (!o) { z7_battery_status = 1; return; }
    if (changed) F(0x103fb345u, void, uint32_t, uint32_t)(o, 299);
    F(0x103fb32fu, uint32_t, uint32_t, uint32_t)(o, 1);
    W(o + 0x44) = W(0xa201e3b4u + 0x44) = 1;
}
static const struct z7_display_hooks hooks = {Z7_DISPLAY_ABI, sizeof(hooks), 0, 0, 0, 0, before, after};
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi != Z7_MODULE_ABI || api->target != Z7_MODULE_TARGET || api->size < 16 ||
        !api->register_display || W(0x1064d610u + 18 * 4) != 0xa1824bf4u ||
        *(volatile uint16_t *)(uintptr_t)0xa181c770u != 1200 ||
        *(volatile uint16_t *)(uintptr_t)0xa181c774u != 284) return 1;
    return api->register_display(&hooks) ? 0 : 1;
}
