/* SPDX-License-Identifier: MIT. Original-Z7 C 3.80 RAW quality transaction.
 * Nikon's NEF-only row calls 1049D0CA(13), then 104065B1(501,1).
 * The resident worker owns this transaction; GUI/input callbacks never write
 * camera properties. JPEG preferences 502/503 and RAW depth/compression stay
 * untouched. A later user quality change wins over our saved value.
 */
#ifndef Z7_PIXEL_NIKON_QUALITY_H
#define Z7_PIXEL_NIKON_QUALITY_H
volatile uint32_t z7_pn_raw_ready,z7_pn_raw_owned,z7_pn_raw_saved,z7_pn_raw_error;
static const uint16_t z7_pn_setup_keys[]={0x209,0x008,0x576,0x568,0x567};
static uint32_t z7_pn_setup_saved[5],z7_pn_setup_target[5],z7_pn_setup_owned,z7_pn_setup_ready;
static uint32_t z7_pn_quality_matches(void)
{
    return VM_W(0x104065a4u)==0xbf03f5ceu && VM_W(0x104065b0u)==0xbe1df5cfu &&
           VM_W(0x101d61eeu)==0x47f0e92du && VM_W(0x1049d132u)==0xe7c9200du &&
           VM_W(0x1049d110u)==0x46202101u;
}
static uint32_t z7_pn_quality(void) { return VM_F(0x104065a5u,uint32_t,uint32_t)(0x501u); }
static uint32_t z7_pn_quality_set(uint32_t value)
{
    uint32_t accepted=VM_F(0x104065b1u,uint32_t,uint32_t,uint32_t)(0x501u,value);
    /* The property manager may publish its accepted change asynchronously. */
    for (uint32_t i=0;i<50u;++i) {
        if (z7_pn_quality()==value) return accepted==1u;
        z7_vm_sleep(20);
    }
    return 0;
}
static uint32_t z7_pn_setup_set(uint32_t index,uint32_t value)
{
    uint32_t key=z7_pn_setup_keys[index];
    uint32_t ok=VM_F(0x104065b1u,uint32_t,uint32_t,uint32_t)(key,value);
    for (uint32_t n=0;n<50u;++n) {
        if (VM_F(0x104065a5u,uint32_t,uint32_t)(key)==value) return ok==1u;
        z7_vm_sleep(20);
    }
    return 0;
}
static uint32_t z7_pn_native_bracket_off(void)
{
    uint32_t type=VM_F(0x104065a5u,uint32_t,uint32_t)(0x56bu);
    if (type>4u) return 0;
    uint32_t key=type<3u ? 0x579u : type==3u ? 0x57au : 0x570u;
    return !VM_F(0x104065a5u,uint32_t,uint32_t)(key);
}
static uint32_t z7_pn_capture_settings_match(void)
{
    if (!z7_pn_setup_ready || z7_pn_quality()!=1u || !z7_pn_native_bracket_off()) return 0;
    for (uint32_t n=0;n<5u;++n)
        if (VM_F(0x104065a5u,uint32_t,uint32_t)(z7_pn_setup_keys[n])!=z7_pn_setup_target[n]) return 0;
    return 1;
}
static uint32_t z7_pn_setup_restore(void)
{
    for (uint32_t n=5u;n--;) if (z7_pn_setup_owned&(1u<<n)) {
        if (VM_F(0x104065a5u,uint32_t,uint32_t)(z7_pn_setup_keys[n])!=z7_pn_setup_target[n] ||
            z7_pn_setup_set(n,z7_pn_setup_saved[n])) z7_pn_setup_owned&=~(1u<<n);
        else return 0;
    }
    z7_pn_setup_ready=0;return 1;
}
static uint32_t z7_pn_setup_prepare(void)
{
    if (z7_pn_setup_ready) {
        for (uint32_t n=0;n<5u;++n)
            if (VM_F(0x104065a5u,uint32_t,uint32_t)(z7_pn_setup_keys[n])!=z7_pn_setup_target[n]) return 0;
        return 1;
    }
    for (uint32_t n=0;n<5u;++n) z7_pn_setup_saved[n]=z7_pn_setup_target[n]=VM_F(0x104065a5u,uint32_t,uint32_t)(z7_pn_setup_keys[n]);
    if (z7_pn_setup_saved[0]>7u || z7_pn_setup_saved[1]>10u || z7_pn_setup_saved[2]>1u ||
        z7_pn_setup_saved[3]>6u || z7_pn_setup_saved[4]>3u) return 0;
    /* Native ordinary AE/WB/ADL bracketing must not advance inside a group. */
    if (!z7_pn_native_bracket_off()) return 0;
    z7_pn_setup_target[0]=0;z7_pn_setup_target[1]=0;z7_pn_setup_target[2]=1;
    if (z7_pn_setup_saved[4]==2u) {
        z7_pn_setup_target[4]=1;
        if (z7_pn_setup_saved[3]==2u) z7_pn_setup_target[3]=1;
    }
    for (uint32_t n=0;n<5u;++n) if (z7_pn_setup_saved[n]!=z7_pn_setup_target[n]) {
        z7_pn_setup_owned|=1u<<n;
        if (!z7_pn_setup_set(n,z7_pn_setup_target[n])) return 0;
    }
    z7_pn_setup_ready=1;return 1;
}
static void z7_pn_quality_worker(void)
{
    if (z7_pm_running) return;
    if (!z7_pn_mode) {
        z7_pn_raw_ready=0;
        /* Never change quality while cleanup still owns a moved sensor. */
        if (Z7_VM_CLEANUP_PENDING()) return;
        if (!z7_pn_quality_matches()) { z7_pn_raw_error=2;return; }
        if (z7_pn_raw_error==2u) return;
        if (!z7_pn_setup_restore()) { z7_pn_raw_error=2;return; }
        if (!z7_pn_raw_owned) return;
        if (z7_pn_quality()!=1u) { z7_pn_raw_owned=0;return; }
        if (z7_pn_raw_error==2u) return; /* Failed restore is latched, not retried forever. */
        if (z7_pn_quality_set(z7_pn_raw_saved)) z7_pn_raw_owned=0;
        else z7_pn_raw_error=2;
        return;
    }
    if (!z7_pn_quality_matches() || !z7_pn_setup_prepare()) { z7_pn_set_mode(PN_OFF);return; }
    if (z7_pn_raw_ready) {
        if (z7_pn_quality()==1u) return;
        z7_pn_set_mode(PN_OFF); /* Preserve an external change and cancel. */
        z7_pn_raw_ready=z7_pn_raw_owned=0;
        return;
    }
    if (z7_pn_raw_error || !z7_pn_quality_matches()) { z7_pn_set_mode(PN_OFF);return; }
    uint32_t quality=z7_pn_quality();
    if (quality>3u) { z7_pn_raw_error=1;z7_pn_set_mode(PN_OFF);return; }
    if (quality!=1u) {
        z7_pn_raw_saved=quality;z7_pn_raw_owned=1;
        if (!z7_pn_quality_set(1u)) { z7_pn_raw_error=1;z7_pn_set_mode(PN_OFF);return; }
    }
    z7_pn_raw_ready=1;
}
#endif
