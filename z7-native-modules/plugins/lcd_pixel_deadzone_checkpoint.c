/* SPDX-License-Identifier: MIT. Everyday LCD module (sound folder, EXIF fix,
 * upside-down playback; camera-verified 8dcee0e0) plus the PIXEL-SHIFT Y
 * DEAD-ZONE RUN (plugins/pixel_series_test.h, Z7_PIXEL_DEADZONE): 20
 * module-fired frames of small y steps between references, an x control and
 * direction tests, with settles, then Nikon's D2 apply restore.
 */
#define Z7_VR_MOVE 1
#define Z7_VR_RESTORE 1
#define Z7_PIXEL_SERIES 1
#define Z7_PIXEL_RELEASE 1
#define Z7_PIXEL_PROBE 1
#define Z7_PIXEL_DEADZONE 1
#include "lcd_folder_playback_checkpoint.c"
