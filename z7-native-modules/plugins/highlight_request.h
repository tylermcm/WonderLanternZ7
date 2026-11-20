/* SPDX-License-Identifier: MIT. Independent original-Z7 C3.80 research.
 * Resident asynchronous request storage, not an installed display feature.
 * One worker owns submission/reaping. A consumer bridge must bracket the
 * ORIGINAL dispatcher (or original completion for a cancelled owned request)
 * with begin/end. Never call the native blocking1034FF1E wrapper here.
 */
#ifndef Z7_HIGHLIGHT_REQUEST_H
#define Z7_HIGHLIGHT_REQUEST_H
#include <stdint.h>
#include <stddef.h>

enum z7_highlight_request_state { Z7_HR_IDLE, Z7_HR_BUILDING, Z7_HR_PENDING,
    Z7_HR_CONSUMING, Z7_HR_RETIRED };
struct z7_highlight_request {
    uint32_t descriptor[7];
    uint32_t payload[26]; /* 100 parameter bytes plus native acknowledgement. */
    uint32_t state, epoch, command, callback, send_returned, send_result, completed;
};
_Static_assert(sizeof(uintptr_t) == 4, "Original-Z7 ARM pointers required");
_Static_assert(offsetof(struct z7_highlight_request, payload) == 28,
               "Descriptor must not overlap the104-byte payload");
#define Z7_HR_FN(a, result, ...) ((result (*)(__VA_ARGS__))(uintptr_t)(a))

static void z7_highlight_request_complete(uint32_t command, void *context)
{
    struct z7_highlight_request *r = context;
    if (r && __atomic_load_n(&r->state, __ATOMIC_ACQUIRE) == Z7_HR_CONSUMING &&
        command == r->command)
        __atomic_store_n(&r->completed, 1, __ATOMIC_RELEASE);
    /* Completion alone does not permit reuse: the original dispatcher must
     * return, and the submitting call may still be on another task's stack. */
}

/* Returns1 for an attempted submission,0 for invalid/busy. Native queue return
 * is diagnostic only: even an error does NOT prove the pointer was not retained.
 * Storage stays resident and immutable until bracketed consumption completes.
 * Kernel queue latency/blocking is not established by this helper. */
static uint32_t z7_highlight_request_submit(struct z7_highlight_request *r,
    const void *gui_request36, uint32_t output_flag, uint32_t epoch)
{
    uint32_t expected = Z7_HR_IDLE;
    if (!r || !gui_request36 || (output_flag != 1 && output_flag != 4) ||
        !__atomic_compare_exchange_n(&r->state, &expected, Z7_HR_BUILDING, 0,
                                    __ATOMIC_ACQUIRE, __ATOMIC_RELAXED)) return 0;
    for (uint32_t i = 0; i < 7; ++i) r->descriptor[i] = 0;
    for (uint32_t i = 0; i < 26; ++i) r->payload[i] = 0;
    r->epoch = epoch;
    r->command = output_flag == 1 ? 0x42060007u : 0x42062007u;
    r->completed = r->send_returned = 0;
    r->send_result = 0xffffffffu;
    r->callback = (uint32_t)(uintptr_t)z7_highlight_request_complete;
    Z7_HR_FN(0x1034fe23u, void, void *, const void *, uint32_t)
        (r->payload, gui_request36, output_flag);
    Z7_HR_FN(0x1034efb1u, void *, uint32_t, uint32_t, uint32_t, void *,
             uint32_t, void *)(16, output_flag == 1 ? 0 : 2, 0, r->payload,
                              r->callback, r->descriptor);
    r->descriptor[6] = (uint32_t)(uintptr_t)r;
    __atomic_store_n(&r->state, Z7_HR_PENDING, __ATOMIC_RELEASE);
    r->send_result = Z7_HR_FN(0x10348495u, uint32_t, void *)(r->descriptor);
    __atomic_store_n(&r->send_returned, 1, __ATOMIC_RELEASE);
    return 1;
}

/* Consumer bridge:0 ordinary native packet;1 owned/current;2 owned/cancel;
 * 3 owned but not safely claimable (suppress duplicate/reentrant consumption).
 * Only2 calls original completion directly;1 executes original dispatcher.
 * Both must call end AFTER the original function returns. No payload mutation.
 * epoch must come from a coherent context snapshot at this dispatch boundary. */
static uint32_t z7_highlight_request_begin(struct z7_highlight_request *r,
    const void *packet, uint32_t epoch)
{
    if (!r || packet != r->descriptor) return 0;
    uint32_t expected = Z7_HR_PENDING;
    if (!__atomic_compare_exchange_n(&r->state, &expected, Z7_HR_CONSUMING, 0,
                                    __ATOMIC_ACQUIRE, __ATOMIC_RELAXED)) return 3;
    if (r->descriptor[3] != r->callback || r->descriptor[4] != r->command ||
        r->descriptor[5] != (uint32_t)(uintptr_t)r->payload ||
        r->descriptor[6] != (uint32_t)(uintptr_t)r) return 3;
    return epoch == r->epoch ? 1 : 2;
}

static void z7_highlight_request_end(struct z7_highlight_request *r)
{
    if (__atomic_load_n(&r->state, __ATOMIC_ACQUIRE) == Z7_HR_CONSUMING &&
        __atomic_load_n(&r->completed, __ATOMIC_ACQUIRE))
        __atomic_store_n(&r->state, Z7_HR_RETIRED, __ATOMIC_RELEASE);
}

/* Worker only:0 pending/parked;1 completed without native application;
 * 2 native handler acknowledged its100-byte copy. This is NOT pixel evidence.
 * No timeout release: a lost/failed enqueue remains parked until consumption. */
static uint32_t z7_highlight_request_reap(struct z7_highlight_request *r)
{
    if (__atomic_load_n(&r->state, __ATOMIC_ACQUIRE) != Z7_HR_RETIRED ||
        !__atomic_load_n(&r->send_returned, __ATOMIC_ACQUIRE)) return 0;
    uint32_t result = r->payload[25] == 1 ? 2 : 1;
    __atomic_store_n(&r->state, Z7_HR_IDLE, __ATOMIC_RELEASE);
    return result;
}
#undef Z7_HR_FN
#endif
