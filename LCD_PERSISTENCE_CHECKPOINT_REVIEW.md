# LCD preference save/restore checkpoint - November 22, 2026

Prepared offline while the owner is away. No card access or firmware update.
This independent original-Z7 C 3.80 module combines the owner-tested LCD grid
policy with the existing exclusive-free display-preference journal policy.
It is a new hardware candidate, not a hardware-validated release.

## Exact candidate and working baseline

Candidate Z7APP.BIN: **21,296 bytes**, SHA-256
`88b53ce46ae816b634c249cfe011f05a501f2619447d9c156e2828c2cf82a71e`.
Source: `z7-native-modules/plugins/lcd_persistence_checkpoint.c`.
Private reproducible build: `.private/builds/20261122-lcd-persistence-bool-01`.
Frozen package: `.private/review/20261122-lcd-persistence-bool-01`.

Preserve the current owner-working 18,060-byte module, SHA-256
`8ec66cea22ebf33755944591351d7d7f4c728e361af2b2bd7794323a72ef52ea`.
It independently rebuilds byte-for-byte after these tooling changes.
The required host is the previously owner-tested worker-task revision, MAIN SHA-256
`24b2074559ca6089432011d98a72193f81e112c2621aee2aa0ed1359febfa7ce`.
The host is unchanged; no new firmware image is needed. The installed host was
inferred from the approved successful update, not physically read back.

## Saved preferences and grid contract

The unchanged v1 preference journal saves Custom pages, enabled DISP pages,
each page's supported grid/horizon and information-group switches, battery
percentage and focal-display preferences. It uses only `A:\Z7CFG0.DAT` and
`A:\Z7CFG1.DAT`, two alternating 80-byte records with CRC and generation checks.
Edits publish from the GUI; the loader worker observes a complete snapshot,
debounces it, saves the other slot and reads it back before acknowledging Saved.
An uncertain close latches saving off until restart. Startup read failures block
saving for that boot rather than replacing unread preferences with defaults.

Grid **visibility within a DISP preset** is a saved preference. The selected
**grid shape** remains in module RAM and defaults to 3x3 when native grid is On
at startup. Legacy native values 2..5 are read without an initialization rewrite;
an explicit shape selection sends only native Off/On (0/1). No grid-layout field
has been added to v1, and `Z7GRID.DAT` is not read or changed by this module.
This is an incremental save/restore checkpoint; grid-shape persistence remains
unfinished release work. EVF/movie behavior remains the native fallback.

Compared with the working storage-free LCD profile, this candidate adds startup
journal reads, the existing menu save-status dispatcher/notification binding,
worker registration and journal writes after preference changes. The worker
notifies the native event flag; it does not render labels. Native menu task
ownership and file-service execution are still physical test boundaries.

## Offline checks

- Reproducible build and independent exact rebuild; 83 ELF-bounded functions,
  zero LDREX/STREX/CLREX instructions and 19 DMB instructions. Native callees are
  outside the module scan.
- 48 LCD checks: compact menu/actions/defaults, legacy filtering, preference
  save/restart, battery/focal switches, native DISP cycling and context fallback.
- 262 grid/storage checks and 450 geometry comparisons: native setter arguments
  only 0/1, legacy inputs, all layout choices, menu selection and EVF/movie fallback.
- Actual GUI writer paused after its odd revision store: four separate-stack
  worker reads return without I/O/spinning; writer resumes with ABI preserved
  and the completed revision is saved.
- 69 exact-candidate fault/restart checks: idle defaults cause no write,
  alternating slots and restart restore, startup open/read/close failures,
  create retry/backoff, short-write fallback and uncertain-close latch.
- 15 native menu-status checks: native event-flag notification, original
  dispatcher and empty-queue path, owned-page title refresh and foreign-page
  notification/paint exclusions.
- 101 root regression tests pass. Graphify is refreshed locally; conditional-C
  parser gaps remain, so the graph is an exploration aid rather than a verifier.

The frozen package manifest identifies the full set of passing reports.
These are instruction fixtures with supplied
filesystem, scheduler and rendering boundaries. They do not establish physical
write durability, shutdown flush, image capture, pixels or camera recovery.

## Installation, preservation and recovery assessment

No card write or test has been authorized for this exact package yet. On return,
review the staged-test scope with the owner before copying. Identify the same
Sony card and verify its current active module against the working baseline.
Inventory all existing file sizes/timestamps and the catalog; privately back up
and verify named payloads, seed and configuration files. Never format/delete.

For the first controlled trial require BOTH journal paths to be absent. If
either exists, preserve it and stop staging this trial until its contents and
the revised test scope are reviewed. A legacy journal can trigger automatic
normalization saving even without a new menu edit; the absent-journal gate
keeps the initial startup trial read-only at the module settings-file layer.

Rename the active working module to an unused
`Z7APP.LCD-GRID-BOOL-WORKING.disabled`, then exclusively create the candidate as
`Z7APP.BIN`. Keep every historical module, seed and updater intact and keep all
updaters disabled. Flush/full-readback verify the candidate, verify all prior
contents/metadata/catalog through the intended rename, and safely eject. An
existing preservation-name collision must stop staging rather than overwrite.
Do not place a firmware updater on the active path or run Update.

If a problem occurs, stop the trial. Card removal recovered controls in earlier
failures; some required battery removal. That history does not guarantee this
candidate's recovery or filesystem durability. Before another test, privately
back up any new journals, preserve/disable the trial module, and restore the
exact working module on the laptop with flush/readback verification. Leave
new journals intact; the storage-free working module ignores them. An SD module
rollback does not change the installed host firmware. No stock firmware recovery
or exact-candidate recovery has been physically established.

## Proposed owner tests, one gate at a time

1. **Startup only:** camera OFF, insert card and start normally. Do not run
   Update or change preferences. Open Display settings; expect Defaults. Check
   MENU, touch, responsiveness and normal power-off. Report before any write test.
2. **One saved preference after the startup gate passes:** enable only Battery
   percentage. Observe Unsaved/Saving then Saved; a later native menu event or
   reopening the page may expose the updated title. Do not power off while it
   says Unsaved, Saving, Save retry or Restart to save. If Saved never appears,
   stop/report instead of repeatedly toggling. After Saved, normal power-off and
   cold-start should restore Battery ON. Check controls and normal power-off.
3. Only after that result, return the card for private journal decode/CRC/
   generation inspection. Further DISP preference or second-slot write tests
   should be chosen from the observed result. Do not add capture/EVF tests here.

These are proposed tests, not an automatic authorization or durability claim.
The owner-working card remains unchanged during offline preparation.
