/* SPDX-License-Identifier: MIT. Independent original-Z7 C3.80 emulator API. */
#ifndef Z7_CACHED_FRAME_PERMISSION_H
#define Z7_CACHED_FRAME_PERMISSION_H
#include "frame_permission.h"
/* Additive60-byte API for native cached primary application1023D794.
 * fields is frame metadata beginning at its native +4 substructure, or NULL
 * for a cached-state gate refresh. NULL supplies no new original frame input.
 * Decision0 preserves,1 enables,2 inhibits; invalid/nonboolean inputs delegate.
 * Init-only resident Thumb callback. Same no-block/no-mutation rules as API56.
 * Neither interface serializes native parameter copying or pins allocations.
 */
struct z7_module_cached_frame_api {
    struct z7_module_frame_permission_api frame;
    uint32_t (*register_cached_frame_permission)(z7_frame_permission_callback callback);
};
#endif
