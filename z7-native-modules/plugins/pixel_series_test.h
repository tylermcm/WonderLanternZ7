/* SPDX-License-Identifier: MIT.
 * Original-Z7 C 3.80 PIXEL-SHIFT SERIES DRY RUN (step 3a of PIXEL_SHIFT_RESEARCH.md).
 * Design follows JKWTCN's MIT Z7II pixel_shift.c (Bayer corner order and the
 * 21/18 half-pixel-step scale); original-Z7 bindings are independent work.
 *
 * Unlike upstream, the module does not fire the shutter: the photographer (or
 * Nikon's own interval timer) takes four photos. Once per boot, from the
 * resident worker:
 *  1. ARM exactly as the one-move test: stabilisation active and settled on
 *     two reads 100 ms apart; snapshot Nikon's D2 parameters (no D2: no move).
 *  2. Hold at Bayer position 0, then after each NEW still photo reported by the
 *     still-file hook (inverted_playback.h, 0x041E0002) move to the next corner
 *     {0,0},{1,0},{1,1},{0,1} x {21,18} steps (target -4*step per axis), and
 *     confirm the telemetry follows.
 *  3. Every worker tick while waiting: read telemetry; if the hold was lost or
 *     the target changed (e.g. a half-press re-applied normal stabilisation),
 *     log it and re-send the current position (at most VS_RESENDS in total).
 *  4. After the fourth photo, or 120 ticks without one, or any lost reply:
 *     centre, re-send Nikon's D2 parameters (vr_move_test.h restore), watch.
 * Each photo's still key is logged so the four NEFs can be merged on a
 * computer. A:\Z7VRMOV.DAT, log version 3.
 */
#ifndef Z7_PIXEL_SERIES_TEST_H
#define Z7_PIXEL_SERIES_TEST_H
#if !defined(Z7_VR_MOVE) || !defined(Z7_VR_RESTORE)
#error The series dry run builds on the VR move test and the D2 restore
#endif
enum {
    VS_FRAMES=4u, VS_WAIT_TICKS=120u, VS_RESENDS=6u,
    VS_PH_SEND=0x16u, VS_PH_FOLLOW=6u, VS_PH_FRAME=7u, VS_PH_WAIT=8u, VS_PH_RESEND=0x18u,
    VS_SERIES_STARTED=1u<<16, VS_FRAME_TIMEOUT=1u<<17, VS_HOLD_LOST=1u<<18, VS_SERIES_COMPLETE=1u<<19,
    VS_POSITION_MISSED=1u<<20, VS_MOVED_LATE=1u<<21
};
static const uint8_t z7_vs_corner[4][2]={{0,0},{1,0},{1,1},{0,1}};
static uint8_t z7_vs_payload[10]={0,0,0,0,0,16,16,0,0,2};
volatile uint32_t z7_vs_photos, z7_vs_seen, z7_vs_last_key, z7_vs_frame, z7_vs_wait, z7_vs_resends, z7_vs_last_wait_state;
#ifdef Z7_PIXEL_MENU
#include "pixel_shift_menu.h"
#ifdef Z7_PIXEL_NIKON_MENU
#include "pixel_nikon_menu.h"
#endif
#ifdef Z7_PIXEL_NIKON_MENU
#define Z7_VS_FRAME_COUNT (z7_pn_job_active ? z7_pn_job_total : z7_pm_count())
#else
#define Z7_VS_FRAME_COUNT z7_pm_count()
#endif
#else
#define Z7_VS_FRAME_COUNT VS_FRAMES
#endif

/* Still-file hook (Nikon's task): one count per new photo record. */
static void z7_vs_still(uint32_t key)
{
    uint32_t stage=__atomic_load_n(&z7_vm_stage,__ATOMIC_ACQUIRE);
    if (stage!=4u
#ifdef Z7_PIXEL_NIKON_MENU
        && stage!=5u
#endif
        ) return;
#ifdef Z7_PIXEL_MENU
    if (!key || key==z7_vs_last_key) return;
    z7_vs_last_key=key;
#endif
    uint32_t n=__atomic_load_n(&z7_vs_photos,__ATOMIC_ACQUIRE);
#ifdef Z7_PIXEL_NIKON_MENU
    uint32_t invalid=n>=Z7_VS_FRAME_COUNT;
    for (uint32_t i=0;i<n && i<288u;++i) if (z7_vm_log.keys[i]==key) invalid=1;
    if (invalid) {
        __atomic_fetch_or(&z7_vm_log.flags,1u<<30,__ATOMIC_RELEASE);
        __atomic_store_n(&z7_pm_cancel,1u,__ATOMIC_RELEASE);return;
    }
#endif
    if (n<Z7_VS_FRAME_COUNT) z7_vm_log.keys[n]=key;
    __atomic_store_n(&z7_vs_photos,n+1u,__ATOMIC_RELEASE);
}
#define Z7_STILL_KEY_HOOK(key) z7_vs_still(key)

#ifdef Z7_PIXEL_SHIFT_V1
/* Z7 scale measured by the calibration run 73567658 (Nov 27): about 20 steps
 * per pixel in x and 18 in y, independent axes. */
#ifdef Z7_PIXEL_SHIFT_V2
/* Dead-zone run 615cf144: the body settles for about 5 s after the button is
 * released (about 1 px), and upward y moves fall about 0.3 px short while the
 * same target reached from above is exact. V2: 7 s start settle, and every
 * frame is approached from VS_APPROACH_Y steps above its y target. */
