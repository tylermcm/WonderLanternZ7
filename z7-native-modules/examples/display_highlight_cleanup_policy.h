/* SPDX-License-Identifier: MIT. Serialized native-consumer plane restoration.
 * Frame callback publishes original input, never a retained frame pointer.
 * Native engine allocation/context lifetime and writer serialization remain
 * preconditions. Register readback does not prove physical display application.
 */
struct highlight_frame_native_record {
    struct z7_highlight_context context;
    uint32_t engine, identity, bank, permission, format, valid;
};
struct {
    uint32_t sequence, serial, halted;
    struct highlight_frame_native_record record;
} z7_highlight_native_frame;
static struct {
    uint32_t ready, generation, permission, format;
    struct highlight_frame_native_record frame;
} highlight_cleanup_pending;
volatile uint32_t z7_highlight_cleanup_done, z7_highlight_cleanup_failed;
volatile uint32_t z7_highlight_cleanup_native_releases;

static uint32_t highlight_frame_native_read(struct highlight_frame_native_record *out)
{
    for (uint32_t attempt = 0; attempt < 3; ++attempt) {
        uint32_t sequence = __atomic_load_n(&z7_highlight_native_frame.sequence, __ATOMIC_ACQUIRE);
        if ((sequence & 1) || __atomic_load_n(&z7_highlight_native_frame.halted, __ATOMIC_ACQUIRE)) continue;
        uint32_t serial = __atomic_load_n(&z7_highlight_native_frame.serial, __ATOMIC_RELAXED);
        struct highlight_frame_native_record r;
        for (uint32_t i = 0; i < sizeof(r) / 4; ++i)
            ((uint32_t *)&r)[i] = __atomic_load_n((const uint32_t *)&z7_highlight_native_frame.record + i, __ATOMIC_RELAXED);
        __atomic_thread_fence(__ATOMIC_ACQUIRE);
        if (sequence != __atomic_load_n(&z7_highlight_native_frame.sequence, __ATOMIC_RELAXED) ||
            serial != __atomic_load_n(&z7_highlight_native_frame.serial, __ATOMIC_RELAXED) ||
            __atomic_load_n(&z7_highlight_native_frame.halted, __ATOMIC_ACQUIRE)) continue;
        for (uint32_t i = 0; i < sizeof(r) / 4; ++i) ((volatile uint32_t *)out)[i] = ((uint32_t *)&r)[i];
        return 1;
    }
    return 0;
}
static uint32_t highlight_frame_engine_matches(const struct highlight_frame_native_record *r)
{
    return W(0xa180a588u) == r->context.state && W(0xa180a578u) == r->engine && ram(r->engine, 8) &&
        (r->identity == 0x141 || r->identity == 0x142) && (r->bank == 0 || r->bank == 0x4000) &&
        W(r->engine) == r->identity && W(r->engine + 4) == r->bank;
}
static uint32_t highlight_cleanup_engine_admitted(void)
{
    uint32_t engine = W(0xa180a578u);
    return ram(engine, 8) && (W(engine) == 0x141 || W(engine) == 0x142) &&
        (W(engine + 4) == 0 || W(engine + 4) == 0x4000);
}
static uint32_t highlight_frame_native_publish(const struct highlight_frame_native_record *r)
{
    uint32_t sequence = __atomic_load_n(&z7_highlight_native_frame.sequence, __ATOMIC_RELAXED);
    if (__atomic_load_n(&z7_highlight_native_frame.halted, __ATOMIC_ACQUIRE) || (sequence & 1) ||
        !__atomic_compare_exchange_n(&z7_highlight_native_frame.sequence, &sequence, sequence + 1, 0,
            __ATOMIC_ACQ_REL, __ATOMIC_RELAXED)) return 0;
    uint32_t serial = __atomic_load_n(&z7_highlight_native_frame.serial, __ATOMIC_RELAXED);
    if (serial == UINT32_MAX) {
        __atomic_store_n(&z7_highlight_native_frame.halted, 1, __ATOMIC_RELEASE);
        __atomic_store_n(&z7_highlight_native_frame.sequence, sequence, __ATOMIC_RELEASE);
        return 0;
    }
    for (uint32_t i = 0; i < sizeof(*r) / 4; ++i)
        __atomic_store_n((uint32_t *)&z7_highlight_native_frame.record + i, ((const uint32_t *)r)[i], __ATOMIC_RELAXED);
    __atomic_store_n(&z7_highlight_native_frame.serial, serial + 1, __ATOMIC_RELAXED);
    __atomic_store_n(&z7_highlight_native_frame.sequence, sequence + 2, __ATOMIC_RELEASE);
    return 1;
}
static uint32_t highlight_frame_native_note(const void *frame, uint32_t native_permission,
                                          const struct z7_highlight_lease_record *lease)
{
    struct highlight_frame_native_record old, r;
    if (!highlight_frame_native_read(&old) || !z7_highlight_context_read(&r.context)) return 0;
    if (!highlight_identity(&r.context, &lease->context)) return 1; /* Keep original owned context. */
    r.engine = W(0xa180a578u);
    if (!ram(r.engine, 8)) return 2;
    r.identity = W(r.engine); r.bank = W(r.engine + 4);
    r.permission = native_permission; r.format = ((const volatile uint8_t *)frame)[5]; r.valid = 1;
    if (!highlight_frame_engine_matches(&r)) return 2;
    if (old.valid && old.context.state == r.context.state &&
        (old.engine != r.engine || old.identity != r.identity || old.bank != r.bank)) return 2;
    if (r.format == 4) return 1; /* Gate bypass: retain last meaningful frame. */
    if (r.format > 4) return 0;
    return highlight_frame_native_publish(&r);
}
static uint32_t highlight_cleanup_gate(const struct highlight_frame_native_record *frame,
                                       uint32_t permission, uint32_t format, uint32_t generation,
                                       const uint32_t *parameters)
{
    uint32_t state = frame->context.state;
    struct z7_highlight_context before, after;
    if (!z7_highlight_context_read(&before) || before.state != state || before.ready != 1 ||
        (before.service != 3 && before.service != 4) || format >= 4 || !highlight_frame_engine_matches(frame) ||
        generation != __atomic_load_n(&z7_highlight_native_parameter_generation, __ATOMIC_ACQUIRE) ||
        !highlight_parameters_match(state, parameters)) return 0;
    *(volatile uint32_t *)(uintptr_t)(state + 0x20) = permission;
    uint32_t result = F(0x1023b76fu, uint32_t, uint32_t)(format);
    uint32_t enabled = permission == 1 && parameters[0] == 1;
    uint32_t stable = result == 1 && highlight_frame_engine_matches(frame) &&
        z7_highlight_context_read(&after) && highlight_identity(&before, &after) &&
        before.ready == after.ready && before.service == after.service &&
        generation == __atomic_load_n(&z7_highlight_native_parameter_generation, __ATOMIC_ACQUIRE) &&
        highlight_parameters_match(state, parameters);
    if (!stable) return 0;
    /* Native active bookkeeping can be stale. For a qualified disable only,
     * use the original driver's bit-preserving disable if readback is still1. */
    if (!enabled && (W(0x20140000u + frame->bank + 0x430) & 1))
        F(0x10241a0fu, uint32_t, uint32_t, const void *, uint32_t)(frame->engine, 0, 0);
    return highlight_frame_engine_matches(frame) &&
        generation == __atomic_load_n(&z7_highlight_native_parameter_generation, __ATOMIC_ACQUIRE) &&
        highlight_parameters_match(state, parameters) && W(state + 0x1c) == enabled &&
        W(state + 0x24) == 0 && (W(0x20140000u + frame->bank + 0x430) & 1) == enabled;
}
static uint32_t highlight_cleanup_prepare(uint32_t operation, const struct z7_highlight_context *context)
{
    highlight_cleanup_pending.ready = 0;
    struct highlight_frame_native_record r;
    if (!highlight_cleanup_engine_admitted() || !highlight_frame_native_read(&r) ||
        (r.valid && !highlight_frame_engine_matches(&r))) return 0;
    if (operation == HO_APPLY) return 1;
    if (!r.valid) return 1; /* No owned primary frame was presented. */
    if (!highlight_frame_engine_matches(&r) || r.context.state != context->state ||
        (operation == HO_RESTORE && !highlight_identity(&r.context, context))) return 0;
    highlight_cleanup_pending.frame = r;
    highlight_cleanup_pending.generation = __atomic_load_n(&z7_highlight_native_parameter_generation, __ATOMIC_ACQUIRE);
    highlight_cleanup_pending.permission = operation == HO_DISABLE ? 0 :
        W(context->state + 0x20) > 1 ? W(context->state + 0x20) : r.permission;
    highlight_cleanup_pending.format = operation == HO_DISABLE ? 0 : r.format;
    highlight_cleanup_pending.ready = 1;
    return 1;
}
static uint32_t highlight_cleanup_finish(const struct z7_highlight_lease_record *next)
{
    if (!highlight_cleanup_pending.ready) return 1;
    highlight_cleanup_pending.ready = 0;
    if (!highlight_cleanup_gate(&highlight_cleanup_pending.frame, highlight_cleanup_pending.permission,
            highlight_cleanup_pending.format, highlight_cleanup_pending.generation, next->parameters)) {
        ++z7_highlight_cleanup_failed; return 0;
    }
    ++z7_highlight_cleanup_done;
    return 1;
}
static uint32_t highlight_cleanup_native_release(void)
{
    struct z7_highlight_lease_snapshot lease;
    struct highlight_frame_native_record frame;
    if (!highlight_cleanup_engine_admitted()) return 0;
    if (!z7_highlight_lease_read(&z7_highlight_lease, &lease)) return 0;
    if (!highlight_frame_native_read(&frame)) return 0;
#ifdef Z7_HIGHLIGHT_CACHED_PROBE
    if (frame.valid && highlight_frame_engine_matches(&frame)) {
        uint32_t permission = W(frame.context.state + 0x20);
        if (permission > 1) frame.permission = permission; /* Unfiltered native inhibit. */
    }
#endif
    if (lease.record.valid && frame.valid &&
        !highlight_cleanup_gate(&frame, 0, 0, lease.record.native_generation, lease.record.parameters)) {
        ++z7_highlight_cleanup_failed; return 0;
    }
    if (lease.record.valid && frame.valid) ++z7_highlight_cleanup_native_releases;
#ifdef Z7_HIGHLIGHT_CACHED_PROBE
    /* A parameter update does not erase the last original frame policy. A
     * subsequent NULL cached refresh may present the new owned parameters. */
    struct z7_highlight_context context;
    if (frame.valid && highlight_frame_engine_matches(&frame) && z7_highlight_context_read(&context) &&
        highlight_identity(&frame.context, &context)) return highlight_frame_native_publish(&frame);
#endif
    frame.valid = 0;
    return highlight_frame_native_publish(&frame);
}
