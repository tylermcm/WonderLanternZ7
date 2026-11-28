/* SPDX-License-Identifier: MIT. Independent original-Z7 page-zero menu binding.
 * Native interface facts derive from original-Z7 menu research. No firmware
 * bytes or foreign component source are embedded. No card writes.
 */
#include "../plugins/display_settings.c"
#ifdef Z7_LCD_FIRST_RELEASE
#include "../plugins/lcd_release_policy.h"
#endif
#ifdef Z7_SHUTTER_SOUND_MENU
#if defined(Z7_LCD_INFORMATION_PAGE) || !defined(Z7_LCD_FIRST_RELEASE)
#error The shutter-sound row uses the release root page's free seventh row
#endif
#include "../plugins/shutter_sound_lcd.h"
#endif
#ifdef Z7_AF_BUTTONS_MENU
#ifndef Z7_SOUND_FOLDER
#error The AF-area buttons page is reached from the sound folder page
#endif
#include "../plugins/af_buttons_lcd.h"
#endif
struct z7_display_settings z7_menu_settings;
#ifdef Z7_SETTINGS_PERSISTENCE
static void persistence_commit(const struct z7_display_settings *);
enum persistence_state { PS_STARTING, PS_DEFAULTS, PS_CLEAN, PS_SAVING, PS_RETRY, PS_BLOCKED };
enum persistence_display { PD_DEFAULTS, PD_SAVED, PD_UNSAVED, PD_SAVING, PD_RETRY, PD_BLOCKED };
static uint32_t persistence_display_status(void);
static uint32_t sm_save_status = UINT32_MAX;
volatile uint32_t z7_menu_status_events, z7_menu_status_paints, z7_menu_status_notifications;
static uint32_t sm_menu_dispatch(uint32_t event, uint32_t data);
static void persistence_menu_notify(void);
static char sm_title[50];
static const char *sm_persistent_title(const char *base, uint32_t status)
{
    static const char *const suffix[] = {"Defaults", "Saved", "Unsaved", "Saving", "Save retry", "Restart to save"};
    uint32_t length = 0;
    while (*base && length < sizeof(sm_title) - 1) sm_title[length++] = *base++;
    const char *separator = ": ";
    while (*separator && length < sizeof(sm_title) - 1) sm_title[length++] = *separator++;
    const char *text = suffix[status <= PD_BLOCKED ? status : PD_BLOCKED];
    while (*text && length < sizeof(sm_title) - 1) sm_title[length++] = *text++;
    sm_title[length] = 0;
    return sm_title;
}
#endif
#ifdef Z7_SETTINGS_READOUT_PROBE
#include "display_readouts_policy.h"
#endif
#ifdef Z7_SETTINGS_DISP_PROBE
#include "display_disp_policy.h"
#endif
volatile uint32_t z7_settings_view, z7_settings_preset, z7_settings_actions;
static uint32_t sm_object[11], sm_meta[7], sm_callbacks[8], sm_controls[7][7], sm_maps[7];
static uint32_t sm_events[14][4], sm_layout[24], sm_geometry[4];
#ifdef Z7_LCD_FIRST_RELEASE
static uint32_t sm_lcd_rows_ready;
static void sm_lcd_prepare_rows(void)
{
    sm_lcd_rows_ready = 0;
    sm_meta[5] = 7u | (7u << 16);
}
#endif
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
#ifdef Z7_PIXEL_NIKON_MENU
static uint32_t sm_owned(uint32_t object);
#include "../plugins/pixel_nikon_photo_menu.h"
#endif
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
#ifdef Z7_PIXEL_NIKON_MENU
    z7_pn_photo_origin=0;
#endif
#ifdef Z7_LCD_FIRST_RELEASE
    sm_lcd_prepare_rows();
