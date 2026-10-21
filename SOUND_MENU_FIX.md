# Z7 C 3.80 sound-menu correction, October 20, 2026

The combined full image in `.private/builds/20261020-09/` opens the Shutter sound
menu, renders all four actions and returns to processed live view. The primary
demo at <http://127.0.0.1:8787/> runs this exact image and was left on the submenu.
No physical camera or card was accessed. WAV playback and flashing are untested.

## Evidence and scope

| Check | Final full image |
| --- | --- |
| Upstream tests using the private Nikon container | 16 pass, none skipped |
| Repeated build and module CRC | All four presets pass |
| Display instruction gates | 1,024 cases pass per applicable preset |
| Config calling convention | 3 cases pass |
| Stock route fallback comparison | 6 cases pass |
| Stock data fallback comparison | 4 cases pass |
| Menu metadata, callback and layout contracts | 20 checks pass per sound preset |
| Candidate admission/corruption checks | 13 pass |
| General UI, including three MENU roundtrips | 21 checks pass |
| Custom sound menu and recovery to live view | 17 checks pass across 30 native button events |

The sound-only preset independently passes the same 17 menu/recovery checks.

The menu probe verifies actual active-page IDs, allocation addresses, parent
objects, state magic, selected rows, enabled/busy/length/result values and
rendered title pixels. It tests OFF, ON with no file, failed file selection,
Preview/Reload with no file, returning to Setup, reopening with retained
selection, and return to the reference processed scene with continued ISP work.
Screenshots were visually inspected for the title, all four root actions and
file/error screens. The primary HTTP demo was independently navigated into the
submenu using its normal native-key action API.

## Causes corrected

- The config trampoline broke stack alignment and discarded the native parser's
  return value. These were fixed before the focused menu investigation.
- Route fallback resumed at `0x1048B402`, within a replaced 12-byte jump span,
  and failed to reconstruct `MOVW R9,#0x3A0`. Resume now follows the full span.
- Data fallback loaded the final R5 value before resuming a native `ADDS #16`,
  doubling the offset. Its literal now matches the displaced stock LDR.
- Callback `0x10405261` skipped `PUSH {r4,lr}` at `0x1040525E`. Its eventual POP
  consumed its caller's stack and entered RAM as ARM instructions. Offline native
  execution reproduces this corruption; pointer `0x1040525F` preserves the caller.
- Setup was identified as page `0x18D` rather than `0x19B`. The correct object is
  `0xA1837BEC`, whose initialized metadata maps to `0x11F10854`. Dynamic-label
  slot 39 and initialization now correspond to the visible Setup row.
- Copying 96 bytes from the old leaf yielded record types `[1,4,4]`, without a
  terminator. Native traversal advances 32 bytes until type zero and could read
  the following rectangle allocation. Validated page `0x2A` provides `[1,4,0]`.
- Setup as a full-page menu parent triggered its native redraw after the switch
  released its widgets. The sound, file and toggle pages now use native menu
  shell `0xA1833574`, matching stock full-page Setup submenus. History provides
  back navigation.
- The borrowed leaf's viewport allowed only two rows. Each private page now sets
  both total and visible row counts, and explicitly shows its dynamic title.

Build 06 captured Data abort at RAM `0xA1837BF8`; its saved R9=0 explains the
resulting address `0xA4` access. Build 07, after correcting that return, captured
the parent-redraw null-widget access at `0x104BCB9A`. Copied `Prefetch abort` text
on an older reporter stack was not evidence of the exception type.

## Preserved results

- Full MAIN: 33,064,940 bytes, SHA-256
  `1d456c84709650e90cc6decd0877a9a51d4692bacc5477fa21ea28fba67cfb76`.
- Sound-only MAIN: 33,064,840 bytes, SHA-256
  `0fe02a264926fe215484fd233b994d26fbdf9e6e4b2358df30027b8d82a93c0d`.
- `.private/builds/20261020-09/summary.json`: source hashes and offline evidence.
- `.private/evidence/sound-menu-events-09/result.json`: full submenu result.
- `.private/evidence/sound-only-menu-events-09b/result.json`: sound-only result,
  including the bounded asynchronous recovery wait.
- `.private/evidence/full-fixed-ui-09/result.json`: general UI result.
- `.private/evidence/original-sound-menu-layout.json`: older callbacks/layouts
  fail the independent native contract checks.
- `.private/evidence/original-sound-page-parent.json`: build 07 fails all three
  native parent relationships.
- `.private/evidence/primary-sound-demo-09.{png,json}`: live primary demo evidence.
- `.private/patches/20261020-09-*.diff`: source changes; original patches and
  all intermediate binaries remain preserved.

The early `sound-native-probe-05`/`05b` attempts used direct page injection before
queued input dispatched. They are harness failures and are excluded from firmware
conclusions. Build 08's final reopen assertion incorrectly expected the selection
to reset; actual native selection retention is now checked. The initial sound-only
09 probe allowed only one second for each return frame. The subsequent `09b`
run passes with the normal bounded recovery wait and unchanged candidate bytes.

## Reproduce

`Run-Z7.ps1` and `tools/launch_z7.py` default to full build 09. Stop an existing
server before starting another instance on port 8787. `-Preset liveview-dual`
selects the earlier display-only behavior using the identical display payload.

For the existing Linux environment, set the workspace path as the working
directory and run with `/home/dixie/nikon-z7-lab/.venv/bin/python` in WSL distro
`Ubuntu`:

```sh
python tools/build_firmware.py --output .private/builds/new-unique-run
python tools/check_candidate_inputs.py --build .private/builds/new-unique-run
python tools/probe_sound_menu.py --build .private/builds/new-unique-run \
  --output .private/evidence/new-unique-menu-run --exercise
```

Each output directory must be new. Original containers remain untouched. MAIN
payloads are QEMU inputs; EG modules are not Nikon update containers. Emulator
startup assistance and synthetic image input remain in use. Real card I/O, speaker
output, shutter timing, power-loss recovery, signed update acceptance, and rollback
have not been established by these results.
