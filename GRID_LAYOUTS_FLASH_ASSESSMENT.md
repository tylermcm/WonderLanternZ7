# Six-choice grid hardware-test preparation — October 27, 2026

## Card staging completed

After the offline preparation, the owner connected the card and confirmed it
was mounted in response to the staging request. The Sony QD-G240F was freshly
identified as the same USB/XQD volume at E:. The old full EG matched the
owner-tested three-choice image and was copied to
`.private/card-backups/20261027-grid-layouts-951c3dab/EG161080.BIN`, with its
complete hash verified before replacing the card file.

`E:\EG161080.BIN` now holds the exact candidate below: 33,056,174 bytes,
SHA-256 `437e1f8edbb89f1409ad768dcf50e91725280481561fcaa8f0f161cc64e5dccc`.
It is the only root `.BIN`. Temporary-copy and final-file hashes passed.
The non-firmware root inventory, settings marker and WAV hashes remained
unchanged. No photo folder was modified, no formatting/deletion was performed,
and the card was not automatically ejected. Camera programming has not started.

This assessment covers the exact independent original Z7 C 3.80 build below.
The owner requested preparing a flash with the new grids. The offline phase
created private files on the laptop; staging occurred subsequently as above.
The body last identified by the owner is an original Z7 C 3.80 without Nikon's
paid RAW-video upgrade. Reconfirm that target and supported power before use.

## Included behavior

The native d9 Framing grid display menu has six choices:

- 4x4 grid
- 3x3 grid
- Golden ratio (straight phi-grid lines near 38.2% and 61.8% of each span)
- Center cross
- 6x6 grid
- Off

The selected choice is intended to persist in the existing internal setting
until changed or reset by normal settings operations. There is no expiry timer.
Off stores zero and forgets the prior type. Existing values 0/1/2 retain their
Off/4x4/3x3 meanings; new values 3/4/5 identify Golden ratio/Center cross/6x6.
No settings migration or added journal record is required in the tested paths.

The Fibonacci curve is excluded. It currently has only an explicit diagnostic
draw entry; automatic repaint/removal has not been integrated. Sound, splash,
dual-display and the held 90-record settings experiment are also excluded.

## Exact private installation input

Fresh build: `.private/builds/20261027-grid-layouts-flash-01/`.
Review bundle: `.private/flash-review/20261027-grid-layouts-01/`.
Convenient candidate: `.private/flash-ready/20261027-grid-layouts/EG161080.BIN`.

- Full EG component: **33,056,174 bytes**, SHA-256
  `437e1f8edbb89f1409ad768dcf50e91725280481561fcaa8f0f161cc64e5dccc`.
- MAIN for emulation: **33,056,172 bytes**, SHA-256
  `6485b0a579eb469701bcb89c442ab6b7faa1cea748dd3716cc524e500595b97f`.
- Five guarded stock edits total 44 bytes; 4,084 bytes appended.
- Original version bytes remain `03.80.00`. The filename is `EG161080.BIN`.
  No version spoofing or updater-admission bypass is added.
- The full EG retains the two-byte CRC. The MAIN file is not the installation
  file, and the candidate is not a repacked official Nikon outer container.

The complete fresh EG and report match the previously tested six-layout
candidate 02 exactly. The stock input is the pinned original `Z_7_0380.bin`:
34,472,614 bytes, SHA-256
`07cf19513ada5b770caec4cfc3531a6734c48aede28dcec037f0f8374ef441a2`.

## Verification

- Repeated independent full-image/report rebuild, exact comparison against
  tested candidate 02, complete EG CRC and read-back hashes pass.
- A fresh execution of all **484 instruction checks** passes on this build,
  including native property/flag comparisons, geometry/crop combinations,
  all six choices, native saves/fresh-RAM reloads and selected failure cases.
- Earlier assisted QEMU evidence for this identical MAIN passes **22 menu and
  13 live-view checks**. The images, recorded payload hashes and check results
  are retained privately and verified for this preparation. QEMU was not rerun
  just to test an identical binary under a new directory name.
- **18 additional previous-build compatibility checks** pass. For each newly
  saved value 3, 4 or 5, a fresh instance of the owner-tested three-choice image
  loads all 89 journal payloads without writing flash, treats the unknown grid
  as Off, and can select/save/reload 3x3 again. Unrelated records are preserved.
- The exact full candidate and untouched stock component pass **12 selected
  original updater header/filename probes**. Official-container bounds, all
  four component CRCs, outer CRC/trailer and private copies also pass.
- All **17 root tests**, including eight review-helper tests, pass. The new
  `grid-layouts` review selection requires an independent six-choice rebuild;
  the old `grid-native` mode still rejects it. A spiral diagnostic report or
  mixed candidate files cannot substitute for the reviewed six-choice input.

