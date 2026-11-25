/* SPDX-License-Identifier: MIT.
 * Original-Z7 C 3.80 shutter-sound TRIGGER PROBE core (shared by the probe and
 * field-test modules). Plays no sound. Counts the
 * events Nikon delivers to three capture-notification callbacks, then logs them
 * to A:\Z7TRIG.DAT from the resident worker, so one camera session shows which
 * event arrives once per photo and which also fires in plain live view.
 *
 * Each callback slot is replaced only while it still holds the native function
 * recorded in a stock boot; the wrapper counts and then calls that native
 * function with the same (event, packet) and returns its result. The wrappers
 * read at most two words of a packet in camera RAM and never call firmware.
 */
#ifndef Z7_SHUTTER_TRIGGER_PROBE_H
#define Z7_SHUTTER_TRIGGER_PROBE_H
#include "module.h"
#include "worker.h"

#define TR_W(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define TR_F(a,r,...) ((r (*)(__VA_ARGS__))(uintptr_t)(a))

enum {
    TR_SLOTS=3u, TR_EVENTS=24u, TR_RING=128u, TR_PROPERTY_SLOT=3u,
    TR_FILE_MAGIC=0x47495254u /* "TRIG" */, TR_FILE_VERSION=1u,
    TR_WRITE_EVERY=3u, TR_MAX_WRITES=400u, TR_SILENT_PROPERTY=0x576u,
    TR_GETTER=0x1016fef3u, TR_CREATE=0x1027c0dbu, TR_WRITE=0x1027c049u,
    TR_CLOSE=0x1027bfcdu, TR_CLEAN=0x101e9f39u
};
static const uint32_t z7_trig_slot[TR_SLOTS]={0xa18d1bd8u,0xa18d1bdcu,0xa18d2750u};
static const uint32_t z7_trig_native[TR_SLOTS]={0x101426a9u,0x1014708du,0x104db211u};
static const uint32_t z7_trig_fingerprint[][2]={
    {0x101426a8u,0x4ff0e92du},{0x1014708cu,0x4ff0e92du},{0x104db210u,0x2900b538u},
    {0x1016fef2u,0x4669b508u},{0x1027c0dau,0xb0abb530u},{0x1027c048u,0xb0abb5f0u},
    {0x1027bfccu,0xb0aab510u},{0x101e9f38u,0x460cb570u}};
static const char z7_trig_path[]="A:\\Z7TRIG.DAT";

struct z7_trig_count { uint32_t event, count; };
struct z7_trig_entry { uint32_t event, tick_slot, word0, word1; };
struct z7_trig_log {
    uint32_t magic, version, bytes, sequence;
    uint32_t ticks, installed_mask, silent, dropped;
    uint32_t calls[TR_SLOTS], ring_next, writes, reserved[3];
    struct z7_trig_count counts[TR_SLOTS][TR_EVENTS];
    struct z7_trig_entry ring[TR_RING];
};
_Static_assert(sizeof(struct z7_trig_log)==64+TR_SLOTS*TR_EVENTS*8+TR_RING*16,"log layout");

static struct z7_trig_log z7_trig_live;
static _Alignas(64) struct z7_trig_log z7_trig_snapshot;
volatile uint32_t z7_trig_init_result, z7_trig_dirty, z7_trig_parked, z7_trig_last_write;
volatile uint32_t z7_trig_write_result;

static uint32_t z7_trig_matches(void)
{
    for (uint32_t i=0;i<sizeof(z7_trig_fingerprint)/sizeof(z7_trig_fingerprint[0]);++i)
        if (TR_W(z7_trig_fingerprint[i][0])!=z7_trig_fingerprint[i][1]) return 0;
    return 1;
}

static void z7_trig_append(uint32_t event, uint32_t slot, uint32_t word0, uint32_t word1)
{
    uint32_t n=__atomic_fetch_add(&z7_trig_live.ring_next,1,__ATOMIC_RELAXED)%TR_RING;
    struct z7_trig_entry *e=&z7_trig_live.ring[n];
    e->event=event; e->word0=word0; e->word1=word1;
    e->tick_slot=(__atomic_load_n(&z7_trig_live.ticks,__ATOMIC_RELAXED)<<8)|slot;
    __atomic_store_n(&z7_trig_dirty,1,__ATOMIC_RELEASE);
}

