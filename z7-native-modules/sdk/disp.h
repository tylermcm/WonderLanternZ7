/* SPDX-License-Identifier: MIT. Independent original-Z7 C 3.80 research. */
#ifndef Z7_DISP_H
#define Z7_DISP_H
#include "update.h"
/* Additive tail: called only when the native shooting DISP handler reaches its
 * page-cycle function, after its original admission gates. Return 0 to delegate
 * to that original function, 0x100 for a consumed normal GUI update, or 2 for an
 * already-performed native app transition. All other results delegate.
 */
struct z7_module_disp_api {
    struct z7_module_update_api update;
    uint32_t (*register_disp_cycle)(uint32_t (*callback)(void));
};
#endif
