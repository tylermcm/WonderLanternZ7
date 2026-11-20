/* SPDX-License-Identifier: MIT. Independent original-Z7 C 3.80 research. */
#ifndef Z7_UPDATE_H
#define Z7_UPDATE_H
#include "module.h"

/* Optional tail extension: existing API fields and display-hook layout retain
 * their offsets. Runs on the native widget-computation path, before its initial
 * snapshot comparison. Registration is init-only and published on success.
 * This callback must return promptly and must not draw or recurse into updates.
 */
struct z7_module_update_api {
    struct z7_module_api base;
    uint32_t (*register_before_update)(void (*callback)(void));
};
#endif