enum { VS_STEP_X=20, VS_STEP_Y=18, VS_SETTLE_START_MS=7000u, VS_SETTLE_FRAME_MS=500u, VS_APPROACH_Y=36, VS_PH_PRE=0x17u };
#else
enum { VS_STEP_X=20, VS_STEP_Y=18, VS_SETTLE_START_MS=2000u, VS_SETTLE_FRAME_MS=500u };
#endif
#else
enum { VS_STEP_X=21, VS_STEP_Y=18 };   /* upstream's Z7II values */
#endif
static void z7_vs_target(uint32_t frame, int *x, int *y)
{
    *x=VS_STEP_X*(int)z7_vs_corner[frame&3u][0]; *y=VS_STEP_Y*(int)z7_vs_corner[frame&3u][1];
#ifdef Z7_PIXEL_MENU
    /* Four Bayer corners at each of four half-pixel offsets. 32 repeats
     * the 16 positions for averaging. Half steps 10/9 are experimental on Z7.
     * Max approach remains y=18+9+36=63 steps (252 telemetry counts).
     */
    if (z7_pm_count()>=16u) {
        *x+=10*(int)z7_vs_corner[(frame>>2)&3u][0];
        *y+=9*(int)z7_vs_corner[(frame>>2)&3u][1];
    }
#endif
}
static int z7_vs_matches(const uint8_t *t, int x, int y)
{
    return t[VM_STATE]==VM_HOLD && z7_vm_word(t)==-4*x && z7_vm_word(t+2)==-4*y &&
        z7_vm_word(t+4)==-4*y && z7_vm_settled(t,VM_HOLD_TOLERANCE);
}
#ifdef Z7_PIXEL_SHIFT_V1
static int z7_vs_matches(const uint8_t *t, int x, int y);
static int z7_vs_matches_now(uint32_t frame)
{
    int x,y; z7_vs_target(frame,&x,&y);
    uint32_t s=z7_vm_sample(VS_PH_FOLLOW,(frame<<5)|31u);
    return !s && z7_vs_matches(z7_vm_output,x,y);
}
#endif
/* Poll every 100 ms until two reads in a row show the commanded position. */
static int z7_vs_follow(uint32_t frame, int x, int y)
{
    int run=0;
    for (uint32_t i=0;i<VM_POLLS;++i) {
        z7_vm_sleep(100);
        uint32_t s=z7_vm_sample(VS_PH_FOLLOW,(frame<<5)|(i+1u));
        if (s==VM_PENDING) return -1;
        run=!s && z7_vs_matches(z7_vm_output,x,y) ? run+1 : 0;
        if (run==2) return 1;
    }
    return 0;
}
#ifdef Z7_PIXEL_SHIFT_V2
/* Pre-position VS_APPROACH_Y steps above the frame's y target, so the target
 * is always reached moving down. 1 followed, 0 not followed, -1 stop. */
static int z7_vs_preposition(uint32_t frame)
{
    int x,y; z7_vs_target(frame,&x,&y); y+=VS_APPROACH_Y;
    z7_vs_payload[1]=(uint8_t)x; z7_vs_payload[3]=(uint8_t)y;
    uint32_t s=z7_vm_exchange(VM_POSITION,z7_vs_payload);
    z7_vm_record(VS_PH_PRE,frame,s,0);
    if (z7_vm_applied(s)) z7_vm_log.flags|=VM_MOVE_SENT;
    if (s) return z7_vm_applied(s) ? -1 : 0;
    return z7_vs_follow(frame,x,y);
}
#endif
/* Send the position for this frame; 1 followed, 0 not followed, -1 stop. */
static int z7_vs_position(uint32_t frame, uint32_t phase)
{
    int x,y; z7_vs_target(frame,&x,&y);
    z7_vs_payload[1]=(uint8_t)x; z7_vs_payload[3]=(uint8_t)y;
    uint32_t s=z7_vm_exchange(VM_POSITION,z7_vs_payload);
    z7_vm_record(phase,frame,s,0);
    if (z7_vm_applied(s)) z7_vm_log.flags|=VM_MOVE_SENT;
    if (s) return z7_vm_applied(s) ? -1 : 0;
    z7_vm_log.flags|=VM_MOVE_ACK;
    int r=z7_vs_follow(frame,x,y);
    if (r>0) z7_vm_log.flags|=VM_MOVE_FOLLOWED; else if (!r) z7_vm_log.flags|=VS_POSITION_MISSED;
    return r;
}
/* Centre, restore D2, then hand over to the watch stage. */
#ifdef Z7_PIXEL_NIKON_MENU
static uint32_t z7_vr_callback(uint32_t,const uint32_t *,uint32_t,uint32_t);
static uint32_t z7_pn_capture_pending(void) { return !!VM_W(0xa238bb28u); }
#endif
static void z7_vs_finish(void)
{
#ifdef Z7_PIXEL_MENU
    __atomic_store_n(&z7_pm_requested,0u,__ATOMIC_RELEASE);
#endif
#ifdef Z7_PIXEL_NIKON_MENU
    if ((z7_vm_log.flags&VM_MOVE_SENT) && z7_pn_capture_pending()) {
        z7_vm_stage=5u;z7_pm_running=0;z7_pn_job_error=5u;
        z7_vm_save();return; /* Native exposure still owns the body: don't move. */
    }
#endif
    z7_vm_stage=2;                                  /* stop counting photos */
    uint32_t s=0x100u;
    if (z7_vm_log.flags&VM_MOVE_SENT) for (uint32_t i=0;i<5u;++i) {
        s=z7_vm_exchange(VM_POSITION,z7_vm_centre);
        z7_vm_record(VM_PH_CENTRE_SEND,i,s,0);
        if (z7_vm_applied(s)) z7_vm_log.flags|=VM_CENTRE_SENT;
        if (!s) break;
        z7_vm_sleep(s==VM_PENDING ? 500 : 200);
    }
    if (!s) {
        z7_vm_log.flags|=VM_CENTRE_ACK;
        if (z7_vm_follow(VM_PH_CENTRE,0)) z7_vm_log.flags|=VM_CENTRE_FOLLOWED;
    }
    if (z7_vm_log.flags&VM_MOVE_SENT) z7_vm_restore();
    z7_vm_log.frames=__atomic_load_n(&z7_vs_photos,__ATOMIC_ACQUIRE);
    z7_vm_save();
#ifdef Z7_PIXEL_MENU
    __atomic_store_n(&z7_pm_running,0u,__ATOMIC_RELEASE);
#endif
}
#ifdef Z7_PIXEL_RELEASE
/* MODULE-FIRED SERIES (step 3b). The step-3a camera run showed that a
 * photographer's half-press makes Nikon re-apply normal stabilisation and so
 * ends the hold before the exposure. As upstream does, the module therefore
 * fires the shutter itself, right after the position is confirmed and with no
 * half-press:
 *  - Release: Nikon's release API 0x101ECFB0(request, callback) - used by the
 *    PTP InitiateCapture handlers (0x10308DE6, 0x10319F40) and the remote
 *    capture control (0x10520FBC); 0 = accepted, else Nikon's refusal code.
 *    Request (0x14 bytes, PTP layout): mode 0, destination override 1 (as PTP
 *    format 0x3800), no AF (word +4 = 0), +8 = 0, +0xC = 1, +0x10 = 1 frame -
 *    the same values as upstream's Z7II settings {0x100,0,0,1,1}.
 *  - Completion: Nikon calls the callback from slot 0x38 of the table
 *    0xA238BA48 (filled by 0x1005ED7C only if empty), once. On the camera
 *    (Nov 27, c813c457) it reported event 0x04100038 without an argument; the
 *    remote-capture callback treats that as success too. 0x04100034 carries a
 *    status word (0 = success). The new still-file record (0x041E0002 hook)
 *    must confirm the file in either case.
 *  - Arming needs the photographer: stabilisation active and settled is not
 *    enough (it already is right after power-on, so c813c457 fired at boot);
 *    the shutter button must be half-pressed (SW0 0xA1F90AA4 bit 0x80000000,
 *    vertical grip 0x20000000) at that moment.
 *  - Start: once the shutter button (bits 0xF0000000: half/full, horizontal
 *    and vertical) has then been free for 0.5 s. Touching it during the series
 *    aborts it.
 * Then centre, Nikon D2 restore, watch - as the dry run.
 */
