/* SPDX-License-Identifier: MIT. Full-profile epoch wiring; no warning writes.
 * Preserves current LCD DISP eligibility. EVF/movie contexts remain delegated.
 * Packet conversion/restoration and visible warnings are subsequent integration.
 */
#include "../plugins/highlight_epoch.h"
struct z7_highlight_publication z7_highlight_publication;
volatile uint32_t z7_highlight_gui_epoch, z7_highlight_source_epoch;
volatile uint32_t z7_highlight_worker_epoch, z7_highlight_worker_eligible;
volatile uint32_t z7_highlight_source_observations, z7_highlight_publish_errors;
static uint32_t highlight_descriptor[7];
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
    (void)packet;
    return 3; /* No requests submitted by this context-integration milestone. */
}
static void highlight_consumer_after(void *packet, uint32_t decision)
{ (void)packet; (void)decision; }
static const struct z7_highlight_hooks highlight_hooks = { Z7_MODULE_ABI,
    sizeof(highlight_hooks), highlight_descriptor, highlight_source_before,
    highlight_source_after, highlight_consumer_before, highlight_consumer_after };
static void highlight_combined_worker(void)
{
    struct z7_highlight_snapshot snapshot;
    uint32_t eligible = highlight_current(&snapshot);
    z7_highlight_worker_epoch = eligible ? snapshot.epoch : 0;
    z7_highlight_worker_eligible = eligible;
    persistence_worker();
}
