/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 WonderLanternZ7 contributors.
 * Independent original-Z7 C 3.80 bindings. See Z7_MODULE_HOST_RESEARCH.md.
 * Emulator-only prototype; no installation or recovery clearance.
 */
#include "z7_380.h"

#define FN(address, result, ...) ((result (*)(__VA_ARGS__))(uintptr_t)(address))
static uint32_t register_display(const struct z7_display_hooks *hooks);
static uint32_t register_grid_menu(const struct z7_grid_menu *menu);
static uint32_t register_before_update(void (*callback)(void));
static uint32_t register_disp_cycle(uint32_t (*callback)(void));
static uint32_t register_after_gui_update(void (*callback)(void));
static uint32_t register_information_cycle(uint32_t (*callback)(void));
static uint32_t register_before_information_update(void (*callback)(void));
static const struct z7_module_information_api api = {
    {{{{Z7_MODULE_ABI, sizeof(api), Z7_MODULE_TARGET, register_display, register_grid_menu}, register_before_update},
      register_disp_cycle}, register_after_gui_update},
    register_information_cycle, register_before_information_update
};
_Static_assert(sizeof(api) == 40, "Information API prefix layout");
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

static uint32_t within(uintptr_t p, uint32_t base, uint32_t bytes, uint32_t n)
{
    return p >= base && n <= bytes && p - base <= bytes - n;
}
static uint32_t loading_data(struct z7_host_state *s, uintptr_t p, uint32_t n)
{
    return p % 4 == 0 && within(p, s->loading_image, s->loading_memory_size, n);
}
static uint32_t loading_code(struct z7_host_state *s, uint32_t fn)
{
    return (fn & 1) && within(fn & ~1u, s->loading_image, s->loading_image_size, 2);
}
static uint32_t register_display(const struct z7_display_hooks *hooks)
{
    struct z7_host_state *s = (struct z7_host_state *)(uintptr_t)Z7_HOST_STATE;
    uintptr_t p = (uintptr_t)hooks;
    if (!valid_state(s) || !s->loading_image || s->display_registered || s->display_ready ||
        p % 4 || !within(p, s->loading_image, s->loading_memory_size, sizeof(*hooks))) return 0;
    if (hooks->abi != Z7_DISPLAY_ABI || hooks->size != sizeof(*hooks)) return 0;
    const uint32_t *words = (const uint32_t *)hooks;
    for (uint32_t i = 2; i < sizeof(*hooks) / 4; ++i) {
        uint32_t fn = words[i];
        if (fn && !loading_code(s, fn)) return 0;
    }
    for (uint32_t i = 0; i < sizeof(*hooks) / 4; ++i)
        ((volatile uint32_t *)&s->display)[i] = words[i];
    s->display_registered = 1;
    return 1;
}
static uint32_t register_grid_menu(const struct z7_grid_menu *menu)
{
    struct z7_host_state *s = (struct z7_host_state *)(uintptr_t)Z7_HOST_STATE;
    if (!valid_state(s) || !s->loading_image || s->grid_menu_registered || s->display_ready ||
        !loading_data(s, (uintptr_t)menu, sizeof(*menu))) return 0;
    if (menu->abi != Z7_DISPLAY_ABI || menu->size != sizeof(*menu) ||
        !loading_data(s, (uintptr_t)menu->metadata, 28) ||
        !loading_data(s, (uintptr_t)menu->callbacks, 20)) return 0;
    const uint32_t *object = (const uint32_t *)(uintptr_t)0xa1836f8cu;
    const uint32_t *native = (const uint32_t *)(uintptr_t)object[10];
    const uint32_t *callbacks = (const uint32_t *)(uintptr_t)object[4];
    const uint32_t *metadata = menu->metadata;
    uint32_t rows = metadata[5] & 65535u;
    if (object[0] != 0x01530002u || rows < 2 || rows > 8 || metadata[5] != (rows | rows << 16) ||
        metadata[0] != native[0] || metadata[2] != native[2] || metadata[6] != native[6] ||
        !loading_code(s, menu->callbacks[0]) || !loading_data(s, metadata[1], 16) ||
        !loading_data(s, metadata[3], rows * 28) || !loading_data(s, metadata[4], rows * 4)) return 0;
    for (uint32_t i = 1; i < 5; ++i) if (menu->callbacks[i] != callbacks[i]) return 0;
    const uint32_t *geometry = (const uint32_t *)(uintptr_t)metadata[1];
    if (geometry[0] != rows) return 0;
    for (uint32_t i = 1; i < 4; ++i)
        if (!loading_data(s, geometry[i], rows * 8)) return 0;
    const uint32_t *maps = (const uint32_t *)(uintptr_t)metadata[4];
    const uint32_t *native_maps = (const uint32_t *)(uintptr_t)native[4];
    for (uint32_t row = 0; row < rows; ++row) {
        if (row + 1 == rows && maps[row] == native_maps[1]) continue;
        if (!loading_data(s, maps[row], 17 * 16)) return 0;
        const uint32_t *events = (const uint32_t *)(uintptr_t)maps[row];
        uint32_t activations = 0;
        for (uint32_t i = 0; i < 17; ++i)
            if (events[i * 4] == 0x239 || events[i * 4] == 0x25f) {
                if (!loading_code(s, events[i * 4 + 1])) return 0;
                ++activations;
            }
        if (activations != 2) return 0;
    }
    s->grid_metadata = (uint32_t)(uintptr_t)menu->metadata;
    s->grid_callbacks = (uint32_t)(uintptr_t)menu->callbacks;
    s->grid_menu_registered = 1;
    return 1;
}
static uint32_t register_before_update(void (*callback)(void))
{
    struct z7_host_state *s = (struct z7_host_state *)(uintptr_t)Z7_HOST_STATE;
    if (!valid_state(s) || !s->loading_image || s->update_registered || s->display_ready ||
        !loading_code(s, (uint32_t)(uintptr_t)callback)) return 0;
    s->before_update = (uint32_t)(uintptr_t)callback;
    s->update_registered = 1;
    return 1;
}
static struct z7_host_state *display_state(void)
{
    struct z7_host_state *s = (struct z7_host_state *)(uintptr_t)Z7_HOST_STATE;
    if (!valid_state(s) || !__atomic_load_n(&s->display_ready, __ATOMIC_ACQUIRE) || !s->image) return 0;
    return s;
}
static uint32_t register_disp_cycle(uint32_t (*callback)(void))
{
    struct z7_host_state *s = (struct z7_host_state *)(uintptr_t)Z7_HOST_STATE;
    if (!valid_state(s) || !s->loading_image || s->disp_registered || s->display_ready ||
        !loading_code(s, (uint32_t)(uintptr_t)callback)) return 0;
    s->disp_cycle = (uint32_t)(uintptr_t)callback;
    s->disp_registered = 1;
    return 1;
}
uint32_t z7_display_disp_cycle(void)
{
    struct z7_host_state *s = display_state();
    if (!s || !s->disp_registered || !s->disp_cycle) return 0;
    uint32_t result = ((uint32_t (*)(void))(uintptr_t)s->disp_cycle)();
    return result == 0x100u || result == 2 ? result : 0;
}
static uint32_t register_after_gui_update(void (*callback)(void))
{
    struct z7_host_state *s = (struct z7_host_state *)(uintptr_t)Z7_HOST_STATE;
    if (!valid_state(s) || !s->loading_image || s->gui_registered || s->display_ready ||
        *(const volatile uint32_t *)(uintptr_t)0xa1829b14u != (uint32_t)(uintptr_t)z7_gui_update_bridge ||
        !loading_code(s, (uint32_t)(uintptr_t)callback)) return 0;
    s->after_gui_update = (uint32_t)(uintptr_t)callback;
    s->gui_registered = 1;
    return 1;
}
void z7_display_after_gui_update(void)
{
    struct z7_host_state *s = display_state();
    if (!s || !s->gui_registered || !s->after_gui_update || s->gui_running ||
        *(const volatile uint32_t *)(uintptr_t)0xa1829b14u != (uint32_t)(uintptr_t)z7_gui_update_bridge) return;
    s->gui_running = 1;
    ((void (*)(void))(uintptr_t)s->after_gui_update)();
    s->gui_running = 0;
}
/* This original callback has no incoming stack arguments. Call its unchanged
 * body first; preserve its complete caller-visible result/register/flag state
 * across the optional module callback. The literal thunk consumes no register. */
