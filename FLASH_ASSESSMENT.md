# Original Z7 C 3.80 installation review — October 21, 2026

**October 25 scope update:** the owner selected a separate stock-based RAM-only
grid candidate for first hardware testing. Its concrete input, verification,
installation sequence and recovery limits are in
[GRID_FLASH_ASSESSMENT.md](GRID_FLASH_ASSESSMENT.md). The sound-build failure
and hold below remain historical/current evidence for sound candidates; they
do not describe the selected grid-only image. No new card staging or flash
occurred during grid preparation.

**Latest result: failed.** The owner reports continuous live-view sound and
Capture audio busy. Read [LIVEVIEW_SOUND_REGRESSION.md](LIVEVIEW_SOUND_REGRESSION.md).
Leave Shutter sound Enabled OFF. Installation of the latest candidate is inferred
from the test sequence without readback. No new flash is cleared; historical
post-installation test instructions below must not be resumed during this hold.

## Port review hold after owner concern

Further installation recommendations are on hold. Read [PORT_AUDIT.md](PORT_AUDIT.md).
The owner raised the risk of copied Z30 assumptions; the corrected silent-property
candidate below is not cleared for a further flash by this review. Existing checks
establish scoped facts, not overall safety or a verified recovery path. Do not
interrupt an update already in progress, and do not attempt an automatic rollback.
Earlier staging and installation instructions below are historical preparation
records while the audit hold remains open.

## Current candidate: Z7 Silent photography property

The owner reports Silent mode required despite Nikon Silent photography ON after
installing/testing the previous candidate. The trigger is reached but reads the
wrong mode property. [SILENT_PROPERTY_FIX.md](SILENT_PROPERTY_FIX.md) identifies
0x576 in Nikon's original menu constructor and documents the independent correction.

Private review suffix: `20261021-silent-property-01`. Full `EG161080.BIN`,
33,065,322 bytes, SHA-256
`9e636d645281ee9f92cb150b6dcc8d771b21ff95c47e45f538d951a1d932420b`.
Only one appended instruction byte and two CRC bytes change from the prior
capture-start candidate. The complete tail, size and `03.80.00` remain. It was
staged on the verified E: Sony QD-G240F card at 2026-10-22 04:38 UTC (October 21
locally), with complete SHA-256 readback matching the candidate above. The old
card EG was backed up privately; SHUTTER.WAV and other files were preserved.
The review bundle's card-staging.json records the copy. Installation is now
inferred from the latest owner report; the live-view regression above supersedes
the earlier pending hardware result.
Both sound presets pass 60 capture checks and 18
playback checks with the real native property getter; all 16 firmware tests pass.

The existing EG installation assessment, fully charged battery requirement and
recovery limits remain applicable. Previous candidates and original stock inputs
are preserved. Reinstall still requires a functioning updater; emergency recovery
is unverified. After installation, reselect SHUTTER.WAV and Enabled ON, restore
Silent photography ON, take one photo and read the heading without resetting the
feature. Correcting the native property is verified offline; audible capture
sound on this candidate still needs a camera result.

## Previous candidate: normal capture callback

The owner reports Waiting for capture after a silent photo, but Silent mode
required after a mechanical photo. This supports the previous diagnostic build
running and the late hook's mode gate, without establishing the silent capture
notification. The new independent correction is described in
[CAPTURE_START_FIX.md](CAPTURE_START_FIX.md).

Private review suffix: `20261021-capture-start-02`. Full `EG161080.BIN`,
33,065,322 bytes, SHA-256
`efcfbda40439354e8707a2c1e8c0b16b5e47a27c0fe8999110ca98eb9f15dc1c`.
CRC, complete appended tail and `03.80.00` are retained. It moves the audio
request to the separate normal callback and leaves the late hook diagnostic-only.
The candidate was staged on the verified E: Sony QD-G240F card at 2026-10-22
04:10 UTC (October 21 locally), with complete SHA-256 readback matching the
candidate above. The previous card firmware was backed up privately; SHUTTER.WAV
and other card files were preserved. The review bundle's card-staging.json
records staging. No installation of this candidate has been reported.
All 48 capture contracts and 18 playback contracts pass for both sound presets,
along with 16 firmware tests, 13 admission and 12 review checks. The first
isolated assisted-QEMU menu run passes all 17 checks with no observed abort.

