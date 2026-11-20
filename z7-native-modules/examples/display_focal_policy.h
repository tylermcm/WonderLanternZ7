/* SPDX-License-Identifier: MIT. Independent original-Z7 focal text ownership.
 * Initial LCD landscape path; EVF/rotation remain explicit port work. Uses a
 * separate native container object, never the VR widget or its visibility.
 */
#include "../plugins/focal_sample.h"
#define FOCAL_SLOT 1198u
#define FOCAL_LABEL 298u
#define FOCAL_FIRST (110u | (194u << 16))
#define FOCAL_LAST (220u | (218u << 16))
volatile uint32_t z7_focal_object, z7_focal_tenths = 0xffffffffu;
volatile uint32_t z7_focal_samples, z7_focal_paints, z7_focal_presents, z7_focal_status;
static uint32_t focal_pool_owner, focal_label_buffer, focal_label_font;
static uint32_t focal_visible, focal_retire, focal_last_tick, focal_repaint_pending;
static char focal_text[16];
static uint32_t focal_painter(uint32_t object, uint32_t next, uint32_t c, uint32_t d);
static uint32_t focal_owned(void)
{
    uint32_t p = pool(), o = z7_focal_object;
    return p && p == focal_pool_owner && ram(o, 284) && W(W(p + 8) + FOCAL_SLOT * 4) == o &&
        W(o) == 0x7a41 && W(o + 0x48) == 0xa201e3b4u &&
        W(o + 0x4c) == (uint32_t)(uintptr_t)focal_painter;
}
static uint32_t focal_label_owned(void)
{
    uint32_t record = 0xa2019e78u + FOCAL_LABEL * 12;
    uint32_t p = W(record + 4);
    if (!ram(p & ~3u, 56)) return 0;
    if (!focal_label_buffer) return !W(record) && !B(p);
    if (p != focal_label_buffer || W(record + 8) != focal_label_font) return 0;
    for (uint32_t i = 0; i < sizeof(focal_text); ++i) {
        if (B(p + i) != (uint8_t)focal_text[i]) return 0;
        if (!focal_text[i]) return W(record) == i;
    }
    return 0;
}
static uint32_t focal_memory_context(void)
{
    if (!base_gui_memory_context() || !z7_base_active || base_blocked || base_releasing ||
        !z7_settings_valid(&z7_menu_settings) || !(z7_menu_settings.flags & Z7_SETTINGS_CUSTOM) ||
        (z7_menu_settings.enabled_pages & 16u) || z7_readout_preset >= 4 ||
        !(z7_menu_settings.information[z7_readout_preset] & Z7_INFO_FOCAL) ||
        B(0xa201d4d0u) || B(0xa201d4d0u + 0x192) || B(0xa201d4d0u + 0x193) ||
        *(volatile uint16_t *)(uintptr_t)(0xa201d4d0u + 0x338) ||
        B(0xa201d4d0u + 0x18a) != z7_base_applied ||
        (W(0xa1821370u + 0x24) & 7u) != 1 ||
        W(0xa1829b0cu) != 0x1030da57u || W(0xa1829b10u) != 0x1030dd1fu) return 0;
    uint32_t font = B(0xa18237e8u + 19 * 2);
    return font <= 110 && B(0xa182158cu + font * 16 + 1) &&
        B(0xa182158cu + font * 16 + 1) <= 24;
}
static uint32_t focal_before_update(void)
{
    if (z7_focal_object && !focal_owned()) {
        z7_focal_object = focal_pool_owner = focal_visible = focal_retire = focal_last_tick = 0;
        uint32_t record = 0xa2019e78u + FOCAL_LABEL * 12, p = W(record + 4);
        if (!W(record) && ram(p & ~3u, 56) && !B(p)) {
            focal_label_buffer = 0; focal_text[0] = 0;
        }
    }
    if (focal_memory_context() && focal_label_owned()) return 0;
    focal_last_tick = 0;
    if (!focal_owned() || !focal_visible) return 0;
    focal_visible = 0; focal_retire = 1;
    F(0x103fb32fu, uint32_t, uint32_t, uint32_t)(z7_focal_object, 0);
    F(0x103fb303u, void, uint32_t, uint32_t)(z7_focal_object, 1);
    W(0xa201e3b4u + 0x44) = 1;
    return 1;
}
static void focal_note_update(uint32_t changed)
{
    if (!focal_memory_context()) return;
    if (changed) { focal_repaint_pending = 1; return; }
    /* Native HUD changes can clear the overlay plane even when our label is
     * unchanged. Treat delta state as an invalidation request, never as proof
     * that native pixels have completed painting. The after-GUI callback still
     * rechecks ownership/context/busy state before its bounded extra pass.
     */
    for (uint32_t offset = 0; offset < 0x33c; offset += 4)
        if (W(0xa201d4d0u + offset) != W(0xa201d80cu + offset)) {
            focal_repaint_pending = 1; return;
        }
}
static uint32_t focal_create_ready(uint32_t p)
{
    if (!p || W(W(p + 8) + FOCAL_SLOT * 4)) return 0;
    uint32_t flags = W(0xa181c77cu);
    if (!ram(flags, 4800)) return 0;
    for (uint32_t i = 0; i < 1200; ++i) if (!W(flags + i * 4)) return 1;
    return 0;
}
static uint32_t focal_create(uint32_t p)
{
    if (!focal_create_ready(p)) return 0;
    uint32_t o = F(0x103fcf0fu, uint32_t, uint32_t, uint32_t, uint32_t)(p, 0, FOCAL_SLOT);
    if (!ram(o, 284)) return 0;
    focal_pool_owner = p; z7_focal_object = o;
    W(o) = 0x7a41; W(o + 4) = W(o + 12) = 2; W(o + 8) = FOCAL_LABEL;
    W(o + 0x10) = FOCAL_FIRST; W(o + 0x14) = FOCAL_LAST;
    W(o + 0x18) = W(o + 0x28) = 0; W(o + 0x2c) = 1;
    W(o + 0x34) = W(o + 0x3c) = 0x1000; W(o + 0x38) = 1;
    W(o + 0x40) = 0x2ed; W(o + 0x48) = 0xa201e3b4u;
    W(o + 0x98) = FOCAL_FIRST; W(o + 0x9c) = FOCAL_LAST;
    F(0x10384d83u, void, uint32_t)(o);
    F(0x10384e03u, uint32_t, uint32_t, uint32_t)(o, 1);
    W(o + 0x4c) = (uint32_t)(uintptr_t)focal_painter;
    F(0x103faebbu, uint32_t, uint32_t, uint32_t)(0xa201e3b4u, o);
    return o;
}
static uint32_t focal_painter(uint32_t object, uint32_t next, uint32_t c, uint32_t d)
{
    if (!focal_owned() || object != z7_focal_object) return 0;
    ++z7_focal_paints;
    /* Never apply old LCD coordinates to a different output/layout. Native
     * scene reconstruction owns clearing that output during the transition.
     */
    if (B(0xa18237c6u) || *(volatile uint16_t *)(uintptr_t)(0xa201d4d0u + 0x338)) {
        W(object + 0x28) = W(object + 0x44) = 0; focal_visible = focal_retire = 0; return 1;
    }
    uint32_t shape[24];
    for (uint32_t i = 0; i < 24; ++i) shape[i] = W(object + i * 4);
    shape[1] = shape[3] = 6; shape[2] = 0;
    shape[4] = FOCAL_FIRST; shape[5] = FOCAL_LAST;
    shape[13] = 2; shape[14] = 0; shape[17] = 1;
    F(0x10433913u, uint32_t, uint32_t *, uint32_t, uint32_t, uint32_t)(shape, next, c, d);
    uint32_t kind = W(0xa24e2600u);
    if (focal_retire || !focal_visible || !focal_memory_context() || !focal_label_owned() ||
        (kind != 1 && kind != 3) || W(0xa24e25a8u) != z7_focal_tenths) {
        W(object + 0x28) = W(object + 0x44) = 0; focal_visible = focal_retire = 0; return 1;
    }
    return F(0x10384969u, uint32_t, uint32_t, uint32_t, uint32_t, uint32_t)(object, next, c, d);
}
static void focal_after_gui(void)
{
    uint32_t changed = focal_before_update();
    if (!focal_memory_context() || base_property() != z7_base_applied ||
        F(0x103fef81u, uint32_t, void)() != 1 || histogram_pending() ||
        !F(0x102f2b85u, uint32_t, void)() || F(0x10301e13u, uint32_t, void)()) return;
    if (!focal_label_owned() || (!focal_owned() && !focal_create_ready(pool()))) { z7_focal_status = 1; return; }
    uint32_t now = F(0x103ffa2du, uint32_t, void)();
    if (!now || (focal_last_tick && now - focal_last_tick < 100)) return;
    focal_last_tick = now;
    uint32_t value = 0xffffffffu;
    ++z7_focal_samples;
    uint32_t valid = focal_direct_sample(&value);
    if (!valid) {
        z7_focal_tenths = 0xffffffffu;
        if (focal_owned() && focal_visible) {
            focal_visible = 0; focal_retire = 1; changed = 1;
            F(0x103fb32fu, uint32_t, uint32_t, uint32_t)(z7_focal_object, 0);
            F(0x103fb303u, void, uint32_t, uint32_t)(z7_focal_object, 1);
        }
    } else {
        char text[16], digits[10]; uint32_t n = 0, count = 0, whole = value / 10;
        do { digits[count++] = (char)('0' + whole % 10); whole /= 10; } while (whole);
        while (count) text[n++] = digits[--count];
        if (value % 10) { text[n++] = '.'; text[n++] = (char)('0' + value % 10); }
        text[n++] = 'm'; text[n++] = 'm'; text[n] = 0;
        uint32_t font = B(0xa18237e8u + 19 * 2), label_changed = !focal_label_buffer || focal_label_font != font;
        for (uint32_t i = 0; i <= n; ++i) if (focal_text[i] != text[i]) label_changed = 1;
        if (label_changed) {
            F(0x103fbb5du, void, const char *, uint32_t, uint32_t)(text, FOCAL_LABEL, font);
            focal_label_buffer = W(0xa2019e78u + FOCAL_LABEL * 12 + 4); focal_label_font = font;
            for (uint32_t i = 0; i <= n; ++i) focal_text[i] = text[i];
            if (!focal_label_owned()) { z7_focal_status = 2; return; }
        }
        uint32_t o = focal_owned() ? z7_focal_object : focal_create(pool());
        if (!o) { z7_focal_status = 3; return; }
        changed |= label_changed || !focal_visible || z7_focal_tenths != value || focal_repaint_pending;
        if (label_changed) F(0x103fb345u, void, uint32_t, uint32_t)(o, FOCAL_LABEL);
        z7_focal_tenths = value; focal_visible = 1; focal_retire = 0;
        if (changed) F(0x103fb32fu, uint32_t, uint32_t, uint32_t)(o, 1);
    }
    if (!changed || !focal_owned()) return;
    focal_repaint_pending = 1;
    if (histogram_pending()) return;
    W(z7_focal_object + 0x44) = W(0xa201e3b4u + 0x44) = 1;
    uint32_t paints = z7_focal_paints;
    if (F(0x102f2043u, uint32_t, void)() && z7_focal_paints != paints &&
        !histogram_pending() && focal_memory_context()) {
        F(0x102f11b7u, void, void)(); ++z7_focal_presents; focal_repaint_pending = 0;
    }
}
