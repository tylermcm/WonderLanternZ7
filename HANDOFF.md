# Laptop handoff — October 20, 2026

## Current state

The local firmware build and assisted QEMU run work. We corrected the sound
port's live-view failure and custom-menu crashes. Build `20261020-09` is the
accepted emulator baseline. All source and local fixes are included in the two
component directories as regular files; cloning this repository needs no submodule
initialization. Upstream origins/commits are recorded in `UPSTREAMS.json`.

The owner's physical camera is an original **Z7, C 3.80**. Paid RAW-video upgrade
status is unknown. No camera/card writes or flashing occurred. The user discussed
accepting experimental risk, but no camera-installable package has been built.
The immediate continuation is to investigate packaging, updater acceptance and
recovery before preparing a hardware attempt.

## Verified results

| Gate | Result |
| --- | --- |
| Upstream patcher tests with real private input | 16 pass, none skipped |
| Repeated builds and module CRC | All four presets pass |
| Histogram/level gate executions | 1,024 pass per applicable preset |
| Config hook calling convention | 3 cases pass per sound preset |
| Route fallback versus native instructions | 6 cases pass per sound preset |
| Data fallback versus native instructions | 4 cases pass per sound preset |
| Menu layout/callback/native hierarchy contracts | 20 checks pass per sound preset |
| Candidate admission and corruption rejection | 13 checks pass |
| Full image general UI, pause/resume, three MENU roundtrips | 21 checks pass |
| Full and sound-only submenus, independently | 17 checks each, 30 native key events each |
| Earlier QEMU synthetic tests | 11 Python, 270 renderer, 398 ISP checks; ASan/UBSan clean |

The submenu checks include the actual active page and RAM state, visible titles,
OFF, ON without a WAV, failed file selection, Preview/Reload without a file,
back/reopen with native selection retention, and return to the reference processed
live-view scene with continued ISP batches. Real WAV loading/playback is untested.
Read `SOUND_MENU_FIX.md` for the exact bug mechanisms and `LAB_REPORT.md` for history.

## Fresh laptop setup

Use Python 3.12+ in Linux or an explicitly selected WSL distribution. The desktop
used **Ubuntu**, not the unrelated `ubuntu-noble` coursework distro. Do not reset
or replace an existing distro. The upstream component docs mention older paths and
`ubuntu-noble-nikon`; the root instructions below govern this workspace.

1. Clone this repository and open a Linux/WSL shell in the checkout.
2. Install the OS dependencies and run setup:

```sh
sudo apt-get update
sudo apt-get install build-essential ninja-build pkg-config python3-venv \
  libglib2.0-dev libpixman-1-dev zlib1g-dev libfdt-dev
python3 tools/setup_lab.py --jobs 4
```

The helper creates `~/.local/share/wonderlantern-z7/venv`, installs the tested
dependencies, builds checked QEMU 10.2.4 and generates synthetic CMOS inputs.
The QEMU archive hash is checked by `z7-qemu/tools/build.py`. Allow several GB;
use `--jobs 2` on a smaller laptop. Generated build files live on the Linux
filesystem. The local interpreter/distro configuration is stored in ignored
`.private/lab-environment.json`; no desktop username is required.

3. Obtain your own official input from
   <https://downloadcenter.nikonimglib.com/en/download/fw/558.html> and place it at
   `.private/stock/Z_7_0380.bin`.

| Input | Size | SHA-256 |
| --- | --- | --- |
| Original container `Z_7_0380.bin` | 34,472,614 | `07cf19513ada5b770caec4cfc3531a6734c48aede28dcec037f0f8374ef441a2` |
| Extracted stock MAIN | 33,052,088 | `e6df1764323fb1c287159dd3ce1c84ac93c72b96ba6eb09c070295c093fecbff` |

The patcher validates the original container and extracted module automatically.
Keep original firmware and all generated candidates private.

4. Build and validate locally:

```sh
LAB_PY="$HOME/.local/share/wonderlantern-z7/venv/bin/python"
"$LAB_PY" tools/build_firmware.py --output .private/builds/20261020-09
"$LAB_PY" tools/check_candidate_inputs.py --build .private/builds/20261020-09
"$LAB_PY" tools/probe_sound_menu.py --build .private/builds/20261020-09 \
  --output .private/evidence/laptop-full-menu-01 --exercise
"$LAB_PY" tools/probe_sound_menu.py --build .private/builds/20261020-09 \
  --preset shutter-sound --output .private/evidence/laptop-sound-menu-01 --exercise
```

