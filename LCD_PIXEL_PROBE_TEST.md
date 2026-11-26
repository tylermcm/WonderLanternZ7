# Pixel shift step 3c: geometry probe (find the Z7's vertical axis)

Status: **prepared, not staged.** This is your everyday module (`8dcee0e0`) plus a
probe built on the module-fired series that worked on Nov 27 (`3b2bb075`). That run
showed that x = 21 steps moves the image about 1.1 pixels, but upstream's "y"
moves the Z7's image only slightly sideways. It also showed that re-sending Nikon's
stabilisation parameters did not end the hold. See
[PIXEL_SHIFT_RESEARCH.md](PIXEL_SHIFT_RESEARCH.md).

## What it does

Arming, clicks and safety are exactly as in the last run: half-press for about
3 seconds, let go, and don't touch. Then it takes **one photo per position
command** (7 photos, one click each):

| Photo | Command (10 bytes) | What it tests |
| --- | --- | --- |
| 1 | `00 00 00 00 00 10 10 00 00 02` | reference (centre, held) |
| 2 | `00 13 …` | x = 19, the calibrated one pixel |
| 3 | `00 00 00 12 …` | y = 18 again (repeatability) |
| 4 | `00 00 00 00 12 …` | byte 4 (unknown field) |
| 5 | `00 00 00 12 00 18 08 …` | y with bytes 5/6 split (can the two "vertical" actuators differ?) |
| 6 | `00 00 FF EE …` | y = −18, if y is a signed 16-bit value |
| 7 | `FF ED …` | x = −19, if x is a signed 16-bit value |

Before each photo, the module reads the telemetry. It fires only if the
sensor is held, settled, and **every target is within ±400 counts** (about 5
pixels). Otherwise it recentres at once and skips that photo, so a variant
the stabiliser reads as a large value is never photographed and never held.

Afterwards it recentres the sensor and tries three ways to switch
stabilisation back on. It stops at the first one that works and logs which:

1. Nikon's parameter sender, with the flags Nikon's own "apply VR mode" uses
   (`sel[1]|0x80`). Last time flags 3 were sent, which didn't work.
2. Nikon's own BodyVr event that re-applies the VR mode, in Nikon's own task.
3. Nikon's apply routine itself.

| Card file | What it is |
| --- | --- |
| `Z7APP.BIN` | Everyday module + geometry probe, SHA-256 `d6e6db28…` |
| `Z7APP.LCD-EVERYDAY-8DCE.disabled` | Your current module, kept unchanged |
| `Z7VRMOV.DAT` | The log (rewritten on every power-on) |

## Steps (about 3 minutes)

1. **Same setup as last time:** tripod, still subject with fine detail. Use
   these settings:
   - VR On
   - Silent photography On
   - Single frame
   - RAW + JPEG (or RAW)
   - low ISO
   - manual focus
2. Power on and wait about 5 seconds. Half-press for about 3 seconds, then
   **let go and don't touch**.
3. Count the clicks: up to **7**. Fewer means a variant was skipped as out of
   range, which is fine and useful.
4. After the last click, wait **one minute**. If you like, pick the camera up
   and check whether live view is stabilised again; that tells me whether a
   restore worked. Then power off, don't power on again, and bring the card
   back. Please keep all the photos.

**If anything seems wrong** (a noise, an error, a frozen screen, more than 7
clicks), power off at once, and take the battery out if needed. The sensor
returns to normal at the next power-on.

## What I will look for

- for each photo, the targets the stabiliser accepted (which bytes drive which
  actuators) and the measured image shift. Together they give the command for
  one pixel **up/down** on the Z7;
- which restore method, if any, ends the hold.

## Verified before the camera

- Every earlier build (`8dcee0e0`, `5fe15dcc`, `b68284dc`, `3b2bb075`,
  `e33474d1`) still rebuilds byte for byte.
- Static firmware audit (54 checks), including:
  - Nikon's apply flags (`|0x80`, `|0xC0`);
  - the BodyVr event bit 4 and its handler;
  - Nikon's event-post call;
  - the BodyVr task record (mask `0x364FFFFF`, task `0xA23826D0`).
- Offline (simulated stabiliser, release, event post and apply):
  - seven frames in variant order, each only while that variant is held
    within ±400;
  - an out-of-range variant is skipped and recentred without a photo;
  - exactly the seven payloads, then the centre;
  - the three restore methods in order, stopping at the first that works;
  - a refusal stops the series;
  - a binding mismatch does nothing.
- The display suite (277), playback (22) and folder (22) checks pass.
- Emulator: boots and Nikon's menus work (26 checks).

Credit: design follows JKWTCN's MIT z7ii-extensions pixel shift; original-Z7
bindings are independent work.
