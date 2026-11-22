/* SPDX-License-Identifier: MIT
 * Independent original-Z7 C 3.80 display module. Native interface facts are
 * documented in GRID_LAYOUTS_RESEARCH.md and the display-module audit.
 * No Z7II addresses, firmware bytes, allocation or image decoding are embedded.
 */
#include "module.h"
#include "display.h"
#include <stdint.h>

#define WORD(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define FN(a, r, ...) ((r (*)(__VA_ARGS__))(uintptr_t)(a))
#define GRID_OBJECT 0xa1836f8cu
#define GRID_RAW 0xa24f182cu
#define GRID_TABLE 0x1064fd90u
#define HISTOGRAM 0xa1827404u
#define Z7_GRID_COMMIT_MASKS() do { \
    for (uint32_t z7_mask_i = 0; z7_mask_i < 9; ++z7_mask_i) WORD(HISTOGRAM + 4 + z7_mask_i * 4) = 0xcccu; \
    __asm__ volatile("dmb sy" ::: "memory"); \
} while (0)

#ifdef Z7_SETTINGS_MENU_ENTRY
#define Z7_GRID_ROWS 7
#define Z7_GRID_ACTIONS 7
#define Z7_GRID_NAME_BYTES 20
static uint32_t sm_open(void);
#else
#define Z7_GRID_ROWS 6
#define Z7_GRID_ACTIONS 5
#define Z7_GRID_NAME_BYTES 16
#endif
static uint16_t tables[4][48];
static uint32_t metadata[7], callbacks[5], controls[Z7_GRID_ROWS][7], maps[Z7_GRID_ROWS];
static uint32_t events[Z7_GRID_ACTIONS][17][4], geometry[4];
static int16_t boxes[Z7_GRID_ROWS][4], labels[Z7_GRID_ROWS][4], values[Z7_GRID_ROWS][4];
static const char names[Z7_GRID_ROWS][Z7_GRID_NAME_BYTES] = {"4x4 grid", "3x3 grid", "Golden ratio", "Center cross", "6x6 grid", "Off"
#ifdef Z7_SETTINGS_MENU_ENTRY
    , "Display settings"
#endif
};
static const uint32_t control_ids[Z7_GRID_ROWS] = {0x1901, 0x7a30, 0x7a31, 0x7a32, 0x7a33, 0x1902
#ifdef Z7_SETTINGS_MENU_ENTRY
    , 0x7a34
#endif
};
volatile uint32_t z7_display_grid_entries;

static uint32_t readable(uint32_t p, uint32_t n)
{
    return p % 4 == 0 && ((p >= 0x10020000u && p <= 0x11fa55b8u - n) ||
                          (p >= 0xa1800000u && p <= 0xa1901200u - n));
}
#ifdef Z7_GRID_VOLATILE_CHECKPOINT
/* Checkpoint only: native storage remains ordinary Off/On (0/1). Layout is
 * volatile, starts at thirds, and never extends the native settings schema.
 */
