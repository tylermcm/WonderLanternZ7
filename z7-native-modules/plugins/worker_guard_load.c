/* SPDX-License-Identifier: MIT. Independent manually triggered exclusive-load control.
 * One LDREX, no STREX, worker registration, file I/O or host writes.
 * Included battery/grid components retain their existing notices.
 */
#include "worker.h"
static void guard_probe_selected(uint32_t value);
static const char *guard_probe_label(uint32_t row,const char *fallback);
#define Z7_GRID_SELECTION_CHECKPOINT_HOOK guard_probe_selected
#define Z7_GRID_LABEL_CHECKPOINT_HOOK guard_probe_label
#define Z7_GRID_MENU_CHECKPOINT_ENTRY guard_probe_prepare
#include "battery_grid_menu_checkpoint.c"
#undef Z7_GRID_MENU_CHECKPOINT_ENTRY
#undef Z7_GRID_SELECTION_CHECKPOINT_HOOK
#undef Z7_GRID_LABEL_CHECKPOINT_HOOK

enum { PROBE_HOST,PROBE_READY,PROBE_STARTED,PROBE_OK,PROBE_FAIL,PROBE_BUSY };
static volatile uint32_t guard_probe_state,guard_probe_attempts;
static __attribute__((noinline)) uint32_t guard_load_once(volatile uint32_t *word)
{
    uint32_t value;
    __asm__ volatile("clrex\nldrex %0, [%1]\nclrex"
                     : "=&r"(value) : "r"(word) : "memory");
    return value;
}
static void guard_probe_selected(uint32_t value)
{
    if(value!=4 || guard_probe_state!=PROBE_READY) return;
    if(W(0xa97000c4u) || W(0xa97000c8u)) {guard_probe_state=PROBE_BUSY;return;}
    guard_probe_state=PROBE_STARTED;
    ++guard_probe_attempts;
    uint32_t result=guard_load_once((volatile uint32_t *)(uintptr_t)0xa97000ccu);
    guard_probe_state=result==0 ? PROBE_OK : PROBE_BUSY;
}
static const char *guard_probe_label(uint32_t row,const char *fallback)
{
    if(row!=3) return fallback;
    switch(guard_probe_state) {
    case PROBE_READY:return "Center [LX run]";
    case PROBE_STARTED:return "Center [LX begun]";
    case PROBE_OK:return "Center [LX OK]";
    case PROBE_FAIL:return "Center [LX fail]";
    case PROBE_BUSY:return "Center [LX busy]";
    default:return "Center [LX host]";
    }
}
uint32_t z7_main(const struct z7_module_api *api)
{
    const struct z7_module_worker_api *worker=(const struct z7_module_worker_api *)api;
    if(guard_probe_prepare(api)) return 1;
    if(api->size<sizeof(*worker) || (uintptr_t)worker->register_worker!=0x11fa66f7u) return 0;
    static const uint8_t signature[28]={
        0x50,0xe8,0x00,0x2f,0x72,0xb9,0x40,0xe8,0x00,0x12,0x00,0x2a,0xf8,0xd1,
        0xbf,0xf3,0x5b,0x8f,0xd4,0xf8,0xa4,0x00,0x80,0x47,0x00,0x20,0xbf,0xf3};
    const volatile uint8_t *code=(void *)(uintptr_t)0x11fa5852u;
    for(uint32_t i=0;i<sizeof(signature);++i) if(code[i]!=signature[i]) return 0;
    guard_probe_state=PROBE_READY;
    return 0;
}
