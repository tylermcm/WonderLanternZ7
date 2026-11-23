/* SPDX-License-Identifier: MIT. Independent original-Z7 native page ownership.
 * Follows JKWTCN's MIT save/apply/conditional-restore design with original-Z7
 * selectors and setters. No foreign camera addresses or firmware bytes.
 */
volatile uint32_t z7_base_active, z7_base_saved, z7_base_applied;
volatile uint32_t z7_base_conflicts, z7_base_errors, z7_base_changes;
static uint32_t base_blocked, base_releasing;
static uint32_t base_grid_key, base_grid_valid;
static uint32_t base_gui_memory_context(void)
{
    if (B(0xa18237c6u) || B(0xa201d4d0u + 0x40) || !pool() ||
        B(0xa201d4d0u + 0x18a) > 3) return 0;
    uint32_t pages = W(0xa181f91cu);
    return ram(pages, 16) && !W(pages + 8);
}
static uint32_t base_gui_context(void)
{
    return base_gui_memory_context() && F(0x103673adu, uint32_t, void)() == 0x2f15u;
}
static uint32_t base_property(void)
{
    return F(0x104065a5u, uint32_t, uint32_t)(0x2f15u);
}
static uint32_t base_grid_suppressed(void)
{
    return z7_base_active && !base_blocked && !base_releasing &&
        z7_settings_valid(&z7_menu_settings) && (z7_menu_settings.flags & Z7_SETTINGS_CUSTOM) &&
        !(Z7_INFORMATION_CONFIG_BLOCKED) && z7_readout_preset < 4 &&
        /* This is called inside native scalar reads. Ownership is validated
         * by base_before; do not re-enter the property service here. */
        base_gui_memory_context() && B(0xa201d4d0u + 0x18a) == z7_base_applied &&
        !(z7_menu_settings.components[z7_readout_preset] & Z7_COMPONENT_GRID);
}
static uint32_t base_release(void)
{
    if (!z7_base_active) { base_releasing = 0; return 0; }
    uint32_t current = base_property();
    uint32_t changed = base_grid_valid && !base_grid_key && base_gui_context();
    if (current == z7_base_applied && current != z7_base_saved) {
        /* An inactive output's property may be restored without changing the
         * shared current-output snapshot. Only use the snapshot setter when
         * it still describes our eligible photo-LCD page. */
        uint32_t native = base_gui_context() &&
            B(0xa201d4d0u + 0x18a) == z7_base_applied;
        uint32_t ok = native ? F(0x103673dfu, uint32_t, uint32_t)(z7_base_saved) :
            F(0x104065b1u, uint32_t, uint32_t, uint32_t)(0x2f15u, z7_base_saved);
        if (!ok || base_property() != z7_base_saved) {
            if (native) F(0x103673dfu, uint32_t, uint32_t)(z7_base_applied);
            ++z7_base_errors; base_releasing = 1; return changed;
        }
        changed |= native;
        ++z7_base_changes;
    }
    z7_base_active = 0; base_releasing = 0; base_grid_valid = 0;
    return changed;
}
static uint32_t base_before(void)
{
    uint32_t master = !!(z7_menu_settings.flags & Z7_SETTINGS_CUSTOM);
    if (!master) { base_blocked = 0; return base_release(); }
    uint32_t changed = 0;
    if (base_releasing) {
        changed = base_release();
        if (base_releasing) return changed;
    }
    if (!z7_settings_valid(&z7_menu_settings) || (Z7_INFORMATION_CONFIG_BLOCKED) ||
        z7_readout_preset >= 4 || !base_gui_context()) return changed | base_release();
    if (base_blocked) return changed;
    uint32_t current = base_property();
    if (z7_base_active && (current != z7_base_applied ||
        B(0xa201d4d0u + 0x18a) != z7_base_applied)) {
        ++z7_base_conflicts; base_blocked = 1;
        return changed | base_release();
    }
    if (!z7_base_active) {
        if (current > 3 || B(0xa201d4d0u + 0x18a) != current) return changed;
        z7_base_saved = z7_base_applied = current; z7_base_active = 1;
        base_grid_valid = 0;
    }
    uint32_t components = z7_menu_settings.components[z7_readout_preset];
    uint32_t grid = !!(components & Z7_COMPONENT_GRID);
#ifdef Z7_BASE_INITIAL_GRID_DELTA_ONLY
    /* First ownership of an enabled grid does not change native visibility.
     * Initial suppression still needs a delta, as do all later visibility edits.
     * Page/readout changes independently request their own native invalidation.
     */
    if ((!base_grid_valid && !grid) || (base_grid_valid && base_grid_key != grid)) changed = 1;
#else
    if (!base_grid_valid || base_grid_key != grid) changed = 1;
#endif
    base_grid_key = grid; base_grid_valid = 1;
    uint32_t desired = components & Z7_COMPONENT_HORIZON ? 3u : 0u;
    if (desired == z7_base_applied) return changed;
    uint32_t ok = F(0x103673dfu, uint32_t, uint32_t)(desired);
    if (!ok || base_property() != desired) {
        /* The original setter stores the snapshot before property storage.
         * Roll it back through the same API, then retain conditional cleanup. */
        F(0x103673dfu, uint32_t, uint32_t)(z7_base_applied);
        ++z7_base_errors; base_blocked = base_releasing = 1;
        return changed | base_release();
    }
    z7_base_applied = desired; ++z7_base_changes;
    return 1;
}
