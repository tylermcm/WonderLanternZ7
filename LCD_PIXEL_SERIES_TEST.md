# Pixel shift step 3a: four-photo series dry run (with stabilisation restore)

Status: **prepared, not staged.** This is your everyday module (`8dcee0e0`:
display features, shutter-sound page, upside-down EXIF fix and playback) plus
the first pixel-shift **series**. It also includes step 2b: putting
stabilisation back to normal afterwards, without a power cycle. See the
[pixel-shift plan](PIXEL_SHIFT_RESEARCH.md). Step 2
([LCD_VR_MOVE_TEST.md](LCD_VR_MOVE_TEST.md)) moved the sensor and recentred it
on this camera.

## What it does

- **Arms** exactly like step 2: it waits until stabilisation is active and
  steady (two reads 100 ms apart). It also notes the stabilisation parameters
  Nikon last sent (the "D2" command). If there are none, for example with VR
  off, it never moves anything.
- **Holds** the sensor at position 0.
- **You take four photos.** After each **new** photo it moves the sensor one
  step to the next Bayer corner: (0,0), then (21,0), (21,18) and (0,18) steps.
  Those are upstream's Z7II values for one pixel. It checks that the sensor
  got there.
- **Watches** once a second while it waits. If the hold is lost, for example
  because a half-press made the camera switch normal stabilisation back on, it
  logs it and re-sends the position (at most 6 times).
- **Finishes** after the fourth photo, or after 2 minutes without a new one. It
  recentres the sensor and re-sends Nikon's own stabilisation parameters with
  Nikon's own call (`0x101C63F8`, the Z7 equivalent of upstream's restore).
  Stabilisation should then be normal again without a power cycle. Then it
  watches for 30 seconds.
- Once per power-on. **It never presses the shutter**; you do. It logs
  everything, including each photo's ID, to `A:\Z7VRMOV.DAT`.

The four photos are **not merged in the camera** and are **not tagged** for
NX Studio's pixel-shift merge. This run only checks that the sensor steps
between your photos and comes back. I will check the photos and the log on
the computer.

| Card file | What it is |
| --- | --- |
| `Z7APP.BIN` | Everyday module + series dry run, SHA-256 `b68284dc…` |
| `Z7APP.LCD-EVERYDAY-8DCE.disabled` | Your current module, kept unchanged |
| `Z7VRMOV.DAT` | The log (rewritten on every power-on) |

## Steps (about 5 minutes)

1. Camera on a **tripod**, aimed at something still with fine detail (text,
   fabric, a plant indoors). Photo mode, **VR On** (Normal), **Silent
   photography On**, image quality **RAW** (NEF; uncompressed if you are happy
   to use it), low ISO, focus set and then left alone (MF or AF-ON).
2. Power on. **Half-press** the shutter and hold it for about 3 seconds, three
   times. That arms the module. Nothing visible happens.
3. Take **four photos**, waiting about **5 seconds** between them. A remote or
   the 2-second self-timer avoids touching the camera. The sensor moves by
   about a pixel after each photo, so you probably won't see it.
4. Leave the camera on for **one more minute**. In that time stabilisation
   should come back by itself. If you like, check it: pick the camera up and
   see whether live view is steady again.
5. Power off. **Do not power on again** before the card comes back (each
   power-on runs it again and rewrites the log). Bring the card back and I will
   restore your everyday module and look at the log and the four photos.

**If anything seems wrong** (a noise from the camera, an error message, a frozen
screen), power off at once. If it does not turn off, take the battery out.
Either way the sensor returns to normal at the next power-on.

## What I will look for

- whether each move followed the photo it should, and whether the hold lasted
  until your next photo (or a half-press or the release broke it);
- whether Nikon's stabilisation parameters, re-sent at the end, brought the
  state back from hold (`0x40`) to normal;
- in the four photos, whether the image moved by about one pixel each time.
  That is the first real check of the 21/18 step scale on the Z7.

## Verified before the camera

- `8dcee0e0` (installed), `5fe15dcc` (step 2, run on the camera) and the
  step-2b build `2ff19bde` all still rebuild byte for byte; the series is
  behind its own switch.
- Static firmware audit: 31 checks, including Nikon's D2 sender `0x101C63F8`
  (selection bytes 0-1 and flags at +8, device command 4, only in BodyVr
  state 1, used by Nikon's own VR-mode apply) and its buffer `0xA235BA44`,
  separate from the position buffer.
- Offline against a simulated VR unit:
  - step-2b restore: 19 checks. It re-sends exactly the snapshot, with the
    service idle and in state 1. It never moves without a snapshot, does not
    re-send if Nikon already did, and refusals are bounded.
  - series: 20 checks. Photos come through the real still-file hook. The four
    corners come in order, only after new photos; photos before arming and
    repeated records are ignored. A lost hold is re-sent (bounded), a missing
    photo times out, and it always recentres and restores once. The four photo
    IDs are logged.
- The display suite (277), playback (22) and folder (22) checks pass.
- Emulator: the module boots and Nikon's menus work (26 checks).

Credit: design follows JKWTCN's MIT z7ii-extensions pixel shift; original-Z7
bindings are independent work.
