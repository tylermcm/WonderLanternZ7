/* SPDX-License-Identifier: MIT. Independent original-Z7 LCD save/restore trial.
 * Journal v1 persists display preferences; grid layout remains GUI-owned RAM.
 * Native grid storage receives only Off/On, matching the owner-tested profile.
 * Offline candidate only; requires a separate exact-candidate hardware review.
 */
#define Z7_GRID_VOLATILE_CHECKPOINT 1
#define Z7_GRID_LEGACY_LAYOUT_INPUT 1
#include "lcd_release.c"
