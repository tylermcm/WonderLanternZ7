# WonderLantern Z7 — Nikon Z7 Firmware Extensions

Experimental, source-only firmware extensions for the **original Nikon Z7
(C 3.80)**: custom framing grids, rear-LCD battery percentage, configurable
LCD DISP presets and saved display settings.

**EXPERIMENTAL CAMERA FIRMWARE RESEARCH. A failed or incorrect flash can
permanently brick a camera, destroy data, or require paid repair/replacement.
Use entirely at your own risk. To the fullest extent permitted by law, the
authors/contributors accept no liability. No warranty or verified emergency
recovery is provided. Read [RISK_NOTICE.md](RISK_NOTICE.md).**

Independent, modified research workspace for the **original Nikon Z7 C 3.80**.
This is not an official Nikon or Wonder Lantern release. Component licenses,
credits and notices are preserved; see [UPSTREAMS.json](UPSTREAMS.json).

## Nikon Z7 LCD features and compatibility

These are development checkpoints, separate from the older released grid preview.
Hardware observations below are limited to the project owner's original Z7.

| Feature | Current status |
| --- | --- |
| Custom framing grids: 4x4, 3x3, Golden ratio, Center cross, 6x6 and Off | Selected layouts owner-tested; all five shapes have offline geometry checks. |
| Rear-LCD battery percentage | Owner-tested ON/OFF and preference retention, with saved-record checks. |
| Four configurable LCD DISP presets | Custom pages retention, menu navigation and DISP cycling owner-tested; individual information/focal controls still have limited hardware coverage. |
| Saved grid shape and display settings | Center cross and 6x6 restored after shutdown; Center cross also after battery removal. Both v3 slots verified, with prior record and older files preserved. Broader preset hardware checks remain pending. |

**Target:** original Nikon Z7 C 3.80, without the paid RAW-video upgrade.
Z7 II, other firmware versions and other body/service configurations are not
validated by this port. EVF, movie and external-output behavior are outside the
current LCD hardware-verification scope. See the
[full hardware status and known issues](DEVELOPMENT_UPDATE_2026-11-23.md).

## Latest development update — November 23, 2026

**Owner hardware-tested LCD checkpoint on one original Z7 C 3.80.** Selected
SD-loader/worker, rear-LCD battery, Custom pages/DISP and saved-grid tests now
have owner reports. Read-only card inspection verified Center cross
and 6x6 records and preservation of the older settings files. **Photo/video proof is
pending; this is limited owner verification, not certification of the full
port, other bodies, safe installation or emergency recovery.**

There is still a brief wrong-grid display after battery removal before the
saved grid appears. Controls remain responsive in the owner's report. EVF,
movie/external output, full capture/sleep/wake behavior and interrupted-save
recovery are not cleared by this LCD trial. Earlier checkpoints froze inputs;
read the [risk notice](RISK_NOTICE.md) before considering any build or update.

Read the [development update and hardware verification scope](DEVELOPMENT_UPDATE_2026-11-23.md)
for working milestones, remaining issues and the evidence. This is a **source
update**, with no firmware or generated module BIN download. The older preview
below does not contain these LCD checkpoints.

