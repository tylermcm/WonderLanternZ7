/* SPDX-License-Identifier: MIT. Independent original-Z7 C3.80 bindings.
 * Bounded RAM-only stable read for source/consumer callbacks. This is not a
 * native transaction/fence or an epoch publisher. Caller owns out exclusively
 * and must still check mode/output/service/UI/preset policy before ownership.
 */
#ifndef Z7_HIGHLIGHT_CONTEXT_H
#define Z7_HIGHLIGHT_CONTEXT_H
#include <stdint.h>
struct z7_highlight_context {
    uint32_t mode, output_kind, selector, state, source, ready, service;
};
static uint32_t z7_hc_word(uint32_t p)
{ return *(volatile const uint32_t *)(uintptr_t)p; }
static uint32_t z7_hc_byte(uint32_t p)
{ return *(volatile const uint8_t *)(uintptr_t)p; }
static uint32_t z7_hc_ram(uint32_t p, uint32_t n)
{ return !(p & 3) && p >= 0xa1800000u && n <= 0x100000u && p <= 0xc0000000u - n; }
static uint32_t z7_highlight_context_read(struct z7_highlight_context *out)
{
    if (!out) return 0;
    for (uint32_t attempt = 0; attempt < 3; ++attempt) {
        struct z7_highlight_context c;
        c.mode = z7_hc_word(0xa24e1e00u); /* Native property138D descriptor. */
        c.output_kind = z7_hc_word(0xa181c764u);
        c.selector = z7_hc_byte(0xa180a568u);
        c.state = z7_hc_word(0xa180a588u);
        c.service = z7_hc_byte(0xa1d68e54u);
        if (c.selector > 1 || !z7_hc_ram(c.state, 0x22c)) return 0;
        c.source = z7_hc_word(c.state + 8 + c.selector * 4);
        c.ready = z7_hc_word(c.state + 0x228);
        /* Native routing may clear this pointer while leaving downstream
         * mirrors stale. Use the primary selected source, never a mirror. */
        if (!z7_hc_ram(c.source, 16)) return 0;
        uint32_t tag = 0x1062a5b8u + c.selector * 16;
        uint32_t matches = 1;
        for (uint32_t i = 0; i < 16; i += 4)
            if (z7_hc_word(c.source + i) != z7_hc_word(tag + i)) matches = 0;
        if (!matches) return 0;
        __atomic_thread_fence(__ATOMIC_ACQUIRE);
        if (c.mode != z7_hc_word(0xa24e1e00u) ||
            c.output_kind != z7_hc_word(0xa181c764u) ||
            c.selector != z7_hc_byte(0xa180a568u) ||
            c.state != z7_hc_word(0xa180a588u) ||
            c.service != z7_hc_byte(0xa1d68e54u)) continue;
        if (c.source != z7_hc_word(c.state + 8 + c.selector * 4) ||
            c.ready != z7_hc_word(c.state + 0x228)) continue;
        *out = c;
        return 1;
    }
    /* A transition detected on every attempt leaves out untouched. Matching
     * repeated values cannot detect ABA or establish physical frame timing. */
    return 0;
}
#endif
