/* SPDX-License-Identifier: MIT. Independent original-Z7 page-zero menu binding.
 * Native interface facts derive from original-Z7 menu research. No firmware
 * bytes or foreign component source are embedded. No card writes.
 */
#include "../plugins/display_settings.c"
struct z7_display_settings z7_menu_settings;
volatile uint32_t z7_settings_view, z7_settings_preset, z7_settings_actions;
static uint32_t sm_object[11], sm_meta[7], sm_callbacks[8], sm_controls[7][7], sm_maps[7];
static uint32_t sm_events[14][4], sm_layout[24], sm_geometry[4];
static const char *sm_text[15];
static int16_t sm_boxes[7][4], sm_labels[7][4], sm_values[7][4];
static uint32_t sm_render(uint32_t object);
static uint32_t sm_action(uint32_t object);
static uint32_t sm_back(uint32_t object);
/* Native event router does not promise the page pointer in R0 at BLX R7. */
static uint32_t sm_activate(void) { return sm_action(0xa1833548u); }
static uint32_t sm_back_event(void) { return sm_back(0xa1833548u); }
static uint32_t sm_zero(uint32_t object) { (void)object; return 0; }
static uint32_t sm_one(uint32_t object) { (void)object; return 1; }
static void sm_bind_text(uint32_t object, uint32_t label)
{
    if (!object) return;
    /* Native104BCBDA rejects direct transitions between font kinds1/2/3.
     * Its supported zero-kind bridge invalidates the old font cache first.
     */
    if (W(object + 12) != 2) F(0x103fb341u, uint32_t, uint32_t, uint32_t, uint32_t)(object, 0, 0);
    F(0x103fb341u, uint32_t, uint32_t, uint32_t, uint32_t)(object, label, 2);
    F(0x104e983bu, void, uint32_t)(object); W(object + 0x44) = 1;
}
static uint32_t sm_owned(uint32_t object)
{
    return object == 0xa1833548u && W(object) == 2 &&
        W(object + 16) == (uint32_t)(uintptr_t)sm_callbacks && W(object + 40) == (uint32_t)(uintptr_t)sm_meta;
}
#ifdef Z7_SETTINGS_MENU_ENTRY
static uint32_t sm_open(void)
{
    if (!sm_owned(0xa1833548u)) return 0;
    z7_settings_view = 0;
    return F(0x10404c43u, uint32_t, uint32_t, uint32_t)(2, 0);
}
#endif
static uint32_t sm_label_ownership(void)
{
    for (uint32_t i = 0; i < 15; ++i) {
        uint32_t record = 0xa2019e78u + (230 + i) * 12, buffer = W(record + 4);
        if (!ram(buffer & ~3u, 56)) return 0;
        if (!sm_text[i]) { if (W(record)) return 0; continue; }
        uint32_t length = 0;
        while (length < 50 && sm_text[i][length]) ++length;
        if (length == 50 || W(record) != length || W(record + 8)) return 0;
        for (uint32_t j = 0; j <= length; ++j)
            if (B(buffer + j) != (uint8_t)sm_text[i][j]) return 0;
    }
    return 1;
}
static void sm_text_put(uint32_t slot, const char *text)
{
    F(0x103fbb5du, void, const char *, uint32_t, uint32_t)(text, slot, 0);
    sm_text[slot - 230] = text;
}
static void sm_focus(uint32_t object, uint32_t row)
{
    F(0x10402bc3u, uint32_t, uint32_t, uint32_t)(object, 0x7b10u + row);
}
static void sm_redraw_request(void)
{
    /* Same native queued redraw request used by original page-open10404C42. */
    F(0x103fac5bu, uint32_t, uint32_t, uint32_t, uint32_t)(0x103fa771, 3, 7);
    uint32_t component = W(0xa1833548u + 12);
    if (ram(component, 256)) F(0x103faec7u, uint32_t, uint32_t, uint32_t)(component, 0);
}
static uint32_t sm_back(uint32_t object)
{
    if (!sm_owned(object)) return 0;
    uint32_t old = z7_settings_view;
    if (!old) return F(0x104025edu, uint32_t, uint32_t)(0x3a1);
    z7_settings_view = old == 3 ? 2 : old == 2 ? 1 : 0;
    sm_render(object); sm_focus(object, old == 1 ? z7_settings_preset + 1 : old == 2 ? 1 : 6);
    sm_redraw_request();
    return 0;
}
static uint32_t sm_action(uint32_t object)
{
    if (!sm_owned(object) || !z7_settings_valid(&z7_menu_settings)) return 0;
    uint32_t row = *(volatile uint16_t *)(uintptr_t)(object + 22) + *(volatile uint16_t *)(uintptr_t)(object + 24);
    if (row >= 7 || z7_settings_preset >= 4) return 0;
    uint32_t view = z7_settings_view, p = z7_settings_preset;
    if (!view) {
        if (row == 0) z7_settings_flag(&z7_menu_settings, 0, !(z7_menu_settings.flags & 1));
        else if (row < 5) { z7_settings_preset = row - 1; z7_settings_view = 1; }
        else if (row == 5) z7_settings_page(&z7_menu_settings, 4, !(z7_menu_settings.enabled_pages & 16));
        else z7_settings_flag(&z7_menu_settings, 1, !(z7_menu_settings.flags & 2));
    } else if (view == 1) {
        if (!row) z7_settings_page(&z7_menu_settings, p, !(z7_menu_settings.enabled_pages & (1u << p)));
        else if (row == 1) z7_settings_view = 2;
        else if (row < 6) z7_settings_component(&z7_menu_settings, p, row - 2, !(z7_menu_settings.components[p] & (1u << (row - 2))));
        else z7_settings_reset(&z7_menu_settings, p);
    } else if (view == 2) {
        if (row < 6) z7_settings_information(&z7_menu_settings, p, row, !(z7_menu_settings.information[p] & (1u << row)));
        else z7_settings_view = 3;
    } else if (view == 3) {
        if (row < 2) z7_settings_information(&z7_menu_settings, p, row + 6, !(z7_menu_settings.information[p] & (1u << (row + 6))));
        else if (row == 6) z7_settings_view = 2;
    }
    ++z7_settings_actions;
    z7_battery_enabled = !!(z7_menu_settings.flags & Z7_SETTINGS_BATTERY);
    sm_render(object);
    if (view != z7_settings_view) sm_focus(object, 0);
    sm_redraw_request();
    return 0;
}
static uint32_t sm_render(uint32_t object)
{
    if (!sm_owned(object) || z7_settings_view > 3 || z7_settings_preset >= 4 || !sm_label_ownership()) return 0;
    static const char *const roots[7] = {"Custom pages", "Standard", "Minimal", "Composition", "Exposure", "Information display", "Battery percentage"};
    static const char *const preset[7] = {"Page enabled", "Shooting information", "Framing grid", "Histogram", "Virtual horizon", "Photo highlights", "Reset preset"};
    static const char *const info[7] = {"Shutter speed", "Aperture", "ISO sensitivity", "Shooting mode", "Release mode", "Focus information", "More information"};
    static const char *const extra[7] = {"Other information", "Focal length", "", "", "", "", "Back"};
    const char *const *names = !z7_settings_view ? roots : z7_settings_view == 1 ? preset : z7_settings_view == 2 ? info : extra;
    const char *title = !z7_settings_view ? "Display settings" : z7_settings_view == 1 ? roots[z7_settings_preset + 1] : "Shooting information";
    sm_text_put(230, title);
    for (uint32_t row = 0; row < 7; ++row) {
        const char *value = "--";
        uint32_t bits = 0, mask = 0;
        if (!z7_settings_view && (row == 0 || row >= 5)) {
            bits = row == 5 ? z7_menu_settings.enabled_pages : z7_menu_settings.flags;
            mask = row == 0 ? 1 : row == 5 ? 16 : 2;
        } else if (z7_settings_view == 1 && row != 1 && row != 6) {
            bits = !row ? z7_menu_settings.enabled_pages : z7_menu_settings.components[z7_settings_preset];
            mask = !row ? 1u << z7_settings_preset : 1u << (row - 2);
        } else if (z7_settings_view == 2 && row < 6) { bits = z7_menu_settings.information[z7_settings_preset]; mask = 1u << row; }
        else if (z7_settings_view == 3 && row < 2) { bits = z7_menu_settings.information[z7_settings_preset]; mask = 1u << (row + 6); }
        if (mask) value = bits & mask ? "ON" : "OFF";
        if (!names[row][0] || (z7_settings_view && row == 6 && z7_settings_view != 2)) value = "";
        sm_text_put(231 + row, names[row]); sm_text_put(238 + row, value);
    }
    /* Keep the current event's destination stable across its callback. */
    for (uint32_t i = 0; i < 14; ++i) if (sm_events[i][0] == 0x238 || sm_events[i][0] == 0x253) {
        sm_events[i][1] = (uint32_t)(uintptr_t)sm_back_event;
        sm_events[i][3] = 0x3a0;
    }
    uint32_t pool_pointer = W(object + 36);
    if (pool_pointer) for (uint32_t row = 0; row < 7; ++row) {
        uint32_t label = F(0x103fcf0fu, uint32_t, uint32_t, uint32_t, uint32_t)(pool_pointer, 1, row);
        uint32_t value = F(0x103fcf5du, uint32_t, uint32_t, uint32_t, uint32_t)(pool_pointer, row, 0);
        sm_bind_text(label, 231 + row); sm_bind_text(value, 238 + row);
    }
    uint32_t header = F(0x103faebfu, uint32_t, uint32_t, uint32_t)(0x203, W(object + 12));
    if (header) {
        sm_bind_text(header, 230);
        F(0x103fb32fu, void, uint32_t, uint32_t)(header, 1);
    }
    if (ram(W(object + 12), 96)) W(W(object + 12) + 0x44) = 1;
    return 0;
}
static uint32_t sm_prepare(void)
{
    for (uint32_t i = 0; i < 11; ++i) if (W(0xa1833548u + i * 4)) return 0;
    const uint32_t *leaf = (const uint32_t *)(uintptr_t)(0xa1833548u + 42 * 44);
    if (leaf[0] != 0x002a0002u || leaf[1] != 0xa1833574u || !readable(leaf[10], 28)) return 0;
    const uint32_t *meta = (const uint32_t *)(uintptr_t)leaf[10];
    if (meta[0] != 0x1008 || meta[5] != 0x00020002 || !readable(meta[2], 96) || !readable(meta[3], 28) || !readable(meta[4], 4)) return 0;
    const uint32_t *map = (const uint32_t *)(uintptr_t)W(meta[4]);
    if (!readable((uint32_t)(uintptr_t)map, 14 * 16) || map[13 * 4] != 0x2f2) return 0;
    for (uint32_t i = 0; i < 14; ++i) for (uint32_t j = 0; j < 4; ++j) sm_events[i][j] = map[i * 4 + j];
    for (uint32_t i = 0; i < 14; ++i) if (sm_events[i][0] == 0x239 || sm_events[i][0] == 0x25f || sm_events[i][0] == 0x252) {
        sm_events[i][1] = (uint32_t)(uintptr_t)sm_activate; sm_events[i][2] = 0; sm_events[i][3] = 0x3a0;
    }
    for (uint32_t i = 0; i < 24; ++i) sm_layout[i] = W(meta[2] + i * 4);
    if (sm_layout[7] >> 16 != 0x203) return 0;
    sm_layout[0] = 230;
    for (uint32_t row = 0; row < 7; ++row) {
        for (uint32_t j = 0; j < 7; ++j) sm_controls[row][j] = W(meta[3] + j * 4);
        sm_controls[row][0] = 231 + row; sm_controls[row][4] = 0x1209; sm_controls[row][5] = 238 + row; sm_controls[row][6] = 0x7b10 + row;
        sm_maps[row] = (uint32_t)(uintptr_t)sm_events;
        int16_t y = 62 + row * 52;
        sm_boxes[row][0] = 72; sm_boxes[row][1] = y; sm_boxes[row][2] = 702; sm_boxes[row][3] = y + 48;
        sm_labels[row][0] = 78; sm_labels[row][1] = y + 4; sm_labels[row][2] = 560; sm_labels[row][3] = y + 44;
        sm_values[row][0] = 570; sm_values[row][1] = y; sm_values[row][2] = 696; sm_values[row][3] = y + 48;
    }
    sm_geometry[0] = 7; sm_geometry[1] = (uint32_t)(uintptr_t)sm_boxes; sm_geometry[2] = (uint32_t)(uintptr_t)sm_labels; sm_geometry[3] = (uint32_t)(uintptr_t)sm_values;
    for (uint32_t i = 0; i < 7; ++i) sm_meta[i] = meta[i];
    sm_meta[1] = (uint32_t)(uintptr_t)sm_geometry; sm_meta[2] = (uint32_t)(uintptr_t)sm_layout; sm_meta[3] = (uint32_t)(uintptr_t)sm_controls;
    sm_meta[4] = (uint32_t)(uintptr_t)sm_maps; sm_meta[5] = 0x00070007;
    sm_callbacks[0] = (uint32_t)(uintptr_t)sm_render; sm_callbacks[1] = (uint32_t)(uintptr_t)sm_zero;
    sm_callbacks[2] = 0x1040525f; sm_callbacks[3] = (uint32_t)(uintptr_t)sm_one;
    sm_callbacks[4] = sm_callbacks[5] = sm_callbacks[6] = (uint32_t)(uintptr_t)sm_zero; sm_callbacks[7] = 0x1040525f;
    sm_object[0] = 2; sm_object[1] = leaf[1]; sm_object[4] = (uint32_t)(uintptr_t)sm_callbacks; sm_object[10] = (uint32_t)(uintptr_t)sm_meta;
    z7_settings_defaults(&z7_menu_settings);
    z7_battery_enabled = 0;
    return 1;
}
static void sm_publish(void)
{
    for (uint32_t i = 1; i < 11; ++i) W(0xa1833548u + i * 4) = sm_object[i];
    __asm__ volatile("dmb sy" ::: "memory");
    W(0xa1833548u) = sm_object[0];
}
static void sm_before(void)
{
    before();
    if (!sm_owned(0xa1833548u) || !W(0xa1833548u + 12)) return;
    uint32_t pages = W(0xa181f91cu);
    if (!ram(pages, 16)) return;
    uint32_t stride = W(pages), count = W(pages + 8), data = W(pages + 12), active = 0;
    if (stride < 4 || stride > 1024 || count > 20 || count > W(pages + 4) || !ram(data, count * stride)) return;
    for (uint32_t i = 0; i < count; ++i) if (W(data + i * stride) == 0xa1833548u) active = 1;
    if (!active) return;
    uint32_t header = F(0x103faebfu, uint32_t, uint32_t, uint32_t)(0x203, W(0xa1833548u + 12));
    if (ram(header, 100) && (W(header + 8) != 230 || W(header + 12) != 2)) sm_render(0xa1833548u);
}
