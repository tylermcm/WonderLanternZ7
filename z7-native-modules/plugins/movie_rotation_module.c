/* SPDX-License-Identifier: MIT. Independent original-Z7 offline mux trial.
 * Runtime native shadows and per-file pose concept follow JKWTCN's MIT design.
 * Original-Z7 call maps and fingerprints are independently derived. No firmware
 * bytes embedded. Prepare-only by default; installation requires separate review.
 */
#include "module.h"
#include "movie_orientation.h"
#include "orientation_sample.h"
#include "movie_native_bindings.h"
#define MW(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define MF(a,r,...) ((r (*)(__VA_ARGS__))(uintptr_t)(a))
#define COUNT(a) (sizeof(a)/sizeof((a)[0]))
#define MOVIE_ROOT 0xa1f532f8u
#define MOVIE_CONTROL (MOVIE_ROOT+0x40u)
#define MOVIE_SLOT (MOVIE_ROOT+0x2cu)
static struct z7_movie_pose movie_poses[11];
static _Alignas(64) uint8_t movie_task_copy[MOVIE_TASK_SIZE+2+sizeof(movie_task_calls)*2+16];
static _Alignas(64) uint8_t movie_close_copy[MOVIE_CLOSE_SIZE+2+sizeof(movie_close_calls)*2+16];
static _Alignas(64) uint8_t movie_header_copy[MOVIE_HEADER_SIZE+sizeof(movie_header_calls)*2+16];
volatile uint32_t z7_movie_prepared,z7_movie_installed;
static uint32_t movie_installable(void)
{
    /* Necessary idle guards only. These do not prove task quiescence or make
     * publication a camera-cleared action; this operation is offline diagnostic.
     */
    return !z7_movie_installed && MW(0xa1815030u)==MOVIE_CONTROL &&
        MW(MOVIE_SLOT)==(MOVIE_TASK_NATIVE|1) && !MW(0xa181503cu) &&
        !MW(MOVIE_CONTROL) && !MW(MOVIE_CONTROL+0x50) && !MW(MOVIE_CONTROL+0x64);
}
static uint32_t movie_task_address(void) { return (uint32_t)(uintptr_t)movie_task_copy+2; }
static uint32_t movie_close_address(void) { return (uint32_t)(uintptr_t)movie_close_copy+2; }
static uint32_t movie_header_address(void) { return (uint32_t)(uintptr_t)movie_header_copy; }
static uint32_t movie_context(uint32_t file)
{
    if (!file || file>10 || MW(0xa1815030u)!=MOVIE_CONTROL) return 0;
    return MW(MOVIE_CONTROL+0x3f0u+file*0x88u+0x2cu);
}
static uint32_t movie_latch(uint32_t file,uint32_t reply_offset)
{
    if (!file || file>10) return file;
    z7_movie_pose_close(movie_poses,11,file);
    if (MW(0xa1815030u)!=MOVIE_CONTROL) return file;
    uint32_t reply=MW(MOVIE_CONTROL+reply_offset+file*8+4),context=movie_context(file),pose=0;
    if (!reply && context && z7_orientation_sample(&pose))
        z7_movie_pose_latch(movie_poses,11,file,context,reply,pose);
    return file;
}
static uint32_t movie_open(void) { return movie_latch(MF(0x1027e50bu,uint32_t,void)(),0x160); }
static uint32_t movie_split(void) { return movie_latch(MF(0x1027de97u,uint32_t,void)(),0x318); }
static uint32_t movie_track(uint32_t context)
{
    uint32_t result=MF(0x102a9c2du,uint32_t,uint32_t)(context);
    if (result || !context || MW(0xa1815030u)!=MOVIE_CONTROL) return result;
    uint32_t current[11];current[0]=0;
    for (uint32_t file=1;file<=10;++file) current[file]=movie_context(file);
    uint32_t pose=z7_movie_pose_find(movie_poses,current,11,context);
    z7_movie_matrix_apply(pose,(uint8_t *)(uintptr_t)(context+0x109),36);
    return result;
}
static uint32_t movie_copy(uint32_t destination,uint32_t source,uint32_t size,uint32_t expected)
{
    uint32_t hash=2166136261u;
    for (uint32_t i=0;i<size;++i) hash=(hash^*(volatile uint8_t *)(uintptr_t)(source+i))*16777619u;
    if (hash!=expected) return 0;
    for (uint32_t i=0;i<size;++i) *(uint8_t *)(uintptr_t)(destination+i)=*(volatile uint8_t *)(uintptr_t)(source+i);
    return 1;
}
static void movie_write_call(uint32_t site,uint32_t stub,uint32_t target)
{
    uint32_t offset=stub-(site+4),s=(offset>>24)&1,imm10=(offset>>12)&1023,imm11=(offset>>1)&2047;
    uint32_t j1=1^(((offset>>23)&1)^s),j2=1^(((offset>>22)&1)^s);
    *(uint16_t *)(uintptr_t)site=(uint16_t)(0xf000|(s<<10)|imm10);
    *(uint16_t *)(uintptr_t)(site+2)=(uint16_t)(0xd000|(j1<<13)|(j2<<11)|imm11);
    *(uint16_t *)(uintptr_t)stub=0xf8df;*(uint16_t *)(uintptr_t)(stub+2)=0xf000;
    MW(stub+4)=target;
}
static uint32_t movie_relocate(uint32_t code,uint32_t size,const uint32_t calls[][2],uint32_t count)
{
    uint32_t stub=(code+size+3)&~3u;
    for (uint32_t i=0;i<count;++i,stub+=8) movie_write_call(code+calls[i][0],stub,calls[i][1]);
    return stub;
}
static uint32_t movie_prepare(void)
{
    if (z7_movie_installed || MW(0xa1815030u)!=MOVIE_CONTROL || MW(MOVIE_SLOT)!=(MOVIE_TASK_NATIVE|1)) return 0;
    uint32_t task=movie_task_address(),close=movie_close_address(),header=movie_header_address();
    z7_movie_prepared=0;
    if (!movie_copy(task,MOVIE_TASK_NATIVE,MOVIE_TASK_SIZE,MOVIE_TASK_HASH) ||
        !movie_copy(close,MOVIE_CLOSE_NATIVE,MOVIE_CLOSE_SIZE,MOVIE_CLOSE_HASH) ||
        !movie_copy(header,MOVIE_HEADER_NATIVE,MOVIE_HEADER_SIZE,MOVIE_HEADER_HASH)) return 0;
    uint32_t stub=movie_relocate(task,MOVIE_TASK_SIZE,movie_task_calls,COUNT(movie_task_calls));
    movie_write_call(task+0x4a,stub,(uint32_t)(uintptr_t)movie_open);
    movie_write_call(task+0x1d4,stub+8,(uint32_t)(uintptr_t)movie_split);
    movie_write_call(task+0x23e,stub+16,close|1);
    stub=movie_relocate(close,MOVIE_CLOSE_SIZE,movie_close_calls,COUNT(movie_close_calls));
    movie_write_call(close+0xbc,stub,header|1);
    stub=movie_relocate(header,MOVIE_HEADER_SIZE,movie_header_calls,COUNT(movie_header_calls));
    movie_write_call(header+0x1c,stub,(uint32_t)(uintptr_t)movie_track);
    z7_movie_prepared=1;return 1;
}
static uint32_t movie_install(void)
{
    if (!movie_installable() || !movie_prepare()) return 0;
    MF(0x101e9f39u,void,void *,uint32_t)(movie_task_copy,sizeof(movie_task_copy));
    MF(0x101e9f39u,void,void *,uint32_t)(movie_close_copy,sizeof(movie_close_copy));
    MF(0x101e9f39u,void,void *,uint32_t)(movie_header_copy,sizeof(movie_header_copy));
    uint32_t zero=0;
    __asm__ volatile("dsb sy\n mcr p15,0,%0,c7,c5,0\n mcr p15,0,%0,c7,c5,6\n dsb sy\n isb" :: "r"(zero) : "memory");
    if (!movie_installable()) return 0;
    for (uint32_t i=0;i<11;++i) z7_movie_pose_close(movie_poses,11,i);
    __asm__ volatile("dmb sy" ::: "memory");
    MW(MOVIE_SLOT)=movie_task_address()|1;
    z7_movie_installed=1;return 1;
}
/* Explicit offline diagnostics. Standalone initialization never publishes a callback.
 * Operation7 requires its own offline fixture, never arbitrary camera calls.
 */
__attribute__((noinline)) uint32_t z7_movie_rotation_operation(uint32_t op,uint32_t arg)
{
    switch(op) {
    case 0:return movie_prepare();
    case 1:return movie_open();
    case 2:return movie_split();
    case 3:return movie_track(arg);
    case 4:return movie_task_address();
    case 5:return movie_close_address();
    case 6:return movie_header_address();
    case 7:return movie_install();
    default:return 0;
    }
}
#ifndef Z7_MOVIE_ROTATION_EMBEDDED
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET || api->size<12) return 1;
    return movie_prepare()?0:1;
}
#endif
