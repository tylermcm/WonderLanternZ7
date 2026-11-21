# Original Z7 LCD first-release installation assessment

November 21, 2026. **Scoped software gates have passed for a controlled first
hardware trial. Owner authorization is recorded; the reviewed pair is staged
and the card safely ejected. Camera programming awaits the owner's operation.**
This is independent WonderLanternZ7 work for original Z7 C 3.80,
with private Nikon inputs and preserved component licenses. Hardware acceptance
and emergency recovery are unverified.

The smaller release includes the SD loader, six grids, four custom DISP presets,
native horizon, supported information controls, battery percentage, landscape
photo LCD focal text and settings persistence. Portrait, zebras, custom Info/
histogram and output extensions remain deferred. The broader port is unfinished.

## Exact candidate and recovery inputs

The API44 display-only host and release04 module are unchanged by the latest
harness work. Both were independently rebuilt twice; explicit updater review
reconstructs host AND module and rejects mixed/modified profiles. The frozen
owner-review bundle is private 20261121-lcd-trial-01.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| Candidate full EG161080.BIN | 33,058,862 | fa709dba7eb7a9addc8bd5b90f839edd578cfb6d4bb0df87a1cd8cb4a7beaa4d |
| Candidate Z7APP.BIN | 21,104 | aafb4b392203589e7dabc244d1d1e4b40a2c02023013621d9fc393328eb60e22 |
| Untouched stock EG161080.BIN | 33,052,090 | 7f59d8993080203a12692cf6927a0a8218786d3f72230c04174f1563c506a6f6 |
| Untouched stock Z_7_0380.bin | See private manifest | 07cf19513ada5b770caec4cfc3531a6734c48aede28dcec037f0f8374ef441a2 |

Candidate MAIN is 33,058,860 bytes, SHA-256
7d7356e7775db90483ed9fe5598f401afb7fb8498a7b42bd71900db849d7f057.
It matches the full EG prefix; MAIN alone is not an update file. Both EG CRC
residues are zero. Candidate size is below the original 43,253,760-byte descriptor
capacity. The stock-based host does not retain every earlier experiment. Displayed
version remains 3.80; that display alone cannot prove this host is installed.

## Scoped checks

| Check | Result |
| --- | --- |
| Native settings/save/restart | 58 checks, two fresh guests, 19 frames; compact navigation, edits, journal save and exact menu-region restoration |
| Native six-grid menu | 19 checks, seven frames; all selections/stored values, not a new shooting pixel test |
| Native focal rendering | 20 checks, 13 frames; values, absence, Other independence and background restoration |
| Combined settings/DISP | 47 instruction checks; filtering, skipping, save/restart and context fallback |
| Native base/horizon policy | 67 instruction checks; selection, restoration, conflicts and retry |
| Focal/battery policy | 45 and 38 instruction checks with scoped supplied services |
| Combined battery MENU/PLAY | 17 checks, 12 frames; display, restoration, adapter exclusion, MENU and no-card PLAY hiding/no sampling/return |
| Native bar converter | Three original-instruction cases; destination canaries and unchanged source cache |
| Updater header/filename | 12 selected original-instruction checks with supplied file/runtime properties |
| Repository suite | 86 tests pass, no skips |

All 12 battery-frame hashes/dimensions and captured probe/helper sources were
independently verified. The icon region restores exactly; this run also records
complete RGB restoration for the disabled-overlay comparison. Active and returned
battery frames were visually inspected.

The bar fixture supplies only two already-read typed inputs at the original
converter compare. Original conversion/stores, renderer, percentage getter and
module callbacks execute. No percentage, object, pixel or peripheral-completion
response is supplied. There were 98 input stops, all at the expected shooting
snapshot. Module/settings files, sensor inputs and focal lens properties remain
modeled. Earlier failed runs remain preserved; the later scoped UI pass does not
prove real telemetry, image playback or a complete physical sensor pipeline.

