/* SPDX-License-Identifier: MIT. Independent original-Z7 C 3.80 input binding.
 * CapStQue invokes the scalar dispatcher stored at event-task +0x2C. Its first fourteen
 * callbacks are registered by 10060A38 (literal pool 10060CBC..CC8):
 *   slot 0 half down 10062A53 (event 16), slot 1 full down 10062A37 (event 17),
 *   slot 2 full up 10060A0D (event 19), slot 3 half up 100609D9 (event 18).
 * Camera run 8e1da6c8 (Nov 27) owned 100609D9 by mistake: the module swallowed
 * Nikon's half-up, so Nikon stayed half-pressed (menus/playback locked) until a
 * power cycle. Only full-down/full-up are owned; half down/up always reach Nikon,
 * and the registration literals are verified before publishing.
 * Input task publishes a request. Capture/log reset stays on the worker.
 */
enum { PN_INPUT_SLOT=0xa238c1b4u,PN_INPUT_NATIVE=0x1005f757u,PN_INPUT_CALLBACKS=0xa238c140u,
       PN_FULL_DOWN=0x10062a37u,PN_FULL_UP=0x10060a0du };
volatile uint32_t z7_pn_full_owned,z7_pn_input_requests,z7_pn_input_refused;
volatile uint32_t z7_pn_j_cancels;
static uint32_t z7_pn_gui_key(uint32_t key,uint32_t a,uint32_t b,uint32_t c)
{
    /* Original AO entry74 (ID_SW_OK) is enabled, group1/mask1: SW1 bit0.
     * Latch in the native key callback so a short J press survives worker sleeps.
     * Menus and ordinary shooting retain the original four-argument callback. */
    if ((z7_pm_running || z7_pn_job_active || z7_pn_full_pending) &&
        VM_W(0xa201d510u)==0u && !sm_menu_visible() && (VM_W(0xa1f90aa8u)&1u)) {
        __atomic_store_n(&z7_pm_cancel,1u,__ATOMIC_RELEASE);++z7_pn_j_cancels;return 0;
    }
    return VM_F(0x1030da57u,uint32_t,uint32_t,uint32_t,uint32_t,uint32_t)(key,a,b,c);
}
static uint32_t z7_pn_input_matches(void)
{
    return VM_W(PN_INPUT_SLOT)==PN_INPUT_NATIVE && VM_W(0xa1829b0cu)==0x1030da57u &&
        VM_W(0x1030da56u)==0x2600b570u &&
        VM_W(0x106345e4u)==1u && VM_W(0x106345ecu)==1u && VM_W(0x106345f0u)==1u &&
        VM_W(PN_INPUT_NATIVE-1u)==0x41f0e92du &&
        VM_W(0x1005f7e0u)==0x483d4933u &&
        VM_W(0x10060cc4u)==PN_FULL_DOWN && VM_W(0x10060cc8u)==PN_FULL_UP &&
        VM_W(PN_FULL_DOWN-1u)==0xb508489eu &&
        VM_W(PN_FULL_UP-1u)==0x4c98b510u && VM_W(0x101f50ccu)==0x4604b51cu;
}
static void z7_pn_input_dispatch(uint32_t flags)
{
    for (uint32_t i=0;i<14u;++i) if (flags&(1u<<i)) {
        uint32_t callback=VM_W(PN_INPUT_CALLBACKS+i*4u),consume=0;
        if (callback==PN_FULL_UP) {
            consume=__atomic_exchange_n(&z7_pn_full_owned,0u,__ATOMIC_ACQ_REL);
        } else if (callback==PN_FULL_DOWN) {
            consume=z7_pn_full_owned || z7_pn_busy();
            if (!consume && z7_pn_mode && VM_W(0xa201d510u)==0u &&
                !*(volatile uint8_t *)(uintptr_t)0xa18237c6u && !sm_menu_visible()) consume=1;
            if (consume && !__atomic_exchange_n(&z7_pn_full_owned,1u,__ATOMIC_ACQ_REL) && !z7_pn_busy()) {
                if (z7_pm_capture_context()) {
                    z7_pn_pressed_at=z7_pn_now();
                    __atomic_store_n(&z7_pn_full_pending,1u,__ATOMIC_RELEASE);
                    ++z7_pn_input_requests;
                } else ++z7_pn_input_refused;
            }
        }
        if (!consume) VM_F(PN_INPUT_NATIVE,void,uint32_t)(1u<<i);
    }
    if (flags&0xffffc000u) VM_F(PN_INPUT_NATIVE,void,uint32_t)(flags&0xffffc000u);
}
static void z7_pn_input_publish(void)
{
    if (!z7_pn_input_matches()) return;
    __asm__ volatile("dmb sy" ::: "memory");
    VM_W(PN_INPUT_SLOT)=(uint32_t)(uintptr_t)z7_pn_input_dispatch;
    VM_W(0xa1829b0cu)=(uint32_t)(uintptr_t)z7_pn_gui_key;
    __atomic_store_n(&z7_pn_input_ready,1u,__ATOMIC_RELEASE);
}
