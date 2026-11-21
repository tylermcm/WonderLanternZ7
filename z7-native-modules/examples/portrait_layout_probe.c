/* SPDX-License-Identifier: MIT. Caller-owned menu orientation diagnostic. */
#include "module.h"
#include "../plugins/portrait_layout.h"
uint32_t z7_portrait_layout_probe(struct z7_portrait_layout *state,volatile const uint32_t *message,uint32_t page,uint32_t sampled)
{ return z7_portrait_layout_choose(state,message,page,sampled); }
void z7_portrait_layout_reset_probe(struct z7_portrait_layout *state)
{ z7_portrait_layout_reset(state); }
uint32_t z7_portrait_layout_draw_probe(volatile uint32_t *message,uint32_t page,uint32_t orientation)
{ return z7_portrait_page_message(message,page,orientation); }
uint32_t z7_main(const struct z7_module_api *api)
{ return !api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET || api->size<12; }
