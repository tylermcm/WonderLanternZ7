/* SPDX-License-Identifier: MIT. Original-Z7 i-menu classification diagnostic. */
#include "module.h"
#include "../plugins/portrait_page.h"
uint32_t z7_portrait_page_probe(void) { return z7_portrait_imenu_page(); }
uint32_t z7_main(const struct z7_module_api *api)
{ return !api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET || api->size<12; }
