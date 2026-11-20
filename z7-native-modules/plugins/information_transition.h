/* SPDX-License-Identifier: MIT. Independent original-Z7 C3.80 transition ledger.
 * Caller must release custom overlays/masks/base before entry. This helper does
 * not grant native input admission, synthesize keys or publish application state.
 * A parent request is asynchronous; only observation confirms entry/return.
 */
#ifndef Z7_INFORMATION_TRANSITION_H
#define Z7_INFORMATION_TRANSITION_H
#include <stdint.h>
#define IT_W(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define IT_B(a) (*(volatile uint8_t *)(uintptr_t)(a))
#define IT_F(a, result, ...) ((result (*)(__VA_ARGS__))(uintptr_t)(a))
enum { IT_IDLE, IT_ENTERING, IT_VISIBLE, IT_EXITING, IT_RECOVERY, IT_CONFLICT,
       IT_CONFIG_EXIT, IT_RETURN_REQUESTED };
struct z7_information_transition {
    uint32_t phase, saved_page, entry_page, recovery_page, recovery_property;
};
static uint32_t information_property(void)
{
    return IT_F(0x104065a5u, uint32_t, uint32_t)(0x2f15u);
}
static uint32_t information_shooting_context(void)
{
    return IT_B(0xa1829af4u) == 0 &&
        IT_W(0xa20207bcu) == 0xa1829af8u &&
        IT_W(0xa20207bcu + 13 * 4) == 0xa182d16cu &&
        IT_W(0xa1829b0cu) == 0x1030da57u && IT_W(0xa1829b10u) == 0x1030dd1fu &&
        IT_F(0x103673adu, uint32_t, void)() == 0x2f15u;
}
static uint32_t information_bindings(void)
{
    uint32_t parent = IT_W(0xa1829af8u);
    return IT_W(0xa182d180u) == 0x102fd647u && IT_W(0xa182d184u) == 0x102fdaefu &&
        (parent & 1u) && parent >= 0x10020001u && parent < 0x11fa0000u;
}
/* Conditional retry also covers the native setter's snapshot-before-property
 * partial failure. Any different property/snapshot is foreign and stays intact.
 */
static uint32_t information_recover(struct z7_information_transition *t)
{
    if (t->phase != IT_RECOVERY || !information_shooting_context() || !information_bindings()) return 0;
    uint32_t page = IT_B(0xa201d65au), property = information_property();
    if ((page != t->recovery_page && page != t->recovery_property) ||
        (property != t->recovery_page && property != t->recovery_property)) {
        t->phase = IT_CONFLICT; return 0;
    }
    uint32_t ok = IT_F(0x103673dfu, uint32_t, uint32_t)(t->recovery_page);
    if (!ok || !information_shooting_context() || information_property() != t->recovery_page ||
        IT_B(0xa201d65au) != t->recovery_page) return 0;
    t->phase = IT_IDLE; return 1;
}
static uint32_t information_enter(struct z7_information_transition *t, uint32_t saved, uint32_t released)
{
    if (t->phase != IT_IDLE || !released || saved > 3 ||
        !information_shooting_context() || !information_bindings()) return 0;
    uint32_t page = IT_B(0xa201d65au);
    if (page > 3 || information_property() != page) return 0;
    t->saved_page = saved; t->entry_page = page;
    t->recovery_page = page; t->recovery_property = 4; t->phase = IT_RECOVERY;
    uint32_t ok = IT_F(0x103673dfu, uint32_t, uint32_t)(4);
    if (!ok || !information_shooting_context() || information_property() != 4 ||
        IT_B(0xa201d65au) != 4) {
        information_recover(t); return 0;
    }
    t->phase = IT_ENTERING;
    /* Exact native shooting request sequence, after verified property publish.
     * Its return value does not prove that the manager accepted the request.
     */
    uint32_t descriptor = IT_F(0x1030d50du, uint32_t, void)();
    IT_F(0x103eb7c5u, void, uint32_t)(descriptor);
    return 2;
}
/* Call only when delegating an already admitted native information DISP exit. */
static uint32_t information_exit_admitted(struct z7_information_transition *t)
{
    if ((t->phase != IT_ENTERING && t->phase != IT_VISIBLE) ||
        IT_B(0xa1829af4u) != 13 || IT_W(0xa20207bcu + 13 * 4) != 0xa182d16cu ||
        !information_bindings() || information_property() != 4 || IT_B(0xa201d65au) != 4) return 0;
    t->phase = IT_EXITING; return 1;
}
/* Settings-driven return uses the ordinary native LCD exit primitives, without
 * synthesizing a key or assigning application state. Defer while the native
 * info snapshot, output or monitor cannot take this ordinary return route.
 */