The existing EG installation assessment, fully charged battery requirement and
recovery limits still apply. Previous builds and stock inputs remain private and
preserved. Reinstall depends on a functioning updater; there is no verified
emergency recovery. Native instruction success does not prove this candidate's
real capture timing or audio behavior. A retest requires selecting the WAV,
Enabled ON and Silent photography ON after restart, taking one photo, and reading
the main sound-page heading without resetting Enabled or cycling power.

## Previous diagnostic candidate: capture trigger

The owner reports WAV playback works but shutter-triggered playback fails even
with Enabled, a selected WAV and Silent photography ON. The new independent
candidate is documented in [SHUTTER_TRIGGER_FIX.md](SHUTTER_TRIGGER_FIX.md).
It repairs a reproduced alternate native callback-path defect and adds capture
status titles; physical shutter-triggered sound remains unresolved.

Private review: `.private/flash-review/20261021-shot-fix-01/`. Full EG filename
`EG161080.BIN`, 33,065,098 bytes, SHA-256
`51dd7feb01e991d0cbce93e952ac42be98981dca510187e2767141ec8974dd9b`.
CRC, complete tail and unchanged `03.80.00` version are retained. The offline
review verifies 12 native header/filename checks and all three private bundle
copies. The diagnostic EG was staged on the re-verified E: Sony QD-G240F card at
2026-10-22 03:39 UTC (October 21 locally), with complete SHA-256 readback matching
the candidate above. The old card firmware was backed up privately; SHUTTER.WAV
and all other card files were preserved. The review bundle's card-staging.json
records staging. The owner later reported its distinctive diagnostic headings;
installation is inferred from those headings without firmware readback.

The same verified EG installation path and fully charged battery requirement
apply. Preserve the working audio-fix build and stock inputs. Normal reinstall
still depends on a functioning camera updater; no emergency recovery is verified.
The previous successful installation does not establish this candidate's hardware
operation. A useful retest is one silent photo after reselecting the WAV and
enabling sound, followed by reopening the sound page to read the diagnostic title.

## Corrected audio candidate, owner reports working WAV playback

The first build documented below loaded the WAV but its Preview was silent
with a false Sound busy result. The new
independent correction is reviewed in [AUDIO_PLAYBACK_FIX.md](AUDIO_PLAYBACK_FIX.md):
it fixes the busy-state address and uses a native-valid, callback-guarded type.

The prepared private candidate is
`.private/flash-review/20261021-audio-fix-01/candidate/EG161080.BIN`, 33,064,942
bytes, SHA-256 `770408b99ff547dd972486656285307b17e4ff2674937dbb50f144200233b7be`.
It retains the CRC, complete appended tail and unchanged `03.80.00` version.
Only five appended-code bytes plus two CRC bytes differ from the image that
the owner installed successfully. The untouched stock and previous modified
images remain available privately. The corrected EG was copied to the verified
E: Sony QD-G240F card at 2026-10-22 03:08 UTC, with complete SHA-256 readback
matching the candidate above. The previous card EG was backed up privately;
SHUTTER.WAV and all other card files were preserved. The private review bundle's
card-staging.json records this. The owner subsequently reported "the wav actually
works now!" following the installation/Preview instructions. This establishes
owner-reported audible WAV playback; the exact playback mode was not stated.
Corrected installation is inferred from the sequence, without firmware readback.
A fresh source-based candidate check must use the new build;
the older payload no longer reproduces from the updated patcher source.

The new owner report supports working audio on this body. It does not establish
shutter-triggered playback, repeated-use stability or rollback after a bad boot.
There is still no verified local emergency recovery route. Stock or
previous-image reinstall requires a functioning installation path; otherwise the
documented service fallback and its limits below still apply.

## First installation record and original assessment

**The owner reports the first flash succeeded and the sound setting is visible
on the camera.** This establishes a reported installation and running menu entry;
audio, capture, stability and recovery remain unverified. The owner authorized an experimental flash attempt
and confirmed an original Z7, C 3.80, without the paid RAW-video output upgrade.

