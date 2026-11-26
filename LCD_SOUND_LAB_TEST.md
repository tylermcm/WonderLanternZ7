# Shutter sound lab: find the speaker's ceiling by ear

Status: **experimental, prepared, not staged.** A temporary build of your LCD
module with shutter sound (`92602a4a`, which
[works on the camera](LCD_SHUTTER_SOUND_TEST.md)) whose **Shutter sound** row
offers extra settings for listening tests. It is not a release build; go back
to the normal module when you have your answer.

## What was found in Nikon's code

- Nikon's own sounds never set a volume when they start: the start path only
  programs a format, a "tone" value, the sample data and the DMA. Whatever sets
  the speaker level is configured elsewhere, so there is no proven hardware
  volume control to raise.
- The "tone" value is the one unknown knob. Nikon checks it is 0–37 for its own
  sounds. This module and upstream's Z7II module always send 31 and play their
  own samples, so what the value does for sample playback is unknown: it may
  change nothing, change loudness, or change the sound. The lab lets you hear it.
- Above level 7 the only other lever is more digital gain, which clips more of
  the click (level 7 already clips about 11%).

## Settings on the row

Press **OK** on **Shutter sound** to step through them in order; each plays a
preview. The row wraps from the last back to OFF.

| Row value | What it does |
| --- | --- |
| `OFF`, `1`–`7` | Same as the normal module (tone 31) |
| `8` | Digital gain ×2.83, more clipping (tone 31) |
| `9` | Digital gain ×4, heavy clipping (tone 31) |
| `5 T0`, `5 T16`, `5 T24`, `5 T28`, `5 T34`, `5 T37` | Level 5 (no clipping) with the driver tone value changed |

Compare each `5 T…` with plain `5`: louder, quieter, same, or a different
sound. Compare `8` and `9` with `7`: still getting louder, or only harsher?

Whatever you leave selected also plays on photos in Silent photography, and is
saved in `Z7SND.DAT` (lab format, which the normal module ignores).

## Card changes

| Card file | What happens |
| --- | --- |
| `Z7APP.BIN` | Sound-lab build, SHA-256 `aed2459c…` |
| `Z7APP.LCD-SHUTTER-SOUND.disabled` | Your current module, kept unchanged |
| `Z7SND-RELEASE.DAT` | Your saved level, kept aside and restored afterwards |

Display features are unchanged. To go back, ask me to restore: your module and
your saved level return as they were.

## What to report

- For `5 T0` … `5 T37`: any difference from `5`?
- Do `8` and `9` sound louder than `7`, or just more distorted?
- Which setting is the loudest that still sounds acceptable?

## Verified before the camera

- `5e62ce53` and `92602a4a` still rebuild byte for byte; every lab change is
  behind its own build switch.
- Offline: the 277-check display suite passes unchanged, plus 27 lab checks:
  all 16 settings in order with the right text, engine level and tone; the tone
  reaches both the copied record and Nikon's tone setter; photos use the chosen
  setting; levels 8 and 9 produce the exact clipped samples; the lab saves its
  own file version and ignores the normal module's file.
- Assisted QEMU, 25 checks on Nikon's real menus (no sound output there).

The tone values are kept inside the 0–37 range Nikon itself accepts. Short
clipped clicks at full scale are louder than the camera's own beeps; stop if
anything sounds strained.
