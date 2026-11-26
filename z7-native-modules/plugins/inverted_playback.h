/* SPDX-License-Identifier: MIT.
 * Original-Z7 C 3.80 upside-down photo PLAYBACK (experimental).
 * Design follows JKWTCN's MIT Z7II inverted playback (94be0b3): report a half
 * turn for upside-down photos so Nikon's own renderer turns them.
 * Original-Z7 bindings (EXIF_ORIENTATION_RESEARCH.md, field tests Nov 25, 2026):
 *  - Display requests are built into two blocks with the same layout (+0 image
 *    id, +0x28 rotation code 0..3; Nikon's converter accepts 2): 0xA289A264
 *    (0x103D3854, message 0x04160009) and 0xA289A2D4 (0x103D1D54, message
 *    0x04160004), and handled by the PlaybackProcess queue handler, whose
 *    pointer lives in RAM at 0xA289C1D8 (stock 0x10315F5D) and is read for every
 *    message. The wrapper sets rotation 2 in either block just before Nikon
 *    reads it. The first camera test (Nov 25) turned nothing while only the
 *    first block was handled.
 *  - A:\Z7IPDBG.DAT records what the wrapper saw (message ids, blocks, ids,
 *    rotations, turns) so a camera run can be diagnosed from the card.
 *  - Nikon's lookup never reports a half turn, and its index of files maps EXIF
 *    Orientation 3 to "no rotation", so the module keeps its own list: when the
 *    EXIF Orientation writer sees capture pose 3 (upside down), the next new
 *    photo record on the still-file event 0x041E0002 is remembered, in
 *    A:\Z7INV.DAT. Only photos taken with this module are known.
 * The native handlers always run with the same arguments and results.
 */
#ifndef Z7_INVERTED_PLAYBACK_H
#define Z7_INVERTED_PLAYBACK_H
#include <stdint.h>

#define IP_W(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define IP_H(a) (*(volatile uint16_t *)(uintptr_t)(a))
#define IP_F(a,r,...) ((r (*)(__VA_ARGS__))(uintptr_t)(a))
enum {
    IP_HANDLER_SLOT=0xa289c1d8u, IP_HANDLER_NATIVE=0x10315f5du,
    IP_REQUEST=0xa289a264u, IP_REQUEST2=0xa289a2d4u, IP_REQUEST_ROTATION=0x28u, IP_DISPLAY=0x04160009u,
    IP_DEBUG_MAGIC=0x47424437u /* "7DBG" */, IP_DEBUG_IDS=8u,
    IP_STILL_SLOT=0xa18d2750u, IP_STILL_NATIVE=0x104db211u, IP_STILL_FILE=0x041e0002u,
    IP_KEY=0x7fffffe0u, IP_KEYS=256u, IP_POSES=16u, IP_HALF_TURN=2u, IP_INVERTED_POSE=3u,
    IP_MAGIC=0x564e4937u /* "7INV" */, IP_VERSION=1u,
    IP_OPEN=0x1027bfa3u, IP_READ=0x1027c019u, IP_CREATE=0x1027c0dbu, IP_WRITE=0x1027c049u,
    IP_CLOSE=0x1027bfcdu, IP_CLEAN=0x101e9f39u, IP_INVALIDATE=0x101e9f77u
};
static const char z7_ip_path[]="A:\\Z7INV.DAT";
static const char z7_ip_debug_path[]="A:\\Z7IPDBG.DAT";
/* Diagnostic counters, written by the worker when they change. */
struct z7_ip_debug {
    uint32_t magic, version, sequence, flags;            /* flags: handler, still, loaded, count */
    uint32_t messages, block1, block2, rotated;
    uint32_t last_message, last_block, last_image, last_rotation;
    uint32_t message_ids[IP_DEBUG_IDS], message_counts[IP_DEBUG_IDS];
    uint32_t still_events, poses, poses_inverted, keys;
};
static _Alignas(64) struct z7_ip_debug z7_ip_debug_file;
static struct z7_ip_debug z7_ip_debug_live;
volatile uint32_t z7_ip_debug_dirty, z7_ip_debug_writes, z7_ip_debug_tick;
struct z7_ip_file { uint32_t magic, version, count, check, keys[IP_KEYS]; };
static _Alignas(64) struct z7_ip_file z7_ip_file;
static uint32_t z7_ip_keys[IP_KEYS];
volatile uint32_t z7_ip_count, z7_ip_next, z7_ip_dirty, z7_ip_loaded, z7_ip_handler_installed, z7_ip_still_installed;
volatile uint32_t z7_ip_requests, z7_ip_rotated, z7_ip_marked, z7_ip_saves, z7_ip_errors, z7_ip_result;
static volatile uint8_t z7_ip_poses[IP_POSES];
static volatile uint32_t z7_ip_pose_head, z7_ip_pose_tail, z7_ip_last_key, z7_ip_quiet, z7_ip_retry;

