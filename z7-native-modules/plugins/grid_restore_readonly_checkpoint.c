/* SPDX-License-Identifier: MIT. Independent post-GUI read-only restore test.
 * No camera-side writes; old settings paths/dispatcher are not used. Included
 * battery and grid components retain their existing component notices.
 */
#include "worker.h"
#include "grid_restore_record.h"
static void restore_menu_enter(void);
static void restore_selected(uint32_t value);
static const char *restore_label(uint32_t row, const char *fallback);
#define Z7_GRID_ENTER_CHECKPOINT_HOOK restore_menu_enter
#define Z7_GRID_SELECTION_CHECKPOINT_HOOK restore_selected
#define Z7_GRID_LABEL_CHECKPOINT_HOOK restore_label
#define Z7_GRID_MENU_CHECKPOINT_ENTRY restore_grid_initialize
#include "battery_grid_menu_checkpoint.c"
#undef Z7_GRID_MENU_CHECKPOINT_ENTRY
#undef Z7_GRID_ENTER_CHECKPOINT_HOOK
#undef Z7_GRID_SELECTION_CHECKPOINT_HOOK
#undef Z7_GRID_LABEL_CHECKPOINT_HOOK
#define Z7_SETTINGS_SLOT0_PATH "A:\\Z7GRID.DAT"
#define Z7_SETTINGS_SLOT1_PATH "A:\\Z7GRID.DAT"
#define Z7_SETTINGS_READ_ONLY 1
#include "settings_files.c"
#undef Z7_SETTINGS_READ_ONLY
#undef Z7_SETTINGS_SLOT0_PATH
#undef Z7_SETTINGS_SLOT1_PATH

enum { RESTORE_WAIT, RESTORE_READING, RESTORE_READY, RESTORE_APPLIED,
       RESTORE_MISSING, RESTORE_ERROR, RESTORE_SKIPPED };
static uint32_t restore_gui_seen, restore_state, restore_choice, restore_selection_revision;
static struct z7_settings_files restore_files;
static void restore_selected(uint32_t value)
{
    if (value >= 1 && value <= 5) __atomic_fetch_add(&restore_selection_revision,1,__ATOMIC_RELEASE);
}
static void restore_menu_enter(void)
{
    if (__atomic_load_n(&restore_state,__ATOMIC_ACQUIRE) != RESTORE_READY) return;
    if (__atomic_load_n(&restore_selection_revision,__ATOMIC_ACQUIRE)) {
        __atomic_store_n(&restore_state,RESTORE_SKIPPED,__ATOMIC_RELEASE); return;
    }
    checkpoint_grid_value=restore_choice;
    __atomic_store_n(&restore_state,RESTORE_APPLIED,__ATOMIC_RELEASE);
}
static const char *restore_label(uint32_t row, const char *fallback)
{
    static const char marked[5][16]={"4x4 [SD]","3x3 [SD]","Golden [SD]","Cross [SD]","6x6 [SD]"};
    uint32_t state=__atomic_load_n(&restore_state,__ATOMIC_ACQUIRE);
    if (state==RESTORE_APPLIED && row+1==restore_choice) return marked[row];
    if (row==5 && state==RESTORE_MISSING) return "Off [SD miss]";
    if (row==5 && state==RESTORE_ERROR) return "Off [SD error]";
    if (row==5 && state==RESTORE_SKIPPED) return "Off [SD skip]";
    return fallback;
}
static void restore_after(void)
{
    after();
    if (z7_battery_samples && z7_battery_object)
        __atomic_store_n(&restore_gui_seen,1,__ATOMIC_RELEASE);
}
static void restore_worker(void)
{
    if (__atomic_load_n(&restore_state,__ATOMIC_ACQUIRE) != RESTORE_WAIT ||
        !__atomic_load_n(&restore_gui_seen,__ATOMIC_ACQUIRE)) return;
    __atomic_store_n(&restore_state,RESTORE_READING,__ATOMIC_RELEASE);
    uint8_t record[80];
    uint32_t choice=0;
    if (!z7_settings_files_init(&restore_files)) {
        __atomic_store_n(&restore_state,RESTORE_ERROR,__ATOMIC_RELEASE); return;
    }
    uint32_t result=z7_settings_files_read(&restore_files,0,record);
    if (result==Z7_STORAGE_IO_OK && checkpoint_grid_record_decode(record,80,&choice)) {
        restore_choice=choice;
        __atomic_store_n(&restore_state,RESTORE_READY,__ATOMIC_RELEASE);
    } else __atomic_store_n(&restore_state,
        result==Z7_STORAGE_IO_ABSENT ? RESTORE_MISSING : RESTORE_ERROR,__ATOMIC_RELEASE);
    /* Retained-close errors stay resident. No return-to-init failure/unload,
     * retries, saves, UI calls, scalar writes or label edits occur here.
     */
}
static uint32_t restore_display_staged, restore_menu_staged;
static uint32_t restore_stage_display(const struct z7_display_hooks *candidate)
{
    if (candidate != &checkpoint_hooks || restore_display_staged) return 0;
    restore_display_staged=1; return 1;
}
static uint32_t restore_stage_menu(const struct z7_grid_menu *candidate)
{
    if (candidate != &menu || restore_menu_staged) return 0;
    restore_menu_staged=1; return 1;
}
static const struct z7_module_api restore_staging={
    Z7_MODULE_ABI,sizeof(restore_staging),Z7_MODULE_TARGET,restore_stage_display,restore_stage_menu
};
static const struct z7_display_hooks restore_hooks={
    Z7_DISPLAY_ABI,sizeof(restore_hooks),grid_source,grid_geometry,0,0,before,restore_after
};
uint32_t z7_main(const struct z7_module_api *api)
{
    const struct z7_module_worker_api *worker=(const struct z7_module_worker_api *)api;
    if (!api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET ||
        api->size<sizeof(*worker) || !api->register_display || !api->register_grid_menu ||
        !worker->register_worker) return 1;
    if (restore_grid_initialize(&restore_staging) || !restore_display_staged || !restore_menu_staged) return 1;
    return api->register_display(&restore_hooks) && api->register_grid_menu(&menu) &&
           worker->register_worker(restore_worker) ? 0 : 1;
}
