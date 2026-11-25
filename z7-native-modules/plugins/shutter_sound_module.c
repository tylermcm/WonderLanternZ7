/* SPDX-License-Identifier: MIT.
 * Standalone original-Z7 shutter-sound PLAYBACK trial. There is no photo trigger:
 * this module loads A:\SHUTTER1.WAV and intercepts only its own sound job. The
 * boot-preview variant (shutter_sound_boot_preview.c) queues one preview a few
 * resident-worker ticks after load. Camera use requires its own review and approval.
 */
#include "module.h"
#include "worker.h"
#include "shutter_sound_playback.h"

static const char z7_sound_path_1[]="A:\\SHUTTER1.WAV";
volatile uint32_t z7_sound_init_result, z7_sound_boot_queued, z7_sound_worker_ticks;

#ifdef Z7_SOUND_BOOT_PREVIEW
/* The preview waits for the resident worker instead of playing during module
 * load, so the camera's GUI and audio path have finished starting. One attempt
 * only: boot_queued is 1 when queued, 2 when refused; never retried. */
#ifndef Z7_SOUND_PREVIEW_TICK
#define Z7_SOUND_PREVIEW_TICK 8u
#endif
static void z7_sound_worker(void)
{
    uint32_t ticks=z7_sound_worker_ticks;
    if (ticks>=Z7_SOUND_PREVIEW_TICK) return;
    z7_sound_worker_ticks=++ticks;
    if (ticks==Z7_SOUND_PREVIEW_TICK && z7_sound_installed)
        z7_sound_boot_queued=z7_sound_enqueue(0,SND_VOLUME_MAX,1)?1u:2u;
}
#endif

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
#ifdef Z7_SOUND_BOOT_PREVIEW
    /* The preview needs the 44-byte worker API; refuse older hosts up front. */
    if (api->size<sizeof(struct z7_module_worker_api)) return 1;
#endif
    /* Fail closed on any firmware mismatch before touching files or slots. */
    if (!z7_sound_native_matches()) return 1;
    z7_sound_init_result=z7_sound_load(0,z7_sound_path_1) ? 1u : 0u;
    if (z7_sound_init_result) z7_sound_init_result|=z7_sound_install()<<1;
#ifdef Z7_SOUND_BOOT_PREVIEW
    if (z7_sound_installed &&
        !((const struct z7_module_worker_api *)api)->register_worker(z7_sound_worker))
        z7_sound_boot_queued=3u;  /* worker refused: installed, no preview */
#endif
    return 0;
}