Hardware gaps remain: update acceptance/programming/boot, card I/O/cache coherence,
shutdown durability, lens/battery telemetry, capture, real image playback, output
switching, sleep/wake, simultaneous combinations and prolonged use. Emulator
success does not establish camera recovery.

## Camera and card evidence

The owner reports normal boot and most recent Z7 firmware. Nikon's
[current listing](https://downloadcenter.nikonimglib.com/en/products/492/Z_7.html)
is C 3.80, matching target. This interprets that report; no screen reading or
installed-image readback was obtained.

Read-only inspection identifies E: as Sony QD-G120F XQD, exFAT, label "NIKON Z 9".
Confirm this is the intended card for the ORIGINAL Z7 before any write. Its label
does not identify the installed camera firmware. Private inspection report
card-backups/20261121-sony-qd-g120f-01/inspection.json records stable identity.
Before staging, none of EG161080.BIN, Z_7_0380.bin, Z7APP.BIN, Z7CFG0.DAT or
Z7CFG1.DAT existed; the root BIN/DAT check found none. Zero files were backed up;
only the private inspection report was created. This is not an installed firmware
or calibration backup.

The owner then authorized: "yes go ahead, but keep the files intact". Only the
exact EG161080.BIN and Z7APP.BIN were added using exclusive creation, flushed and
fully hash-verified. All 217 existing user-file metadata records and the Nikon
catalog hash were unchanged; Windows system-volume metadata was excluded from
inventory. No existing files were overwritten/deleted/moved and no photo contents
were read. Windows safe eject completed and E: was verified unmounted. The
private staging/authorization record is card-staging/20261121-lcd-trial-01/staging.json.

## Proposed owner-operated trial, only after authorization

1. Recheck this same intended card and its contents. Preserve unrelated files.
   If new update/configuration files appeared, privately back them up and review
   the changed state before replacing anything. Fresh preferences are required
   so custom pages/battery start OFF. Use a charged camera battery.
2. Stage ONLY the exact candidate EG161080.BIN and Z7APP.BIN at the card root.
   Verify complete readback hashes, flush and safely eject. Keep rollback files
   off the trial card; do not put stock and candidate EGs there together.
3. The owner inserts it into the ORIGINAL Z7 C 3.80 and operates Setup > Firmware
   version > Update. If no update is offered or accepted, report it; do not guess
   filenames/headers or bypass admission. During programming, do not interrupt
   power, remove the card or operate it. Follow completion/restart instructions.
4. With custom pages/battery OFF, confirm rear-LCD menus and ordinary capture.
   Open Framing grid display > Display settings. Enable one feature at a time:
   grids/presets, horizon/information, battery, then focal. Check DISP, MENU and
   playback return after each. Compare readings with native camera information.
   Stop on unexpected behavior and preserve observations.
5. Check preferences after normal power-off/restart, then real image playback,
   native EVF/movie fallback and sleep/wake. Report results before prolonged use.
   These are hardware tests to perform, not established results.

## Recovery limits and authorization

Removing Z7APP.BIN before a later cold boot can prevent module initialization;
it does not unload a resident module or undo installed host firmware. Do not
interrupt programming to try this. Journals are preferences, not camera backups.
Physical loader/card timing and fallback remain unverified.

If boot and updater access survive, the exact private stock inputs above are
potential normal-updater rollback inputs. Nikon's
[official update page](https://downloadcenter.nikonimglib.com/en/download/fw/558.html)
describes its stock container and firmware through 3.70 as update inputs. It does
not establish acceptance of this extracted EG or same-version rollback from 3.80.
Selected instruction checks and prior trials are not an official recovery
procedure. **No emergency recovery is verified for an unbootable camera;
professional service may be required.**

The frozen pre-approval bundle retains emulator-only identities, offline review
limits and installation_cleared=false. Owner approval/staging is recorded
separately; camera update acceptance, completion and hardware results remain
unobserved. Card staging does not establish a successful camera update.
[AGENTS.md](AGENTS.md) requires explicit user authorization and this concrete
installation/recovery assessment before flashing.
