/* SPDX-License-Identifier: MIT.
 * Original-Z7 C 3.80 playback rotation OBSERVER (read-only). Polls the two
 * RAM places Nikon's playback fills while showing a photo
 * (EXIF_ORIENTATION_RESEARCH.md, "In-camera playback"):
 *  - the PlaybackProcess display request 0xA289A264, built by 0x103D3854 for
 *    message 0x04160011: image id at +0, rotation code at +0x28 (0..3);
 *  - the per-image turn cache of lookup 0x103D4C10 at 0xA18E4DB8: turn at +0,
 *    image id at +0x1C.
 * Each change is reported through Z7_PB_REPORT(event, request_id, cache_id)
 * with event 0x9B000000 | turn<<8 | rotation. Reads four words, writes nothing
 * in camera RAM, calls no firmware. Bounded to Z7_PB_MAX reports per boot.
 */
#ifndef Z7_PLAYBACK_OBSERVER_H
#define Z7_PLAYBACK_OBSERVER_H
#include <stdint.h>

#ifndef Z7_PB_REPORT
#error "Z7_PB_REPORT(event, request_id, cache_id) must be defined"
#endif
#ifndef Z7_PB_MAX
#define Z7_PB_MAX 48u
#endif
enum {
    PB_REQUEST=0xa289a264u, PB_REQUEST_ROTATION=0x28u,
    PB_CACHE=0xa18e4db8u, PB_CACHE_ID=0x1cu, PB_EVENT=0x9b000000u
};
static uint32_t z7_pb_last[4]={0xffffffffu,0xffffffffu,0xffffffffu,0xffffffffu};
volatile uint32_t z7_pb_reports;

/* Worker task only. */
static void z7_pb_poll(void)
{
    uint32_t now[4]={
        *(volatile uint32_t *)(uintptr_t)PB_REQUEST,
        *(volatile uint16_t *)(uintptr_t)(PB_REQUEST+PB_REQUEST_ROTATION),
        *(volatile uint8_t *)(uintptr_t)PB_CACHE,
        *(volatile uint32_t *)(uintptr_t)(PB_CACHE+PB_CACHE_ID)};
    if (now[0]==z7_pb_last[0] && now[1]==z7_pb_last[1] && now[2]==z7_pb_last[2] && now[3]==z7_pb_last[3]) return;
    for (uint32_t i=0;i<4;++i) z7_pb_last[i]=now[i];
    if (z7_pb_reports>=Z7_PB_MAX) return;
    ++z7_pb_reports;
    Z7_PB_REPORT(PB_EVENT|((now[2]&0xffu)<<8)|(now[1]&0xffu),now[0],now[3]);
}
#endif
