/* SPDX-License-Identifier: MIT. Independent original-Z7 startup comparison.
 * Avoid only a redundant initial grid-ON invalidation when claiming a preset.
 * Camera startup flash is not established fixed by this offline candidate.
 */
#define Z7_BASE_INITIAL_GRID_DELTA_ONLY 1
#include "lcd_persistence_checkpoint.c"
