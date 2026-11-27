# Pixel shift series v2

Status: **prepared, not staged.** This is your everyday module (`8dcee0e0`)
plus the pixel-shift series, corrected with what the 20-photo dead-zone run
(`615cf144`) measured. See [PIXEL_SHIFT_RESEARCH.md](PIXEL_SHIFT_RESEARCH.md):

- vertical steps are linear at 18 per pixel; horizontal at 20;
- the camera body keeps settling for about 5 seconds after you let go of the
  button (about 1 pixel);
- upward moves fall about 0.3 px short, but the same target reached **from
  above** is exact.

## What changes from v1 (`f4e46989`)

- **7-second wait** after you let go, instead of 2. Touching the button then
  still cancels.
- **Every photo's position is approached from above.** The sensor first
  goes 2 pixels (36 steps) higher, then comes down to the target. This also
  covers the first photo's centre position.
- Unchanged: the 0.5 s settle with a position re-check before each release,
  one click per photo, and recentring and turning stabilisation back on at
  the end.

The four NEFs are a pixel-shift set at the corners (0,0), (1,0), (1,1) and
(0,1) px. After this run I will measure them on the raw data and, if they
land within a few tenths of a pixel, build the merge.

| Card file | What it is |
| --- | --- |
| `Z7APP.BIN` | Everyday module + pixel-shift series v2, SHA-256 `9814fb58…` |
| `Z7APP.LCD-EVERYDAY-8DCE.disabled` | Your current module, kept unchanged |
| `Z7VRMOV.DAT` | The log (rewritten on every power-on) |

## Steps (about 1 minute)

1. Same setup as before:
   - sturdy tripod
   - a still, well-lit, detailed subject
   - M mode with fixed settings
   - Silent photography On
   - Single frame
   - RAW
   - manual focus
2. Power on and wait about 5 seconds. Half-press for about 3 seconds, then
   **let go and step back**.
3. After about **7.5 seconds** you should hear **four clicks**.
4. Wait a minute, then power off and bring the card back. Please keep the
   four photos.

**If anything seems wrong** (a noise, an error, a frozen screen, more than 4
clicks), power off at once, and take the battery out if needed.

## Verified before the camera

- Every earlier build still rebuilds byte for byte.
- Offline, 11 checks:
  - each corner is approached from 36 steps above, then the target;
  - releases happen only at the targets, never at the approach positions;
  - the 7 s start settle, cancelled by a touch;
  - the 0.5 s settle with a re-check (a lost hold stops without a release);
  - one click per photo;
  - recentre and the apply restore;
  - no target beyond ±216 counts.
- The display suite (277), playback (22) and folder (22) checks pass.
- Emulator: boots and Nikon's menus work (26 checks).

Credit: design follows JKWTCN's MIT z7ii-extensions pixel shift; original-Z7
bindings and measurements are independent work.
