/* SPDX-License-Identifier: MIT.
 * Original-Z7 C 3.80 shutter-sound TRIGGER PROBE module. Plays no sound; see
 * shutter_trigger_probe.h and SHUTTER_TRIGGER_PROBE_TEST.md.
 */
#include "shutter_trigger_probe.h"

uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET ||
        api->size<sizeof(struct z7_module_worker_api)) return 1;
    if (!z7_trig_matches()) return 1;
    if (!((const struct z7_module_worker_api *)api)->register_worker(z7_trig_worker)) return 1;
    z7_trig_install();
    return 0;
}