static uint32_t information_request_return(struct z7_information_transition *t)
{
    if ((t->phase != IT_ENTERING && t->phase != IT_VISIBLE && t->phase != IT_CONFIG_EXIT) ||
        IT_B(0xa1829af4u) != 13 || IT_W(0xa20207bcu + 13 * 4) != 0xa182d16cu ||
        !information_bindings() || IT_F(0x103673adu, uint32_t, void)() != 0x2f15u) return 0;
    uint32_t state = IT_B(0xa20210edu) & 63u, property = information_property();
    uint32_t parent = IT_W(0xa182d16cu);
    if (state == 2 || state == 5 || (parent & 1u) == 0 ||
        parent < 0x10020001u || parent >= 0x11fa0000u ||
        (property != 4 && !(property == 0 && t->phase == IT_CONFIG_EXIT)) ||
        (IT_B(0xa201d65au) != 4 && !(IT_B(0xa201d65au) == 0 && t->phase == IT_CONFIG_EXIT)) ||
        IT_F(0x1040a4afu, uint32_t, void)() ||
        IT_F(0x103fec19u, uint32_t, void)() == 3 ||
        IT_F(0x10297a2fu, uint32_t, void)() || IT_F(0x10297a17u, uint32_t, void)()) return 0;
    t->phase = IT_CONFIG_EXIT;
    IT_F(0x10333e1bu, void, uint32_t, uint32_t)(0, 0);
    IT_F(0x10301215u, void, uint32_t)(1);
    uint32_t ok = IT_F(0x104065b1u, uint32_t, uint32_t, uint32_t)(0x2f15u, 0);
    if (!ok || information_property() != 0 || IT_B(0xa1829af4u) != 13) return 0;
    t->phase = IT_RETURN_REQUESTED;
    IT_F(0x103764b9u, void, uint32_t, uint32_t, uint32_t)(0xa182d16cu, 4, 0x100000u);
    return 1;
}
/* Returns 1 only after confirmed native return and original-user-page restore.
 * A nonzero parent return or intermediate native page0 is never a new baseline.
 */
static uint32_t information_observe(struct z7_information_transition *t)
{
    if (t->phase == IT_RECOVERY) return information_recover(t);
    if (t->phase == IT_IDLE || t->phase == IT_CONFLICT) return 0;
    if (!information_bindings()) { t->phase = IT_CONFLICT; return 0; }
    uint32_t app = IT_B(0xa1829af4u);
    uint32_t returning = t->phase == IT_EXITING || t->phase == IT_CONFIG_EXIT || t->phase == IT_RETURN_REQUESTED;
    if (app == 13) {
        if (IT_W(0xa20207bcu + 13 * 4) != 0xa182d16cu ||
            (information_property() != 4 && !(returning && information_property() == 0)) ||
            (IT_B(0xa201d65au) != 4 && !(returning && IT_B(0xa201d65au) == 0))) t->phase = IT_CONFLICT;
        else if (t->phase == IT_ENTERING) t->phase = IT_VISIBLE;
        return 0;
    }
    if (!information_shooting_context()) return 0;
    uint32_t page = IT_B(0xa201d65au), property = information_property();
    if (page == 4 && property == 4 && t->phase == IT_ENTERING) return 0;
    if (page == 4 && property == 0 && returning) return 0;
    if (page != 0 || property != 0) { t->phase = IT_CONFLICT; return 0; }
    t->recovery_page = t->saved_page; t->recovery_property = 0; t->phase = IT_RECOVERY;
    return information_recover(t);
}
#undef IT_W
#undef IT_B
#undef IT_F
#endif
