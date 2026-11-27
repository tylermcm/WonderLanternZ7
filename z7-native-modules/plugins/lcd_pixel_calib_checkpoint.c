/* SPDX-License-Identifier: MIT. Everyday LCD module (sound folder, EXIF fix,
 * upside-down playback; camera-verified 8dcee0e0) plus the PIXEL-SHIFT
 * CALIBRATION RUN (plugins/pixel_series_test.h, Z7_PIXEL_CALIB): nine
 * module-fired frames at larger x/y steps with repeated references, then
 * Nikon's D2 apply restore (flags sel[1]|0x80, camera-verified d6e6db28).
 */
#define Z7_VR_MOVE 1
#define Z7_VR_RESTORE 1
#define Z7_PIXEL_SERIES 1
#define Z7_PIXEL_RELEASE 1
#define Z7_PIXEL_PROBE 1
#define Z7_PIXEL_CALIB 1
#include "lcd_folder_playback_checkpoint.c"
