/* SPDX-License-Identifier: MIT. Caller-admitted portrait controls diagnostic. */
#include "module.h"
#include "../plugins/portrait_navigation.h"
uint32_t z7_portrait_input_point_probe(int16_t *p,uint32_t page,uint32_t orientation)
{ return z7_portrait_input_point(p,page,orientation); }
uint32_t z7_portrait_input_event_probe(const uint32_t *event,uint32_t *local,uint32_t page,uint32_t orientation)
{ return z7_portrait_input_event(event,local,page,orientation); }
uint32_t z7_portrait_input_target_probe(uint32_t current,uint32_t direction,uint32_t orientation,uint32_t disabled)
{ return z7_portrait_input_target(current,direction,orientation,disabled); }
uint32_t z7_portrait_input_key_probe(uint32_t key,uint32_t orientation)
{ return z7_portrait_input_key(key,orientation); }
uint32_t z7_portrait_navigation_probe(uint32_t direction,uint32_t page,uint32_t orientation)
{ return z7_portrait_navigation(direction,page,orientation); }
uint32_t z7_main(const struct z7_module_api *api)
{ return !api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET || api->size<12; }
