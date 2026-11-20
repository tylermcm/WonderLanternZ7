/* SPDX-License-Identifier: MIT. Independent original-Z7 resident worker API. */
#ifndef Z7_WORKER_H
#define Z7_WORKER_H
#include "information.h"
/* Additive44-byte ARM API. One callback may be registered during initialization.
 * It runs on the resident module-loader task after each native delay(1000),
 * only following successful initialization. Delay units are not milliseconds.
 * No paint/menu callback runs it, and recursive dispatch is suppressed.
 * The callback must bound its own work and coordinate shared module state;
 * this API supplies neither card readiness, shutdown flushing nor an I/O lock.
 * Successful modules/callbacks stay resident until power-off; no hot unload.
 */
struct z7_module_worker_api {
    struct z7_module_information_api information;
    uint32_t (*register_worker)(void (*callback)(void));
};
#endif
