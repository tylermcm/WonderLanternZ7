/* SPDX-License-Identifier: MIT.
 * Original-Z7 AF-AREA BUTTONS inside the LCD module: assign Pinpoint, Single,
 * Dynamic, Wide (S), Wide (L) or Auto-area AF to Fn1, Fn2, AF-ON, the
 * sub-selector centre and the movie-record button from the module's own page.
 * Design follows JKWTCN's MIT Z7II AF-area shortcut (press once to select and
 * keep an AF-area mode; only buttons whose Nikon f2 assignment is None act);
 * original-Z7 bindings are independent work (AF_SHORTCUT_RESEARCH.md).
 *
 *  - Runtime: af_shortcut_runtime.h, once per shooting-display update (the LCD
 *    module's before-update hook), photo mode only (0xA201D4D0+0x40 == 0, as
 *    the battery overlay) and not while Nikon's menu/playback flag
 *    0xA18237C6 is set. AF-area writes go through af_area_native.h, which
 *    enforces the menu's focus-mode rules and reads the value back.
 *  - Saved in its own 16-byte file A:\Z7AFB.DAT (3 bits per button), written by
 *    the resident worker only after a change; the display journal and the
 *    shutter-sound file are untouched. No file: every button OFF.
 *  - Any firmware mismatch (getter/setter) leaves the feature off.
 */
#ifndef Z7_AF_BUTTONS_LCD_H
#define Z7_AF_BUTTONS_LCD_H
#ifndef Z7_SHUTTER_SOUND_LCD_H
#error AF-area buttons reuse the shutter-sound page's file helpers
#endif
#include "af_shortcut_runtime.h"

enum { AB_MAGIC=0x42464137u /* "7AFB" */, AB_VERSION=1u, AB_CHOICES=7u, AB_ROWS=5u, AB_BITS=3u };
static const char z7_ab_path[]="A:\\Z7AFB.DAT";
static const uint8_t z7_ab_area[AB_CHOICES]={0xffu,AF_AREA_PINPOINT,AF_AREA_SINGLE,AF_AREA_DYNAMIC,
                                             AF_AREA_WIDE_S,AF_AREA_WIDE_L,AF_AREA_AUTO};
static const char *const z7_ab_text[AB_CHOICES]={"OFF","Pinpt","Single","Dynamic",
                                                 "Wide-S","Wide-L","Auto"};
/* Menu row -> runtime button (Fn1, Fn2, AF-ON, sub-selector centre, movie). */
static const uint8_t z7_ab_button[AB_ROWS]={AF_BUTTON_FN1,AF_BUTTON_FN2,AF_BUTTON_AF_ON,AF_BUTTON_SS_CENTER,AF_BUTTON_MOVIE};
volatile uint32_t z7_ab_state, z7_ab_saved, z7_ab_loaded, z7_ab_ready;
volatile uint32_t z7_ab_steps, z7_ab_applied, z7_ab_refused, z7_ab_last, z7_ab_saves, z7_ab_errors, z7_ab_result;
static uint32_t z7_ab_observed, z7_ab_quiet, z7_ab_retry;
static _Alignas(64) uint32_t z7_ab_record[16];
static struct z7_af_runtime z7_ab_runtime;

static uint32_t z7_ab_check(uint32_t state) { return AB_MAGIC ^ (AB_VERSION<<8) ^ (state*0x9e3779b1u) ^ 0x5a5a5a5au; }
static uint32_t z7_ab_choice(uint32_t state, uint32_t row) { return state>>(AB_BITS*row)&7u; }
static uint32_t z7_ab_valid(uint32_t state)
{
    if (state>>(AB_BITS*AB_ROWS)) return 0;
    for (uint32_t r=0;r<AB_ROWS;++r) if (z7_ab_choice(state,r)>=AB_CHOICES) return 0;
    return 1;
}
static void z7_ab_assign(uint32_t state)
{
    for (uint32_t r=0;r<AB_ROWS;++r) {
        uint32_t c=z7_ab_choice(state,r);
        z7_af_shortcut_assign(&z7_ab_runtime.policy,z7_ab_button[r],c ? z7_ab_area[c]+1u : 0u);
    }
}

