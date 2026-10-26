# Original Z7 grid hardware-test preparation — October 25, 2026

**Owner hardware result:** the grid build works, and the owner counted an
approximate off-time threshold: under three seconds switched off retains 3x3;
longer off periods return to 4x4. This is temporary retention, not reliable
persistence. The grid-only EG has no custom journal hooks. Its initializer
defaults to 4x4 when executed, but the actual quick-restart/shutdown mechanism
has not been traced. The precise threshold and battery-removal behavior are
unverified. The preparation's expectation of a reset on every off/on was too
broad. LCD/EVF coverage, all choices, standby/wake, recorded-image behavior,
stock rollback and emergency recovery are not established by this owner report.
The preparation/staging descriptions below are historical phases preceding it.

**Staging update:** after the owner requested a binary and connected the XQD,
the exact candidate was freshly rebuilt and copied to the newly verified Sony
QD-G240F at `E:\EG161080.BIN`. Its full SHA-256 readback matches the table below.
The older EG was verified/backed up on the laptop before replacement; photos,
SHUTTER.WAV and other card files were preserved. A convenient laptop copy is
`.private/flash-ready/20261025-grid-only/EG161080.BIN`. No formatting, automatic
ejection or camera flash occurred. The next step is camera recognition with
supported fully charged power and inspection of the actual current/new versions.
Preparation details below describe the preceding offline review phase.

The owner selected the **simpler, RAM-only grid build for the first hardware
test**. Preparation is complete. The next hardware step is card identification,
verified staging and camera recognition, followed by a separate decision to
start programming. No card or camera was accessed during this preparation.

This is an independent experimental build, based on the pinned original Nikon
Z7 C 3.80. It replaces the earlier experimental feature set with stock behavior
plus the d9 **4x4 grid / 3x3 grid / Off** menu. It contains only the grid feature.
The custom grid choice starts at 4x4 on a cold startup. Nikon's existing grid
visibility property remains boolean and follows its normal persistence rules.
There is no added settings-journal record or change to its native schema.

The persistent-grid prototype remains on hold. Do not substitute any
`grid-persistent-*` candidate, a splash build, or an earlier sound build.
The previous sound-port hold in `PORT_AUDIT.md` continues to apply to sound
builds; it is not behavioral evidence against or clearance of this separate
stock-based grid candidate.

## Exact local installation input

Private bundle: `.private/flash-review/20261025-grid-01/`.

| File | Purpose | Bytes | SHA-256 |
| --- | --- | --- | --- |
| `candidate/EG161080.BIN` | Independent full modified EG, including CRC | 33,053,802 | `ae46a48d52f4a89dac7c54bf63fc4b6d40b6c7d5adc49f67335e8b50fe97973b` |
| `stock-module/EG161080.BIN` | Untouched original EG | 33,052,090 | `7f59d8993080203a12692cf6927a0a8218786d3f72230c04174f1563c506a6f6` |
| `stock-container/Z_7_0380.bin` | Untouched official update container | 34,472,614 | `07cf19513ada5b770caec4cfc3531a6734c48aede28dcec037f0f8374ef441a2` |

The candidate matches a complete independent rebuild of
`.private/builds/20261025-grid-emulator-03/`. Its MAIN hash is
`2762ccd5276e1c4720c06e26f636c6c551cafe3772eb6d24400b769c200cd348`.
Four guarded windows replace 32 bytes; 1,712 bytes are appended. Version bytes
remain `03.80.00`. This is a component-file update input, **not a repacked Nikon
outer container**. Use the full EG file, not `grid.emulator.main.bin`; the latter
omits the two CRC bytes. The original build report's emulator-only identity is
retained as provenance: it does not claim physical verification or clearance.

The 33,053,802-byte EG is below the patcher's 32 MiB bound and the original
43,253,760-byte EG storage descriptor. Its appended code ends below Nikon's main
settings banks at `0x12E00000` and `0x131E0000`. These are checked layout facts,
not measurements of the physical programming operation.

## Verification and limits

- **192 instruction checks passed**, with 270 native geometry calls. These
  cover 4x4/3x3 geometry, three viewport inputs, five crop-property inputs, native
  menu focus/current-value marking, invalid-state fallback, cold-hook ABI and
  the original workspace allocator starting after the owned 64-byte block.
  UI, crop, viewport and allocator mutex boundaries are supplied in Unicorn.
- The same exact MAIN passed **10 native-key QEMU menu checks** and **6 assisted
  live-view checks** in the earlier completed grid run. The menu uses native key
  events. Live view calls compiled choice handlers and the native visibility
  update diagnostically. The current QEMU binary and its five source inputs
  match the hashes used for that evidence.
