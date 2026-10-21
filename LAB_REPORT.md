# Nikon Z7 firmware lab — October 20, 2026

The Z7 C 3.80 extensions build locally and run in the WonderLantern QEMU machine.
The upstream sound port's live-view and submenu failures have local corrections.
Build 09 passes 21 general UI checks and 17 sound-menu checks in the combined
full image, including a return to processed live view after exercising the menu.
The primary demo at <http://127.0.0.1:8787/> now runs that full image.
Real WAV playback, camera operation and updater acceptance remain unverified.

The owner's camera reports C 3.80. Paid RAW-video upgrade status is unknown.
No physical camera connection, card preparation or flashing was performed.

## Reproducible inputs

- Emulator: <https://github.com/WonderLantern/z7-qemu>, commit `97abf0b81cd3211f8374a38987a0beaf4549b90f`.
- Extensions: <https://github.com/totwoto02/z7-firmware-extensions>, commit `96d03002220ecb0da9e387f88361632b9c3daa54`, plus the local sound-hook corrections.
- Official Nikon input: <https://downloadcenter.nikonimglib.com/en/download/fw/558.html>.
- `Z_7_0380.bin`: 34,472,614 bytes, SHA-256 `07cf19513ada5b770caec4cfc3531a6734c48aede28dcec037f0f8374ef441a2`.
- Extracted stock MAIN: 33,052,088 bytes, SHA-256 `e6df1764323fb1c287159dd3ce1c84ac93c72b96ba6eb09c070295c093fecbff`.
- QEMU 10.2.4 was built from the upstream archive with its pinned SHA-256 checked.

Private firmware, outputs, screenshots and logs are in `.private/` or the emulator's
ignored `.local/` directory. They must stay out of public commits and attachments.

## Results

| Image or check | Result |
| --- | --- |
| Stock MAIN, normal BIOS loader | All 21 UI checks pass |
| Stock MAIN, generic loader used for candidates | All 21 UI checks pass |
| Histogram + level only | All 21 UI checks pass |
| M900 only | All 21 UI checks pass; a real 900-second exposure is untested |
| Upstream full and sound-only images | Boot/shooting overlays render, but ISP stalls at one batch and processed live-view scanout fails |
| Corrected full image, build 02 | All 21 UI checks pass, including three MENU roundtrips in one guest |
| Corrected full image, build 09 | All 21 general UI checks pass |
| Build 09 full sound submenu | 17 checks pass across 30 native button events: titles, page identity, OFF, missing-file ON/load/Preview/Reload, back/reopen and return to processed live view |
| Build 09 sound-only submenu | Same 17 checks pass, including bounded asynchronous return to processed live view |
| Build 09 menu contracts | 20 checks per sound preset pass: actual Setup object, terminated layouts, native shell hierarchy, viewport sizes and executed native callback stack/return behavior |
| Build 09 hook comparisons | Config 3, route 6 and data 4 instruction-level cases pass per sound preset |
| Upstream firmware tests with real private input | 16 pass, none skipped |
| Histogram/level ARM gate verification | 1,024 executions pass for each applicable candidate |
| Candidate admission checks | 13 pass, including truncation, altered bytes/tail, report mismatch, wrong model and wrong stock input |
| Emulator synthetic checks | 11 Python tests, 270 renderer checks and 398 ISP checks pass; ASan/UBSan report no issues |

UI checks cover synthetic RAW transfer, image processing and scanout, scene detail,
red no-card icon, pause/resume and three menu roundtrips. They do not test a real
sensor, autofocus, shutter timing, card access, recording, speaker or firmware updates.
The emulator uses documented startup assistance and synthetic calibration inputs.

## Local corrections and evidence

1. The upstream sound config trampoline pushed only LR, misaligning SP by four bytes.
   It now saves R4/LR together.
2. The config wrapper restored the input R0 over the native parser's result. Its
   caller immediately compares that result with 1. The wrapper now returns the
   parser result. This correction restores live view in the combined build.
3. The new Setup row used the row count as a label index. It now references the
   slot populated by `labels()`. The actual Setup object also had to be corrected.
4. The route fallback resumed inside its own jump literal and omitted a displaced
   `MOVW R9,#0x3A0`. It now reproduces the complete prologue and resumes at `0x1048B406`.
5. The data fallback applied a native `+0x10` twice. Its reconstructed R5 literal
   is now `0xA188D190`, matching the original instruction before that addition.
6. Custom callback pointer `0x10405261` skipped the required native PUSH. Correct
   pointer `0x1040525F` preserves the caller's stack and return address.
7. The port's Setup object was unrelated page 0x18D. The corrected page 0x19B
   matches the patched metadata and seeds the visible Shutter sound label.
8. The old leaf layout omitted its terminator. A validated native page-0x2A
   template supplies header, back bitmap and terminator within the copied 96 bytes.
9. Full-page sound menus now share the native menu-shell parent. Parenting them
   to Setup caused a redraw after its widget collection had been freed.
