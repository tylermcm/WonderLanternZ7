# Automatic spiral: experimental hardware trial, October 27, 2026

The owner explicitly requested trying the spiral on the camera and accepts
the curve appearing in front of status icons. The owner also confirmed charged
battery power and a backed-up card connected through its reader. This assessment
covers only the exact spiral build below. Clean-display research is excluded.

Target: original Nikon Z7, C 3.80, without the paid RAW-video upgrade, as
previously identified by the owner. This is independent modified firmware.

## Staged and owner update in progress

The Sony QD-G240F was freshly identified as the expected E: USB/XQD volume by
model, serial, physical capacity, volume identity and non-system/writable status.
The current six-grid EG matched its expected complete hash. It was backed up
and read back at `.private/card-backups/20261027-spiral-b20cb240/EG161080.BIN`.
The spiral was copied through a flushed, hash-verified temporary file, then
renamed to `E:\EG161080.BIN`. Final full size/hash match the candidate below.
It is the only root BIN. The settings/WAV hashes and other root-file inventory
are unchanged. No photo folder was changed, no formatting was performed, and
there was no automatic ejection or camera operation by the agent.

The owner subsequently reported "flashing now. ill report back", then confirmed
that the spiral appears only for Golden ratio and disappears when another grid
is selected. This is one owner's post-update display/selection report, not an
independent observation or firmware readback. The owner also confirms MENU clears
the curve and returning restores it. Broader behavior remains pending. Owner
evidence: `evidence/20261027-grid-spiral-owner-hardware.json`.
The owner was told to allow programming to finish without interruption and follow
the camera's completion/restart instructions. Sanitized preparation/staging evidence:
`evidence/20261027-grid-spiral-flash-review.json`.

## What this version does

The six existing grid choices remain. Selecting **Golden ratio** now adds the
Fibonacci curve to the straight phi grid on the rear LCD. There is no separate
spiral option. Choosing 3x3, 4x4, Center cross, 6x6 or Off disables the automatic
curve; Off stores zero. Existing internal grid values and the 89-record settings
journal format are unchanged. The curve can cross status icons, which the owner
has explicitly accepted for this trial. Sound and splash are excluded.

The native shooting UI paint walker runs first. A guarded Z7-only return-path
hook then checks the stored layout and the LCD grid enable flag, selects the
registered native 720x480 UI surface, draws the immutable PNG through the original
Z7 routines, restores the previous graphics target and returns. No new timer,
capture callback, internal settings record, custom writer or reserved workspace
is added. Missing/duplicate/inactive/wrong-size UI surfaces refuse the draw.

## Exact private candidate

Fresh build: `.private/builds/20261027-spiral-flash-01/`.
Review bundle: `.private/flash-review/20261027-spiral-01/`.
Convenient full EG: `.private/flash-ready/20261027-spiral/EG161080.BIN`.

- Full EG: **33,062,334 bytes**, SHA-256
  `52c593aff9895e31b4cfaf15ceb0335bdf4f26671d346dcb499080ea11c0f316`.
- MAIN: **33,062,332 bytes**, SHA-256
  `06b89e2a4eb864a96599eea504dd1d2f8aba05c8f072243c3a7d51c999fbd136`.
- Identical to the tested automatic-paint candidate 01. The 12-byte additional
  guarded stock window is at `0x103FCC54`; 11 bytes differ there. The explicit
  drawing parent and asset otherwise remain intact, with 352 bytes appended.
- Version remains `03.80.00`; no version spoof or update-admission bypass.
  The installation file retains its final two-byte CRC. Do not flash MAIN.
- Private stock input: official `Z_7_0380.bin`, SHA-256
  `07cf19513ada5b770caec4cfc3531a6734c48aede28dcec037f0f8374ef441a2`.

## What is checked

The prior identical MAIN passed 95 instruction checks with supplied native
UI/graphics boundaries and 18 assisted-QEMU checks. Both tested MENU roundtrips
clear and automatically restore the curve. Changes through exact native choice
handlers while MENU owns the screen remove it for 3x3 and Off, and restore it for
Golden ratio. No host drawing call or asset upload is used. Nine saved PNG hashes
verify. Startup/calibration/RAW and choice/visibility inputs remain diagnostic
assistance. This is not physical sensor, lens, AF, capture or update verification.

