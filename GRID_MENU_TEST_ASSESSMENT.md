# Battery plus six grid choices: SD test assessment

Owner subsequently approved "go ahead". Exact candidate staged, flushed,
readback/hash verified and safely ejected. Working thirds module preserved as
Z7APP.THIRDS-WORKING.disabled; earlier battery and all original trials intact.
227 existing metadata records/catalog/settings preserved except authorized rename.
No firmware update. Await ONE owner startup/grid-menu/layout/control/power-off
observation. Frozen preapproval bundle unchanged; this supersedes approval status.

November 21, 2026. Independent original Nikon Z7 C 3.80 checkpoint.
Prepared for owner review; no new card staging/test authorization yet.
Existing component MIT licenses and battery attribution retained.

## Exact candidate

`Z7APP.BIN`, 5,260 bytes. SHA-256:
`53334536d00ed18ea9d80d36dd736d6341fd1943da674f6e0fd513112f226195`.
Image 5,120 bytes, BSS 2,216 bytes, 19 relocations, entry offset 1,388.
Built twice identically. API20 minimum, tested on the already-installed API44
host MAIN hash `7d7356e7775db90483ed9fe5598f401afb7fb8498a7b42bd71900db849d7f057`.
Host installation is inferred from prior successful update, not physical readback.
No new firmware image or firmware update is part of this trial.

Keep battery percentage. Extend Nikon's existing Framing grid display page with
4x4 grid, 3x3 grid, Golden ratio (phi grid, not spiral), Center cross, 6x6 grid,
and Off. These layouts apply to rear-LCD photo view; EVF/movie rendering keeps
the stock table. EVF/menu/output transitions are outside this first test scope.

Layout choice is deliberately **volatile**. Nikon stores only its normal grid
On/Off value (1/0); the module never stores extended layout values. If native
grid remains On, a new cold startup defaults to 3x3. If Off, it stays Off.
Custom layout persistence remains required later for the actual LCD release.

The module prepares owned data and stages grid-page metadata through the host.
It writes no native GUI RAM during initialization. The installed host publishes
the two grid-page pointers on its existing GUI before-paint path only while the
grid page is inactive. The page's native rendering/activation adapters then use
module-owned metadata and volatile layout state.

There is no custom Display settings page, dispatcher/key replacement, settings
journal, resident worker, histogram-mask change, DISP hook or readout hook.
Native On/Off changes use Nikon's existing setter and camera-owned persistence.
This is separate from the withdrawn full-module and ownership-hardening builds.

## Software evidence and limits

270 checkpoint checks pass: no initialization GUI writes; pre-ready and active
page publication deferral; native GUI publication when inactive; six labels and
selection marks; owned menu event adapters; native stored values always 0/1;
stock visibility; fresh-load default; no custom page/dispatcher/key/mask changes;
EVF/movie stock grid fallback; failed initialization/registration clean up before
publication. 450 native geometry-builder calls compare layout results across
3 viewports, 3 modes and 5 crop inputs, including bounded golden-ratio spacing.
38 battery policy checks and 95 root tests pass. The previous grid variant is
byte-for-byte identical with the checkpoint flag absent.

UI services, page-list state, filesystem/kernel/storage, telemetry and viewport
inputs remain supplied. Actual menu widgets, label appearance, repaint timing,
task scheduling, physical pixels and recovery are unverified. Passing native
instruction tests did not predict the earlier full-module freezes. This new
candidate could freeze too. A different payload size also changes loading timing;
success does not establish the original freeze cause. Full release stays withdrawn.

## Proposed staging after explicit approval

Camera OFF, connect card to reader. Reidentify the same external card and privately
back up/readback named trial/configuration files. Verify current working
`Z7APP.BIN` is the 3,160-byte battery/thirds module:
`78af00b6fb9dd2cb29c2d391e1ce36412a25bd771a9f56ce02fdcd1e8ebadc91`.
Verify `Z7APP.BATTERY-WORKING.disabled` matches the earlier working battery hash
`89358992419867380781bafae7a1624f4d51955b3920127718f6daba9318ea23`, and verify
the four original disabled payloads against the previous assessments/staging logs.

Require EG161080.BIN absent, no unexpected active root BIN, and both names
`Z7APP.THIRDS-WORKING.disabled` and `Z7APP.GRID-MENU.disabled` absent. Stop on
identity/hash/name mismatch; never overwrite. Rename current working file to
`Z7APP.THIRDS-WORKING.disabled`. Exclusively add only the exact new `Z7APP.BIN`,
flush/fsync, read back/hash, verify all existing metadata/catalog except that
authorized rename, and safely eject. Preserve photos, settings and every trial.
No format, deletion, EG reenable, custom settings-file write or firmware flash.

## One owner test

1. Camera OFF: insert safely ejected card, turn on normally. Do NOT run Update.
2. Check battery percentage and ordinary controls on the rear photo LCD.
3. Open Framing grid display: expect the six entries listed above. Try 3x3,
   Golden ratio, Center cross, and 6x6, returning to live view to inspect each.
   Also check 4x4 and Off. Expected lines per axis: 3, 2, 2 at phi spacing, 1,
   5, and none respectively. Do not look for a new Display settings page.
4. Check MENU/touch and normal power-off. Stop this first trial here; no capture,
   movie, EVF/output switching, extended run or repeated restart test.

Report labels, visible layouts (including whether changes repaint), percentage,
responsiveness and normal shutdown. If labels/layouts are missing or stale but
controls work, report the mismatch; do not loop restarts or enable other trials.
A pass clears only this checkpoint's observed scope.

## Stop and preservation/recovery

If frozen, stop. Card removal previously restored inputs; an unresponsive switch
previously required battery removal. If normal power-off cannot work during this
ordinary-startup test, use that previously used shutdown method, remove the card
before restarting, and report symptoms. Recovery for this exact candidate is not
physically verified or guaranteed. Do not flash or repeatedly start with it active.

Return card to reader for hash-verified rename of the failed candidate to
`Z7APP.GRID-MENU.disabled` only if absent, preserve files/metadata/catalog and
safely eject. Do not automatically restore another active module. Both working
baselines remain preserved for an explicitly agreed restoration. Disabling this
SD module does not uninstall the modified host; firmware rollback and emergency
recovery remain unverified and are not part of this trial.

Preparing this assessment does not authorize staging or a camera test.
