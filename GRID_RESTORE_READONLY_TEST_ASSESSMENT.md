# Read-only grid restore: SD test assessment

November22: owner approved restoration of the earlier working six-grid/battery
module. Exact5260-byte SHA53334536...12f226195 now active; failed restore code,
seed and every baseline preserved. Full readback/metadata/catalog/safe eject
verified. Owner has not tested restored card yet. No firmware change. Separate
offline worker-guard findings are in WORKER_GUARD_FAILURE_REVIEW.md.

**WITHDRAWN: hardware test FAILED.** Owner reports the same input/power freeze,
card-removal recovery and battery pull. Owner confirms camera normal without card.
Failed module now preserved as Z7APP.RESTORE-RO.disabled; all nine named files
and inert seed hash-verified/backed up, metadata/catalog preserved and safe eject
verified. No active root BIN remains. Owner saw the percentage while controls were already frozen; no prior responsive
interval or SD marker established. Worker/read execution and cause unproven.
No further file-I/O trial or flash. Frozen bundle remains intact with adjacent
withdrawal record. See evidence/20261121-grid-restore-readonly-hardware-result.json.
Restoration of the previous working six-grid payload requires explicit approval;
it has not been performed. This supersedes all pending/success-gate wording below.

Owner subsequently approved "go ahead". Exact module and seed now staged,
flushed/readback/hash verified and safely ejected. Working six-grid module
preserved as Z7APP.GRID-MENU-WORKING.disabled; all prior baselines/trials/settings
intact.228 existing metadata records/catalog preserved except authorized rename.
No firmware update. Await ONE owner marker/layout/control/power-off result.
Frozen preapproval bundle unchanged; this supersedes pending approval status.

November 21, 2026. Independent original Z7 C 3.80 checkpoint, prepared for owner
review only. No new staging or camera-test authorization. Existing MIT notices
and battery attribution retained. This is the read half of persistence;
camera-side saving is NOT implemented in this checkpoint.

## Exact two-file candidate

`Z7APP.BIN`: 6,628 bytes, SHA-256
`0714fe8491b4e802406ed0867f0c5ecacc3ceb4c573feecceb742364b2c4bf95`.
Image 6,464 bytes, BSS 2,260 bytes, 25 relocations, entry offset 2,164.
`Z7GRID.DAT`: 80-byte canonical seed selecting 6x6, SHA-256
`a0b38b760a81b292131af5944fa3ade0ce48bc9e21e9a424b712dc2368567ae0`.

The module was built twice identically. It uses the already-installed API44 host,
MAIN hash `7d7356e7775db90483ed9fe5598f401afb7fb8498a7b42bd71900db849d7f057`.
Installed identity is inferred from prior installation, not physical readback.
No new firmware image or firmware update is proposed.

Keep the working battery/six-grid feature set. Add one resident worker: it waits
until an eligible GUI callback has sampled/displayed the battery object, then
attempts one read of `A:\Z7GRID.DAT`. This is a GUI-progress condition, not a
native card-ready query. It validates size, magic, version, CRC, reserved bytes
and choice range. The file-write function is excluded at compile time.
No Z7CFG0/1 journals, custom settings page, dispatcher/key replacement, histogram
mask changes or extended native grid values are introduced.

The worker publishes a result only; it does not edit UI labels, apply a layout,
call the On/Off setter or paint. On the next native grid-menu entry, the GUI
applies the seed to module memory if no layout has been selected meanwhile.
The loaded row becomes `6x6 [SD]`. That marker requires successful file read,
decode and GUI application. Choosing it displays the dense grid through the
same native On/Off path as the working six-grid checkpoint.

Missing/invalid/error results preserve default 3x3 and mark the Off row as
`Off [SD miss]` or `Off [SD error]`. A user choice made before application wins;
the Off row shows `Off [SD skip]`. There are no retries for that boot. Failed
close leaves the uncertain handle and module allocation resident; initialization
has already succeeded, so there is no error-path unload of that context.

