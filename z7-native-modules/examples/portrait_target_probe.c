/* SPDX-License-Identifier: MIT. Read-only original-Z7 target diagnostic. */
#include "module.h"
#include "../plugins/portrait_target.h"
uint32_t z7_portrait_target_probe(void) { return z7_portrait_lcd_target(); }
uint32_t z7_main(const struct z7_module_api *api)
{ return !api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET || api->size<12; }
