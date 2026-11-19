/* SPDX-License-Identifier: MIT. Original-Z7 GUI-phase clean-DISP experiment.
 * Included after battery/grid definitions; no firmware mask/pixel patch.
 */
volatile uint32_t z7_clean_request, z7_clean_active, z7_clean_brackets_hidden;
static uint32_t clean_masks[61][9];
static uint32_t clean_descriptors[61];
static uint32_t clean_brackets[4], clean_visibility[4];
static uint32_t clean_context(void)
{
    if (z7_clean_request != 1 || B(0xa18237c6u) || B(0xa201d4d0u + 0x40) || !pool()) return 0;
    uint32_t pages = W(0xa181f91cu);
    return pages && ram(pages, 16) && !W(pages + 8);
}
static void clean_before(void)
{
    before();
    uint32_t desired = clean_context();
    /* Validate every descriptor before any store. */
    for (uint32_t i = 0; i < 61; ++i) {
        uint32_t p = W(0x1064d610u + i * 4);
        if (!ram(p, 48) || (z7_clean_active && p != clean_descriptors[i])) desired = 0;
    }
    if (desired && !z7_clean_active) {
        for (uint32_t i = 0; i < 61; ++i) {
            uint32_t p = W(0x1064d610u + i * 4);
            clean_descriptors[i] = p;
            for (uint32_t j = 0; j < 9; ++j) {
                clean_masks[i][j] = W(p + 4 + j * 4);
                W(p + 4 + j * 4) = clean_masks[i][j] & ~0x22222u;
            }
        }
        z7_clean_active = 1;
    } else if (!desired && z7_clean_active) {
        for (uint32_t i = 0; i < 61; ++i) {
            uint32_t p = clean_descriptors[i];
            if (W(0x1064d610u + i * 4) != p) continue;
            for (uint32_t j = 0; j < 9; ++j)
                if (W(p + 4 + j * 4) == (clean_masks[i][j] & ~0x22222u)) W(p + 4 + j * 4) = clean_masks[i][j];
        }
        z7_clean_active = 0;
    }
    uint32_t hide = desired && B(0xa201d4d0u + 0x18a) == 1;
    for (uint32_t i = 0; i < 4; ++i) {
        uint32_t control = 0xa1824684u + (i + 1) * 48, object = W(control + 36);
        if (!ram(object, 284) || W(object + 0x48) != 0xa201e3b4u ||
            W(object + 0x4c) != 0x10384969u || *(volatile uint16_t *)(uintptr_t)(object + 4) != 4) continue;
        if (hide) {
            if (clean_brackets[i] != object) {
                clean_brackets[i] = object; clean_visibility[i] = W(object + 40);
            }
            F(0x103fb32fu, uint32_t, uint32_t, uint32_t)(object, 0);
            ++z7_clean_brackets_hidden;
        } else if (clean_brackets[i] == object) {
            F(0x103fb32fu, uint32_t, uint32_t, uint32_t)(object, clean_visibility[i]);
            clean_brackets[i] = 0;
        }
    }
}
#ifdef Z7_DISP_KEY_PROBE
volatile uint32_t z7_disp_key_enabled, z7_disp_key_accepted, z7_disp_key_rejected;
static uint32_t clean_key(uint32_t key, uint32_t a, uint32_t b, uint32_t c)
{
    /* Run the exact native outer callback and its inner admission/cycle first.
     * A blocked button must never activate this diagnostic. No admission service
     * is replaced or forced. Non-DISP keys retain their original result.
     */
    uint32_t old_mode = B(0xa201d4d0u + 0x18a);
    uint32_t result = F(0x1030da57u, uint32_t, uint32_t, uint32_t, uint32_t, uint32_t)(key, a, b, c);
    uint32_t new_mode = B(0xa201d4d0u + 0x18a);
    if (key == 0x29 && z7_disp_key_enabled == 1 && old_mode <= 4 && new_mode != old_mode &&
        !B(0xa18237c6u) && !B(0xa201d4d0u + 0x40) && pool()) {
        uint32_t pages = W(0xa181f91cu);
        if (pages && ram(pages, 16) && !W(pages + 8)) {
            ++z7_disp_key_accepted;
            return result;
        }
    }
    if (key == 0x29) ++z7_disp_key_rejected;
    return result;
}
static void disp_key_before(void)
{
    /* Prime only the simplified-state mask bits before the next native button
     * event. Other DISP states retain those masks' original bits. This avoids
     * changing eligibility after the native key callback already laid out page1.
     */
    z7_clean_request = z7_disp_key_enabled == 1;
    clean_before();
}
#endif
