/* SPDX-License-Identifier: MIT. Caller-admitted synchronous text diagnostic. */
#include "module.h"
#include "../plugins/portrait_text.h"
uint32_t z7_portrait_text_probe(volatile uint32_t *message,const struct z7_portrait_text_transform *transform)
{ return z7_portrait_text_draw(message,transform); }
uint32_t z7_main(const struct z7_module_api *api)
{ return !api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET || api->size<12; }
