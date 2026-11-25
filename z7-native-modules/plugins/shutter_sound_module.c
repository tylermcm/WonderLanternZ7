/* SPDX-License-Identifier: MIT.
 * Standalone original-Z7 shutter-sound PLAYBACK trial. There is no photo trigger:
 * this module loads A:\SHUTTER1.WAV and intercepts only its own sound job. The
 * boot-preview variant (shutter_sound_boot_preview.c) queues one preview at init.
 * Offline research build; camera use requires its own review and approval.
 */
#include "module.h"
#include "shutter_sound_playback.h"

static const char z7_sound_path_1[]="A:\\SHUTTER1.WAV";
volatile uint32_t z7_sound_init_result, z7_sound_boot_queued;

/* Offline audit seam; no camera behavior depends on it. */
uint32_t z7_sound_operation(uint32_t op, uint32_t a, uint32_t b, uint32_t c)
{
    switch (op) {
    case 1: return z7_sound_enqueue(a,b,c);
    case 2: return z7_sound_decode((const uint8_t *)(uintptr_t)a,b,(int16_t *)(uintptr_t)c);
    case 3: return z7_sound_native_matches();
    default: return 0;
    }
}

uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET || api->size<12) return 1;
    /* Fail closed on any firmware mismatch before touching files or slots. */
    if (!z7_sound_native_matches()) return 1;
    z7_sound_init_result=z7_sound_load(0,z7_sound_path_1) ? 1u : 0u;
    if (z7_sound_init_result) z7_sound_init_result|=z7_sound_install()<<1;
#ifdef Z7_SOUND_BOOT_PREVIEW
    z7_sound_boot_queued=z7_sound_enqueue(0,SND_VOLUME_MAX,1);
#endif
    return 0;
}
