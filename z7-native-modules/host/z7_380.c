/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 WonderLanternZ7 contributors.
 * Independent original-Z7 C 3.80 bindings. See Z7_MODULE_HOST_RESEARCH.md.
 * Emulator-only prototype; no installation or recovery clearance.
 */
#include "z7_380.h"

#define FN(address, result, ...) ((result (*)(__VA_ARGS__))(uintptr_t)(address))
static const struct z7_module_api api = {Z7_MODULE_ABI, sizeof(api), Z7_MODULE_TARGET};
static void *allocate(uint32_t n) { return FN(0x1016fe39u, void *, uint32_t, uint32_t)(n, 0); }
static void release(void *p) { FN(0x1016fe4bu, void, void *)(p); }
static void delay(uint32_t n) { FN(0x1017081fu, void, uint32_t)(n); }
static void invalidate(void *p, uint32_t n) { FN(0x101e9f77u, void, void *, uint32_t)(p, n); }
static uint32_t close_file(uint32_t *file) { return FN(0x102d85f3u, uint32_t, uint32_t *)(file); }
static uint32_t read_file(uint32_t *file, void *p, uint32_t n, uint32_t *actual)
{
    return FN(0x102d86d9u, uint32_t, uint32_t *, void *, uint32_t, uint32_t *)(file, p, n, actual);
}
static uint32_t valid_state(const struct z7_host_state *s)
{
    if ((uintptr_t)s != Z7_HOST_STATE || s->magic != Z7_HOST_MAGIC) return 0;
    for (uint32_t i = 0; i < 4; ++i) if (s->guards[i] != 0xa5a5a5a5u) return 0;
    return 1;
}

/* Original cache helpers step by 64 bytes and invalidate one or more extra
 * lines. The private staging array below reserves 127 bytes beyond the largest
 * 513-byte read, so no unrelated dirty stack line is invalidated.
 * Executable publication cleans each affected D line to PoU, then invalidates
 * I-cache to PoU. Cache coherence on physical hardware remains untested.
 */
__attribute__((noinline)) void z7_module_publish(uint8_t *body, uint32_t n)
{
    uint32_t first = (uint32_t)(uintptr_t)body;
    for (uint32_t p = first; p < first + n; p += 64)
        __asm__ volatile("mcr p15, 0, %0, c7, c11, 1" :: "r"(p) : "memory");
    uint32_t zero = 0;
    __asm__ volatile("dsb sy\n mcr p15, 0, %0, c7, c5, 0\n dsb sy\n isb sy"
                     :: "r"(zero) : "memory");
}
__attribute__((noinline)) uint32_t z7_module_call(uint8_t *body, uint32_t entry)
{
    return ((uint32_t (*)(const struct z7_module_api *))
             ((uintptr_t)body + entry + 1))(&api);
}
__attribute__((noinline)) void z7_module_result(struct z7_host_state *s)
{
    __asm__ volatile("" :: "r"(s) : "memory");
}

