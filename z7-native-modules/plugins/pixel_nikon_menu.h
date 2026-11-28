/* SPDX-License-Identifier: MIT. Independent original-Z7 C 3.80 controls.
 * Nikon's public Z6III/Z8 menu is the naming/organization reference.
 * Full shutter input is queued to the resident capture worker.
 * Advanced options stay unavailable until original-Z7 bindings are verified.
 */
#ifndef Z7_PIXEL_NIKON_MENU_H
#define Z7_PIXEL_NIKON_MENU_H
enum { PN_OFF=0u, PN_SERIES=1u, PN_SINGLE=2u };
static const uint8_t z7_pn_delays[]={0,1,2,3,5,10};
/* Interval is seconds, not an index: Nikon's numeric range is 00..30. */
volatile uint32_t z7_pn_delay_index, z7_pn_interval_index, z7_pn_interval_draft, z7_pn_previous_half;
volatile uint32_t z7_pn_input_ready,z7_pn_full_pending;
volatile uint32_t z7_pn_pressed_at;
extern volatile uint32_t z7_pn_raw_error;
extern volatile uint32_t z7_pn_job_active,z7_pn_exposure_owned;
static uint32_t z7_pn_cleanup_log_pending;
volatile uint32_t z7_pn_new_folder,z7_pn_reset_numbering,z7_pn_folder_result;
static uint32_t z7_pn_folder_matches(void)
{
    return VM_W(0x1031fa9cu)==0x2232b570u && VM_W(0x1031fb12u)==0x4896b510u &&
           VM_W(0x102717f6u)==0x460ab538u;
}
static uint32_t z7_pn_start_folder(void)
{
    if (!z7_pn_new_folder) return 1;
    z7_pn_folder_result=0x04390089u;
    if (!z7_pn_folder_matches() || !VM_F(0x1031fb13u,uint32_t,void)()) return 0;
    /* Nikon's own focus-shift/interval helper selects the next unused DCF
     * folder (100..999) under its card-manager lock; optionally resets the
     * file counter. No filenames, directories or photo records are rewritten. */
    z7_pn_folder_result=VM_F(0x1031fa9du,uint32_t,uint32_t)(!!z7_pn_reset_numbering);
    return z7_pn_folder_result==0x04390080u;
}
static uint32_t z7_pn_now(void)
{
    uint32_t time[2]={0,0};
    VM_F(0x101f50cdu,void,uint32_t *)(time);
    return time[1]; /* Native callers compare this millisecond word with 500. */
}
static char z7_pn_interval_buffer[5];
/* Counts requested native sleeps, conservatively excluding processing time. */
volatile uint32_t z7_pn_elapsed, z7_pn_frame_started;
static uint32_t z7_pn_help_focus=4u;
static void z7_pn_prepare(void);
static void z7_pn_save_worker(void);
static uint32_t z7_pn_busy(void) { return z7_pm_running || z7_pm_requested || z7_pn_full_pending || z7_pn_job_active || z7_vm_stage==2u; }
static uint32_t z7_pn_delay_ms(void) { return 1000u*z7_pn_delays[z7_pn_delay_index<6u ? z7_pn_delay_index : 0u]; }
static uint32_t z7_pn_interval_ms(void) { return 1000u*(z7_pn_interval_index<=30u ? z7_pn_interval_index : 0u); }
static const char *z7_pn_delay_text(void) {
    static const char *const text[]={"Off","1 s","2 s","3 s","5 s","10 s"};
    return text[z7_pn_delay_index<6u ? z7_pn_delay_index : 0u];
}
static const char *z7_pn_seconds_text(uint32_t value) {
    if (value>30u) value=0;
    z7_pn_interval_buffer[0]=(char)('0'+value/10u);z7_pn_interval_buffer[1]=(char)('0'+value%10u);
    z7_pn_interval_buffer[2]=' ';z7_pn_interval_buffer[3]='s';z7_pn_interval_buffer[4]=0;
    return z7_pn_interval_buffer;
}
static const char *z7_pn_interval_text(void) { return z7_pn_seconds_text(z7_pn_interval_index); }
static void z7_pn_set_mode(uint32_t mode)
{
    if (mode>PN_SINGLE || (mode && (z7_pn_busy() || z7_pn_exposure_owned || !z7_pn_input_ready || z7_pn_raw_error))) return;
    if (mode) {
        __atomic_store_n(&z7_pm_cancel,0u,__ATOMIC_RELEASE);
    }
    __atomic_store_n(&z7_pn_mode,mode,__ATOMIC_RELEASE);
    if (!mode) {
        __atomic_store_n(&z7_pm_cancel,1u,__ATOMIC_RELEASE);
        __atomic_store_n(&z7_pm_requested,0u,__ATOMIC_RELEASE);
        __atomic_store_n(&z7_pn_full_pending,0u,__ATOMIC_RELEASE);
    }
}
#include "pixel_nikon_quality.h"
#include "pixel_nikon_exposure.h"
static const char *z7_pn_title(uint32_t view)
{
    static const char *const text[]={"Pixel shift shooting","Pixel shift shooting mode","Number of shots","Delay",
        "Interval until next shot","Options","Starting storage folder","Unavailable"};
    if (view==15u) return "AE bracketing";
    if (view==16u) return "Number of shots";
    if (view==17u) return "Increment";
    return view>=7u && view<=14u ? text[view-7u] : "Pixel shift shooting";
}
static uint32_t z7_pn_entry_row(uint32_t view)
{
    if (view==8u) return z7_pn_mode==PN_SERIES ? 0u : z7_pn_mode==PN_SINGLE ? 1u : 2u;
    if (view==9u) return z7_pm_count_index<4u ? z7_pm_count_index : 0u;
    if (view==10u) return z7_pn_delay_index<6u ? 5u-z7_pn_delay_index : 5u;
    if (view==11u) return 0u;
    return view==12u ? !z7_pn_ae_enabled : 0u;
}
static const char *z7_pn_label(uint32_t view,uint32_t row)
{
    static const char *const root[]={"Pixel shift shooting mode","Number of shots","Delay","Interval until next shot","Options","Starting storage folder","Back"};
    static const char *const mode[]={"On (series)","On (single photo)","Off"};
    static const char *const counts[]={"4","8","16","32"};
    static const char *const delays[]={"10 s","5 s","3 s","2 s","1 s","Off"};
    if (row==6u) return "Back";
    if (view==7u) return row<7u ? root[row] : "";
    if (view==8u) return row<3u ? mode[row] : "";
    if (view==9u) return row<4u ? counts[row] : "";
    if (view==10u) return row<6u ? delays[row] : "";
    if (view==11u) return row==0u ? "Seconds (00-30)" : "";
    if (view==12u) return row==0 ? "AE bracketing" : row==1 ? "Off" : "";
    if (view==13u) return row==0 ? "New folder" : row==1 ? "Reset file numbering" : "";
    if (view==15u) return row==0 ? "Number of shots" : row==1 ? "Increment" : row==2 ? "Done" : "";
    if (view==16u) return row==0 ? "Number of shots" : "";
    if (view==17u) return row==0 ? "Increment" : "";
    if (view==14u) return row==0 ? "Not available in this build" : row==1 ? "No camera setting changed" : "";
    return "";
}
static const char *z7_pn_value(uint32_t view,uint32_t row)
{
    if (view==7u) {
        if (!row) return z7_vm_stage==5u ? "Wait" : z7_pn_raw_error || z7_pn_exposure_owned || z7_pn_job_error==2u ? "Restart" : z7_pn_mode ? "On" : z7_pn_job_error ? "Stopped" : "Off";
        if (row==1u) return z7_pm_count_text();
        if (row==2u) return z7_pn_delay_text();
        if (row==3u) return z7_pn_interval_text();
        if (row==4u) return z7_pn_ae_enabled ? "AE" : "Off";
        if (row==5u) return z7_pn_new_folder ? "On" : "Off";
    }
    if (view==8u && row<3u) return z7_pn_mode==(row==0u ? PN_SERIES : row==1u ? PN_SINGLE : PN_OFF) ? "*" : "";
    if (view==9u && row<4u) return row==z7_pm_count_index ? "*" : "";
    if (view==10u) return row<6u && 5u-row==z7_pn_delay_index ? "*" : "";
    if (view==11u) return row==0u ? z7_pn_seconds_text(z7_pn_interval_draft) : "";
    if (view==13u && row<2u) return (row==0u ? z7_pn_new_folder : z7_pn_reset_numbering) ? "[x]" : "[ ]";
    if (view==12u && row==0u) return z7_pn_ae_enabled ? "*" : "";
    if (view==12u && row==1u) return z7_pn_ae_enabled ? "" : "*";
    if ((view==15u && row==0u) || view==16u) return z7_pn_ae_count_names[z7_pn_ae_draft_count<9u ? z7_pn_ae_draft_count : 5u];
    if ((view==15u && row==1u) || view==17u) return z7_pn_ae_step_names[z7_pn_ae_draft_step<12u ? z7_pn_ae_draft_step : 3u];
    return "";
}
/* Menu model only. Returns the root row that should regain focus. */
static uint32_t z7_pn_action(uint32_t *view,uint32_t row)
{
    uint32_t old=*view;
    if (old==7u) { if (row<6u) { *view=8u+row;if (row==3u) z7_pn_interval_draft=z7_pn_interval_index; } else *view=5u; return 2u; }
    if (old==8u && row<3u) { z7_pn_set_mode(row==0u ? PN_SERIES : row==1u ? PN_SINGLE : PN_OFF); *view=7u; return 0; }
    if (old==9u && row<4u) { if (!z7_pn_busy()) z7_pm_count_index=row; *view=7u; return 1; }
    if (old==10u && row<6u) { if (!z7_pn_busy()) z7_pn_delay_index=5u-row; *view=7u; return 2; }
    if (old==11u && row==0u) { if (!z7_pn_busy()) z7_pn_interval_index=z7_pn_interval_draft; *view=7u; return 3; }
    if (old==12u && row==0u) { z7_pn_ae_draft_count=z7_pn_ae_count;z7_pn_ae_draft_step=z7_pn_step_current();*view=15u;return 0; }
    if (old==12u && row==1u) { if (!z7_pn_busy()) z7_pn_ae_enabled=0;*view=7u;return 4; }
    if (old==15u) {
        if (row==6u) { *view=12u;return 0; }
        if (row<2u) { *view=16u+row;return 0; }
        if (row==2u && !z7_pn_busy()) { z7_pn_ae_count=z7_pn_ae_draft_count;z7_pn_ae_step=z7_pn_ae_draft_step;z7_pn_ae_enabled=z7_pn_ae_count!=4u; }
        *view=7u;return 4;
    }
    if (old==16u || old==17u) { *view=15u;return old-16u; }
    if (old==13u && row<2u) {
        if (!z7_pn_busy() && z7_pn_folder_matches()) {
            if (!row) { z7_pn_new_folder^=1u;if (!z7_pn_new_folder) z7_pn_reset_numbering=0; }
            else if (z7_pn_new_folder) z7_pn_reset_numbering^=1u;
        }
        return row;
    }
    *view=7u; return old>=8u && old<=13u ? old-8u : z7_pn_help_focus;
}
/* Input only publishes a scalar. Log reset and arming stay on the worker. */
static void z7_pn_poll_trigger(void)
{
    if (!__atomic_exchange_n(&z7_pn_full_pending,0u,__ATOMIC_ACQ_REL) ||
        !z7_pn_mode || z7_pn_busy() || !z7_pm_capture_ready()) return;
    z7_pm_arm();
    if (!z7_pm_requested) return;
    z7_pn_job_groups=1;z7_pn_job_shots=z7_pm_count();
    if (!z7_pn_job_prepare()) {
        if (!z7_pn_job_error) z7_pn_job_error=1;
        z7_pn_set_mode(PN_OFF);z7_pn_cleanup_log_pending=1;
    } else if (!z7_pm_requested || !z7_pn_mode) { z7_pn_job_finish();z7_pn_set_mode(PN_OFF); }
    z7_vm_log.group_count=z7_pn_job_groups;z7_vm_log.group_shots=z7_pn_job_shots;
    for (uint32_t g=0;g<z7_pn_job_groups;++g) z7_vm_log.ev_sixths[g]=z7_pn_job_ev[g];
    z7_pn_log_exposure();
}
static void z7_pn_after_worker(void)
{
    if (z7_vm_stage==5u) { z7_pn_set_mode(PN_OFF);return; }
    if ((z7_vm_stage==2u || z7_vm_stage==3u || !z7_pn_mode) && !z7_pm_running && z7_pn_job_active && z7_pn_job_error!=2u) {
        uint32_t complete=!!(z7_vm_log.flags&VS_SERIES_COMPLETE);
        z7_pn_job_finish();
        z7_pn_cleanup_log_pending=1;
        if (!complete || z7_pn_mode==PN_SINGLE || z7_pn_exposure_owned) z7_pn_set_mode(PN_OFF);
    }
}
static void z7_pn_cleanup_log(void)
{
    if (!z7_pn_cleanup_log_pending) return;
    z7_pn_cleanup_log_pending=0;z7_pn_log_exposure();z7_vm_save();
}
#include "pixel_nikon_input.h"
#endif