**Upstream credit:** this port builds on
[JKWTCN's Z7II extensions](https://github.com/JKWTCN/z7ii-extensions), including
the module framework and custom-DISP concepts. The original-Z7 adaptation is
independent work; the upstream MIT copyright/license and all other component
licenses remain intact. See [CREDITS.md](CREDITS.md) and
[UPSTREAMS.json](UPSTREAMS.json).

## Frequently asked questions

### Is WonderLantern Z7 custom firmware for the original Nikon Z7?

It is an experimental firmware-extension research project for the original Z7
on C 3.80. The current work includes an installed module host and SD-loaded LCD
extensions. It is independent of Nikon and the upstream projects; installation
and recovery are not guaranteed safe.

### Does it work on a Nikon Z7 II?

This repository targets the original Z7. The separate
[JKWTCN Z7II extensions project](https://github.com/JKWTCN/z7ii-extensions)
provides the upstream framework and feature concepts credited here. Native
addresses, hosts and module packages are model-specific and are not interchangeable.

### Has it been tested on a real camera?

The owner has tested selected LCD checkpoints on one original Z7. Some saved
settings have also been decoded from the card and checked for
integrity. [The hardware report](DEVELOPMENT_UPDATE_2026-11-23.md) distinguishes
those observations from offline tests. Photo/video proof is pending; a brief
wrong-grid display after battery removal remains open.

### Can I download a ready-to-flash Nikon Z7 firmware BIN here?

No stock or modified Nikon firmware or generated module binaries are distributed
with the current source update. The older source/patcher prerelease below is a
separate preview. Read the [risk notice](RISK_NOTICE.md),
[Windows build guide](WINDOWS_BUILD.md) and the
[exact LCD checkpoint assessment](LCD_GRID_PERSISTENCE_REVIEW.md) before
considering a local build with your own matching official firmware.

## Earlier published 3x3 grid preview

[Experimental source/patcher prerelease v0.1.0-grid-preview.1](https://github.com/tylermcm/WonderLanternZ7/releases/tag/v0.1.0-grid-preview.1)

The preview adds **3x3 / 4x4 / Off** to the native framing-grid menu, with the
choice stored in the camera's existing internal settings. It has no timed
reversion. The owner reports that the latest build is installed and keeps 3x3
after more than ten seconds switched off on one original Z7. That limited
result is not certification or proof of compatibility with every Z7.

**Source/patcher release only:** no stock or modified Nikon firmware BIN is
redistributed. Build the exact reviewed image locally using your own official
`Z_7_0380.bin`. Start with [the release/build guide](RELEASE_GRID_PREVIEW.md),
then read [the exact-candidate assessment](GRID_NATIVE_FLASH_ASSESSMENT.md).
Target scope is original Z7 C 3.80 without Nikon's paid RAW-video upgrade;
other bodies/versions, including Z7 II, are not supported by this preview.

The exact image passed 107 instruction checks, 16 assisted QEMU checks and 12
selected updater probes. Test boundaries and remaining gaps are documented in
[NATIVE_GRID_SETTINGS.md](NATIVE_GRID_SETTINGS.md). Owner hardware results are
recorded separately in `evidence/20261026-grid-saved-owner-hardware.json`.
Off intentionally clears the selected type; presets/import/export, indirect
consumers, wake behavior, extended use and failure recovery need further review.

## Other lab experiments

The [Z7II-to-Z7 SD module port](SD_MODULE_PORT.md) adapts JKWTCN's extension
framework for the original Z7. The host and incremental LCD modules now have
selected owner camera trials in addition to instruction fixtures and assisted
QEMU work. The [current hardware status](DEVELOPMENT_UPDATE_2026-11-23.md)
supersedes older emulator-only milestones in the research notes; it does not
clear every profile or establish full cache correctness and recovery.

The [display module research](Z7_DISPLAY_MODULE_RESEARCH.md) covers the native
six-choice grid menu and display hooks. The latest
[grid-persistence checkpoint](LCD_GRID_PERSISTENCE_REVIEW.md) saves grid shape
in separate versioned journals while preserving the older settings files.
Center cross and 6x6 have owner restart observations and physical journal
readbacks; Center cross also returns after battery removal. Broader preset
hardware validation remains pending.

The [configurable DISP work](z7-native-modules/DISPLAY_SETTINGS.md) now includes
four presets, native base-page selection, six separate information groups and
an Other-information group covering18 independently identified original-Z7
widgets. Scoped policy and captured-pixel checks preserve shared warnings and
native restoration on the standard page. A no-focal control isolates native ADL
edge settling; combined focal/horizon restoration now passes with exact qualified
native frames. The [native information-page contracts](Z7_INFORMATION_APP_RESEARCH.md)
are independently bound. The custom information-page integration, highlights,
portrait and broader lifecycle remain under development. Selected LCD
preference persistence now has the limited hardware results linked above.

An initial [focal-length overlay](FOCAL_LENGTH_RESEARCH.md) now displays whole
and fractional millimeters on custom LCD landscape pages, independently of Other
information. Standard/horizon rendering and restoration pass with supplied lens values;
EVF, rotation, broader lifecycle and physical lens telemetry remain unverified.

An [automatic LCD-photo battery module](Z7_BATTERY_DISPLAY_RESEARCH.md) now
adds bounded native sampling, compact percentage text, warning-color preservation
and stock-icon restoration. It is a separate SD-module profile with an initial
on/off build setting. Assisted-emulator checks include a labeled GUI icon fixture;
rear-LCD on/off and preference retention have owner camera reports. Physical
calibration accuracy and the remaining lifecycle/output paths are unverified.

The optional [additional-grid lab candidate](GRID_LAYOUTS_RESEARCH.md) adds
Golden ratio, Center cross and 6x6 alongside 4x4, 3x3 and Off. Menu, drawing
and simulated saved-choice tests passed, and the owner has tried the separately
reviewed candidate on one camera. These layouts are not part of the published
preview. Read its [trial assessment](GRID_LAYOUTS_FLASH_ASSESSMENT.md).

A separate [Fibonacci-curve experiment](GRID_SPIRAL_RESEARCH.md) automatically
draws a gray spiral with Golden ratio on the monitor and EVF. The owner reports
the separately reviewed trial works, with **visible electronic-level lag in
EVF** and slight lag on the monitor, only with Golden ratio. The lag is not fixed.
The [exact trial assessment](GRID_SPIRAL_DISPLAY_FLASH_ASSESSMENT.md) records
validation and recovery limits. No firmware BIN is redistributed or new release
declared by this source update.

[Clean-display research](CLEAN_DISPLAY_RESEARCH.md) hides most shooting widgets
in an emulator experiment but still leaves card-count brackets. It is not
included in the camera trial.

The source also retains earlier sound, splash and added-journal-record work.
Those are **not included in the grid preview's generated image**. Automatic
shutter sound still has the reported live-view repetition defect; its
[port audit hold](PORT_AUDIT.md) remains. Do not substitute older presets or the
held 90-record journal prototype for the preview's `--native-choice` build.
For current hardware status and remaining work, read the
[development update](DEVELOPMENT_UPDATE_2026-11-23.md).

Earlier assisted-emulator runs passed 21 general UI checks and 17 sound-submenu
checks for each sound-capable preset. Those results establish selected emulator
behavior; they do not clear the capture-trigger defect or establish physical
capture timing, recording, recovery or compatibility with other camera models.

## Contents

- `z7-qemu/`: complete source overlay and tools, with local changes included.
- `z7-firmware-extensions/`: complete patcher source, including all sound fixes.
- `tools/`: local build, validation, setup and launch helpers.
- [DEVELOPMENT_UPDATE_2026-11-23.md](DEVELOPMENT_UPDATE_2026-11-23.md): current hardware scope, results and remaining work.
- [SOUND_MENU_FIX.md](SOUND_MENU_FIX.md): fault analysis and corrected addresses.
- [AUDIO_PLAYBACK_FIX.md](AUDIO_PLAYBACK_FIX.md): WAV specification check and corrected Z7 playback admission.
- [FLASH_ASSESSMENT.md](FLASH_ASSESSMENT.md): private EG preparation, updater evidence and hardware recovery limits.
- [SHUTTER_TRIGGER_FIX.md](SHUTTER_TRIGGER_FIX.md): capture-hook correction and diagnostics after working Preview but silent capture.
- [CAPTURE_START_FIX.md](CAPTURE_START_FIX.md): normal-callback correction after the silent/mechanical diagnostic comparison.
- [SILENT_PROPERTY_FIX.md](SILENT_PROPERTY_FIX.md): verified native Z7 silent-mode property and tests through the original getter.
- [PORT_AUDIT.md](PORT_AUDIT.md): current flash hold and independent Z7 evidence gaps after the owner's port-safety concern.
- [LIVEVIEW_SOUND_REGRESSION.md](LIVEVIEW_SOUND_REGRESSION.md): reproduced unwanted admission and owner-confirmed OFF containment.
- [CAPTURE_EVENT_TRACE.md](CAPTURE_EVENT_TRACE.md): original callback execution and stock live-view counterexamples.
- [STILL_FILE_TRACE.md](STILL_FILE_TRACE.md): record-bearing file notification as a backward-tracing anchor; no replacement hook selected.
- [SPLASH_SCREEN_FEASIBILITY.md](SPLASH_SCREEN_FEASIBILITY.md): private stock resource findings and the proposed startup image approach.
- [LAB_REPORT.md](LAB_REPORT.md): complete lab history.
- [UPSTREAMS.json](UPSTREAMS.json): original repository and commit provenance.
- `evidence/`: source-only validation summary; no firmware or camera screenshots.

The three component directories are vendored source snapshots, **not submodules**.
Their upstream licenses and notices remain in place. This repository is a modified
research workspace and does not claim to be an official WonderLantern release.

## Windows app

The lab also supports native Windows using an isolated MSYS2/UCRT64 build.
It does not require WSL. After setup, double-click `Start-Z7.cmd` to open the
local browser app, or run `./Run-Z7.ps1` from PowerShell.

For a fresh build, obtain the official `Z_7_0380.bin` in Downloads and use
Python 3.12+:

```powershell
.\Setup-Z7.ps1
# Or select an unregistered Python explicitly:
.\Setup-Z7.ps1 -PythonPath C:\path\to\python.exe
```

The helper checks the firmware hash, creates a private Python environment,
downloads a digest-checked MSYS2 environment under `.private/toolchain/`,
builds the hash-checked QEMU source and all four firmware presets, and checks
the native host contracts and candidate admission. It preserves existing firmware and build directories.
See [WINDOWS_BUILD.md](WINDOWS_BUILD.md) for rebuilding and validation commands.

## Linux / WSL setup

Use Linux or WSL with Python 3.12+. In an already installed Ubuntu environment:

```sh
sudo apt-get update
sudo apt-get install build-essential ninja-build pkg-config python3-venv \
  libglib2.0-dev libpixman-1-dev zlib1g-dev libfdt-dev
python3 tools/setup_lab.py --jobs 4
```

Obtain your own official Nikon `Z_7_0380.bin` and place it at
`.private/stock/Z_7_0380.bin`. Check its SHA-256 against the handoff, then:

```sh
LAB_PY="$HOME/.local/share/wonderlantern-z7/venv/bin/python"
"$LAB_PY" tools/build_firmware.py --output .private/builds/20261020-09
"$LAB_PY" tools/check_candidate_inputs.py --build .private/builds/20261020-09
"$LAB_PY" tools/launch_z7.py
```

Open <http://127.0.0.1:8787/>. On Windows, after the Linux setup/build above,
`Run-Z7.ps1 -WslDistro Ubuntu` uses the locally recorded Linux interpreter.
Windows needs a Python launcher (`py` or `python`); no Windows Python packages
are needed just to start the WSL server.

## Inputs and distribution

No Nikon firmware, modified firmware binary, dump, key, camera screenshot,
private media, virtual environment or compiled QEMU binary is included. These
stay in ignored local directories. Generated CMOS color bars are recreated from
source. No camera-installable update package or flash writer is supplied.

See `z7-qemu/NOTICE.md`, `z7-qemu/COPYING`, and the license/notices inside
`z7-firmware-extensions/`. Their respective licenses apply to their components;
no license here grants rights over Nikon firmware.
