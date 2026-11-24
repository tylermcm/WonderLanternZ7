/* SPDX-License-Identifier: MIT. Independent original-Z7 C 3.80 menu binding.
 * Optional Custom Settings overview entry. No native rows are replaced.
 * Prepared during loading, published with the owned page before GUI readiness.
 */
#define SM_ROOT_OBJECT 0xa18367a4u
static uint32_t sm_root_meta[7], sm_root_callbacks[8];
static uint32_t sm_root_controls[9][7], sm_root_maps[9], sm_root_events[18][4];

static uint32_t sm_root_enter(uint32_t object)
{
    F(0x103fbb5du, void, const char *, uint32_t, uint32_t)("Display settings", 45, 0);
    return F(0x104ec719u, uint32_t, uint32_t)(object);
}

static uint32_t sm_root_prepare(void)
{
    const uint32_t *object = (const uint32_t *)(uintptr_t)SM_ROOT_OBJECT;
    /* Reject an occupied/foreign overview instead of replacing live widgets. */
    if (object[0] != 0x01250002u || object[1] != 0xa1833574u ||
        object[3] || object[9] || object[4] != 0x1066cae4u ||
        object[10] != 0xa18719b8u) return 0;
    const uint32_t *meta = (const uint32_t *)(uintptr_t)object[10];
    if (meta[0] != 0x1002 || meta[3] != 0x112d69d0u ||
        meta[4] != 0x11307accu || meta[5] != 0x00080008u) return 0;
    for (uint32_t i = 0; i < 7; ++i) sm_root_meta[i] = meta[i];
    for (uint32_t i = 0; i < 8; ++i) {
        sm_root_callbacks[i] = W(object[4] + i * 4);
        sm_root_maps[i] = W(meta[4] + i * 4);
        for (uint32_t j = 0; j < 7; ++j)
            sm_root_controls[i][j] = W(meta[3] + (i * 7 + j) * 4);
    }
    uint32_t source = sm_root_maps[0], activations = 0;
    if (!readable(source, sizeof(sm_root_events))) return 0;
    for (uint32_t i = 0; i < 18; ++i) {
        for (uint32_t j = 0; j < 4; ++j) sm_root_events[i][j] = W(source + (i * 4 + j) * 4);
        if (sm_root_events[i][0] == 0x239 || sm_root_events[i][0] == 0x252 ||
            sm_root_events[i][0] == 0x25f) {
            if (sm_root_events[i][1] != 0x10404f89u || sm_root_events[i][3] != 0x126) return 0;
            sm_root_events[i][1] = (uint32_t)(uintptr_t)sm_open;
            sm_root_events[i][3] = 0x3a0;
            ++activations;
        }
    }
    if (activations != 3 || sm_root_events[17][0] != 0x2f2) return 0;
    for (uint32_t j = 0; j < 7; ++j) sm_root_controls[8][j] = sm_root_controls[0][j];
    sm_root_controls[8][0] = 45;
    sm_root_controls[8][4] = 0x1209;
    sm_root_controls[8][5] = 0;
    sm_root_controls[8][6] = 0x7c00;
    sm_root_maps[8] = (uint32_t)(uintptr_t)sm_root_events;
    sm_root_meta[3] = (uint32_t)(uintptr_t)sm_root_controls;
    sm_root_meta[4] = (uint32_t)(uintptr_t)sm_root_maps;
    sm_root_meta[5] = 0x00080009u; /* Native eight-row viewport, nine scrollable entries. */
    sm_root_callbacks[0] = (uint32_t)(uintptr_t)sm_root_enter;
    return 1;
}

static void sm_root_publish(void)
{
    W(SM_ROOT_OBJECT + 40) = (uint32_t)(uintptr_t)sm_root_meta;
    __asm__ volatile("dmb sy" ::: "memory");
    W(SM_ROOT_OBJECT + 16) = (uint32_t)(uintptr_t)sm_root_callbacks;
}
