/* SPDX-License-Identifier: MIT. Independent original-Z7 readout mask adapter.
 * Only independently identified shutter/aperture/ISO groups are bound here.
 * No custom DISP routing, forced visibility or unidentified widget edits.
 */
volatile uint32_t z7_readout_preset, z7_readout_active, z7_readout_conflicts, z7_readout_changes;
static uint32_t readout_blocked, readout_pending, readout_saved[3][2], readout_applied[3][2];
static const uint32_t readout_descriptors[3] = {0xa1824174u, 0xa1824264u, 0xa1824654u};
static const uint8_t readout_widgets[3] = {10, 11, 15};
static const uint8_t readout_formats[3] = {0, 1, 5};
static const uint8_t readout_bits[3] = {Z7_INFO_SHUTTER, Z7_INFO_APERTURE, Z7_INFO_ISO};
static const uint32_t readout_updaters[3] = {0x102f378du, 0x102f3951u, 0x102f3b5bu};
static uint32_t readout_bindings(void)
{
    for (uint32_t i = 0; i < 3; ++i) {
        uint32_t p = readout_descriptors[i];
        if (W(0x1064d610u + readout_widgets[i] * 4) != p || !ram(p, 48) ||
            W(0x1064c67cu + readout_widgets[i] * 4) != readout_updaters[i]) return 0;
    }
    return 1;
}
static uint32_t readout_gui_context(void)
{
    if (B(0xa18237c6u) || B(0xa201d4d0u + 0x40) || !pool()) return 0;
    uint32_t page = B(0xa201d4d0u + 0x18a);
    if (page != 0 && page != 3) return 0;
    uint32_t pages = W(0xa181f91cu);
    return ram(pages, 16) && !W(pages + 8);
}
static uint32_t readout_context(void)
{
    return z7_settings_valid(&z7_menu_settings) && (z7_menu_settings.flags & Z7_SETTINGS_CUSTOM) &&
        z7_readout_preset < 4 && readout_gui_context();
}
static uint32_t readout_release(uint32_t words)
{
    uint32_t changed = 0, pending = 0;
    for (uint32_t i = 0; i < 3; ++i) {
        uint32_t p = readout_descriptors[i];
        for (uint32_t bank = 0; bank < 2; ++bank) {
            uint32_t bit = 1u << (i * 2 + bank);
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
    uint32_t changed = 0, conflict = 0;
    if (readout_pending) changed = readout_release(readout_pending);
    uint32_t master = !!(z7_menu_settings.flags & Z7_SETTINGS_CUSTOM);
    if (!master) readout_blocked = 0;
    if (z7_readout_active) {
        conflict = !readout_bindings();
        for (uint32_t i = 0; i < 3; ++i) if (W(0x1064d610u + readout_widgets[i] * 4) == readout_descriptors[i])
            for (uint32_t bank = 0; bank < 2; ++bank)
                if (W(readout_descriptors[i] + 4 + bank * 12) != readout_applied[i][bank]) conflict = 1;
        if (conflict) { readout_blocked = master; ++z7_readout_conflicts; }
        if (conflict || !readout_context()) changed |= readout_release(0x3fu);
    }
    if (!readout_pending && !readout_blocked && !conflict && readout_context() && readout_bindings()) {
        if (!z7_readout_active) {
            /* Validate all bindings before recording or editing any mask. */
            for (uint32_t i = 0; i < 3; ++i) for (uint32_t bank = 0; bank < 2; ++bank)
                readout_saved[i][bank] = readout_applied[i][bank] = W(readout_descriptors[i] + 4 + bank * 12);
            z7_readout_active = 1;
        }
        uint32_t information = z7_menu_settings.information[z7_readout_preset];
        for (uint32_t i = 0; i < 3; ++i) for (uint32_t bank = 0; bank < 2; ++bank) {
            /* Nonzero native format states include Err/Card and other special
             * readouts. Keep the complete native group in every such state.
             * Photo page0/3 are bits0/3, or8/11 in operation193 states. Movie
             * nibble4..7, alternate outputs and the third bank stay untouched.
             */
            uint32_t value = readout_saved[i][bank];
            if (!(information & readout_bits[i]) && !B(0xa18237b8u + readout_formats[i])) value &= ~0x909u;
            uint32_t address = readout_descriptors[i] + 4 + bank * 12;
            if (W(address) != value) { W(address) = value; changed |= 1u << i; }
            readout_applied[i][bank] = value;
        }
    }
    if (changed) {
        __asm__ volatile("dmb sy" ::: "memory");
        ++z7_readout_changes;
    }
    /* This callback runs before the native snapshot comparison and widget
     * computation, never during paint. Force the original delta machinery to
     * recompute the transition; leave permissions, text, layout and painting
     * entirely to the following native pipeline.
     */
    if (changed) F(0x10367c5bu, void, void)();
}
