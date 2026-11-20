/* SPDX-License-Identifier: MIT. Independent original-Z7 C3.80 emulator API. */
#ifndef Z7_PARAMETERS_H
#define Z7_PARAMETERS_H
#include "highlight.h"
/* Optional52-byte prefix. Init-only resident callback, after highlight hooks
 * have registered. Called before ORIGINAL native dispatch for foreign native
 * highlight commands42060007/42062007 only, matching selector, service1..4,
 * aligned RAM descriptor/payload104 and enable0/1. A writable payload is exposed
 * ONLY for property138D==0/service3..4. Otherwise payload100 is NULL: a native
 * update notice for invalidating prior ownership, with no caller memory exposed.
 * A notice must not change warning parameters. Track it even if incoming bytes
 * would equal the extension's last parameters; equality alone is not ownership.
 * Owned registered descriptor never enters this callback. All other packets
 * remain native. Callback may convert the100 payload bytes synchronously; do
 * not change descriptor/source/callback/ack, retain caller memory, wait, paint,
 * access files or dispatch recursively. No after callback can safely restore
 * caller memory: original completion may wake and release its stack first.
 * Reentry delegates unchanged. This API does not supply UI/preset eligibility,
 * converter policy, ownership/restoration or physical frame synchronization.
 */
struct z7_module_parameters_api {
    struct z7_module_highlight_api highlight;
    uint32_t (*register_parameters)(void (*callback)(uint32_t command, void *payload100));
};
#endif
