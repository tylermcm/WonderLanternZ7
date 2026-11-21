/* SPDX-License-Identifier: MIT. Independent original-Z7 diagnostic API72. */
#ifndef Z7_NATIVE_WARNING_TRANSACTION_H
#define Z7_NATIVE_WARNING_TRANSACTION_H
#include "owned_frame_coordination.h"
struct z7_module_native_warning_api {
    struct z7_module_owned_frame_api owned;
    uint32_t (*enable_native_warning_transactions)(void); /* Init-only. */
    /* Foreign admission covers aligned camera-RAM descriptors for the two
     * highlight commands with matching selector and sampled service1..4.
     * Other requests keep native dispatch; state/task lifetime is not pinned.
     */
    /* False requests owned-feature shutdown; native transactions keep running.
     * Callbacks must be bounded, may call the native gate, and must NOT submit
     * a synchronous nested parameter request while their transaction is held.
     * Foreign completion callbacks run after their transaction has retired.
     */
    uint32_t (*owned_warning_available)(void);
};
#endif
