/* SPDX-License-Identifier: MIT.
 * Original-Z7 shutter sound inside the LCD module, with a volume menu row.
 * Design follows JKWTCN's MIT Z7II shutter-sound feature (Silent photography
 * only, volume 1-5 plus preview); original-Z7 bindings are independent work.
 *
 *  - Plays A:\SHUTTER1.WAV on capture controller event 0x0419000B (once per
 *    photo and burst frame on the camera, November 25, 2026) while Silent
 *    photography (property 0x576) is on.
 *  - Level OFF or 1-7 from the module's settings page. Levels 1-5 are the
 *    engine's attenuations; 6 and 7 boost (x1.41, x2) with clipping, because
 *    level 5 of the camera-tested click was still a little quiet.
 *  - The level lives in its own 16-byte file A:\Z7SND.DAT, written by the
 *    resident worker only after the user changes it, so the display-settings
 *    journal and its format are untouched. No file means level 5.
 * The native controller handler always runs with the same arguments and result.
 */
#ifndef Z7_SHUTTER_SOUND_LCD_H
#define Z7_SHUTTER_SOUND_LCD_H
#include <stdint.h>
#ifdef Z7_SOUND_LAB
/* EXPERIMENTAL sound lab: extra digital levels 8 (x2.83) and 9 (x4), and the
 * driver tone value at level 5, all on the same row with a preview each, so the
 * owner can find the speaker's ceiling by ear. Saved as Z7SND.DAT version 2,
 * which the release module ignores (it then uses level 5). */
#define Z7_SOUND_LEVELS 9u
#define Z7_SOUND_TONE_OVERRIDE 1
#else
/* Menu levels: 7 in the first release (92602a4a); 9 adds the x2.83 and x4
 * boosts that the sound lab showed are still clean on the camera. */
#ifndef Z7_SOUND_MENU_LEVELS
#define Z7_SOUND_MENU_LEVELS 7u
#endif
#define Z7_SOUND_LEVELS Z7_SOUND_MENU_LEVELS
#endif
#include "../plugins/shutter_sound_playback.h"

#ifdef Z7_SOUND_LAB
struct z7_sl_choice { const char *text; uint8_t volume, tone; };
static const struct z7_sl_choice z7_sl_lab[]={
    {"OFF",0,31},{"1",1,31},{"2",2,31},{"3",3,31},{"4",4,31},{"5",5,31},{"6",6,31},{"7",7,31},
    {"8",8,31},{"9",9,31},
    {"5 T0",5,0},{"5 T16",5,16},{"5 T24",5,24},{"5 T28",5,28},{"5 T34",5,34},{"5 T37",5,37}};
#define SL_COUNT (sizeof(z7_sl_lab)/sizeof(z7_sl_lab[0]))
#define SL_VOLUME(i) (z7_sl_lab[i].volume)
#define SL_APPLY(i) __atomic_store_n(&z7_sound_tone,(uint32_t)z7_sl_lab[i].tone,__ATOMIC_RELEASE)
#define SL_RECORD_VERSION 2u
#else
#define SL_COUNT (Z7_SOUND_MENU_LEVELS+1u)
#define SL_VOLUME(i) (i)
#define SL_APPLY(i) ((void)(i))
#define SL_RECORD_VERSION 1u
#endif

enum {
    SL_LEVELS=SL_COUNT-1u, SL_DEFAULT=5u, SL_MAGIC=0x444e5337u /* "7SND" */, SL_VERSION=SL_RECORD_VERSION,
    SL_SLOT=0xa18d1bd8u, SL_NATIVE=0x101426a9u, SL_EXPOSURE=0x0419000bu,
    SL_GETTER=0x1016fef3u, SL_SILENT=0x576u,
    SL_CREATE=0x1027c0dbu, SL_WRITE=0x1027c049u
};
static const char z7_sl_wav_path[]="A:\\SHUTTER1.WAV";
static const char z7_sl_path[]="A:\\Z7SND.DAT";
#ifndef Z7_SOUND_LAB
static const char *const z7_sl_text[SL_LEVELS+1]={"OFF","1","2","3","4","5","6","7"
#if Z7_SOUND_MENU_LEVELS > 7
    ,"8","9"
#endif
};
#endif
volatile uint32_t z7_sl_level=SL_DEFAULT, z7_sl_saved=SL_DEFAULT, z7_sl_loaded, z7_sl_installed;
volatile uint32_t z7_sl_seen, z7_sl_queued, z7_sl_busy, z7_sl_previews, z7_sl_saves, z7_sl_errors, z7_sl_result;
static uint32_t z7_sl_observed=SL_DEFAULT, z7_sl_quiet, z7_sl_retry;
static _Alignas(64) uint32_t z7_sl_record[16];

static uint32_t z7_sl_check(uint32_t level) { return SL_MAGIC ^ (SL_VERSION<<8) ^ (level*0x01010101u) ^ 0xa5a5a5a5u; }

static uint32_t z7_sl_matches(void)
{
    return z7_sound_native_matches() && SND_W(SL_NATIVE-1u)==0x4ff0e92du && SND_W(SL_GETTER-1u)==0x4669b508u &&
        SND_W(SL_CREATE-1u)==0xb0abb530u && SND_W(SL_WRITE-1u)==0xb0abb5f0u && SND_W(0x1027bfccu)==0xb0aab510u;
}