The seed is never changed by the module. Choosing another layout does NOT save
it for the next startup. This tests read-only restore of a laptop-supplied seed,
not completed persistence. EVF/movie rendering remains stock as before.

## Evidence and limits

52 restore/fault/preemption checks pass, including compiled record decoding,
waiting for GUI progress, one read, missing/short/long/corrupt/error cases,
retained-close residency, no retries/writes, and a compiled GUI selection on a
separate emulated stack winning over a paused read. The exact candidate also
passes 270 menu/geometry checks (450 native builder calls), 38 battery checks and
99 root tests. The working six-grid variant still builds byte-for-byte identically.

Kernel/filesystem dispatch, incoming GUI/telemetry/render services and the normal
On/Off UI service remain supplied. No real card readiness, native scheduler,
pixels, physical cold startup or recovery is established. Native file calls are
synchronous: this module cannot cancel or time out a blocked native call.
Returned errors are handled conservatively; a native service could still hang
and reproduce the previous control/power freeze. Prior passing software checks
did not predict those freezes. Full LCD release stays withdrawn.

## Staging after fresh explicit approval

Camera OFF; connect card to reader. Reidentify the same external card and privately
back up/readback all named payload/configuration files. Require active working
`Z7APP.BIN` to match the 5,260-byte six-grid hash
`53334536d00ed18ea9d80d36dd736d6341fd1943da674f6e0fd513112f226195`.
Verify the six earlier disabled payloads against their staging records: both
working battery/thirds baselines plus four original trials. Require EG161080.BIN
absent and no unexpected active root BIN files.

Require `Z7GRID.DAT`, `Z7APP.GRID-MENU-WORKING.disabled`, and
`Z7APP.RESTORE-RO.disabled` absent. Stop if any already exists, any identity/hash
differs, or any filename collides; do not overwrite or rename unknown user data.
Preserve working module by rename to `Z7APP.GRID-MENU-WORKING.disabled`.
Exclusively add only the exact new `Z7APP.BIN` and `Z7GRID.DAT`, flush/fsync,
read back/hash both, verify existing metadata/catalog except authorized rename,
then safely eject. Preserve all photos/settings/trial files. No format, deletion,
EG reenable, firmware flash, or existing settings-file change.

## One owner check

1. Camera OFF: insert safely ejected card, start normally. Do NOT run Update.
2. Rear photo LCD: confirm percentage and responsive controls. Wait up to
   30 seconds before choosing a layout so the one read can complete.
3. Open Framing grid display. Look for `6x6 [SD]`. If present, choose it and
   confirm five lines per axis. The native On/Off setting may initially be Off;
   the marker, not its initial selection mark, proves the read.
4. Check MENU/touch and normal power-off. Stop this first trial here: no extra
   restart/capture/movie/EVF/output/long-run test.

Report the exact marker (loaded/miss/error/skip/none), grid appearance, percentage,
controls and normal power-off. No marker is inconclusive; do not loop restarts.
An error marker with working controls is useful fault evidence, not a restore pass.
Do not expect later menu choices to be saved by this read-only build.

## Stop/recovery and preservation

If frozen, stop. Previously, card removal restored inputs and an unresponsive
switch required battery removal. If normal power-off is impossible in this
ordinary-startup test, use that previously used shutdown method, remove card
before restarting, and report symptoms. Exact-candidate recovery remains
physically unverified and is not guaranteed. No flash or repeated active-card boot.

Return card to reader for hash-verified rename of the failed module to
`Z7APP.RESTORE-RO.disabled` only if absent. Leave the inert seed intact and
preserve all bytes/metadata/catalog before safe eject. Do not automatically
restore another active module. The working six-grid baseline remains preserved
for an agreed restoration. Disabling SD code does not uninstall the modified
host; firmware rollback/emergency recovery remain unverified and out of scope.

This assessment alone does not authorize staging or a camera test.
