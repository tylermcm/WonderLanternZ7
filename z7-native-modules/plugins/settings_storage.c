/* SPDX-License-Identifier: MIT. Independent two-slot settings transaction.
 * Z7J1 wraps the unchanged64-byte Z7C1 payload. No native camera addresses.
 */
#include "settings_storage.h"
static uint32_t journal_get32(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static void journal_put32(uint8_t *p, uint32_t value)
{
    for (uint32_t i = 0; i < 4; ++i) p[i] = (uint8_t)(value >> (8 * i));
}
static uint32_t journal_crc(const uint8_t *p)
{
    uint32_t value = 0xffffffffu;
    for (uint32_t i = 0; i < Z7_SETTINGS_RECORD_BYTES; ++i) {
        value ^= i >= 12 && i < 16 ? 0 : p[i];
        for (uint32_t j = 0; j < 8; ++j) value = (value >> 1) ^ ((0u - (value & 1)) & 0xedb88320u);
    }
    return ~value;
}
static uint32_t journal_equal(const uint8_t *a, const uint8_t *b, uint32_t bytes)
{
    for (uint32_t i = 0; i < bytes; ++i) if (a[i] != b[i]) return 0;
    return 1;
}
uint32_t z7_storage_record_encode(const struct z7_display_settings *s, uint32_t generation, uint8_t *out, uint32_t bytes)
{
    if (!out || bytes != Z7_SETTINGS_RECORD_BYTES) return 0;
    uint8_t record[Z7_SETTINGS_RECORD_BYTES];
    if (!z7_settings_encode(s, record + 16, Z7_SETTINGS_BYTES)) return 0;
    journal_put32(record, 0x314a375au); journal_put32(record + 4, 1);
    journal_put32(record + 8, generation); journal_put32(record + 12, 0);
    journal_put32(record + 12, journal_crc(record));
    for (uint32_t i = 0; i < bytes; ++i) out[i] = record[i];
    return 1;
}
uint32_t z7_storage_record_decode(const uint8_t *p, uint32_t bytes, struct z7_display_settings *out, uint32_t *generation)
{
    if (!p || !out || !generation || bytes != Z7_SETTINGS_RECORD_BYTES ||
        journal_get32(p) != 0x314a375au || journal_get32(p + 4) != 1 || journal_get32(p + 12) != journal_crc(p)) return 0;
    struct z7_display_settings settings;
    uint32_t serial = journal_get32(p + 8);
    if (!z7_settings_decode(p + 16, Z7_SETTINGS_BYTES, &settings)) return 0;
    *out = settings; *generation = serial;
    return 1;
}
static uint32_t journal_scan(const struct z7_settings_storage_io *io, uint8_t records[2][Z7_SETTINGS_RECORD_BYTES], struct z7_settings_storage_info *info)
{
    uint32_t serial[2] = {0, 0};
    struct z7_display_settings settings;
    info->valid_slots = info->io_error_slots = info->generation = 0;
    info->active_slot = 2;
    for (uint32_t slot = 0; slot < 2; ++slot) {
        uint32_t result = io->read(io->context, slot, records[slot]);
        if (result != Z7_STORAGE_IO_OK && result != Z7_STORAGE_IO_ABSENT && result != Z7_STORAGE_IO_INVALID) info->io_error_slots |= 1u << slot;
        if (result == Z7_STORAGE_IO_OK && z7_storage_record_decode(records[slot], Z7_SETTINGS_RECORD_BYTES, &settings, &serial[slot]))
            info->valid_slots |= 1u << slot;
    }
    if (!info->valid_slots) return info->io_error_slots ? Z7_STORAGE_IO_FAILED : Z7_STORAGE_DEFAULTS;
    uint32_t active = info->valid_slots == 2;
    if (info->valid_slots == 3) {
        uint32_t distance = serial[1] - serial[0];
        if ((!distance && !journal_equal(records[0], records[1], Z7_SETTINGS_RECORD_BYTES)) || distance == 0x80000000u)
            return Z7_STORAGE_AMBIGUOUS;
        active = distance && distance < 0x80000000u;
    }
    info->active_slot = active;
    info->generation = serial[active];
    return Z7_STORAGE_LOADED;
}
uint32_t z7_storage_load(const struct z7_settings_storage_io *io, struct z7_display_settings *out, struct z7_settings_storage_info *info)
{
    if (!io || !io->read || !out || !info) return Z7_STORAGE_INVALID;
    uint8_t records[2][Z7_SETTINGS_RECORD_BYTES];
    struct z7_settings_storage_info found;
    uint32_t result = journal_scan(io, records, &found);
    struct z7_display_settings settings;
    if (result == Z7_STORAGE_LOADED)
        z7_settings_decode(records[found.active_slot] + 16, Z7_SETTINGS_BYTES, &settings);
    else if (result == Z7_STORAGE_DEFAULTS) z7_settings_defaults(&settings);
    else { *info = found; return result; }
    *out = settings; *info = found;
    return result;
}
uint32_t z7_storage_save(const struct z7_settings_storage_io *io, const struct z7_display_settings *s, struct z7_settings_storage_info *info)
{
    if (!io || !io->read || !io->write || !info || !z7_settings_valid(s)) return Z7_STORAGE_INVALID;
    /* Encode before I/O so a transport callback cannot change this snapshot. */
    uint8_t desired[Z7_SETTINGS_BYTES], records[2][Z7_SETTINGS_RECORD_BYTES], pending[Z7_SETTINGS_RECORD_BYTES];
    z7_settings_encode(s, desired, Z7_SETTINGS_BYTES);
    struct z7_settings_storage_info found;
    uint32_t result = journal_scan(io, records, &found);
    *info = found;
    if (found.io_error_slots) return Z7_STORAGE_IO_FAILED;
    if (result == Z7_STORAGE_AMBIGUOUS) return result;
    if (found.active_slot < 2 && journal_equal(desired, records[found.active_slot] + 16, Z7_SETTINGS_BYTES)) return Z7_STORAGE_UNCHANGED;
    uint32_t slot = found.active_slot < 2 ? found.active_slot ^ 1u : 0;
    uint32_t serial = found.active_slot < 2 ? found.generation + 1 : 0;
    journal_put32(pending, 0x314a375au); journal_put32(pending + 4, 1);
    journal_put32(pending + 8, serial); journal_put32(pending + 12, 0);
    for (uint32_t i = 0; i < Z7_SETTINGS_BYTES; ++i) pending[16 + i] = desired[i];
    journal_put32(pending + 12, journal_crc(pending));
    if (io->write(io->context, slot, pending) != Z7_STORAGE_IO_OK) return Z7_STORAGE_IO_FAILED;
    if (io->read(io->context, slot, records[slot]) != Z7_STORAGE_IO_OK ||
        !journal_equal(pending, records[slot], Z7_SETTINGS_RECORD_BYTES)) return Z7_STORAGE_VERIFY_FAILED;
    info->valid_slots |= 1u << slot; info->active_slot = slot; info->generation = serial;
    return Z7_STORAGE_SAVED;
}
