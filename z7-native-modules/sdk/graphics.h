/* SPDX-License-Identifier: MIT. Independent original-Z7 experimental API84. */
#ifndef Z7_GRAPHICS_API_H
#define Z7_GRAPHICS_API_H
#include "native_cache.h"
struct z7_module_graphics_api {
    struct z7_module_native_cache_api cache;
    /* Staged during init; published only for a committed resident module.
     * Runs on native graphics dispatch. Return0 without changing/acknowledging
     * the message to use stock dispatch, or1 after complete synchronous handling.
     * The callback owns LCD/page/command admission and producer completion.
     * No hot unload, task exclusion or renderer lifetime guarantee is supplied.
     */
    uint32_t (*register_graphics)(uint32_t (*callback)(volatile uint32_t *message));
};
#endif
