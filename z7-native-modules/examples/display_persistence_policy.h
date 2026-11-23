/* SPDX-License-Identifier: MIT. Independent settings publication/worker policy.
 * Menu is the sole post-startup writer. Worker only reads atomic word snapshots.
 * Native renderer/menu task concurrency and physical scheduling remain open.
 */
#include "../plugins/settings_storage.c"
#include "../plugins/settings_files.c"
volatile uint32_t z7_settings_revision;
struct z7_settings_files z7_persistence_files;
struct z7_settings_storage_info z7_persistence_info;
volatile uint32_t z7_persistence_ready, z7_persistence_result, z7_persistence_attempts;
volatile uint32_t z7_persistence_saved_revision, z7_persistence_errors, z7_persistence_saves;
static uint32_t persistence_observed, persistence_quiet, persistence_retry;
static uint32_t persistence_state;
static void persistence_set_state(uint32_t state)
{
    __atomic_store_n(&persistence_state, state, __ATOMIC_RELEASE);
    persistence_menu_notify();
}
static uint32_t persistence_display_status(void)
{
    uint32_t state = __atomic_load_n(&persistence_state, __ATOMIC_ACQUIRE);
    if (state == PS_STARTING || state == PS_BLOCKED) return PD_BLOCKED;
    if (state == PS_SAVING) return PD_SAVING;
    if (state == PS_RETRY) return PD_RETRY;
    uint32_t revision = __atomic_load_n(&z7_settings_revision, __ATOMIC_ACQUIRE);
    uint32_t saved = __atomic_load_n(&z7_persistence_saved_revision, __ATOMIC_ACQUIRE);
    if ((revision & 1) || revision != saved) return PD_UNSAVED;
    return state == PS_DEFAULTS ? PD_DEFAULTS : PD_SAVED;
}
static const struct z7_settings_storage_io persistence_io = {
    &z7_persistence_files, z7_settings_files_read, z7_settings_files_write
};
static void persistence_commit(const struct z7_display_settings *staged)
{
#ifdef Z7_LCD_FIRST_RELEASE
    if (!staged) return;
    struct z7_display_settings filtered = *staged;
    if (!z7_lcd_release_filter(&filtered)) return;
    staged = &filtered;
#endif
    if (!z7_settings_valid(staged)) return;
    const uint32_t *source = (const uint32_t *)staged;
    uint32_t *destination = (uint32_t *)&z7_menu_settings;
    uint32_t changed = 0;
    for (uint32_t i = 0; i < sizeof(*staged) / 4; ++i)
        if (__atomic_load_n(destination + i, __ATOMIC_RELAXED) != source[i]) changed = 1;
    if (!changed) return;
    /* One GUI writer (or loader before GUI publication), worker only reads.
     * A fetch-add unnecessarily emits exclusive accesses. Publish odd first,
     * then fence before payload stores; final release publishes the even value.
     * This does not serialize multiple concurrent writers.
     */
    uint32_t revision=__atomic_load_n(&z7_settings_revision,__ATOMIC_RELAXED);
    if (revision & 1) return;
    __atomic_store_n(&z7_settings_revision,revision+1,__ATOMIC_RELAXED);
    __atomic_thread_fence(__ATOMIC_SEQ_CST);
    for (uint32_t i = 0; i < sizeof(*staged) / 4; ++i)
        __atomic_store_n(destination + i, source[i], __ATOMIC_RELAXED);
    __atomic_store_n(&z7_settings_revision,revision+2,__ATOMIC_RELEASE);
}
static uint32_t persistence_snapshot(struct z7_display_settings *out, uint32_t *revision)
{
    for (uint32_t attempt = 0; attempt < 3; ++attempt) {
        uint32_t first = __atomic_load_n(&z7_settings_revision, __ATOMIC_ACQUIRE);
        if (first & 1) continue;
        for (uint32_t i = 0; i < sizeof(*out) / 4; ++i)
            ((uint32_t *)out)[i] = __atomic_load_n(((uint32_t *)&z7_menu_settings) + i, __ATOMIC_RELAXED);
        __atomic_thread_fence(__ATOMIC_ACQUIRE);
        if (first == __atomic_load_n(&z7_settings_revision, __ATOMIC_RELAXED) && z7_settings_valid(out)) {
            *revision = first;
            return 1;
        }
    }
    return 0;
}
static void persistence_prepare(void)
{
    /* Runs once on loader task BEFORE native menu publication/host readiness.
     * No failing initializer operation may follow this I/O: any uncertain handle
     * and diagnostics must remain resident even when settings cannot be loaded.
     */
    if (!z7_settings_files_init(&z7_persistence_files)) {
        z7_persistence_result = Z7_STORAGE_INVALID;
        persistence_set_state(PS_BLOCKED);
        return;
    }
#ifdef Z7_PERSISTENCE_LOAD_OVERRIDE
    z7_persistence_result = Z7_PERSISTENCE_LOAD_OVERRIDE();
#else
    z7_persistence_result = z7_storage_load(&persistence_io, &z7_menu_settings, &z7_persistence_info);
#endif
    z7_persistence_ready = z7_persistence_result == Z7_STORAGE_LOADED || z7_persistence_result == Z7_STORAGE_DEFAULTS;
#ifdef Z7_LCD_FIRST_RELEASE
    if (z7_persistence_ready) persistence_commit(&z7_menu_settings);
#endif
#ifdef Z7_GRID_LAYOUT_PREFERENCES
    if (z7_persistence_ready) checkpoint_grid_value = z7_menu_settings.grid_layout;
#endif
    if (!z7_persistence_ready) ++z7_persistence_errors;
    persistence_set_state(!z7_persistence_ready ? PS_BLOCKED :
        z7_persistence_result == Z7_STORAGE_DEFAULTS ? PS_DEFAULTS : PS_CLEAN);
    z7_battery_enabled = !!(z7_menu_settings.flags & Z7_SETTINGS_BATTERY);
}
static void persistence_save_worker(void)
{
    /* Failed startup loading stays volatile for this boot; never save defaults
     * over an unread original or publish late worker writes into menu state.
     * A restart retries startup loading. Later save errors retry after5 ticks.
     */
    if (!z7_persistence_ready || z7_persistence_files.retained_fd != UINT32_MAX) return;
    struct z7_display_settings snapshot;
    uint32_t revision;
    if (!persistence_snapshot(&snapshot, &revision) || revision == z7_persistence_saved_revision) return;
    if (revision != persistence_observed) {
        persistence_observed = revision;
        persistence_quiet = 0;
        return;
    }
    if (persistence_quiet < 2) { ++persistence_quiet; return; }
    if (persistence_retry) { --persistence_retry; return; }
    ++z7_persistence_attempts;
    persistence_set_state(PS_SAVING);
    z7_persistence_result = z7_storage_save(&persistence_io, &snapshot, &z7_persistence_info);
    if (z7_persistence_result == Z7_STORAGE_SAVED || z7_persistence_result == Z7_STORAGE_UNCHANGED) {
        __atomic_store_n(&z7_persistence_saved_revision, revision, __ATOMIC_RELEASE);
        persistence_set_state(PS_CLEAN);
        if (z7_persistence_result == Z7_STORAGE_SAVED) ++z7_persistence_saves;
    } else {
        ++z7_persistence_errors;
        persistence_retry = 5;
        persistence_set_state(z7_persistence_files.retained_fd != UINT32_MAX ? PS_BLOCKED : PS_RETRY);
    }
}

static void persistence_worker(void)
{
    persistence_menu_notify();
    persistence_save_worker();
}