The instruction fixtures supply OS/event, flash-controller and selected UI
boundaries. Header probes supply file I/O and runtime-property results. These
tests do not execute physical programming, complete card enumeration, every
indirect property consumer or emergency recovery. See `GRID_LAYOUTS_RESEARCH.md`
and `evidence/20261027-grid-layouts-flash-review.json` for scope.

## Installation and rollback assessment

The owner reported previous same-version component installations on this body,
including the earlier three-choice saved-grid image. That is useful precedent,
not proof that this new candidate will be accepted or boot correctly.
[Nikon's official C 3.80 page](https://downloadcenter.nikonimglib.com/en/download/fw/558.html)
does not certify this independently modified, same-version component.

The review bundle keeps three alternatives separate from the new candidate:

- The previously working three-choice full EG, 33,054,026 bytes, SHA-256
  `07d77574bc9fed84d357b4e7c3df808127d361106c10ca26e0b6e2c818f6d0a7`.
- Untouched original EG, 33,052,090 bytes, SHA-256
  `7f59d8993080203a12692cf6927a0a8218786d3f72230c04174f1563c506a6f6`.
- The untouched official container identified above.

If normal boot and updater access remain usable, these are potential rollback
inputs. Actual same-version rollback to them is not physically verified. After
returning to the previous three-choice image, a newly saved value 3/4/5 appears
as Off in the tested menu/visibility paths; explicitly select 3x3 or 4x4 again.
The 89-record journal format is unchanged. Stock also treats the new values as
Off in the selected tested consumers. This is not exhaustive compatibility.

**There is no verified local emergency recovery for an unbootable Z7.** These
files are not a full flash/calibration backup. Removing the card does not undo
installed firmware. A failed update/boot could require professional servicing.
The [official update guide](https://download.nikonimglib.com/archive3/jFBMN00KI4Ix03x9LuU85FxJko41/Z-series_FirmUp_Win_En.pdf)
directs an inoperable device after a failed update to authorized service; it
does not supply a proven recovery path for this build.

## Hardware sequence

1. Confirm the original Z7 C 3.80/no paid RAW upgrade, and a fully charged
   supported battery or supported AC power. Follow Nikon's power precautions.
2. Connect the backed-up XQD/approved CFexpress card through its reader. Identify
   its current drive and physical identity before copying. The earlier E: card
   mapping alone is insufficient. No camera card was mounted at the initial
   preparation check; the later verified staging is recorded above.
3. Preserve the existing card firmware first. Stage only the new reviewed full
   EG at the card root as `EG161080.BIN`, then compare its complete read-back
   SHA-256. Keep stock and previous-build alternatives off that card. Do not
   format or delete user files as part of preparation.
4. Eject normally, insert in the camera and inspect Setup > Firmware version.
   Report the exact current/new versions and Update action before confirming
   programming. Same displayed version numbers can be expected for this
   unchanged-version component, but do not infer acceptance from the filename.
5. Start only on the owner's explicit instruction for this exact assessed
   candidate. During an update, follow the camera's completion instructions;
   do not interrupt power, remove the card or operate controls. Do not interrupt
   an update already in progress.
6. After successful completion, follow the camera's restart/card instructions.
   Inspect d9 and check each grid on LCD and EVF, then Off and live/menu/playback
   transitions. Select each new choice and check a normal shutdown longer than
   ten seconds, then a longer off interval. These test persistence; they are not
   expiry thresholds. Test standby/wake and ordinary NEF/JPEG capture/playback,
   and inspect the recorded image to check that guides are not burned in.
7. Record unexpected behavior before any further update. Presets/import/export,
   dynamic crop/EVF cases, long-term use and recovery remain unverified. If the
   camera cannot boot or reach its updater, no local recovery is established.

## Reproduce offline preparation

```powershell
.\.venv\Scripts\python.exe tools/build_grid_firmware.py --native-choice --extra-grids --output .private/builds/NEW-GRID-BUILD
.\.venv\Scripts\python.exe tools/prepare_flash_review.py --preset grid-layouts --build .private/builds/NEW-GRID-BUILD --output .private/flash-review/NEW-GRID-REVIEW
.\.venv\Scripts\python.exe tools/audit_grid_layouts_rollback.py --build .private/builds/NEW-GRID-BUILD --previous-build .private/builds/20261025-grid-native-value-02 --container .private/stock/Z_7_0380.bin --output .private/grid-layouts-previous-loader.json
```

All generated firmware and raw review inputs stay private. This assessment is
for an experimental hardware trial; it is not a production-safety certification.
