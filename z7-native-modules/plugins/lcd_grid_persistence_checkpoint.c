/* SPDX-License-Identifier: MIT. Independent original-Z7 LCD grid preference.
 * v3 payload in new Z7DSP slots; legacy Z7CFG slots are read-only fallback.
 * No native grid schema extension, automatic migration write or host change.
 */
#include <stdint.h>
static uint32_t lcd_grid_legacy_paths, lcd_grid_absent_slots;
static const char *lcd_grid_settings_path(uint32_t slot);
static uint32_t lcd_grid_load_settings(void);
static void lcd_grid_selected(uint32_t value);
#define Z7_GRID_LAYOUT_PREFERENCES 1
#define Z7_SETTINGS_SLOT_PATH_HOOK(slot) lcd_grid_settings_path(slot)
#define Z7_PERSISTENCE_LOAD_OVERRIDE() lcd_grid_load_settings()
#define Z7_GRID_SELECTION_CHECKPOINT_HOOK(value) lcd_grid_selected(value)
#include "lcd_startup_grid_checkpoint.c"

static const char *lcd_grid_settings_path(uint32_t slot)
{
#ifdef Z7_COMBINED_DISPLAY_PREFERENCES
    if (lcd_grid_legacy_paths == 2) return slot ? "A:\\Z7CFG1.DAT" : "A:\\Z7CFG0.DAT";
    if (lcd_grid_legacy_paths == 1) return slot ? "A:\\Z7DSP1.DAT" : "A:\\Z7DSP0.DAT";
    return slot ? "A:\\Z7EXT1.DAT" : "A:\\Z7EXT0.DAT";
#else
    if (lcd_grid_legacy_paths) return slot ? "A:\\Z7CFG1.DAT" : "A:\\Z7CFG0.DAT";
    return slot ? "A:\\Z7DSP1.DAT" : "A:\\Z7DSP0.DAT";
#endif
}
static uint32_t lcd_grid_read(void *context, uint32_t slot, uint8_t *out)
{
    uint32_t result = z7_settings_files_read(context,slot,out);
#ifdef Z7_COMBINED_DISPLAY_PREFERENCES
    if (result == Z7_STORAGE_IO_ABSENT)
#else
    if (!lcd_grid_legacy_paths && result == Z7_STORAGE_IO_ABSENT)
#endif
        lcd_grid_absent_slots |= 1u << slot;
    return result;
}
static uint32_t lcd_grid_load_settings(void)
{
    /* Loader only, before GUI publication/host readiness; no worker may run
     * while the read-only legacy path selector is active. Always clear it. */
    const struct z7_settings_storage_io input = {
        &z7_persistence_files, lcd_grid_read, 0
    };
#ifdef Z7_COMBINED_DISPLAY_PREFERENCES
    uint32_t result = Z7_STORAGE_DEFAULTS;
    for (uint32_t stage = 0; stage < 3; ++stage) {
        lcd_grid_legacy_paths = stage; lcd_grid_absent_slots = 0;
        result = z7_storage_load(&input,&z7_menu_settings,&z7_persistence_info);
        if (result != Z7_STORAGE_DEFAULTS) break;
        if (lcd_grid_absent_slots != 3) { result = Z7_STORAGE_INVALID; break; }
    }
    lcd_grid_legacy_paths = 0;
    return result;
#else
    uint32_t result = z7_storage_load(&input,&z7_menu_settings,&z7_persistence_info);
    if (result != Z7_STORAGE_DEFAULTS) return result;
    /* Existing invalid/unknown new records must not silently fall back to
     * defaults/legacy and then overwrite evidence on the next menu edit. */
    if (lcd_grid_absent_slots != 3) return Z7_STORAGE_INVALID;
    lcd_grid_legacy_paths = 1;
    result = z7_storage_load(&input,&z7_menu_settings,&z7_persistence_info);
    lcd_grid_legacy_paths = 0;
    return result;
#endif
}
static void lcd_grid_selected(uint32_t value)
{
    /* Same GUI writer as the preference menu. Off is native visibility and
     * retains the last shape; shape publication performs no filesystem I/O. */
    if (value < 1 || value > 5) return;
    struct z7_display_settings staged = z7_menu_settings;
    staged.grid_layout = value;
    persistence_commit(&staged);
}
