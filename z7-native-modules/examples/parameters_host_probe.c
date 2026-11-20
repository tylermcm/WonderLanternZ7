/* SPDX-License-Identifier: MIT. Native parameter API registration/filter fixture. */
#include "parameters.h"
volatile uint32_t z7_ph_mask, z7_ph_calls, z7_ph_command, z7_ph_recurse, z7_ph_packet;
volatile uint32_t z7_ph_notices;
static uint32_t descriptor[7];
static const struct z7_module_parameters_api *saved;
static uint32_t before_source(uint32_t output, void *frame) { (void)output; (void)frame; return 0; }
static void after_source(uint32_t output, void *frame, uint32_t token) { (void)output; (void)frame; (void)token; }
static uint32_t before_consumer(void *packet) { (void)packet; return 3; }
static void after_consumer(void *packet, uint32_t decision) { (void)packet; (void)decision; }
static const struct z7_highlight_hooks hooks = { Z7_MODULE_ABI, sizeof(hooks), descriptor,
    before_source, after_source, before_consumer, after_consumer };
static void parameter(uint32_t command, void *payload)
{
    ++z7_ph_calls;
    z7_ph_command = command;
    if (!payload) { ++z7_ph_notices; return; }
    if (z7_ph_recurse) {
        z7_ph_recurse = 0;
        ((uint32_t (*)(void *))(uintptr_t)0x10239841u)((void *)(uintptr_t)z7_ph_packet);
    }
    *(volatile uint32_t *)payload = 1;
}
uint32_t z7_ph_late(void) { return saved->register_parameters(parameter); }
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi != Z7_MODULE_ABI || api->target != Z7_MODULE_TARGET || api->size < sizeof(*saved)) return 1;
    saved = (const struct z7_module_parameters_api *)api;
    if (!saved->register_parameters || !saved->highlight.register_highlight) return 1;
    if (!saved->register_parameters(parameter)) z7_ph_mask |= 1;
    if (!saved->highlight.register_highlight(&hooks)) return 1;
    if (!saved->register_parameters(0)) z7_ph_mask |= 2;
    if (!saved->register_parameters((void *)((uintptr_t)parameter & ~(uintptr_t)1))) z7_ph_mask |= 4;
    if (!saved->register_parameters((void *)((uintptr_t)&z7_ph_calls | 1))) z7_ph_mask |= 8;
    if (!saved->register_parameters((void *)(uintptr_t)0x102fd647u)) z7_ph_mask |= 16;
    if (saved->register_parameters(parameter)) z7_ph_mask |= 32;
    if (!saved->register_parameters(parameter)) z7_ph_mask |= 64;
#ifdef Z7_PARAMETER_INIT_FAIL
    return 1;
#else
    return z7_ph_mask == 127 ? 0 : 1;
#endif
}
