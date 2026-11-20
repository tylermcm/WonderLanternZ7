/* SPDX-License-Identifier: MIT. Independent original-Z7 preset input routing.
 * Runs inside the original cycle call after native admission, never replaces
 * the outer key callback. API40 optionally adds owned information-app routing.
 */
volatile uint32_t z7_preset_cycles, z7_preset_delegated;
static uint32_t preset_cycle(void)
{
#ifdef Z7_INFORMATION_APP_PROBE
    return information_preset_cycle();
#else
    if (!readout_context()) { ++z7_preset_delegated; return 0; }
    uint32_t next = z7_settings_next(&z7_menu_settings, z7_readout_preset);
    if (next >= 4) { ++z7_preset_delegated; return 0; }
    z7_readout_preset = next;
    ++z7_preset_cycles;
    return 0x100u;
#endif
}