static uint32_t z7_ip_native_ok(void)
{
    /* Prologues of the two wrapped native handlers and the file wrappers. */
    return IP_W(0x10315f5cu)==0x43fee92du && IP_W(IP_STILL_NATIVE-1u)==0x2900b538u &&
        IP_W(IP_OPEN-1u)==0xb0aab570u && IP_W(IP_READ-1u)==0xb0abb5f0u && IP_W(IP_CREATE-1u)==0xb0abb530u &&
        IP_W(IP_WRITE-1u)==0xb0abb5f0u && IP_W(IP_CLOSE-1u)==0xb0aab510u;
}
static uint32_t z7_ip_check(const struct z7_ip_file *f)
{
    uint32_t v=f->magic^(f->version<<8)^f->count^0x5a5a5a5au;
    for (uint32_t i=0;i<IP_KEYS;++i) v=(v<<5|v>>27)^f->keys[i];
    return v;
}
static uint32_t z7_ip_contains(uint32_t key)
{
    uint32_t n=__atomic_load_n(&z7_ip_count,__ATOMIC_ACQUIRE);
    for (uint32_t i=0;i<n && i<IP_KEYS;++i) if (z7_ip_keys[i]==key) return 1;
    return 0;
}
/* Still-file task. Oldest entry is replaced once the list is full. */
static void z7_ip_add(uint32_t key)
{
    if (!key || z7_ip_contains(key)) return;
    uint32_t n=z7_ip_count, slot=n<IP_KEYS ? n : z7_ip_next%IP_KEYS;
    z7_ip_keys[slot]=key;
    if (n<IP_KEYS) __atomic_store_n(&z7_ip_count,n+1,__ATOMIC_RELEASE);
    else z7_ip_next=(z7_ip_next+1)%IP_KEYS;
    ++z7_ip_marked;
    __atomic_store_n(&z7_ip_dirty,1,__ATOMIC_RELEASE);
}

/* File-writer task: called from the EXIF Orientation writer for every photo. */
static void z7_ip_pose(uint32_t pose)
{
    ++z7_ip_debug_live.poses;
    if (pose==IP_INVERTED_POSE) ++z7_ip_debug_live.poses_inverted;
    z7_ip_debug_dirty=1;
    uint32_t head=z7_ip_pose_head;
    if (head-z7_ip_pose_tail>=IP_POSES) ++z7_ip_pose_tail;  /* keep the newest */
    z7_ip_poses[head%IP_POSES]=(uint8_t)pose;
    __atomic_store_n(&z7_ip_pose_head,head+1,__ATOMIC_RELEASE);
}

/* Still-file notification: pair each new photo record with the oldest pose. */
static uint32_t z7_ip_still(uint32_t event, uint32_t packet, uint32_t a2, uint32_t a3)
{
    if (event==IP_STILL_FILE && packet && !(packet&3u) && packet>=0xa1800000u && packet<0xb0000000u) {
        ++z7_ip_debug_live.still_events; z7_ip_debug_dirty=1;
        uint32_t key=IP_W(packet)&IP_KEY;
        if (key && key!=z7_ip_last_key) {
            z7_ip_last_key=key;
#ifdef Z7_STILL_KEY_HOOK
            Z7_STILL_KEY_HOOK(key);
#endif
            uint32_t tail=z7_ip_pose_tail;
            if (tail!=__atomic_load_n(&z7_ip_pose_head,__ATOMIC_ACQUIRE)) {
                uint32_t pose=z7_ip_poses[tail%IP_POSES];
                z7_ip_pose_tail=tail+1;
                if (pose==IP_INVERTED_POSE) z7_ip_add(key);
            }
        }
    }
    return IP_F(IP_STILL_NATIVE,uint32_t,uint32_t,uint32_t,uint32_t,uint32_t)(event,packet,a2,a3);
}

