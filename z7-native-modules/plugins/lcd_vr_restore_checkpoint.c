/* SPDX-License-Identifier: MIT. Everyday LCD module (sound folder, EXIF fix,
 * upside-down playback; camera-verified 8dcee0e0) plus the VR ONE-MOVE test
 * with the D2 RESTORE (pixel-shift step 2b, plugins/vr_move_test.h): once per
 * boot, one tiny 0xF1F1 move and back, then Nikon's own D2 parameters re-sent
 * so stabilisation leaves the hold without a power cycle.
 */
#define Z7_VR_MOVE 1
#define Z7_VR_RESTORE 1
#include "lcd_folder_playback_checkpoint.c"