uint32_t z7_module_load_once(struct z7_host_state *s)
{
    if (!valid_state(s)) return Z7_HOST_BAD_STATE;
    if (s->image || s->allocation) return Z7_HOST_ALREADY_LOADED;
    /* A failed close is never retried using a possibly stale/recycled handle. */
    if (s->retained_fd != UINT32_MAX) return Z7_HOST_CLOSE_FAILED;
    uint32_t file[10];
    for (uint32_t i = 0; i < 10; ++i) ((volatile uint32_t *)file)[i] = 0;
    FN(0x102d8563u, void, uint32_t *, const char *)(file, "A:\\Z7APP.BIN");
    uint32_t native = FN(0x102d8567u, uint32_t, uint32_t *, uint32_t, uint32_t)(file, 0, 0);
    uint32_t status = Z7_HOST_NO_FILE, descriptor = file[2], size = file[6];
    uint8_t *raw = 0;
    s->native_result = native;
    if (native == Z7_HOST_FS_OK) {
        status = Z7_HOST_BAD_SIZE;
        if (!file[7] && size >= Z7_MODULE_HEADER && size <= Z7_MODULE_MAX_FILE) {
            raw = allocate(size);
            status = Z7_HOST_ALLOC_FAILED;
            if (raw) {
                _Alignas(64) uint8_t staging[640];
                status = Z7_HOST_IDLE;
                for (uint32_t offset = 0; offset < size;) {
                    uint32_t count = size - offset, actual = 0;
                    if (count > 512) count = 512;
                    /* The last request also checks the observed EOF boundary. */
                    uint32_t capacity = count + (offset + count == size);
                    invalidate(staging, capacity);
                    native = read_file(file, staging, capacity, &actual);
                    invalidate(staging, capacity);
                    s->native_result = native;
                    if (native != Z7_HOST_FS_OK || actual != count) {
                        status = Z7_HOST_READ_FAILED;
                        break;
                    }
                    for (uint32_t i = 0; i < count; ++i) raw[offset + i] = staging[i];
                    offset += count;
                }
            }
        }
    }
    if ((int32_t)descriptor >= 0) {
        native = close_file(file);
        if (native != Z7_HOST_FS_OK) {
            s->retained_fd = descriptor;
            s->native_result = native;
            status = Z7_HOST_CLOSE_FAILED;
        }
    }
    if (status) {
        if (raw) release(raw);
        return status;
    }
    struct z7_module_info info;
    uint32_t result = z7_module_validate(raw, size, &info);
    if (result) {
        s->module_result = result;
        release(raw);
        return Z7_HOST_INVALID_MODULE;
    }
    uint32_t memory = info.image_size + info.bss_size;
    void *allocation = allocate(memory + 63);
    if (!allocation) { release(raw); return Z7_HOST_ALLOC_FAILED; }
    uint8_t *body = (uint8_t *)(((uintptr_t)allocation + 63u) & ~(uintptr_t)63u);
    result = z7_module_prepare(raw, size, body, memory, (uint32_t)(uintptr_t)body, &info);
    release(raw);
    if (result) {
        s->module_result = result;
        release(allocation);
        return Z7_HOST_INVALID_MODULE;
    }
    z7_module_publish(body, memory);
    s->module_result = z7_module_call(body, info.entry_offset);
    if (s->module_result) { release(allocation); return Z7_HOST_INIT_FAILED; }
    s->image = (uint32_t)(uintptr_t)body;
    s->allocation = (uint32_t)(uintptr_t)allocation;
    s->memory_size = memory;
    s->entry_offset = info.entry_offset;
    __asm__ volatile("dmb sy" ::: "memory");
    return Z7_HOST_LOADED;
}

void z7_module_worker(struct z7_host_state *s)
{
    if (valid_state(s)) {
        for (uint32_t i = 0; i < Z7_HOST_RETRIES; ++i) {
            s->attempts = i + 1;
            s->status = z7_module_load_once(s);
            if (s->status != Z7_HOST_NO_FILE) break;
            if (i + 1 < Z7_HOST_RETRIES) delay(100);
        }
        z7_module_result(s);
    }
    /* Keep the task and any successful module resident; no hot unload. */
    for (;;) delay(1000);
}
void z7_module_boot(void)
{
    struct z7_host_state *s = (struct z7_host_state *)(uintptr_t)Z7_HOST_STATE;
    if (!valid_state(s) || s->booted) return;
    s->booted = 1;
    s->retained_fd = UINT32_MAX;
    _Alignas(4) uint8_t descriptor[28];
    const uint8_t *original = (const uint8_t *)(uintptr_t)0x11f9a92cu; /* APPIDLE */
    for (uint32_t i = 0; i < sizeof(descriptor); ++i) descriptor[i] = original[i];
    static const uint8_t name[8] = {'Z','7','M','O','D',0,0,0};
    for (uint32_t i = 0; i < 8; ++i) descriptor[16 + i] = name[i];
    descriptor[26] = descriptor[27] = 0;
    FN(0x1017074bu, uint32_t, void *, void (*)(struct z7_host_state *), void *)(s, z7_module_worker, descriptor);
    if ((int32_t)s->task[0] <= 0) { s->status = Z7_HOST_TASK_FAILED; return; }
    __asm__ volatile("dmb sy" ::: "memory");
    s->native_result = FN(0x101707f5u, uint32_t, void *, void *)(s, s);
    if (s->native_result) s->status = Z7_HOST_TASK_FAILED;
    else s->booted = 2;
}
uint32_t z7_autoop_init(void)
{
    uint32_t result = FN(0x102697f5u, uint32_t, void)();
    z7_module_boot();
    return result;
}
