/* SPDX-License-Identifier: MIT.
 * PROVISIONAL original-Z7 shutter sound on still-file finalization. Loads
 * A:\SHUTTER1.WAV, installs the private playback intercept (shutter_sound_playback.h)
 * and wraps the still-file notification slot 0xA18D2750. On a new photo record in
 * Silent photography it queues one sound; the native handler always runs, with
 * the same arguments and result. Not for the camera until the trigger probe
 * confirms this event is one per photo and absent in live view.
 */
#include "module.h"
#include "shutter_sound_playback.h"
#include "shutter_sound_trigger.h"

enum { TRG_SLOT=0xa18d2750u, TRG_NATIVE=0x104db211u, TRG_GETTER=0x1016fef3u, TRG_SILENT_PROPERTY=0x576u };
static const char z7_sound_path_1[]="A:\\SHUTTER1.WAV";
static struct z7_trigger_policy z7_trigger;
volatile uint32_t z7_trigger_init_result, z7_trigger_queued, z7_trigger_busy;

static uint32_t z7_trigger_wrap(uint32_t event, uint32_t packet, uint32_t a2, uint32_t a3)
{
    if (event==TRG_STILL_FILE_EVENT && packet && !(packet&3u) && packet>=0xa1800000u && packet<0xb0000000u) {
        uint32_t record=SND_W(packet);
        uint32_t silent=SND_F(TRG_GETTER,uint32_t,uint32_t)(TRG_SILENT_PROPERTY);
        if (z7_trigger_still_file(&z7_trigger,event,record,silent)==TRG_PLAY) {
            if (z7_sound_enqueue(0,SND_VOLUME_MAX,0)) ++z7_trigger_queued;
            else ++z7_trigger_busy;
        }
    }
    return SND_F(TRG_NATIVE,uint32_t,uint32_t,uint32_t,uint32_t,uint32_t)(event,packet,a2,a3);
}

/* Offline audit seam; no camera behavior depends on it. */
uint32_t z7_trigger_operation(uint32_t op, uint32_t a, uint32_t b, uint32_t c)
{
    switch (op) {
    case 1: return z7_trigger_still_file(&z7_trigger,a,b,c);
    case 2: return z7_trigger_key(a);
    default: return 0;
    }
}

uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET || api->size<12) return 1;
    if (!z7_sound_native_matches() || SND_W(TRG_NATIVE-1u)!=0x2900b538u || SND_W(TRG_GETTER-1u)!=0x4669b508u) return 1;
    if (!z7_sound_load(0,z7_sound_path_1) || !z7_sound_install()) return 0;  /* no clip: stays inert */
    if (SND_W(TRG_SLOT)==TRG_NATIVE) {
        SND_W(TRG_SLOT)=(uint32_t)(uintptr_t)z7_trigger_wrap;
        __asm__ volatile("dmb sy" ::: "memory");
        z7_trigger_init_result=1;
    }
    return 0;
}
