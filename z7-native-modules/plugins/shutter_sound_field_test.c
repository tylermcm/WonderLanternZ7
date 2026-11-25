/* SPDX-License-Identifier: MIT.
 * Original-Z7 shutter-sound FIELD TEST: one module, one camera session.
 *  - Playback smoke test: loads A:\SHUTTER1.WAV, installs the private playback
 *    intercept and queues one preview on resident-worker tick 8.
 *  - Trigger probe: wraps the three capture callbacks and logs events to
 *    A:\Z7TRIG.DAT (shutter_trigger_probe.h).
 *  - Upside-down photo EXIF orientation (photo_orientation_exif.h): writes
 *    Orientation 3 for capture pose 3, and logs every pose Nikon's Orientation
 *    writer sees (ring slot 4), so the session shows whether the camera records
 *    pose 3 for an upside-down exposure.
 *  - AF-area shortcut trial (af_shortcut_runtime.h): the movie record button,
 *    stock None in photo mode, switches AF-area to Wide-area AF (L) through the
 *    validated setter, from the host's before-update hook. Each apply is logged
 *    (ring slot 5). The trial assumes photo mode; test it in photo mode only.
 *  - Playback rotation observer (playback_observer.h): read-only; logs each
 *    change of Nikon's playback display request rotation and turn cache
 *    (ring slot 6), so viewing a tall and an upside-down photo shows the
 *    values a playback rotation module would change.
 *  - The log header also carries the sound counters, so a silent preview can be
 *    diagnosed from the card: queued, started, rejected, finished, and native
 *    requests that passed through the intercept.
 * No photo-triggered sound. Never writes any other file.
 */
#include <stdint.h>
/* Display-update counter: a finer clock than worker ticks for the log stamps. */
static volatile uint32_t z7_field_updates;
#define Z7_TRIG_STAMP() z7_field_updates
#include "shutter_trigger_probe.h"
#include "shutter_sound_playback.h"
#define Z7_EXIF_IFD_SLOT 0xa18d3410u
#define Z7_EXIF_POSE_HOOK(pose) z7_trig_append(0xe1f00000u|(pose),4u,0,0)
#include "photo_orientation_exif.h"
#include "update.h"
#include "af_shortcut_runtime.h"
#define Z7_PB_REPORT(event,request,cache) z7_trig_append((event),6u,(request),(cache))
#include "playback_observer.h"

#ifndef Z7_SOUND_PREVIEW_TICK
#define Z7_SOUND_PREVIEW_TICK 8u
#endif
static const char z7_sound_path_1[]="A:\\SHUTTER1.WAV";
volatile uint32_t z7_sound_init_result, z7_sound_boot_queued, z7_field_preview_tick;

/* Header words 13..15 (reserved in the probe-only module). */
static void z7_field_publish(void)
{
    uint32_t words[3]={
        (z7_sound_boot_queued&0xffu)|((z7_sound_installed&0xffu)<<8)|((z7_sound_init_result&0xffu)<<16)|(1u<<24)|((z7_exif_installed&1u)<<25),
        (z7_sound_starts&0xffffu)|((z7_sound_rejects&0xffffu)<<16),
        (z7_sound_finished&0xffffu)|((z7_sound_passthrough&0xffffu)<<16)};
    for (uint32_t i=0;i<3;++i)
        if (z7_trig_live.reserved[i]!=words[i]) {
            z7_trig_live.reserved[i]=words[i];
            __atomic_store_n(&z7_trig_dirty,1,__ATOMIC_RELEASE);
        }
    /* v2 extra words: EXIF writer calls and inversions, playback reports. */
    uint32_t extra[3]={z7_exif_writes,z7_exif_inverted,z7_pb_reports};
    for (uint32_t i=0;i<3;++i)
        if (z7_trig_live.extra[i]!=extra[i]) {
            z7_trig_live.extra[i]=extra[i];
            __atomic_store_n(&z7_trig_dirty,1,__ATOMIC_RELEASE);
        }
}

static struct z7_af_runtime z7_field_af;
volatile uint32_t z7_field_af_registered;
static void z7_field_update(void)
{
    __atomic_add_fetch(&z7_field_updates,1,__ATOMIC_RELAXED);
    uint32_t r=z7_af_runtime_step(&z7_field_af,1,0,z7_af_native_none_buttons());
    if (r) z7_trig_append(0xaf000000u|(r<<8)|(z7_field_af.last&0xffu),5u,z7_af_get(AF_PROP_AREA),0);
}

static void z7_field_worker(void)
{
    z7_trig_worker();
    z7_pb_poll();
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
    if (z7_exif_matches()) z7_exif_install();  /* optional part: skipped, not fatal */
    if (z7_af_area_matches()) {               /* optional part: skipped, not fatal */
        z7_af_shortcut_reset(&z7_field_af.policy);
        z7_af_shortcut_assign(&z7_field_af.policy,AF_BUTTON_MOVIE,AF_AREA_WIDE_L+1u);
        z7_field_af_registered=((const struct z7_module_update_api *)api)->register_before_update(z7_field_update);
    }
    z7_field_publish();
    return 0;
}
