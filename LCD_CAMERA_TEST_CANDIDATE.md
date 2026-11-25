# Consolidated LCD camera-test candidate — November 24, 2026

One SD-module packet that gathers every offline LCD checkpoint that runs on the
**installed host**, so a single camera session can check them together instead of
staging four separate trials. It is the same packet already described in the
[Information page review](LCD_INFORMATION_PAGE_REVIEW.md); this document adds the
current-source rebuild, the re-run gate set and the combined test plan.

## Exact candidate

- `Z7APP.BIN`: 26,040 bytes, SHA256
  `cec4c39bdda98fb5269bb87cb6cd15961bc78e6eca464b6a39f78477cf3f62c5`.
- Build: `tools/build_z7_lcd_volatile.py --information-page` at the commit that
  adds this document. The rebuild from current sources is byte-identical to the
  packet frozen earlier on November 24, so later highlight and movie-orientation
  commits did not change it.
- Original Z7 C 3.80, photo and movie mode, rear LCD. Needs the API44 host already
  installed on the camera (main payload `24b2074559ca6089…`). **No firmware update.**
- Not camera-tested. Not staged. Staging needs explicit owner approval.

## What it contains

| Feature | Source review | State before this test |
| --- | --- | --- |
| Display settings name-label repair (`5e62` fix) | [LCD_SETTINGS_LABEL_REVIEW.md](LCD_SETTINGS_LABEL_REVIEW.md) | Staged as `5e62`; owner reported only the deferred startup grid flash, not the label result |
| Histogram switch in each of the four LCD presets | [LCD_HISTOGRAM_PRESETS_REVIEW.md](LCD_HISTOGRAM_PRESETS_REVIEW.md) | Offline only |
| Battery percentage on the movie-mode LCD (global switch) | [LCD_MOVIE_BATTERY_REVIEW.md](LCD_MOVIE_BATTERY_REVIEW.md) | Offline only |
| Native Information display as an optional fifth DISP page | [LCD_INFORMATION_PAGE_REVIEW.md](LCD_INFORMATION_PAGE_REVIEW.md) | Offline only |

New switches default OFF, and an older module still loads the same `Z7DSP` journals.

**Excluded:** photo highlight stripes and movie orientation. Both need the
experimental API72 host, which would mean a firmware update, and movie orientation
is not cleared for camera use. The brief 3x3 grid flash at cold start stays
deferred at the owner's request.

## Offline gates re-run on the current-source rebuild

| Gate | Checks | Result |
| --- | ---: | --- |
| Live histogram renderer (busy, transition, cleanup guards) | 170 | Pass |
| Histogram preset menu/storage, five saves and reloads | 96 | Pass |
| Movie LCD battery admission, exclusions and transitions | 47 | Pass |
| Information page native DISP routing | 54 | Pass |
| Information page storage, cold loads and rollback to `cc9d6b39…` | 57 | Pass |
| Display settings root/label compiled contracts | 76 | Pass |
| QEMU: name label restored after injected label/cache loss | 8 | Pass |
| QEMU: seven-row root menu, Information and Battery switches | 12 | Pass |
| QEMU: Histogram + Virtual horizon preset controls, settled pixels | 13 | Pass (4 runs) |
| Root unit tests | 103 | Pass |

This is the first run of the movie-battery audit on this combined packet. Its
fixture had hard-coded the Battery percentage row as root row 5, which is
Information display in this profile. The audit now selects row 6 for the
Information profile and still passes 47 checks on the earlier movie-battery
profile. The module itself was not changed.

The histogram menu probe now also checks pixels. Across four runs, the frame
captured immediately after the second back-to-back toggle, while the title reads
"Saving", showed one value cell (Framing grid) blank in three runs. The recapture
about five seconds later showed every value in all four runs. This is a brief
repaint gap during the save, not a stuck value; the stored settings were correct
throughout.

Assisted QEMU and instruction-level fixtures supply firmware services, file
contents and rendering boundaries. None of this proves live histogram pixels,
Information display text orientation, the movie HUD layout, recording, sleep/wake
or recovery from this packet.

The probe tooling's host-equivalence check rejected the older stored host
reports because newer builder versions record two extra opt-in flags, both false.
The host binary itself is unchanged: a fresh default display-host rebuild is
byte-identical to the installed main payload `24b2074559ca6089…`, and the QEMU
probes ran against that rebuild.

## Combined camera test (one session)

Camera OFF, insert the card, power on normally. **Do not select Firmware update.**
Stop at the first freeze or wrong behavior; don't repeat the step.

1. **Cold-start label.** After at least 20 seconds powered off, open MENU → Custom
   Settings. The **h Display settings** row should show its full name *before*
   you open it. (A brief 3x3 grid flash at startup is the known, deferred issue.)
2. **Root menu.** Open Display settings. Seven rows: Custom pages, Standard,
   Minimal, Composition, Exposure, Information display, Battery percentage.
3. **Histogram preset.** In Composition (or any page), turn Histogram ON. A value
   on that screen may blank for a moment while the title reads "Saving"; note it
   only if it stays blank after "Saved". Back out
   to photo live view and DISP to that page: histogram, horizon and grid together;
   the histogram moves when you point at brighter and darker scenes; dials,
   shutter and DISP respond normally.
4. **Information page.** Turn Information display ON. Cycle DISP into Nikon's full
   information screen and back out. Check the text reads normally, not mirrored,
   and MENU returns cleanly.
5. **Movie battery.** Turn Battery percentage ON. Switch to movie mode: the
   percentage appears inside the battery icon on the rear LCD. Optionally record
   about 10 seconds and stop; the camera stays responsive.
6. **Persistence and power.** Power off normally (wait for the card lamp), wait 20
   seconds, power on. The histogram, Information display and battery choices are
   still set, and the label is still complete.

Report pass/fail per step. Photos of steps 3–5 are welcome but optional.

## Installation and recovery

`.private/stage-lcd-camera-candidate-test-01.py` (private) performs the swap only
after recording the owner's approval. It re-identifies the card, requires the
current module to be `5e62…`, backs up every root file, renames `5e62` to
`Z7APP.LCD-SETTINGS-LABEL.disabled`, writes the exact packet, verifies a full
readback and leaves the settings journals, photos and the camera-tested baseline
`Z7APP.LCD-GRID-PERSISTENCE-WORKING.disabled` (`f848e62d…`) untouched.

On a freeze, remove the battery. Earlier failures recovered that way, but
recovery from this exact packet is not physically verified. Bring the card back:
the working `f848` module (or `5e62`) can be restored by an SD file swap with no
firmware update. Emergency firmware recovery remains unverified.
