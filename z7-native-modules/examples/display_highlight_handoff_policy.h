/* SPDX-License-Identifier: MIT. Consumer-written per-output native baselines.
 * Cache snapshots are coherent copies, not atomic application/lifetime pins.
 * Producer/index/boot closure and physical output mapping remain host contracts.
 */
struct z7_highlight_lease z7_highlight_native_origins[2];
static uint32_t highlight_handoff_output(const struct z7_highlight_context *c)
{
    if (c->mode || c->selector > 1) return 0;
    return c->output_kind == c->selector + 1 ? (c->selector ? 4 : 1) : 0;
}
static uint32_t highlight_handoff_origin(const struct z7_highlight_context *c,
                                        struct z7_highlight_lease_snapshot *s)
{
    return c->selector < 2 && z7_highlight_lease_read(&z7_highlight_native_origins[c->selector], s) &&
        s->serial != UINT32_MAX;
}
static uint32_t highlight_handoff_raw_equal(const struct z7_native_cache_snapshot *a,
                                           const struct z7_native_cache_snapshot *b)
{
    if (a->bank != b->bank) return 0;
    for (uint32_t i = 0; i < 9; ++i) if (a->request[i] != b->request[i]) return 0;
    return 1;
}
static uint32_t highlight_handoff_available(const struct z7_highlight_context *c)
{
    uint32_t output = highlight_handoff_output(c);
    struct z7_native_cache_snapshot cache;
    struct z7_highlight_lease_snapshot origin;
    if (!output || !highlight_handoff_origin(c, &origin)) return 0;
    return highlight_cache_api->native_cache_snapshot(output, &cache) ||
        (origin.record.valid && !origin.record.cache_bound && highlight_identity(c, &origin.record.context));
}
static uint32_t highlight_handoff_source_current(const struct z7_highlight_lease_record *r)
{
    uint32_t output = highlight_handoff_output(&r->context);
    if (!output) return 0;
    if (r->cache_bound) return highlight_cache_api->native_cache_snapshot_valid(output, &r->cache);
    /* Exact foreign parameters remain authoritative until a tracked cache
     * completion supplies a newer request. Never invent an unobserved cache.
     */
    struct z7_native_cache_snapshot cache;
    return !highlight_cache_api->native_cache_snapshot(output, &cache);
}
static uint32_t highlight_native_origin_note(uint32_t command, const void *payload, uint32_t generation)
{
    struct z7_highlight_lease_record r;
    for (uint32_t i = 0; i < sizeof(r) / 4; ++i) ((uint32_t *)&r)[i] = 0;
    r.native_generation = generation;
    uint32_t output = 0;
    if (payload && z7_highlight_context_read(&r.context) && r.context.ready == 1 &&
        (r.context.service == 3 || r.context.service == 4)) output = highlight_handoff_output(&r.context);
    if (output && command == (output == 1 ? 0x42060007u : 0x42062007u)) {
        r.valid = r.baseline_foreign = 1; highlight_baseline(r.baseline, payload);
        r.cache_bound = highlight_cache_api->native_cache_snapshot(output, &r.cache);
        return z7_highlight_lease_publish(&z7_highlight_native_origins[r.context.selector], &r);
    }
    /* Unknown/non-photo updates retire both historical photo origins. */
    uint32_t ok = 1;
    for (uint32_t i = 0; i < 2; ++i) ok &= z7_highlight_lease_publish(&z7_highlight_native_origins[i], &r);
    return ok;
}
static uint32_t highlight_handoff_prepare(struct z7_highlight_lease_record *r,
                                         const struct z7_highlight_context *c)
{
    struct z7_highlight_lease_snapshot origin;
    uint32_t output = highlight_handoff_output(c);
    if (!output || !highlight_handoff_origin(c, &origin)) return 0;
    for (uint32_t i = 0; i < sizeof(*r) / 4; ++i) ((uint32_t *)r)[i] = 0;
    r->context = *c;
    r->palette = W(0xa1f18facu);
    if (!ram(r->palette, 1024)) return 0;
    r->cache_bound = highlight_cache_api->native_cache_snapshot(output, &r->cache);
    uint32_t retained = origin.record.valid && highlight_identity(c, &origin.record.context);
    if (r->cache_bound) {
        if (retained && origin.record.cache_bound && highlight_handoff_raw_equal(&r->cache, &origin.record.cache) &&
            (origin.record.baseline_foreign || origin.record.palette == r->palette)) {
            r->baseline_foreign = origin.record.baseline_foreign;
            for (uint32_t i = 0; i < 25; ++i) r->baseline[i] = origin.record.baseline[i];
        } else {
            if (r->cache.request[0] > 1) return 0;
            if (r->cache.request[0])
                F(0x1034fe23u, void, void *, const void *, uint32_t)(r->baseline, r->cache.request, output);
        }
        return highlight_cache_api->native_cache_snapshot_valid(output, &r->cache);
    }
    if (!retained || origin.record.cache_bound) return 0;
    r->baseline_foreign = origin.record.baseline_foreign;
    for (uint32_t i = 0; i < 25; ++i) r->baseline[i] = origin.record.baseline[i];
    return 1;
}
static uint32_t highlight_handoff_commit(const struct z7_highlight_lease_record *r)
{
    struct z7_highlight_lease_record origin;
    highlight_record_copy(&origin, r); origin.valid = 1;
    return z7_highlight_lease_publish(&z7_highlight_native_origins[r->context.selector], &origin);
}
static uint32_t highlight_handoff_retire_frame(const struct z7_highlight_context *c,
                                              const struct z7_highlight_lease_record *old)
{
    if (highlight_identity(c, &old->context)) return 1;
    struct highlight_frame_native_record frame;
    if (!old->disabled || !highlight_frame_native_read(&frame)) return 0;
    if (!frame.valid) return 1;
    if (!highlight_frame_engine_matches(&frame) || W(c->state + 0x28) || W(c->state + 0x1c) ||
        (W(0x20140000u + frame.bank + 0x430) & 1)) return 0;
    frame.valid = 0;
    return highlight_frame_native_publish(&frame);
}
