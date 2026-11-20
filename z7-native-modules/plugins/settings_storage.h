/* SPDX-License-Identifier: MIT. Independent original-Z7 settings journal. */
#ifndef Z7_SETTINGS_STORAGE_H
#define Z7_SETTINGS_STORAGE_H
#include "display_settings.h"
#define Z7_SETTINGS_RECORD_BYTES 80u
/* Transport operations concern exactly one owned slot. Read must distinguish
 * confirmed absence and a completed wrong-length read from other errors.
 * IO_OK means exactly80 bytes; IO_INVALID means a known unusable record length.
 * Write must replace only that slot and report short write/close failures.
 * No operation may modify the other slot. Caller serializes operations and
 * supplies a coherent settings snapshot; this is not a filesystem durability
 * guarantee or an implementation of native file/cache/shutdown contracts.
 * Buffers must have the declared capacity/alignment. The record codecs support
 * overlapping settings/record storage; generation output must be separate.
 * The I/O table, context and info must not alias settings or transport buffers.
 */
enum z7_storage_io_result { Z7_STORAGE_IO_OK, Z7_STORAGE_IO_ABSENT, Z7_STORAGE_IO_ERROR, Z7_STORAGE_IO_INVALID };
struct z7_settings_storage_io {
    void *context;
    uint32_t (*read)(void *, uint32_t slot, uint8_t record[Z7_SETTINGS_RECORD_BYTES]);
    uint32_t (*write)(void *, uint32_t slot, const uint8_t record[Z7_SETTINGS_RECORD_BYTES]);
};
enum z7_storage_result {
    Z7_STORAGE_LOADED, Z7_STORAGE_DEFAULTS, Z7_STORAGE_IO_FAILED,
    Z7_STORAGE_AMBIGUOUS, Z7_STORAGE_INVALID, Z7_STORAGE_SAVED,
    Z7_STORAGE_UNCHANGED, Z7_STORAGE_VERIFY_FAILED
};
struct z7_settings_storage_info {
    uint32_t valid_slots, io_error_slots, active_slot, generation;
};
uint32_t z7_storage_record_encode(const struct z7_display_settings *, uint32_t generation, uint8_t *, uint32_t bytes);
uint32_t z7_storage_record_decode(const uint8_t *, uint32_t bytes, struct z7_display_settings *, uint32_t *generation);
uint32_t z7_storage_load(const struct z7_settings_storage_io *, struct z7_display_settings *, struct z7_settings_storage_info *);
uint32_t z7_storage_save(const struct z7_settings_storage_io *, const struct z7_display_settings *, struct z7_settings_storage_info *);
#endif