enum {
    VR_RELEASE=0x101ecfb1u, VR_SLOT_TABLE=0xa238ba48u, VR_SLOT=0xa238ba48u+0x38u*4u, VR_DONE=0x04100034u,
    VR_RELEASED=0x04100038u,  /* camera run c813c457: Nikon reports this one (no argument) */
    VR_SW0=0xa1f90aa4u, VR_SHUTTER_BITS=0xf0000000u, VR_HALF_BITS=0xa0000000u,
    VR_PH_FIRE=0x19u, VR_PH_EVENT=0x1au, VR_PH_FREE=0x1bu,
    VR_FIRED=1u<<22, VR_REFUSED=1u<<23, VR_FRAME_FAILED=1u<<24, VR_TOUCHED=1u<<25, VR_NOT_FREED=1u<<26, VR_SLOT_BUSY=1u<<27
};
struct z7_vr_request { uint8_t mode, destination, af_mode, sub; uint32_t af, word8, wordc, frames; };
_Static_assert(sizeof(struct z7_vr_request)==0x14,"release request");
static const struct z7_vr_request z7_vr_request={0,1,0,0,0,0,1,1};
/* One audible click per confirmed frame so the photographer can count them
 * (Silent photography hides the blackout). Defined after the shutter-sound
 * component in combined_display.c; without it, no click. */
static uint32_t z7_vr_sound_mark(void);
static void z7_vr_count_click(uint32_t mark);
volatile uint32_t z7_vr_events, z7_vr_last_event, z7_vr_arg0, z7_vr_arg1, z7_vr_done;

static uint32_t z7_vr_native_ok(void)
{
    return VM_W(VR_RELEASE-1u)==0x4ff0e92du && VM_W(VR_RELEASE+3u)==0x468b2500u &&
        VM_W(0x1005ed7cu)==0x46022900u && VM_W(0x10649ac0u)==VR_DONE;
}
static int z7_vr_ram(uint32_t p) { return p && !(p&3u) && p>=0xa1800000u && p<0xb0000000u; }
/* Capture task: release progress. Only records; returns 0 like upstream's. */
static uint32_t z7_vr_callback(uint32_t event, const uint32_t *arg, uint32_t c, uint32_t d)
{
    (void)c; (void)d;
    uint32_t a0=0xffffffffu,a1=0xffffffffu;
    if (z7_vr_ram((uint32_t)(uintptr_t)arg)) { a0=arg[0]; a1=arg[1]; }
    z7_vr_arg0=a0; z7_vr_arg1=a1;
    __atomic_store_n(&z7_vr_last_event,event,__ATOMIC_RELEASE);
    if (event==VR_DONE) __atomic_store_n(&z7_vr_done,a0 ? 2u : 1u,__ATOMIC_RELEASE);
    else if (event==VR_RELEASED) __atomic_store_n(&z7_vr_done,1u,__ATOMIC_RELEASE);  /* file still confirmed */
    __atomic_add_fetch(&z7_vr_events,1u,__ATOMIC_RELEASE);
    return 0;
}
#ifdef Z7_PIXEL_NIKON_MENU
/* Camera test (cb8cb929, Nov 27): OK (J) did not cancel a running group; the
 * GUI key callback is not called while shooting. Read the physical OK switch
 * (SW1 bit0, ID_SW1_OK) directly, as the shutter is, and latch the cancel. */
volatile uint32_t z7_pn_ok_cancels;
static uint32_t z7_pn_ok_down(void)
{
    if (!(VM_W(0xa1f90aa8u)&1u)) return 0;
    if (!__atomic_exchange_n(&z7_pm_cancel,1u,__ATOMIC_ACQ_REL)) ++z7_pn_ok_cancels;
    return 1;
}
#endif
static uint32_t z7_vr_touched(void) { return (VM_W(VR_SW0)&VR_SHUTTER_BITS)
#ifdef Z7_PIXEL_NIKON_MENU
    || z7_pn_ok_down()
#endif
#ifdef Z7_PIXEL_MENU
    || __atomic_load_n(&z7_pm_cancel,__ATOMIC_ACQUIRE)
#endif
    ; }
