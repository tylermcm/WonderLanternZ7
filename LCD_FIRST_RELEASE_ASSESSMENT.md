# Original Z7 LCD first release assessment

November 21, 2026. **Installation remains on hold.** This assessment identifies
the software under test; it does not clear a camera update.

The owner confirms normal boot and the most recent Z7 firmware. Nikon currently
lists C 3.80 on its [Z7 download page](https://downloadcenter.nikonimglib.com/en/products/492/Z_7.html),
matching this lab's target. This interprets the owner's report; no firmware-screen
reading or installed-image readback was obtained. Windows disk/volume inventory
shows only the internal C: disk, so current card files and rollback backups cannot
yet be checked. No card contents were read or written.

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
Both were independently rebuilt twice. The explicit LCD updater review now
independently reconstructs this display-only host and the first-release module,
requiring exact packet/report agreement. Mixed profiles, advanced hosts and
modified artifacts are rejected. MAIN alone is not an update file.

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
The exact six-choice native grid menu passes 19 checks across seven frames,
selecting Fourths, Thirds, Golden, Center, Dense and Off with the expected native
stored values. This is selection/menu evidence, not a new shooting pixel test.
The existing battery instruction audit now also passes 38 checks on this exact
combined profile, enabled through its compact native menu callback. Sampling,
palette preservation, ownership, retirement and unsupported contexts execute
compiled module/native helpers with supplied icon/telemetry/mutex/render
services. This does not clear native visual MENU/PLAY integration or hardware.

Battery drawing, its native icon-region restoration and adapter exclusion pass
before the native MENU call stops QEMU on an unmodeled write to `0x10000aaa`
(guest PC `0xa2a40652`). Preserve private `lcd-shooting-battery-01` as failed;
PLAY was not reached. This does not establish a release defect or clear MENU.
The battery-only control on the SAME host passes 15 checks/12 frames, including
native MENU and no-card PLAY return. It does not prove the combined profile.
Measured-ready run01 failed because no eligible percentage appeared. Run02's
saved baseline visibly contains the adapter glyph; it was intentionally stopped
after identifying an invalid request baseline, not counted as a lifecycle pass.
Battery-auto had checkpointed AFTER supplying its icon request, allowing native
tasks to overwrite it. The existing settings-battery integration explicitly
avoids that ordering. The current run03 reuses that ordering and qualifies the
actual native battery glyph (up to three labeled requests, all frames retained).
It also pumps the persistent file-service observation point during free runs
using the established persistence-probe wait. Pipeline readiness is measured.
Run03 fails its six-attempt measured pipeline-readiness gate before rendering
or MENU tests; it cannot validate the corrected icon request path. Do not rerun
blindly or count this as a feature failure/pass. Inspect its RAW/ISP/scanout
observations first. No successful device response or framebuffer is supplied.

Inspection confirms RAW advances while ISP remains at one frame and processed
scanout is absent in run03. Battery's compiled context guard instead depends on
native LCD/photo/menu/pool/font/icon ownership. The isolated `lcd-battery-ui-01`
therefore records sensor health without claiming a pipeline pass and qualifies
those UI dependencies. It FAILS native battery-glyph qualification after three
labeled requests; MENU/PLAY are not reached. Preserve that failure. Original
snapshot conversion at 10368564..103685AA rebuilds the bar from an incoming
cache type/value, with default bar6; the run starts at bar6 (adapter). One-time
snapshot/icon requests are not yet a stable native battery-input fixture. Do not
patch native objects/pixels or describe this failure as hardware telemetry proof.

A private held snapshot `20261121-lcd-first-release-01` preserves the full EG,
MAIN, module and build reports with readback hashes. Full EG is 33,058,862 bytes,
SHA-256 `fa709dba7eb7a9addc8bd5b90f839edd578cfb6d4bb0df87a1cd8cb4a7beaa4d`;
MAIN matches its prefix and full EG CRC residue is zero. This is an artifact
freeze with explicit holds, not an installation-approved review bundle.

Private `20261121-lcd-updater-review-02` independently reconstructs the full EG
and module and verifies six private bundle files by readback. Twelve selected
original-updater instruction checks pass: stock/candidate headers under both
modeled version-property values, invalid size/version rejection and exact
filename acceptance/rejection. Use `EG161080.BIN` for the full EG and
`Z7APP.BIN` for the SD module. The candidate is below the original descriptor's
43,253,760-byte capacity. These checks supply file I/O and runtime properties;
they do not execute full updater admission, erase/program/readback or real boot.
Same-version acceptance on the camera and emergency recovery remain unverified.
The report records its review-source hash, retains emulator-only identities and
`installation_cleared=false`. Review01 is an earlier preserved snapshot.

Untouched stock EG in the review is 33,052,090 bytes, SHA-256
`7f59d8993080203a12692cf6927a0a8218786d3f72230c04174f1563c506a6f6`.
It is a specific normal-updater rollback input if boot and updater access
survive; it does not establish emergency recovery or preserve prior experiments.

## Requirements before staging

1. Finish the focused combined-profile shooting gate and retain failed results.
2. The explicit independent reconstruction and selected updater checks above
   are complete. Preserve their limits when reviewing the remaining hardware
   acceptance questions; do not relabel emulator artifacts as hardware-tested.
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
Before a first trial, back up any existing `Z7CFG0.DAT`/`Z7CFG1.DAT` off the card
and use fresh defaults, so old preferences cannot enable overlays on first boot.
Preserve those originals; do not silently replace or discard them.

If the camera still boots and its updater works, a reviewed previous full EG
may allow normal-updater rollback. Removing the module/card does not undo
installed host firmware. The two settings journals are preferences, not a
firmware or calibration backup. **No emergency recovery is verified for an
unbootable camera; professional service may be required.**
Nikon's [official update page](https://downloadcenter.nikonimglib.com/en/download/fw/558.html)
describes its stock container and firmware versions through 3.70 as update
inputs. It does not establish acceptance of this lab's extracted EG or a
same-version rollback from C 3.80. Prior lab trials and selected instruction
checks must not be presented as an official recovery procedure.

After a separately authorized installation, start with custom pages and battery
off. Confirm ordinary rear-LCD shooting/menu operation, then enable one feature
at a time. Check DISP, grid/horizon, MENU/PLAY return, save/restart and normal
capture. EVF/movie transitions should retain native behavior with unsupported
overlays withheld; successful emulator fallback does not prove physical output
switching. Stop testing on unexpected behavior and preserve observations before
choosing any rollback. No automated camera programming is part of this review.
