# Laptop handoff — October 20, 2026

## Source publication checkpoint — October 24, 2026

The owner requested a source push and review of possible contributions to both
vendored upstream projects. The root README now reflects the hardware reports:
WAV Preview works, automatic capture sound repeats during live view, and Enabled
OFF contains the loop. Historical preparation and test instructions below are
not current installation clearance. The port audit and flash hold remain active.

The latest stock assisted-emulator observation collected three distinct
0x041F0001 -> 0x04190001 callback deliveries without a shutter action. Controller
mode was 0 and the native capture-service state byte was 9 in each observation.
Read the new section in [CAPTURE_EVENT_TRACE.md](CAPTURE_EVENT_TRACE.md) and the
sanitized summary `evidence/20261024-stock-liveview-observation.json`. This is
negative evidence against the current trigger, not a physical-camera trace.

A separate stock capture-request probe timed out before recording any action;
it establishes no positive capture signal. No firmware source was changed for
these observations and no new candidate was built, staged or installed. Private
RAM, disassembly, emulator sessions and probe logs stay excluded from publication.

Publication checks were rerun on October 24: 8 root host tests, 11 QEMU Python
tests, 270 renderer contracts, 398 ISP contracts, firmware-free QMP realization,
and 14 synthetic patch/container tests passed. Existing-image probes passed 24
native-callback, 14 still-file and 60 selected callback/property checks. The
retrigger audit still fails both required no-photo rejection checks; its two
OFF checks pass. These results do not clear automatic shutter sound. No new
firmware build, camera update or sanitizer run was included. See
`evidence/20261024-source-validation.json` for scope and exclusions.

## Backward tracing anchor: still-file record — October 22, 2026

The owner asked how to obtain a verified per-photo signal. Read
[STILL_FILE_TRACE.md](STILL_FILE_TRACE.md). Original still-file finalization wrapper
0x1026FADC sends 0x041E0002 with a record ID through a separately registered
callback. Native record helpers expose slot/group/number/kind fields and compare
records while ignoring kind. Fourteen offline evidence checks execute that
wrapper, registration/dispatch and ID helpers with controlled file operations.

This is a new backward-tracing anchor, not a chosen shutter hook. File completion
can lag exposure, repeat or occur multiple times per photo; physical timing and
per-photo cardinality remain unverified. Follow upstream exposure/record creation
before connecting audio. No firmware source, image or camera/card content changed;
Enabled OFF and the flash hold remain in force.

## Native callback trace — October 22, 2026

The owner asked to keep tracing. Read [CAPTURE_EVENT_TRACE.md](CAPTURE_EVENT_TRACE.md).
The new audit executes the original registered Z7 callback instead of stubbing
its return. Two supplied classification cases schedule no native work, but the
existing sound hook still queues audio. Six stock/patched cases retain native
scheduling while exposing that unconditional custom admission. A separate native
zero-count AutoRelease probe also emits its request notification without invoking
release control, ruling that notification out as sufficient per-photo evidence.

All 24 trace evidence checks pass; this confirms the defect, not a replacement
trigger or candidate clearance. Real per-photo signal semantics remain unresolved.
Enabled OFF is owner-confirmed to stop repetition. Firmware source and existing
images were untouched; no rebuild, staging or camera write. The flash hold remains.

## Latest hardware failure: repeated live-view audio — October 21, 2026

The owner reports repeated sound during live view and Capture audio busy on
opening the menu. Read [LIVEVIEW_SOUND_REGRESSION.md](LIVEVIEW_SOUND_REGRESSION.md).
The owner confirms Enabled OFF stops the repeating sound on the camera. Leave it
OFF. This confirms containment, not correct shutter triggering. The latest
silent-property candidate is associated by sequence, without firmware readback.
It fails the shutter-cue behavior requirement; audible repetition is not success.

An audit-only probe of the existing binary queues three requests from three
notifications without an independently identified photo transaction, and confirms
the pending/finished restart path. Two required rejection checks fail; two compiled
OFF checks pass with controlled device boundaries. The callback's photo-specific
meaning was never established. Earlier passing callback tests missed this case.
No firmware source change, rebuild, staging, camera write or rollback occurred.
The port audit and flash hold below remain in force.

## Current owner caution and port audit hold — October 21, 2026

