/* SPDX-License-Identifier: MIT. Instruction-only transition adapter diagnostic.
 * No native page or application changes occur during module initialization.
 * Explicit exported operations let the fixture execute the production helper.
 */
#include "module.h"
#include "../plugins/information_transition.h"
struct z7_information_transition z7_information_ledger;
uint32_t z7_information_operation(uint32_t operation, uint32_t saved, uint32_t released)
{
    switch (operation) {
    case 0: return information_enter(&z7_information_ledger, saved, released);
    case 1: return information_observe(&z7_information_ledger);
    case 2: return information_exit_admitted(&z7_information_ledger);
    default: return 0;
    }
}
uint32_t z7_main(const struct z7_module_api *api)
{
    return !api || api->abi != Z7_MODULE_ABI || api->target != Z7_MODULE_TARGET || api->size < sizeof(*api);
}