#endif
    z7_settings_view = 0;
    return F(0x10404c43u, uint32_t, uint32_t, uint32_t)(2, 0);
}
#endif
#ifdef Z7_SETTINGS_ROOT_ENTRY
#include "settings_root_entry.h"
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
    uint32_t old = *(volatile uint16_t *)(uintptr_t)(object + 22) + *(volatile uint16_t *)(uintptr_t)(object + 24);
    uint32_t ready = W(object + 36) && old < 7 && row < 7;
    /* 10402BC2 only changes row indices; native palette changes are separate.
     * Use the original unfocus/highlight routines around that index change.
     */
    if (ready) {
        uint32_t previous = F(0x103fcf0fu, uint32_t, uint32_t, uint32_t, uint32_t)(W(object + 36), 1, old);
        if (previous) F(0x103fb30bu, uint32_t, uint32_t, uint32_t)(previous, 0);
        F(0x10405d49u, uint32_t, uint32_t, uint32_t)(object, 0x7b10u + old);
    }
    F(0x10402bc3u, uint32_t, uint32_t, uint32_t)(object, 0x7b10u + row);
    if (ready) {
        uint32_t current = F(0x103fcf0fu, uint32_t, uint32_t, uint32_t, uint32_t)(W(object + 36), 1, row);
        if (current) F(0x103fb30bu, uint32_t, uint32_t, uint32_t)(current, 1);
        F(0x10405a93u, uint32_t, uint32_t, uint32_t, uint32_t)(object, (uint32_t)(uintptr_t)sm_controls[row], row);
    }
}
static void sm_redraw_request(void)
{
    /* Paint changed component commands before the native display refresh.
     * Refreshing first presents the previous text until the next event.
     * 103FA770 is the native refresh predicate, not a deferred callback.
     */
    uint32_t component = W(0xa1833548u + 12);
    if (ram(component, 256)) F(0x103faec7u, uint32_t, uint32_t, uint32_t)(component, 0);
    F(0x103fac5bu, uint32_t, uint32_t, uint32_t, uint32_t)(0x103fa771, 3, 7);
}
static uint32_t sm_back(uint32_t object)
{
    if (!sm_owned(object)) return 0;
    uint32_t old = z7_settings_view;
    if (!old) return F(0x104025edu, uint32_t, uint32_t)(0x3a1);
#ifdef Z7_PIXEL_MENU
#ifdef Z7_PIXEL_NIKON_MENU
    if (old>=15u && old<=17u) {
        z7_settings_view=old==15u ? 12u : 15u;
        sm_render(object);sm_focus(object,old==15u ? 0u : old-16u);
        sm_redraw_request();return 0;
    }
    if (old>=8u && old<=14u) {
        uint32_t row=old<=13u ? old-8u : z7_pn_help_focus;
        z7_settings_view=7;sm_render(object);sm_focus(object,row);
        sm_redraw_request();return 0;
    }
#endif
    if (old == 7) {
#ifdef Z7_PIXEL_NIKON_MENU
        if (z7_pn_photo_origin) { z7_pn_photo_origin=0;return F(0x104025edu,uint32_t,uint32_t)(0x3a1); }
#endif
        z7_settings_view = 5; sm_render(object); sm_focus(object, 2);
        sm_redraw_request(); return 0;
    }
#endif
#ifdef Z7_AF_BUTTONS_MENU
    if (old == 6) {
        z7_settings_view = 5; sm_render(object); sm_focus(object, 2);
        sm_redraw_request(); return 0;
    }
#endif
#ifdef Z7_SOUND_FOLDER
    if (old == 5) {
        z7_settings_view = 0; sm_render(object); sm_focus(object, 6);
        sm_redraw_request(); return 0;
    }
#endif
#ifdef Z7_HIGHLIGHT_PREFERENCES
    if (old == 4) {
        z7_settings_view = 1; sm_render(object); sm_focus(object, 5);
        sm_redraw_request(); return 0;
    }
#endif
    z7_settings_view = old == 3 ? 2 : old == 2 ? 1 : 0;
    sm_render(object); sm_focus(object, old == 1 ? z7_settings_preset + 1 : old == 2 ? 1 : 6);
    sm_redraw_request();
    return 0;
}
#ifdef Z7_PIXEL_NIKON_MENU
static uint32_t sm_pn_interval_change(int step)
{
    if (!sm_owned(0xa1833548u)) return 0;
    volatile uint32_t *draft=0;uint32_t maximum=0;
    if (z7_settings_view==11u) { draft=&z7_pn_interval_draft;maximum=30; }
    if (z7_settings_view==16u) { draft=&z7_pn_ae_draft_count;maximum=8; }
    if (z7_settings_view==17u) { draft=&z7_pn_ae_draft_step;maximum=11; }
    if (!draft) return 0;
    if (z7_settings_view==17u) {
        int next=(int)*draft+step;
        while (next>=0 && next<=11 && !z7_pn_step_allowed((uint32_t)next)) next+=step;
        if (next>=0 && next<=11) *draft=(uint32_t)next;
        if (z7_pn_ae_sixths[*draft]>=12u && z7_pn_ae_draft_count>=7u) z7_pn_ae_draft_count=6u;
    } else {
        if (step>0 && *draft<maximum) ++*draft;
        if (step<0 && *draft) --*draft;
        if (z7_settings_view==16u && z7_pn_ae_sixths[z7_pn_ae_draft_step]>=12u && *draft>=7u) *draft=6u;
    }
    sm_render(0xa1833548u);sm_redraw_request();return 0;
}
static uint32_t sm_pn_interval_up(void) { return sm_pn_interval_change(1); }
static uint32_t sm_pn_interval_down(void) { return sm_pn_interval_change(-1); }
#endif
static uint32_t sm_action(uint32_t object)
{
    if (!sm_owned(object) || !z7_settings_valid(&z7_menu_settings)) return 0;
    uint32_t row = *(volatile uint16_t *)(uintptr_t)(object + 22) + *(volatile uint16_t *)(uintptr_t)(object + 24);
#ifdef Z7_LCD_FIRST_RELEASE
    row = z7_lcd_release_row(z7_settings_view,row);
#endif
#ifdef Z7_SHUTTER_SOUND_MENU
    /* Sound level is not a display setting: own file, no display journal edit. */
#ifdef Z7_PIXEL_MENU
#ifdef Z7_PIXEL_NIKON_MENU
    if (z7_settings_view>=7u && z7_settings_view<=17u) {
        if (z7_settings_view==7u && row==6u && z7_pn_photo_origin) return sm_back(object);
        uint32_t previous_view=z7_settings_view,view=previous_view;
        uint32_t focus=z7_pn_action(&view,row);
        z7_settings_view=view;
        ++z7_settings_actions;sm_render(object);
        sm_focus(object,view==7u || view==5u || (view==13u && previous_view==13u) || (view==15u && previous_view>=15u) ? focus : z7_pn_entry_row(view));
        sm_redraw_request();return 0;
    }
#else
    if (z7_settings_view == 7) {
        if (row == 0) z7_pm_next_count();
        else if (row == 1) z7_pm_arm();
        else if (row == 6) z7_settings_view = 5;
        ++z7_settings_actions;
        sm_render(object);
        if (z7_settings_view == 5) sm_focus(object, 2);
        sm_redraw_request(); return 0;
    }
#endif
    if (z7_settings_view == 5 && row == 2) {
        z7_settings_view = 7;
        ++z7_settings_actions;
        sm_render(object); sm_focus(object, 0);
        sm_redraw_request(); return 0;
    }
#endif
#ifdef Z7_AF_BUTTONS_MENU
    if (z7_settings_view == 6) {
        if (row < AB_ROWS) z7_ab_menu_next(row);
        else if (row == 6) z7_settings_view = 5;
        ++z7_settings_actions;
        sm_render(object);
        if (z7_settings_view == 5) sm_focus(object, 2);
        sm_redraw_request();
        return 0;
    }
    if (z7_settings_view == 5 && row == 2) {
        z7_settings_view = 6;
        ++z7_settings_actions;
        sm_render(object); sm_focus(object, 0);
        sm_redraw_request();
        return 0;
    }
#endif
#ifdef Z7_SOUND_FOLDER
    if (z7_settings_view == 5) {
        if (row == 0) z7_sl_menu_next();
        else if (row == 1) z7_sf_menu_next();
        else if (row == 6) z7_settings_view = 0;
        ++z7_settings_actions;
        sm_render(object);
        if (!z7_settings_view) sm_focus(object, 6);
        sm_redraw_request();
        return 0;
    }
    if (!z7_settings_view && row == 7) {
        z7_settings_view = 5;
        ++z7_settings_actions;
        sm_render(object); sm_focus(object, 0);
        sm_redraw_request();
        return 0;
    }
#endif
    if (!z7_settings_view && row == 7) {
        z7_sl_menu_next();
        ++z7_settings_actions;
        sm_render(object);
        sm_redraw_request();
        return 0;
    }
#endif
    if (row >= 7 || z7_settings_preset >= 4) return 0;
    uint32_t view = z7_settings_view, p = z7_settings_preset;
#ifdef Z7_SETTINGS_PERSISTENCE
    struct z7_display_settings staged = z7_menu_settings;
#define SM_MODEL staged
#else
#define SM_MODEL z7_menu_settings
#endif
    if (!view) {
        if (row == 0) z7_settings_flag(&SM_MODEL, 0, !(SM_MODEL.flags & 1));
        else if (row < 5) { z7_settings_preset = row - 1; z7_settings_view = 1; }
        else if (row == 5) z7_settings_page(&SM_MODEL, 4, !(SM_MODEL.enabled_pages & 16));
        else z7_settings_flag(&SM_MODEL, 1, !(SM_MODEL.flags & 2));
    } else if (view == 1) {
        if (!row) z7_settings_page(&SM_MODEL, p, !(SM_MODEL.enabled_pages & (1u << p)));
        else if (row == 1) z7_settings_view = 2;
#ifdef Z7_HIGHLIGHT_PREFERENCES
        else if (row == 5) z7_settings_view = 4;
#endif
        else if (row < 6) z7_settings_component(&SM_MODEL, p, row - 2, !(SM_MODEL.components[p] & (1u << (row - 2))));
        else z7_settings_reset(&SM_MODEL, p);
    } else if (view == 2) {
        if (row < 6) z7_settings_information(&SM_MODEL, p, row, !(SM_MODEL.information[p] & (1u << row)));
        else z7_settings_view = 3;
    } else if (view == 3) {
        if (row < 2) z7_settings_information(&SM_MODEL, p, row + 6, !(SM_MODEL.information[p] & (1u << (row + 6))));
        else if (row == 6) z7_settings_view = 2;
#ifdef Z7_HIGHLIGHT_PREFERENCES
    } else if (view == 4) {
        if (!row) z7_settings_component(&SM_MODEL, p, 3, !(SM_MODEL.components[p] & Z7_COMPONENT_HIGHLIGHTS));
        else if (row == 1) z7_settings_highlights(&SM_MODEL, (SM_MODEL.highlight_pattern + 1) % 3, SM_MODEL.highlight_threshold);
        else if (row == 2) z7_settings_highlights(&SM_MODEL, SM_MODEL.highlight_pattern, (SM_MODEL.highlight_threshold + 1) % 8);
        else if (row == 6) z7_settings_view = 1;
#endif
    }
#ifdef Z7_SETTINGS_PERSISTENCE
    persistence_commit(&staged);
#elif defined(Z7_LCD_FIRST_RELEASE)
    (void)z7_lcd_release_filter(&z7_menu_settings);
#endif
#undef SM_MODEL
    ++z7_settings_actions;
    z7_battery_enabled = !!(z7_menu_settings.flags & Z7_SETTINGS_BATTERY);
    sm_render(object);
    if (view != z7_settings_view) sm_focus(object,
#ifdef Z7_HIGHLIGHT_PREFERENCES
        view == 4 ? 5 :
#endif
        0);
    sm_redraw_request();
    return 0;
}
static uint32_t sm_render(uint32_t object)
{
    if (!sm_owned(object) || (z7_settings_view >
#ifdef Z7_HIGHLIGHT_PREFERENCES
        4
#else
        3
#endif
#ifdef Z7_SOUND_FOLDER
        && z7_settings_view != 5
#endif
#ifdef Z7_AF_BUTTONS_MENU
        && z7_settings_view != 6
#endif
#ifdef Z7_PIXEL_MENU
#ifdef Z7_PIXEL_NIKON_MENU
        && !(z7_settings_view>=7u && z7_settings_view<=17u)
#else
        && z7_settings_view != 7
#endif
#endif
        ) || z7_settings_preset >= 4 || !sm_label_ownership()) return 0;
    static const char *const roots[7] = {"Custom pages", "Standard", "Minimal", "Composition", "Exposure", "Information display", "Battery percentage"};
    static const char *const preset[7] = {"Page enabled", "Shooting information", "Framing grid", "Histogram", "Virtual horizon", "Photo highlights", "Reset preset"};
    static const char *const info[7] = {"Shutter speed", "Aperture", "ISO sensitivity", "Shooting mode", "Release mode", "Focus information", "More information"};
    static const char *const extra[7] = {"Other information", "Focal length", "", "", "", "", "Back"};
#ifdef Z7_HIGHLIGHT_PREFERENCES
    static const char *const highlights[7] = {"Show on this page", "Pattern (all pages)", "Threshold (all pages)", "", "", "", "Back"};
    static const char *const patterns[3] = {"OFF", "Type 1", "Type 2"};
    static const char *const thresholds[8] = {"255", "248", "235", "224", "213", "202", "191", "180"};
    const char *const *names = z7_settings_view == 4 ? highlights :
        !z7_settings_view ? roots : z7_settings_view == 1 ? preset : z7_settings_view == 2 ? info : extra;
#else
    const char *const *names = !z7_settings_view ? roots : z7_settings_view == 1 ? preset : z7_settings_view == 2 ? info : extra;
#endif
    const char *title = !z7_settings_view ? "Display settings" : z7_settings_view == 1 ? roots[z7_settings_preset + 1] : "Shooting information";
#ifdef Z7_SOUND_FOLDER
#ifdef Z7_PIXEL_MENU
    static const char *const sound_rows[7] = {"Shutter volume", "Shutter sound", "Pixel shift", "", "", "", "Back"};
    static const char *const pixel_rows[7] = {"Frames", "Arm series", "Status", "", "", "", "Back"};
    if (z7_settings_view == 5) { names = sound_rows; title = "Extras"; }
    if (z7_settings_view == 7) { names = pixel_rows; title = "Pixel shift"; }
#elif defined(Z7_AF_BUTTONS_MENU)
    static const char *const sound_rows[7] = {"Shutter volume", "Shutter sound", "AF-area buttons", "", "", "", "Back"};
    static const char *const af_rows[7] = {"Fn1 button", "Fn2 button", "AF-ON button", "Sub-selector center", "Movie-record button", "", "Back"};
    if (z7_settings_view == 5) { names = sound_rows; title = "Extras"; }
    if (z7_settings_view == 6) { names = af_rows; title = "AF-area buttons"; }
#else
    static const char *const sound_rows[7] = {"Volume", "Sound", "", "", "", "", "Back"};
    if (z7_settings_view == 5) { names = sound_rows; title = "Shutter sound"; }
#endif
#endif
#ifdef Z7_HIGHLIGHT_PREFERENCES
    if (z7_settings_view == 4) title = "Photo highlights";
#endif
#ifdef Z7_SETTINGS_PERSISTENCE
    uint32_t save_status = persistence_display_status();
#ifdef Z7_PIXEL_MENU
#ifdef Z7_PIXEL_NIKON_MENU
    if (z7_settings_view>=5u) title=z7_settings_view>=7u ? z7_pn_title(z7_settings_view) : "Extras"; else
#else
    if (z7_settings_view >= 5) title = z7_settings_view == 7 ? "Pixel shift" : "Extras"; else
#endif
#elif defined(Z7_AF_BUTTONS_MENU)
    if (z7_settings_view >= 5) title = z7_settings_view == 6 ? "AF-area buttons" : "Extras"; else  /* own files */
#elif defined(Z7_SOUND_FOLDER)
    if (z7_settings_view == 5) title = "Shutter sound"; else  /* not a display setting: no save status */
#endif
    title = sm_persistent_title(!z7_settings_view ? "Display" :
#ifdef Z7_HIGHLIGHT_PREFERENCES
        z7_settings_view == 4 ? "Highlights" :
#endif
        z7_settings_view == 1 ? title : "Information", save_status);
#endif
    sm_text_put(230, title);
#ifdef Z7_SETTINGS_PERSISTENCE
    __atomic_store_n(&sm_save_status, save_status, __ATOMIC_RELEASE);
#endif
#ifdef Z7_LCD_FIRST_RELEASE
    for (uint32_t physical_row = 0; physical_row < 7; ++physical_row) {
        uint32_t row = physical_row;
        row = z7_lcd_release_row(z7_settings_view,physical_row);
        if (row==UINT32_MAX) {
            sm_text_put(231+physical_row,"");sm_text_put(238+physical_row,"");
            continue;
        }
#ifdef Z7_SHUTTER_SOUND_MENU
        if (!z7_settings_view && row==7) {
#if defined(Z7_AF_BUTTONS_MENU) || defined(Z7_PIXEL_MENU)
            sm_text_put(231+physical_row,"Extras");sm_text_put(238+physical_row,"");
#else
            sm_text_put(231+physical_row,"Shutter sound");sm_text_put(238+physical_row,z7_sl_value_text());
#endif
            continue;
        }
#ifdef Z7_PIXEL_MENU
#ifdef Z7_PIXEL_NIKON_MENU
        if (z7_settings_view>=7u && z7_settings_view<=17u) {
            sm_text_put(231+physical_row,z7_pn_label(z7_settings_view,row));
            sm_text_put(238+physical_row,z7_pn_value(z7_settings_view,row));
            continue;
        }
#endif
        if (z7_settings_view==7) {
            sm_text_put(231+physical_row,names[row]);
            sm_text_put(238+physical_row,row==0 ? z7_pm_count_text() : row==1 ?
                (z7_pm_requested || z7_pm_running ? "Cancel" : "OK") : row==2 ? z7_pm_status() : "");
            continue;
        }
#endif
#ifdef Z7_AF_BUTTONS_MENU
        if (z7_settings_view==6) {
            sm_text_put(231+physical_row,names[row]);
            sm_text_put(238+physical_row,row<AB_ROWS ? z7_ab_value_text(row) : "");
            continue;
        }
#endif
#ifdef Z7_SOUND_FOLDER
        if (z7_settings_view==5) {
            sm_text_put(231+physical_row,names[row]);
            sm_text_put(238+physical_row,row==0 ? z7_sl_value_text() : row==1 ? z7_sf_value_text() : "");
            continue;
        }
#endif
#endif
#else
    for (uint32_t row = 0; row < 7; ++row) {
#endif
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
#ifdef Z7_HIGHLIGHT_PREFERENCES
        else if (z7_settings_view == 4) {
            if (!row) { bits = z7_menu_settings.components[z7_settings_preset]; mask = Z7_COMPONENT_HIGHLIGHTS; }
            else if (row == 1) value = patterns[z7_menu_settings.highlight_pattern];
            else if (row == 2) value = thresholds[z7_menu_settings.highlight_threshold];
        }
#endif
        if (mask) value = bits & mask ? "ON" : "OFF";
        if (!names[row][0] || (z7_settings_view && row == 6 && z7_settings_view != 2)) value = "";
#ifdef Z7_LCD_FIRST_RELEASE
        sm_text_put(231 + physical_row, names[row]); sm_text_put(238 + physical_row, value);
#else
        sm_text_put(231 + row, names[row]); sm_text_put(238 + row, value);
#endif
    }
#ifdef Z7_LCD_FIRST_RELEASE
    uint32_t rows = z7_lcd_release_rows(z7_settings_view);
    /* Keep seven native widget slots allocated as subviews grow/shrink.
     * Low halfword is selectable item count; high halfword is viewport capacity. */
    if (sm_lcd_rows_ready) sm_meta[5] = rows | (7u << 16);
#endif
    /* Keep the current event's destination stable across its callback. */
    for (uint32_t i = 0; i < 14; ++i) if (sm_events[i][0] == 0x238 || sm_events[i][0] == 0x253) {
        sm_events[i][1] = (uint32_t)(uintptr_t)sm_back_event;
        sm_events[i][3] = 0x3a0;
    }
#ifdef Z7_PIXEL_NIKON_MENU
    for (uint32_t i=0;i<14;++i) {
        uint32_t event=sm_events[i][0];
        if (event==0x236u || event==0x250u) {
            sm_events[i][1]=(z7_settings_view==11u || z7_settings_view==16u || z7_settings_view==17u) ? (uint32_t)(uintptr_t)sm_pn_interval_up : 0x10404f6fu;
        } else if (event==0x237u || event==0x251u) {
            sm_events[i][1]=(z7_settings_view==11u || z7_settings_view==16u || z7_settings_view==17u) ? (uint32_t)(uintptr_t)sm_pn_interval_down : 0x10404f7bu;
        } else continue;
        /* Numeric editor owns held-key repeats too, without a second native
         * cursor move. Other pages retain their original wheel/hold guard. */
        sm_events[i][2]=z7_settings_view==11u || z7_settings_view==16u || z7_settings_view==17u || event<0x250u ? 0u : 0x10405009u;
    }
#endif
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
#ifdef Z7_SETTINGS_PERSISTENCE
/* Native menu state1 handles queued key/input notifications on the menu task.
 * Delegate the complete native event FIRST. Only the owned, focused page may
 * then refresh its title. There are no synthetic keys or borrowed timer slots.
 */
static uint32_t sm_menu_dispatch(uint32_t event, uint32_t data)
{
    ++z7_menu_status_events;
    uint32_t result = F(0x1048bffdu, uint32_t, uint32_t, uint32_t)(event, data);
    if (W(0xa182ed34u) != (uint32_t)(uintptr_t)sm_menu_dispatch ||
        B(0xa182ed2cu) != 1 || !sm_owned(0xa1833548u) ||
        F(0x104061edu, uint32_t)() != 0xa1833548u ||
        !W(0xa1833548u + 12) || !sm_label_ownership()) return result;
    if (persistence_display_status() != __atomic_load_n(&sm_save_status, __ATOMIC_ACQUIRE)) {
        sm_render(0xa1833548u);
        sm_redraw_request();
        ++z7_menu_status_paints;
    }
    return result;
}
static uint32_t sm_menu_visible(void)
{
    uint32_t pages = W(0xa181f91cu);
    if (!ram(pages, 16)) return 0;
    uint32_t stride = W(pages), count = W(pages + 8), data = W(pages + 12);
    if (stride < 4 || stride > 1024 || stride % 4 || !count || count > 20 ||
        count > W(pages + 4) || !ram(data, count * stride)) return 0;
    return W(data + (count - 1) * stride) == 0xa1833548u;
}
static void persistence_menu_notify(void)
{
    /* The original event-flag setter wakes the native menu wait loop. Bit2
     * polls its existing input queue; an empty queue is handled natively. No
     * input is enqueued or synthesized and no widget/label is touched here.
     */
    if (W(0xa182ed34u) == (uint32_t)(uintptr_t)sm_menu_dispatch &&
        B(0xa182ed2cu) == 1 && sm_owned(0xa1833548u) && sm_menu_visible() &&
        persistence_display_status() != __atomic_load_n(&sm_save_status, __ATOMIC_ACQUIRE) &&
        W(0xa181f910u)) {
        ++z7_menu_status_notifications;
        F(0x104064cdu, void, uint32_t, uint32_t)(0xa181f910u, 2);
    }
}
#endif
static uint32_t sm_prepare(void)
{
#ifdef Z7_PIXEL_NIKON_MENU
    if (!z7_pn_photo_prepare()) return 0;
#endif
#ifdef Z7_SETTINGS_ROOT_ENTRY
    if (!sm_root_prepare()) return 0;
#endif
#ifdef Z7_SETTINGS_PERSISTENCE
    if (W(0xa182ed34u) != 0x1048bffdu) return 0;
#endif
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
#ifdef Z7_PIXEL_NIKON_MENU
        sm_labels[row][2]=600;sm_values[row][0]=610;
#endif
    }
    sm_geometry[0] = 7; sm_geometry[1] = (uint32_t)(uintptr_t)sm_boxes; sm_geometry[2] = (uint32_t)(uintptr_t)sm_labels; sm_geometry[3] = (uint32_t)(uintptr_t)sm_values;
    for (uint32_t i = 0; i < 7; ++i) sm_meta[i] = meta[i];
    sm_meta[1] = (uint32_t)(uintptr_t)sm_geometry; sm_meta[2] = (uint32_t)(uintptr_t)sm_layout; sm_meta[3] = (uint32_t)(uintptr_t)sm_controls;
    sm_meta[4] = (uint32_t)(uintptr_t)sm_maps; sm_meta[5] = 0x00070007;
#ifdef Z7_LCD_FIRST_RELEASE
    sm_lcd_prepare_rows();
#endif
    sm_callbacks[0] = (uint32_t)(uintptr_t)sm_render; sm_callbacks[1] = (uint32_t)(uintptr_t)sm_zero;
    sm_callbacks[2] = 0x1040525f; sm_callbacks[3] = (uint32_t)(uintptr_t)sm_one;
    sm_callbacks[4] = sm_callbacks[5] = sm_callbacks[6] = (uint32_t)(uintptr_t)sm_zero; sm_callbacks[7] = 0x1040525f;
    sm_object[0] = 2; sm_object[1] = leaf[1]; sm_object[4] = (uint32_t)(uintptr_t)sm_callbacks; sm_object[10] = (uint32_t)(uintptr_t)sm_meta;
    z7_settings_defaults(&z7_menu_settings);
#if defined(Z7_LCD_FIRST_RELEASE) && !defined(Z7_SETTINGS_PERSISTENCE)
    if (!z7_lcd_release_filter(&z7_menu_settings)) return 0;
#endif
    z7_battery_enabled = 0;
    return 1;
}
static void sm_publish(void)
{
#ifdef Z7_PIXEL_NIKON_MENU
    z7_pn_photo_publish();
#endif
#ifdef Z7_SETTINGS_ROOT_ENTRY
    sm_root_publish();
#endif
    for (uint32_t i = 1; i < 11; ++i) W(0xa1833548u + i * 4) = sm_object[i];
    __asm__ volatile("dmb sy" ::: "memory");
    W(0xa1833548u) = sm_object[0];
#ifdef Z7_SETTINGS_PERSISTENCE
    __asm__ volatile("dmb sy" ::: "memory");
    W(0xa182ed34u) = (uint32_t)(uintptr_t)sm_menu_dispatch;
#endif
}
static void sm_before(void)
{
    before();
    if (!sm_owned(0xa1833548u) || !W(0xa1833548u + 12)) {
#ifdef Z7_LCD_FIRST_RELEASE
        sm_lcd_prepare_rows();
#endif
        return;
    }
    uint32_t pages = W(0xa181f91cu);
    if (!ram(pages, 16)) return;
    uint32_t stride = W(pages), count = W(pages + 8), data = W(pages + 12), active = 0;
    if (stride < 4 || stride > 1024 || count > 20 || count > W(pages + 4) || !ram(data, count * stride)) return;
    for (uint32_t i = 0; i < count; ++i) if (W(data + i * stride) == 0xa1833548u) active = 1;
    if (!active) {
#ifdef Z7_LCD_FIRST_RELEASE
        sm_lcd_prepare_rows();
#endif
        return;
    }
#ifdef Z7_LCD_FIRST_RELEASE
    if (!sm_lcd_rows_ready) {
        sm_lcd_rows_ready = 1;
        sm_render(0xa1833548u);
    }
#endif
    uint32_t header = F(0x103faebfu, uint32_t, uint32_t, uint32_t)(0x203, W(0xa1833548u + 12));
    uint32_t changed = 0;
#ifdef Z7_SETTINGS_PERSISTENCE
    /* Native menu/paint paths update text. The worker publishes scalar state
     * and requests a native event-flag wake; it never edits labels or paints.
     */
    changed = persistence_display_status() != sm_save_status;
#endif
    if (ram(header, 100) && (changed || W(header + 8) != 230 || W(header + 12) != 2)) sm_render(0xa1833548u);
}
