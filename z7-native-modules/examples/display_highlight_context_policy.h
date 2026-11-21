/* SPDX-License-Identifier: MIT. Full-profile epoch and optional parameter wiring.
 * Preserves current LCD DISP eligibility. Owned builds add parameter restoration;
 * source-frame permissions and visible warning rendering remain native.
 */
#include "../plugins/highlight_epoch.h"
struct z7_highlight_publication z7_highlight_publication;
volatile uint32_t z7_highlight_gui_epoch, z7_highlight_source_epoch;
volatile uint32_t z7_highlight_worker_epoch, z7_highlight_worker_eligible;
volatile uint32_t z7_highlight_source_observations, z7_highlight_publish_errors;
#ifdef Z7_HIGHLIGHT_OWNED_PROBE
#include "../plugins/highlight_request.h"
static struct z7_highlight_request z7_highlight_owned_request;
#define highlight_descriptor z7_highlight_owned_request.descriptor
static uint32_t highlight_owned_before(void *packet);
static void highlight_owned_after(uint32_t decision);
static void highlight_owned_worker(void);
static void highlight_native_lease_invalidate(void);
#ifdef Z7_HIGHLIGHT_CLEANUP_PROBE
static uint32_t highlight_cleanup_native_release(void);
extern volatile uint32_t z7_highlight_owned_parked;
#endif
static uint32_t highlight_native_lease_capture(const struct z7_highlight_snapshot *,
    uint32_t generation, uint32_t palette, const volatile uint32_t *, const uint32_t *);
#else
static uint32_t highlight_descriptor[7];
#endif
static uint32_t highlight_ui_ready(void)
{
    return z7_base_active && !base_blocked && !base_releasing &&
        !information_components_blocked() && !W(0xa2c41008u) &&
        !W(0xa18b4de8u) && base_gui_memory_context();
}
static void highlight_gui_publish(void)
{
    struct z7_highlight_view view;
    for (uint32_t i = 0; i < sizeof(view) / 4; ++i) ((volatile uint32_t *)&view)[i] = 0;
    struct z7_display_settings settings;
    uint32_t valid = persistence_snapshot(&settings, &view.settings_revision);
    if (!valid) view.settings_revision = __atomic_load_n(&z7_settings_revision, __ATOMIC_ACQUIRE);
    view.preset = z7_readout_preset;
    view.preset_generation = z7_preset_cycles;
    uint32_t context = z7_highlight_context_read(&view.context);
    view.wanted = valid && view.preset < 4 && (settings.flags & Z7_SETTINGS_CUSTOM) &&
        (settings.enabled_pages & (1u << view.preset)) &&
        (settings.components[view.preset] & Z7_COMPONENT_HIGHLIGHTS);
    view.wanted = !!view.wanted;
    view.eligible = context && view.context.mode == 0 && view.context.selector == 0 &&
        view.context.output_kind == 1 && view.context.ready == 1 &&
        (view.context.service == 3 || view.context.service == 4) && highlight_ui_ready();
    if (!z7_highlight_publish(&z7_highlight_publication, &view)) ++z7_highlight_publish_errors;
    struct z7_highlight_snapshot snapshot;
    z7_highlight_gui_epoch = z7_highlight_snapshot(&z7_highlight_publication, &snapshot) ? snapshot.epoch : 0;
}
static uint32_t highlight_current(struct z7_highlight_snapshot *snapshot)
{
    struct z7_highlight_context live;
    if (!z7_highlight_snapshot(&z7_highlight_publication, snapshot) ||
#ifdef Z7_HIGHLIGHT_NATIVE_WARNING_PROBE
        !Z7_HIGHLIGHT_COORDINATION_AVAILABLE() ||
#endif
        !snapshot->view.wanted || !snapshot->view.eligible || !highlight_ui_ready() ||
        snapshot->view.settings_revision != __atomic_load_n(&z7_settings_revision, __ATOMIC_ACQUIRE) ||
        snapshot->view.preset != z7_readout_preset || snapshot->view.preset_generation != z7_preset_cycles ||
        !z7_highlight_context_read(&live)) return 0;
    const uint32_t *a = (const uint32_t *)&snapshot->view.context;
    const uint32_t *b = (const uint32_t *)&live;
    for (uint32_t i = 0; i < sizeof(live) / 4; ++i) if (a[i] != b[i]) return 0;
    __atomic_thread_fence(__ATOMIC_ACQUIRE);
    return snapshot->view.settings_revision == __atomic_load_n(&z7_settings_revision, __ATOMIC_RELAXED) &&
        snapshot->view.preset == z7_readout_preset && highlight_ui_ready() &&
        snapshot->view.preset_generation == z7_preset_cycles &&
        snapshot->epoch == __atomic_load_n(&z7_highlight_publication.epoch, __ATOMIC_ACQUIRE) &&
        !(__atomic_load_n(&z7_highlight_publication.sequence, __ATOMIC_ACQUIRE) & 1) &&
        !__atomic_load_n(&z7_highlight_publication.halted, __ATOMIC_ACQUIRE);
}
static uint32_t highlight_source_before(uint32_t output, void *frame)
{
    (void)frame;
    struct z7_highlight_snapshot snapshot;
    ++z7_highlight_source_observations;
    return output == 0 && highlight_current(&snapshot) ? snapshot.epoch : 0;
}
static void highlight_source_after(uint32_t output, void *frame, uint32_t epoch)
{
    (void)output; (void)frame;
    z7_highlight_source_epoch = epoch;
    /* Observation token only: caller/deferred frame flags remain native until
     * matching owned parameter acknowledgement/restoration is integrated. */
}
static uint32_t highlight_consumer_before(void *packet)
{
#ifdef Z7_HIGHLIGHT_OWNED_PROBE
    return highlight_owned_before(packet);
#else
    (void)packet;
    return 3; /* No requests submitted by this context-integration milestone. */
#endif
}
static void highlight_consumer_after(void *packet, uint32_t decision)
{
    (void)packet;
#ifdef Z7_HIGHLIGHT_OWNED_PROBE
    highlight_owned_after(decision);
#else
    (void)decision;
#endif
}
static const struct z7_highlight_hooks highlight_hooks = { Z7_MODULE_ABI,
    sizeof(highlight_hooks), highlight_descriptor, highlight_source_before,
    highlight_source_after, highlight_consumer_before, highlight_consumer_after };