/* PlaybackProcess task: Nikon handles the display request right after this. */
static uint32_t z7_ip_handler(uint32_t message, uint32_t a1, uint32_t a2, uint32_t a3)
{
    if (message && !(message&3u) && message>=0xa1800000u && message<0xb0000000u-32u) {
        uint32_t command=IP_W(message+16), block=IP_W(message+20);
        struct z7_ip_debug *d=&z7_ip_debug_live;
        ++d->messages; d->last_message=command;
        for (uint32_t i=0;i<IP_DEBUG_IDS;++i) {
            if (d->message_ids[i]==command) { ++d->message_counts[i]; break; }
            if (!d->message_ids[i]) { d->message_ids[i]=command; d->message_counts[i]=1; break; }
        }
        if (block==IP_REQUEST || block==IP_REQUEST2) {
            __atomic_add_fetch(&z7_ip_requests,1,__ATOMIC_RELAXED);
            if (block==IP_REQUEST) ++d->block1; else ++d->block2;
            uint32_t image=IP_W(block), rotation=IP_H(block+IP_REQUEST_ROTATION);
            d->last_block=block; d->last_image=image; d->last_rotation=rotation;
            if (rotation==0 && z7_ip_contains(image&IP_KEY)) {
                IP_H(block+IP_REQUEST_ROTATION)=IP_HALF_TURN;
                __atomic_add_fetch(&z7_ip_rotated,1,__ATOMIC_RELAXED);
                ++d->rotated;
            }
        }
        z7_ip_debug_dirty=1;
    }
    return IP_F(IP_HANDLER_NATIVE,uint32_t,uint32_t,uint32_t,uint32_t,uint32_t)(message,a1,a2,a3);
}

static void z7_ip_try_handler(void)
{
    if (z7_ip_handler_installed || IP_W(IP_HANDLER_SLOT)!=IP_HANDLER_NATIVE) return;
    __asm__ volatile("dmb sy" ::: "memory");
    IP_W(IP_HANDLER_SLOT)=(uint32_t)(uintptr_t)z7_ip_handler;
    __asm__ volatile("dmb sy" ::: "memory");
    z7_ip_handler_installed=1;
}

/* Loader task, once. Never fails the module. */
static void z7_ip_prepare(void)
{
    if (!z7_ip_native_ok()) return;
    uint32_t fd=IP_F(IP_OPEN,uint32_t,const char *,uint32_t,uint32_t)(z7_ip_path,0,0);
    if ((int32_t)fd>=0) {
        uint32_t actual=0;
        IP_F(IP_INVALIDATE,void,void *,uint32_t)(&z7_ip_file,sizeof(z7_ip_file));
        uint32_t result=IP_F(IP_READ,uint32_t,uint32_t,void *,uint32_t,uint32_t *)(fd,&z7_ip_file,sizeof(z7_ip_file),&actual);
        IP_F(IP_INVALIDATE,void,void *,uint32_t)(&z7_ip_file,sizeof(z7_ip_file));
        uint32_t closed=IP_F(IP_CLOSE,uint32_t,uint32_t)(fd);
        if (!result && !closed && actual==sizeof(z7_ip_file) && z7_ip_file.magic==IP_MAGIC &&
            z7_ip_file.version==IP_VERSION && z7_ip_file.count<=IP_KEYS && z7_ip_file.check==z7_ip_check(&z7_ip_file)) {
            for (uint32_t i=0;i<z7_ip_file.count;++i) z7_ip_keys[i]=z7_ip_file.keys[i];
            z7_ip_count=z7_ip_file.count; z7_ip_loaded=1;
        } else z7_ip_loaded=2;
    }
    if (IP_W(IP_STILL_SLOT)==IP_STILL_NATIVE) {
        __asm__ volatile("dmb sy" ::: "memory");
        IP_W(IP_STILL_SLOT)=(uint32_t)(uintptr_t)z7_ip_still;
        __asm__ volatile("dmb sy" ::: "memory");
        z7_ip_still_installed=1;
    }
    z7_ip_try_handler();
}

