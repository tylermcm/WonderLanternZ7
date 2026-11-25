/* SPDX-License-Identifier: MIT. Independent original-Z7 display preferences.
 * Page/component concepts follow the pinned JKWTCN MIT custom-DISP feature.
 * This model contains no camera addresses or filesystem operations.
 */
#ifndef Z7_DISPLAY_SETTINGS_H
#define Z7_DISPLAY_SETTINGS_H
#include <stdint.h>
#if defined(Z7_GRID_LAYOUT_PREFERENCES) && defined(Z7_HIGHLIGHT_PREFERENCES) && !defined(Z7_COMBINED_DISPLAY_PREFERENCES)
#error Grid layout v3 and highlight v2 are separate preference profiles
#endif
#define Z7_SETTINGS_BYTES 64u
#define Z7_SETTINGS_INVALID 0xffffffffu
#define Z7_SETTINGS_CUSTOM 1u
#define Z7_SETTINGS_BATTERY 2u
#define Z7_COMPONENT_GRID 1u
#define Z7_COMPONENT_HISTOGRAM 2u
#define Z7_COMPONENT_HORIZON 4u
#define Z7_COMPONENT_HIGHLIGHTS 8u
#define Z7_INFO_SHUTTER 1u
#define Z7_INFO_APERTURE 2u
#define Z7_INFO_ISO 4u
#define Z7_INFO_SHOOTING 8u
#define Z7_INFO_RELEASE 16u
#define Z7_INFO_FOCUS 32u
#define Z7_INFO_OTHER 64u
#define Z7_INFO_FOCAL 128u
struct z7_display_settings {
    uint32_t flags, enabled_pages, components[4], information[4];
#ifdef Z7_GRID_LAYOUT_PREFERENCES
    uint32_t grid_layout;
#endif
#ifdef Z7_HIGHLIGHT_PREFERENCES
    uint32_t highlight_pattern, highlight_threshold;
#endif
};
void z7_settings_defaults(struct z7_display_settings *);
uint32_t z7_settings_valid(const struct z7_display_settings *);
uint32_t z7_settings_encode(const struct z7_display_settings *, uint8_t *, uint32_t);
uint32_t z7_settings_decode(const uint8_t *, uint32_t, struct z7_display_settings *);
uint32_t z7_settings_page(struct z7_display_settings *, uint32_t, uint32_t);
uint32_t z7_settings_reset(struct z7_display_settings *, uint32_t);
uint32_t z7_settings_next(const struct z7_display_settings *, uint32_t);
uint32_t z7_settings_information(struct z7_display_settings *, uint32_t, uint32_t, uint32_t);
uint32_t z7_settings_component(struct z7_display_settings *, uint32_t, uint32_t, uint32_t);
uint32_t z7_settings_flag(struct z7_display_settings *, uint32_t, uint32_t);
#ifdef Z7_HIGHLIGHT_PREFERENCES
uint32_t z7_settings_highlights(struct z7_display_settings *, uint32_t pattern, uint32_t threshold);
#endif
#endif