static uint32_t checkpoint_grid_value = 2;
static uint32_t checkpoint_grid_lcd(void)
{
    return !*(volatile uint8_t *)(uintptr_t)0xa18237c6u &&
           !*(volatile uint8_t *)(uintptr_t)0xa201d510u;
}
static uint32_t grid_value(void)
{
    return WORD(GRID_RAW) == 1 ? checkpoint_grid_value : 0;
}
#endif
static const uint16_t *grid_source(const uint16_t *native)
{
#ifdef Z7_GRID_VOLATILE_CHECKPOINT
    if (!checkpoint_grid_lcd() || WORD(GRID_RAW) != 1) return native;
    uint32_t value = grid_value();
#else
    (void)native;
    uint32_t value = WORD(GRID_RAW);
#endif
    if (value == 2 || value == 3) return tables[1];
    if (value == 4) return tables[2];
    if (value == 5) return tables[3];
    return tables[0];
}
#ifdef Z7_SETTINGS_BASE_PROBE
static uint32_t base_grid_suppressed(void);
#endif
static uint32_t scalar_value(uint32_t key, uint32_t value)
{
#ifdef Z7_SETTINGS_BASE_PROBE
    if (key == 0x102du && base_grid_suppressed()) return 0;
#endif
    return key == 0x102d && value >= 2 && value <= 5 ? 1 : value;
}
static uint32_t histogram_gate(uint32_t state) {
#ifdef Z7_HISTOGRAM_EXTRA_PROBE
    return state == 2;
#else
    return state == 2 || state == 3;
#endif
}
static void grid_geometry(void *pointer)
{
#ifdef Z7_GRID_VOLATILE_CHECKPOINT
    if (!checkpoint_grid_lcd() || grid_value() != 3 || (uintptr_t)pointer != 0xa2020c2cu) return;
#else
    if (WORD(GRID_RAW) != 3 || (uintptr_t)pointer != 0xa2020c2cu) return;
#endif
    uint8_t *p = pointer;
    int32_t origins[2];
    uint32_t intervals[2];
    const uint32_t spans[2] = {16, 4}, offsets[2] = {2, 12}, steps[2] = {8, 20};
    for (uint32_t i = 0; i < 2; ++i) {
        uint32_t span = *(uint32_t *)(p + spans[i]);
        uint32_t old = *(uint16_t *)(p + steps[i]);
        if (!span || span > 32767) return;
        uint32_t first = (span * 25033u) >> 16;
        origins[i] = *(int16_t *)(p + offsets[i]) - (int32_t)old + (int32_t)first;
        intervals[i] = span - 2 * first;
        if (origins[i] < -32768 || origins[i] > 32767 || intervals[i] > 65535) return;
    }
    for (uint32_t i = 0; i < 2; ++i) {
        *(int16_t *)(p + offsets[i]) = (int16_t)origins[i];
        *(uint16_t *)(p + steps[i]) = (uint16_t)intervals[i];
    }
}
static uint32_t set_grid(uint32_t value) {
#ifdef Z7_GRID_VOLATILE_CHECKPOINT
    if (value >= 1 && value <= 5) checkpoint_grid_value = value;
    value = !!value;
#endif
    return FN(0x104065b1u, uint32_t, uint32_t, uint32_t)(0x102d, value);
}
static uint32_t fourths(void) { return set_grid(1); }
static uint32_t thirds(void) { return set_grid(2); }
static uint32_t golden(void) { return set_grid(3); }
static uint32_t center(void) { return set_grid(4); }
static uint32_t dense(void) { return set_grid(5); }
#ifdef Z7_SETTINGS_MENU_ENTRY
static uint32_t off_owned(void) { return FN(0x104f5593u, uint32_t, void)(); }
#endif
static uint32_t (*const choices[Z7_GRID_ACTIONS])(void) = {fourths, thirds, golden, center, dense
#ifdef Z7_SETTINGS_MENU_ENTRY
    , off_owned, sm_open
#endif
};

static uint32_t grid_enter(uint32_t object)
{
    ++z7_display_grid_entries;
    for (uint32_t i = 0; i < Z7_GRID_ROWS; ++i)
        FN(0x103fbb5du, void, const char *, uint32_t, uint32_t)(names[i], 39 + i, 0);
    uint32_t list = WORD(object + 36);
    if (list) for (uint32_t i = 0; i < Z7_GRID_ROWS; ++i) {
        uint32_t control = FN(0x103fcf0fu, uint32_t, uint32_t, uint32_t, uint32_t)(list, 1, i);
        if (!control) break;
        FN(0x103fb345u, void, uint32_t, uint32_t)(control, 39 + i);
    }
#ifdef Z7_GRID_VOLATILE_CHECKPOINT
    uint32_t value = grid_value();
#else
    uint32_t value = WORD(GRID_RAW);
#endif
    uint32_t id = control_ids[value >= 1 && value <= 5 ? value - 1 : 5];
    if (FN(0x10405f01u, uint32_t, void)() != 1)
        FN(0x10402bc3u, void, uint32_t, uint32_t)(object, id);
    FN(0x10404cd9u, void, uint32_t, uint32_t, uint32_t)(object, id, 1);
    return 0;
}
static const struct z7_display_hooks hooks = {
    Z7_DISPLAY_ABI, sizeof(hooks), grid_source, grid_geometry, scalar_value, histogram_gate, 0, 0
};
static const struct z7_grid_menu menu = {Z7_DISPLAY_ABI, sizeof(menu), metadata, callbacks};

uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi != Z7_MODULE_ABI || api->target != Z7_MODULE_TARGET ||
        api->size < sizeof(*api) || !api->register_display || !api->register_grid_menu) return 1;
    volatile uint32_t *object = (volatile uint32_t *)(uintptr_t)GRID_OBJECT;
    if (object[0] != 0x01530002u || !readable(object[10], 28) || !readable(object[4], 20) ||
        WORD(0x1064d610u + 31 * 4) != HISTOGRAM || WORD(0x114d30ccu) != 7 ||
        WORD(0x114d30d4u) != GRID_RAW) return 1;
    const uint32_t *old_meta = (const uint32_t *)(uintptr_t)object[10];
    const uint32_t *old_callbacks = (const uint32_t *)(uintptr_t)object[4];
    if (old_meta[5] != 0x00020002u || old_callbacks[0] != 0x104efa6bu || old_callbacks[2] != 0x1040525fu ||
        !readable(old_meta[3], 56) || !readable(old_meta[4], 8)) return 1;
    const uint32_t *old_controls = (const uint32_t *)(uintptr_t)old_meta[3];
    const uint32_t *old_maps = (const uint32_t *)(uintptr_t)old_meta[4];
    if (old_controls[6] != 0x1901 || old_controls[13] != 0x1902 || !readable(old_maps[0], 272)) return 1;
    const uint32_t *old_events = (const uint32_t *)(uintptr_t)old_maps[0];
    const uint16_t *native = (const uint16_t *)(uintptr_t)GRID_TABLE;
    for (uint32_t i = 0; i < 3; ++i)
        if (native[i * 16 + 5] != 3 || native[i * 16 + 11] != 3) return 1;
    for (uint32_t i = 0; i < 9; ++i)
        if (WORD(HISTOGRAM + 4 + i * 4) != (i < 6 ? 0x444u : 0x440u)) return 1;
    const uint32_t counts[4] = {3, 2, 1, 5};
    for (uint32_t table = 0; table < 4; ++table) {
        for (uint32_t i = 0; i < 48; ++i) tables[table][i] = native[i];
        for (uint32_t i = 0; i < 3; ++i)
            tables[table][i * 16 + 5] = tables[table][i * 16 + 11] = (uint16_t)counts[table];
    }
