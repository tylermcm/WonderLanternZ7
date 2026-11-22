/* SPDX-License-Identifier: MIT. Independent no-I/O worker progress checkpoint.
 * Included working battery/grid components retain their existing notices.
 */
#include "worker.h"
static const char *worker_progress_label(uint32_t row,const char *fallback);
#define Z7_GRID_LABEL_CHECKPOINT_HOOK worker_progress_label
#define Z7_GRID_MENU_CHECKPOINT_ENTRY worker_progress_prepare
#include "battery_grid_menu_checkpoint.c"
#undef Z7_GRID_MENU_CHECKPOINT_ENTRY
#undef Z7_GRID_LABEL_CHECKPOINT_HOOK

static uint32_t worker_progress_ticks;
static char worker_progress_text[13]="Off [W 0000]";
static void worker_progress_tick(void)
{
    /* This callback is the only writer. GUI only samples. No atomic RMW: the
     * aligned load/store publication compiles without exclusive instructions.
     * Saturation keeps the four-digit display and avoids wraparound ambiguity.
     */
    uint32_t count=__atomic_load_n(&worker_progress_ticks,__ATOMIC_RELAXED);
    if(count<9999) __atomic_store_n(&worker_progress_ticks,count+1,__ATOMIC_RELEASE);
}
static const char *worker_progress_label(uint32_t row,const char *fallback)
{
    if(row!=5) return fallback;
    uint32_t count=__atomic_load_n(&worker_progress_ticks,__ATOMIC_ACQUIRE);
    for(uint32_t i=0;i<4;++i) {
        worker_progress_text[10-i]=(char)('0'+count%10);count/=10;
    }
    return worker_progress_text;
}
uint32_t z7_main(const struct z7_module_api *api)
{
    const struct z7_module_worker_api *worker=(const struct z7_module_worker_api *)api;
    if(!api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET ||
       api->size<sizeof(*worker) || !worker->register_worker) return 1;
    if(worker_progress_prepare(api)) return 1;
    return worker->register_worker(worker_progress_tick) ? 0 : 1;
}
