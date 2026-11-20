/* SPDX-License-Identifier: MIT. Independent original-Z7 C3.80 file adapter. */
#ifndef Z7_SETTINGS_FILES_H
#define Z7_SETTINGS_FILES_H
#include "settings_storage.h"
struct z7_settings_files {
    uint32_t magic, retained_fd, native_result, operation, slot;
};
/* Initialize once from zeroed storage. A failed close permanently parks this
 * adapter for this boot; reinitialization cannot discard an uncertain handle.
 * Synchronous calls only on the resident loader/worker task, serialized by the
 * caller. No GUI callbacks, physical flush promise or hot-unload contract.
 */
uint32_t z7_settings_files_init(struct z7_settings_files *);
uint32_t z7_settings_files_read(void *, uint32_t, uint8_t *);
uint32_t z7_settings_files_write(void *, uint32_t, const uint8_t *);
#endif