static void highlight_combined_worker(void)
{
    struct z7_highlight_snapshot snapshot;
    uint32_t eligible = highlight_current(&snapshot);
    z7_highlight_worker_epoch = eligible ? snapshot.epoch : 0;
    z7_highlight_worker_eligible = eligible;
#ifdef Z7_HIGHLIGHT_OWNED_PROBE
    highlight_owned_worker();
#endif
    persistence_worker();
}
#ifdef Z7_HIGHLIGHT_PARAMETERS_PROBE
#include <stddef.h>
/* Initial pattern1/threshold248 match the independently audited native request.
 * Style/threshold menu configuration remains open. Native request/descriptor/ack stay
 * with their original caller; conversion finishes BEFORE original dispatch. */
volatile uint32_t z7_highlight_parameter_epoch, z7_highlight_parameter_count;
volatile uint32_t z7_highlight_parameter_input_enabled;
volatile uint32_t z7_highlight_native_parameter_generation;
struct highlight_native_request {
    uint32_t enabled;
    uint8_t reserved[2];
    uint16_t groups[8], padding;
    uint32_t horizontal, vertical;
    uint8_t patterns[2], tail[2];
};
_Static_assert(sizeof(struct highlight_native_request) == 36 &&
    offsetof(struct highlight_native_request, groups) == 6 &&
    offsetof(struct highlight_native_request, horizontal) == 24 &&
    offsetof(struct highlight_native_request, patterns) == 32, "Native request layout");
static void highlight_native_parameters(uint32_t command, void *payload100)
{
    struct z7_highlight_snapshot snapshot, final;
#ifdef Z7_HIGHLIGHT_OWNED_PROBE
#ifdef Z7_HIGHLIGHT_CLEANUP_PROBE
    uint32_t cleanup_ok = highlight_cleanup_native_release();
#endif
    highlight_native_lease_invalidate();
#endif
    uint32_t generation = __atomic_load_n(&z7_highlight_native_parameter_generation, __ATOMIC_RELAXED);
    z7_highlight_parameter_epoch = 0;
    if (generation == UINT32_MAX) return; /* Never recycle native-update identity. */
    __atomic_store_n(&z7_highlight_native_parameter_generation, generation + 1, __ATOMIC_RELEASE);
#ifdef Z7_HIGHLIGHT_OWNED_PROBE
    if (generation + 1 == UINT32_MAX) return;
#endif
#ifdef Z7_HIGHLIGHT_CLEANUP_PROBE
    if (!cleanup_ok) { z7_highlight_owned_parked = 1; return; }
#endif
    if (!payload100) return; /* Ineligible native update, no writable data exposed. */
    if (command != 0x42060007u || !highlight_current(&snapshot)) return;
    uint32_t palette = W(0xa1f18facu);
    if (!ram(palette, 256 * 4)) return;
    struct highlight_native_request request;
    uint32_t converted[25];
    for (uint32_t i = 0; i < sizeof(request); ++i) ((volatile uint8_t *)&request)[i] = 0;
    for (uint32_t i = 0; i < 25; ++i) ((volatile uint32_t *)converted)[i] = 0;
    request.enabled = 1;
    for (uint32_t i = 0; i < 2; ++i) {
        request.groups[i * 4] = 255;
        request.groups[i * 4 + 1] = 248;
        request.groups[i * 4 + 2] = 15;
        request.groups[i * 4 + 3] = 5;
    }
    request.horizontal = request.vertical = 4;
    F(0x1034fe23u, void, void *, const void *, uint32_t)(converted, &request, 1);
    if (!highlight_current(&final) || final.epoch != snapshot.epoch || W(0xa1f18facu) != palette) return;
    volatile uint32_t *data = payload100;
#ifdef Z7_HIGHLIGHT_OWNED_PROBE
    if (!highlight_native_lease_capture(&snapshot, generation + 1, palette, data, converted)) return;
#endif
    z7_highlight_parameter_input_enabled = data[0];
    for (uint32_t i = 1; i < 25; ++i) data[i] = converted[i];
    __atomic_thread_fence(__ATOMIC_RELEASE);
    data[0] = converted[0];
    z7_highlight_parameter_epoch = snapshot.epoch; /* Prepared, not yet copied/acknowledged. */
    ++z7_highlight_parameter_count;
}
#endif
#ifdef Z7_HIGHLIGHT_OWNED_PROBE
#include "display_highlight_owned_policy.h"
#endif
