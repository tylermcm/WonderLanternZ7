/* SPDX-License-Identifier: MIT.
 * Original-Z7 shutter sound on every photo: CAMERA TEST module.
 *  - Loads A:\SHUTTER1.WAV and installs the private playback intercept
 *    (shutter_sound_playback.h, which played on the camera on November 25, 2026).
 *  - Plays it on each exposure in Silent photography: capture controller event
 *    0x0419000B (shutter_sound_capture_trigger.h), measured once per photo and
 *    per burst frame in field-test session 2.
 *  - Keeps the trigger-probe log (shutter_trigger_probe.h, log v2) in
 *    A:\Z7TRIG.DAT with the trigger counters in the header, so a missing or
 *    extra sound can be diagnosed from the card.
 * No boot chime. The native controller handler always runs with the same
 * arguments and result. Never writes any file other than Z7TRIG.DAT.
 */
#include "module.h"
#include "worker.h"
#include "shutter_sound_playback.h"
#include "shutter_sound_capture_trigger.h"

static struct z7_capture_policy z7_capture;
volatile uint32_t z7_capture_queued, z7_capture_busy, z7_capture_init_result;

/* Runs on the capture controller's notifying task, before Nikon's handler. */
static void z7_capture_event(uint32_t slot, uint32_t event)
{
    if (slot!=CAP_SLOT_CONTROLLER || event!=CAP_EXPOSURE_EVENT) return;
    uint32_t silent=((uint32_t (*)(uint32_t))(uintptr_t)0x1016fef3u)(0x576u);
    if (z7_capture_decide(&z7_capture,slot,event,silent)!=CAP_PLAY) return;
    if (z7_sound_enqueue(0,SND_VOLUME_MAX,0)) __atomic_add_fetch(&z7_capture_queued,1,__ATOMIC_RELAXED);
    else __atomic_add_fetch(&z7_capture_busy,1,__ATOMIC_RELAXED);
}
#define Z7_TRIG_EVENT_HOOK(slot,event,packet) z7_capture_event((slot),(event))
#include "shutter_trigger_probe.h"

static const char z7_sound_path_1[]="A:\\SHUTTER1.WAV";
volatile uint32_t z7_sound_init_result;

/* Header words 13..15 carry the sound state as in the field test (bit 26 marks
 * this module); v2 extra words 3..6 carry seen/play/queued/busy. Worker only. */
static void z7_capture_publish(void)
{
    uint32_t words[3]={
        ((z7_sound_installed&0xffu)<<8)|((z7_sound_init_result&0xffu)<<16)|(1u<<24)|(1u<<26),
        (z7_sound_starts&0xffffu)|((z7_sound_rejects&0xffffu)<<16),
        (z7_sound_finished&0xffffu)|((z7_sound_passthrough&0xffffu)<<16)};
    uint32_t extra[4]={z7_capture.seen,z7_capture.play,z7_capture_queued,z7_capture_busy};
    uint32_t changed=0;
    for (uint32_t i=0;i<3;++i) if (z7_trig_live.reserved[i]!=words[i]) { z7_trig_live.reserved[i]=words[i]; changed=1; }
    for (uint32_t i=0;i<4;++i) if (z7_trig_live.extra[3+i]!=extra[i]) { z7_trig_live.extra[3+i]=extra[i]; changed=1; }
    if (changed) __atomic_store_n(&z7_trig_dirty,1,__ATOMIC_RELEASE);
}

static void z7_capture_worker(void)
{
    z7_trig_worker();
    z7_capture_publish();
}

uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET ||
        api->size<sizeof(struct z7_module_worker_api)) return 1;
    /* Fail closed on any firmware mismatch before touching files or slots. */
    if (!z7_trig_matches() || !z7_sound_native_matches()) return 1;
    if (!((const struct z7_module_worker_api *)api)->register_worker(z7_capture_worker)) return 1;
    z7_sound_init_result=z7_sound_load(0,z7_sound_path_1) ? 1u : 0u;
    if (z7_sound_init_result) z7_sound_init_result|=z7_sound_install()<<1;
    z7_capture_init_result=z7_trig_install();
    z7_capture_publish();
    return 0;
}
