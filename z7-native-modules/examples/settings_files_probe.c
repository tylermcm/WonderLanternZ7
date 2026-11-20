/* SPDX-License-Identifier: MIT. Original-Z7 native-file instruction diagnostic.
 * No hooks registered. The audit supplies the native filesystem dispatcher.
 */
#include "module.h"
#include "../plugins/display_settings.c"
#include "../plugins/settings_storage.c"
#include "../plugins/settings_files.c"
struct z7_settings_files z7_files_probe_state;
uint8_t z7_files_probe_record[Z7_SETTINGS_RECORD_BYTES];
struct z7_display_settings z7_files_probe_model;
struct z7_settings_storage_info z7_files_probe_info;
static const struct z7_settings_storage_io files_io = {
    &z7_files_probe_state, z7_settings_files_read, z7_settings_files_write
};
uint32_t z7_files_probe_load(void) { return z7_storage_load(&files_io, &z7_files_probe_model, &z7_files_probe_info); }
uint32_t z7_files_probe_save(void) { return z7_storage_save(&files_io, &z7_files_probe_model, &z7_files_probe_info); }
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi != Z7_MODULE_ABI || api->target != Z7_MODULE_TARGET || api->size < 12) return 1;
    z7_settings_defaults(&z7_files_probe_model);
    return z7_settings_files_init(&z7_files_probe_state) ? 0 : 1;
}