The following assessment preserves the checks and uncertainties recorded before
the attempt. The owner reported the updating warning at about 30%, then reported
success and the sound setting's presence. No post-installation camera dump,
exact completion message, physical WAV playback or recovery result was supplied.

Card staging completed at 10:47 UTC: `EG161080.BIN`, 33,064,942 bytes, with complete
SHA-256 readback matching the candidate below. The Sony QD-G240F is removable,
exFAT, healthy and writable; no firmware file was present before copying. No card
formatting or existing-file deletion occurred. The private `card-staging.json`
receipt records this separately from the offline helper's earlier results.
The owner reports the camera page shows C 3.80 with Done, Update and Delete
firmware files. This supports file recognition; it does not establish complete
updater admission or successful programming. Battery charge and the separate
update confirmation dialog were initially unconfirmed. The owner subsequently
reported **Update? Current A3.80 → New A3.80**, Yes/No. The camera is offering a
same-version choice for the staged EG; no Yes selection or flash completion has
been reported. The exact A-label mapping was not independently established by
the bounded native probes. A fully charged battery is still a prerequisite.

## Exact artifact

The private review bundle is `.private/flash-review/20261021-01/`:

| File | Meaning | Bytes | SHA-256 |
| --- | --- | --- | --- |
| `candidate/EG161080.BIN` | Independent modified full EG; includes its two CRC bytes | 33,064,942 | `9e98eae9b726d1ced0e9cef60c89b6ef25eff369430673e753b5c3054be4f6b4` |
| `stock-module/EG161080.BIN` | Untouched original EG; potential rollback input | 33,052,090 | `7f59d8993080203a12692cf6927a0a8218786d3f72230c04174f1563c506a6f6` |
| `stock-container/Z_7_0380.bin` | Untouched official four-module update container | 34,472,614 | `07cf19513ada5b770caec4cfc3531a6734c48aede28dcec037f0f8374ef441a2` |

The candidate is byte-identical to an independent rebuild of the accepted `full`
emulator image. It includes the histogram/level display, M900 and sound menu
patches, with 12,852 appended MAIN bytes. Sound starts disabled. This is an
independent modified release, not Nikon or an official Wonder Lantern release.
Firmware version bytes remain `03.80.00`; no version was spoofed.

`full.main.bin` is for QEMU and omits the final two EG CRC bytes. Preserve every
appended code byte. Neither that MAIN file nor a renamed EG is a complete
`Z_7_0380.bin` container.

## Installation-path evidence

The pinned Z7 stock firmware contains a separate component-file path:

- At `0x11BABB64`, the filename pattern is `EG1610??.BIN`. Both directory tables
  identify it as component type 2. Its callback at `0x101B5CC8` returns enabled.
- The type-2 dispatch at `0x101B7FC0` calls the EG header checker at `0x101B5F36`.
  The checker reads the module marker and version and compares file size against
  the selected storage descriptor.
- Storage selection functions `0x10091F10`, `0x10091EFE` and `0x101AE9CA` resolve
  the EG descriptor to base `0x10020000`, length `0x02940000` (43,253,760 bytes).
  This candidate is below both that descriptor and the patcher's stricter 32 MiB
  bound. This is static metadata, not a physical flash readback or programming test.
- Twelve bounded Unicorn checks passed: stock and candidate header checks with
  runtime property `0x111` set to 0 and 1; oversized and short-header rejection;
  and six filename cases. `EG161080.BIN` and its lowercase spelling match the
  native single-name loop. The literal longer name `EG16100380.BIN` does not.
  FAT short-name aliases and actual card enumeration were not tested.

The header checks mock seek/read, memory helpers, the NUL marker classification
and runtime property `0x111`; they do not establish that property's meaning.
They do not execute directory enumeration, the complete updater admission path,
CRC handling in the updater, flash erase/program/readback, or real power-on.
The bundle separately verifies the candidate's entire module CRC and checks all
four stock module CRCs, package CRC, reserved fields, extents and trailer.

