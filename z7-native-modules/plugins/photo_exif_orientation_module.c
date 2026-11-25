/* SPDX-License-Identifier: MIT.
 * Standalone original-Z7 upside-down photo EXIF orientation module
 * (photo_orientation_exif.h). Offline/test build; no menu, no settings file.
 */
#include "module.h"
#define Z7_EXIF_IFD_SLOT 0xa18d3410u
#include "photo_orientation_exif.h"

uint32_t z7_main(const struct z7_module_api *api)
{
    if (!api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET || api->size<12) return 1;
    if (!z7_exif_matches()) return 1;
    z7_exif_install();
    return 0;
}
