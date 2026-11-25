/* SPDX-License-Identifier: MIT.
 * Original-Z7 C 3.80 upside-down photo EXIF orientation. Design follows
 * JKWTCN's MIT Z7II photo_rotation.h (2b596ab); original-Z7 bindings derived
 * independently (EXIF_ORIENTATION_RESEARCH.md).
 *
 * Nikon's IFD0 writer table (38 entries at 0x11532D94) gives Orientation (0x0112,
 * entry 9) the writer 0x102868D9, which maps the capture pose byte at +0x24FD as
 * 0->1, 1->8, 2->6 and anything else->1. The camera's own orientation API uses
 * 3 for inverted landscape, and Nikon's EXIF reader decodes 1/8/6 to 0/1/2 with
 * 3 left as the gap, so an upside-down photo is saved as Orientation 1. This
 * component copies the table to RAM, swaps only entry 9's writer, and writes 3
 * (rotate 180) for pose 3; every other pose runs Nikon's writer unchanged.
 *
 * The table is reached through a RAM getter slot holding {getter, count}; it is
 * replaced only while it holds the stock pair and the stock entry matches.
 * Whether the camera stores pose 3 for an upside-down exposure is measured on the
 * camera (the field test logs every pose this writer sees).
 */
#ifndef Z7_PHOTO_ORIENTATION_EXIF_H
#define Z7_PHOTO_ORIENTATION_EXIF_H
#include <stdint.h>

#ifndef Z7_EXIF_IFD_SLOT
#error "Z7_EXIF_IFD_SLOT must be the live RAM address of the {getter,count} pair"
#endif
enum {
    EXIF_IFD_GET=0x1028bb5fu, EXIF_IFD_COUNT=0x1028bb8bu, EXIF_IFD_STOCK=0x11532d94u,
    EXIF_ORIENTATION_WRITE=0x102868d9u, EXIF_ORIENTATION_TAG=0x00030112u,
    EXIF_POSE=0x24fdu, EXIF_ENTRIES=0x26u, EXIF_ORIENTATION_INDEX=9u, EXIF_POSE_INVERTED=3u
};
struct z7_exif_entry {
    uint32_t type_tag, count, flags;
    void (*write)(uint16_t *, const uint32_t *, void *);
};
static struct z7_exif_entry z7_exif_entries[EXIF_ENTRIES];
volatile uint32_t z7_exif_installed, z7_exif_writes, z7_exif_inverted, z7_exif_last_pose;
#ifndef Z7_EXIF_POSE_HOOK
#define Z7_EXIF_POSE_HOOK(pose) ((void)(pose))
#endif

/* Runs on Nikon's file-writer task while it builds IFD0. */
static void z7_exif_orientation_write(uint16_t *entry, const uint32_t *metadata, void *writer)
{
    const uint8_t *capture=(const uint8_t *)(uintptr_t)metadata[1];
    uint32_t pose=capture[EXIF_POSE];
    z7_exif_last_pose=pose; ++z7_exif_writes;
    Z7_EXIF_POSE_HOOK(pose);
    if (pose==EXIF_POSE_INVERTED) {
        entry[4]=3;  /* value field of the 12-byte IFD entry: rotate 180 */
        ++z7_exif_inverted;
        return;
    }
    ((void (*)(uint16_t *, const uint32_t *, void *))(uintptr_t)EXIF_ORIENTATION_WRITE)(entry,metadata,writer);
}

static const struct z7_exif_entry *z7_exif_get(void) { return z7_exif_entries; }

static uint32_t z7_exif_matches(void)
{
    const volatile uint32_t *w=(const volatile uint32_t *)(uintptr_t)(EXIF_ORIENTATION_WRITE-1u);
    return w[0]==0x2101684au;  /* ldr r2,[r1,#4]; movs r1,#1 */
}

/* Initialization only. Returns 1 when installed. */
static uint32_t z7_exif_install(void)
{
    volatile uint32_t *slot=(volatile uint32_t *)(uintptr_t)Z7_EXIF_IFD_SLOT;
    const struct z7_exif_entry *stock=(const struct z7_exif_entry *)(uintptr_t)EXIF_IFD_STOCK;
    if (slot[0]!=EXIF_IFD_GET || slot[1]!=EXIF_IFD_COUNT || !z7_exif_matches() ||
        stock[EXIF_ORIENTATION_INDEX].type_tag!=EXIF_ORIENTATION_TAG || stock[EXIF_ORIENTATION_INDEX].count!=1 ||
        (uint32_t)(uintptr_t)stock[EXIF_ORIENTATION_INDEX].write!=EXIF_ORIENTATION_WRITE) return 0;
    for (uint32_t i=0;i<EXIF_ENTRIES;++i) z7_exif_entries[i]=stock[i];
    z7_exif_entries[EXIF_ORIENTATION_INDEX].write=z7_exif_orientation_write;
    __atomic_store_n(slot,(uint32_t)(uintptr_t)z7_exif_get,__ATOMIC_RELEASE);
    z7_exif_installed=1;
    return 1;
}
#endif
