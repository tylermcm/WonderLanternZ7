/* SPDX-License-Identifier: MIT; independent original-Z7 C 3.80 research. */
#ifndef Z7_HOST_380_H
#define Z7_HOST_380_H
#include "module.h"
#include "display.h"
#include "update.h"
#include "disp.h"
#include "gui.h"
#include "information.h"
#include "worker.h"
#ifdef Z7_HOST_HIGHLIGHTS
#include "highlight.h"
#endif
#ifdef Z7_HOST_PARAMETERS
#include "parameters.h"
#endif
#ifdef Z7_HOST_FRAME_PERMISSION
#include "frame_permission.h"
#endif
#ifdef Z7_HOST_CACHED_FRAME
#include "cached_frame_permission.h"
#endif
#ifdef Z7_HOST_OWNED_FRAME_COORDINATION
#include "owned_frame_coordination.h"
#include "highlight_lane.h"
#endif
#ifdef Z7_HOST_NATIVE_WARNING_TRANSACTION
#include "native_warning_transaction.h"
#endif
#ifdef Z7_HOST_NATIVE_CACHE_COPY
#include "native_cache.h"
#include "../plugins/cache_observation.h"
#endif
#ifdef Z7_HOST_GRAPHICS
#ifndef Z7_HOST_NATIVE_CACHE_COPY
#error Graphics API requires the native cache API prefix
#endif
#include "graphics.h"
#endif
#ifdef Z7_HOST_NAVIGATION
#ifndef Z7_HOST_GRAPHICS
#error Navigation API requires the graphics API prefix
#endif
#include "navigation.h"
#endif
#ifdef Z7_HOST_TOUCH
#ifndef Z7_HOST_NAVIGATION
#error Touch API requires the navigation API prefix
#endif
#include "touch.h"
#endif

#define Z7_HOST_STATE 0xa9700000u
#ifdef Z7_HOST_TOUCH
#define Z7_HOST_STATE_BYTES 424u
#elif defined(Z7_HOST_NAVIGATION)
#define Z7_HOST_STATE_BYTES 404u
#elif defined(Z7_HOST_GRAPHICS)
#define Z7_HOST_STATE_BYTES 384u
#elif defined(Z7_HOST_NATIVE_CACHE_COPY)
#define Z7_HOST_STATE_BYTES 360u
#elif defined(Z7_HOST_NATIVE_WARNING_TRANSACTION)
#define Z7_HOST_STATE_BYTES 336u
#elif defined(Z7_HOST_OWNED_FRAME_COORDINATION)
#define Z7_HOST_STATE_BYTES 324u
#elif defined(Z7_HOST_CACHED_FRAME)
#define Z7_HOST_STATE_BYTES 304u
#elif defined(Z7_HOST_FRAME_PERMISSION)
#define Z7_HOST_STATE_BYTES 288u
#elif defined(Z7_HOST_PARAMETERS)
#define Z7_HOST_STATE_BYTES 272u
#else
#define Z7_HOST_STATE_BYTES 256u
#endif
#define Z7_HOST_MAGIC 0x5a37484du
#define Z7_HOST_FS_OK 0x04390080u
#define Z7_HOST_RETRIES 100u

