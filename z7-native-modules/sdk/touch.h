/* SPDX-License-Identifier: MIT. Independent original-Z7 experimental API92. */
#ifndef Z7_TOUCH_API_H
#define Z7_TOUCH_API_H
#include "navigation.h"
typedef uint32_t (*z7_touch_callback)(const uint32_t *event,uint32_t *copy);
struct z7_module_touch_api {
    struct z7_module_navigation_api navigation;
    /* Init-only, resident callback. Return1 after writing a complete60-byte
     * replacement, or0 without touching caller data to retain stock input.
     * Host calls the original producer once and preserves its native result.
     * Copy is synchronous host storage; callback must not retain either pointer.
     * Callback owns page/output/layout/task admission. No hot unload. */
    uint32_t (*register_touch)(z7_touch_callback callback);
};
#endif
