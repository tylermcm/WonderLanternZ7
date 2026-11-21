/* SPDX-License-Identifier: MIT. Independent original-Z7 emulator research. */
#ifndef Z7_OWNED_FRAME_COORDINATION_H
#define Z7_OWNED_FRAME_COORDINATION_H
#include "cached_frame_permission.h"
/* Additive64-byte API. Init-only activation after all highlight callbacks.
 * Coordinates the two identified native primary frame bodies against ONLY
 * the registered module-owned parameter descriptor, through after-consumer.
 * Busy owned work is cancelled with normal completion and may be retried.
 * Foreign native parameter requests are NOT coordinated by this interface.
 * No native caller closure, allocation pin, physical scheduling or recovery
 * guarantee. Generation exhaustion refuses frame/owned admission; shutdown
 * handling is not provided in this diagnostic profile.
 */
struct z7_module_owned_frame_api {
    struct z7_module_cached_frame_api cached;
    uint32_t (*enable_owned_frame_coordination)(void);
};
#endif
