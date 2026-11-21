/* SPDX-License-Identifier: MIT. Resident graphics API diagnostic; no rotation. */
#include "module.h"
#include "graphics.h"
volatile uint32_t z7_graphics_probe_api_size,z7_graphics_probe_registered;
volatile uint32_t z7_graphics_probe_calls,z7_graphics_probe_mode,z7_graphics_probe_bridge;
volatile uint32_t z7_graphics_probe_late_registration;
static uint32_t (*register_again)(uint32_t (*)(volatile uint32_t *));
static uint32_t graphics_probe(volatile uint32_t *message)
{
    ++z7_graphics_probe_calls;
    if (z7_graphics_probe_mode==1) {
        message[6]=0x2468u;
        ((void (*)(uint32_t,uint32_t))(uintptr_t)message[3])(0x42010062u,message[6]);
        return 1;
    }
    if (z7_graphics_probe_mode==2) return 7; /* Invalid result must use stock. */
    if (z7_graphics_probe_mode==3) {
        z7_graphics_probe_mode=0;
        ((void (*)(volatile uint32_t *))(uintptr_t)z7_graphics_probe_bridge)(message);
        z7_graphics_probe_mode=3;
        return 1; /* Nested bridge already dispatched the native packet. */
    }
    if (z7_graphics_probe_mode==4)
        z7_graphics_probe_late_registration=register_again(graphics_probe);
    return 0;
}
uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET || api->size<84) return 1;
    const struct z7_module_graphics_api *graphics=(const void *)api;
    z7_graphics_probe_api_size=api->size;
    if (!graphics->register_graphics) return 1;
    register_again=graphics->register_graphics;
    z7_graphics_probe_registered=register_again(graphics_probe);
    if (!z7_graphics_probe_registered) return 1;
#ifdef Z7_GRAPHICS_PROBE_FAIL_INIT
    return 1;
#else
    return 0;
#endif
}
