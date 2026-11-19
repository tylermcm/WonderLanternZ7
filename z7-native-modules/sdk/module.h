/* SPDX-License-Identifier: MIT
 * Independent original-Z7 research, derived from JKWTCN's Z7II module format.
 * Copyright (c) 2026 JKWTCN; modifications (c) 2026 WonderLanternZ7 contributors.
 */
#ifndef Z7_MODULE_H
#define Z7_MODULE_H
#include <stdint.h>

#define Z7_MODULE_ABI 1u
#define Z7_MODULE_TARGET 0x03800007u /* Original Z7 C 3.80, experimental ABI. */
#define Z7_MODULE_HEADER 64u
#define Z7_MODULE_MAX_FILE (1u << 20)
#define Z7_MODULE_MAX_MEMORY (4u << 20)

struct z7_display_hooks;
struct z7_grid_menu;
/* This ABI is deliberately separate
 * from Z7II. Modules are trusted native code and must return from init.
 * On failure, init must leave no tasks, callbacks or other retained pointers.
 */
struct z7_module_api {
    uint32_t abi, size, target;
    uint32_t (*register_display)(const struct z7_display_hooks *hooks);
    uint32_t (*register_grid_menu)(const struct z7_grid_menu *menu);
};
uint32_t z7_main(const struct z7_module_api *api);

struct z7_module_info {
    uint32_t image_size, bss_size, entry_offset, relocation_count;
};
enum z7_module_status {
    Z7_MOD_OK = 0,
    Z7_MOD_BAD_BUFFER,
    Z7_MOD_BAD_HEADER,
    Z7_MOD_BAD_CRC,
    Z7_MOD_BAD_RELOCATION,
    Z7_MOD_BAD_DESTINATION
};

/* Firmware-independent parsing/relocation core. Inputs must remain immutable
 * during the call; info must be separate from both buffers. On any error the
 * destination and info are untouched. No allocation, file access or execution.
 */
uint32_t z7_module_validate(const uint8_t *raw, uint32_t size,
                            struct z7_module_info *info);
/* runtime_base is the intended 32-bit execution address. The caller owns the
 * destination and is responsible for mapping it there and publishing caches.
 * Raw bytes and destination must not overlap. No unload protocol is provided.
 */
uint32_t z7_module_prepare(const uint8_t *raw, uint32_t size,
                          uint8_t *destination, uint32_t capacity,
                          uint32_t runtime_base, struct z7_module_info *info);
#endif