/* Any task. Lock-free: a new event claims a zero key by compare-exchange. */
static void z7_trig_record(uint32_t slot, uint32_t event, uint32_t packet)
{
    __atomic_fetch_add(&z7_trig_live.calls[slot],1,__ATOMIC_RELAXED);
    struct z7_trig_count *row=z7_trig_live.counts[slot];
    uint32_t i=0;
    for (;i<TR_EVENTS;++i) {
        uint32_t key=__atomic_load_n(&row[i].event,__ATOMIC_ACQUIRE);
        if (!key) {
            uint32_t empty=0;
            if (__atomic_compare_exchange_n(&row[i].event,&empty,event,0,__ATOMIC_ACQ_REL,__ATOMIC_ACQUIRE)) break;
            key=empty;
        }
        if (key==event) break;
    }
    if (i<TR_EVENTS) __atomic_fetch_add(&row[i].count,1,__ATOMIC_RELAXED);
    else __atomic_fetch_add(&z7_trig_live.dropped,1,__ATOMIC_RELAXED);
    uint32_t word0=0,word1=0;
    if (packet && !(packet&3u) && packet>=0xa1800000u && packet<0xb0000000u) {
        word0=TR_W(packet); word1=TR_W(packet+4);
    }
    z7_trig_append(event,slot,word0,word1);
}

#define TR_WRAPPER(n) \
static uint32_t z7_trig_wrap##n(uint32_t event, uint32_t packet, uint32_t a2, uint32_t a3) \
{ \
    z7_trig_record(n,event,packet); \
    return TR_F(z7_trig_native[n],uint32_t,uint32_t,uint32_t,uint32_t,uint32_t)(event,packet,a2,a3); \
}
TR_WRAPPER(0)
TR_WRAPPER(1)
TR_WRAPPER(2)
static uint32_t (*const z7_trig_wrapper[TR_SLOTS])(uint32_t,uint32_t,uint32_t,uint32_t)={
    z7_trig_wrap0,z7_trig_wrap1,z7_trig_wrap2};

/* Worker task only. A failed close parks logging for this boot. */
static uint32_t z7_trig_write(void)
{
    const uint8_t *from=(const uint8_t *)&z7_trig_live;
    uint8_t *to=(uint8_t *)&z7_trig_snapshot;
    for (uint32_t i=0;i<sizeof(z7_trig_snapshot);++i) to[i]=from[i];
    z7_trig_snapshot.sequence=++z7_trig_live.sequence;
    z7_trig_snapshot.writes=++z7_trig_live.writes;
    uint32_t fd=TR_F(TR_CREATE,uint32_t,const char *,uint32_t)(z7_trig_path,0);
    if ((int32_t)fd<0) return fd;
    uint32_t actual=0;
    TR_F(TR_CLEAN,void,void *,uint32_t)(&z7_trig_snapshot,sizeof(z7_trig_snapshot));
    uint32_t result=TR_F(TR_WRITE,uint32_t,uint32_t,const void *,uint32_t,uint32_t *)(fd,&z7_trig_snapshot,sizeof(z7_trig_snapshot),&actual);
    if (TR_F(TR_CLOSE,uint32_t,uint32_t)(fd)) { z7_trig_parked=1; return 0xc105e000u; }
    if (!result && actual!=sizeof(z7_trig_snapshot)) result=0x5407e000u;
    return result;
}

static void z7_trig_worker(void)
{
    uint32_t tick=__atomic_add_fetch(&z7_trig_live.ticks,1,__ATOMIC_RELAXED);
    uint32_t silent=TR_F(TR_GETTER,uint32_t,uint32_t)(TR_SILENT_PROPERTY);
    if (silent!=z7_trig_live.silent || tick==1) {
        /* Silent photography (0x576) timeline marker, slot 3 in the ring. */
        z7_trig_live.silent=silent;
        z7_trig_append((TR_SILENT_PROPERTY<<16)|(silent&0xffffu),TR_PROPERTY_SLOT,0,0);
    }
    if (z7_trig_parked || z7_trig_live.writes>=TR_MAX_WRITES || !__atomic_load_n(&z7_trig_dirty,__ATOMIC_ACQUIRE) ||
        tick-z7_trig_last_write<TR_WRITE_EVERY) return;
    __atomic_store_n(&z7_trig_dirty,0,__ATOMIC_RELEASE);
    z7_trig_last_write=tick;
    z7_trig_write_result=z7_trig_write();
    if (z7_trig_write_result) __atomic_store_n(&z7_trig_dirty,1,__ATOMIC_RELEASE);
}

/* Initialization only, after the worker is registered: header, then each slot
 * replaced only while it still holds the recorded native handler. */
static uint32_t z7_trig_install(void)
{
    z7_trig_live.magic=TR_FILE_MAGIC; z7_trig_live.version=TR_FILE_VERSION;
    z7_trig_live.bytes=sizeof(z7_trig_live);
    uint32_t mask=0;
    for (uint32_t i=0;i<TR_SLOTS;++i)
        if (TR_W(z7_trig_slot[i])==z7_trig_native[i]) {
            TR_W(z7_trig_slot[i])=(uint32_t)(uintptr_t)z7_trig_wrapper[i];
            mask|=1u<<i;
        }
    __asm__ volatile("dmb sy" ::: "memory");
    z7_trig_live.installed_mask=mask;
    z7_trig_init_result=mask;
    return mask;
}
#endif
