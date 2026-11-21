/* SPDX-License-Identifier: MIT. Bounded native cache write observation.
 * Every relevant writer must bracket its complete write exactly once. This
 * Caller owns aligned state and a separate exclusive ticket output. This
 * neither excludes writers nor pins allocation/bank mappings. A valid ticket
 * establishes a copied snapshot, not an atomic later application/restore.
 */
#ifndef Z7_CACHE_OBSERVATION_H
#define Z7_CACHE_OBSERVATION_H
#include <stdint.h>
struct z7_cache_observation { uint32_t active, serial, halted; };
static void z7_cache_observation_halt(struct z7_cache_observation *p)
{ __atomic_store_n(&p->halted, 1, __ATOMIC_RELEASE); }
static uint32_t z7_cache_observation_step(struct z7_cache_observation *p)
{
    for (uint32_t n = 0; n < 3; ++n) {
        uint32_t serial = __atomic_load_n(&p->serial, __ATOMIC_RELAXED);
        if (serial == UINT32_MAX) break;
        if (__atomic_compare_exchange_n(&p->serial, &serial, serial + 1, 0,
                                        __ATOMIC_ACQ_REL, __ATOMIC_RELAXED)) return 1;
    }
    z7_cache_observation_halt(p); return 0;
}
/* Token1 must be retired once, even if serial exhaustion halted observation.
 * Token0 still permits the original native write; this is not writer admission.
 */
static uint32_t z7_cache_observation_begin(struct z7_cache_observation *p)
{
    if (!p || __atomic_load_n(&p->halted, __ATOMIC_ACQUIRE)) return 0;
    for (uint32_t n = 0; n < 3; ++n) {
        uint32_t active = __atomic_load_n(&p->active, __ATOMIC_RELAXED);
        if (active == UINT32_MAX) break;
        if (__atomic_compare_exchange_n(&p->active, &active, active + 1, 0,
                                        __ATOMIC_ACQ_REL, __ATOMIC_RELAXED)) {
            z7_cache_observation_step(p); return 1;
        }
    }
    z7_cache_observation_halt(p); return 0;
}
static void z7_cache_observation_end(struct z7_cache_observation *p, uint32_t token)
{
    if (!p || !token) return;
    if (token != 1) { z7_cache_observation_halt(p); return; }
    z7_cache_observation_step(p);
    for (uint32_t n = 0; n < 3; ++n) {
        uint32_t active = __atomic_load_n(&p->active, __ATOMIC_RELAXED);
        if (!active) break;
        if (__atomic_compare_exchange_n(&p->active, &active, active - 1, 0,
                                        __ATOMIC_RELEASE, __ATOMIC_RELAXED)) return;
    }
    z7_cache_observation_halt(p);
}
static uint32_t z7_cache_observation_valid(const struct z7_cache_observation *p, uint32_t ticket)
{
    if (!p || ticket == UINT32_MAX) return 0;
    __atomic_thread_fence(__ATOMIC_ACQUIRE);
    return !__atomic_load_n(&p->halted, __ATOMIC_ACQUIRE) &&
        !__atomic_load_n(&p->active, __ATOMIC_ACQUIRE) &&
        __atomic_load_n(&p->serial, __ATOMIC_ACQUIRE) == ticket;
}
static uint32_t z7_cache_observation_ticket(const struct z7_cache_observation *p, uint32_t *out)
{
    if (!p || !out) return 0;
    uint32_t serial = __atomic_load_n(&p->serial, __ATOMIC_ACQUIRE);
    if (!z7_cache_observation_valid(p, serial)) return 0;
    *out = serial; return 1;
}
#endif
