# Pixel shift step 3d: calibration run

Status: **prepared, not staged.** This is your everyday module (`8dcee0e0`) plus
a calibration run built on the geometry probe that ran on Nov 27 (`d6e6db28`).
The probe found how the Z7 reads the position command (x and y are signed
16-bit values) and the call that turns stabilisation back on. It also showed
that one-pixel steps are too small to measure reliably. This run uses larger
steps and repeats the reference. See [PIXEL_SHIFT_RESEARCH.md](PIXEL_SHIFT_RESEARCH.md).

## What it does

Arming, clicks and safety are exactly as before: half-press for about 3
seconds, let go, and don't touch. Then **nine photos**, one click each:

| Photo | Steps (x, y) | Expected image shift |
| --- | --- | --- |
| 1 | (0, 0) | reference |
| 2 | (+80, 0) | about 4 px sideways |
| 3 | (0, 0) | reference again (noise) |
| 4 | (−80, 0) | about 4 px the other way |
| 5 | (0, +72) | y: vertical? how far? |
| 6 | (0, 0) | reference again |
| 7 | (0, −72) | y the other way |
| 8 | (+40, +36) | diagonal (are x and y independent?) |
| 9 | (0, 0) | reference again |

Every target stays within ±320 counts (well inside the ±400 guard; the
sensor's travel is ±8180). Afterwards it recentres and turns stabilisation
back on with the call that worked last time (Nikon's apply flags). The two
other methods remain only as fallbacks.

| Card file | What it is |
| --- | --- |
| `Z7APP.BIN` | Everyday module + calibration run, SHA-256 `73567658…` |
| `Z7APP.LCD-EVERYDAY-8DCE.disabled` | Your current module, kept unchanged |
| `Z7VRMOV.DAT` | The log (rewritten on every power-on) |

## Steps (about 3 minutes)

1. Tripod. Use a subject with **fine detail in every direction** (text, a
   printed page, fabric, a brick wall, a bookshelf), evenly lit and filling
   the frame. Use these settings:
   - VR On
   - Silent photography On
   - Single frame
   - RAW + JPEG (or RAW)
   - low ISO
   - manual focus, sharp
2. Power on and wait about 5 seconds. Half-press for about 3 seconds, then
   **let go and don't touch**.
3. Count **nine clicks**. You may see the image jump a few pixels between
   shots; that is expected this time.
4. Wait a minute, then power off and bring the card back. Please keep all the
   photos.

**If anything seems wrong** (a noise, an error, a frozen screen, more than 9
clicks), power off at once, and take the battery out if needed.

## What I will look for

- **x:** steps per pixel, using both signs. The repeated references tell me
  how much the camera or tripod drifts.
- **y:** whether the image moves vertically, and steps per pixel.
- **diagonal:** whether x and y add up independently.

That gives the Z7's pixel-shift step values. Then the four-frame series can
use them.

## Verified before the camera

- Every earlier build still rebuilds byte for byte.
- The simulated stabiliser now uses the camera-measured layout. The probe
  audit reproduces the camera's outcome: variants 4, 6 and 7 skipped, 4
  photos.
- Calibration audit: nine payloads in order, each fired only while held at
  its target (within ±320), one click each, then centre and the working
  restore.
- The display suite (277), playback (22) and folder (22) checks pass.
- Emulator: boots and Nikon's menus work (26 checks).

Credit: design follows JKWTCN's MIT z7ii-extensions pixel shift; original-Z7
bindings are independent work.