10. Each private viewport now fits all of its rows; its dynamic title is explicitly
    made visible. All four root actions and all five file choices render.

See `SOUND_MENU_FIX.md` for fault evidence, final hashes and reproduction commands.

`tools/verify_sound_hook.py` executes the actual callsite, trampoline and fallback
in Unicorn. Three controlled native return values all fail against the original
image and all pass with the correction, checking parser arguments, aligned SP,
return value, saved R4 and restored stack. It does not execute hardware playback.

The loader now has an explicit candidate mode. It independently rebuilds the
requested preset from the fingerprinted Nikon container and compares every MAIN
byte before launch. It repeats validation on restart. Stock checks remain intact.
The generic raw loader preserves appended code; only the final two module CRC
bytes are omitted. Trimming a patched image to the original stock length is wrong.
DISP/D was added using the native AO table's checked bank/mask mapping (index 83).
Manual DISP cycling in the final display-patch demo renders the native electronic
level over processed color bars. Simultaneous histogram visibility remains
unconfirmed under this synthetic, no-lens profile.

QEMU can optionally capture fault-stack and exception diagnostics. Unmodeled
hardware accesses still stop the guest; no fake response was added to hide faults.
The earlier `0x10000AAA` stop was the abort reporter's later activity. Capturing
the reporter at entry establishes Data abort (kind 1), rather than inferring
exception type from copied strings on its stack. Build 06 returned into a RAM
page object because of the skipped callback PUSH; build 07 then exposed the
invalid parent redraw. Both are corrected; the final full menu run has no abort.

## Artifacts and runs

- `.private/builds/20261020-01/`: original upstream binaries and reports, preserved.
- `.private/builds/20261020-02/`: config return/alignment correction; full image passed 21 UI checks.
- `.private/builds/20261020-03/`: earlier label-index correction; preserved failed menu candidate.
- `.private/builds/20261020-04/`: incomplete Windows build attempt; preserved.
- `.private/builds/20261020-05/` through `20261020-08/`: intermediate corrections and diagnostics, preserved.
- `.private/builds/20261020-09/`: current source; reproducible candidates, source hashes and all offline checks.
- `.private/evidence/stock-ui-02/result.json`: stock baseline, 21 checks pass.
- `.private/evidence/stock-raw-ui-01/result.json`: loader control, 21 pass.
- `.private/evidence/dual-ui-01/result.json`: histogram/level candidate, 21 pass.
- `.private/evidence/m900-ui-01/result.json`: M900 candidate, 21 pass.
- `.private/evidence/full-ui-01/result.json`: original full image times out without processed scanout.
- `.private/evidence/full-fixed-ui-01/result.json`: corrected full image, 21 pass.
- `.private/evidence/original-sound-hook.json` and `fixed-sound-hook.json`: instruction-level failure/success evidence.
- `.private/evidence/corrected-sound-menu-error.json` and `sound-menu-fault-stack.txt`: historical failure.
- `.private/evidence/sound-menu-events-09/result.json`: full menu, 17 checks pass; screenshots are actual QEMU output.
- `.private/evidence/sound-only-menu-events-09b/result.json`: sound-only menu, same 17 checks pass.
- `.private/evidence/full-fixed-ui-09/result.json`: final full image, all 21 general UI checks pass.
- `.private/evidence/primary-sound-demo-09.png`: current full demo displaying the repaired submenu.
- `.private/patches/`: source diffs; new helper sources remain in this workspace.

The histogram/level and M900 binaries are identical across these build folders.
The standard port is 8787. Historical test ports are not intended as active demos.

## Run and rebuild

Ubuntu is explicitly selected as `Ubuntu`; no WSL distro was replaced or reset.
Linux dependencies and QEMU are under `/home/dixie/nikon-z7-lab/`, with sources
in this Windows workspace. Windows firmware tools are isolated in `.venv/`.

From PowerShell in this directory:

```powershell
# Default: the corrected full build 09, using port 8787.
.\Run-Z7.ps1

# Individual presets, preferably after stopping the previous server.
.\Run-Z7.ps1 -Preset m900
.\Run-Z7.ps1 -Preset stock

# The full research image includes the corrected sound submenu.
.\Run-Z7.ps1 -Preset full

# Rebuild into a fresh directory; existing results are never overwritten.
.\.venv\Scripts\python.exe tools\build_firmware.py --output .private\builds\next-run
.\.venv\Scripts\python.exe tools\check_candidate_inputs.py --build .private\builds\next-run
```

Open <http://127.0.0.1:8787/>. MENU, arrows, OK and DISP are native guest inputs;
DISP also uses the D key. The browser Stop control stops the guest while retaining
the local server for inspection/restart. Pause retains the current frame.
The host controls retain the upstream Chinese text; Nikon's menus render English.

The `.eg.bin` outputs are complete EG modules, not repackaged Nikon update
containers. Emulator acceptance does not establish Z7 updater acceptance or a
recovery/rollback procedure. Validate real file/audio behavior and establish
those hardware-specific points before deciding whether to flash this camera.
