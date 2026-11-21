/* SPDX-License-Identifier: MIT. Diagnostic only; no native hook registration. */
#include "module.h"
#include "../host/highlight_lane.h"
struct z7_highlight_lane z7_lane;
uint32_t z7_lane_enter(uint32_t role, uint32_t owner)
{ return z7_highlight_lane_enter(&z7_lane, role, owner); }
uint32_t z7_lane_owns(uint32_t token, uint32_t owner)
{ return z7_highlight_lane_owns(&z7_lane, token, owner); }
uint32_t z7_lane_leave(uint32_t token, uint32_t owner)
{ return z7_highlight_lane_leave(&z7_lane, token, owner); }
uint32_t z7_main(const struct z7_module_api *api) { (void)api; return 0; }