/* Resident worker: late handler install, and save the list one quiet tick
 * after a change; a failed write retries after five ticks. */
/* Worker: diagnostic snapshot at most every three ticks when something changed. */
static void z7_ip_debug_write(void)
{
    if (!z7_ip_debug_dirty || ++z7_ip_debug_tick<3u || z7_ip_debug_writes>=200u) return;
    z7_ip_debug_tick=0; z7_ip_debug_dirty=0;
    const volatile uint32_t *from=(const volatile uint32_t *)&z7_ip_debug_live;
    uint32_t *to=(uint32_t *)&z7_ip_debug_file;
    for (uint32_t i=0;i<sizeof(z7_ip_debug_file)/4;++i) to[i]=from[i];  /* no memcpy in modules */
    z7_ip_debug_file.magic=IP_DEBUG_MAGIC; z7_ip_debug_file.version=1;
    z7_ip_debug_file.sequence=++z7_ip_debug_writes;
    z7_ip_debug_file.flags=(z7_ip_handler_installed&1u)|((z7_ip_still_installed&1u)<<1)|((z7_ip_loaded&3u)<<2)|(z7_ip_count<<8);
    z7_ip_debug_file.keys=z7_ip_count;
    IP_F(IP_CLEAN,void,void *,uint32_t)(&z7_ip_debug_file,sizeof(z7_ip_debug_file));
    uint32_t fd=IP_F(IP_CREATE,uint32_t,const char *,uint32_t)(z7_ip_debug_path,0), actual=0;
    if ((int32_t)fd<0) return;
    IP_F(IP_WRITE,uint32_t,uint32_t,const void *,uint32_t,uint32_t *)(fd,&z7_ip_debug_file,sizeof(z7_ip_debug_file),&actual);
    IP_F(IP_CLOSE,uint32_t,uint32_t)(fd);
}

static void z7_ip_worker(void)
{
    if (!z7_ip_native_ok()) return;
    z7_ip_try_handler();
    z7_ip_debug_write();
    if (!__atomic_load_n(&z7_ip_dirty,__ATOMIC_ACQUIRE)) { z7_ip_quiet=0; return; }
    if (z7_ip_quiet<1u) { ++z7_ip_quiet; return; }
    if (z7_ip_retry) { --z7_ip_retry; return; }
    __atomic_store_n(&z7_ip_dirty,0,__ATOMIC_RELEASE);
    uint32_t n=__atomic_load_n(&z7_ip_count,__ATOMIC_ACQUIRE);
    z7_ip_file.magic=IP_MAGIC; z7_ip_file.version=IP_VERSION; z7_ip_file.count=n;
    for (uint32_t i=0;i<IP_KEYS;++i) z7_ip_file.keys[i]=i<n ? z7_ip_keys[i] : 0;
    z7_ip_file.check=z7_ip_check(&z7_ip_file);
    IP_F(IP_CLEAN,void,void *,uint32_t)(&z7_ip_file,sizeof(z7_ip_file));
    uint32_t fd=IP_F(IP_CREATE,uint32_t,const char *,uint32_t)(z7_ip_path,0);
    uint32_t result=fd, actual=0;
    if ((int32_t)fd>=0) {
        result=IP_F(IP_WRITE,uint32_t,uint32_t,const void *,uint32_t,uint32_t *)(fd,&z7_ip_file,sizeof(z7_ip_file),&actual);
        uint32_t closed=IP_F(IP_CLOSE,uint32_t,uint32_t)(fd);
        if (!result && (closed || actual!=sizeof(z7_ip_file))) result=0x5407e000u;
    }
    z7_ip_result=result;
    if (!result) ++z7_ip_saves;
    else { ++z7_ip_errors; z7_ip_retry=5u; __atomic_store_n(&z7_ip_dirty,1,__ATOMIC_RELEASE); }
}
#endif
