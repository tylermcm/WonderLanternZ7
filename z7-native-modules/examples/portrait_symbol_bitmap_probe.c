/* SPDX-License-Identifier: MIT. Native symbol bitmap decode diagnostic. */
#include "module.h"
#include "../plugins/portrait_symbol_bitmap.h"
uint32_t z7_portrait_symbol_bitmap_probe(uint32_t asset,uint32_t length,
    struct z7_portrait_symbol_bitmap *info)
{ return z7_portrait_symbol_bitmap_decode(asset,length,info); }
uint32_t z7_main(const struct z7_module_api *api)
{ return !api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET || api->size<12; }
