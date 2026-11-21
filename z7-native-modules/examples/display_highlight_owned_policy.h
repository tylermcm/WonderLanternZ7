/* SPDX-License-Identifier: MIT. Serialized DisplayService parameter ownership.
 * Worker submits/reaps only. Consumer callbacks alone write the lease. Source
 * flags remain native; immediate pending-frame suppression is still required.
 */
#include "../plugins/highlight_lease.h"
enum highlight_owned_operation { HO_NONE, HO_APPLY, HO_RESTORE, HO_DISABLE };
struct z7_highlight_lease z7_highlight_lease;
volatile uint32_t z7_highlight_owned_queued, z7_highlight_owned_applied;
volatile uint32_t z7_highlight_owned_restored, z7_highlight_owned_disabled;
volatile uint32_t z7_highlight_owned_cancelled, z7_highlight_owned_parked;
static struct {
    uint32_t operation, native_generation, lease_serial;
    struct z7_highlight_context context;
} highlight_owned_metadata;
static uint32_t highlight_owned_transaction;
static struct z7_highlight_lease_record highlight_owned_next;

static uint32_t highlight_identity(const struct z7_highlight_context *a,
                                  const struct z7_highlight_context *b)
{
    return a->mode == b->mode && a->output_kind == b->output_kind &&
        a->selector == b->selector && a->state == b->state && a->source == b->source;
}
static uint32_t highlight_parameters_match(uint32_t state, const uint32_t *parameters)
{
    for (uint32_t i = 0; i < 25; ++i) if (W(state + 0x28 + i * 4) != parameters[i]) return 0;
    return 1;
}
#ifdef Z7_HIGHLIGHT_CLEANUP_PROBE
#include "display_highlight_cleanup_policy.h"
#endif
#ifdef Z7_HIGHLIGHT_FRAME_PROBE
volatile uint32_t z7_highlight_frame_enabled, z7_highlight_frame_inhibited;
static uint32_t highlight_frame_permission(const void *frame, uint32_t native_permission)
{
    (void)frame; (void)native_permission;
    struct z7_highlight_lease_snapshot lease;
    struct z7_highlight_snapshot wanted;
    uint32_t state = W(0xa180a588u);
    uint32_t generation = __atomic_load_n(&z7_highlight_native_parameter_generation, __ATOMIC_ACQUIRE);
    if (!ram(state, 0x22c)) return 0;
    /* An interrupted/exhausted publication cannot prove that native parameters
     * are free of an earlier owned application. Inhibit until readable. */
    if (!z7_highlight_lease_read(&z7_highlight_lease, &lease)) return 2;
    if (!lease.record.valid || lease.record.context.state != state ||
        lease.record.native_generation != generation ||
        !highlight_parameters_match(state, lease.record.parameters)) return 0;
#ifdef Z7_HIGHLIGHT_CLEANUP_PROBE
    uint32_t note = highlight_frame_native_note(frame, native_permission, &lease.record);
    if (note != 1) {
        z7_highlight_owned_parked = 1; return note == 2 ? 0 : 2;
    }
#endif
    /* Inhibit stale owned parameters even when native permission was1. Once
     * restoration/new native traffic relinquishes the lease, delegate native. */
    uint32_t enabled = !z7_highlight_owned_parked && !lease.record.disabled &&
        highlight_current(&wanted) && wanted.epoch == lease.record.epoch &&
        highlight_identity(&wanted.view.context, &lease.record.context) &&
        W(0xa1f18facu) == lease.record.palette &&
        generation == __atomic_load_n(&z7_highlight_native_parameter_generation, __ATOMIC_ACQUIRE);
    if (enabled) ++z7_highlight_frame_enabled; else ++z7_highlight_frame_inhibited;
    return enabled ? 1 : 2;
}
#endif
static void highlight_record_copy(struct z7_highlight_lease_record *to,
                                 const struct z7_highlight_lease_record *from)
{
    for (uint32_t i = 0; i < sizeof(*to) / 4; ++i)
        ((volatile uint32_t *)to)[i] = ((const uint32_t *)from)[i];
}
static void highlight_baseline(uint32_t *to, const volatile uint32_t *from)
{
    uint32_t enabled = from[0];
    for (uint32_t i = 0; i < 25; ++i) to[i] = enabled ? from[i] : 0;
    /* Disabled native conversion defines only word0. Normalize the unused
     * remainder; never interpret undefined native disabled scratch fields. */
}
static void highlight_native_lease_invalidate(void)
{
    struct z7_highlight_lease_snapshot old;
    if (!z7_highlight_lease_read(&z7_highlight_lease, &old)) {
        z7_highlight_owned_parked = 1; return;
    }
    old.record.valid = old.record.disabled = 0;
    z7_highlight_owned_parked = !z7_highlight_lease_publish(&z7_highlight_lease, &old.record);
}
static uint32_t highlight_native_lease_capture(const struct z7_highlight_snapshot *snapshot,
    uint32_t generation, uint32_t palette, const volatile uint32_t *native, const uint32_t *converted)
{
    struct z7_highlight_lease_record record;
    record.valid = 1; record.native_generation = generation; record.epoch = snapshot->epoch;
    record.palette = palette; record.disabled = 0; record.context = snapshot->view.context;
    highlight_baseline(record.baseline, native);
    for (uint32_t i = 0; i < 25; ++i) record.parameters[i] = converted[i];
    uint32_t ok = z7_highlight_lease_publish(&z7_highlight_lease, &record);
    z7_highlight_owned_parked = !ok;
    return ok;
}
static void highlight_owned_request_make(struct highlight_native_request *request)
{
    for (uint32_t i = 0; i < sizeof(*request); ++i) ((volatile uint8_t *)request)[i] = 0;
    request->enabled = 1;
    for (uint32_t i = 0; i < 2; ++i) {
        request->groups[i * 4] = 255; request->groups[i * 4 + 1] = 248;
        request->groups[i * 4 + 2] = 15; request->groups[i * 4 + 3] = 5;
    }
    request->horizontal = request->vertical = 4;
}
static uint32_t highlight_owned_cancel(void)
{
    z7_highlight_request_cancel_claim(&z7_highlight_owned_request);
    return 2;
}
static uint32_t highlight_owned_before(void *packet)
{
    struct z7_highlight_snapshot publication, wanted;
    struct z7_highlight_context context;
    struct z7_highlight_lease_snapshot lease;
    highlight_owned_transaction = HO_NONE;
    uint32_t epoch = z7_highlight_snapshot(&z7_highlight_publication, &publication) ? publication.epoch : 0;
    uint32_t decision = z7_highlight_request_begin(&z7_highlight_owned_request, packet, epoch);
    if (decision != 1) return decision;
    uint32_t generation = __atomic_load_n(&z7_highlight_native_parameter_generation, __ATOMIC_ACQUIRE);
    if (z7_highlight_owned_parked || generation == UINT32_MAX || generation != highlight_owned_metadata.native_generation ||
        !z7_highlight_context_read(&context) || context.ready != 1 || (context.service != 3 && context.service != 4) ||
        !highlight_identity(&context, &highlight_owned_metadata.context) ||
        !z7_highlight_lease_read(&z7_highlight_lease, &lease)) return highlight_owned_cancel();
    uint32_t current = highlight_current(&wanted);
    uint32_t owned = lease.record.valid && lease.record.native_generation == generation &&
        lease.record.context.state == context.state && highlight_parameters_match(context.state, lease.record.parameters);
    uint32_t same = owned && highlight_identity(&lease.record.context, &context);
    uint32_t operation = highlight_owned_metadata.operation;
    if (operation == HO_APPLY) {
        uint32_t palette = W(0xa1f18facu);
        if (!current || wanted.epoch != epoch || !ram(palette, 1024) ||
            (owned && !same) || W(context.state + 0x28) > 1) return highlight_owned_cancel();
        if (same && !lease.record.disabled && lease.record.epoch == epoch && lease.record.palette == palette)
            return highlight_owned_cancel(); /* Native update already settled it. */
        struct highlight_native_request request;
        highlight_owned_request_make(&request);
        if (!z7_highlight_request_convert_deferred(&z7_highlight_owned_request, &request, epoch) ||
            !highlight_current(&publication) || publication.epoch != epoch || W(0xa1f18facu) != palette ||
            generation != __atomic_load_n(&z7_highlight_native_parameter_generation, __ATOMIC_ACQUIRE)) return highlight_owned_cancel();
        highlight_owned_next.valid = 1; highlight_owned_next.native_generation = generation;
        highlight_owned_next.epoch = epoch; highlight_owned_next.palette = palette;
        highlight_owned_next.disabled = 0; highlight_owned_next.context = context;
        if (same) for (uint32_t i = 0; i < 25; ++i) highlight_owned_next.baseline[i] = lease.record.baseline[i];
        else highlight_baseline(highlight_owned_next.baseline, (const volatile uint32_t *)(uintptr_t)(context.state + 0x28));
        for (uint32_t i = 0; i < 25; ++i) highlight_owned_next.parameters[i] = z7_highlight_owned_request.payload[i];
    } else {
        if (!owned || lease.serial != highlight_owned_metadata.lease_serial ||
            (operation != HO_RESTORE && operation != HO_DISABLE)) return highlight_owned_cancel();
        if ((operation == HO_RESTORE && (!same || current)) ||
            (operation == HO_DISABLE && (lease.record.disabled || (current && same)))) return highlight_owned_cancel();
        highlight_record_copy(&highlight_owned_next, &lease.record);
        for (uint32_t i = 0; i < 25; ++i)
            z7_highlight_owned_request.payload[i] = operation == HO_RESTORE ? lease.record.baseline[i] : lease.record.parameters[i];
        if (operation == HO_DISABLE) z7_highlight_owned_request.payload[0] = 0;
        for (uint32_t i = 0; i < 25; ++i) highlight_owned_next.parameters[i] = z7_highlight_owned_request.payload[i];
        highlight_owned_next.disabled = operation == HO_DISABLE;
        if (operation == HO_RESTORE) highlight_owned_next.valid = 0;
    }
#ifdef Z7_HIGHLIGHT_CLEANUP_PROBE
    if (!highlight_cleanup_prepare(operation, &context)) {
        z7_highlight_owned_parked = 1; return highlight_owned_cancel();
    }
#endif
    highlight_owned_transaction = operation;
    return 1;
}
static void highlight_owned_after(uint32_t decision)
{
    uint32_t operation = highlight_owned_transaction;
    if (decision == 1 && z7_highlight_owned_request.payload[25] == 1 && operation) {
        struct z7_highlight_context context;
        if (highlight_owned_next.native_generation != __atomic_load_n(&z7_highlight_native_parameter_generation, __ATOMIC_ACQUIRE) ||
            !z7_highlight_context_read(&context) || context.state != highlight_owned_next.context.state ||
            !highlight_parameters_match(context.state, highlight_owned_next.parameters) ||
#ifdef Z7_HIGHLIGHT_CLEANUP_PROBE
            !highlight_cleanup_finish(&highlight_owned_next) ||
#endif
            !z7_highlight_lease_publish(&z7_highlight_lease, &highlight_owned_next)) z7_highlight_owned_parked = 1;
        else if (operation == HO_APPLY) ++z7_highlight_owned_applied;
        else if (operation == HO_RESTORE) ++z7_highlight_owned_restored;
        else ++z7_highlight_owned_disabled;
    } else ++z7_highlight_owned_cancelled;
    highlight_owned_transaction = HO_NONE;
    /* LAST request access/publication: worker may reap/reuse immediately. */
    z7_highlight_request_end(&z7_highlight_owned_request);
}
static void highlight_owned_worker(void)
{
    (void)z7_highlight_request_reap(&z7_highlight_owned_request);
    if (z7_highlight_owned_parked || __atomic_load_n(&z7_highlight_owned_request.state, __ATOMIC_ACQUIRE) != Z7_HR_IDLE) return;
    struct z7_highlight_snapshot publication, wanted;
    struct z7_highlight_context context;
    struct z7_highlight_lease_snapshot lease;
    uint32_t generation = __atomic_load_n(&z7_highlight_native_parameter_generation, __ATOMIC_ACQUIRE);
    if (generation == UINT32_MAX || !z7_highlight_snapshot(&z7_highlight_publication, &publication) ||
        !z7_highlight_context_read(&context) || context.ready != 1 || (context.service != 3 && context.service != 4) ||
        !z7_highlight_lease_read(&z7_highlight_lease, &lease)) return;
    uint32_t current = highlight_current(&wanted);
    uint32_t owned = lease.record.valid && lease.record.native_generation == generation &&
        lease.record.context.state == context.state && highlight_parameters_match(context.state, lease.record.parameters);
    uint32_t same = owned && highlight_identity(&lease.record.context, &context);
    uint32_t operation = HO_NONE;
    if (owned && !same) { if (!lease.record.disabled) operation = HO_DISABLE; }
    else if (current) {
        if (!same || lease.record.disabled || lease.record.epoch != wanted.epoch || lease.record.palette != W(0xa1f18facu)) operation = HO_APPLY;
    } else if (same) operation = HO_RESTORE;
    if (!operation) return;
    highlight_owned_metadata.operation = operation;
    highlight_owned_metadata.native_generation = generation;
    highlight_owned_metadata.lease_serial = lease.serial;
    highlight_owned_metadata.context = context;
    /* Metadata precedes the helper's release publication and kernel send. */
    if (z7_highlight_request_submit_deferred(&z7_highlight_owned_request, context.selector == 0 ? 1 : 4, publication.epoch))
        ++z7_highlight_owned_queued;
}
