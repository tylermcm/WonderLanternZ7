/* SPDX-License-Identifier: MIT. Independent original-Z7 experimental API80. */
#ifndef Z7_NATIVE_CACHE_H
#define Z7_NATIVE_CACHE_H
#include "native_warning_transaction.h"
struct z7_native_cache_snapshot {
    uint32_t request[9], serial, bank;
};
struct z7_module_native_cache_api {
    struct z7_module_native_warning_api warning;
    /* Output1 LCD /4 EVF. Failure leaves output unchanged. Only tracked,
     * completed photo-mode kind0 copies are admitted, in current photo mode.
     * Fixed native index mapping is a
     * profile contract; this neither pins banks nor excludes later writers.
     */
    uint32_t (*native_cache_snapshot)(uint32_t output, struct z7_native_cache_snapshot *out);
    uint32_t (*native_cache_snapshot_valid)(uint32_t output, const struct z7_native_cache_snapshot *snapshot);
};
_Static_assert(sizeof(struct z7_native_cache_snapshot) == 44, "Native cache snapshot layout");
#endif
