/* SPDX-License-Identifier: MIT. Independent original-Z7 C 3.80 controls.
 * Menu actions only arm/cancel. Sensor/capture work stays on the worker.
 * Settings are volatile: boot always starts disarmed at four frames.
 */
#ifndef Z7_PIXEL_SHIFT_MENU_H
#define Z7_PIXEL_SHIFT_MENU_H
#ifdef Z7_PIXEL_NIKON_MENU
static const uint32_t z7_pm_counts[4]={4,8,16,32};
volatile uint32_t z7_pn_mode;
#define Z7_PM_COUNT_CHOICES 4u
#else
static const uint32_t z7_pm_counts[3]={4,16,32};
#define Z7_PM_COUNT_CHOICES 3u
#endif
volatile uint32_t z7_pm_count_index, z7_pm_requested, z7_pm_cancel, z7_pm_running;
/* 0 free, 1 worker, 2 menu reset. Cancelling never waits for this lock. */
volatile uint32_t z7_pm_lock;
static uint32_t sm_menu_visible(void);
#ifdef Z7_PIXEL_NIKON_MENU
static uint32_t z7_pn_capture_settings_match(void);
#endif
static uint32_t z7_pm_count(void) { return z7_pm_counts[z7_pm_count_index<Z7_PM_COUNT_CHOICES ? z7_pm_count_index : 0u]; }
static const char *z7_pm_count_text(void) {
#ifdef Z7_PIXEL_NIKON_MENU
    static const char *const text[]={"4","8","16","32"};
    return text[z7_pm_count_index<4u ? z7_pm_count_index : 0u];
#else
    return z7_pm_count_index==2 ? "32" : z7_pm_count_index==1 ? "16" : "4";
#endif
}
static const char *z7_pm_status(void)
{
    if (z7_pm_running) return "Running";
    if (z7_pm_requested) return "Armed";
    if (z7_vm_stage==2u) return "Wait";
    if (z7_vm_log.flags&VM_TIMED_OUT) return "Restart";
    if ((z7_vm_log.flags&VM_MOVE_SENT) &&
        (z7_vm_log.flags&(VM_CENTRE_FOLLOWED|VM_RESTORED))!=(VM_CENTRE_FOLLOWED|VM_RESTORED)) return "Restart";
    if (z7_vm_log.flags&VS_SERIES_COMPLETE) return "Done";
    if (z7_vm_log.flags) return "Stopped";
    return "Ready";
}
#ifndef Z7_PIXEL_NIKON_MENU
static void z7_pm_next_count(void)
{
    if (!z7_pm_requested && !z7_pm_running && z7_vm_stage!=2u)
        z7_pm_count_index=(z7_pm_count_index+1u)%Z7_PM_COUNT_CHOICES;
}
#endif
static void z7_pm_arm(void)
{
    if (z7_pm_requested || z7_pm_running) {
        __atomic_store_n(&z7_pm_cancel,1u,__ATOMIC_RELEASE);
        __atomic_store_n(&z7_pm_requested,0u,__ATOMIC_RELEASE);
        return;
    }
    uint32_t free=0;
    if (!__atomic_compare_exchange_n(&z7_pm_lock,&free,2u,0,__ATOMIC_ACQ_REL,__ATOMIC_ACQUIRE)) return;
    if (z7_vm_stage==2u || (z7_vm_log.flags&VM_TIMED_OUT)) {
        __atomic_store_n(&z7_pm_lock,0u,__ATOMIC_RELEASE); return;
    }
    /* After any sensor move, a new group needs confirmed centering AND restore. */
    if ((z7_vm_log.flags&VM_MOVE_SENT) &&
        (z7_vm_log.flags&(VM_CENTRE_FOLLOWED|VM_RESTORED))!=(VM_CENTRE_FOLLOWED|VM_RESTORED)) {
        __atomic_store_n(&z7_pm_lock,0u,__ATOMIC_RELEASE); return;
    }
#ifdef Z7_PIXEL_NIKON_MENU
    uint32_t *log=(uint32_t *)&z7_vm_log;
    _Static_assert(sizeof(z7_vm_log)%4u==0,"word-aligned pixel log");
    for (uint32_t i=0;i<sizeof(z7_vm_log)/4u;++i) log[i]=0;
#else
    uint8_t *log=(uint8_t *)&z7_vm_log;
    for (uint32_t i=0;i<sizeof(z7_vm_log);++i) log[i]=0;
#endif
    z7_vm_tick=z7_vm_stage=z7_vm_armed=z7_vm_watch=z7_vm_arm_logged=z7_vm_last_state=0;
    z7_vs_seen=z7_vs_frame=z7_vs_wait=z7_vs_resends=z7_vs_last_wait_state=0;
    z7_vs_last_key=0;
    z7_vs_photos=0;
    __atomic_store_n(&z7_pm_cancel,0u,__ATOMIC_RELEASE);
    __atomic_store_n(&z7_pm_requested,1u,__ATOMIC_RELEASE);
    __atomic_store_n(&z7_pm_lock,0u,__ATOMIC_RELEASE);
}
/* Read-only guards. The original-Z7 property table has release mode 0x209,
 * self timer 0x008 and Silent photography 0x576. Never write Z7II settings.
 * S=0 and self timer=0 are required; the user keeps control of their setup.
 */
static uint32_t z7_pm_capture_context(void)
{
    return !__atomic_load_n(&z7_pm_cancel,__ATOMIC_ACQUIRE) &&
#ifdef Z7_PIXEL_NIKON_MENU
        __atomic_load_n(&z7_pn_mode,__ATOMIC_ACQUIRE)!=0u &&
#endif
        !sm_menu_visible() &&
        VM_W(0xa201d510u)==0u && /* original-Z7 photo mode, as the battery/AF guards */
        !*(volatile uint8_t *)(uintptr_t)0xa18237c6u && /* menu/playback */
        VM_W(0x104065a4u)==0xbf03f5ceu &&
#ifndef Z7_PIXEL_NIKON_MENU
        VM_F(0x104065a5u,uint32_t,uint32_t)(0x209u)==0u &&
        VM_F(0x104065a5u,uint32_t,uint32_t)(0x008u)==0u &&
        VM_F(0x104065a5u,uint32_t,uint32_t)(0x576u)==1u &&
#endif
        1;
}
static uint32_t z7_pm_capture_ready(void)
{
    return z7_pm_capture_context()
#ifdef Z7_PIXEL_NIKON_MENU
        && z7_pn_capture_settings_match()
#endif
        ;
}
#endif