#ifdef Z7_SETTINGS_MENU_ENTRY
    if (!readable(old_maps[1], 17 * 16)) return 1;
#endif
    for (uint32_t row = 0; row < Z7_GRID_ACTIONS; ++row) {
        const uint32_t *source_events = old_events;
        uint32_t expected = 0x104f5589u;
#ifdef Z7_SETTINGS_MENU_ENTRY
        if (row == 5) { source_events = (const uint32_t *)(uintptr_t)old_maps[1]; expected = 0x104f5593u; }
#endif
        uint32_t activations = 0;
        for (uint32_t i = 0; i < 17; ++i) {
            for (uint32_t j = 0; j < 4; ++j) events[row][i][j] = source_events[i * 4 + j];
            if (events[row][i][0] == 0x239 || events[row][i][0] == 0x25f) {
                if (events[row][i][1] != expected || events[row][i][2] || events[row][i][3] != 0x3a1) return 1;
                events[row][i][1] = (uint32_t)(uintptr_t)choices[row];
#ifdef Z7_SETTINGS_MENU_ENTRY
                if (row == 6) events[row][i][3] = 0x3a0;
#endif
                ++activations;
            }
        }
        if (activations != 2) return 1;
        maps[row] = (uint32_t)(uintptr_t)events[row];
    }
#ifndef Z7_SETTINGS_MENU_ENTRY
    maps[5] = old_maps[1];
#endif
    for (uint32_t row = 0; row < Z7_GRID_ROWS; ++row) {
        for (uint32_t i = 0; i < 7; ++i) controls[row][i] = old_controls[(row == 5 ? 7 : 0) + i];
        controls[row][0] = 39 + row;
        controls[row][4] = 0x1209;
        controls[row][6] = control_ids[row];
        int16_t y = (int16_t)(96 + row * 52);
        boxes[row][0] = 72; boxes[row][1] = y; boxes[row][2] = 702; boxes[row][3] = y + 48;
        labels[row][0] = 150; labels[row][1] = y + 4; labels[row][2] = 690; labels[row][3] = y + 44;
        values[row][0] = 690; values[row][1] = y; values[row][2] = 696; values[row][3] = y + 48;
    }
    geometry[0] = Z7_GRID_ROWS;
    geometry[1] = (uint32_t)(uintptr_t)boxes;
    geometry[2] = (uint32_t)(uintptr_t)labels;
    geometry[3] = (uint32_t)(uintptr_t)values;
    for (uint32_t i = 0; i < 7; ++i) metadata[i] = old_meta[i];
    metadata[1] = (uint32_t)(uintptr_t)geometry;
    metadata[3] = (uint32_t)(uintptr_t)controls;
    metadata[4] = (uint32_t)(uintptr_t)maps;
    metadata[5] = Z7_GRID_ROWS | Z7_GRID_ROWS << 16;
    for (uint32_t i = 0; i < 5; ++i) callbacks[i] = old_callbacks[i];
    callbacks[0] = (uint32_t)(uintptr_t)grid_enter;
#ifdef Z7_DISPLAY_MENU_FOREIGN_CONTROLS
    metadata[3] = old_meta[3];
#endif
#ifdef Z7_DISPLAY_MENU_BAD_CALLBACK
    callbacks[0] = old_callbacks[0];
#endif
    if (!api->register_display(&hooks) || !api->register_grid_menu(&menu)) return 1;
#ifdef Z7_DISPLAY_MODULE_FAIL
    return 1;
#endif
    /* Both registrations are staged. These scalar mask stores cannot publish
     * module code or dangling pointers; no failure path follows them.
     */
#ifndef Z7_GRID_DEFER_MASKS
    Z7_GRID_COMMIT_MASKS();
#endif
    return 0;
}
