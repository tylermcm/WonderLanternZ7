/* SPDX-License-Identifier: MIT.
 * Original-Z7 shutter-sound trigger policy, PROVISIONAL: still-file finalization.
 *
 * Nikon's still-file writer sends 0x041E0002 with packet {record, flag, 0} after a
 * file is finalized (STILL_FILE_TRACE.md). The record packs slot (bits 29-30),
 * group (19-28), number (5-18) and kind (0-3). JPEG+NEF saves two records with
 * the same slot/group/number, so the key ignores kind and a recently seen key is
 * not played twice. Sound only in Silent photography (property 0x576 == 1),
 * like upstream: with the mechanical shutter the camera already makes a sound.
 *
 * Whether this event is exactly one per photo, and never in live view, is what
 * the trigger probe measures on the camera. Until then this policy is a
 * candidate only. Single caller task (the still-file notification); no locks.
 */
#ifndef Z7_SHUTTER_SOUND_TRIGGER_H
#define Z7_SHUTTER_SOUND_TRIGGER_H
#include <stdint.h>

enum {
    TRG_STILL_FILE_EVENT=0x041e0002u, TRG_KEY_MASK=0x7fffffe0u,
    TRG_RECENT=8u, TRG_SILENT_ON=1u
};
enum z7_trigger_decision {
    TRG_IGNORED=0, TRG_PLAY=1, TRG_DUPLICATE=2, TRG_NOT_SILENT=3, TRG_NO_RECORD=4
};
struct z7_trigger_policy {
    uint32_t recent[TRG_RECENT], next;
    uint32_t played, duplicates, not_silent, ignored, no_record;
};

static uint32_t z7_trigger_key(uint32_t record) { return record & TRG_KEY_MASK; }

/* Decide for one notification. A key is remembered even when not played (not
 * silent), so turning Silent photography on mid-save doesn't sound an old photo. */
static uint32_t z7_trigger_still_file(struct z7_trigger_policy *p, uint32_t event,
                                      uint32_t record, uint32_t silent)
{
    if (event!=TRG_STILL_FILE_EVENT) { ++p->ignored; return TRG_IGNORED; }
    uint32_t key=z7_trigger_key(record);
    if (!key) { ++p->no_record; return TRG_NO_RECORD; }
    for (uint32_t i=0;i<TRG_RECENT;++i)
        if (p->recent[i]==key) { ++p->duplicates; return TRG_DUPLICATE; }
    p->recent[p->next%TRG_RECENT]=key;
    p->next=(p->next+1)%TRG_RECENT;
    if (silent!=TRG_SILENT_ON) { ++p->not_silent; return TRG_NOT_SILENT; }
    ++p->played;
    return TRG_PLAY;
}
#endif