The fresh build is independently reproduced and compared with that exact tested
image. The dedicated `grid-spiral` review mode requires the full independent
rebuild, matching metadata, complete MAIN and EG CRC. Existing grid review modes
remain separate. A new admission regression rejects mixed/truncated/modified
images and the explicit-draw-only report. Root tests currently pass 20 checks.
The fresh image passes all 95 supplied-boundary instruction checks and 12
selected original updater header/name checks. All stock container/module CRCs,
bounds and three private review copies pass. Eighteen selected compatibility
checks on this exact image also pass with the previous three-choice loader:
new values 3/4/5 retain all 89 payloads, appear as Off in old selected consumers,
and can be changed/saved/reloaded as 3x3 without changing unrelated records.
These are not physical rollback tests. The identical MAIN's existing 18 QEMU
checks and nine frame hashes were verified; no redundant QEMU run was performed
for a byte-identical copy. The separate display research does not change this BIN.

## Trial limits and rollback

Foreground placement is accepted. Other limits remain: the fixed LCD surface,
dynamic crop/rotation, EVF switching, DISP/playback transitions, low-memory
failure, concurrent painting, repeated decoding cost, complete power/wake timing,
and physical update/boot are not comprehensively verified. A diagnostic direct
setting change outside MENU has no dedicated erase hook. Do not interpret the
image proof as a finished general display feature or a recovery guarantee.

For a first bounded trial, select **3x3** in the currently installed firmware
before updating. Use the rear LCD and enter Golden ratio only after ordinary
startup and menu access are confirmed. This keeps the spiral disabled at the
first startup. To end a functioning trial, change back to 3x3 or Off through MENU.
This disables drawing; it does not restore the previous firmware.

The review retains the prior six-grid EG (SHA-256
`437e1f8edbb89f1409ad768dcf50e91725280481561fcaa8f0f161cc64e5dccc`),
the owner-tested three-grid EG (SHA-256
`07d77574bc9fed84d357b4e7c3df808127d361106c10ca26e0b6e2c818f6d0a7`),
untouched stock EG (SHA-256
`7f59d8993080203a12692cf6927a0a8218786d3f72230c04174f1563c506a6f6`)
and official container in separate folders. If boot/menu/updater access survive,
these are potential normal-updater rollback inputs. They are not physically
verified rollback or full calibration/flash backups. The spiral adds no new
stored encoding beyond the existing six-grid parent.

**No local emergency recovery is verified for an unbootable camera.** A bad
update or boot can require professional service. Removing the card does not undo
installed firmware. The [official Nikon update guide](https://download.nikonimglib.com/archive3/jFBMN00KI4Ix03x9LuU85FxJko41/Z-series_FirmUp_Win_En.pdf)
requires appropriate charged power, no interruption during programming and
authorized service if an update leaves the camera inoperable.

## Installation sequence

1. Set the existing grid to 3x3 before the first update. Keep the first test on
   the rear LCD. The owner has confirmed charged battery power.
2. Re-identify the actual card, back up its existing firmware, stage only the
   reviewed full EG as `EG161080.BIN` and verify the complete read-back hash.
   Preserve photo/settings/audio files. Never place rollback and candidate BINs
   together on the update card.
3. Eject normally, insert the card, inspect Setup > Firmware version, then the
   exact current/new version confirmation. The version is intentionally unchanged.
   The owner controls starting the update after reviewing this exact candidate.
4. Once programming starts, follow the camera's completion directions. Do not
   interrupt power, remove the card or operate controls during the update.
5. After completion and the instructed restart, confirm ordinary 3x3/menu use.
   Select Golden ratio and check the curve, MENU removal/return, then 3x3/Off.
   Start with single still photographs; inspect the recorded files separately.
6. Record behavior before broader EVF/crop/playback/power-cycle tests. Any
   unexpected display behavior is a reason to stop the experiment through MENU
   while access remains available. No clean-screen patch is included.

## Reproduce offline review

```powershell
.\.venv\Scripts\python.exe tools/build_spiral_lifecycle.py --output .private/builds/NEW-SPIRAL
.\.venv\Scripts\python.exe tools/audit_spiral_lifecycle.py --build .private/builds/NEW-SPIRAL --stock .private/stock/Z_7_0380.bin --output .private/spiral-preflash-instructions.json
.\.venv\Scripts\python.exe tools/prepare_flash_review.py --preset grid-spiral --build .private/builds/NEW-SPIRAL --output .private/flash-review/NEW-SPIRAL
```
