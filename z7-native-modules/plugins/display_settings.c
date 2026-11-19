/* SPDX-License-Identifier: MIT. Independent original-Z7 display settings model.
 * Wire format Z7C1, version1, exact64 bytes. CRC detects damage, not authenticity.
 */
#include "display_settings.h"
static const uint32_t default_components[4] = {1, 0, 5, 10};
static const uint32_t default_information[4] = {127, 7, 0, 127};
static uint32_t get32(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static void put32(uint8_t *p, uint32_t v)
{
    for (uint32_t i = 0; i < 4; ++i) p[i] = (uint8_t)(v >> (i * 8));
}
static uint32_t crc(const uint8_t *p)
{
    uint32_t v = 0xffffffffu;
    for (uint32_t i = 0; i < Z7_SETTINGS_BYTES; ++i) {
        v ^= i >= 12 && i < 16 ? 0 : p[i];
        for (uint32_t j = 0; j < 8; ++j) v = (v >> 1) ^ ((0u - (v & 1)) & 0xedb88320u);
    }
    return ~v;
}
void z7_settings_defaults(struct z7_display_settings *s)
{
    if (!s) return;
    s->flags = 0; s->enabled_pages = 15;
    for (uint32_t i = 0; i < 4; ++i) {
        s->components[i] = default_components[i]; s->information[i] = default_information[i];
    }
}
uint32_t z7_settings_valid(const struct z7_display_settings *s)
{
    if (!s || s->flags & ~3u || !s->enabled_pages || s->enabled_pages & ~31u) return 0;
    for (uint32_t i = 0; i < 4; ++i)
        if (s->components[i] & ~15u || s->information[i] & ~255u) return 0;
    return 1;
}
uint32_t z7_settings_encode(const struct z7_display_settings *s, uint8_t *out, uint32_t bytes)
{
    if (!out || bytes != Z7_SETTINGS_BYTES || !z7_settings_valid(s)) return 0;
    /* Stage all bytes before writing so source/output overlap is well-defined. */
    uint8_t packet[Z7_SETTINGS_BYTES];
    put32(packet, 0x3143375au); put32(packet + 4, 1); put32(packet + 8, 0x03800007u);
    put32(packet + 12, 0);
    put32(packet + 16, s->flags); put32(packet + 20, s->enabled_pages);
    put32(packet + 56, 0); put32(packet + 60, 0);
    for (uint32_t i = 0; i < 4; ++i) {
        put32(packet + 24 + i * 4, s->components[i]); put32(packet + 40 + i * 4, s->information[i]);
    }
    put32(packet + 12, crc(packet));
    for (uint32_t i = 0; i < Z7_SETTINGS_BYTES; ++i) out[i] = packet[i];
    return 1;
}
uint32_t z7_settings_decode(const uint8_t *p, uint32_t bytes, struct z7_display_settings *out)
{
    if (!p || !out || bytes != Z7_SETTINGS_BYTES || get32(p) != 0x3143375au ||
        get32(p + 4) != 1 || get32(p + 8) != 0x03800007u || get32(p + 56) || get32(p + 60) || get32(p + 12) != crc(p)) return 0;
    struct z7_display_settings staged;
    staged.flags = get32(p + 16); staged.enabled_pages = get32(p + 20);
    for (uint32_t i = 0; i < 4; ++i) {
        staged.components[i] = get32(p + 24 + i * 4); staged.information[i] = get32(p + 40 + i * 4);
    }
    if (!z7_settings_valid(&staged)) return 0;
    *out = staged;
    return 1;
}
uint32_t z7_settings_page(struct z7_display_settings *s, uint32_t page, uint32_t enabled)
{
    if (!z7_settings_valid(s) || page >= 5 || enabled > 1) return 0;
    uint32_t pages = enabled ? s->enabled_pages | (1u << page) : s->enabled_pages & ~(1u << page);
    if (!pages) return 0;
    s->enabled_pages = pages; return 1;
}
uint32_t z7_settings_reset(struct z7_display_settings *s, uint32_t page)
{
    if (!z7_settings_valid(s) || page >= 4) return 0;
    s->components[page] = default_components[page]; s->information[page] = default_information[page]; return 1;
}
uint32_t z7_settings_next(const struct z7_display_settings *s, uint32_t current)
{
    if (!z7_settings_valid(s) || current >= 5) return Z7_SETTINGS_INVALID;
    for (uint32_t i = 1; i <= 5; ++i) {
        uint32_t next = current + i;
        if (next >= 5) next -= 5;
        if (s->enabled_pages & (1u << next)) return next;
    }
    return Z7_SETTINGS_INVALID;
}
static uint32_t setting_bit(struct z7_display_settings *s, uint32_t page, uint32_t bit, uint32_t enabled, uint32_t information)
{
    if (!z7_settings_valid(s) || page >= 4 || bit >= (information ? 8u : 4u) || enabled > 1) return 0;
    uint32_t *word = information ? &s->information[page] : &s->components[page];
    *word = enabled ? *word | (1u << bit) : *word & ~(1u << bit); return 1;
}
uint32_t z7_settings_information(struct z7_display_settings *s, uint32_t p, uint32_t b, uint32_t e) { return setting_bit(s, p, b, e, 1); }
uint32_t z7_settings_component(struct z7_display_settings *s, uint32_t p, uint32_t b, uint32_t e) { return setting_bit(s, p, b, e, 0); }
uint32_t z7_settings_flag(struct z7_display_settings *s, uint32_t flag, uint32_t enabled)
{
    if (!z7_settings_valid(s) || flag >= 2 || enabled > 1) return 0;
    s->flags = enabled ? s->flags | (1u << flag) : s->flags & ~(1u << flag); return 1;
}
