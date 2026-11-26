/* SPDX-License-Identifier: MIT. Everyday LCD module (sound folder, EXIF fix,
 * upside-down playback; camera-verified 8dcee0e0) plus the PIXEL-SHIFT
 * GEOMETRY PROBE (plugins/pixel_series_test.h, Z7_PIXEL_PROBE): one
 * module-fired frame per position-command variant, then three ways to end the
 * hold, stopping at the first that works.
 */
#define Z7_VR_MOVE 1
#define Z7_VR_RESTORE 1
#define Z7_PIXEL_SERIES 1
#define Z7_PIXEL_RELEASE 1
#define Z7_PIXEL_PROBE 1
#include "lcd_folder_playback_checkpoint.c"
