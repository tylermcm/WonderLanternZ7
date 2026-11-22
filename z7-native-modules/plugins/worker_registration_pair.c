/* SPDX-License-Identifier: MIT. Independent single-variable worker test.
 * Working battery/grid components retain their existing notices. No restore,
 * file I/O, status hooks or selection atomics are added to this profile.
 */
#include "worker.h"
#define Z7_GRID_MENU_CHECKPOINT_ENTRY worker_pair_prepare
#include "battery_grid_menu_checkpoint.c"
#undef Z7_GRID_MENU_CHECKPOINT_ENTRY

volatile uint32_t worker_pair_enabled = 1;
static __attribute__((noinline)) void worker_pair_noop(void)
{
    __asm__ volatile("" ::: "memory");
}
uint32_t z7_main(const struct z7_module_api *api)
{
    const struct z7_module_worker_api *worker=(const struct z7_module_worker_api *)api;
    if (!api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET ||
        api->size<sizeof(*worker) || !worker->register_worker) return 1;
    if (worker_pair_prepare(api)) return 1;
    if (!worker_pair_enabled) return 0;
    return worker->register_worker(worker_pair_noop) ? 0 : 1;
}
