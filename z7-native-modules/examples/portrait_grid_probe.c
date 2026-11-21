/* SPDX-License-Identifier: MIT. Caller-admitted original-Z7 grid reflow diagnostic. */
#include "module.h"
#include "../plugins/portrait_grid.h"
#include "../plugins/portrait_draw.h"
uint32_t z7_portrait_grid_probe(volatile uint32_t *message,const struct z7_portrait_box *stock,
                               uint32_t orientation,uint32_t edge)
{
    if (!stock) return 0;
    struct z7_portrait_box boxes[2]; uint32_t count;
    if (edge) count=z7_portrait_grid_edge(stock,boxes);
    else { boxes[0]=*stock; count=z7_portrait_grid_relocate(boxes,0); }
    return count ? z7_portrait_draw_boxes(message,boxes,count,orientation) : 0;
}
uint32_t z7_portrait_batch_probe(volatile uint32_t *message,const struct z7_portrait_box *boxes,
                                uint32_t count,uint32_t orientation)
{ return z7_portrait_draw_boxes(message,boxes,count,orientation); }
uint32_t z7_portrait_grid_geometry_probe(struct z7_portrait_box *box,uint32_t image)
{ return z7_portrait_grid_relocate(box,image); }
uint32_t z7_main(const struct z7_module_api *api)
{ return !api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET || api->size<12; }
