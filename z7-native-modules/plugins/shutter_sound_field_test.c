/* SPDX-License-Identifier: MIT.
 * Original-Z7 shutter-sound FIELD TEST: one module, one camera session.
 *  - Playback smoke test: loads A:\SHUTTER1.WAV, installs the private playback
 *    intercept and queues one preview on resident-worker tick 8.
 *  - Trigger probe: wraps the three capture callbacks and logs events to
 *    A:\Z7TRIG.DAT (shutter_trigger_probe.h).
 *  - The log header also carries the sound counters, so a silent preview can be
 *    diagnosed from the card: queued, started, rejected, finished, and native
 *    requests that passed through the intercept.
 * No photo-triggered sound. Never writes any other file.
 */
#include "shutter_trigger_probe.h"
#include "shutter_sound_playback.h"

#ifndef Z7_SOUND_PREVIEW_TICK
#define Z7_SOUND_PREVIEW_TICK 8u
#endif
static const char z7_sound_path_1[]="A:\\SHUTTER1.WAV";
volatile uint32_t z7_sound_init_result, z7_sound_boot_queued, z7_field_preview_tick;

/* Header words 13..15 (reserved in the probe-only module). */
static void z7_field_publish(void)
{
    uint32_t words[3]={
        (z7_sound_boot_queued&0xffu)|((z7_sound_installed&0xffu)<<8)|((z7_sound_init_result&0xffu)<<16)|(1u<<24),
        (z7_sound_starts&0xffffu)|((z7_sound_rejects&0xffffu)<<16),
        (z7_sound_finished&0xffffu)|((z7_sound_passthrough&0xffffu)<<16)};
    for (uint32_t i=0;i<3;++i)
        if (z7_trig_live.reserved[i]!=words[i]) {
            z7_trig_live.reserved[i]=words[i];
            __atomic_store_n(&z7_trig_dirty,1,__ATOMIC_RELEASE);
        }
}

static void z7_field_worker(void)
{
    z7_trig_worker();
    uint32_t tick=__atomic_load_n(&z7_trig_live.ticks,__ATOMIC_RELAXED);
    if (tick==Z7_SOUND_PREVIEW_TICK && !z7_field_preview_tick) {
        z7_field_preview_tick=tick;
        z7_sound_boot_queued=!z7_sound_installed ? 4u : z7_sound_enqueue(0,SND_VOLUME_MAX,1) ? 1u : 2u;
    }
    z7_field_publish();
}

uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET ||
        api->size<sizeof(struct z7_module_worker_api)) return 1;
    /* Fail closed on any firmware mismatch before touching files or slots. */
    if (!z7_trig_matches() || !z7_sound_native_matches()) return 1;
    if (!((const struct z7_module_worker_api *)api)->register_worker(z7_field_worker)) return 1;
    z7_sound_init_result=z7_sound_load(0,z7_sound_path_1) ? 1u : 0u;
    if (z7_sound_init_result) z7_sound_init_result|=z7_sound_install()<<1;
    z7_trig_install();
    z7_field_publish();
    return 0;
}
