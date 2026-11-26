/* SPDX-License-Identifier: MIT. LCD module with shutter sound, volume OFF/1-9.
 * Same as lcd_shutter_sound_checkpoint.c (92602a4a, camera-verified) plus levels
 * 8 (x2.83) and 9 (x4), which the sound lab found still clean on the camera.
 * The driver tone stays fixed at 31 (values above 31 are unsafe).
 */
#define Z7_SOUND_MENU_LEVELS 9u
#include "lcd_shutter_sound_checkpoint.c"