The owner raised the risk of ported camera code leaving the Z7 unusable and asked
for more care. Further flash recommendations and candidate staging are on hold
pending an independent Z7 port audit. Read [PORT_AUDIT.md](PORT_AUDIT.md) before
continuing. The most recently staged silent-property image remains experimental;
the earlier preparation/testing notes below are not clearance to install it.
Do not interrupt a camera update already running. Do not automatically roll back,
reflash stock, or prepare another candidate as a response to this concern.

Initial review confirms a Z7 stock base with Z30-derived custom feature code, not
proof that all copied interfaces are correct. The inventory identifies 23 direct
literal native sound call targets and 17 full-image edits; dynamic/assembly-embedded
targets and lifecycle/recovery gaps remain. The native translation dictionaries
are not used by the generated routines, so reviewing them alone is insufficient.
No camera/card/firmware mutation occurred in this audit turn. No complete port
audit or verified emergency recovery is claimed.

## Current Silent photography property correction — October 21, 2026

The owner followed the capture-start candidate's installation/test instructions:
still no audio, now with heading Silent mode required after a silent photo.
This supports trigger reachability; the remaining mode gate queries the wrong
property. The Z7's own Silent photography page 0xB2 constructor reads 0x576;
the port retained Z30 key 0x57B. Read [SILENT_PROPERTY_FIX.md](SILENT_PROPERTY_FIX.md).

New private build/review suffix: `20261021-silent-property-01`, full EG SHA-256
`9e636d645281ee9f92cb150b6dcc8d771b21ff95c47e45f538d951a1d932420b`.
Exactly one appended instruction byte plus two CRC bytes differ from the previous
candidate; length and menu/Preview code are unchanged. Both sound presets pass
60 capture checks and 18 playback checks using the original native property
getter/tables. Contradictory Z7/legacy values also execute the original Silent
photography menu constructor, exposing the previous mocked-getter test gap.
Sixteen firmware tests and reproducible/CRC checks for all four presets pass.
The candidate was staged on the re-verified E: Sony QD-G240F card at
2026-10-22 04:38 UTC (October 21 locally). Full SHA-256 readback matched the
candidate above. The previous card EG was backed up privately; SHUTTER.WAV and
other card files were preserved. The review bundle's card-staging.json records
the copy. The subsequent live-view regression above supersedes this pending
status: installation is inferred, and correct physical capture audio has failed.

## Current normal-capture callback correction — October 21, 2026

The owner now reports Waiting for capture after silent shooting, and Silent mode
required after one mechanical photo with the feature still enabled. This supports
the installed diagnostic build and late-hook mode gating, with no late-hook
notification observed for silent capture. Installation is inferred from the unique
headings; no readback or explicit updater-completion report was supplied.

Read [CAPTURE_START_FIX.md](CAPTURE_START_FIX.md). A separate normal native
callback at 0x100726AC was outside the previous diagnostic's coverage. The new
hook queues sound from its normal notification and retains the late hook for
diagnostics only, avoiding duplicate cues. All three callback paths and the full
native dispatcher now pass 48 capture checks for each sound preset; the existing
18 playback checks and 16 firmware tests also pass. Hardware triggering remains
unresolved until a camera retest.

New private build/review suffix: `20261021-capture-start-02`, full EG SHA-256
`efcfbda40439354e8707a2c1e8c0b16b5e47a27c0fe8999110ca98eb9f15dc1c`.
It was staged on the re-verified E: Sony QD-G240F card at 2026-10-22 04:10 UTC
(October 21 locally). Full SHA-256 readback matched the candidate above. The
previous card EG was backed up privately; SHUTTER.WAV and other card files were
preserved. The private review bundle's card-staging.json records the copy.
The owner subsequently followed the installation/test instructions and reported
Silent mode required after the silent photo, with no audio. Installation is
inferred from that sequence without readback; the property fix above supersedes
this candidate. The first offline relocation attempt failed
null-callback branch checks and was corrected before producing this candidate.
The candidate passes 13 admission checks, 12 private review checks and all 17
assisted-QEMU sound-menu checks with 30 native key events and return to live view.
No abort was observed in that run. The source graph has been refreshed locally.

## Startup splash investigation — October 21, 2026

The owner asked whether a custom splash could be installed. Read
[SPLASH_SCREEN_FEASIBILITY.md](SPLASH_SCREEN_FEASIBILITY.md). Private stock scans
confirm PNG resources and libpng strings, with 198 of the first 200 signature
hits verified by Pillow and 16 large resources verified by chunk CRC. An original
compact embedded image plus a one-time native UI hook is promising; no startup
logo replacement, callable decoder interface or power-on-only hook is yet proven.
The current EG has 489,334 bytes of room under the existing patcher limit. This
was read-only firmware investigation; no splash build or card/camera write occurred.

