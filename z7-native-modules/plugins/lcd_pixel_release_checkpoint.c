/* SPDX-License-Identifier: MIT. Everyday LCD module (sound folder, EXIF fix,
 * upside-down playback; camera-verified 8dcee0e0) plus the MODULE-FIRED
 * PIXEL-SHIFT SERIES (plugins/pixel_series_test.h, Z7_PIXEL_RELEASE): after
 * arming, the module holds each Bayer position and fires Nikon's own release
 * itself, four frames, then recentres and restores stabilisation.
 */
#define Z7_VR_MOVE 1
#define Z7_VR_RESTORE 1
#define Z7_PIXEL_SERIES 1
#define Z7_PIXEL_RELEASE 1
#include "lcd_folder_playback_checkpoint.c"
