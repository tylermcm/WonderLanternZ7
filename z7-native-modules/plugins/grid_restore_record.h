/* SPDX-License-Identifier: MIT. Independent fixed-size read-only grid seed. */
#ifndef Z7_GRID_RESTORE_RECORD_H
#define Z7_GRID_RESTORE_RECORD_H
#include <stdint.h>
static uint32_t restore_get32(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1]<<8 | (uint32_t)p[2]<<16 | (uint32_t)p[3]<<24;
}
__attribute__((noinline)) uint32_t checkpoint_grid_record_decode(
    const uint8_t *p, uint32_t bytes, uint32_t *choice)
{
    if (!p || !choice || bytes != 80 || restore_get32(p) != 0x3147375au ||
        restore_get32(p+4) != 1 || restore_get32(p+8) != 80) return 0;
    uint32_t value=restore_get32(p+16), crc=0xffffffffu;
    if (value < 1 || value > 5) return 0;
    for (uint32_t i=20; i<80; ++i) if (p[i]) return 0;
    for (uint32_t i=0; i<80; ++i) {
        crc ^= i >= 12 && i < 16 ? 0 : p[i];
        for (uint32_t bit=0; bit<8; ++bit) crc=(crc>>1)^((0u-(crc&1))&0xedb88320u);
    }
    if (~crc != restore_get32(p+12)) return 0;
    *choice=value;
    return 1;
}
#endif