## Current capture-trigger investigation — October 21, 2026

The owner clarified that WAV playback works but shutter replacement does not,
with Enabled ON, SHUTTER.WAV selected and Nikon Silent photography ON. Read
[SHUTTER_TRIGGER_FIX.md](SHUTTER_TRIGGER_FIX.md). A native branch bypasses the
old hook entry and lands inside its patched literal; this is reproduced offline.
The new shared-callback hook preserves both native paths and passes 24 capture/
diagnostic checks for both sound presets. Diagnostic titles distinguish callback
reachability from mode/busy gating. The role of this defect in the failed camera
test remains unknown; actual shutter-triggered sound still fails by owner report.

After diagnostic staging, the owner again reported no shutter sound and initially
could not identify the expected heading (described as a "tile"). The later
Waiting for capture / Silent mode required comparison is recorded above. The diagnostic
is the page title above Enabled/Sound file/Preview/Reload, not a new menu row.
With Enabled ON and no error it should initially read Waiting for capture;
after a photo read that heading without power-cycling or selecting ON again,
which resets the capture status.

New private build/review suffix: `20261021-shot-fix-01`, full EG SHA-256
`51dd7feb01e991d0cbce93e952ac42be98981dca510187e2767141ec8974dd9b`.
The diagnostic candidate was staged on the re-verified E: Sony QD-G240F card at
2026-10-22 03:39 UTC (October 21 locally), with full SHA-256 readback matching
the candidate above. The previous card firmware was backed up privately;
SHUTTER.WAV and other card files were preserved. The private review bundle's
card-staging.json records the copy. The later unique diagnostic headings above
support this build running on the camera, inferred without firmware readback.
The new build also passes 13 candidate checks, 12 private review checks and all
17 assisted-QEMU sound-menu checks on an isolated retry. The first QEMU attempt
stopped during assisted menu entry; both outcomes are preserved in the sanitized
capture evidence. Card staging and the later inferred installation are recorded
above; shutter-triggered audio has not passed.

## Current audio correction — October 21, 2026

**Latest owner result: "the wav actually works now!"** This follows staging the
corrected candidate below and the installation/Preview instructions. Record this
as owner-reported audible WAV playback; the subsequent capture failure above
separates that result from shutter-triggered playback.
Corrected installation is inferred from that sequence, without firmware readback.
Shutter-triggered playback, repeated-use stability and recovery are not established.

Read [AUDIO_PLAYBACK_FIX.md](AUDIO_PLAYBACK_FIX.md). The owner tested the stronger
WAV: still no audible output; Sound busy appears when moving the selector after
activation. The file matches every documented 8 kHz/mono/16-bit/canonical-header
requirement. The installed code reads the format table instead of the native busy
byte, and requests a type outside the native exclusive range. Both blockers are
corrected in source, with five failing checks reproduced against the installed
image and all 18 request-path checks passing for corrected full and sound-only.

New private build/review directory suffix: `20261021-audio-fix-01`. Full EG SHA-256
is `770408b99ff547dd972486656285307b17e4ff2674937dbb50f144200233b7be`.
The corrected firmware was staged on the re-verified E: Sony QD-G240F card at
2026-10-22 03:08 UTC (October 21 locally). Full SHA-256 readback matched the
candidate above; the previous card firmware was backed up privately, and the
stronger SHUTTER.WAV and other card files were preserved. The private review
bundle's card-staging.json records the copy. The owner subsequently reported
working WAV playback as recorded above. Earlier silent-playback reports below
describe the previous build, before this correction.

The corrected full image passed 17 isolated QEMU menu checks with 30 native key
events. All four builds are reproducible with valid CRCs; 16 existing firmware
tests, 13 candidate checks and 12 private review/header checks passed. Both sound
presets passed 18 playback-admission contracts. Results are recorded in
`evidence/20261021-audio-playback-fix.json`. Root default/native app configuration
still names the earlier private build; launch the corrected build explicitly
when inspecting it. Restart validation of an older payload against the changed
patcher source will intentionally reject it; the previous binaries are preserved.

## Latest hardware result — October 21, 2026

