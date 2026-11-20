/* SPDX-License-Identifier: MIT. Explicit diagnostic policy, not photo eligibility. */
#include "highlight.h"
#include "../plugins/highlight_request.h"
struct z7_highlight_request z7_hr;
volatile uint32_t z7_hl_api_bytes, z7_hl_registration_mask, z7_hl_epoch = 17;
volatile uint32_t z7_hl_source_enable = 1, z7_hl_source_calls, z7_hl_source_after;
volatile uint32_t z7_hl_consumer_calls, z7_hl_consumer_after, z7_hl_token;
volatile uint32_t z7_hl_recurse_source, z7_hl_recurse_consumer;
volatile uint32_t z7_hl_nested_source, z7_hl_nested_consumer;
volatile uint32_t z7_hl_invalid_callback_fields, z7_hl_invalid_ranges;
volatile uint32_t z7_hl_cycle_after, z7_hl_next_request, z7_hl_reaped_after;
volatile uint32_t z7_hl_submitted_after, z7_hl_consumed_after;
extern const uint8_t __memory_end[] __attribute__((visibility("hidden")));
static const struct z7_module_highlight_api *saved;
static uint32_t source(uint32_t output, void *frame)
{
    ++z7_hl_source_calls;
    if (z7_hl_recurse_source) {
        z7_hl_recurse_source = 0;
        z7_hl_nested_source = ((uint32_t (*)(uint32_t, void *))(uintptr_t)0x1034866fu)(3, frame);
    }
    uint32_t *permission = (uint32_t *)((uint8_t *)frame + 0x34);
    if (z7_hl_source_enable && (output == 0 || output == 2) && *permission == 0) {
        *permission = 1;
        return 0xabc12345u;
    }
    return 0;
}
static void source_after(uint32_t output, void *frame, uint32_t token)
{
    (void)output;
    ++z7_hl_source_after;
    z7_hl_token = token;
    uint32_t *permission = (uint32_t *)((uint8_t *)frame + 0x34);
    if (token == 0xabc12345u && *permission == 1) *permission = 0;
}
static uint32_t consumer(void *packet)
{
    ++z7_hl_consumer_calls;
    if (z7_hl_recurse_consumer) {
        z7_hl_recurse_consumer = 0;
        z7_hl_nested_consumer = ((uint32_t (*)(void *))(uintptr_t)0x10239841u)(packet);
    }
    return z7_highlight_request_begin(&z7_hr, packet, z7_hl_epoch);
}
static void consumer_after(void *packet, uint32_t decision)
{
    (void)packet; (void)decision;
    ++z7_hl_consumer_after;
    z7_highlight_request_end(&z7_hr);
    /* Diagnostic interleaving: model a worker reaping/submitting immediately
     * after retirement, before the previous host leave function returns.
     * Production submission remains worker-only, not a consumer callback. */
    if (z7_hl_cycle_after) {
        z7_hl_cycle_after = 0;
        z7_hl_reaped_after = z7_highlight_request_reap(&z7_hr);
        z7_hl_submitted_after = z7_highlight_request_submit(&z7_hr,
            (const void *)(uintptr_t)z7_hl_next_request, 1, z7_hl_epoch);
        z7_hl_consumed_after = ((uint32_t (*)(void *))(uintptr_t)0x10239841u)(z7_hr.descriptor);
    }
}
static struct z7_highlight_hooks hooks = { Z7_MODULE_ABI, sizeof(hooks),
    z7_hr.descriptor, source, source_after, consumer, consumer_after };
uint32_t z7_hl_late(void) { return saved->register_highlight(&hooks); }
uint32_t z7_hl_submit(const void *gui, uint32_t output, uint32_t epoch)
{ return z7_highlight_request_submit(&z7_hr, gui, output, epoch); }
uint32_t z7_hl_reap(void) { return z7_highlight_request_reap(&z7_hr); }
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi != Z7_MODULE_ABI || api->target != Z7_MODULE_TARGET ||
        api->size < sizeof(*saved)) return 1;
    saved = (const struct z7_module_highlight_api *)api;
    z7_hl_api_bytes = api->size;
    if (!saved->register_highlight) return 1;
    if (!saved->register_highlight(0)) z7_hl_registration_mask |= 1;
    ++hooks.abi;
    if (!saved->register_highlight(&hooks)) z7_hl_registration_mask |= 2;
    --hooks.abi; --hooks.size;
    if (!saved->register_highlight(&hooks)) z7_hl_registration_mask |= 4;
    ++hooks.size;
    if (!saved->register_highlight((const void *)((uintptr_t)&hooks + 1))) z7_hl_registration_mask |= 8;
    hooks.descriptor = (void *)(uintptr_t)0x50001000u;
    if (!saved->register_highlight(&hooks)) z7_hl_registration_mask |= 16;
    hooks.descriptor = z7_hr.descriptor;
    hooks.before_source = 0;
    if (!saved->register_highlight(&hooks)) z7_hl_registration_mask |= 32;
    hooks.before_source = (void *)((uintptr_t)source & ~(uintptr_t)1);
    if (!saved->register_highlight(&hooks)) z7_hl_registration_mask |= 64;
    hooks.before_source = (void *)((uintptr_t)&z7_hr | 1);
    if (!saved->register_highlight(&hooks)) z7_hl_registration_mask |= 128;
    hooks.before_source = (void *)(uintptr_t)0x102fd647u;
    if (!saved->register_highlight(&hooks)) z7_hl_registration_mask |= 256;
    hooks.before_source = source;
    uint32_t *fields = (uint32_t *)&hooks.before_source;
    for (uint32_t i = 0; i < 4; ++i) {
        uint32_t original = fields[i];
        fields[i] = 0;
        if (!saved->register_highlight(&hooks)) ++z7_hl_invalid_callback_fields;
        fields[i] = original;
    }
    hooks.descriptor = (uint8_t *)z7_hr.descriptor + 1;
    if (!saved->register_highlight(&hooks)) ++z7_hl_invalid_ranges;
    hooks.descriptor = (void *)(__memory_end - 24);
    if (!saved->register_highlight(&hooks)) ++z7_hl_invalid_ranges;
    hooks.descriptor = z7_hr.descriptor;
    if (!saved->register_highlight((const void *)(__memory_end - 4))) ++z7_hl_invalid_ranges;
    if (saved->register_highlight(&hooks)) z7_hl_registration_mask |= 512;
    if (!saved->register_highlight(&hooks)) z7_hl_registration_mask |= 1024;
#ifdef Z7_HL_FAIL
    return 1;
#else
    return z7_hl_registration_mask == 2047 ? 0 : 1;
#endif
}
