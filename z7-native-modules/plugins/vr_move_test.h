/* SPDX-License-Identifier: MIT.
 * Original-Z7 C 3.80 VR (IBIS) ONE-MOVE TEST: step 2 of the pixel-shift port
 * (PIXEL_SHIFT_RESEARCH.md). Design follows JKWTCN's MIT Z7II
 * pixel_shift_vr.h; original-Z7 bindings are independent work (step 1 probe
 * and tools/audit_z7_pixel_shift_bindings.py).
 *
 * Once per boot, from the resident worker:
 *  1. ARM: one 0xF040 telemetry read (window 0x0FE0, 42 bytes) per worker tick
 *     until a read shows stabilisation active (state byte 0x22 == 1) and settled
 *     (|target - measured| <= 48 on every axis), confirmed by a second read
 *     100 ms later. Gives up after
 *     VM_ARM_TICKS ticks; the sensor is then never commanded.
 *  2. MOVE: one 0xF1F1 position command with upstream's 10-byte payload and the
 *     smallest step used here, x = 4 (Z7II scale: about 0.2 pixel), y = 0.
 *     Telemetry is read every 100 ms to see whether the target and measured
 *     positions follow (upstream expects state 0x40 and target -4*x).
 *  3. CENTRE: whenever the move may have reached the device, the centre command
 *     {0,0,0,0,0,16,16,0,0,2} is sent (retried), and telemetry is read again.
 *  4. WATCH: one read per tick for VM_WATCH_TICKS ticks, to see whether Nikon
 *     returns the state to normal stabilisation by itself.
 * Nikon's own D2 VR parameters are not touched; a power cycle restores normal
 * stabilisation. No capture. Everything is logged to A:\Z7VRMOV.DAT.
 */
#ifndef Z7_VR_MOVE_TEST_H
#define Z7_VR_MOVE_TEST_H
#include <stdint.h>

#define VM_W(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define VM_F(a,r,...) ((r (*)(__VA_ARGS__))(uintptr_t)(a))
enum {
    VM_SEND=0x100f1f9fu, VM_EVENT=0x042f0021u, VM_CALLBACK_SLOT=0xa18b5d88u,
    VM_BUSY=0xa18b6030u+0x34u, VM_READ=0xf040u, VM_POSITION=0xf1f1u,
    VM_DELAY=0x1017081fu,
    VM_TELEMETRY=0x0fe0u, VM_TELEMETRY_BYTES=42u, VM_STATE=0x22u, VM_MEASURED=0x24u,
    VM_NORMAL=1u, VM_HOLD=0x40u, VM_STEP=4u,
    VM_PENDING=0x102u, VM_ARM_TICKS=600u, VM_WATCH_TICKS=30u, VM_POLLS=20u,
    VM_ENTRIES=128u, VM_ARM_ENTRIES=48u,
    VM_MAGIC=0x564d5637u /* "7VMV" */, VM_VERSION=1u,
    VM_CREATE=0x1027c0dbu, VM_WRITE=0x1027c049u, VM_CLOSE=0x1027bfcdu, VM_CLEAN=0x101e9f39u
};
/* Result flags (log header). */
enum {
    VM_ARMED=1u<<0, VM_MOVE_SENT=1u<<1, VM_MOVE_ACK=1u<<2, VM_MOVE_FOLLOWED=1u<<3,
    VM_CENTRE_SENT=1u<<4, VM_CENTRE_ACK=1u<<5, VM_CENTRE_FOLLOWED=1u<<6,
    VM_NORMAL_AGAIN=1u<<7, VM_TIMED_OUT=1u<<8, VM_GAVE_UP=1u<<9, VM_DONE=1u<<10
};
/* Phase codes in each log entry. */
enum { VM_PH_ARM=1u, VM_PH_MOVE=2u, VM_PH_CENTRE=3u, VM_PH_WATCH=4u,
       VM_PH_MOVE_SEND=0x12u, VM_PH_CENTRE_SEND=0x13u };
static const char z7_vm_path[]="A:\\Z7VRMOV.DAT";
static const uint8_t z7_vm_move[10]={0,VM_STEP,0,0,0,16,16,0,0,2};
static const uint8_t z7_vm_centre[10]={0,0,0,0,0,16,16,0,0,2};

