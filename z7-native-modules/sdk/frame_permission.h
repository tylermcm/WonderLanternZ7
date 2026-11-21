/* SPDX-License-Identifier: MIT. Independent original-Z7 C3.80 emulator API. */
#ifndef Z7_FRAME_PERMISSION_H
#define Z7_FRAME_PERMISSION_H
#include "parameters.h"
/* Optional additive56-byte API. Init-only resident Thumb callback, called at
 * primary frame permission consumption, including forced deferred replay.
 * Decisions:0 preserve native,1 enable,2 inhibit; other values preserve native.
 * Native nonboolean permissions and unsupported pointers/kinds are delegated.
 * Never block, paint, use files/locks, mutate frame data or recursively apply.
 * The callback does not pin the native context or establish a physical fence.
 * It changes only the consumed permission, never caller/pending frame storage.
 */
typedef uint32_t (*z7_frame_permission_callback)(const void *frame, uint32_t native_permission);
struct z7_module_frame_permission_api {
    struct z7_module_parameters_api parameters;
    uint32_t (*register_frame_permission)(z7_frame_permission_callback callback);
};
#endif