The owner reports **the flash worked and the sound setting is present** on the
original Z7 C 3.80, no paid RAW-video upgrade. This follows the camera's
`Current A3.80 → New A3.80` confirmation and an updating warning/progress report
at about 30%. The verified card candidate was the full EG with SHA-256
`9e98eae9b726d1ced0e9cef60c89b6ef25eff369430673e753b5c3054be4f6b4`.

This establishes an owner-reported same-version installation, subsequent camera
operation and visible sound-menu entry. The exact completion message, firmware
readback, submenu operation, WAV loading/playback, capture, video and recovery
have not been independently observed. Do not expand this result to full hardware
validation or a proven rollback path. Earlier preparation notes below describe
the state before this first installation.

A private canonical test sound is prepared at
`.private/sound-test/20261021-01/SHUTTER.WAV`: 0.18 seconds, 660 Hz, 8 kHz,
mono signed 16-bit PCM, with fades and approximately 6% full-scale peak. Its
44-byte header, sample count and exact normalization roundtrip passed. At the
owner's request it was copied to the verified E: Sony QD-G240F card root as
`SHUTTER.WAV`; complete readback matched SHA-256
`e8bc84dc82c53e36c5ec8fc8a28556272b367a7e93ed0e0c91782797ea7ea5cb`.
Existing card files were preserved. The private sound-test `card-staging.json`
records the copy. The owner then reported **Sound file shows SHUTTER.WAV;
Preview produces no error but nothing audible**. Loaded-file/menu behavior is
owner-reported; audible output has not passed. Preview is designed to work with
Enabled OFF. Ordinary photo/playback has not been explicitly reported.

On resuming October 21, a stronger test WAV was staged on the re-verified E:
Sony QD-G240F card: `.private/sound-test/20261021-02/SHUTTER.WAV`, 14,444 bytes,
SHA-256 `d9b38aae45fbe7cb6ccbe79e64bafc40c2d69d987beb6608f00d8c0fc1145ac0`.
It contains three faded notes at 1, 2 and 3 kHz, 0.9 seconds total, 50% peak
amplitude. The earlier 0.18-second/6% tone is preserved locally, including a
verified copy of the old card file. Both WAVs passed the exact installed full
image's native validator and converter; every converted stereo PCM byte matched
the independent interpolation reference, output was nonzero and buffer guards
held. This checks parsing/conversion, not audio scheduling or speaker output.

The new card file passed complete SHA-256 readback. Firmware and other card
files were not changed; another flash is not needed for this test. Next safely
eject, insert into the camera, select Sound file → SHUTTER.WAV again and use
Preview with Enabled OFF. Audible output from this stronger file is pending.
If still silent, investigate native audio routing/gain and use normal Nikon
beeps as a separate control; do not infer a volume-only cause from the first test.

## Native Windows continuation — October 21, 2026

The app now runs on this laptop without WSL. Double-click `Start-Z7.cmd` or open
<http://127.0.0.1:8787/> while the prepared server is running. It was left paused
after verification to save CPU; click **Resume**. English browser controls and
keyboard/menu instructions are included. The selected private build is
`.private/builds/20261021-laptop-01`; the earlier laptop build is preserved.

QEMU 10.2.4 was compiled from the pinned archive with a separate MSYS2/UCRT64
toolchain under `.private/`. The existing system MSYS2 was not updated. A private
CPython 3.12.14 core and the local virtual environment keep the prepared app
independent of the Codex runtime cache. Firmware, binaries, guest diagnostics,
screenshots and Graphify output remain ignored. No camera/card writes occurred.

Current native validation: 16 firmware tests with no skips; all four payloads
match the accepted emulator baseline; 13 candidate admission/corruption checks;
5 launcher tests; 11 Python RAW/input tests; 270 renderer and 398 ISP contracts;
firmware-free QMP/TCP realization; 21 general UI checks; 17 sound-menu checks
each for full and sound-only. ASan/UBSan were not run on this Windows host.
See [the sanitized native results](evidence/20261021-windows-validation.json).

Cold assisted boot took about 140 seconds. The old fixed 12-second menu-return
verification window expired on this host despite subsequent scene recovery.
The verifier now records per-cycle timing with a configurable bounded deadline;
the three successful returns took 16.890, 16.985 and 18.453 seconds, each with
zero scene-region pixel RMS difference, continued ISP batches and the same guest
session. Native Windows stdio corrupted batched QMP smoke requests; the smoke
check now uses sequential commands over localhost TCP, matching the controller.

