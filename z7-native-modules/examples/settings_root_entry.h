/* SPDX-License-Identifier: MIT. Independent original-Z7 C 3.80 menu binding.
 * Optional Custom Settings overview entry. No native rows are replaced.
 * Prepared during loading, published with the owned page before GUI readiness.
 */
#define SM_ROOT_OBJECT 0xa18367a4u
static uint32_t sm_root_meta[7], sm_root_callbacks[8];
static uint32_t sm_root_controls[9][7], sm_root_maps[9], sm_root_events[18][4];

#ifdef Z7_SETTINGS_ROOT_LABEL_REFRESH
static uint32_t sm_root_label_widget, sm_root_label_dirty;
static uint32_t sm_root_seed_labels(void)
{
    static const char *const text[2] = {"Display settings", "h"};
    for (uint32_t i = 0; i < 2; ++i) {
        uint32_t record = 0xa2019e78u + (45 + i) * 12;
        uint32_t buffer = W(record + 4), length = 0;
        if (!ram(buffer & ~3u, 56)) return 0;
        while (text[i][length]) ++length;
        uint32_t same = W(record) == length && !W(record + 8);
        if (same) for (uint32_t j = 0; j <= length; ++j)
            if (B(buffer + j) != (uint8_t)text[i][j]) { same = 0; break; }
        if (!same) {
            F(0x103fbb5du, void, const char *, uint32_t, uint32_t)(text[i], 45 + i, 0);
            sm_root_label_dirty |= 1u << i;
        }
    }
    return 1;
}
#endif

#ifdef Z7_SETTINGS_CATEGORY_ENTRY
static uint32_t sm_root_prefix_paint(uint32_t prefix)
{
    uint32_t pool = W(SM_ROOT_OBJECT + 36);
    if (pool && W(pool + 8)) {
        /* Read the existing primary row widget, without allocating one. */
        uint32_t reserved = *(volatile uint16_t *)(uintptr_t)(pool + 4);
        uint32_t row = W(W(pool + 8) + (reserved + 8) * 4);
        if (row) {
            /* Match the menu row's general-widget theme, not the separate
             * regular-text theme (whose background is the value-column fill).
             * This is the same resolver used by the native row font path. */
            uint32_t background[2];
            F(0x104bd407u, void, uint32_t, uint32_t *, uint32_t, uint32_t,
              uint32_t, uint32_t)(1, background, W(row + 0x38), W(row + 0x30),
                                W(row + 0x2c), 0);
            W(prefix + 0x34) = 2;
            uint32_t header = W(SM_ROOT_OBJECT + 12);
            W(prefix + 0x38) = W(row + 0x30) && header && W(header + 0x30) ?
                              0xa00040ffu : 0xff5599ffu;
            W(prefix + 0x3c) = background[0]; W(prefix + 0x40) = background[1];
        }
    }
    return F(0x10384969u, uint32_t, uint32_t)(prefix);
}
static uint32_t sm_root_decorate(uint32_t object)
{
#ifdef Z7_SETTINGS_ROOT_LABEL_REFRESH
    uint32_t labels_ready = object == SM_ROOT_OBJECT && sm_root_seed_labels();
#endif
    uint32_t result = F(0x104ec725u, uint32_t, uint32_t)(object);
    if (object != SM_ROOT_OBJECT || !W(object + 36)) return result;
#ifdef Z7_SETTINGS_ROOT_LABEL_REFRESH
    /* Native row construction can precede entry-label registration. Rebind
     * a newly created row, or a repaired shared label, on the GUI task only.
     * Do not recreate its font cache on every ordinary paint. */
    uint32_t pool = W(object + 36), pointers = W(pool + 8);
    uint32_t reserved = *(volatile uint16_t *)(uintptr_t)(pool + 4);
    uint32_t row = pointers ? W(pointers + (reserved + 8) * 4) : 0;
    if (labels_ready && row && (row != sm_root_label_widget || (sm_root_label_dirty & 1))) {
        sm_bind_text(row, 45);
        sm_root_label_widget = row; sm_root_label_dirty &= ~1u;
    }
#endif
    /* Decorate only an existing native prefix widget; never allocate a hidden
     * row or index past the native viewport geometry from this callback. */
    if (!F(0x103fcf3bu, uint32_t, uint32_t, uint32_t, uint32_t)(W(object + 36), 8, 3)) return result;
    uint32_t prefix = F(0x103fcf5du, uint32_t, uint32_t, uint32_t, uint32_t)(W(object + 36), 8, 3);
    if (!prefix) return result;
    uint32_t refresh_prefix = W(prefix + 8) != 46 || W(prefix + 12) != 2;
#ifdef Z7_SETTINGS_ROOT_LABEL_REFRESH
    refresh_prefix |= labels_ready && (sm_root_label_dirty & 2);
#endif
    if (refresh_prefix) sm_bind_text(prefix, 46);
#ifdef Z7_SETTINGS_ROOT_LABEL_REFRESH
    if (labels_ready) sm_root_label_dirty &= ~2u;
#endif
    W(prefix + 0x4c) = (uint32_t)(uintptr_t)sm_root_prefix_paint;
    W(prefix + 0x44) = 1;
    return result;
}
#endif

static uint32_t sm_root_enter(uint32_t object)
{
#ifdef Z7_SETTINGS_ROOT_LABEL_REFRESH
    sm_root_seed_labels(); sm_root_label_widget = 0; sm_root_label_dirty = 3;
#else
    F(0x103fbb5du, void, const char *, uint32_t, uint32_t)("Display settings", 45, 0);
#ifdef Z7_SETTINGS_CATEGORY_ENTRY
    F(0x103fbb5du, void, const char *, uint32_t, uint32_t)("h", 46, 0);
#endif
#endif
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
#ifdef Z7_SETTINGS_CATEGORY_ENTRY
    sm_root_controls[8][4] = 0x1a09;
    /* The value column stays blank. The owned decorator binds h separately. */
    sm_root_controls[8][5] = 0;
    sm_root_callbacks[4] = (uint32_t)(uintptr_t)sm_root_decorate;
#endif
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