/* Capture controller task, before Nikon's handler. Never blocks. */
static uint32_t z7_sl_controller(uint32_t event, uint32_t packet, uint32_t a2, uint32_t a3)
{
    if (event==SL_EXPOSURE) {
        __atomic_add_fetch(&z7_sl_seen,1,__ATOMIC_RELAXED);
        uint32_t level=__atomic_load_n(&z7_sl_level,__ATOMIC_ACQUIRE);
        if (level && level<=SL_LEVELS && SND_F(SL_GETTER,uint32_t,uint32_t)(SL_SILENT)==1u) {
            SL_APPLY(level);
            if (z7_sound_enqueue(0,SL_VOLUME(level),0)) __atomic_add_fetch(&z7_sl_queued,1,__ATOMIC_RELAXED);
            else __atomic_add_fetch(&z7_sl_busy,1,__ATOMIC_RELAXED);
        }
    }
    return SND_F(SL_NATIVE,uint32_t,uint32_t,uint32_t,uint32_t,uint32_t)(event,packet,a2,a3);
}

/* Loader task, once, after the display settings loaded. Never fails the module:
 * any missing piece leaves the sound off and the native slot untouched. */
static void z7_sl_prepare(void)
{
    if (!z7_sl_matches()) return;
    uint32_t fd=SND_F(SND_FILE_OPEN,uint32_t,const char *,uint32_t,uint32_t)(z7_sl_path,0,0);
    if ((int32_t)fd>=0) {
        uint32_t actual=0;
        SND_F(SND_INVALIDATE,void,void *,uint32_t)(z7_sl_record,sizeof(z7_sl_record));
        uint32_t result=SND_F(SND_FILE_READ,uint32_t,uint32_t,void *,uint32_t,uint32_t *)(fd,z7_sl_record,sizeof(z7_sl_record),&actual);
        SND_F(SND_INVALIDATE,void,void *,uint32_t)(z7_sl_record,sizeof(z7_sl_record));
        uint32_t closed=SND_F(SND_FILE_CLOSE,uint32_t,uint32_t)(fd);
        if (!result && !closed && actual==16u && z7_sl_record[0]==SL_MAGIC && z7_sl_record[1]==SL_VERSION &&
            z7_sl_record[2]<=SL_LEVELS && z7_sl_record[3]==z7_sl_check(z7_sl_record[2])) {
            z7_sl_level=z7_sl_saved=z7_sl_observed=z7_sl_record[2];
            z7_sl_loaded=1;
        } else z7_sl_loaded=2;  /* unreadable: keep the default, rewrite on next change */
    }
    if (!z7_sound_load(0,z7_sl_wav_path) || !z7_sound_install()) return;
    if (SND_W(SL_SLOT)!=SL_NATIVE) return;
    __asm__ volatile("dmb sy" ::: "memory");
    SND_W(SL_SLOT)=(uint32_t)(uintptr_t)z7_sl_controller;
    __asm__ volatile("dmb sy" ::: "memory");
    z7_sl_installed=1;
}

/* Menu task: OK on the Shutter sound row steps OFF,1..7 and previews the level. */
static void z7_sl_menu_next(void)
{
    uint32_t level=(__atomic_load_n(&z7_sl_level,__ATOMIC_RELAXED)+1u)%(SL_LEVELS+1u);
    __atomic_store_n(&z7_sl_level,level,__ATOMIC_RELEASE);
#ifdef Z7_SOUND_LAB
    if (!level) return;
    SL_APPLY(level);
    if (z7_sound_enqueue(0,SL_VOLUME(level),1)) __atomic_add_fetch(&z7_sl_previews,1,__ATOMIC_RELAXED);
#else
    if (level && z7_sound_enqueue(0,level,1)) __atomic_add_fetch(&z7_sl_previews,1,__ATOMIC_RELAXED);
#endif
}
static const char *z7_sl_value_text(void)
{
    uint32_t level=__atomic_load_n(&z7_sl_level,__ATOMIC_ACQUIRE);
#ifdef Z7_SOUND_LAB
    return level<=SL_LEVELS ? z7_sl_lab[level].text : "--";
#else
    return level<=SL_LEVELS ? z7_sl_text[level] : "--";
#endif
}

/* Resident worker only. Saves a level that has been stable for two ticks;
 * a failed write retries after five ticks. Never writes without a change. */
static void z7_sl_worker(void)
{
    if (!z7_sl_matches()) return;
    uint32_t level=__atomic_load_n(&z7_sl_level,__ATOMIC_ACQUIRE);
    if (level>SL_LEVELS || level==z7_sl_saved) return;
    if (level!=z7_sl_observed) { z7_sl_observed=level; z7_sl_quiet=0; return; }
    if (z7_sl_quiet<2u) { ++z7_sl_quiet; return; }
    if (z7_sl_retry) { --z7_sl_retry; return; }
    z7_sl_record[0]=SL_MAGIC; z7_sl_record[1]=SL_VERSION; z7_sl_record[2]=level; z7_sl_record[3]=z7_sl_check(level);
    SND_F(SND_CLEAN,void,void *,uint32_t)(z7_sl_record,sizeof(z7_sl_record));
    uint32_t fd=SND_F(SL_CREATE,uint32_t,const char *,uint32_t)(z7_sl_path,0);
    uint32_t result=fd, actual=0;
    if ((int32_t)fd>=0) {
        result=SND_F(SL_WRITE,uint32_t,uint32_t,const void *,uint32_t,uint32_t *)(fd,z7_sl_record,16u,&actual);
        uint32_t closed=SND_F(SND_FILE_CLOSE,uint32_t,uint32_t)(fd);
        if (!result && (closed || actual!=16u)) result=0x5407e000u;
    }
    z7_sl_result=result;
    if (!result) { z7_sl_saved=level; ++z7_sl_saves; }
    else { ++z7_sl_errors; z7_sl_retry=5u; }
}
#endif
