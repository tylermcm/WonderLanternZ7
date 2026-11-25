/* SPDX-License-Identifier: MIT. Pure file-pose policy diagnostic, no hooks. */
#include "module.h"
#include "../plugins/movie_orientation.h"
struct z7_movie_pose z7_movie_records[11];
uint32_t z7_movie_contexts[11],z7_movie_reply;
uint8_t z7_movie_matrix[44];
__attribute__((noinline)) uint32_t z7_movie_operation(uint32_t op,uint32_t a,uint32_t b,uint32_t c)
{
    switch(op) {
    case 0:
        for (uint32_t i=0;i<11;++i) { z7_movie_records[i].context=z7_movie_records[i].pose=0; z7_movie_contexts[i]=0; }
        return 1;
    case 1:return z7_movie_pose_latch(z7_movie_records,11,a,b,z7_movie_reply,c);
    case 2:return z7_movie_pose_find(z7_movie_records,z7_movie_contexts,11,a);
    case 3:return z7_movie_pose_close(z7_movie_records,11,a);
    case 4:return z7_movie_matrix_apply(a,z7_movie_matrix,b);
    default:return 0;
    }
}
uint32_t z7_main(const struct z7_module_api *api)
{
    return !api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET || api->size<12 || !z7_movie_operation(0,0,0,0);
}
