/* SPDX-License-Identifier: MIT. Everyday LCD module (sound folder, EXIF fix,
 * upside-down playback; camera-verified 8dcee0e0) plus the first real
 * PIXEL-SHIFT SERIES for the Z7 (plugins/pixel_series_test.h, Z7_PIXEL_SHIFT_V1):
 * four module-fired frames at the Bayer corners with the calibrated Z7 steps
 * (x 20, y 18 per pixel), settle delays, one click each, then recentre and
 * Nikon's D2 apply restore.
 */
#define Z7_VR_MOVE 1
#define Z7_VR_RESTORE 1
#define Z7_PIXEL_SERIES 1
#define Z7_PIXEL_RELEASE 1
#define Z7_PIXEL_SHIFT_V1 1
#include "lcd_folder_playback_checkpoint.c"
