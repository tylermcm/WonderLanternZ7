/* SPDX-License-Identifier: MIT. Everyday LCD module (sound folder, EXIF fix,
 * upside-down playback; camera-verified 8dcee0e0) plus the PIXEL-SHIFT SERIES
 * DRY RUN (plugins/pixel_series_test.h): the photographer takes four photos,
 * the module moves the sensor one Bayer step after each, then recentres and
 * restores Nikon's D2 stabilisation parameters.
 */
#define Z7_VR_MOVE 1
#define Z7_VR_RESTORE 1
#define Z7_PIXEL_SERIES 1
#include "lcd_folder_playback_checkpoint.c"
