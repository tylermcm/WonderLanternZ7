/* SPDX-License-Identifier: MIT. Independent original-Z7 readout mask adapter.
 * Only independently identified ordinary groups are bound here.
 * No direct control visibility stores or unidentified widget edits.
 */
volatile uint32_t z7_readout_preset, z7_readout_active, z7_readout_conflicts, z7_readout_changes;
#ifdef Z7_INFORMATION_OTHER_PROBE
#include "display_other_bindings.h"
typedef uint64_t readout_ownership;
#elif defined(Z7_INFORMATION_GROUPS_PROBE)
#define READOUT_COUNT 6u
static const uint32_t readout_descriptors[READOUT_COUNT] = {0xa1824174u, 0xa1824264u, 0xa1824654u, 0xa1823cf4u, 0xa18284dcu, 0xa1823a24u};
static const uint8_t readout_widgets[READOUT_COUNT] = {10, 11, 15, 5, 51, 2};
/* 255 denotes an ordinary group without the exposure-format selector. */
static const uint8_t readout_formats[READOUT_COUNT] = {0, 1, 5, 255, 255, 255};
static const uint8_t readout_bits[READOUT_COUNT] = {Z7_INFO_SHUTTER, Z7_INFO_APERTURE, Z7_INFO_ISO, Z7_INFO_SHOOTING, Z7_INFO_RELEASE, Z7_INFO_FOCUS};
static const uint32_t readout_updaters[READOUT_COUNT] = {0x102f378du, 0x102f3951u, 0x102f3b5bu, 0x102f346fu, 0x102f6d01u, 0x102f31a7u};
typedef uint32_t readout_ownership;
#else
#define READOUT_COUNT 3u
static const uint32_t readout_descriptors[3] = {0xa1824174u, 0xa1824264u, 0xa1824654u};
static const uint8_t readout_widgets[3] = {10, 11, 15};
static const uint8_t readout_formats[3] = {0, 1, 5};
static const uint8_t readout_bits[3] = {Z7_INFO_SHUTTER, Z7_INFO_APERTURE, Z7_INFO_ISO};
static const uint32_t readout_updaters[3] = {0x102f378du, 0x102f3951u, 0x102f3b5bu};
typedef uint32_t readout_ownership;
#endif
static uint32_t readout_blocked;
static readout_ownership readout_pending;
static uint32_t readout_saved[READOUT_COUNT][2], readout_applied[READOUT_COUNT][2];
#ifdef Z7_SETTINGS_BASE_PROBE
#include "display_base_policy.h"
#define READOUT_RENDER_CONTEXT() (readout_context() && z7_base_active)
#else
#define READOUT_RENDER_CONTEXT() readout_context()
#endif
static uint32_t readout_bindings(void)
{
    for (uint32_t i = 0; i < READOUT_COUNT; ++i) {
        uint32_t p = readout_descriptors[i];
        if (W(0x1064d610u + readout_widgets[i] * 4) != p || !ram(p, 48) ||
            W(0x1064c67cu + readout_widgets[i] * 4) != readout_updaters[i]) return 0;
    }
    return 1;
}
static uint32_t readout_gui_context(void)
{
#ifdef Z7_SETTINGS_BASE_PROBE
    return base_gui_context();
#else
    if (B(0xa18237c6u) || B(0xa201d4d0u + 0x40) || !pool()) return 0;
    uint32_t page = B(0xa201d4d0u + 0x18a);
    if (page != 0 && page != 3) return 0;
    uint32_t pages = W(0xa181f91cu);
    return ram(pages, 16) && !W(pages + 8);
#endif
}
static uint32_t readout_context(void)
{
#ifdef Z7_SETTINGS_BASE_PROBE
    if (base_blocked || base_releasing) return 0;
#endif
#ifdef Z7_SETTINGS_DISP_PROBE
    /* API32 profiles reject the unbound information choice. The API40
     * profile instead suspends custom components during owned app transitions.
     */
    if (Z7_INFORMATION_CONFIG_BLOCKED) return 0;
#endif
    return z7_settings_valid(&z7_menu_settings) && (z7_menu_settings.flags & Z7_SETTINGS_CUSTOM) &&
        z7_readout_preset < 4 && readout_gui_context();
}
#ifdef Z7_SETTINGS_DISP_PROBE
volatile uint32_t z7_preset_reselections;
static void readout_sync_preset(void)
{
#ifdef Z7_INFORMATION_APP_PROBE
    information_sync_preset();
#else
    /* Menu edits can disable the currently selected logical page. Apply the
     * next enabled page on return to eligible shooting, without counting a
     * button press or changing a native page/property. */
    if (!readout_context() || (z7_menu_settings.enabled_pages & (1u << z7_readout_preset))) return;
    uint32_t next = z7_settings_next(&z7_menu_settings, z7_readout_preset);
    if (next < 4) { z7_readout_preset = next; ++z7_preset_reselections; }
#endif
}
#endif
static uint32_t readout_release(readout_ownership words)
{
    uint32_t changed = 0;
    readout_ownership pending = 0;
    for (uint32_t i = 0; i < READOUT_COUNT; ++i) {
        uint32_t p = readout_descriptors[i];
        for (uint32_t bank = 0; bank < 2; ++bank) {
            readout_ownership bit = (readout_ownership)1u << (i * 2 + bank);
            if (!(words & bit)) continue;
            if (W(0x1064d610u + readout_widgets[i] * 4) != p) {
                if (readout_applied[i][bank] != readout_saved[i][bank]) pending |= bit;
                continue;
            }
            uint32_t address = p + 4 + bank * 12;
            if (W(address) == readout_applied[i][bank] && W(address) != readout_saved[i][bank]) {
                W(address) = readout_saved[i][bank]; changed |= 1u << i;
            }
        }
    }
    readout_pending = pending;
    z7_readout_active = 0;
    return changed;
}
static void readouts_before(void)
{
#ifdef Z7_SETTINGS_DISP_PROBE
    readout_sync_preset();
#endif
    uint32_t changed = 0, conflict = 0;
#ifdef Z7_HISTOGRAM_EXTRA_PROBE
    changed = histogram_before();
#endif
#ifdef Z7_SETTINGS_BASE_PROBE
    changed |= base_before();
#endif
    if (readout_pending) changed |= readout_release(readout_pending);
    uint32_t master = !!(z7_menu_settings.flags & Z7_SETTINGS_CUSTOM);
    if (!master) readout_blocked = 0;
    if (z7_readout_active) {
        conflict = !readout_bindings();
        for (uint32_t i = 0; i < READOUT_COUNT; ++i) if (W(0x1064d610u + readout_widgets[i] * 4) == readout_descriptors[i])
            for (uint32_t bank = 0; bank < 2; ++bank)
                if (W(readout_descriptors[i] + 4 + bank * 12) != readout_applied[i][bank]) conflict = 1;
        if (conflict) { readout_blocked = master; ++z7_readout_conflicts; }
        if (conflict || !READOUT_RENDER_CONTEXT()) changed |= readout_release(((readout_ownership)1u << (2u * READOUT_COUNT)) - 1u);
    }
    if (!readout_pending && !readout_blocked && !conflict && READOUT_RENDER_CONTEXT() && readout_bindings()) {
        if (!z7_readout_active) {
            /* Validate all bindings before recording or editing any mask. */
            for (uint32_t i = 0; i < READOUT_COUNT; ++i) for (uint32_t bank = 0; bank < 2; ++bank)
                readout_saved[i][bank] = readout_applied[i][bank] = W(readout_descriptors[i] + 4 + bank * 12);
            z7_readout_active = 1;
        }
        uint32_t information = z7_menu_settings.information[z7_readout_preset];
        for (uint32_t i = 0; i < READOUT_COUNT; ++i) for (uint32_t bank = 0; bank < 2; ++bank) {
            /* Nonzero native format states include Err/Card and other special
             * readouts. Keep the complete native group in every such state.
             * Photo page0/3 are bits0/3, or8/11 in operation193 states. Movie
             * nibble4..7, alternate outputs and the third bank stay untouched.
             */
            uint32_t value = readout_saved[i][bank];
#ifdef Z7_INFORMATION_GROUPS_PROBE
            /* Match custom-DISP information semantics using this Z7's own
             * interpreter bits. Each operation state's standard-photo bit
             * seeds its own pair of base pages independently in each bank.
             * Native control eligibility/visibility still runs afterward.
             * Exposure warnings retain the whole original mask unchanged.
             */
            if (readout_formats[i] == 255u || !B(0xa18237b8u + readout_formats[i])) {
                uint32_t photo = (value & 1u) ? 9u : 0u;
                if (value & 0x100u) photo |= 0x900u;
                value = (value & ~0x909u) | ((information & readout_bits[i]) ? photo : 0u);
            }
#else
            if (!(information & readout_bits[i]) && (readout_formats[i] == 255u || !B(0xa18237b8u + readout_formats[i]))) value &= ~0x909u;
#endif
            uint32_t address = readout_descriptors[i] + 4 + bank * 12;
            if (W(address) != value) { W(address) = value; changed |= 1u << i; }
            readout_applied[i][bank] = value;
        }
    }
    if (changed) {
        __asm__ volatile("dmb sy" ::: "memory");
        ++z7_readout_changes;
    }
    /* This callback runs after format selection and before native control
     * preparation/layout, never during paint. Force the original delta machinery to
     * recompute the transition; leave permissions, text, layout and painting
     * entirely to the following native pipeline.
     */
#ifdef Z7_FOCAL_OVERLAY_PROBE
    changed |= focal_before_update();
    focal_note_update(changed);
#endif
    if (changed) F(0x10367c5bu, void, void)();
}
