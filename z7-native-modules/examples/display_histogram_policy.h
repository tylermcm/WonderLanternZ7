/* SPDX-License-Identifier: MIT
 * Copyright (c)2026 JKWTCN; WonderLanternZ7 contributors.
 * Independent original-Z7 adaptation of the pinned MIT extra-pass design in
 * plugins/histogram_horizon_ram.c. All native interfaces are original-Z7.
 */
#define HG_DESC 0xa1827404u
#define HG_CONTROL 0xa18273d4u
#define HG_STATE 0xa201d308u
#define HG_BINS 0xa201df88u
#define HG_DEFAULT 0x10433913u
#define HG_DRAW 0x102f1545u
enum z7_histogram_result {
    HG_DISABLED, HG_TRANSITION, HG_CONTEXT, HG_PENDING, HG_BINDING,
    HG_BUSY, HG_INELIGIBLE, HG_READINESS, HG_FAILED, HG_EMPTY, HG_OVERFLOW,
    HG_CHANGED, HG_HIDDEN, HG_PAINTER, HG_SUBMIT, HG_DRAWN, HG_RESULTS
};
volatile uint32_t z7_histogram_result, z7_histogram_attempts, z7_histogram_draws;
volatile uint32_t z7_histogram_paints, z7_histogram_presents, z7_histogram_last_end;
volatile uint32_t z7_histogram_context_bits;
volatile uint32_t z7_histogram_outcomes[HG_RESULTS];
static _Alignas(64) uint32_t histogram_samples[256];
static uint32_t histogram_visible;
static uint32_t histogram_owned;
static uint32_t histogram_bindings(void)
{
    return W(0x1064d610u + 31u * 4) == HG_DESC &&
        W(HG_DESC + 44) == HG_CONTROL && B(HG_DESC + 40) == 1 &&
        W(0x1064c67cu + 31u * 4) == 0x102f5541u;
}
static uint32_t histogram_masks(void)
{
    for (uint32_t i = 0; i < 9; ++i)
        if (W(HG_DESC + 4 + i * 4) != (i < 6 ? 0x444u : 0x440u)) return 0;
    return 1;
}
static uint32_t histogram_context(void)
{
    uint32_t bits = (!readout_context()) | ((!z7_base_active) << 1) |
        (!!base_blocked << 2) | (!!base_releasing << 3) |
        ((B(0xa201d4d0u + 0x18a) != z7_base_applied) << 4) |
        ((base_property() != z7_base_applied) << 5) |
        (!!B(0xa201d4d0u + 0x192) << 6) |
        (((W(0xa1829b0cu) != 0x1030da57u) || (W(0xa1829b10u) != 0x1030dd1fu)) << 7) |
        (!!B(0xa201f698u + 0x1f) << 8) |
        ((F(0x103fef81u, uint32_t, void)() != 1) << 9) |
        (((W(0xa1821370u + 0x24) & 7u) != 1) << 14);
    z7_histogram_context_bits = bits;
    return !bits;
}
static uint32_t histogram_pending(void)
{
    return F(0x103fa771u, uint32_t, void)() || W(0xa1821370u + 0x34) ||
        (W(0xa1821370u + 0x30) && F(0x103ecf91u, uint32_t, void)());
}
static uint32_t histogram_before(void)
{
    if (!histogram_owned) return 0;
    if (histogram_context() &&
        (z7_menu_settings.components[z7_readout_preset] & Z7_COMPONENT_HISTOGRAM)) return 0;
    uint32_t object = histogram_owned;
    histogram_owned = 0;
    if (!histogram_bindings() || W(HG_CONTROL + 0x24) != object ||
        !ram(object, 284) || W(object + 0x48) != 0xa201e3b4u ||
        (W(object + 0x4c) != HG_DEFAULT && W(object + 0x4c) != HG_DRAW)) return 0;
    F(0x103fb32fu, uint32_t, uint32_t, uint32_t)(object, 0);
    F(0x103fb303u, void, uint32_t, uint32_t)(object, 1);
    B(HG_CONTROL) = 1; B(HG_CONTROL + 1) = 0;
    return 1; /* The before-update adapter invalidates native layout/redraw. */
}
static void histogram_layout(void)
{
    F(0x10369249u, uint32_t, uint32_t)(31);
    F(0x10369215u, void, uint32_t)(31);
    F(0x102f27a9u, void, uint32_t)(31);
}
static uint32_t histogram_painter(uint32_t object, uint32_t next, uint32_t c, uint32_t d)
{
    ++z7_histogram_paints;
    /* Render callbacks must use RAM-only guards; do not re-enter property or
     * display-wait services while native rendering holds its own locks. */
    if (!histogram_bindings() || W(HG_CONTROL + 0x24) != object ||
        !z7_base_active || base_blocked || base_releasing ||
        !z7_settings_valid(&z7_menu_settings) || !(z7_menu_settings.flags & Z7_SETTINGS_CUSTOM) ||
        (Z7_INFORMATION_CONFIG_BLOCKED) ||
        z7_readout_preset >= 4 || !(z7_menu_settings.components[z7_readout_preset] & Z7_COMPONENT_HISTOGRAM) ||
        !base_gui_memory_context() || B(0xa201d4d0u + 0x18a) != z7_base_applied ||
        (W(0xa1821370u + 0x24) & 7u) != 1) return 1;
    if (W(object + 0x28)) histogram_visible = 1;
    return F(HG_DRAW, uint32_t, uint32_t, uint32_t, uint32_t, uint32_t)(object, next, c, d);
}
/* Avoid a freestanding compiler division dependency. */
static uint32_t histogram_average(uint32_t total, uint32_t count)
{
    uint32_t quotient = 0, remainder = 0;
    for (int bit = 31; bit >= 0; --bit) {
        remainder = (remainder << 1) | ((total >> bit) & 1u);
        if (remainder >= count) { remainder -= count; quotient |= 1u << bit; }
    }
    return quotient;
}
__attribute__((noinline)) static enum z7_histogram_result histogram_update(void)
{
    if (!readout_context() || !z7_base_active ||
        !(z7_menu_settings.components[z7_readout_preset] & Z7_COMPONENT_HISTOGRAM)) return HG_DISABLED;
    uint32_t page = B(0xa201d4d0u + 0x18a);
    if ((page != 0 && page != 3) || B(0xa201d80cu + 0x18a) != page) return HG_TRANSITION;
    if (!histogram_context()) return HG_CONTEXT;
    if (F(0x10301e13u, uint32_t, void)()) { z7_histogram_context_bits |= 1u << 10; return HG_CONTEXT; }
    if (!F(0x102f2b85u, uint32_t, void)()) { z7_histogram_context_bits |= 1u << 11; return HG_CONTEXT; }
    if (F(0x10401d23u, uint32_t, void)() == 1) { z7_histogram_context_bits |= 1u << 12; return HG_CONTEXT; }
    if (F(0x103ea09fu, uint32_t, uint32_t)(12)) { z7_histogram_context_bits |= 1u << 13; return HG_CONTEXT; }
    if (histogram_pending()) return HG_PENDING;
    if (!histogram_bindings() || !histogram_masks()) return HG_BINDING;
    uint32_t object = W(HG_CONTROL + 0x24);
    if (!ram(object, 284) || W(object + 0x48) != 0xa201e3b4u) return HG_BINDING;
    if (B(HG_CONTROL) || B(HG_CONTROL + 1)) return HG_BUSY;
    if (W(object + 0x4c) != HG_DEFAULT && W(object + 0x4c) != HG_DRAW) return HG_PAINTER;
    /* Preserve the native photo eligibility tests without substituting page2
     * into the native snapshot just to call the page-gated eligibility helper. */
    if (F(0x104065a5u, uint32_t, uint32_t)(0x102c) != 1 ||
        F(0x103709abu, uint32_t, void)() || F(0x103ebb43u, uint32_t, void)()) return HG_INELIGIBLE;
    _Alignas(4) uint8_t readiness[0x420];
    F(0x10437191u, void, void *)(readiness);
    if (readiness[0x28] || readiness[0x29]) return HG_READINESS;
    /* A lower-level nominal success can leave the destination untouched.
     * Never reuse the last successful bins after an empty/failed producer. */
    for (uint32_t i = 0; i < 256; ++i) histogram_samples[i] = 0;
    ++z7_histogram_attempts;
    if (!F(0x104070adu, uint32_t, uint32_t *)(histogram_samples)) return HG_FAILED;
    uint32_t peak = 0, total = 0, count = 0;
    for (uint32_t i = 0; i < 256; ++i) {
        uint32_t bin = histogram_samples[i];
        if (bin > peak) peak = bin;
        if (bin) {
            if (bin > 0xffffffffu - total) return HG_OVERFLOW;
            total += bin; ++count;
        }
    }
    if (!count) return HG_EMPTY;
    if (!histogram_context() || B(0xa201d4d0u + 0x18a) != page ||
        !histogram_bindings() || W(HG_CONTROL + 0x24) != object ||
        !histogram_masks() || histogram_pending()) return HG_CHANGED;
    uint32_t mean = histogram_average(total, count);
    uint32_t scale = mean > 0x3fffffffu ? peak : mean << 2;
    if (scale > peak) scale = peak;
    for (uint32_t i = 0; i < 256; ++i) W(HG_BINS + i * 4) = histogram_samples[i];
    W(HG_STATE + 0x34) = scale; B(HG_STATE + 0x10) = 1;
    B(HG_CONTROL) = B(HG_CONTROL + 1) = 1;
    /* Only the two photo LCD banks change, and only during placement. */
    W(HG_DESC + 4) = W(HG_DESC + 16) = 0x444u | (0x101u << page);
    histogram_layout();
    W(HG_DESC + 4) = W(HG_DESC + 16) = 0x444u;
    enum z7_histogram_result result = HG_HIDDEN;
    if (!histogram_bindings() || W(HG_CONTROL + 0x24) != object) return HG_CHANGED;
    uint32_t painter = W(object + 0x4c);
    if (B(HG_CONTROL + 1) == 1 && (painter == HG_DEFAULT || painter == HG_DRAW)) {
        F(0x102f2adbu, void, uint32_t)(31);
        if (W(object + 0x4c) == HG_DRAW && histogram_context() && !histogram_pending()) {
            histogram_visible = 0;
            F(0x104bcb3du, uint32_t, uint32_t, uint32_t)(object, (uint32_t)(uintptr_t)histogram_painter);
            uint32_t drawn = F(0x102f2043u, uint32_t, void)();
            /* Native submit consumes dirty callbacks synchronously. Never
             * retain an optional module painter in a native object afterward. */
            if (W(object + 0x4c) == (uint32_t)(uintptr_t)histogram_painter)
                F(0x104bcb3du, uint32_t, uint32_t, uint32_t)(object, HG_DEFAULT);
            else return HG_CHANGED;
            if (!histogram_bindings() || W(HG_CONTROL + 0x24) != object) return HG_CHANGED;
            if (drawn && histogram_visible && histogram_context() &&
                B(0xa201d4d0u + 0x18a) == page && !histogram_pending()) {
                F(0x102f11b7u, void, void)();
                histogram_owned = object;
                ++z7_histogram_presents; ++z7_histogram_draws;
                return HG_DRAWN;
            }
            F(0x103fb303u, void, uint32_t, uint32_t)(object, 1);
            result = HG_SUBMIT;
        } else result = HG_PAINTER;
    }
    B(HG_STATE + 0x10) = 0;
    B(HG_CONTROL) = 1; B(HG_CONTROL + 1) = 0;
    /* Do not run the new output's placement code against our old LCD object
     * after an output transition. Native hide/dirty is output-independent. */
    if (!B(0xa18237c6u) && !B(0xa201d4d0u + 0x40) &&
        (W(0xa1821370u + 0x24) & 7u) == 1) histogram_layout();
    if (histogram_bindings() && W(HG_CONTROL + 0x24) == object) {
        F(0x103fb32fu, uint32_t, uint32_t, uint32_t)(object, 0);
        F(0x103fb303u, void, uint32_t, uint32_t)(object, 1);
    }
    return result;
}
static void histogram_after_gui(void)
{
    uint32_t now = F(0x103ffa2du, uint32_t, void)();
    if (!now || (z7_histogram_last_end && now - z7_histogram_last_end < 100)) return;
    enum z7_histogram_result result = histogram_update();
    z7_histogram_result = result; ++z7_histogram_outcomes[result];
    /* Throttle from completion even when the native getter waits/fails. */
    z7_histogram_last_end = F(0x103ffa2du, uint32_t, void)();
}
