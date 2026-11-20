/* SPDX-License-Identifier: MIT. Single-GUI-writer, bounded-reader publication.
 * Independent original-Z7 module state; not a native camera transaction/fence.
 */
#ifndef Z7_HIGHLIGHT_EPOCH_H
#define Z7_HIGHLIGHT_EPOCH_H
#include "highlight_context.h"
struct z7_highlight_view {
    struct z7_highlight_context context;
    uint32_t settings_revision, preset, wanted, eligible, preset_generation;
};
struct z7_highlight_publication {
    uint32_t sequence, epoch, halted;
    struct z7_highlight_view view;
};
struct z7_highlight_snapshot {
    uint32_t epoch;
    struct z7_highlight_view view;
};
static uint32_t z7_highlight_publish(struct z7_highlight_publication *p,
                                   const struct z7_highlight_view *view)
{
    if (__atomic_load_n(&p->halted, __ATOMIC_ACQUIRE)) return 0;
    uint32_t sequence = __atomic_load_n(&p->sequence, __ATOMIC_RELAXED);
    if ((sequence & 1) || !__atomic_compare_exchange_n(&p->sequence, &sequence,
        sequence + 1, 0, __ATOMIC_ACQ_REL, __ATOMIC_RELAXED)) return 0;
    const uint32_t *from = (const uint32_t *)view;
    uint32_t *to = (uint32_t *)&p->view;
    uint32_t epoch = __atomic_load_n(&p->epoch, __ATOMIC_RELAXED), changed = !epoch;
    for (uint32_t i = 0; i < sizeof(*view) / 4; ++i)
        if (from[i] != __atomic_load_n(to + i, __ATOMIC_RELAXED)) changed = 1;
    if (!changed) {
        __atomic_store_n(&p->sequence, sequence, __ATOMIC_RELEASE);
        return 1;
    }
    if (epoch == UINT32_MAX) {
        /* Never recycle an old queued epoch. Park until a fresh boot. */
        __atomic_store_n(&p->halted, 1, __ATOMIC_RELEASE);
        __atomic_store_n(&p->sequence, sequence, __ATOMIC_RELEASE);
        return 0;
    }
    for (uint32_t i = 0; i < sizeof(*view) / 4; ++i)
        __atomic_store_n(to + i, from[i], __ATOMIC_RELAXED);
    __atomic_store_n(&p->epoch, epoch + 1, __ATOMIC_RELAXED);
    __atomic_store_n(&p->sequence, sequence + 2, __ATOMIC_RELEASE);
    return 1;
}
static uint32_t z7_highlight_snapshot(const struct z7_highlight_publication *p,
                                    struct z7_highlight_snapshot *out)
{
    for (uint32_t attempt = 0; attempt < 3; ++attempt) {
        uint32_t sequence = __atomic_load_n(&p->sequence, __ATOMIC_ACQUIRE);
        if ((sequence & 1) || __atomic_load_n(&p->halted, __ATOMIC_ACQUIRE)) continue;
        struct z7_highlight_snapshot snapshot;
        snapshot.epoch = __atomic_load_n(&p->epoch, __ATOMIC_RELAXED);
        const uint32_t *from = (const uint32_t *)&p->view;
        uint32_t *to = (uint32_t *)&snapshot.view;
        for (uint32_t i = 0; i < sizeof(snapshot.view) / 4; ++i)
            to[i] = __atomic_load_n(from + i, __ATOMIC_RELAXED);
        __atomic_thread_fence(__ATOMIC_ACQUIRE);
        if (snapshot.epoch && sequence == __atomic_load_n(&p->sequence, __ATOMIC_RELAXED) &&
            snapshot.epoch == __atomic_load_n(&p->epoch, __ATOMIC_RELAXED) &&
            !__atomic_load_n(&p->halted, __ATOMIC_ACQUIRE)) {
            for (uint32_t i = 0; i < sizeof(snapshot) / 4; ++i)
                ((volatile uint32_t *)out)[i] = ((const uint32_t *)&snapshot)[i];
            return 1;
        }
    }
    return 0;
}
#endif
