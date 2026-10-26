# Experimental original Z7 3x3 grid preview

**WARNING: A FAILED OR INCORRECT FLASH CAN PERMANENTLY BRICK YOUR CAMERA,
DESTROY DATA, OR REQUIRE PAID REPAIR OR REPLACEMENT. USE ENTIRELY AT YOUR OWN
RISK. TO THE FULLEST EXTENT PERMITTED BY LAW, THE AUTHORS, CONTRIBUTORS,
MAINTAINERS AND DISTRIBUTORS ACCEPT NO LIABILITY FOR RESULTING DAMAGE OR LOSS.
NO WARRANTY AND NO VERIFIED EMERGENCY RECOVERY ARE PROVIDED.**

Read [RISK_NOTICE.md](RISK_NOTICE.md) before building or installing anything.
This is an independent experimental release, not an official Nikon or Wonder
Lantern release. A disclaimer does not make installation safe.

## What this preview does

It adds **3x3 / 4x4 / Off** to the original Z7's framing-grid menu. The selected
type is intended to remain in the camera's internal settings across shutdowns.
There is no timed reset. The owner reports a successful installation and 3x3
retention after more than ten seconds off on one original Z7. Broader camera
compatibility and reliability are not established.

Target: **original Nikon Z7, C 3.80, without Nikon's paid RAW-video upgrade**.
This is not a Z7 II or general Z-series build. This release's generated image
contains the grid changes only; historical sound, splash and other experiments
in the source tree are not enabled. The known sound-trigger defect remains held.

## Source/patcher release, not a downloadable Nikon firmware image

Nikon's [official C 3.80 page](https://downloadcenter.nikonimglib.com/en/download/fw/558.html)
marks reproduction as not permitted. With the owner's agreement, no complete
stock or modified Nikon BIN is attached. Use the source asset or GitHub source
archive and your own official `Z_7_0380.bin` to reproduce the exact reviewed image.
No Nikon firmware, key, dump, calibration data or camera screenshot is included.

Preserve all licenses: `z7-firmware-extensions/LICENSE`, its
`THIRD_PARTY_NOTICES.md` and `licenses/Wonder-Lantern.txt`, and `z7-qemu/COPYING`
and notices. Some components have a community license with free-distribution
and source-availability requirements; do not describe the entire mixed tree as
uniformly MIT or OSI-licensed. Modified Wonder Lantern derivatives must remain
free of charge and must not claim to be official upstream releases.

## Build the exact preview locally on Windows

Use Python 3.12 or newer. Extract the source archive and open PowerShell in its
root. Obtain the official firmware directly from Nikon and retain it privately.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".\z7-firmware-extensions[sound,verify]"
New-Item -ItemType Directory -Force .private\stock | Out-Null
# Copy your own official Z_7_0380.bin to .private\stock\Z_7_0380.bin.
.\.venv\Scripts\python.exe tools\build_grid_firmware.py --native-choice `
  --output .private\builds\grid-preview-1
.\.venv\Scripts\python.exe tools\prepare_flash_review.py --preset grid-native `
  --build .private\builds\grid-preview-1 `
  --output .private\flash-review\grid-preview-1
```

The extra named `sound` installs the assembler dependency; the command above
selects only the existing-setting grid feature. It does not enable sound. Do
not substitute `--persistent`: that selects the different, held journal prototype.
The build and review helpers do not copy to a card or operate a camera.

The original input must be exactly 34,472,614 bytes with SHA-256
`07cf19513ada5b770caec4cfc3531a6734c48aede28dcec037f0f8374ef441a2`.
The builder rejects a different file rather than trying another camera's image.

Expected full local EG is **33,054,026 bytes**, SHA-256
`07d77574bc9fed84d357b4e7c3df808127d361106c10ca26e0b6e2c818f6d0a7`.
The review helper names it `candidate/EG161080.BIN`. Preserve the full file and
its CRC. The separate `grid.emulator.main.bin` is for emulation and is not that
installation file. No outer Nikon update container is repacked or version spoofed.

## Validation and limits

The exact image passed 107 scoped instruction checks and 16 assisted QEMU
menu/live-view checks, plus 12 selected original updater header/filename probes.
The source reports separate supplied OS/flash/UI boundaries from real hardware
behavior. Read [NATIVE_GRID_SETTINGS.md](NATIVE_GRID_SETTINGS.md),
[GRID_NATIVE_FLASH_ASSESSMENT.md](GRID_NATIVE_FLASH_ASSESSMENT.md) and the
`evidence/20261025-grid-native-*` summaries for details.

The new type uses Nikon's existing saved grid field. The original journal
format remains unchanged. Selected unmodified-stock loader/menu/display tests
preserve the native records and treat the new value as Off; that is not a full
camera rollback or emergency-recovery result.

After installation, select 3x3 once: the earlier RAM-only build did not save the
type. Off intentionally clears the selected type. Native settings resets or
imports can also change settings. U1/U2/U3, indirect consumers, all wake/display
combinations, long sessions and physical failure recovery remain review items.

This preview is intended for people who understand experimental camera-firmware
research and can accept the possible complete loss of their camera and data.
Do not infer safety or general support from one owner's successful test.

## Credits

Built on the research and source provided by
[WonderLantern/z7-qemu](https://github.com/WonderLantern/z7-qemu) and
[totwoto02/z7-firmware-extensions](https://github.com/totwoto02/z7-firmware-extensions).
Their original notices/licenses are preserved. See [UPSTREAMS.json](UPSTREAMS.json)
for the vendored source provenance. This repository's changes are independent work.
