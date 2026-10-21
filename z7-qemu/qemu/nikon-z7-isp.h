/* SPDX-License-Identifier: GPL-2.0-or-later */
/* Opt-in functional ISP experiment. This models a complete raster transaction
 * across the observed 2038 -> tiled 40000000 stream -> 2010 pipeline. It reads
 * guest RAW DMA buffers and writes only native submitted output descriptors.
 * RGGB/u16, sRGB tone response and NV12 are explicit layout/algorithm hypotheses,
 * not an implementation of Nikon's proprietary denoise/calibration operators.
 * No GUI pixels or exposure reports are synthesized here. */

static bool z7_image_process_ready(Z7LabState *s)
{
    return s->image_process_test && s->capture_test_running &&
        s->capture_native0_frames > s->image_process_last_input &&
        (s->image_processor_config[0][8 / 4] & 1) &&
        (s->image_command_config[1][0] & 1) &&
        (s->image_sequence_config[8 / 4] & 1) && s->capture_native0_frames;
}

static void z7_image_process_schedule(Z7LabState *s)
{
    if (z7_image_process_ready(s)) {
        timer_mod(s->image_process_timer, qemu_clock_get_ns(QEMU_CLOCK_VIRTUAL) + 1000000);
    }
}

static void z7_image_raw_irq(Z7LabState *s)
{
    uint32_t *r = s->image_processor_config[0];
    qemu_set_irq(qdev_get_gpio_in(DEVICE(s->priv), 99 - 32),
                 (r[0x24 / 4] & r[0x20 / 4]) != 0);
}

static void z7_image_drain_tick(void *opaque)
{
    Z7LabState *s = opaque;
    if (s->image_drain_requests != 15) { return; }
    s->image_drain_requests = 0;
    /* Native101059f6 requests drain on54/60/6c/78. 100d5652 accumulates
     * status014a0000, calls10105a2a, then wakes IMPMIPU0's stop wait80.
     * Raster DMA is synchronous in this functional model; after cancelling
     * its timer all four channels are idle, even when TG has already stopped.
     * No new frame or pixel completion is implied by this stop handshake. */
    s->image_processor_config[0][8 / 4] &= ~1u;
    s->image_processor_config[0][0x24 / 4] |= 0x014a0000;
    z7_image_raw_irq(s);
    fprintf(stderr, "Z7_IMAGE_DRAIN_COMPLETE irq99_status=0x014a0000 channels=4 new_frames=0\n");
}

static void z7_image_process_tick(void *opaque)
{
    Z7LabState *s = opaque;
    g_autofree uint8_t *raw = NULL;
    if (!z7_image_process_ready(s)) { return; }
    int64_t host_start = g_get_monotonic_time();
    uint32_t *raw_regs = s->image_processor_config[0];
    const size_t raw_bytes = 5568 * 932;
    /* This first implementation accepts only the geometry actually traced.
     * Validate every transaction before writing any destination. */
    if (raw_regs[0x30c / 4] != 5568 || raw_regs[0x48 / 4] != 0x05640396) { goto unsupported; }
    for (unsigned frame = 0; frame < 4; frame++) {
        uint32_t src = raw_regs[0x310 / 4 + frame];
        if (src < 0x53900000 || (uint64_t)src + raw_bytes > 0x9e5b3000) { goto unsupported; }
        for (unsigned channel = 3; channel <= 5; channel++) {
            uint32_t *r = s->image_transfer_config[channel];
            unsigned w = r[8] & 0x7fff, h = r[8] >> 16, stride = r[4];
            uint32_t dst = s->image_command_lists[0][frame * 16 + channel];
            uint64_t uv = (uint64_t)dst + r[10];
            if (r[0] != 0x09000201 || !w || !h || (w & 1) || (h & 1) ||
                w > 1920 || h > 1280 || stride < w || stride > 2048 ||
                r[10] < (uint64_t)stride * h || uv > UINT32_MAX ||
                !z7_copy_ram_range(dst, (uint64_t)stride * h) ||
                !z7_copy_ram_range(uv, (uint64_t)stride * (h / 2))) { goto unsupported; }
        }
    }
    if (!s->image_pixels) {
        s->image_pixels = z7_isp_images_new(g_strcmp0(getenv("Z7_ISP_DISABLE_CACHE"), "1") == 0);
    }
    raw = g_malloc(raw_bytes);
    for (unsigned frame = 0; frame < 4; frame++) {
        uint32_t src = raw_regs[0x310 / 4 + frame];
        cpu_physical_memory_read(src, raw, raw_bytes);
        z7_isp_images_input(s->image_pixels, raw);
        fprintf(stderr, "Z7_IMAGE_PROCESS_INPUT frame=%u source=0x%08x bytes=%zu sha256=%s\n", frame, src, raw_bytes, s->image_pixels->sha);
        for (unsigned channel = 3; channel <= 5; channel++) {
            uint32_t *r = s->image_transfer_config[channel];
            unsigned w = r[8] & 0x7fff, h = r[8] >> 16, stride = r[4];
            uint32_t dst = s->image_command_lists[0][frame * 16 + channel];
            size_t ybytes = (size_t)stride * h, uvbytes = ybytes / 2;
            const uint8_t *yplane = z7_isp_images_output(s->image_pixels, channel - 3, w, h, stride);
            const uint8_t *uvplane = yplane + ybytes;
            cpu_physical_memory_write(dst, yplane, ybytes);
            cpu_physical_memory_write(dst + r[10], uvplane, uvbytes);
            fprintf(stderr, "Z7_IMAGE_PROCESS_OUTPUT frame=%u channel=%u y=0x%08x uv=0x%08x width=%u height=%u stride=%u layout=NV12_hypothesis\n",
                    frame, channel, dst, dst + r[10], w, h, stride);
        }
    }
    ++s->image_process_batches;
    s->image_process_last_input = s->capture_native0_frames;
    /* Native table a1801dd0 maps status20100020 bit2 -> logical1
     * (bank0 / VMAP callback100a4716), bit3 -> logical80 (bank1 /
     * callback100a475a). Both command banks participate in this raster.
     * Bank0's submitted job a2357d88 has callback100a4717 at +3c.
     * Report only enabled banks, after the actual output writes above.
     * Per-unit2010001c dispatches a different event42173082. */
    uint32_t bank_complete = 8;
    if (s->image_command_config[0][0] & 1) { bank_complete |= 4; }
    s->engine_regs[8] |= bank_complete;
    z7_engine_irq(s);
    /* 101053cc -> 100d5652 -> 100a4fac event42170805: bit1 is
     * RAW input completion; bit12 at100a5168 completes MIPU processing
     * and wakes a23307c8/0x200000. Both are enabled by native mask1402.
     * This functional transaction has completed input AND output DMA.
     * Bit10 is a separate stop indication, not a frame completion. */
    raw_regs[0x24 / 4] |= 0x1002;
    z7_image_raw_irq(s);
    s->image_process_host_us += g_get_monotonic_time() - host_start;
    fprintf(stderr, "Z7_IMAGE_PROCESS_BATCH batches=%u raw_inputs=4 outputs=12 irq102_status20=0x%x irq99=0x1002 bit_accurate=0 host_us=%" PRId64 " cache_hits=%" PRIu64 " cache_misses=%" PRIu64 "\n",
            s->image_process_batches, bank_complete, s->image_process_host_us, s->image_pixels->hits, s->image_pixels->misses);
    return;
unsupported:
    fprintf(stderr, "Z7_IMAGE_PROCESS_REJECT unsupported_geometry_or_unmapped_descriptor completion=0\n");
}
