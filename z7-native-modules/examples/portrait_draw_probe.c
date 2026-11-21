/* SPDX-License-Identifier: MIT. Caller-admitted portrait draw diagnostic. */
#include "module.h"
#include "../plugins/portrait_draw.h"
uint32_t z7_portrait_draw_probe(volatile uint32_t *message,
                               const struct z7_portrait_box *box, uint32_t orientation)
{ return z7_portrait_draw_box(message,box,orientation); }
uint32_t z7_main(const struct z7_module_api *api)
{ return !api || api->abi != Z7_MODULE_ABI || api->target != Z7_MODULE_TARGET || api->size < 12; }