- **12 updater probes passed** for this exact full EG and stock EG: native
  header admission with two supplied runtime-property values, oversized/short
  rejection, and six native filename cases. These supply file I/O and runtime
  boundaries; they do not run full enumeration, updater CRC handling or flash
  erase/program/readback. All four stock module CRCs, container CRC, bounds and
  trailer, the candidate EG CRC and all three bundle copies are checked.
- **5 preparation tests passed**, covering private output paths, overwrite
  protection, unknown presets and mixed/modified EG, MAIN or report files.
  Patch/container/Thumb tests passed 14, with 2 optional stock-location
  integrations skipped. Direct private-source rebuild/probes above do execute
  the actual Z7 container path.

Evidence: `evidence/20261025-grid-preflash-instructions.json`,
`evidence/20261025-grid-firmware-qemu.json`, and
`evidence/20261025-grid-flash-review.json`. Source-only evidence is public;
firmware and camera frames remain private.

Hardware boot, LCD/EVF placement, standby/wake, native capture, card enumeration,
update acceptance and recovery remain unverified for this exact image. Emulator
success cannot establish those results. This preparation supports an explicitly
authorized experimental hardware test, not a claim of production safety.

## Installation and rollback assessment

The owner previously identified an original Z7 C 3.80 without Nikon's paid
RAW-video upgrade, and reported successful same-version component installations.
Reconfirm the current body/version before programming. The earlier E: drive and
card identity are historical: identify the actual card again before copying.
Never format or select a drive by assumption.

[Nikon's current Z7 page](https://downloadcenter.nikonimglib.com/en/download/fw/558.html)
describes official C 3.80 updating and says an already installed 3.80 does not
need that update. It does not certify same-version installation of this modified
component. No version spoofing or acceptance-check bypass is included.

If the camera remains bootable and its updater is usable, the separately kept
stock module/container are potential normal-updater rollback inputs. This
grid-only candidate does not add an incompatible settings schema requiring
conversion before stock rollback. Same-version stock rollback on this body is
still unverified. These files are not a complete flash/calibration backup.

**There is no verified local emergency recovery for a Z7 that cannot boot or
reach the updater.** Removing the card does not uninstall MAIN. A failed boot
could require professional servicing/reprogramming. Nikon's
[official update guide](https://download.nikonimglib.com/archive3/jFBMN00KI4Ix03x9LuU85FxJko41/Z-series_FirmUp_Win_En.pdf)
directs an inoperable device after a failed update to authorized service; it
does not provide a demonstrated recovery for this independent build. The stock
files and emulator checks cannot guarantee recovery.

## Hardware sequence

1. Reconfirm the original Z7/C 3.80/no paid RAW upgrade and stable supported
   power. Nikon calls for a fully charged supported battery or supported AC
   adapter, and an approved card formatted in the camera. Back up the card
   before any user-chosen formatting.
2. Identify the reader/card and its exact drive. Inspect existing firmware files
   and user data before copying. Stage only the reviewed candidate EG at the
   root; compare its full SHA-256 after copying. Keep both stock alternatives
   on the laptop and keep unrelated update files off the test card.
3. Eject normally, insert into the camera and inspect Setup → Firmware version.
   Report the exact current/new versions and available Update action. Recognition
   is a separate checkpoint: do not start programming merely because the file
   is listed. Rejection or an unexpected model/version requires investigation.
4. Start programming only after explicit owner authorization for this exact
   candidate and acknowledgment of the recovery assessment. During an update,
   follow the camera's completion instructions; do not interrupt power, operate
   controls or remove the card. Let an already running update finish.
5. After completion, remove the update card as instructed, restart and inspect
   Custom Settings → d Shooting/display → d9 Framing grid display. Check all
   three choices, live-view LCD and EVF, Off, playback/menu return, standby/wake,
   one ordinary NEF/JPEG capture and a power cycle. Confirm the grid is not
   burned into recorded images. On cold startup, expect the custom choice to
   return to 4x4; the camera's native visibility setting can remain enabled.
6. Record exact symptoms before any further update. If normal updater access
   remains, assess stock rollback using its separate reviewed input. A missing
   boot/updater has no established local recovery procedure.

## Reproduce preparation

```powershell
.venv/Scripts/python.exe tools/prepare_flash_review.py `
  --preset grid --build .private/builds/20261025-grid-emulator-03 `
  --output .private/flash-review/NEW-UNUSED-NAME
.venv/Scripts/python.exe -m unittest discover -s tests -p test_flash_review_paths.py -v
```

The preparation helper never accesses a card, camera or removable drive. It
refuses existing output directories and output outside `.private/`.