static void z7_vr_note_event(uint32_t frame)
{
    if (z7_vm_log.entries>=VM_ENTRIES) return;
    struct z7_vm_entry *e=&z7_vm_log.entry[z7_vm_log.entries++];
    e->tick=z7_vm_tick; e->phase=VR_PH_EVENT; e->poll=(uint8_t)frame; e->status=(uint16_t)z7_vr_last_event;
#ifdef Z7_PIXEL_NIKON_MENU
    e->pad[0]=(uint8_t)frame;e->pad[1]=(uint8_t)(frame>>8);
#endif
    uint32_t v[4]={z7_vr_last_event,z7_vr_arg0,z7_vr_arg1,z7_vr_events};
    for (uint32_t i=0;i<16u;++i) e->bytes[i]=(uint8_t)(v[i>>2]>>(8*(i&3u)));
    for (uint32_t i=16u;i<VM_TELEMETRY_BYTES;++i) e->bytes[i]=0;
}
#ifndef Z7_PIXEL_PROBE
/* One frame: position, confirm, fire, wait for Nikon's completion and the file. */
static int z7_vr_frame(uint32_t frame)
{
#ifdef Z7_PIXEL_MENU
    if (!z7_pm_capture_ready() || z7_vr_touched()
#ifdef Z7_PIXEL_NIKON_MENU
        || !z7_pn_exposure_matches() || z7_pn_capture_pending()
#endif
        ) return 0;
#endif
#ifdef Z7_PIXEL_SHIFT_V2
    if (z7_vs_preposition(frame)<=0) { z7_vm_log.flags|=VS_POSITION_MISSED; return 0; }
#endif
    int r=z7_vs_position(frame,VS_PH_SEND);
    if (r<=0) { if (!r && z7_vs_resends<VS_RESENDS) { ++z7_vs_resends; z7_vm_log.resends=z7_vs_resends; r=z7_vs_position(frame,VS_PH_RESEND); } }
    if (r<=0) return 0;
#ifdef Z7_PIXEL_SHIFT_V1
    z7_vm_sleep(VS_SETTLE_FRAME_MS);              /* let the body settle on the new position */
#ifdef Z7_PIXEL_NIKON_MENU
    while (frame && z7_pn_now()-z7_pn_frame_started<z7_pn_interval_ms()) {
        z7_vm_sleep(100);
        if (z7_vr_touched() || !z7_pm_capture_ready()) return 0;
    }
#endif
#ifdef Z7_PIXEL_NIKON_MENU
    /* One noisy read must not end the group: up to five reads 100 ms apart.
     * A real loss (normal state or another target) never matches. */
    {
        uint32_t held=0;
        for (uint32_t n=0;n<5u && !(held=(uint32_t)z7_vs_matches_now(frame));++n) {
            z7_vm_sleep(100);
            if (z7_vr_touched()) break;
        }
        if (!held) { z7_vm_log.flags|=VS_HOLD_LOST; return 0; }
    }
#else
    if (!z7_vs_matches_now(frame)) { z7_vm_log.flags|=VS_HOLD_LOST; return 0; }
#endif
#endif
    if (z7_vr_touched()) { z7_vm_log.flags|=VR_TOUCHED; return 0; }
#ifdef Z7_PIXEL_MENU
    if (!z7_pm_capture_ready()) { z7_vm_log.flags|=VR_FRAME_FAILED; return 0; }
#endif
#ifdef Z7_PIXEL_NIKON_MENU
    if (!z7_pn_exposure_matches()) { z7_vm_log.flags|=VR_FRAME_FAILED;return 0; }
#endif
    if (VM_W(VR_SLOT)) { z7_vm_log.flags|=VR_SLOT_BUSY; return 0; }
    uint32_t photos=__atomic_load_n(&z7_vs_photos,__ATOMIC_ACQUIRE), mark=z7_vr_sound_mark();
#ifdef Z7_PIXEL_NIKON_MENU
    z7_pn_frame_started=z7_pn_now();
#endif
    __atomic_store_n(&z7_vr_done,0u,__ATOMIC_RELEASE);
    uint32_t result=VM_F(VR_RELEASE,uint32_t,const struct z7_vr_request *,
        uint32_t (*)(uint32_t,const uint32_t *,uint32_t,uint32_t))(&z7_vr_request,z7_vr_callback);
    z7_vm_record(VR_PH_FIRE,frame,result,0);
    if (result) { z7_vm_log.flags|=VR_REFUSED; return 0; }
    z7_vm_log.flags|=VR_FIRED;
    for (uint32_t i=0;i<
#ifdef Z7_PIXEL_NIKON_MENU
        z7_pn_capture_wait_polls()
#else
        300u
#endif
        ;++i) {
        z7_vm_sleep(50);
        uint32_t done=__atomic_load_n(&z7_vr_done,__ATOMIC_ACQUIRE);
        if (done==2u) { z7_vr_note_event(frame); z7_vm_log.flags|=VR_FRAME_FAILED; return 0; }
        if (done && __atomic_load_n(&z7_vs_photos,__ATOMIC_ACQUIRE)>photos) {
#if defined(Z7_PIXEL_NIKON_MENU)
            /* Camera run 13e0ce7d: once the capture completes Nikon returns VR to
             * normal (state 1), as the proven v2 series also tolerated. The hold
             * was verified immediately before the release and the next frame
             * re-sends its position, so only log the post-capture state. */
            (void)z7_vs_matches_now(frame);
#elif defined(Z7_PIXEL_MENU)
            if (!z7_vs_matches_now(frame)) { z7_vm_log.flags|=VS_HOLD_LOST; return 0; }
#endif
#ifdef Z7_PIXEL_NIKON_MENU
            if (!z7_pn_exposure_matches() || !z7_pm_capture_ready()) { z7_vm_log.flags|=VR_FRAME_FAILED;return 0; }
#endif
            z7_vr_note_event(frame);
            z7_vm_record(VS_PH_FRAME,frame+1u,0,0);
            z7_vr_count_click(mark);
            return 1;
        }
    }
    z7_vr_note_event(frame); z7_vm_log.flags|=VR_FRAME_FAILED;
    return 0;
}
static void z7_vr_series(void)
{
    uint32_t free_polls=0;
    for (uint32_t i=0;i<100u && free_polls<5u;++i) { z7_vm_sleep(100); free_polls=z7_vr_touched() ? 0u : free_polls+1u; }
    z7_vm_record(VR_PH_FREE,free_polls,0,0);
    if (free_polls<5u) { z7_vm_log.flags|=VR_NOT_FREED; z7_vs_finish(); return; }
#ifdef Z7_PIXEL_SHIFT_V1
#ifdef Z7_PIXEL_NIKON_MENU
    uint32_t settle_started=z7_pn_now();
    z7_pn_elapsed=0;
    while (z7_pn_now()-settle_started<VS_SETTLE_START_MS ||
           z7_pn_now()-z7_pn_pressed_at<z7_pn_delay_ms()) {
#else
    for (uint32_t i=0;i<VS_SETTLE_START_MS/100u;++i) {
#endif
        z7_vm_sleep(100);
        if (z7_vr_touched()) { z7_vm_log.flags|=VR_TOUCHED; z7_vs_finish(); return; }
    }
#endif
    uint32_t frame=0;
#ifdef Z7_PIXEL_NIKON_MENU
    if (!z7_pm_capture_ready()) { z7_vs_finish();return; }
    while (frame<Z7_VS_FRAME_COUNT) {
        if (!(frame&(z7_pn_job_shots-1u))) {
            uint32_t group=frame>>z7_pn_job_shift;
            if (group) {
                z7_vs_finish();
                if (!(z7_vm_log.flags&VM_RESTORED) || z7_vr_touched()) break;
                z7_pm_running=1;z7_vm_stage=4;
            }
            if (!z7_pn_group_exposure(group) || !z7_pn_start_folder()) break;
            z7_pn_log_exposure();z7_vm_save();
            if (z7_pn_log_error) { z7_pn_job_error=4;break; }
            if (group) {
                /* Exposure setters may reapply native VR. Verify normal state,
                 * snapshot the new native D2 selection and settle before hold. */
                uint32_t stable=0;
                for (uint32_t n=0;n<VM_POLLS;++n) {
                    z7_vm_sleep(100);
                    uint32_t s=z7_vm_sample(VM_PH_ARM,n);
                    stable=!s && z7_vm_output[VM_STATE]==VM_NORMAL && z7_vm_settled(z7_vm_output,48) ? stable+1u : 0u;
                    if (stable==2u || z7_vr_touched()) break;
                }
                if (stable!=2u || z7_vr_touched() || !z7_vm_snapshot()) break;
                for (uint32_t n=0;n<VS_SETTLE_START_MS/100u;++n) {
                    z7_vm_sleep(100);if (z7_vr_touched()) break;
                }
                if (z7_vr_touched()) break;
                z7_vm_log.flags&=~(VM_MOVE_SENT|VM_MOVE_ACK|VM_MOVE_FOLLOWED|VM_CENTRE_SENT|VM_CENTRE_ACK|VM_CENTRE_FOLLOWED|VM_RESTORED);
            }
        }
        if (!z7_vr_frame(frame)) break;
        ++frame;
        if (!(frame&(z7_pn_job_shots-1u))) z7_vm_log.groups_complete=frame>>z7_pn_job_shift;
    }
#else
    while (frame<Z7_VS_FRAME_COUNT && z7_vr_frame(frame)) ++frame;
#endif
    if (frame==Z7_VS_FRAME_COUNT) z7_vm_log.flags|=VS_SERIES_COMPLETE;
    z7_vs_finish();
}
#endif /* !Z7_PIXEL_PROBE */
#ifdef Z7_PIXEL_PROBE
/* GEOMETRY PROBE (step 3c). The 3b2bb075 series showed that x = 21 moves the
 * image about 1.1 px but y (both "vertical" actuators equal) moves it only a
 * little sideways: the Z7 actuator layout differs from the Z7II. One module-
 * fired frame per position-command variant, each only if the telemetry shows
 * the hold reached and every target within +-VP_LIMIT counts; otherwise the
 * sensor is recentred at once and that frame skipped. Then three ways to end
 * the hold, stopping at the first that works (state no longer 0x40):
 *   1. Nikon's D2 sender 0x101C63F8 with the apply flags sel[1]|0x80 (what
 *      Nikon's VR-mode apply 0x101C69D8 passes; the 3b re-send used flags 3);
 *   2. Nikon's own BodyVr event bit 4 (task 0xA23826D0, post 0x1017088C; its
 *      handler 0x101DF34C re-applies the VR mode in Nikon's task);
 *   3. Nikon's apply 0x101C69D8(selection, callback) itself.
 */
#ifdef Z7_PIXEL_DEADZONE
/* Y DEAD-ZONE RUN (step 3e). The raw analysis of f4e46989 showed 18-step y
 * moves shift the image by only about 0.06 px while 36/72-step y and all x
 * moves are proportional. 20 frames: a discarded first frame (the first
 * exposure catches the body moving), then y +-18/+-36/+54 each between
 * references, an x 20 control, and y 18 / -18 reached from above and below
 * (54 -> 18, -54 -> -18) to test direction dependence. All targets <= 216. */
#define VP_XY(x,y) {0,(uint8_t)((x)&0xff),(uint8_t)(((x)>>8)&0xff),(uint8_t)((y)&0xff),(uint8_t)(((y)>>8)&0xff),16,16,0,0,2}
enum { VP_VARIANTS=20u, VP_SETTLE_START_MS=2000u, VP_SETTLE_FRAME_MS=500u };
#elif defined(Z7_PIXEL_CALIB)
/* CALIBRATION RUN (step 3d). Payload layout found by the probe (d6e6db28):
 * x = little-endian int16 at bytes 1-2, y at bytes 3-4, target = -4 * step.
 * Larger steps (about 2-4 px) for signal, both signs, a diagonal, and the
 * reference repeated three times to measure the noise. All targets <= 320. */
#define VP_XY(x,y) {0,(uint8_t)((x)&0xff),(uint8_t)(((x)>>8)&0xff),(uint8_t)((y)&0xff),(uint8_t)(((y)>>8)&0xff),16,16,0,0,2}
enum { VP_VARIANTS=9u };
#else
enum { VP_VARIANTS=7u };
#endif
enum {
    VP_LIMIT=400,
    VP_TASK=0xa23826d0u, VP_POST=0x1017088du, VP_APPLY=0x101c69d9u,
    VP_PH_VARIANT=0x1cu, VP_PH_SKIP=0x1du, VP_PH_RESTORE=0x1eu, VP_PH_RESTORE_POLL=0x1fu,
    VP_SKIPPED=1u<<28, VP_RESTORE_WORKED=1u<<29
};
static const uint8_t z7_vp_variant[VP_VARIANTS][10]={
#ifdef Z7_PIXEL_DEADZONE
    VP_XY(0,0), VP_XY(0,0), VP_XY(0,18), VP_XY(0,0), VP_XY(0,36), VP_XY(0,0), VP_XY(0,54), VP_XY(0,0),
    VP_XY(0,-18), VP_XY(0,0), VP_XY(0,-36), VP_XY(0,0), VP_XY(20,0), VP_XY(0,0),
    VP_XY(0,54), VP_XY(0,18), VP_XY(0,0), VP_XY(0,-54), VP_XY(0,-18), VP_XY(0,0),
#elif defined(Z7_PIXEL_CALIB)
    VP_XY(0,0), VP_XY(80,0), VP_XY(0,0), VP_XY(-80,0), VP_XY(0,72),
    VP_XY(0,0), VP_XY(0,-72), VP_XY(40,36), VP_XY(0,0),
#else
    {0,0,0,0,0,16,16,0,0,2},          /* V0 reference */
    {0,19,0,0,0,16,16,0,0,2},         /* V1 x = 19 (about 1 px) */
    {0,0,0,18,0,16,16,0,0,2},         /* V2 y = 18 (repeat) */
    {0,0,0,0,18,16,16,0,0,2},         /* V3 byte 4 */
    {0,0,0,18,0,24,8,0,0,2},          /* V4 y = 18 with bytes 5/6 split */
    {0,0,0xff,0xee,0,16,16,0,0,2},    /* V5 y = -18 if int16 */
    {0xff,0xed,0,0,0,16,16,0,0,2},    /* V6 x = -19 if int16 */
#endif
};
volatile uint32_t z7_vp_restore_method, z7_vp_apply_called;
static uint32_t z7_vp_native_ok(void)
{
    return VM_W(VP_POST-1u)==0xf0003020u && VM_W(VP_APPLY-1u)==0x4604b5feu && VM_W(VP_APPLY+3u)==0x460e4892u;
}
static int z7_vp_in_limit(const uint8_t *t)
{
    for (uint32_t a=0;a<3u;++a) if (z7_vm_abs(z7_vm_word(t+2*a))>(int)VP_LIMIT) return 0;
    return 1;
}
/* Send variant v; 1 held within limits, 0 skipped (recentred), -1 stop. */
static int z7_vp_hold(uint32_t v)
{
    for (uint32_t i=0;i<10u;++i) z7_vs_payload[i]=z7_vp_variant[v][i];
    uint32_t s=z7_vm_exchange(VM_POSITION,z7_vs_payload);
    z7_vm_record(VP_PH_VARIANT,v,s,0);
    if (z7_vm_applied(s)) z7_vm_log.flags|=VM_MOVE_SENT;
    if (s) return z7_vm_applied(s) ? -1 : 0;
    int run=0;
    for (uint32_t i=0;i<VM_POLLS;++i) {
        z7_vm_sleep(100);
        uint32_t r=z7_vm_sample(VS_PH_FOLLOW,(v<<5)|(i+1u));
        if (r==VM_PENDING) return -1;
        const uint8_t *t=z7_vm_output;
        if (!r && !z7_vp_in_limit(t)) break;            /* outside the safe range */
        run=!r && t[VM_STATE]==VM_HOLD && z7_vm_settled(t,24) ? run+1 : 0;
        if (run==2) { z7_vm_log.flags|=VM_MOVE_FOLLOWED; return 1; }
    }
    z7_vm_log.flags|=VP_SKIPPED;
    uint32_t c=z7_vm_exchange(VM_POSITION,z7_vm_centre);
    z7_vm_record(VP_PH_SKIP,v,c,0);
    if (c) return -1;
    return z7_vm_follow(VM_PH_CENTRE,0) ? 0 : -1;
}
/* Fire one frame at the held variant; 1 done, 0 stop. */
static int z7_vp_fire(uint32_t v)
{
    if (z7_vr_touched()) { z7_vm_log.flags|=VR_TOUCHED; return 0; }
    if (VM_W(VR_SLOT)) { z7_vm_log.flags|=VR_SLOT_BUSY; return 0; }
    uint32_t photos=__atomic_load_n(&z7_vs_photos,__ATOMIC_ACQUIRE), mark=z7_vr_sound_mark();
    __atomic_store_n(&z7_vr_done,0u,__ATOMIC_RELEASE);
    uint32_t result=VM_F(VR_RELEASE,uint32_t,const struct z7_vr_request *,
        uint32_t (*)(uint32_t,const uint32_t *,uint32_t,uint32_t))(&z7_vr_request,z7_vr_callback);
    z7_vm_record(VR_PH_FIRE,v,result,0);
    if (result) { z7_vm_log.flags|=VR_REFUSED; return 0; }
    z7_vm_log.flags|=VR_FIRED;
    for (uint32_t i=0;i<
#ifdef Z7_PIXEL_NIKON_MENU
        z7_pn_capture_wait_polls()
#else
        300u
#endif
        ;++i) {
        z7_vm_sleep(50);
        uint32_t done=__atomic_load_n(&z7_vr_done,__ATOMIC_ACQUIRE);
        if (done==2u) break;
        if (done && __atomic_load_n(&z7_vs_photos,__ATOMIC_ACQUIRE)>photos) {
            z7_vr_note_event(v); z7_vm_record(VS_PH_FRAME,v+1u,0,0); z7_vr_count_click(mark);
            return 1;
        }
    }
    z7_vr_note_event(v); z7_vm_log.flags|=VR_FRAME_FAILED;
    return 0;
}
static void z7_vp_apply_done(uint32_t event) { (void)event; __atomic_store_n(&z7_vp_apply_called,1u,__ATOMIC_RELEASE); }
/* Poll up to 1.5 s for the hold to end. */
static int z7_vp_released(uint32_t method)
{
    for (uint32_t i=0;i<15u;++i) {
        z7_vm_sleep(100);
        uint32_t s=z7_vm_sample(VP_PH_RESTORE_POLL,(method<<5)|(i+1u));
        if (s==VM_PENDING) return 0;
        uint32_t state=z7_vm_output[VM_STATE];
        if (!s && state!=VM_HOLD && state!=0x88u) { z7_vm_log.restore_state=state; return 1; }
    }
    return 0;
}
static void z7_vp_restore(void)
{
    uint32_t v=z7_vm_d2_value();
    if ((v&0xffu)<1u || (v&0xffu)>3u) v=z7_vm_log.d2;            /* Nikon's latest, else the snapshot */
    z7_vm_selection[0]=(uint8_t)v; z7_vm_selection[1]=(uint8_t)(v>>8);
    for (uint32_t method=1;method<=3u;++method) {
        for (uint32_t j=0;j<50u && !z7_vm_service_idle();++j) z7_vm_sleep(20);
        uint32_t r=0x100u;
        if (z7_vm_service_idle()) {
            if (method==1u) r=VM_F(VM_D2_SEND,uint32_t,const uint8_t *,uint32_t,void (*)(uint32_t))(z7_vm_selection,(uint32_t)z7_vm_selection[1]|0x80u,z7_vm_d2_complete);
            else if (method==2u) { VM_F(VP_POST,void,uint32_t,uint32_t)(VP_TASK,0x10u); r=1u; }
            else r=VM_F(VP_APPLY,uint32_t,const uint8_t *,void (*)(uint32_t))(z7_vm_selection,z7_vp_apply_done);
        }
        z7_vm_record(VP_PH_RESTORE,method,r,0);
        if (r==1u) z7_vm_log.flags|=VM_RESTORE_SENT;
        if (z7_vp_released(method)) {
            z7_vp_restore_method=method; z7_vm_log.restore=method|(r&0xffu)<<8;
            z7_vm_log.flags|=VM_RESTORED|VP_RESTORE_WORKED;
            return;
        }
    }
}
static void z7_vp_series(void)
{
    uint32_t free_polls=0;
    for (uint32_t i=0;i<100u && free_polls<5u;++i) { z7_vm_sleep(100); free_polls=z7_vr_touched() ? 0u : free_polls+1u; }
    z7_vm_record(VR_PH_FREE,free_polls,0,0);
    if (free_polls<5u) { z7_vm_log.flags|=VR_NOT_FREED; z7_vm_stage=2; z7_vm_save(); return; }
#ifdef Z7_PIXEL_DEADZONE
    for (uint32_t i=0;i<VP_SETTLE_START_MS/100u;++i) {
        z7_vm_sleep(100);
        if (z7_vr_touched()) { z7_vm_log.flags|=VR_TOUCHED; z7_vm_stage=2; z7_vm_save(); return; }
    }
#endif
    uint32_t v=0, shots=0;
    for (;v<VP_VARIANTS;++v) {
        int h=z7_vp_hold(v);
        if (h<0) break;
        if (!h) continue;
#ifdef Z7_PIXEL_DEADZONE
        z7_vm_sleep(VP_SETTLE_FRAME_MS);          /* let the body settle on the new position */
#endif
        if (!z7_vp_fire(v)) break;
        ++shots;
    }
    if (v==VP_VARIANTS) z7_vm_log.flags|=VS_SERIES_COMPLETE;
    z7_vm_stage=2;
    uint32_t s=0x100u;
    if (z7_vm_log.flags&VM_MOVE_SENT) for (uint32_t i=0;i<5u;++i) {
        s=z7_vm_exchange(VM_POSITION,z7_vm_centre);
        z7_vm_record(VM_PH_CENTRE_SEND,i,s,0);
        if (z7_vm_applied(s)) z7_vm_log.flags|=VM_CENTRE_SENT;
        if (!s) break;
        z7_vm_sleep(s==VM_PENDING ? 500 : 200);
    }
    if (!s) { z7_vm_log.flags|=VM_CENTRE_ACK; if (z7_vm_follow(VM_PH_CENTRE,0)) z7_vm_log.flags|=VM_CENTRE_FOLLOWED; }
    if (z7_vm_log.flags&VM_MOVE_SENT) z7_vp_restore();
    z7_vm_log.frames=shots;
    z7_vm_save();
}
#endif
#endif
/* Resident worker only (replaces the one-move worker in this build). */
static void z7_vm_worker(void)
{
#ifdef Z7_PIXEL_NIKON_MENU
    if (z7_vm_stage==5u) { if (!z7_pn_capture_pending()) z7_vs_finish();return; }
#endif
#ifdef Z7_PIXEL_MENU
    if (!z7_vm_stage && (!__atomic_load_n(&z7_pm_requested,__ATOMIC_ACQUIRE) || !z7_pm_capture_ready())) return;
#endif
    if (z7_vm_stage==3u || !z7_vm_native_ok()) return;
#ifdef Z7_PIXEL_RELEASE
    if (!z7_vr_native_ok()) return;
#endif
#ifdef Z7_PIXEL_PROBE
    if (!z7_vp_native_ok()) return;
#endif
    ++z7_vm_tick;
    if (!z7_vm_stage) {                             /* ARM, as the one-move test */
        if (z7_vm_tick>VM_ARM_TICKS) { z7_vm_log.flags|=VM_GAVE_UP|VM_DONE; z7_vm_stage=3; z7_vm_save(); return; }
        if (!z7_vm_idle()) return;
        uint32_t s=z7_vm_exchange(VM_READ,0);
        const uint8_t *t=z7_vm_output;
        uint32_t state=s ? 0x100u : t[VM_STATE];
        if (z7_vm_arm_logged<VM_ARM_ENTRIES && (state!=z7_vm_last_state || z7_vm_tick%15u==1u)) {
            z7_vm_record(VM_PH_ARM,0,s,t); ++z7_vm_arm_logged;
        }
        z7_vm_last_state=state;
        if (s==VM_PENDING) { z7_vm_log.flags|=VM_DONE; z7_vm_stage=3; z7_vm_save(); return; }
        z7_vm_armed=!s && state==VM_NORMAL && z7_vm_settled(t,48);
#if defined(Z7_PIXEL_RELEASE) && !defined(Z7_PIXEL_NIKON_MENU)
        if (!(VM_W(VR_SW0)&VR_HALF_BITS)) z7_vm_armed=0;   /* only on a deliberate half-press */
#endif
        if (z7_vm_armed) {
            z7_vm_sleep(100);
            s=z7_vm_sample(VM_PH_ARM,1);
            z7_vm_armed=!s && z7_vm_output[VM_STATE]==VM_NORMAL && z7_vm_settled(z7_vm_output,48);
            if (s==VM_PENDING) { z7_vm_log.flags|=VM_DONE; z7_vm_stage=3; z7_vm_save(); return; }
        }
        if (!z7_vm_armed) { if (z7_vm_tick%30u==0u) z7_vm_save(); return; }
        if (!z7_vm_snapshot()) { z7_vm_log.flags|=VM_DONE; z7_vm_stage=3; z7_vm_save(); return; }
        z7_vm_log.flags|=VM_ARMED|VS_SERIES_STARTED;
#ifdef Z7_PIXEL_MENU
        __atomic_store_n(&z7_pm_running,1u,__ATOMIC_RELEASE);
#endif
        z7_vs_frame=0; z7_vs_seen=0; z7_vs_wait=0;
        __atomic_store_n(&z7_vs_photos,0u,__ATOMIC_RELEASE);
        __atomic_store_n(&z7_vm_stage,4u,__ATOMIC_RELEASE);  /* count photos from here */
#ifdef Z7_PIXEL_RELEASE
#ifdef Z7_PIXEL_PROBE
        z7_vp_series();                             /* one frame per command variant */
#else
        z7_vr_series();                             /* fires the four frames itself */
#endif
#else
        if (z7_vs_position(0,VS_PH_SEND)<0) { z7_vs_finish(); }
#endif
        z7_vm_save();
        return;
    }
    if (z7_vm_stage==4u) {                          /* SERIES */
        uint32_t photos=__atomic_load_n(&z7_vs_photos,__ATOMIC_ACQUIRE);
        if (photos>z7_vs_seen) {
            if (photos>z7_vs_seen+1u) z7_vm_log.flags|=VS_MOVED_LATE;   /* two photos in one tick */
            z7_vs_seen=photos; z7_vs_wait=0;
            z7_vm_record(VS_PH_FRAME,photos,0,0);
            if (photos>=VS_FRAMES) { z7_vm_log.flags|=VS_SERIES_COMPLETE; z7_vs_finish(); return; }
            z7_vs_frame=photos;
            if (z7_vs_position(photos,VS_PH_SEND)<0) { z7_vs_finish(); return; }
            z7_vm_save();
            return;
        }
        if (++z7_vs_wait>VS_WAIT_TICKS) { z7_vm_log.flags|=VS_FRAME_TIMEOUT; z7_vs_finish(); return; }
        if (!z7_vm_idle()) return;
        uint32_t s=z7_vm_exchange(VM_READ,0);
        if (s==VM_PENDING) { z7_vs_finish(); return; }
        int x,y; z7_vs_target(z7_vs_frame,&x,&y);
        uint32_t held=!s && z7_vs_matches(z7_vm_output,x,y);
        uint32_t state=s ? 0x100u : z7_vm_output[VM_STATE];
        if (state!=z7_vs_last_wait_state || !held || z7_vs_wait%5u==1u) z7_vm_record(VS_PH_WAIT,z7_vs_frame,s,z7_vm_output);
        z7_vs_last_wait_state=state;
        if (!s && !held) {
            z7_vm_log.flags|=VS_HOLD_LOST;
            if (z7_vs_resends<VS_RESENDS) {
                ++z7_vs_resends; z7_vm_log.resends=z7_vs_resends;
                if (z7_vs_position(z7_vs_frame,VS_PH_RESEND)<0) { z7_vs_finish(); return; }
            }
        }
        if (z7_vs_wait%10u==0u) z7_vm_save();
        return;
    }
    /* WATCH (stage 2), as the one-move test. */
    uint32_t s=z7_vm_sample(VM_PH_WATCH,0);
    if (!s && z7_vm_output[VM_STATE]==VM_NORMAL) z7_vm_log.flags|=VM_NORMAL_AGAIN;
    if (s==VM_PENDING || ++z7_vm_watch>=VM_WATCH_TICKS
#ifdef Z7_PIXEL_NIKON_MENU
        /* Camera test (cb8cb929): the 30 s watch kept the menu busy, so picking
         * a new shot count right after a group was ignored. Normal VR is the
         * watch's purpose; end it as soon as that is seen. */
        || (z7_vm_log.flags&VM_NORMAL_AGAIN)
#endif
        ) { z7_vm_log.flags|=VM_DONE; z7_vm_stage=3; }
    if (z7_vm_stage==3u || z7_vm_watch%10u==0u) z7_vm_save();
}
#endif
