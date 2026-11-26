/* SPDX-License-Identifier: MIT.
 * Original-Z7 C 3.80 VR (IBIS) TELEMETRY PROBE: READ-ONLY. First step of the
 * pixel-shift port (PIXEL_SHIFT_RESEARCH.md); design follows JKWTCN's MIT Z7II
 * pixel_shift_vr.h, original-Z7 bindings are independent work.
 *
 * From the resident worker, while the body-VR command service is idle and has
 * no request outstanding, it sends position READS (opcode 0xF040) through
 * Nikon's BodyVrCommandService send function 0x100F1F9E and logs the returned
 * bytes to A:\Z7VRLOG.DAT. It never sends a position command (0xF1F1) and
 * never writes VR settings: the sensor is not moved.
 *  - Windows read: 0x0FE0/42 bytes (the Z7II telemetry block), 0x1018/6 and
 *    0x1FF8/1, 0x1FF9/1 (addresses Nikon's own Z7 code reads).
 *  - Completion: Nikon calls the stored callback with event 0x042F0021 and a
 *    result whose first byte is the status; the callback slot 0xA18B5D88 is
 *    cleared afterwards. The send refuses while the service busy flag
 *    (0xA18B6030+0x34) is 1; the probe also waits for an empty callback slot.
 *  - One read per worker tick at most, 48 rounds, then it stops for this boot.
 */
#ifndef Z7_VR_TELEMETRY_PROBE_H
#define Z7_VR_TELEMETRY_PROBE_H
#include <stdint.h>

#define VP_W(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define VP_F(a,r,...) ((r (*)(__VA_ARGS__))(uintptr_t)(a))
enum {
    VP_SEND=0x100f1f9fu, VP_EVENT=0x042f0021u, VP_CALLBACK_SLOT=0xa18b5d88u,
    VP_BUSY=0xa18b6030u+0x34u, VP_READ=0xf040u,
    VP_WINDOWS=4u, VP_ROUNDS=48u, VP_BYTES=50u, VP_PENDING=0x102u, VP_TIMEOUT_TICKS=4u,
    VP_MAGIC=0x47524637u /* "7FRG" */, VP_VERSION=1u,
    VP_CREATE=0x1027c0dbu, VP_WRITE=0x1027c049u, VP_CLOSE=0x1027bfcdu, VP_CLEAN=0x101e9f39u
};
static const uint16_t z7_vp_address[VP_WINDOWS]={0x0fe0,0x1018,0x1ff8,0x1ff9};
static const uint8_t z7_vp_length[VP_WINDOWS]={42,6,1,1};
static const uint8_t z7_vp_offset[VP_WINDOWS]={0,42,48,49};
static const char z7_vp_path[]="A:\\Z7VRLOG.DAT";

struct z7_vp_request {          /* BodyVr request, 40 bytes (same layout as Z7II) */
    uint16_t opcode, reserved;
    uint32_t address, length, words[4];
    const void *payload;
    uint32_t word;
    void *output;
};
_Static_assert(sizeof(struct z7_vp_request)==0x28,"BodyVr request size");
struct z7_vp_round { uint32_t tick, status; uint8_t bytes[VP_BYTES]; uint8_t pad[6]; };
struct z7_vp_log {
    uint32_t magic, version, rounds, sends, refused, timeouts, writes, flags;
    struct z7_vp_round round[VP_ROUNDS];
};
static _Alignas(64) struct z7_vp_log z7_vp_log;
static _Alignas(64) uint8_t z7_vp_output[64];
static struct z7_vp_request z7_vp_request;
volatile uint32_t z7_vp_reply, z7_vp_window, z7_vp_busy_ticks, z7_vp_tick, z7_vp_dirty, z7_vp_waiting;

