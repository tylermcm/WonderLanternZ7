/* SPDX-License-Identifier: MIT. Independent original-Z7 GUI update interface. */
#ifndef Z7_GUI_H
#define Z7_GUI_H
#include "disp.h"
/* Additive32-byte ARM API. Runs after original shooting-update1030DB42 returns,
 * including its native early-return/app-transition paths. It is not a camera
 * frame/ISP completion guarantee. The module must revalidate current ownership
 * and native render-busy state before submitting an extra pass. */
struct z7_module_gui_api {
    struct z7_module_disp_api disp;
    uint32_t (*register_after_gui_update)(void (*callback)(void));
};
#endif
