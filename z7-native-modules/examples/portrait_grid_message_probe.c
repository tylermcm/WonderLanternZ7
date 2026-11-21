/* SPDX-License-Identifier: MIT. Caller-admitted GRID message diagnostic. */
#include "module.h"
#include "../plugins/portrait_grid_message.h"
uint32_t z7_portrait_grid_message_probe(volatile uint32_t *message,uint32_t orientation)
{ return z7_portrait_grid_message(message,orientation); }
uint32_t z7_portrait_message_source_probe(volatile const uint32_t *message,struct z7_portrait_draw_source *out)
{ return z7_portrait_message_source(message,out); }
uint32_t z7_main(const struct z7_module_api *api)
{ return !api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET || api->size<12; }