enum z7_host_status {
    Z7_HOST_IDLE = 0, Z7_HOST_NO_FILE, Z7_HOST_BAD_SIZE,
    Z7_HOST_ALLOC_FAILED, Z7_HOST_READ_FAILED, Z7_HOST_CLOSE_FAILED,
    Z7_HOST_INVALID_MODULE, Z7_HOST_INIT_FAILED, Z7_HOST_LOADED,
    Z7_HOST_TASK_FAILED, Z7_HOST_ALREADY_LOADED, Z7_HOST_BAD_STATE
};
struct z7_host_state {
    uint32_t task[8];
    uint32_t magic, booted, status, native_result;
    uint32_t image, allocation, memory_size, entry_offset;
    uint32_t module_result, attempts, retained_fd;
    uint32_t loading_image, loading_image_size, loading_memory_size;
    uint32_t display_registered, display_ready;
    struct z7_display_hooks display;
    uint32_t grid_metadata, grid_callbacks, grid_menu_registered, grid_menu_committed;
    uint32_t before_update, update_registered;
    uint32_t disp_cycle, disp_registered;
    uint32_t after_gui_update, gui_registered, gui_running;
    uint32_t information_cycle, information_cycle_registered;
    uint32_t before_information_update, information_update_registered;
    uint32_t information_cycle_running, information_update_running;
    uint32_t worker_callback, worker_registered, worker_running, resident_image_size;
#ifdef Z7_HOST_HIGHLIGHTS
    uint32_t highlight_descriptor, highlight_before_source, highlight_after_source;
    uint32_t highlight_before_consumer, highlight_after_consumer;
    uint32_t highlight_source_running, highlight_consumer_running;
#else
    uint32_t reserved[7];
#endif
    uint32_t guards[4];
#ifdef Z7_HOST_PARAMETERS
    uint32_t parameter_callback, parameter_running, parameter_guards[2];
#endif
#ifdef Z7_HOST_FRAME_PERMISSION
    uint32_t frame_permission_callback, frame_permission_running, frame_permission_guards[2];
#endif
#ifdef Z7_HOST_CACHED_FRAME
    uint32_t cached_frame_callback, cached_frame_running, cached_frame_guards[2];
#endif
#ifdef Z7_HOST_OWNED_FRAME_COORDINATION
    uint32_t owned_frame_enabled;
    struct z7_highlight_lane owned_frame_lane;
    uint32_t owned_frame_guards[2];
#endif
#ifdef Z7_HOST_NATIVE_WARNING_TRANSACTION
    uint32_t native_warning_enabled, native_warning_guards[2];
#endif
#ifdef Z7_HOST_NATIVE_CACHE_COPY
    struct z7_cache_observation native_cache;
    uint32_t native_cache_ready, native_cache_guards[2];
#endif
#ifdef Z7_HOST_GRAPHICS
    uint32_t graphics_callback, graphics_registered, graphics_phase, graphics_running;
    uint32_t graphics_guards[2];
#endif
#ifdef Z7_HOST_NAVIGATION
    uint32_t navigation_callback,navigation_registered,navigation_running;
    uint32_t navigation_guards[2];
#endif
#ifdef Z7_HOST_TOUCH
    uint32_t touch_callback,touch_registered,touch_running,touch_guards[2];
#endif
};
_Static_assert(sizeof(struct z7_host_state) == Z7_HOST_STATE_BYTES, "Host state layout");
#ifdef Z7_HOST_GRAPHICS
_Static_assert(__builtin_offsetof(struct z7_host_state,graphics_callback)==360, "Graphics state prefix");
_Static_assert(__builtin_offsetof(struct z7_host_state,graphics_guards)==376, "Graphics state guards");
#endif
#ifdef Z7_HOST_NAVIGATION
_Static_assert(__builtin_offsetof(struct z7_host_state,navigation_callback)==384, "Navigation state prefix");
_Static_assert(__builtin_offsetof(struct z7_host_state,navigation_guards)==396, "Navigation guards");
#endif
#ifdef Z7_HOST_TOUCH
_Static_assert(__builtin_offsetof(struct z7_host_state,touch_callback)==404, "Touch state prefix");
_Static_assert(__builtin_offsetof(struct z7_host_state,touch_guards)==416, "Touch guards");
#endif
uint32_t z7_module_load_once(struct z7_host_state *state);
void z7_module_worker(struct z7_host_state *state);
void z7_module_boot(void);
uint32_t z7_autoop_init(void);
const uint16_t *z7_display_grid_source(void);
void z7_display_grid_geometry(void);
uint32_t z7_display_scalar(uint32_t key, uint32_t value);
uint32_t z7_display_histogram_gate(uint32_t state);
void z7_display_before_paint(void);
void z7_display_after_paint(void);
void z7_display_before_update(void);
uint32_t z7_display_disp_cycle(void);
void z7_display_after_gui_update(void);
void z7_gui_update_bridge(void);
uint32_t z7_display_information_cycle(void);
uint32_t z7_display_before_information_update(void);
void z7_information_update_bridge(void);
#endif
