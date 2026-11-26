/* SPDX-License-Identifier: MIT. Everyday LCD module (sound folder, EXIF fix,
 * upside-down playback; camera-verified 8dcee0e0) plus the VR ONE-MOVE TEST for
 * the pixel-shift port (plugins/vr_move_test.h): once per boot, one tiny
 * 0xF1F1 sensor move and back, only while stabilisation is active and settled.
 */
#define Z7_VR_MOVE 1
#include "lcd_folder_playback_checkpoint.c"
