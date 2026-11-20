/* SPDX-License-Identifier: MIT. Independent original-Z7 five-choice routing.
 * Includes the complete focal/Other/histogram stack. No application, registry,
 * native snapshot or framebuffer assignments implement the transition.
 */
static uint32_t information_fault;
static uint32_t information_custom(void)
{
    return z7_settings_valid(&z7_menu_settings) && (z7_menu_settings.flags & Z7_SETTINGS_CUSTOM);
}
static uint32_t information_menu_clear(void)
{
    uint32_t p = W(0xa181f91cu);
    return ram(p, 16) && !W(p + 8);
}
static uint32_t information_start(void)
{
    if (information_fault || z7_information_pending || z7_information_ledger.phase != IT_IDLE ||
        !information_custom() || !(z7_menu_settings.enabled_pages & 16u) ||
        !base_gui_context() || !information_shooting_context() || !information_bindings() ||
        base_blocked || base_releasing || readout_blocked || readout_pending) return 0;
    uint32_t page = base_property();
    if (page > 3 || B(0xa201d4d0u + 0x18a) != page ||
        (z7_base_active && page != z7_base_applied)) return 0;
    information_saved = z7_base_active ? z7_base_saved : page;
    information_previous = z7_readout_preset < 4 ? z7_readout_preset : 0;
    z7_information_target = information_previous;
    z7_information_pending = z7_information_suspended = 1;
    return 1;
}
static uint32_t information_return_target(void)
{
    uint32_t target = z7_information_target;
    if (!information_custom()) return information_previous;
    if (target < 4 && (z7_menu_settings.enabled_pages & (1u << target))) return target;
    target = z7_settings_next(&z7_menu_settings, 4);
    return target < 4 ? target : information_previous;
}
static void information_sync_preset(void)
{
    if (z7_information_ledger.phase != IT_IDLE) {
        if (information_observe(&z7_information_ledger)) {
            z7_readout_preset = information_return_target();
            z7_information_suspended = information_fault;
            if (!information_fault) ++z7_information_returns;
        } else if (z7_information_ledger.phase == IT_CONFLICT && !information_custom()) {
            /* Foreign state is abandoned, never restored or adopted while ON. */
            z7_information_ledger.phase = IT_IDLE;
            z7_information_suspended = 0;
        }
    }
    if (!information_custom()) {
        information_fault = 0;
        if (z7_information_ledger.phase == IT_IDLE) {
            z7_information_pending = z7_information_suspended = 0;
            if (z7_readout_preset >= 4) z7_readout_preset = information_previous;
        }
        return;
    }
    if (z7_information_pending && !(z7_menu_settings.enabled_pages & 16u)) {
        z7_information_pending = z7_information_suspended = 0;
    }
    if (information_fault || z7_information_pending || z7_information_ledger.phase != IT_IDLE ||
        !base_gui_context() || !information_shooting_context()) return;
    if (z7_readout_preset < 4 && (z7_menu_settings.enabled_pages & (1u << z7_readout_preset))) return;
    uint32_t next = z7_settings_next(&z7_menu_settings, z7_readout_preset);
    if (next < 4) { z7_readout_preset = next; ++z7_preset_reselections; }
    else if (next == 4 && information_start()) ++z7_preset_reselections;
}
static uint32_t information_preset_cycle(void)
{
    if (z7_information_pending || (z7_information_ledger.phase != IT_IDLE &&
        z7_information_ledger.phase != IT_CONFLICT)) return 0x100u;
    if (!readout_context() || information_fault) { ++z7_preset_delegated; return 0; }
    uint32_t next = z7_settings_next(&z7_menu_settings, z7_readout_preset);
    if (next < 4) z7_readout_preset = next;
    else if (next != 4 || !information_start()) { ++z7_preset_delegated; return 0; }
    ++z7_preset_cycles;
    return 0x100u;
}
static uint32_t information_native_cycle(void)
{
    if (z7_information_ledger.phase == IT_IDLE || z7_information_ledger.phase == IT_CONFLICT) return 0;
    information_observe(&z7_information_ledger);
    if (z7_information_ledger.phase == IT_EXITING || z7_information_ledger.phase == IT_CONFIG_EXIT ||
        z7_information_ledger.phase == IT_RETURN_REQUESTED) return 0x100u;
    if (z7_information_ledger.phase != IT_VISIBLE) return 0;
    z7_readout_preset = 4;
    uint32_t next = information_custom() ? z7_settings_next(&z7_menu_settings, 4) : information_previous;
    if (next == 4) { ++z7_preset_cycles; return 0x100u; }
    if (next > 3 || !information_exit_admitted(&z7_information_ledger)) return 0;
    z7_information_target = next; ++z7_preset_cycles;
    return 0; /* Execute the original admitted native return, with its gates. */
}
static void information_before_update(void)
{
    if (z7_information_ledger.phase == IT_IDLE || z7_information_ledger.phase == IT_CONFLICT) return;
    information_observe(&z7_information_ledger);
    if (z7_information_ledger.phase == IT_VISIBLE) z7_readout_preset = 4;
    if (information_custom() && (z7_menu_settings.enabled_pages & 16u)) return;
    z7_information_target = information_custom() ? z7_settings_next(&z7_menu_settings, 4) : information_previous;
    if (information_menu_clear()) information_request_return(&z7_information_ledger);
}
static void information_after_gui(void)
{
    if (!z7_information_pending) return;
    if (!information_custom() || !(z7_menu_settings.enabled_pages & 16u)) {
        z7_information_pending = z7_information_suspended = 0; return;
    }
    /* Retired painters must have cleared their own flags. Native rendering,
     * not a synthetic clear or screenshot, performs this cleanup. No claim of
     * a hardware completed-paint fence is made by these ownership checks.
     */
    if (z7_base_active || base_releasing || z7_readout_active || readout_pending ||
        histogram_owned || focal_visible || focal_retire || visible || retire || histogram_pending()) return;
    if (readout_blocked || base_blocked) {
        information_fault = 1; ++z7_information_errors; z7_information_pending = 0; return;
    }
    if (!information_shooting_context() || !base_gui_context()) return;
    /* Input was admitted before retirement began. Revalidate native cycle
     * eligibility before issuing the deferred request: a menu/output/busy
     * transition during cleanup must not turn old admission into a new entry.
     * Settings-driven reselection uses the same native eligibility boundaries.
     */
    uint32_t state = B(0xa201d4d0u) & 63u;
    if (state == 2 || state == 5 || state == 11 || B(0xa201d4d0u + 0x192) ||
        F(0x10401d23u, uint32_t, void)() || F(0x10297a2fu, uint32_t, void)() ||
        F(0x10297a17u, uint32_t, void)()) return;
    if (!F(0x103ea09fu, uint32_t, uint32_t)(0x2a) &&
        (F(0x103ea09fu, uint32_t, uint32_t)(2) || !F(0x102c7427u, uint32_t, void)())) return;
    if (base_property() != information_saved || B(0xa201d4d0u + 0x18a) != information_saved) {
        information_fault = 1; ++z7_information_errors; z7_information_pending = 0; return;
    }
    uint32_t entered = information_enter(&z7_information_ledger, information_saved, 1);
    z7_information_pending = 0;
    if (entered == 2) ++z7_information_entries;
    else {
        ++z7_information_errors; information_fault = 1;
        /* The ledger retains partial-failure recovery. Master OFF acknowledges
         * an entry failure; never issue a fresh request every GUI frame. */
    }
}
