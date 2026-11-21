/* SPDX-License-Identifier: MIT. Caller-admitted original-Z7 footer diagnostic. */
#include "module.h"
#include "../plugins/portrait_page_message.h"
uint32_t z7_portrait_page_message_probe(volatile uint32_t *message,uint32_t page,uint32_t orientation)
{ return z7_portrait_page_message(message,page,orientation); }
uint32_t z7_portrait_footer_box_probe(const struct z7_portrait_box *stock,uint32_t command,struct z7_portrait_box *out)
{ return z7_portrait_footer_box(stock,command,out); }
uint32_t z7_main(const struct z7_module_api *api)
{ return !api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET || api->size<12; }
