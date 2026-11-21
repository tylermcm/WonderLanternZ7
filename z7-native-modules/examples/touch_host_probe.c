/* SPDX-License-Identifier: MIT. Resident API92 touch contract diagnostic. */
#include "module.h"
#include "touch.h"
volatile uint32_t z7_touch_probe_api_size,z7_touch_probe_registered,z7_touch_probe_duplicate;
volatile uint32_t z7_touch_probe_calls,z7_touch_probe_mode,z7_touch_probe_late;
static uint32_t (*register_again)(z7_touch_callback);
static uint32_t touch_probe(const uint32_t *event,uint32_t *copy)
{
    ++z7_touch_probe_calls;
    for (uint32_t i=0;i<15;++i) copy[i]=event[i];
    copy[5]^=0x12340000u;
    if (z7_touch_probe_mode==1) return 1;
    if (z7_touch_probe_mode==2) return 7;
    if (z7_touch_probe_mode==3)
        ((uint32_t (*)(const uint32_t *))(uintptr_t)0x103319d9u)(event);
    if (z7_touch_probe_mode==4) z7_touch_probe_late=register_again(touch_probe);
    return 0;
}
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET || api->size<92) return 1;
    const struct z7_module_touch_api *touch=(const void *)api;
    if (!touch->register_touch) return 1;
    z7_touch_probe_api_size=api->size;register_again=touch->register_touch;
    z7_touch_probe_registered=register_again(touch_probe);
    z7_touch_probe_duplicate=register_again(touch_probe);
    if (!z7_touch_probe_registered) return 1;
#ifdef Z7_TOUCH_PROBE_FAIL_INIT
    return 1;
#else
    return 0;
#endif
}