/* Loader task, once. Never fails the module. */
static void z7_ab_prepare(void)
{
    z7_af_shortcut_reset(&z7_ab_runtime.policy);
    if (!z7_af_area_matches() || !z7_sl_matches()) return;
    uint32_t fd=SND_F(SND_FILE_OPEN,uint32_t,const char *,uint32_t,uint32_t)(z7_ab_path,0,0);
    if ((int32_t)fd>=0) {
        uint32_t actual=0;
        SND_F(SND_INVALIDATE,void,void *,uint32_t)(z7_ab_record,sizeof(z7_ab_record));
        uint32_t result=SND_F(SND_FILE_READ,uint32_t,uint32_t,void *,uint32_t,uint32_t *)(fd,z7_ab_record,sizeof(z7_ab_record),&actual);
        SND_F(SND_INVALIDATE,void,void *,uint32_t)(z7_ab_record,sizeof(z7_ab_record));
        uint32_t closed=SND_F(SND_FILE_CLOSE,uint32_t,uint32_t)(fd);
        if (!result && !closed && actual==16u && z7_ab_record[0]==AB_MAGIC && z7_ab_record[1]==AB_VERSION &&
            z7_ab_valid(z7_ab_record[2]) && z7_ab_record[3]==z7_ab_check(z7_ab_record[2])) {
            z7_ab_state=z7_ab_saved=z7_ab_observed=z7_ab_record[2];
            z7_ab_loaded=1;
        } else z7_ab_loaded=2;                     /* unreadable: all OFF, rewrite on change */
    }
    z7_ab_assign(z7_ab_state);
    __atomic_store_n(&z7_ab_ready,1u,__ATOMIC_RELEASE);
}

/* Menu task: OK on a button row steps OFF, Pinpoint, ..., Auto-area. */
static void z7_ab_menu_next(uint32_t row)
{
    if (row>=AB_ROWS) return;
    uint32_t state=__atomic_load_n(&z7_ab_state,__ATOMIC_RELAXED);
    uint32_t c=(z7_ab_choice(state,row)+1u)%AB_CHOICES;
    state=(state&~(7u<<(AB_BITS*row)))|(c<<(AB_BITS*row));
    __atomic_store_n(&z7_ab_state,state,__ATOMIC_RELEASE);
    z7_ab_assign(state);
}
static const char *z7_ab_value_text(uint32_t row)
{
    if (!__atomic_load_n(&z7_ab_ready,__ATOMIC_ACQUIRE)) return "--";
    return row<AB_ROWS ? z7_ab_text[z7_ab_choice(__atomic_load_n(&z7_ab_state,__ATOMIC_ACQUIRE),row)] : "";
}

/* GUI task, once per shooting-display update. */
static void z7_ab_update(void)
{
    if (!__atomic_load_n(&z7_ab_ready,__ATOMIC_ACQUIRE) || !__atomic_load_n(&z7_ab_state,__ATOMIC_ACQUIRE)) return;
    ++z7_ab_steps;
    uint32_t photo=!*(const volatile uint8_t *)(uintptr_t)0xa18237c6u &&
        !*(const volatile uint8_t *)(uintptr_t)(0xa201d4d0u+0x40u);
    uint32_t r=z7_af_runtime_step(&z7_ab_runtime,photo,0,z7_af_native_none_buttons());
    if (!r) return;
    z7_ab_last=z7_ab_runtime.last|r<<16;
    if (r==AF_APPLY_SET || r==AF_APPLY_ALREADY) ++z7_ab_applied; else ++z7_ab_refused;
}

/* Resident worker only: save a state stable for two ticks; retry after five. */
static void z7_ab_worker(void)
{
    if (!__atomic_load_n(&z7_ab_ready,__ATOMIC_ACQUIRE)) return;
    uint32_t state=__atomic_load_n(&z7_ab_state,__ATOMIC_ACQUIRE);
    if (!z7_ab_valid(state) || state==z7_ab_saved) return;
    if (state!=z7_ab_observed) { z7_ab_observed=state; z7_ab_quiet=0; return; }
    if (z7_ab_quiet<2u) { ++z7_ab_quiet; return; }
    if (z7_ab_retry) { --z7_ab_retry; return; }
    z7_ab_record[0]=AB_MAGIC; z7_ab_record[1]=AB_VERSION; z7_ab_record[2]=state; z7_ab_record[3]=z7_ab_check(state);
    SND_F(SND_CLEAN,void,void *,uint32_t)(z7_ab_record,sizeof(z7_ab_record));
    uint32_t fd=SND_F(SL_CREATE,uint32_t,const char *,uint32_t)(z7_ab_path,0);
    uint32_t result=fd, actual=0;
    if ((int32_t)fd>=0) {
        result=SND_F(SL_WRITE,uint32_t,uint32_t,const void *,uint32_t,uint32_t *)(fd,z7_ab_record,16u,&actual);
        uint32_t closed=SND_F(SND_FILE_CLOSE,uint32_t,uint32_t)(fd);
        if (!result && (closed || actual!=16u)) result=0x5407e000u;
    }
    z7_ab_result=result;
    if (!result) { z7_ab_saved=state; ++z7_ab_saves; }
    else { ++z7_ab_errors; z7_ab_retry=5u; }
}
#endif
