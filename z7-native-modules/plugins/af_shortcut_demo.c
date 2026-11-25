/* SPDX-License-Identifier: MIT.
 * EMULATOR DEMO of the original-Z7 AF-area shortcut runtime. Fixed assignment:
 * Fn1 -> Wide-area AF (L). Runs once per shooting-display update through the
 * host's before-update hook. Acts only when Fn1's f2 assignment is None.
 * Not a release: no menu, no saved settings, not for the camera.
 */
#include "update.h"
#include "af_shortcut_runtime.h"

static struct z7_af_runtime z7_af_demo;
volatile uint32_t z7_af_demo_steps, z7_af_demo_last_result, z7_af_demo_init;

static void z7_af_demo_update(void)
{
    ++z7_af_demo_steps;
    uint32_t r=z7_af_runtime_step(&z7_af_demo,1,0,z7_af_native_none_buttons());
    if (r) z7_af_demo_last_result=r;
}

uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET ||
        api->size<sizeof(struct z7_module_update_api)) return 1;
    if (!z7_af_area_matches()) return 1;
    z7_af_shortcut_reset(&z7_af_demo.policy);
    z7_af_shortcut_assign(&z7_af_demo.policy,AF_BUTTON_FN1,AF_AREA_WIDE_L+1u);
    if (!((const struct z7_module_update_api *)api)->register_before_update(z7_af_demo_update)) return 1;
    z7_af_demo_init=1;
    return 0;
}
