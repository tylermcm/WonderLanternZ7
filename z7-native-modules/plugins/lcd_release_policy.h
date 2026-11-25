/* SPDX-License-Identifier: MIT. Independent original-Z7 LCD release scope. */
#ifndef Z7_LCD_RELEASE_POLICY_H
#define Z7_LCD_RELEASE_POLICY_H
#include "display_settings.h"
/* Keep the existing journal format; remove unsupported choices on load/edit.
 * A legacy information-only configuration falls back to Standard. */
static inline uint32_t z7_lcd_release_filter(struct z7_display_settings *s)
{
    if (!z7_settings_valid(s)) return 0;
#ifdef Z7_LCD_INFORMATION_PAGE
    s->enabled_pages &= 31u;
#else
    s->enabled_pages &= 15u;
#endif
    if (!s->enabled_pages) s->enabled_pages = 1;
    for (uint32_t i=0;i<4;++i) s->components[i] &= Z7_COMPONENT_GRID | Z7_COMPONENT_HORIZON
#ifdef Z7_LCD_HISTOGRAM_PRESETS
        | Z7_COMPONENT_HISTOGRAM
#endif
        ;
    return 1;
}
static inline uint32_t z7_lcd_release_rows(uint32_t view)
{
    static const uint8_t count[]={
#ifdef Z7_LCD_INFORMATION_PAGE
        7,
#else
        6,
#endif
#ifdef Z7_LCD_HISTOGRAM_PRESETS
        6,
#else
        5,
#endif
        7,3};
    return view<4 ? count[view] : 0;
}
/* Physical compact-menu row -> existing settings action/label index. */
static inline uint32_t z7_lcd_release_row(uint32_t view,uint32_t row)
{
    static const uint8_t map[4][7]={
#ifdef Z7_LCD_INFORMATION_PAGE
                                 {0,1,2,3,4,5,6},
#else
                                 {0,1,2,3,4,6,255},
#endif
#ifdef Z7_LCD_HISTOGRAM_PRESETS
                                 {0,1,2,3,4,6,255},
#else
                                 {0,1,2,4,6,255,255},
#endif
                                 {0,1,2,3,4,5,6},{0,1,6,255,255,255,255}};
    return view<4 && row<z7_lcd_release_rows(view) ? map[view][row] : UINT32_MAX;
}
#endif
