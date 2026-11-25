/* SPDX-License-Identifier: MIT. Original-Z7 LCD module with shutter sound.
 * The installed 5e62 LCD configuration (settings label refresh, v3 display
 * journal) plus the shutter sound on capture event 0x0419000B in Silent
 * photography, with a Shutter sound volume row (OFF, 1-7) on the root settings
 * page and the level in its own A:\Z7SND.DAT (plugins/shutter_sound_lcd.h).
 */
#define Z7_SHUTTER_SOUND_MENU 1
#include "lcd_settings_label_checkpoint.c"
