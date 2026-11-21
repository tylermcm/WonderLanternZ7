# Original Z7 LCD first release assessment

November 21, 2026. **Installation remains on hold.** This assessment identifies
the software under test; it does not clear a camera update.

The selected scope is the SD loader, six native grid choices, four custom DISP
presets, native horizon, supported information controls, battery percentage,
supported LCD focal text and two-slot settings persistence. Portrait, zebras,
custom Info/histogram and output extensions are deferred.

The exact host is private `20261121-lcd-core-host-01`, API44, display hooks only.
Its MAIN is 33,058,860 bytes, SHA-256
`7d7356e7775db90483ed9fe5598f401afb7fb8498a7b42bd71900db849d7f057`.
The exact module is private `20261121-lcd-first-release-04/Z7APP.BIN`,
21,104 bytes, SHA-256
`aafb4b392203589e7dabc244d1d1e4b40a2c02023013621d9fc393328eb60e22`.
Both were independently rebuilt twice. These are emulator artifacts. The
complete host EG and its hash must be independently reconstructed and reviewed
before it can become an installation input; MAIN alone is not an update file.

Native settings navigation, compact rows, reset, save and fresh-guest reload
passed 58 checks across two guests and 19 frames. Exact menu regions match
after restart. The combined focal rendering test passed 20 checks across 13
frames, including fractional/whole values, lens absence, independent Other,
component off and master off with native background restoration. Lens values
and module/settings filesystem services are supplied. This proves neither
physical lens telemetry nor card durability. The combined instruction audit
passes 47 checks including native DISP cycling, disabled-page skipping and
movie/EVF/menu fallback. The focal instruction lifecycle audit passes 45 checks.
These supply incoming context and OS/render services and are not physical-output
tests. The exact combined profile also passes 67 native base-page instruction
checks covering horizon selection, master-off restoration, conflicting state,
failed setter/restore retry and unsupported menu/movie/output fallback.

Battery drawing, its native icon-region restoration and adapter exclusion pass
before the native MENU call stops QEMU on an unmodeled write to `0x10000aaa`
(guest PC `0xa2a40652`). Preserve private `lcd-shooting-battery-01` as failed;
PLAY was not reached. This does not establish a release defect or clear MENU.
The next investigation is a bounded comparison with the existing diagnostic
profile to distinguish the original guest device path from a combined-profile
regression. Do not invent a successful device response merely to pass the gate.

A private held snapshot `20261121-lcd-first-release-01` preserves the full EG,
MAIN, module and build reports with readback hashes. Full EG is 33,058,862 bytes,
SHA-256 `fa709dba7eb7a9addc8bd5b90f839edd578cfb6d4bb0df87a1cd8cb4a7beaa4d`;
MAIN matches its prefix and full EG CRC residue is zero. This is an artifact
freeze with explicit holds, not an installation-approved review bundle.

## Requirements before staging

1. Finish the focused combined-profile shooting gate and retain failed results.
2. Independently reconstruct the full EG from the pinned private stock input;
   verify every intended edit, retained tail, bounds, CRC, version and original
   updater filename/header admission. Extend the review tool to explicitly
   recognize this host; do not relabel an emulator report to bypass admission.
3. Freeze full EG, module, reports and hashes together. Review loader startup
   timing, native file/cache operations and missing/bad-module fallback with
   their remaining physical limitations. A stock-based host changes installed
   firmware and must not be represented as retaining all previous experiments.
4. Identify the current camera firmware and card, preserve and hash the card's
   existing update/module/settings files, and identify a specific rollback EG.
   Earlier owner-tested images are historical options, not a verified current
   backup. Preserve unrelated card files.
5. Present that exact bundle and recovery limits for explicit user authorization.
   No staging or camera update has been authorized by passing these checks.

## Installation and recovery limits

Any later authorized trial requires a charged battery, the reviewed full EG
under the original updater's verified filename, and the module under its exact
loader filename. Stage only the selected update EG, verify its full readback
hash and safely eject. The owner operates the camera updater. The current
candidate's actual updater acceptance and boot behavior are unverified.

If the camera still boots and its updater works, a reviewed previous full EG
may allow normal-updater rollback. Removing the module/card does not undo
installed host firmware. The two settings journals are preferences, not a
firmware or calibration backup. **No emergency recovery is verified for an
unbootable camera; professional service may be required.**

After a separately authorized installation, start with custom pages and battery
off. Confirm ordinary rear-LCD shooting/menu operation, then enable one feature
at a time. Check DISP, grid/horizon, MENU/PLAY return, save/restart and normal
capture. EVF/movie transitions should retain native behavior with unsupported
overlays withheld; successful emulator fallback does not prove physical output
switching. Stop testing on unexpected behavior and preserve observations before
choosing any rollback. No automated camera programming is part of this review.
