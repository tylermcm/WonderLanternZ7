/* SPDX-License-Identifier: MIT. Everyday LCD module (sound folder, EXIF fix,
 * upside-down playback; camera-verified 8dcee0e0) plus PIXEL-SHIFT SERIES V2
 * (plugins/pixel_series_test.h, Z7_PIXEL_SHIFT_V2): four module-fired frames
 * at the calibrated corners (x 20, y 18), a 7 s start settle, every frame
 * approached from 36 y-steps above, 0.5 s settle and re-check, one click each,
 * then recentre and Nikon's D2 apply restore.
 */
#define Z7_VR_MOVE 1
#define Z7_VR_RESTORE 1
#define Z7_PIXEL_SERIES 1
#define Z7_PIXEL_RELEASE 1
#define Z7_PIXEL_SHIFT_V1 1
#define Z7_PIXEL_SHIFT_V2 1
#include "lcd_folder_playback_checkpoint.c"
