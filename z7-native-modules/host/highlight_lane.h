/* SPDX-License-Identifier: MIT. Independent original-Z7 research.
 * Nonblocking ownership for a future whole-frame / parameter-consumer bridge.
 * This primitive alone does not fence native code: callers must retain the
 * token through their LAST native access and handle admission failure safely.
 * It neither pins allocations nor establishes native scheduling/lock order.
 */
#ifndef Z7_HIGHLIGHT_LANE_H
#define Z7_HIGHLIGHT_LANE_H
#include <stdint.h>

enum z7_highlight_lane_role { Z7_LANE_FRAME = 1, Z7_LANE_PARAMETERS = 2 };
struct z7_highlight_lane { uint32_t state, owner; };
_Static_assert(sizeof(struct z7_highlight_lane) == 8, "Lane layout");

/* Low bits: 0 idle, 1 frame, 2 parameters, 3 publication/release in progress.
 * Remaining bits are a nonrecycled generation. Zero is never a valid token.
 * Exhaustion leaves idle 0xfffffffc permanently closed to admission; the
 * integration must arrange feature shutdown, never reset a live lane to zero.
 */
static uint32_t z7_highlight_lane_enter(struct z7_highlight_lane *p,
                                      uint32_t role, uint32_t owner)
{
    if ((role != Z7_LANE_FRAME && role != Z7_LANE_PARAMETERS) || !owner) return 0;
    uint32_t idle = __atomic_load_n(&p->state, __ATOMIC_ACQUIRE);
    if ((idle & 3) || idle == 0xfffffffcu) return 0;
    if (!__atomic_compare_exchange_n(&p->state, &idle, idle | 3, 0,
                                    __ATOMIC_ACQ_REL, __ATOMIC_RELAXED)) return 0;
    __atomic_store_n(&p->owner, owner, __ATOMIC_RELAXED);
    __atomic_store_n(&p->state, idle | role, __ATOMIC_RELEASE);
    return idle | role;
}

static uint32_t z7_highlight_lane_owns(const struct z7_highlight_lane *p,
                                     uint32_t token, uint32_t owner)
{
    uint32_t role = token & 3;
    if ((role != Z7_LANE_FRAME && role != Z7_LANE_PARAMETERS) || !owner) return 0;
    if (__atomic_load_n(&p->state, __ATOMIC_ACQUIRE) != token ||
        __atomic_load_n(&p->owner, __ATOMIC_RELAXED) != owner) return 0;
    return __atomic_load_n(&p->state, __ATOMIC_ACQUIRE) == token;
}

static uint32_t z7_highlight_lane_leave(struct z7_highlight_lane *p,
                                      uint32_t token, uint32_t owner)
{
    if (!z7_highlight_lane_owns(p, token, owner)) return 0;
    uint32_t expected = token;
    if (!__atomic_compare_exchange_n(&p->state, &expected, (token & ~3u) | 3, 0,
                                    __ATOMIC_ACQ_REL, __ATOMIC_RELAXED)) return 0;
    __atomic_store_n(&p->owner, 0, __ATOMIC_RELAXED);
    __atomic_store_n(&p->state, (token & ~3u) + 4, __ATOMIC_RELEASE);
    return 1;
}
#endif
