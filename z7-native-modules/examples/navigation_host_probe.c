/* SPDX-License-Identifier: MIT. Resident API88 navigation contract diagnostic. */
#include "module.h"
#include "navigation.h"
volatile uint32_t z7_navigation_probe_api_size,z7_navigation_probe_registered,z7_navigation_probe_duplicate;
volatile uint32_t z7_navigation_probe_calls,z7_navigation_probe_mode,z7_navigation_probe_late;
volatile uint32_t z7_navigation_probe_foreign;
static uint32_t (*register_again)(z7_navigation_callback);
static uint32_t navigation_probe(uint32_t direction,uint32_t *result)
{
    ++z7_navigation_probe_calls;
    if (z7_navigation_probe_mode==1) {*result=0x24680000u|direction;return 1;}
    if (z7_navigation_probe_mode==2) {*result=0xdeadbeefu;return 7;}
    if (z7_navigation_probe_mode==3) {
        *result=((uint32_t (*)(uint32_t))(uintptr_t)0x104389b1u)(direction);return 1;
    }
    if (z7_navigation_probe_mode==4) z7_navigation_probe_late=register_again(navigation_probe);
    if (z7_navigation_probe_mode==5)
        *(volatile uint32_t *)(uintptr_t)0xa182df88u=z7_navigation_probe_foreign;
    return 0;
}
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET || api->size<88) return 1;
    const struct z7_module_navigation_api *nav=(const void *)api;
    if (!nav->register_navigation) return 1;
    z7_navigation_probe_api_size=api->size;register_again=nav->register_navigation;
    z7_navigation_probe_registered=register_again(navigation_probe);
    z7_navigation_probe_duplicate=register_again(navigation_probe);
    if (!z7_navigation_probe_registered) return 1;
#ifdef Z7_NAVIGATION_PROBE_FAIL_INIT
    return 1;
#else
    return 0;
#endif
}