__attribute__((naked)) void z7_gui_update_bridge(void)
{
    __asm__ volatile(
        "push {r4, lr}\n"
        "bl 1f\n"
        "push.w {r0-r3, r12, lr}\n"
        "mrs r0, apsr\n"
        "push {r0, r1}\n"
        "bl z7_display_after_gui_update\n"
        "pop {r0, r1}\n"
        "msr APSR_nzcvq, r0\n"
        "pop.w {r0-r3, r12, lr}\n"
        "pop {r4, pc}\n"
        ".balign 4\n"
        "1: ldr.w pc, [pc, #0]\n"
        ".word 0x1030db43\n");
}
static uint32_t information_bindings(void)
{
    return *(const volatile uint32_t *)(uintptr_t)0xa182d180u == 0x102fd647u &&
        *(const volatile uint32_t *)(uintptr_t)0xa182d184u == 0x102fdaefu &&
        *(const volatile uint32_t *)(uintptr_t)0xa182d188u == (uint32_t)(uintptr_t)z7_information_update_bridge;
}
static uint32_t information_context(void)
{
    return *(const volatile uint8_t *)(uintptr_t)0xa1829af4u == 13 &&
        *(const volatile uint32_t *)(uintptr_t)(0xa20207bcu + 13u * 4) == 0xa182d16cu;
}
static uint32_t register_information_cycle(uint32_t (*callback)(void))
{
    struct z7_host_state *s = (struct z7_host_state *)(uintptr_t)Z7_HOST_STATE;
    if (!valid_state(s) || !s->loading_image || s->display_ready || s->information_cycle_registered ||
        !information_bindings() || !loading_code(s, (uint32_t)(uintptr_t)callback)) return 0;
    s->information_cycle = (uint32_t)(uintptr_t)callback;
    s->information_cycle_registered = 1;
    return 1;
}
static uint32_t register_before_information_update(void (*callback)(void))
{
    struct z7_host_state *s = (struct z7_host_state *)(uintptr_t)Z7_HOST_STATE;
    if (!valid_state(s) || !s->loading_image || s->display_ready || s->information_update_registered ||
        !information_bindings() || !loading_code(s, (uint32_t)(uintptr_t)callback)) return 0;
    s->before_information_update = (uint32_t)(uintptr_t)callback;
    s->information_update_registered = 1;
    return 1;
}
uint32_t z7_display_information_cycle(void)
{
    struct z7_host_state *s = display_state();
    if (!s || !s->information_cycle_registered || !s->information_cycle ||
        s->information_cycle_running || s->information_update_running ||
        !information_bindings() || !information_context()) return 0;
    s->information_cycle_running = 1;
    uint32_t result = ((uint32_t (*)(void))(uintptr_t)s->information_cycle)();
    s->information_cycle_running = 0;
    return result == 0x100u || result == 2 ? result : 0;
}
uint32_t z7_display_before_information_update(void)
{
    struct z7_host_state *s = display_state();
    /* Absent/invalid hooks always delegate to the unchanged native body. */
    if (!s || !s->information_update_registered || !s->before_information_update ||
        s->information_cycle_running || s->information_update_running ||
        !information_bindings() || !information_context()) return 1;
    s->information_update_running = 1;
    ((void (*)(void))(uintptr_t)s->before_information_update)();
    s->information_update_running = 0;
    return information_context();
}
__attribute__((naked)) void z7_information_update_bridge(void)
{
    __asm__ volatile(
        "push.w {r0-r12, lr}\n"
        "mrs r0, apsr\n"
        "push {r0, r1}\n"
        "bl z7_display_before_information_update\n"
        "cmp r0, #0\n"
        "beq 2f\n"
        "pop {r0, r1}\n"
        "msr APSR_nzcvq, r0\n"
        "pop.w {r0-r12, lr}\n"
        ".balign 4\n"
        "ldr.w pc, [pc, #0]\n"
        ".word 0x102fda09\n"
        "2: pop {r0, r1}\n"
        "msr APSR_nzcvq, r0\n"
        "pop.w {r0-r12, lr}\n"
        "bx lr\n");
}
const uint16_t *z7_display_grid_source(void)
{
    const uint16_t *native = (const uint16_t *)(uintptr_t)0x1064fd90u;
    struct z7_host_state *s = display_state();
    if (!s || !s->display.grid_source) return native;
    const uint16_t *table = s->display.grid_source(native);
    if ((uintptr_t)table % 2 || !within((uintptr_t)table, s->image, s->memory_size, 96)) return native;
    for (uint32_t i = 0; i < 3; ++i)
        if (!table[i * 16 + 5] || table[i * 16 + 5] > 8 ||
            !table[i * 16 + 11] || table[i * 16 + 11] > 8) return native;
    return table;
}
void z7_display_grid_geometry(void)
{
    struct z7_host_state *s = display_state();
    if (s && s->display.grid_geometry) s->display.grid_geometry((void *)(uintptr_t)0xa2020c2cu);
}
uint32_t z7_display_scalar(uint32_t key, uint32_t value)
{
    struct z7_host_state *s = display_state();
    return s && s->display.scalar_value ? s->display.scalar_value(key, value) : value;
}
uint32_t z7_display_histogram_gate(uint32_t state)
{
    struct z7_host_state *s = display_state();
    return s && s->display.histogram_gate ? !!s->display.histogram_gate(state) : state == 2;
}
void z7_display_before_paint(void)
{
    struct z7_host_state *s = display_state();
    if (s && s->grid_menu_registered && !s->grid_menu_committed) {
        uint32_t pointer = *(const volatile uint32_t *)(uintptr_t)0xa181f91cu;
        uint32_t active = 0;
        if (pointer) {
            if (pointer < 0xa1800000u || pointer > 0xc0000000u - 16 || pointer % 4) active = 1;
            else {
                const volatile uint32_t *list = (const volatile uint32_t *)(uintptr_t)pointer;
                uint32_t stride = list[0], capacity = list[1], count = list[2], data = list[3];
                if (stride < 4 || stride > 1024 || stride % 4 || data % 4 || count > capacity || count > 20 ||
                    data < 0xa1800000u || data > 0xc0000000u - count * stride) active = 1;
                else for (uint32_t i = 0; i < count; ++i)
                    if (*(const volatile uint32_t *)(uintptr_t)(data + i * stride) == 0xa1836f8cu) active = 1;
            }
        }
        if (!active) {
            volatile uint32_t *object = (volatile uint32_t *)(uintptr_t)0xa1836f8cu;
            object[10] = s->grid_metadata;
            __asm__ volatile("dmb sy" ::: "memory");
            object[4] = s->grid_callbacks;
            s->grid_menu_committed = 1;
        }
    }
    if (s && s->display.before_paint) s->display.before_paint();
}
void z7_display_after_paint(void)
{
    struct z7_host_state *s = display_state();
    if (s && s->display.after_paint) s->display.after_paint();
}
void z7_display_before_update(void)
{
    struct z7_host_state *s = display_state();
    if (s && s->update_registered && s->before_update)
        ((void (*)(void))(uintptr_t)s->before_update)();
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
             ((uintptr_t)body + entry + 1))(&api.gui.disp.update.base);
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
    s->loading_image = (uint32_t)(uintptr_t)body;
    s->loading_image_size = info.image_size;
    s->loading_memory_size = memory;
    s->display_registered = 0;
    s->before_update = s->update_registered = 0;
    s->disp_cycle = s->disp_registered = 0;
    s->after_gui_update = s->gui_registered = s->gui_running = 0;
    s->information_cycle = s->information_cycle_registered = 0;
    s->before_information_update = s->information_update_registered = 0;
    s->information_cycle_running = s->information_update_running = 0;
    s->grid_metadata = s->grid_callbacks = s->grid_menu_registered = s->grid_menu_committed = 0;
    for (uint32_t i = 0; i < sizeof(s->display) / 4; ++i)
        ((volatile uint32_t *)&s->display)[i] = 0;
    s->module_result = z7_module_call(body, info.entry_offset);
    s->loading_image = s->loading_image_size = s->loading_memory_size = 0;
    if (s->module_result) {
        s->display_registered = 0;
        s->before_update = s->update_registered = 0;
        s->disp_cycle = s->disp_registered = 0;
        s->after_gui_update = s->gui_registered = s->gui_running = 0;
        s->information_cycle = s->information_cycle_registered = 0;
        s->before_information_update = s->information_update_registered = 0;
        s->information_cycle_running = s->information_update_running = 0;
        s->grid_metadata = s->grid_callbacks = s->grid_menu_registered = s->grid_menu_committed = 0;
        for (uint32_t i = 0; i < sizeof(s->display) / 4; ++i)
            ((volatile uint32_t *)&s->display)[i] = 0;
        release(allocation);
        return Z7_HOST_INIT_FAILED;
    }
    s->image = (uint32_t)(uintptr_t)body;
    s->allocation = (uint32_t)(uintptr_t)allocation;
    s->memory_size = memory;
    s->entry_offset = info.entry_offset;
    __asm__ volatile("dmb sy" ::: "memory");
    if (s->display_registered || s->grid_menu_registered || s->update_registered || s->disp_registered || s->gui_registered ||
        s->information_cycle_registered || s->information_update_registered)
        __atomic_store_n(&s->display_ready, 1, __ATOMIC_RELEASE);
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
