/* SPDX-License-Identifier: MIT.
 * Original-Z7 shutter-sound FOLDER: choose the click from up to ten WAV files
 * in A:\SHUTTER\ (SOUND01.WAV ... SOUND10.WAV), or the original A:\SHUTTER1.WAV
 * ("Card"). Design follows JKWTCN's MIT Z7II sound choice (SHUTTER1-5); the
 * folder and lazy loading are this port's own: only the selected file is in
 * memory, so memory use stays at one clip.
 *
 * Which files exist is checked once at power-on (open/close each name). The
 * menu (GUI task) only changes the selection; the resident worker loads the
 * newly selected file when no sound is playing, then plays the requested
 * preview. Requires shutter_sound_lcd.h (included first).
 */
#ifndef Z7_SHUTTER_SOUND_FOLDER_H
#define Z7_SHUTTER_SOUND_FOLDER_H
#include <stdint.h>

enum { SF_SOUNDS=11u /* 0 = Card (A:\SHUTTER1.WAV), 1..10 = folder */ };
static const char *const z7_sf_path[SF_SOUNDS]={
    "A:\\SHUTTER1.WAV",
    "A:\\SHUTTER\\SOUND01.WAV","A:\\SHUTTER\\SOUND02.WAV","A:\\SHUTTER\\SOUND03.WAV",
    "A:\\SHUTTER\\SOUND04.WAV","A:\\SHUTTER\\SOUND05.WAV","A:\\SHUTTER\\SOUND06.WAV",
    "A:\\SHUTTER\\SOUND07.WAV","A:\\SHUTTER\\SOUND08.WAV","A:\\SHUTTER\\SOUND09.WAV",
    "A:\\SHUTTER\\SOUND10.WAV"};
static const char *const z7_sf_text[SF_SOUNDS]={"Card","1","2","3","4","5","6","7","8","9","10"};
volatile uint32_t z7_sf_available, z7_sf_selected, z7_sf_loaded=0xffffffffu, z7_sf_preview, z7_sf_loads, z7_sf_failed;

/* Loader task, once: which files exist. */
static void z7_sf_scan(void)
{
    uint32_t mask=0;
    for (uint32_t i=0;i<SF_SOUNDS;++i) {
        uint32_t fd=SND_F(SND_FILE_OPEN,uint32_t,const char *,uint32_t,uint32_t)(z7_sf_path[i],0,0);
        if ((int32_t)fd<0) continue;
        if (!SND_F(SND_FILE_CLOSE,uint32_t,uint32_t)(fd)) mask|=1u<<i;
    }
    z7_sf_available=mask;
}
/* Loader or worker task, only while no sound is queued or playing. */
static uint32_t z7_sf_load(uint32_t sound)
{
    if (sound>=SF_SOUNDS || !(z7_sf_available>>sound&1u)) return 0;
    uint32_t ok=z7_sound_load(0,z7_sf_path[sound]);
    z7_sound_prepared_key=0xffffffffu;  /* new samples: rebuild the scaled copy */
    __atomic_store_n(&z7_sf_loaded,ok ? sound : 0xffffffffu,__ATOMIC_RELEASE);
    if (ok) ++z7_sf_loads; else ++z7_sf_failed;
    return ok;
}
/* Menu task: next available sound; preview it once loaded. */
static void z7_sf_menu_next(void)
{
    uint32_t mask=__atomic_load_n(&z7_sf_available,__ATOMIC_ACQUIRE);
    if (!mask) return;
    uint32_t s=__atomic_load_n(&z7_sf_selected,__ATOMIC_RELAXED);
    for (uint32_t i=1;i<=SF_SOUNDS;++i) {
        uint32_t next=(s+i)%SF_SOUNDS;
        if (mask>>next&1u) { s=next; break; }
    }
    __atomic_store_n(&z7_sf_selected,s,__ATOMIC_RELEASE);
    __atomic_store_n(&z7_sf_preview,1,__ATOMIC_RELEASE);
}
static const char *z7_sf_value_text(void)
{
    uint32_t s=__atomic_load_n(&z7_sf_selected,__ATOMIC_ACQUIRE);
    if (!__atomic_load_n(&z7_sf_available,__ATOMIC_ACQUIRE)) return "None";
    return s<SF_SOUNDS ? z7_sf_text[s] : "--";
}
/* Resident worker: load the selection when idle, then play a pending preview. */
static void z7_sf_worker(void)
{
    uint32_t s=__atomic_load_n(&z7_sf_selected,__ATOMIC_ACQUIRE);
    if (s!=__atomic_load_n(&z7_sf_loaded,__ATOMIC_ACQUIRE)) {
        if (__atomic_load_n(&z7_sound_playback,__ATOMIC_ACQUIRE)!=SND_IDLE) return;
        if (!z7_sf_load(s)) { __atomic_store_n(&z7_sf_preview,0,__ATOMIC_RELEASE); return; }
    }
    if (__atomic_exchange_n(&z7_sf_preview,0,__ATOMIC_ACQ_REL)) {
        uint32_t level=__atomic_load_n(&z7_sl_level,__ATOMIC_ACQUIRE);
        if (level && level<=SL_LEVELS && z7_sound_enqueue(0,SL_VOLUME(level),1)) ++z7_sl_previews;
    }
}
#endif