struct z7_vm_request {          /* BodyVr request, 40 bytes */
    uint16_t opcode, reserved;
    uint32_t address, length, words[4];
    const void *payload;
    uint32_t word;
    void *output;
};
_Static_assert(sizeof(struct z7_vm_request)==0x28,"BodyVr request size");
struct z7_vm_entry { uint32_t tick; uint8_t phase, poll; uint16_t status; uint8_t bytes[VM_TELEMETRY_BYTES]; uint8_t pad[6]; };
_Static_assert(sizeof(struct z7_vm_entry)==56,"log entry");
struct z7_vm_log {
    uint32_t magic, version, entries, flags, sends, refused, timeouts, writes;
    struct z7_vm_entry entry[VM_ENTRIES];
};
static _Alignas(64) struct z7_vm_log z7_vm_log;
static _Alignas(64) uint8_t z7_vm_output[64];
static struct z7_vm_request z7_vm_request;
volatile uint32_t z7_vm_reply, z7_vm_tick, z7_vm_stage, z7_vm_armed, z7_vm_watch, z7_vm_arm_logged, z7_vm_last_state;

static uint32_t z7_vm_native_ok(void)
{
    return VM_W(VM_SEND-1u)==0x4ff8e92du && VM_W(VM_SEND+3u)==0x0b01f04fu &&
        VM_W(0x100f31ceu)==0x6b404840u && VM_W(0x100f2000u)==0x13f1f24fu &&
        VM_W(VM_CREATE-1u)==0xb0abb530u &&
        VM_W(VM_WRITE-1u)==0xb0abb5f0u && VM_W(VM_CLOSE-1u)==0xb0aab510u;
}
static void z7_vm_sleep(uint32_t ms) { VM_F(VM_DELAY,void,uint32_t)(ms); }
/* BodyVr task: completion of our request. */
static void z7_vm_complete(uint32_t event, const uint8_t *result)
{
    uint32_t status=event==VM_EVENT && result ? result[0] : 0x103u;
    __atomic_store_n(&z7_vm_reply,status,__ATOMIC_RELEASE);
}
static uint32_t z7_vm_idle(void) { return VM_W(VM_BUSY)!=1u && !VM_W(VM_CALLBACK_SLOT); }
static void z7_vm_save(void)
{
    z7_vm_log.magic=VM_MAGIC; z7_vm_log.version=VM_VERSION; ++z7_vm_log.writes;
    VM_F(VM_CLEAN,void,void *,uint32_t)(&z7_vm_log,sizeof(z7_vm_log));
    uint32_t fd=VM_F(VM_CREATE,uint32_t,const char *,uint32_t)(z7_vm_path,0), actual=0;
    if ((int32_t)fd<0) return;
    VM_F(VM_WRITE,uint32_t,uint32_t,const void *,uint32_t,uint32_t *)(fd,&z7_vm_log,sizeof(z7_vm_log),&actual);
    VM_F(VM_CLOSE,uint32_t,uint32_t)(fd);
}
/* Send one request and wait (100 x 20 ms) for its completion.
 * 0x100 not idle, 0x101 refused, 0x102 timed out; else the device status. */
