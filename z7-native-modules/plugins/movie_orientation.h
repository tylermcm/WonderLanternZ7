/* SPDX-License-Identifier: MIT. Independent original-Z7 movie pose policy.
 * Per-file latching and ISO track matrices follow JKWTCN's MIT movie-rotation
 * design. Original-Z7 mux open/split/close bindings are not installed here.
 * Caller serializes on the native file task and supplies current contexts.
 */
#ifndef Z7_MOVIE_ORIENTATION_H
#define Z7_MOVIE_ORIENTATION_H
#include <stdint.h>
struct z7_movie_pose { uint32_t context,pose; };
static uint32_t z7_movie_pose_latch(struct z7_movie_pose *records,uint32_t count,
    uint32_t file,uint32_t context,uint32_t reply,uint32_t pose)
{
    if (!records || !file || file>=count) return 0;
    records[file].context=0; records[file].pose=0;
    if (reply || !context || pose>3) return 0;
    records[file].pose=pose; records[file].context=context;
    return 1;
}
static uint32_t z7_movie_pose_find(const struct z7_movie_pose *records,
    const uint32_t *current,uint32_t count,uint32_t context)
{
    if (!records || !current || !context) return 0;
    uint32_t pose=0,found=0;
    for (uint32_t i=1;i<count;++i) if (records[i].context==context && current[i]==context) {
        if (found || records[i].pose>3) return 0;
        pose=records[i].pose;found=1;
    }
    return pose;
}
static uint32_t z7_movie_pose_close(struct z7_movie_pose *records,uint32_t count,uint32_t file)
{
    if (!records || !file || file>=count) return 0;
    records[file].context=records[file].pose=0; return 1;
}
static uint32_t z7_movie_matrix_apply(uint32_t pose,uint8_t *out,uint32_t bytes)
{
    if (!out || bytes<36 || !pose || pose>3) return 0;
    static const uint8_t matrices[3][36]={
        {[4]=0xff,[5]=0xff,[13]=1,[32]=0x40},
        {[5]=1,[12]=0xff,[13]=0xff,[32]=0x40},
        {[0]=0xff,[1]=0xff,[16]=0xff,[17]=0xff,[32]=0x40}
    };
    for (uint32_t i=0;i<36;++i) out[i]=matrices[pose-1][i];
    return 1;
}
#endif
