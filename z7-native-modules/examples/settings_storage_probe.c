/* SPDX-License-Identifier: MIT. In-memory transport for ARM policy checks.
 * These buffers model two files; no camera filesystem function is called.
 */
#include "module.h"
#include "../plugins/display_settings.c"
#include "../plugins/settings_storage.c"
uint8_t z7_storage_probe_slots[2][Z7_SETTINGS_RECORD_BYTES];
uint8_t z7_storage_probe_record[Z7_SETTINGS_RECORD_BYTES];
uint32_t z7_storage_probe_status[2];
uint32_t z7_storage_probe_reads, z7_storage_probe_writes, z7_storage_probe_last_slot;
uint32_t z7_storage_probe_write_prefix, z7_storage_probe_write_result, z7_storage_probe_read_error;
uint32_t z7_storage_probe_mutate_on_read, z7_storage_probe_generation;
struct z7_display_settings z7_storage_probe_model, z7_storage_probe_output;
struct z7_settings_storage_info z7_storage_probe_info;
static uint32_t storage_read(void *context, uint32_t slot, uint8_t *record)
{
    (void)context;
    ++z7_storage_probe_reads;
    if (slot > 1 || z7_storage_probe_reads == z7_storage_probe_read_error) return Z7_STORAGE_IO_ERROR;
    if (z7_storage_probe_mutate_on_read) {
        z7_storage_probe_mutate_on_read = 0;
        z7_storage_probe_model.flags ^= 3;
    }
    if (z7_storage_probe_status[slot] != Z7_STORAGE_IO_OK) return z7_storage_probe_status[slot];
    for (uint32_t i = 0; i < Z7_SETTINGS_RECORD_BYTES; ++i) record[i] = z7_storage_probe_slots[slot][i];
    return Z7_STORAGE_IO_OK;
}
static uint32_t storage_write(void *context, uint32_t slot, const uint8_t *record)
{
    (void)context;
    ++z7_storage_probe_writes;
    z7_storage_probe_last_slot = slot;
    if (slot > 1 || z7_storage_probe_write_prefix > Z7_SETTINGS_RECORD_BYTES) return Z7_STORAGE_IO_ERROR;
    for (uint32_t i = 0; i < z7_storage_probe_write_prefix; ++i) z7_storage_probe_slots[slot][i] = record[i];
    z7_storage_probe_status[slot] = Z7_STORAGE_IO_OK;
    return z7_storage_probe_write_result;
}
static const struct z7_settings_storage_io storage_io = {0, storage_read, storage_write};
uint32_t z7_storage_probe_load(void) { return z7_storage_load(&storage_io, &z7_storage_probe_output, &z7_storage_probe_info); }
uint32_t z7_storage_probe_save(void) { return z7_storage_save(&storage_io, &z7_storage_probe_model, &z7_storage_probe_info); }
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi != Z7_MODULE_ABI || api->target != Z7_MODULE_TARGET || api->size < 12) return 1;
    z7_storage_probe_status[0] = z7_storage_probe_status[1] = Z7_STORAGE_IO_ABSENT;
    z7_storage_probe_write_prefix = Z7_SETTINGS_RECORD_BYTES;
    z7_settings_defaults(&z7_storage_probe_model);
    return 0;
}
