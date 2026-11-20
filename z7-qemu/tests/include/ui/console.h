/* SPDX-License-Identifier: GPL-2.0-or-later */
/* Minimal host test adapters; production renderer is included unchanged. */
#include <glib.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
typedef struct { uint8_t data[720*480*4]; unsigned width; } DisplaySurface;
typedef struct { DisplaySurface surface; } QemuConsole;
typedef struct { int unused; } GraphicHwOps;
static QemuConsole test_console;
static DisplaySurface *qemu_console_surface(QemuConsole *q) { return &q->surface; }
static uint8_t *surface_data(DisplaySurface *s) { return s->data; }
static unsigned surface_stride(DisplaySurface *s) { return (s->width ? s->width : 8)*4; }
static void dpy_gfx_update(QemuConsole *q, int x, int y, int w, int h) {}
static void qemu_console_resize(QemuConsole *q, int w, int h) { assert(w*h*4<=sizeof(q->surface.data)); q->surface.width=w; }
static QemuConsole *graphic_console_init(void *d, int n, const GraphicHwOps *o, void *p) { return &test_console; }
static uint8_t memory[2*1024*1024];
static void cpu_physical_memory_read(uint32_t a, void *p, size_t n) {
    assert(a >= 0xa1000000 && (uint64_t)a+n <= 0xa1000000+sizeof(memory));
    memcpy(p, memory+a-0xa1000000, n);
}
static void cpu_physical_memory_write(uint32_t a, const void *p, size_t n) {
    assert(a >= 0xa1000000 && (uint64_t)a+n <= 0xa1000000+sizeof(memory));
    memcpy(memory+a-0xa1000000, p, n);
}
static uint32_t ldl_le_p(const void *p) { uint32_t v; memcpy(&v,p,4); return v; }
static uint16_t lduw_le_p(const void *p) { uint16_t v; memcpy(&v,p,2); return v; }
static void stl_p(void *p, uint32_t v) { memcpy(p,&v,4); }
