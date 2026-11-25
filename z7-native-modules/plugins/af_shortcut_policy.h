/* SPDX-License-Identifier: MIT.
 * Independent original-Z7 port component. Press-edge/GUI deferral design follows
 * JKWTCN's MIT AF shortcut implementation. No firmware bindings or publication.
 */
#ifndef Z7_AF_SHORTCUT_POLICY_H
#define Z7_AF_SHORTCUT_POLICY_H
#include <stdint.h>
#define Z7_AF_BUTTONS 5u
#define Z7_AF_TARGETS 13u
#define Z7_AF_BUTTON_MASK 31u
struct z7_af_shortcut_policy {
    uint32_t assignments[Z7_AF_BUTTONS];
    uint32_t pending;
};
/* Caller must supply verified press edges, never held-state bits. Only the
 * input task produces pending bits; GUI context consumes them. Assignments
 * belong to GUI/configuration state, not a native AF property namespace.
 */
static inline void z7_af_shortcut_reset(struct z7_af_shortcut_policy *p)
{
    for (uint32_t i=0;i<Z7_AF_BUTTONS;++i) __atomic_store_n(&p->assignments[i],0,__ATOMIC_RELEASE);
    __atomic_store_n(&p->pending,0,__ATOMIC_RELEASE);
}
static inline uint32_t z7_af_shortcut_assign(struct z7_af_shortcut_policy *p,
                                           uint32_t button,uint32_t target)
{
    if (button>=Z7_AF_BUTTONS || target>Z7_AF_TARGETS) return 0;
    __atomic_store_n(&p->assignments[button],target,__ATOMIC_RELEASE);
    return 1;
}
static inline void z7_af_shortcut_capture(struct z7_af_shortcut_policy *p,
                                        uint32_t photo_context,uint32_t press_edges)
{
    if (!photo_context) {
        __atomic_store_n(&p->pending,0,__ATOMIC_RELEASE);
        return;
    }
    uint32_t pressed=0;
    for (uint32_t i=0;i<Z7_AF_BUTTONS;++i) {
        uint32_t target=__atomic_load_n(&p->assignments[i],__ATOMIC_ACQUIRE);
        if (target && target<=Z7_AF_TARGETS &&
            (press_edges&(1u<<i))) pressed|=1u<<i;
    }
    if (pressed) __atomic_fetch_or(&p->pending,pressed,__ATOMIC_RELEASE);
}
/* Returns (button+1)<<8 | target, or zero. available_targets uses target-1
 * bits and includes native focus restrictions plus extension readiness.
 * native_none_buttons admits only buttons still assigned native None.
 * No property write, autofocus start, file write, or rollback is performed here.
 */
static inline uint32_t z7_af_shortcut_take(struct z7_af_shortcut_policy *p,
    uint32_t photo_context,uint32_t busy,uint32_t native_none_buttons,
    uint32_t available_targets)
{
    if (!__atomic_load_n(&p->pending,__ATOMIC_ACQUIRE)) return 0;
    if (!photo_context) {
        __atomic_store_n(&p->pending,0,__ATOMIC_RELEASE);
        return 0;
    }
    if (busy) return 0;
    uint32_t pending=__atomic_exchange_n(&p->pending,0,__ATOMIC_ACQ_REL);
    for (uint32_t i=0;i<Z7_AF_BUTTONS;++i) {
        uint32_t target=__atomic_load_n(&p->assignments[i],__ATOMIC_ACQUIRE);
        if (!(pending&(1u<<i)) || !(native_none_buttons&(1u<<i)) ||
            !target || target>Z7_AF_TARGETS || !(available_targets&(1u<<(target-1)))) continue;
        return ((i+1)<<8)|target;
    }
    return 0;
}
#endif