Fresh setup/rebuild commands are in [WINDOWS_BUILD.md](WINDOWS_BUILD.md).
`Setup-Z7.ps1` builds privately and runs native host/candidate checks;
`tools/check_windows.ps1` repeats firmware-free host checks. Linux setup now
also adds the vendored patcher to the new venv's import path, which is required
for candidate validation outside the firmware builder. WSL command construction
was unit-tested; an actual Linux/WSL run was not repeated on this laptop.

No complete modified Nikon container, complete camera updater acceptance,
recovery route or actual WAV playback was validated by the emulator work.

## Hardware preparation continuation — October 21, 2026

The owner authorized an experimental flash attempt and confirmed original Z7,
C 3.80, **no paid RAW-video upgrade**. Read [FLASH_ASSESSMENT.md](FLASH_ASSESSMENT.md)
before continuing. A separate native EG path was found in the Z7 stock code;
a complete outer container is not the only route worth investigating. Twelve
bounded native header/filename checks and all stock container/module CRC checks
passed. The private bundle `.private/flash-review/20261021-01/` contains the
reproducibly rebuilt full candidate as `candidate/EG161080.BIN` and separate
untouched stock inputs. This is an offline review, not hardware acceptance.

The candidate retains its CRC and entire appended tail. The native filename
pattern is `EG1610??.BIN`; the longer literal filename used in upstream build
examples does not match the tested loop (FAT aliases are untested). The storage
descriptor accommodates the candidate, but the complete updater and flash writer
remain untested. Same-version acceptance is unresolved. No verified emergency
recovery is available; stock files are not a full flash/calibration backup.

The owner then identified E:. It was verified as a removable, writable Sony
QD-G240F XQD/exFAT card, with no root user/firmware files. At 10:47 UTC the
candidate was copied as `E:\EG161080.BIN` and its complete SHA-256 read back as
`9e98eae9b726d1ced0e9cef60c89b6ef25eff369430673e753b5c3054be4f6b4`.
No formatting/deletion or camera flashing occurred. The private bundle's
`card-staging.json` records the copy. Battery charge and the real firmware screen
are still unconfirmed. Eject normally and stop at the camera's firmware version
screen, before selecting Update or Yes, for the proposed recognition check.

The owner subsequently reported the actual camera page shows **C 3.80** with
**Done, Update, Delete firmware files**. This is a user-reported recognition
observation; update execution, same-version installation and post-boot behavior
are still untested. Next inspect the separate confirmation dialog after choosing
Update, before choosing Yes, and confirm a fully charged battery.

The owner then reported the separate warning/confirmation dialog: **Update?
Current A3.80 → New A3.80**, Yes/No. This confirms the same-version choice is
offered, not that programming or post-boot operation succeeded. No Yes selection
or completed flash has been reported. The battery prerequisite remains necessary.

## Current state

The local firmware build and assisted QEMU run work. We corrected the sound
port's live-view failure and custom-menu crashes. Build `20261020-09` is the
accepted emulator baseline. All source and local fixes are included in the two
component directories as regular files; cloning this repository needs no submodule
initialization. Upstream origins/commits are recorded in `UPSTREAMS.json`.

The owner's physical camera is an original **Z7, C 3.80**, without the paid
RAW-video upgrade (confirmed October 21). The first same-version full-EG flash
and visible sound-menu entry are now owner-reported successful; see the latest
hardware result above. Audio, capture and recovery still need physical tests.

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

1. Continue the dedicated EG updater investigation from `FLASH_ASSESSMENT.md`.
   Stock container/module layout and CRCs are mapped; the complete outer digest
   remains unsolved for Z7. Our `.main.bin` is a QEMU payload; `.eg.bin` is an EG
   module. Neither is a validated camera update container.
2. Establish complete updater version/compatibility checks. The owner's camera
   already has 3.80; Nikon's official page lists 1.00–3.70 as the supported starting
   versions. Modified same-version acceptance is unknown. No paid RAW upgrade.
3. Find a concrete, model-specific boot recovery/rollback route and what still works
   after a bad boot. Reinstalling stock requires a functioning installation path;
   do not assume a saved stock file alone provides recovery.
4. Investigate actual WAV/card/audio and capture behavior. Current tests only prove
   missing-file handling and selected assisted-emulator paths. No verified real
   sensor, AF, shutter timing, recording or update acceptance follows from them.

Preserve all original inputs and earlier candidates. Card staging is complete;
the reviewed camera recognition step is next. This handoff does not authorize posting firmware, private dumps or
screenshots to the public repository.

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
