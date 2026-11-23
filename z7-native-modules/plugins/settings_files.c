/* SPDX-License-Identifier: MIT. Independent original-Z7 C3.80 bindings.
 * Original wrappers/cache instructions are instruction-audited with supplied
 * filesystem/sector boundaries. Real card/cache durability is unverified.
 */
#include "settings_files.h"
#define FILE_FN(a, result, ...) ((result (*)(__VA_ARGS__))(uintptr_t)(a))
#define FILE_STATE_MAGIC 0x3146535au
#define FILE_NOT_FOUND 0x80000010u
#ifndef Z7_SETTINGS_SLOT0_PATH
#define Z7_SETTINGS_SLOT0_PATH "A:\\Z7CFG0.DAT"
#endif
#ifndef Z7_SETTINGS_SLOT1_PATH
#define Z7_SETTINGS_SLOT1_PATH "A:\\Z7CFG1.DAT"
#endif
static const char *settings_slot_path(uint32_t slot)
{
#ifdef Z7_SETTINGS_SLOT_PATH_HOOK
    return Z7_SETTINGS_SLOT_PATH_HOOK(slot);
#else
    return slot ? Z7_SETTINGS_SLOT1_PATH : Z7_SETTINGS_SLOT0_PATH;
#endif
}
uint32_t z7_settings_files_init(struct z7_settings_files *s)
{
    if (!s || s->magic) return 0;
    s->retained_fd = UINT32_MAX;
    s->native_result = s->operation = s->slot = 0;
    s->magic = FILE_STATE_MAGIC;
    return 1;
}
static uint32_t settings_files_ready(struct z7_settings_files *s, uint32_t slot, const void *data)
{
    return s && s->magic == FILE_STATE_MAGIC && s->retained_fd == UINT32_MAX && slot < 2 && data;
}
static uint32_t settings_files_close(struct z7_settings_files *s, uint32_t fd)
{
    uint32_t result = FILE_FN(0x1027bfcdu, uint32_t, uint32_t)(fd);
    if (!result) return 1;
    s->native_result = result;
    s->retained_fd = fd;
    return 0;
}
uint32_t z7_settings_files_read(void *context, uint32_t slot, uint8_t *out)
{
    struct z7_settings_files *s = context;
    if (!settings_files_ready(s, slot, out)) return Z7_STORAGE_IO_ERROR;
    s->operation = 0; s->slot = slot;
    uint32_t fd = FILE_FN(0x1027bfa3u, uint32_t, const char *, uint32_t, uint32_t)(settings_slot_path(slot), 0, 0);
    s->native_result = fd;
    if ((int32_t)fd < 0) return fd == FILE_NOT_FOUND ? Z7_STORAGE_IO_ABSENT : Z7_STORAGE_IO_ERROR;
    /* Native line helpers touch an extra line beyond the byte request. */
    _Alignas(64) uint8_t staging[192];
    uint32_t actual = 0;
    FILE_FN(0x101e9f77u, void, void *, uint32_t)(staging, Z7_SETTINGS_RECORD_BYTES + 1);
    uint32_t result = FILE_FN(0x1027c019u, uint32_t, uint32_t, void *, uint32_t, uint32_t *)(fd, staging, Z7_SETTINGS_RECORD_BYTES + 1, &actual);
    FILE_FN(0x101e9f77u, void, void *, uint32_t)(staging, Z7_SETTINGS_RECORD_BYTES + 1);
    s->native_result = result;
    if (!settings_files_close(s, fd) || result || actual > Z7_SETTINGS_RECORD_BYTES + 1) return Z7_STORAGE_IO_ERROR;
    if (actual != Z7_SETTINGS_RECORD_BYTES) return Z7_STORAGE_IO_INVALID;
    for (uint32_t i = 0; i < Z7_SETTINGS_RECORD_BYTES; ++i) out[i] = staging[i];
    return Z7_STORAGE_IO_OK;
}
#ifndef Z7_SETTINGS_READ_ONLY
uint32_t z7_settings_files_write(void *context, uint32_t slot, const uint8_t *record)
{
    struct z7_settings_files *s = context;
    if (!settings_files_ready(s, slot, record)) return Z7_STORAGE_IO_ERROR;
    s->operation = 1; s->slot = slot;
    _Alignas(64) uint8_t staging[192];
    for (uint32_t i = 0; i < Z7_SETTINGS_RECORD_BYTES; ++i) staging[i] = record[i];
    uint32_t fd = FILE_FN(0x1027c0dbu, uint32_t, const char *, uint32_t)(settings_slot_path(slot), 0);
    s->native_result = fd;
    if ((int32_t)fd < 0) return Z7_STORAGE_IO_ERROR;
    uint32_t actual = 0;
    FILE_FN(0x101e9f39u, void, void *, uint32_t)(staging, Z7_SETTINGS_RECORD_BYTES);
    uint32_t result = FILE_FN(0x1027c049u, uint32_t, uint32_t, const void *, uint32_t, uint32_t *)(fd, staging, Z7_SETTINGS_RECORD_BYTES, &actual);
    s->native_result = result;
    if (!settings_files_close(s, fd) || result || actual != Z7_SETTINGS_RECORD_BYTES) return Z7_STORAGE_IO_ERROR;
    return Z7_STORAGE_IO_OK;
}
#endif
