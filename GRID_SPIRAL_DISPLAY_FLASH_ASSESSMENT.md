# Gray LCD/EVF spiral: bounded hardware trial, October 27, 2026

## Owner outcome

The owner confirms the trial works, but reports conspicuous electronic level
lag in EVF, barely noticeable lag on the monitor, only when Golden ratio (the
spiral) is selected. This is a known performance regression; broad reliability
is not established. See `GRID_SPIRAL_RESEARCH.md` and
`evidence/20261027-grid-spiral-display-owner-hardware.json`. The current candidate
has no performance fix. Recovery limits below remain unchanged.

The owner requested matching the normal grid color and displaying the curve in
EVF, then explicitly authorized staging and a camera trial: "card is mounted
lets flash it". Target remains the owner's original Nikon Z7, C 3.80, without
the paid RAW-video upgrade. This is independent modified firmware.

## Exact candidate

- Full EG: **33,074,646 bytes**, SHA-256
  `c3cbb8fd4aaa932fc74cfd662cbfaac3f5471ea6ab81edb6148766d5a93449b6`.
- MAIN: **33,074,644 bytes**, SHA-256
  `7049b2120a9f88e3859a5d8ec335bb4858e6642ba9a278e5cd95474edf597543`.
- Fresh build: `.private/builds/20261027-spiral-display-flash-01/`.
- Review: `.private/flash-review/20261027-spiral-display-01/`.
- Installation filename: `EG161080.BIN`, full EG including its two-byte CRC.
  Version remains `03.80.00`; no version spoof or admission bypass is added.
- Original input: official Z7 C 3.80 container, SHA-256
  `07cf19513ada5b770caec4cfc3531a6734c48aede28dcec037f0f8374ef441a2`.

The six existing choices and internal grid encoding remain. Golden ratio adds
the curve; there is no separate spiral row. The curve is now gray RGBA
`(216,216,216,255)`. It follows the original Z7's component-1 active display
descriptor and exact registered bitmap: LCD 720x480, EVF 1280x960. It accepts
IDs 1/4 and refuses unsupported outputs, null, inactive, missing, ambiguous or
mismatched surfaces. Existing native graphics lock/select/draw/restore and the
post-widget paint hook remain. The original UI walker and return behavior are
preserved. No code from another camera, display-switch hook, new bitmap
allocation, new settings journal format, custom flash writer, sound, splash or
clean-display feature is included. Foreground placement remains accepted.

## Evidence and limits

The earlier identical image has a complete independent rebuild and CRC,
132 supplied-boundary instruction checks, 18 assisted LCD lifecycle checks,
nine verified screenshot hashes and nine native EVF-sized bitmap checks.
All 7,589 expected curve pixels exactly match gray in the raw native bitmap,
including 6,621 outside LCD-sized bounds. Native rows are bottom-up. This is
explicit supplied EVF routing and native decoding/drawing, **not physical EVF
scanout or eye-sensor switching**. LCD automatic drawing clears/returns through
two MENU roundtrips and disappears with 3x3/Off. Failed observation attempts
are retained and explained in `GRID_SPIRAL_RESEARCH.md`.

The fresh review independently reconstructs all MAIN/EG/report bytes with
`--preset grid-spiral-display`, checks the original container/modules/CRC/bounds
and selected original updater header/filename instructions. Its identity is
separate from the earlier yellow review. Admission regressions cover mixed,
modified, legacy and explicit-only artifacts. Relevant results and their scope
are recorded in `evidence/20261027-grid-spiral-display-flash-review.json`.

Physical update/boot, EVF output/transitions, DISP/playback, crop/rotation,
low-memory/assertion behavior, concurrency, repeated PNG decode cost, capture,
power/wake and prolonged performance remain unverified for this new image.
The existing bitmap requirement may refuse drawing during a transition; no
fallback to guessed buffers is used. A direct setting change outside MENU has
no dedicated erase hook. Emulator success does not establish safe programming
or recovery on a camera.

## Rollback and recovery

Keep separate private copies of the current owner-tested yellow full EG
(`52c593aff9895e31b4cfaf15ceb0335bdf4f26671d346dcb499080ea11c0f316`),
six-grid EG (`437e1f8edbb89f1409ad768dcf50e91725280481561fcaa8f0f161cc64e5dccc`),
owner-tested three-choice EG
(`07d77574bc9fed84d357b4e7c3df808127d361106c10ca26e0b6e2c818f6d0a7`),
untouched stock EG
(`7f59d8993080203a12692cf6927a0a8218786d3f72230c04174f1563c506a6f6`)
and official container. The card's current full EG must be backed up and hashed
before replacement. Never put candidate and rollback BINs on the card together.

If startup/menu/updater access survives, these are potential normal-updater
rollback inputs. Previous-loader journal compatibility is checked with supplied
OS/flash boundaries, not physical rollback. Selecting 3x3 or Off disables the
curve, but does not undo the firmware installation. Removing the card also
does not undo installed firmware.

**No emergency recovery is verified for an unbootable camera.** Professional
service may be needed after a failed update or boot. These are not full-camera
flash or calibration backups. The owner has explicitly chosen a bounded trial
with these existing recovery limits; no guarantee is implied.

## Installation and first test

1. Use the charged battery already confirmed by the owner. Set the current grid
   to **3x3** before starting the update so the curve is disabled at first boot.
2. Freshly identify the Sony XQD card, back up its current yellow EG, stage the
   reviewed full EG, flush and verify the final full hash. Preserve other files.
3. Safely eject in Windows, insert the card and use Setup > Firmware version >
   Update. The version is intentionally unchanged at 3.80. The owner operates
   the camera and starts programming after reviewing this candidate.
4. During programming, do not interrupt power, remove the card or operate the
   camera. Follow its completion/restart instructions.
5. Confirm normal 3x3/menu use on the rear monitor first. Select Golden ratio:
   check gray curve, MENU removal/return, then 3x3 removal. Return to Golden ratio
   and test EVF, then monitor, including MENU on each output. Report which output
   works and whether placement/color match. Stop the curve through MENU > 3x3/Off
   if behavior is unexpected while menus remain usable.

The first test is display validation. No new camera flash is reported complete
until the owner confirms it.

## Staging outcome

Fresh independent review passes all 12 selected original updater header/name
checks. The candidate exactly matches all files of the earlier tested build;
132 instruction, 18 LCD lifecycle and nine native EVF-bitmap results retain the
same MAIN hash. Nine LCD frame hashes and the native EVF raw bitmap hash verify.
Fresh previous-loader compatibility passes 18 checks, and all 23 root tests pass.

The expected Sony QD-G240F, serial `3335384A314B5230`, was freshly identified as
E: with the expected volume identity and writable, non-system USB partition.
The current yellow EG fully hash-matched and was backed up/read back at
`.private/card-backups/20261027-spiral-display-4d73d3a5/EG161080.BIN`.
The new full EG was staged through a flushed/hash-verified temporary file, then
renamed and fully read back at `E:\EG161080.BIN`: 33,074,646 bytes and the exact
candidate hash above. It is the only root BIN. Other root files, including WAV
and Nikon settings, retain their hashes and sizes. Photo directories were not
modified. No formatting, automatic ejection or camera operation occurred.

The card is ready for the owner-controlled bounded trial. Installation,
physical EVF success and recovery are still unverified for this candidate.