static uint32_t z7_vm_exchange(uint16_t opcode, const uint8_t *payload)
{
    for (uint32_t i=0;i<25u && !z7_vm_idle();++i) z7_vm_sleep(10);
    if (!z7_vm_idle()) { ++z7_vm_log.refused; return 0x100u; }
    for (uint32_t i=0;i<sizeof(z7_vm_output);++i) z7_vm_output[i]=0;
    uint32_t *q=(uint32_t *)&z7_vm_request;
    for (uint32_t i=0;i<sizeof(z7_vm_request)/4;++i) q[i]=0;  /* no memset in modules */
    z7_vm_request.opcode=opcode;
    if (payload) z7_vm_request.payload=payload;
    else { z7_vm_request.address=VM_TELEMETRY; z7_vm_request.length=VM_TELEMETRY_BYTES; z7_vm_request.output=z7_vm_output; }
    __atomic_store_n(&z7_vm_reply,VM_PENDING,__ATOMIC_RELEASE);
    ++z7_vm_log.sends;
    if (!VM_F(VM_SEND,uint32_t,const struct z7_vm_request *,void (*)(uint32_t,const uint8_t *))(&z7_vm_request,z7_vm_complete)) {
        ++z7_vm_log.refused; return 0x101u;
    }
    for (uint32_t i=0;i<100u;++i) {
        uint32_t s=__atomic_load_n(&z7_vm_reply,__ATOMIC_ACQUIRE);
        if (s!=VM_PENDING) return s;
        z7_vm_sleep(20);
    }
    ++z7_vm_log.timeouts; z7_vm_log.flags|=VM_TIMED_OUT;
    return VM_PENDING;
}
static int z7_vm_word(const uint8_t *b) { return (int16_t)(b[0]|(b[1]<<8)); }
static int z7_vm_abs(int v) { return v<0 ? -v : v; }
static int z7_vm_settled(const uint8_t *t, int limit)
{
    for (uint32_t a=0;a<3u;++a)
        if (z7_vm_abs(z7_vm_word(t+2*a)-z7_vm_word(t+VM_MEASURED+2*a))>limit) return 0;
    return 1;
}
static void z7_vm_record(uint32_t phase, uint32_t poll, uint32_t status, const uint8_t *t)
{
    if (z7_vm_log.entries>=VM_ENTRIES) return;
    struct z7_vm_entry *e=&z7_vm_log.entry[z7_vm_log.entries++];
    e->tick=z7_vm_tick; e->phase=(uint8_t)phase; e->poll=(uint8_t)poll; e->status=(uint16_t)status;
    for (uint32_t i=0;i<VM_TELEMETRY_BYTES;++i) e->bytes[i]=t && !status ? t[i] : 0;
}
/* Read telemetry and log it; the bytes stay in z7_vm_output. */
static uint32_t z7_vm_sample(uint32_t phase, uint32_t poll)
{
    uint32_t status=z7_vm_exchange(VM_READ,0);
    z7_vm_record(phase,poll,status,z7_vm_output);
    return status;
}
/* Poll every 100 ms until two reads in a row show the commanded hold. */
static int z7_vm_follow(uint32_t phase, int x)
{
    int run=0;
    for (uint32_t i=0;i<VM_POLLS;++i) {
        z7_vm_sleep(100);
        uint32_t s=z7_vm_sample(phase,i+1u);
        if (s==VM_PENDING) return 0;
        const uint8_t *t=z7_vm_output;
        int ok=!s && t[VM_STATE]==VM_HOLD && z7_vm_word(t)==x && !z7_vm_word(t+2) && !z7_vm_word(t+4) &&
            z7_vm_settled(t,24);
        run=ok ? run+1 : 0;
        if (run==2) return 1;
    }
    return 0;
}
static int z7_vm_applied(uint32_t s) { return s!=0x100u && s!=0x101u; }
/* The move itself: runs once, blocking the worker for a few seconds. */
static void z7_vm_run(void)
{
    uint32_t s=z7_vm_exchange(VM_POSITION,z7_vm_move);
    z7_vm_record(VM_PH_MOVE_SEND,0,s,0);
    if (!z7_vm_applied(s)) return;                 /* never reached the device */
    z7_vm_log.flags|=VM_MOVE_SENT;
    if (!s) {
        z7_vm_log.flags|=VM_MOVE_ACK;
        if (z7_vm_follow(VM_PH_MOVE,-4*(int)VM_STEP)) z7_vm_log.flags|=VM_MOVE_FOLLOWED;
    }
    /* Always recentre once the move may have applied. */
    for (uint32_t i=0;i<5u;++i) {
        if (s==VM_PENDING) z7_vm_sleep(500);       /* let a late completion land */
        s=z7_vm_exchange(VM_POSITION,z7_vm_centre);
        z7_vm_record(VM_PH_CENTRE_SEND,i,s,0);
        if (z7_vm_applied(s)) z7_vm_log.flags|=VM_CENTRE_SENT;
        if (!s) break;
        z7_vm_sleep(200);
    }
    if (!s) {
        z7_vm_log.flags|=VM_CENTRE_ACK;
        if (z7_vm_follow(VM_PH_CENTRE,0)) z7_vm_log.flags|=VM_CENTRE_FOLLOWED;
    }
}
/* Resident worker only. */
static void z7_vm_worker(void)
{
    if (z7_vm_stage>=3u || !z7_vm_native_ok()) return;
    ++z7_vm_tick;
    if (!z7_vm_stage) {                            /* ARM */
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
        if (z7_vm_armed) {                         /* confirm 100 ms later */
            z7_vm_sleep(100);
            s=z7_vm_sample(VM_PH_ARM,1);
            z7_vm_armed=!s && z7_vm_output[VM_STATE]==VM_NORMAL && z7_vm_settled(z7_vm_output,48);
            if (s==VM_PENDING) { z7_vm_log.flags|=VM_DONE; z7_vm_stage=3; z7_vm_save(); return; }
        }
        if (!z7_vm_armed) { if (z7_vm_tick%30u==0u) z7_vm_save(); return; }
        z7_vm_log.flags|=VM_ARMED;
        z7_vm_run();
        z7_vm_stage=2; z7_vm_save();
        return;
    }
    /* WATCH: does Nikon bring stabilisation back to normal by itself? */
    uint32_t s=z7_vm_sample(VM_PH_WATCH,0);
    if (!s && z7_vm_output[VM_STATE]==VM_NORMAL) z7_vm_log.flags|=VM_NORMAL_AGAIN;
    if (s==VM_PENDING || ++z7_vm_watch>=VM_WATCH_TICKS) { z7_vm_log.flags|=VM_DONE; z7_vm_stage=3; }
    if (z7_vm_stage==3u || z7_vm_watch%10u==0u) z7_vm_save();
}
#endif
