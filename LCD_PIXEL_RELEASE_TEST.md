# Pixel shift step 3b: the module fires the four shots itself

Status: **prepared, not staged.** This is your everyday module (`8dcee0e0`)
plus the first pixel-shift series in which **the module presses the shutter
itself**. The step-3a run
([LCD_PIXEL_SERIES_TEST.md](LCD_PIXEL_SERIES_TEST.md)) showed why this is
needed: every half-press makes the camera switch normal stabilisation back
on, so photos you take yourself are never shifted. Upstream's Z7II design
works the same way. See [PIXEL_SHIFT_RESEARCH.md](PIXEL_SHIFT_RESEARCH.md).

## What it does

1. **Arms** as before: you half-press for a few seconds until stabilisation is
   active and steady. It notes Nikon's stabilisation parameters; with VR off
   it never does anything.
2. **Waits for you to let go.** It starts only once the shutter button (half
   or full, either grip) has been untouched for half a second. If you hold it
   for 10 seconds, it gives up without moving anything.
3. **Four frames.** For each corner, (0,0), (21,0), (21,18) and (0,18) steps
   (upstream's one-pixel values), it:
   - holds the sensor there;
   - confirms the position from telemetry;
   - fires the shutter through **Nikon's own release call** (`0x101ECFB0`,
     the same one PTP remote shooting uses), with no autofocus;
   - waits for Nikon's "capture done" signal and the new file before the
     next frame.
4. **Stops early** if Nikon refuses a release, a frame fails or takes over
   15 s, another client is waiting on the release, or you touch the shutter
   button.
5. **Finishes** by recentring the sensor and putting Nikon's stabilisation
   parameters back (`0x101C63F8`), then watching for 30 s.

Once per power-on. Everything goes to `A:\Z7VRMOV.DAT`: each release result
and Nikon's completion events, and each photo's ID.

The four photos are **not merged or tagged** for NX Studio yet. I will measure
them on the computer.

| Card file | What it is |
| --- | --- |
| `Z7APP.BIN` | Everyday module + module-fired series, SHA-256 `c813c457…` |
| `Z7APP.LCD-EVERYDAY-8DCE.disabled` | Your current module, kept unchanged |
| `Z7VRMOV.DAT` | The log (rewritten on every power-on) |

## Steps (about 3 minutes)

1. Tripod, and a still subject with fine detail. Photo mode with these
   settings:
   - **VR On** (Normal)
   - **Silent photography On**
   - release mode **Single frame**
   - image quality **RAW + JPEG** (or RAW)
   - low ISO
   - focus set and then **manual focus**, so nothing refocuses
2. Power on. **Half-press** the shutter for about 3 seconds, then **let go
   completely and don't touch the camera**. Within a second or two the camera
   should take **four photos by itself**, about 1–3 seconds apart.
   - If nothing happens, half-press again for 3 seconds and let go. It
     arms on the first steady half-press.
3. Leave the camera on for **one more minute**. Then power off. **Do not power
   on again** before the card comes back (each power-on runs it again).

**If anything seems wrong** (a noise from the camera, an error message, a frozen
screen, more than four photos), power off at once. If it does not turn off,
take the battery out. The sensor returns to normal at the next power-on.

## What I will look for

- whether Nikon accepted each release (code 0) and its completion events;
- whether the hold survived each exposure (telemetry right before and after);
- whether stabilisation came back after the module restored it;
- in the four photos, whether the image moved by about one pixel each time.
  That is the first real calibration of the step scale on the Z7.

## Verified before the camera

- `8dcee0e0`, `5fe15dcc` and `b68284dc` all still rebuild byte for byte.
- Static firmware audit, 48 checks. For the release call they cover:
  - the callback is kept and registered in completion slot `0x38`;
  - the property `0x11B` gate;
  - how each request field is read;
  - the three Nikon callers (PTP and remote);
  - the PTP request builder;
  - the slot table `0xA238BA48`;
  - the "capture done" event `0x04100034`;
  - the shutter switch bits `0x80000000` (half) and `0x40000000` (full) from
    Nikon's switch-name table.
- Offline against a simulated stabiliser and release (20 checks):
  - exactly four fires, each only while the commanded corner is held, with
    the exact request and the module's callback;
  - never with the button touched;
  - stops on a held button, a touched button, a refusal, a failed or missing
    completion, or a busy slot, and always recentres and restores;
  - nothing on a binding mismatch;
  - the callback itself, run for real.
- The display suite (277), playback (22) and folder (22) checks pass.
- Emulator: the module boots and Nikon's menus work (26 checks). The emulator
  cannot take photos.

Credit: design follows JKWTCN's MIT z7ii-extensions pixel shift; original-Z7
bindings are independent work.
