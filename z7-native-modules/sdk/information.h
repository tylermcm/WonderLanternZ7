/* SPDX-License-Identifier: MIT. Independent original-Z7 information interface. */
#ifndef Z7_INFORMATION_H
#define Z7_INFORMATION_H
#include "gui.h"
/* Additive40-byte ARM API; the32-byte GUI prefix is unchanged.
 * The cycle callback runs after native information-DISP admission. Return0 to
 * delegate the unchanged native exit path,100h to consume without that exit,
 * or2 only after performing an owned native transition. Other values delegate.
 * The pre-update callback may change app ownership; the host skips the old
 * information update if the original information app is no longer current.
 * Neither callback is a display-completion fence or a physical-camera proof.
 */
struct z7_module_information_api {
    struct z7_module_gui_api gui;
    uint32_t (*register_information_cycle)(uint32_t (*callback)(void));
    uint32_t (*register_before_information_update)(void (*callback)(void));
};
#endif
