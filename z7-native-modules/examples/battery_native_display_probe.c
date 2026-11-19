/* SPDX-License-Identifier: MIT.
 * Native snapshot-to-HUD integration diagnostic. Phase control is supplied by
 * the emulator tool; the text value comes from the real Z7 snapshot getter.
 * This is not a finished automatically gated battery-display feature.
 */
#define Z7_BATTERY_USE_NATIVE_SAMPLE 1
#include "battery_display_probe.c"
