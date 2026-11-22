/* SPDX-License-Identifier: MIT. Independent original-Z7 resident worker API. */
#ifndef Z7_WORKER_H
#define Z7_WORKER_H
#include "information.h"
/* Additive44-byte ARM API. One callback may be registered during initialization.
 * It runs on the resident module-loader task after each native delay(1000),
 * only following successful initialization. Delay units are not milliseconds.
 * Dispatch is private to that single task; the SDK exposes no dispatch entry.
 * An ordinary task-owned flag suppresses recursion without exclusive accesses
 * to the host state region. This flag is not a mutex for concurrent callers.
 * No paint/menu callback runs the worker. Changes adding another dispatcher
 * caller must first supply an appropriate synchronization/ownership contract.
 * The callback must bound its own work and coordinate shared module state;
 * this API supplies neither card readiness, shutdown flushing nor an I/O lock.
 * Successful modules/callbacks stay resident until power-off; no hot unload.
 */
struct z7_module_worker_api {
    struct z7_module_information_api information;
    uint32_t (*register_worker)(void (*callback)(void));
};
#endif
