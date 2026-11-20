/* SPDX-License-Identifier: MIT. Independent original-Z7 C3.80 emulator API. */
#ifndef Z7_HIGHLIGHT_H
#define Z7_HIGHLIGHT_H
#include "worker.h"
/* Additive48-byte API, enabled only in an explicit highlight-host build.
 * Registration is init-only; every callback and the28-byte descriptor must
 * reside in the loading module. All callbacks are mandatory. No unload.
 * Source callbacks bracket native1034866E and must not block, paint, access
 * files, acquire UI/property locks or call source application recursively.
 * A source token is local to that invocation; after_source restores temporary
 * caller metadata. This does NOT cancel the native deferred frame copy.
 * Consumer callbacks run only for the registered descriptor address.
 * before_consumer:1 execute native;2 cancel via original completion;3 park.
 * Other values park. after_consumer runs after native return only for1/2.
 * Foreign descriptor addresses always execute native with no module callback.
 * Concurrent/reentrant source calls delegate; owned consumer reentry parks
 * during before_consumer/native dispatch. The host claim is released before
 * after_consumer publishes retirement so immediately submitted work can run.
 * The module must reject an old owned packet until retirement, and finish its
 * old-packet accesses before publishing reuse. After publication it must allow
 * a new consumer to overlap the tail of after_consumer's return.
 * Context and queue latency/cancellation policy remain the module's job.
 */
struct z7_highlight_hooks {
    uint32_t abi, size;
    void *descriptor;
    uint32_t (*before_source)(uint32_t output, void *frame);
    void (*after_source)(uint32_t output, void *frame, uint32_t token);
    uint32_t (*before_consumer)(void *packet);
    void (*after_consumer)(void *packet, uint32_t decision);
};
struct z7_module_highlight_api {
    struct z7_module_worker_api worker;
    uint32_t (*register_highlight)(const struct z7_highlight_hooks *hooks);
};
#endif
