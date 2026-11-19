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
