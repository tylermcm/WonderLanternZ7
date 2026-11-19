/* SPDX-License-Identifier: MIT; independent original-Z7 module interface. */
#ifndef Z7_MODULE_DISPLAY_H
#define Z7_MODULE_DISPLAY_H
#include <stdint.h>

#define Z7_DISPLAY_ABI 1u
/* Installed host hooks always retain stock behavior without a committed module.
 * All function pointers must refer to Thumb code inside the loading module's
 * image. Registration is allowed once, during initialization only. A failed
 * initializer publishes none of these callbacks.
 */
struct z7_display_hooks {
    uint32_t abi, size;
    const uint16_t *(*grid_source)(const uint16_t *native_table);
    void (*grid_geometry)(void *native_descriptor);
    uint32_t (*scalar_value)(uint32_t key, uint32_t native_value);
    uint32_t (*histogram_gate)(uint32_t native_state);
    void (*before_paint)(void);
    void (*after_paint)(void);
};
/* Native grid-page metadata/callbacks owned by the module. The host validates
 * and stages them during init, then publishes on the GUI paint path only while
 * the native grid page is inactive. No module pointer is published on failure.
 */
struct z7_grid_menu {
    uint32_t abi, size;
    const uint32_t *metadata;
    const uint32_t *callbacks;
};
#endif