static uint32_t z7_vp_native_ok(void)
{
    return VP_W(VP_SEND-1u)==0x4ff8e92du && VP_W(VP_SEND+3u)==0x0b01f04fu &&
        VP_W(0x100f31ceu)==0x6b404840u && VP_W(VP_CREATE-1u)==0xb0abb530u &&
        VP_W(VP_WRITE-1u)==0xb0abb5f0u && VP_W(VP_CLOSE-1u)==0xb0aab510u;
}
/* BodyVr task: completion of our read. */
static void z7_vp_complete(uint32_t event, const uint8_t *result)
{
    uint32_t status=event==VP_EVENT && result ? result[0] : 0x103u;
    __atomic_store_n(&z7_vp_reply,status,__ATOMIC_RELEASE);
}
static void z7_vp_save(void)
{
    z7_vp_log.magic=VP_MAGIC; z7_vp_log.version=VP_VERSION; ++z7_vp_log.writes;
    VP_F(VP_CLEAN,void,void *,uint32_t)(&z7_vp_log,sizeof(z7_vp_log));
    uint32_t fd=VP_F(VP_CREATE,uint32_t,const char *,uint32_t)(z7_vp_path,0), actual=0;
    if ((int32_t)fd<0) return;
    VP_F(VP_WRITE,uint32_t,uint32_t,const void *,uint32_t,uint32_t *)(fd,&z7_vp_log,sizeof(z7_vp_log),&actual);
    VP_F(VP_CLOSE,uint32_t,uint32_t)(fd);
}
/* Resident worker only. */
static void z7_vp_worker(void)
{
    if (!z7_vp_native_ok()) return;
    ++z7_vp_tick;
    uint32_t r=z7_vp_log.rounds;
    if (z7_vp_waiting) {
        uint32_t status=__atomic_load_n(&z7_vp_reply,__ATOMIC_ACQUIRE);
        if (status==VP_PENDING) {
            if (++z7_vp_busy_ticks<VP_TIMEOUT_TICKS) return;
            ++z7_vp_log.timeouts;          /* keep waiting for the slot to clear */
            if (VP_W(VP_CALLBACK_SLOT)) return;
            status=0x104u;
        }
        uint32_t w=z7_vp_window;
        struct z7_vp_round *row=&z7_vp_log.round[r];
        if (!w) row->tick=z7_vp_tick;
        row->status|=(status&0xffu)<<(8*w);
        if (!status) for (uint32_t i=0;i<z7_vp_length[w];++i) row->bytes[z7_vp_offset[w]+i]=z7_vp_output[i];
        z7_vp_waiting=0; z7_vp_busy_ticks=0;
        if (++z7_vp_window==VP_WINDOWS) { z7_vp_window=0; z7_vp_log.rounds=r+1; z7_vp_dirty=1; }
        return;
    }
    if (z7_vp_dirty && (r==VP_ROUNDS || r%4==0)) { z7_vp_dirty=0; z7_vp_save(); }
    if (r>=VP_ROUNDS) return;
    if (VP_W(VP_BUSY)==1u || VP_W(VP_CALLBACK_SLOT)) { ++z7_vp_log.refused; return; }
    uint32_t w=z7_vp_window;
    for (uint32_t i=0;i<sizeof(z7_vp_output);++i) z7_vp_output[i]=0;
    uint32_t *q=(uint32_t *)&z7_vp_request;
    for (uint32_t i=0;i<sizeof(z7_vp_request)/4;++i) q[i]=0;  /* no memset in modules */
    z7_vp_request.opcode=VP_READ; z7_vp_request.address=z7_vp_address[w];
    z7_vp_request.length=z7_vp_length[w]; z7_vp_request.output=z7_vp_output;
    __atomic_store_n(&z7_vp_reply,VP_PENDING,__ATOMIC_RELEASE);
    ++z7_vp_log.sends;
    if (!VP_F(VP_SEND,uint32_t,const struct z7_vp_request *,void (*)(uint32_t,const uint8_t *))(&z7_vp_request,z7_vp_complete)) {
        ++z7_vp_log.refused; return;
    }
    z7_vp_waiting=1;
}
#endif
