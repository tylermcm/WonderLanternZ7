/* SPDX-License-Identifier: MIT.
 * Original-Z7 shutter-sound trigger policy on the capture controller event.
 *
 * Two camera sessions (SHUTTER_SOUND_FIELD_TEST.md, November 25, 2026) showed
 * that the capture controller callback (slot 0xA18D1BD8) receives event
 * 0x0419000B exactly once per photo, once per burst frame, first in each
 * exposure's event sequence, and never outside photos. The earlier still-file
 * candidate did not fire at all in the first session, so it is not used.
 *
 * Like upstream, a sound plays only in Silent photography (property 0x576 == 1):
 * with the mechanical shutter the camera already makes its own sound.
 * Each 0x0419000B is one exposure, so there is no de-duplication; a request
 * that finds the sound service still busy is counted, not retried.
 */
#ifndef Z7_SHUTTER_SOUND_CAPTURE_TRIGGER_H
#define Z7_SHUTTER_SOUND_CAPTURE_TRIGGER_H
#include <stdint.h>

enum {
    CAP_SLOT_CONTROLLER=0u, CAP_EXPOSURE_EVENT=0x0419000bu, CAP_SILENT_ON=1u
};
enum z7_capture_decision { CAP_IGNORED=0, CAP_PLAY=1, CAP_NOT_SILENT=2 };
struct z7_capture_policy { uint32_t seen, play, not_silent; };

/* Any task. Counters only; no locks. */
static uint32_t z7_capture_decide(struct z7_capture_policy *p, uint32_t slot, uint32_t event, uint32_t silent)
{
    if (slot!=CAP_SLOT_CONTROLLER || event!=CAP_EXPOSURE_EVENT) return CAP_IGNORED;
    __atomic_add_fetch(&p->seen,1,__ATOMIC_RELAXED);
    if (silent!=CAP_SILENT_ON) { __atomic_add_fetch(&p->not_silent,1,__ATOMIC_RELAXED); return CAP_NOT_SILENT; }
    __atomic_add_fetch(&p->play,1,__ATOMIC_RELAXED);
    return CAP_PLAY;
}
#endif
