/* SPDX-License-Identifier: MIT. Independent original-Z7 experimental API88. */
#ifndef Z7_NAVIGATION_API_H
#define Z7_NAVIGATION_API_H
#include "graphics.h"
typedef uint32_t (*z7_navigation_callback)(uint32_t direction,uint32_t *result);
struct z7_module_navigation_api {
    struct z7_module_graphics_api graphics;
    /* Init-only, committed resident code. Return1 after synchronous handling
     * and write *result, or0 without native state changes to use stock. Invalid
     * results delegate. Callback owns page/output/layout/task admission. */
    uint32_t (*register_navigation)(z7_navigation_callback callback);
};
#endif
