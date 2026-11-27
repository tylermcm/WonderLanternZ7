# Pixel shift: first real four-frame series on the Z7

Status: **prepared, not staged.** This is your everyday module (`8dcee0e0`)
plus the first pixel-shift series that uses everything measured on your
camera so far. See [PIXEL_SHIFT_RESEARCH.md](PIXEL_SHIFT_RESEARCH.md):

- the module fires the shutter itself (Nikon's capture call, with the "done"
  signal `0x04100038`);
- the Z7 step scale from the calibration run: **20 steps per pixel in x, 18
  in y**, with independent axes;
- the call that turns stabilisation back on (Nikon's apply flags), which
  worked on the last two runs;
- a settle delay, because the calibration's first photo caught the camera
  still moving after the button was released.

## What it does

1. **Arms** while you half-press (stabilisation active and steady).
2. Waits until the button has been untouched for half a second, then **2
   more seconds** for the camera to settle. Touching the button then cancels
   the series without a photo.
3. **Four photos**, each moved one pixel to the next corner of the colour
   filter pattern: (0,0), (20,0), (20,18) and (0,18) steps. For each, it
   moves the sensor, confirms it from telemetry, waits **0.5 s**, confirms
   again, releases, and waits for Nikon's "done" signal and the file. It
   clicks once per photo.
4. Recentres the sensor and turns stabilisation back on.

The four NEFs are a normal pixel-shift set: each colour-filter site is
sampled with R, G and B across the four. They are **not merged in the
camera** and **not tagged** for NX Studio's merge. I will merge them on the
computer and compare the result with a single frame.

| Card file | What it is |
| --- | --- |
| `Z7APP.BIN` | Everyday module + pixel-shift series, SHA-256 `f4e46989…` |
| `Z7APP.LCD-EVERYDAY-8DCE.disabled` | Your current module, kept unchanged |
| `Z7VRMOV.DAT` | The log (rewritten on every power-on) |

## Steps (about 2 minutes)

1. **Set up:** a sturdy tripod, and a still subject with fine detail and
   some colour (fabric, a printed page with colour, a plant indoors) that
   fills the frame. Use these settings:
   - VR On
   - Silent photography On
   - Single frame
   - **RAW (NEF)**, lossless compressed is fine
   - lowest base ISO
   - an aperture around f/5.6-f/8
   - manual focus, sharp
   - no wind or moving light
2. Power on and wait about 5 seconds. Half-press for about 3 seconds, then
   **let go and step back**.
3. After about 2.5 seconds you should hear **four clicks**, roughly a second
   or two apart.
4. Wait a minute, then power off and bring the card back. Please keep all
   four photos.

**If anything seems wrong** (a noise, an error, a frozen screen, more than 4
clicks), power off at once, and take the battery out if needed.

## Verified before the camera

- Every earlier build still rebuilds byte for byte.
- Offline (simulated stabiliser with the camera-measured layout, release and
  restore), 10 checks:
  - four photos at the calibrated corners, each released only while held;
  - the 2 s and 0.5 s settles, with the position re-checked before each
    release (a lost hold stops the series without a release);
  - touching the button during the settle cancels it;
  - one click per photo;
  - recentre, then the restore with the apply flags.
- The display suite (277), playback (22) and folder (22) checks pass.
- Emulator: boots and Nikon's menus work (26 checks).

Credit: design follows JKWTCN's MIT z7ii-extensions pixel shift; original-Z7
bindings and the Z7 calibration are independent work.
