/* SPDX-License-Identifier: MIT. Caller-admitted native band lifecycle diagnostic. */
#include "module.h"
#include "../plugins/portrait_bands.h"
uint32_t z7_portrait_bands_dispatch_probe(struct z7_portrait_bands *state,volatile uint32_t *message,uint32_t page,uint32_t orientation)
{
    z7_portrait_bands_before(state,message,page,orientation);
    uint32_t handled=z7_portrait_page_message(message,page,orientation);
    if (!handled) ((void (*)(volatile uint32_t *))(uintptr_t)0x10372391u)(message);
    return handled;
}
void z7_portrait_bands_observe_probe(struct z7_portrait_bands *state,volatile const uint32_t *message)
{ z7_portrait_bands_observe_clear(state,message); }
void z7_portrait_bands_forget_probe(struct z7_portrait_bands *state)
{ z7_portrait_bands_forget(state); }
uint32_t z7_main(const struct z7_module_api *api)
{ return !api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET || api->size<12; }
