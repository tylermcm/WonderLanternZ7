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

/* Still-file hook (Nikon's task): one count per new photo record. */
static void z7_vs_still(uint32_t key)
{
    if (__atomic_load_n(&z7_vm_stage,__ATOMIC_ACQUIRE)!=4u) return;
    uint32_t n=__atomic_load_n(&z7_vs_photos,__ATOMIC_ACQUIRE);
    if (n<VS_FRAMES) z7_vm_log.keys[n]=key;
    __atomic_store_n(&z7_vs_photos,n+1u,__ATOMIC_RELEASE);
}
#define Z7_STILL_KEY_HOOK(key) z7_vs_still(key)

static void z7_vs_target(uint32_t frame, int *x, int *y)
{
    *x=21*(int)z7_vs_corner[frame&3u][0]; *y=18*(int)z7_vs_corner[frame&3u][1];
}
static int z7_vs_matches(const uint8_t *t, int x, int y)
{
    return t[VM_STATE]==VM_HOLD && z7_vm_word(t)==-4*x && z7_vm_word(t+2)==-4*y &&
        z7_vm_word(t+4)==-4*y && z7_vm_settled(t,24);
}
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
static void z7_vs_finish(void)
{
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
}
/* Resident worker only (replaces the one-move worker in this build). */
static void z7_vm_worker(void)
{
    if (z7_vm_stage==3u || !z7_vm_native_ok()) return;
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
        if (z7_vm_armed) {
            z7_vm_sleep(100);
            s=z7_vm_sample(VM_PH_ARM,1);
            z7_vm_armed=!s && z7_vm_output[VM_STATE]==VM_NORMAL && z7_vm_settled(z7_vm_output,48);
            if (s==VM_PENDING) { z7_vm_log.flags|=VM_DONE; z7_vm_stage=3; z7_vm_save(); return; }
        }
        if (!z7_vm_armed) { if (z7_vm_tick%30u==0u) z7_vm_save(); return; }
        if (!z7_vm_snapshot()) { z7_vm_log.flags|=VM_DONE; z7_vm_stage=3; z7_vm_save(); return; }
        z7_vm_log.flags|=VM_ARMED|VS_SERIES_STARTED;
        z7_vs_frame=0; z7_vs_seen=0; z7_vs_wait=0;
        __atomic_store_n(&z7_vs_photos,0u,__ATOMIC_RELEASE);
        __atomic_store_n(&z7_vm_stage,4u,__ATOMIC_RELEASE);  /* count photos from here */
        if (z7_vs_position(0,VS_PH_SEND)<0) { z7_vs_finish(); }
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
    if (s==VM_PENDING || ++z7_vm_watch>=VM_WATCH_TICKS) { z7_vm_log.flags|=VM_DONE; z7_vm_stage=3; }
    if (z7_vm_stage==3u || z7_vm_watch%10u==0u) z7_vm_save();
}
#endif
