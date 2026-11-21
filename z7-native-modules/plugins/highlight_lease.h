/* SPDX-License-Identifier: MIT. Native-consumer writer / bounded worker readers.
 * Native parameter writers use the DisplayService consumer lane. This module
 * publication is not a native allocation pin or physical frame transaction.
 */
#ifndef Z7_HIGHLIGHT_LEASE_H
#define Z7_HIGHLIGHT_LEASE_H
#include "highlight_context.h"
struct z7_highlight_lease_record {
    uint32_t valid, native_generation, epoch, palette, disabled;
    struct z7_highlight_context context;
    uint32_t baseline[25], parameters[25];
};
struct z7_highlight_lease {
    uint32_t sequence, serial, halted;
    struct z7_highlight_lease_record record;
};
struct z7_highlight_lease_snapshot {
    uint32_t serial;
    struct z7_highlight_lease_record record;
};
static uint32_t z7_highlight_lease_read(const struct z7_highlight_lease *p,
                                     struct z7_highlight_lease_snapshot *out)
{
    for (uint32_t attempt = 0; attempt < 3; ++attempt) {
        uint32_t sequence = __atomic_load_n(&p->sequence, __ATOMIC_ACQUIRE);
        if ((sequence & 1) || __atomic_load_n(&p->halted, __ATOMIC_ACQUIRE)) continue;
        struct z7_highlight_lease_snapshot s;
        s.serial = __atomic_load_n(&p->serial, __ATOMIC_RELAXED);
        for (uint32_t i = 0; i < sizeof(s.record) / 4; ++i)
            ((uint32_t *)&s.record)[i] = __atomic_load_n((const uint32_t *)&p->record + i, __ATOMIC_RELAXED);
        __atomic_thread_fence(__ATOMIC_ACQUIRE);
        if (sequence != __atomic_load_n(&p->sequence, __ATOMIC_RELAXED) ||
            s.serial != __atomic_load_n(&p->serial, __ATOMIC_RELAXED) ||
            __atomic_load_n(&p->halted, __ATOMIC_ACQUIRE)) continue;
        for (uint32_t i = 0; i < sizeof(s) / 4; ++i)
            ((volatile uint32_t *)out)[i] = ((const uint32_t *)&s)[i];
        return 1; /* Serial0 is the initial, invalid lease. */
    }
    return 0;
}
static uint32_t z7_highlight_lease_publish(struct z7_highlight_lease *p,
                                        const struct z7_highlight_lease_record *record)
{
    if (__atomic_load_n(&p->halted, __ATOMIC_ACQUIRE)) return 0;
    uint32_t sequence = __atomic_load_n(&p->sequence, __ATOMIC_RELAXED);
    if ((sequence & 1) || !__atomic_compare_exchange_n(&p->sequence, &sequence, sequence + 1, 0,
            __ATOMIC_ACQ_REL, __ATOMIC_RELAXED)) return 0;
    uint32_t serial = __atomic_load_n(&p->serial, __ATOMIC_RELAXED);
    if (serial == UINT32_MAX) {
        __atomic_store_n(&p->halted, 1, __ATOMIC_RELEASE);
        __atomic_store_n(&p->sequence, sequence, __ATOMIC_RELEASE);
        return 0;
    }
    for (uint32_t i = 0; i < sizeof(*record) / 4; ++i)
        __atomic_store_n((uint32_t *)&p->record + i, ((const uint32_t *)record)[i], __ATOMIC_RELAXED);
    __atomic_store_n(&p->serial, serial + 1, __ATOMIC_RELAXED);
    __atomic_store_n(&p->sequence, sequence + 2, __ATOMIC_RELEASE);
    return 1;
}
#endif