Related upstream projects report component-only installation on
[Z6 C 3.80](https://github.com/WonderLantern/WonderLantern-z6/blob/main/README.md)
and [Z30 C 1.20](https://github.com/WonderLantern/wonder-lantern-z30/blob/main/README.en.md).
Those reports support investigating this route; they are not Z7 hardware results.
The [Z7 patcher's guide](https://github.com/totwoto02/z7-firmware-extensions/blob/main/PATCH_GUIDE.md)
produces an EG module but supplies no Z7 recovery validation.

The complete outer container is a separate route. The current upstream
[digest solver/repacker](https://github.com/WonderLantern/nikon-fw-key-tool/blob/33426e892afd329a3b366b73776bcf53b9ac4ee8/README.md)
supports model digest recovery for Z8/Z9, not Z7. We did not repackage an outer
container, copy a stale digest onto modified data, or rename our EG to the official
container name. A valid outer digest is not established by an EG CRC.

## Same-version acceptance and recovery

[Nikon's official Z7 page](https://downloadcenter.nikonimglib.com/en/download/fw/558.html)
lists C 1.00–3.70 as supported starting versions for the 3.80 update. It does not
establish reinstalling 3.80 over 3.80. The local header probe accepts our unchanged
version string; a complete camera update can still reject it at another stage.
We will not force acceptance by changing version bytes or bypassing checks.

If the modified camera still boots and reaches its normal firmware menu, the
saved stock module or official container can be presented as rollback inputs.
Neither same-version rollback path has been tested on this body. Keep them
separate from the candidate and preserve the original Downloads file.

If it cannot boot or reach that menu, **there is no verified local Z7 emergency
button, USB, boot-ROM or external-programmer recovery procedure in this lab**.
The stock files are update inputs, not a full flash/calibration backup. Removing
the card does not uninstall a persistent MAIN modification.

[Nikon's update guide](https://download.nikonimglib.com/archive3/jFBMN00KI4Ix03x9LuU85FxJko41/Z-series_FirmUp_Win_En.pdf)
directs an inoperable camera after an unsuccessful update to authorized service.
That is the documented fallback, not a demonstrated recovery of this modified
image. An experimental attempt could require hardware servicing/reprogramming;
the available stock files do not guarantee recovery.

## Next hardware step

1. The owner identified E: and the card was verified as a Sony QD-G240F XQD.
   Its root had no user files or firmware files. Nikon specifies a card formatted
   in the camera; the format's origin was not independently verified. No automatic
   formatting or guessed drive is permitted.
2. Check the normal camera firmware page still shows C 3.80. Use the fully charged
   supported battery or supported AC supply specified by Nikon's guide.
3. Staging is complete: only candidate `EG161080.BIN` was added at the card root,
   and its complete SHA-256 was verified after copying. Stock files remain on the
   laptop. Do not trim the EG or add a second firmware update file to the test card.
4. Eject the card normally. On the camera open Setup → Firmware version and
   record the screen's exact current/new version and Update availability. Stop
   there: do not select Update or Yes during the recognition check. If it ignores
   the file or rejects it, retain the message and investigate the actual check.
5. Final programming and post-boot testing remain a separate hardware step after
   interpreting that screen and this recovery limitation. Emulated menus, valid
   CRCs and the owner's authorization do not supply the missing hardware result.

Real card/audio loading, sensor initialization, autofocus, mechanical shutter,
NEF/JPEG capture, video, update acceptance and post-failure recovery remain
unverified. If a later programming attempt is started, follow the camera's
completion instructions without interrupting power, controls or card access.

## Reproduce the offline review

```powershell
.venv/Scripts/python.exe tools/prepare_flash_review.py `
  --build .private/builds/20261021-laptop-01 `
  --output .private/flash-review/NEW-UNUSED-NAME
.venv/Scripts/python.exe -m unittest discover -s tests -p test_flash_review_paths.py -v
```

The helper refuses output outside a new subdirectory of `.private/`, verifies
written files by readback, and has no camera/card access or flashing command.
Three output-path protection tests passed. Private probe logs and disassembly
remain ignored; the sanitized scope is in `evidence/20261021-flash-review.json`.
