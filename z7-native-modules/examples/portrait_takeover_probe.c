/* SPDX-License-Identifier: MIT. Original-Z7 native screen task diagnostic. */
#include "module.h"
#include "../plugins/portrait_takeover.h"
uint32_t z7_portrait_takeover_probe(void) { return z7_portrait_native_takeover(); }
uint32_t z7_main(const struct z7_module_api *api)
{ return !api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET || api->size<12; }