Output directories must be new. After the first build use a new suffix and pass
that directory to the launcher. Expected MAIN outputs for unchanged firmware source:

| Preset | Size | SHA-256 |
| --- | --- | --- |
| full | 33,064,940 | `1d456c84709650e90cc6decd0877a9a51d4692bacc5477fa21ea28fba67cfb76` |
| shutter-sound | 33,064,840 | `0fe02a264926fe215484fd233b994d26fbdf9e6e4b2358df30027b8d82a93c0d` |
| liveview-dual | 33,052,156 | `b15532154d9bff9aea4649b8977f2c9ed737aba4256a7cc5e40880024761b9ff` |
| m900 | 33,052,120 | `806c026b3c1aed197326ad8cc7e78692016b488d863264b6ce3a7f24d28038db` |

5. Start the browser demo:

```sh
"$LAB_PY" tools/launch_z7.py
# Another local terminal, while the server runs:
"$LAB_PY" z7-qemu/tools/verify_ui.py --menu \
  --output .private/evidence/laptop-general-ui-01
```

On Windows use `Run-Z7.ps1 -WslDistro Ubuntu` after completing Linux setup/build.
`--linux-python` and `--wsl-distro` on `tools/launch_z7.py` support custom setups.
Open <http://127.0.0.1:8787/>. MENU/arrows/OK/DISP are native guest inputs. From
fresh shooting: MENU, left twice, down four times, right, up, OK opens Shutter sound.
Stop an existing owned server before reusing its port. The browser Stop control
stops the guest but leaves the HTTP server available for inspection.

## Next investigation

1. Map the original Nikon update container and module lengths/checksums and determine
   how a modified EG module could be packaged. Our `.main.bin` is a QEMU payload;
   `.eg.bin` is an EG module. Neither is a validated camera update container.
2. Establish updater version/compatibility checks. The owner's camera already has
   3.80; Nikon's official page lists 1.00–3.70 as the supported starting versions.
   Modified same-version acceptance is unknown. Confirm the paid RAW-video state.
3. Find a concrete, model-specific boot recovery/rollback route and what still works
   after a bad boot. Reinstalling stock requires a functioning installation path;
   do not assume a saved stock file alone provides recovery.
4. Investigate actual WAV/card/audio and capture behavior. Current tests only prove
   missing-file handling and selected assisted-emulator paths. No verified real
   sensor, AF, shutter timing, recording or update acceptance follows from them.

Preserve all original inputs and earlier candidates. No scheduled work or hardware
attempt is pending. This handoff does not authorize posting firmware, private dumps
or screenshots to the public repository.

## Source orientation and troubleshooting

- Sound fixes: `z7-firmware-extensions/src/z30_extensions/features/` files
  `shutter_sound_z7.py`, `sound_layout_z7.py`, `sound_ui_z7.py`.
- Root `tools/verify_sound_*.py`: native instruction/layout regressions.
- `tools/probe_sound_menu.py`: owns an isolated guest and captures abort context.
- `z7-qemu/tools/firmware_input.py`: re-creates the candidate from private stock
  and compares every payload byte before launch/restart.
- `z7-qemu/tools/interactive.py`: native-key browser controller and assistance.
- `z7-qemu/qemu/nikon-z7-lab.c`: emulated peripherals and diagnostics.
- Use Graphify when available: `graphify .`, then `graphify query "question"`.
  Generated graphs are excluded and can be recreated from this source.

Do not trim appended patch code back to the stock MAIN length. Only the final two
EG CRC bytes are omitted for QEMU. Keep calibration/startup assistance explicit;
do not conceal unknown device accesses by supplying invented completion values.
Capture the abort reporter at Thumb `0x100545EC`; R0 identifies exception kind,
R1 points to saved context. Copied exception strings on its stack are insufficient
to identify the fault. See the probe for checked offsets.

Some desktop command-runner contexts could not start WSL/network worker threads;
the existing Ubuntu environment worked through the desktop process runtime. That
was a host tool issue, not a reason to reset the distro. A normal laptop shell
should use the ordinary commands above. Do not copy desktop `.local` manifests:
they contain absolute host paths and QEMU fingerprints; regenerate them.

## Included and excluded

All component source, local fixes, root helpers, license notices, reports and a
sanitized validation summary are included. Original Nikon input, generated firmware,
QEMU executable/source downloads, RAM/disassembly traces, camera UI PNGs, local
tokens, virtual environments and runtime logs remain only on the desktop. Rebuild
them from your own input. The public source is sufficient to reconstruct the lab;
it is not a backup of the ignored private artifacts.
