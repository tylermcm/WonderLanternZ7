/* SPDX-License-Identifier: MIT
 * Independent original-Z7 adaptation of the validation and relocation logic
 * in JKWTCN/z7ii-extensions host/host.c, commit 50a22b24c50619cffa646dac386e8334659f475a.
 * Copyright (c) 2026 JKWTCN; modifications (c) 2026 WonderLanternZ7 contributors.
 */
#include "module.h"

static uint32_t word(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 |
           (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static void put_word(uint8_t *p, uint32_t value)
{
    for (uint32_t i = 0; i < 4; ++i) p[i] = (uint8_t)(value >> (8 * i));
}
static uint32_t checksum(const uint8_t *data, uint32_t size)
{
    uint32_t crc = ~0u;
    for (uint32_t i = 0; i < size; ++i) {
        crc ^= i >= 32 && i < 36 ? 0 : data[i];
        for (uint32_t bit = 0; bit < 8; ++bit)
            crc = (crc >> 1) ^ ((0u - (crc & 1)) & 0xedb88320u);
    }
    return ~crc;
}
uint32_t z7_module_validate(const uint8_t *raw, uint32_t size,
                            struct z7_module_info *info)
{
    if (!raw || !info) return Z7_MOD_BAD_BUFFER;
    if (size < Z7_MODULE_HEADER || size > Z7_MODULE_MAX_FILE)
        return Z7_MOD_BAD_HEADER;
    uint32_t image = word(raw + 16), bss = word(raw + 20);
    uint32_t entry = word(raw + 24), count = word(raw + 28);
    if (word(raw) != 0x314d375au || word(raw + 4) != Z7_MODULE_ABI ||
        word(raw + 8) != Z7_MODULE_TARGET || word(raw + 12) != size ||
        !image || image % 64 || image > Z7_MODULE_MAX_FILE - Z7_MODULE_HEADER ||
        bss > Z7_MODULE_MAX_MEMORY - image || entry % 2 || entry >= image ||
        count > (Z7_MODULE_MAX_FILE - Z7_MODULE_HEADER - image) / 4 ||
        size != Z7_MODULE_HEADER + image + 4 * count)
        return Z7_MOD_BAD_HEADER;
    for (uint32_t i = 36; i < Z7_MODULE_HEADER; i += 4)
        if (word(raw + i)) return Z7_MOD_BAD_HEADER;
    if (checksum(raw, size) != word(raw + 32)) return Z7_MOD_BAD_CRC;
    uint32_t previous = 0;
    for (uint32_t i = 0; i < count; ++i) {
        uint32_t offset = word(raw + Z7_MODULE_HEADER + image + 4 * i);
        if (offset % 4 || offset > image - 4 || (i && offset <= previous) ||
            word(raw + Z7_MODULE_HEADER + offset) >= image + bss)
            return Z7_MOD_BAD_RELOCATION;
        previous = offset;
    }
    const struct z7_module_info result = {image, bss, entry, count};
    *info = result;
    return Z7_MOD_OK;
}
uint32_t z7_module_prepare(const uint8_t *raw, uint32_t size,
                          uint8_t *destination, uint32_t capacity,
                          uint32_t runtime_base, struct z7_module_info *info)
{
    if (!destination || !info) return Z7_MOD_BAD_BUFFER;
    struct z7_module_info parsed;
    uint32_t status = z7_module_validate(raw, size, &parsed);
    if (status) return status;
    uint32_t memory = parsed.image_size + parsed.bss_size;
    if (capacity < memory || runtime_base % 64 || !runtime_base ||
        runtime_base > UINT32_MAX - memory)
        return Z7_MOD_BAD_DESTINATION;
    uintptr_t source = (uintptr_t)raw, target = (uintptr_t)destination;
    if ((source <= target && target - source < size) ||
        (target < source && source - target < memory))
        return Z7_MOD_BAD_DESTINATION;
    /* All validation, including every relocation, precedes the first write. */
    for (uint32_t i = 0; i < parsed.image_size; ++i)
        destination[i] = raw[Z7_MODULE_HEADER + i];
    for (uint32_t i = parsed.image_size; i < memory; ++i) destination[i] = 0;
    for (uint32_t i = 0; i < parsed.relocation_count; ++i) {
        uint32_t offset = word(raw + Z7_MODULE_HEADER + parsed.image_size + 4 * i);
        put_word(destination + offset, word(destination + offset) + runtime_base);
    }
    *info = parsed;
    return Z7_MOD_OK;
}
