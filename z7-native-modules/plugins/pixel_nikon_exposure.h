/* SPDX-License-Identifier: MIT. Independent original-Z7 C 3.80 exposure job.
 * The Z7's exposure mode comes from the physical mode dial: the camera run of
 * ede43437 (Nov 27) showed the PTP mode write is refused in A. Pixel shift
 * therefore requires the dial on M (job error 6, nothing written otherwise).
 * In M, preserve the user's configured shutter/aperture and freeze Auto ISO.
 * A bracket changes shutter only BETWEEN complete pixel groups. All property
 * changes are worker-owned, checked and restored in reverse order. Native
 * PTP binds mode request1/effective136F, ISO207/508, Av205, Tv204/special20D.
 */
#ifndef Z7_PIXEL_NIKON_EXPOSURE_H
#define Z7_PIXEL_NIKON_EXPOSURE_H
volatile uint32_t z7_pn_ae_enabled,z7_pn_ae_count=5u,z7_pn_ae_step=3u;
volatile uint32_t z7_pn_ae_draft_count,z7_pn_ae_draft_step;
volatile uint32_t z7_pn_job_active,z7_pn_job_total,z7_pn_job_groups,z7_pn_job_shots,z7_pn_job_shift,z7_pn_job_error;
volatile uint32_t z7_pn_exposure_owned;
static const uint16_t z7_pn_exp_keys[]={1,0x508,0x207,0x205,0x20d,0x204};
static uint32_t z7_pn_exp_saved[6],z7_pn_exp_applied[6];
static int32_t z7_pn_base_tv,z7_pn_base_av,z7_pn_job_ev[9];
static const uint8_t z7_pn_ae_sizes[]={2,2,3,3,1,3,5,7,9};
static const uint8_t z7_pn_ae_sixths[]={2,3,4,6,8,9,10,12,14,15,16,18};
static const char *const z7_pn_ae_count_names[]={"2F (-)","2F (+)","3F (-)","3F (+)","0F","3F","5F","7F","9F"};
static const char *const z7_pn_ae_step_names[]={"0.3 EV","0.5 EV","0.7 EV","1.0 EV","1.3 EV","1.5 EV","1.7 EV","2.0 EV","2.3 EV","2.5 EV","2.7 EV","3.0 EV"};
static uint32_t z7_pn_prop(uint32_t key) { return VM_F(0x104065a5u,uint32_t,uint32_t)(key); }
static uint32_t z7_pn_step_allowed(uint32_t index)
{
    if (index>=12u) return 0;
    uint32_t mode=z7_pn_prop(0x1013u),value=z7_pn_ae_sixths[index];
    return mode==0u ? !(value&1u) : mode==1u ? value==3u || value==6u || value==9u || value==12u || value==15u || value==18u :
           mode==2u ? value==6u || value==12u || value==18u : 0u;
}
static uint32_t z7_pn_step_current(void)
{
    uint32_t index=z7_pn_ae_step<12u ? z7_pn_ae_step : 3u;
    while (index<12u && !z7_pn_step_allowed(index)) ++index;
    return index<12u ? index : 3u;
}
static uint32_t z7_pn_exposure_native(void)
{
    return z7_pn_quality_matches() && VM_W(0x103fe8d8u)==0xf240b508u &&
        VM_W(0x101c22dcu)==0xf5b0b510u &&
        VM_W(0x1154e798u)==312u && VM_W(0x1154e79cu)==1u &&
        VM_W(0x1154eca8u)==0xff88u && VM_W(0x1154ecacu)==300000u;
}
static uint32_t z7_pn_capture_wait_polls(void)
{
    int32_t tv=(int32_t)z7_pn_exp_applied[5];
    if (tv < -120 || tv>312 || tv%4) return 300u;
    uint32_t row=(uint32_t)(312-tv)/4u;
    uint32_t tenths_ms=VM_W(0x1154e798u+row*12u+4u);
    return ((tenths_ms+9u)/10u+15000u+49u)/50u;
}
static uint32_t z7_pn_exp_read(uint32_t i) { return z7_pn_prop(i ? z7_pn_exp_keys[i] : 0x136fu); }
static uint32_t z7_pn_exp_write(uint32_t i,uint32_t value)
{
    uint32_t key=z7_pn_exp_keys[i];
    if (VM_F(0x1033de5du,uint32_t,uint32_t,uint32_t)(i ? key : 0u,value)!=0x2001u) return 0;
    uint32_t ok=VM_F(0x104065b1u,uint32_t,uint32_t,uint32_t)(key,value);
    for (uint32_t n=0;n<50u;++n) {
        if (z7_pn_exp_read(i)==value) return ok==1u;
        z7_vm_sleep(20);
    }
    return 0;
}
static uint32_t z7_pn_exp_apply(uint32_t i,uint32_t value)
{
    if (z7_pn_exp_read(i)==value) { z7_pn_exp_applied[i]=value;return 1; }
    z7_pn_exposure_owned|=1u<<i;z7_pn_exp_applied[i]=value;
    return z7_pn_exp_write(i,value);
}
static uint32_t z7_pn_exp_restore(void)
{
    for (uint32_t n=6u;n--;) if (z7_pn_exposure_owned&(1u<<n)) {
        /* An external change wins. Never overwrite a setting we no longer own. */
        if (z7_pn_exp_read(n)!=z7_pn_exp_applied[n] || z7_pn_exp_write(n,z7_pn_exp_saved[n]))
            z7_pn_exposure_owned&=~(1u<<n);
        else { z7_pn_job_error=2u;return 0; }
    }
    return 1;
}
static uint32_t z7_pn_effective(uint32_t key,int32_t *value)
{
    int32_t pair[2]={0,0};
    VM_F(0x103fe8d9u,void,uint32_t,void *,uint32_t)(key,pair,8u);
    int32_t denominator=(int16_t)pair[0],numerator=pair[1];
    if (denominator<=0 || denominator>1024 || numerator < -65536 || numerator>65536) return 0;
    if (!VM_F(0x101c22ddu,uint32_t,uint32_t,void *)(24u,pair)) return 0;
    int32_t scaled=pair[1];
    /* Native shutter/aperture values are in 24ths EV on a 1/6-EV grid. */
    *value=(scaled>=0 ? (scaled+2)/4 : (scaled-2)/4)*4;
    return 1;
}
static uint32_t z7_pn_exposure_matches(void)
{
    if (!z7_pn_job_active) return 1;
    for (uint32_t i=0;i<6u;++i) if (z7_pn_exp_read(i)!=z7_pn_exp_applied[i]) return 0;
    int32_t tv,av,sv;
    if (!z7_pn_effective(0x1308u,&tv) || !z7_pn_effective(0x1303u,&av) || !z7_pn_effective(0x1309u,&sv)) return 0;
    if (tv!=(int32_t)z7_pn_exp_applied[5] || av!=(int32_t)z7_pn_exp_applied[3] || sv!=(int32_t)z7_pn_exp_applied[2]) return 0;
    return 1;
}
static void z7_pn_log_exposure(void)
{
    for (uint32_t i=0;i<6u;++i) {
        z7_vm_log.exposure_saved[i]=z7_pn_exp_saved[i];z7_vm_log.exposure_applied[i]=z7_pn_exp_applied[i];
    }
    z7_vm_log.exposure_owned=z7_pn_exposure_owned;z7_vm_log.job_error=z7_pn_job_error;
    z7_vm_log.setup_error=z7_pn_raw_error;
}
static uint32_t z7_pn_job_prepare(void)
{
    if (z7_pn_job_active || z7_pn_exposure_owned || !z7_pn_exposure_native()) return 0;
    z7_pn_job_error=0;
    for (uint32_t i=0;i<6u;++i) z7_pn_exp_saved[i]=z7_pn_exp_applied[i]=z7_pn_exp_read(i);
    uint32_t mode=z7_pn_exp_saved[0],automatic=z7_pn_exp_saved[1];
    if (mode!=3u) { z7_pn_job_error=6u;return 0; }   /* dial not on M: nothing written */
    if (automatic>1u || z7_pn_exp_saved[4]) return 0;
    z7_pn_base_tv=(int32_t)z7_pn_exp_saved[5];z7_pn_base_av=(int32_t)z7_pn_exp_saved[3];
    if (mode!=3u && (!z7_pn_effective(0x1308u,&z7_pn_base_tv) || !z7_pn_effective(0x1303u,&z7_pn_base_av))) return 0;
    int32_t effective_iso=(int32_t)z7_pn_exp_saved[2];
    /* The original actual-ISO PTP getter1052FB32 reads the Sv rational1309.
     * Convert it to the same Sv24 units as the configured ISO207 table. */
    if (automatic && !z7_pn_effective(0x1309u,&effective_iso)) return 0;
    uint32_t iso=(uint32_t)effective_iso;
    if (iso>600u || z7_pn_base_av<0 || z7_pn_base_av>384) return 0;
    uint32_t choice=z7_pn_ae_count<9u ? z7_pn_ae_count : 5u;
    uint32_t step=z7_pn_ae_sixths[z7_pn_step_current()];
    if (step>=12u && choice>=7u) choice=6u; /* Nikon's >=2EV programs stop at5F. */
    z7_pn_job_groups=z7_pn_ae_enabled ? z7_pn_ae_sizes[choice] : 1u;
    z7_pn_job_shots=z7_pm_count();z7_pn_job_shift=2u+z7_pm_count_index;
    z7_pn_job_total=z7_pn_job_groups*z7_pn_job_shots;
    for (uint32_t g=0;g<z7_pn_job_groups;++g) {
        int32_t ev=0;
        if (z7_pn_ae_enabled && choice!=4u) {
            if (choice<4u) ev=(int32_t)g*(choice&1u ? (int32_t)step : -(int32_t)step);
            else if (g) ev=(g&1u ? -1 : 1)*(int32_t)((g+1u)/2u)*(int32_t)step;
        }
        z7_pn_job_ev[g]=ev;
        int32_t target=z7_pn_base_tv-ev*4;
        if (target < -120 || target>312 || target%4) { z7_pn_job_error=3;return 0; }
    }
    if (!z7_pn_exp_apply(0,3u) || !z7_pn_exp_apply(1,0u) || !z7_pn_exp_apply(2,iso) ||
        !z7_pn_exp_apply(3,(uint32_t)z7_pn_base_av) || !z7_pn_exp_apply(4,0u) ||
        !z7_pn_exp_apply(5,(uint32_t)z7_pn_base_tv)) {
        z7_pn_job_error=1;z7_pn_exp_restore();return 0;
    }
    z7_pn_job_active=1;
    return 1;
}
static uint32_t z7_pn_group_exposure(uint32_t group)
{
    if (!z7_pn_exposure_matches() || group>=z7_pn_job_groups) return 0;
    return z7_pn_exp_apply(5,(uint32_t)(z7_pn_base_tv-z7_pn_job_ev[group]*4));
}
static void z7_pn_job_finish(void)
{
    if (!z7_pn_job_active) return;
    if (Z7_VM_CLEANUP_PENDING()) {
        z7_pn_job_error=2;return;
    }
    z7_pn_exp_restore();
    z7_pn_job_active=0;
}
#endif
