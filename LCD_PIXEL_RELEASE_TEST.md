# Pixel shift step 3b: the module fires the four shots itself

Status: **second build `3b2bb075`, prepared, not staged.** The first build
(`c813c457`) fired one frame on the camera, at power-on; see "First run"
below. This is your everyday module (`8dcee0e0`) plus the first pixel-shift series in which **the module presses the shutter
itself**. The step-3a run
([LCD_PIXEL_SERIES_TEST.md](LCD_PIXEL_SERIES_TEST.md)) showed why this is
needed: every half-press makes the camera switch normal stabilisation back
on, so photos you take yourself are never shifted. Upstream's Z7II design
works the same way. See [PIXEL_SHIFT_RESEARCH.md](PIXEL_SHIFT_RESEARCH.md).

## What it does

1. **Arms only while you half-press**, once stabilisation is active and
   steady. It notes Nikon's stabilisation parameters; with VR off it never
   does anything.
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
     next frame;
   - **clicks once** so you can count the frames. If your shutter sound is on,
     its own click is the count. With it OFF, the module plays the click at
     level 5.
4. **Stops early** if Nikon refuses a release, a frame fails or takes over
   15 s, another client is waiting on the release, or you touch the shutter
   button.
5. **Finishes** by recentring the sensor and re-sending Nikon's latest
   stabilisation parameters (`0x101C63F8`; the release replaces them), then
   watching for 30 s.

Once per power-on. Everything goes to `A:\Z7VRMOV.DAT`: each release result
and Nikon's completion events, and each photo's ID.

The four photos are **not merged or tagged** for NX Studio yet. I will measure
them on the computer.

| Card file | What it is |
| --- | --- |
| `Z7APP.BIN` | Everyday module + module-fired series, SHA-256 `3b2bb075…` |
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
2. Power on and wait about 5 seconds. **Half-press** the shutter and hold it
   for about 3 seconds, then **let go completely and don't touch the camera**.
   Within a second or two you should hear **four clicks**, one per photo,
   about 1–3 seconds apart.
   - If there are no clicks, half-press again for 3 seconds and let go.
3. Leave the camera on for **one more minute**. Then power off. **Do not power
   on again** before the card comes back (each power-on runs it again).

**If anything seems wrong** (a noise from the camera, an error message, a frozen
screen, more than four photos), power off at once. If it does not turn off,
take the battery out. The sensor returns to normal at the next power-on.

## First run (`c813c457`, Nov 27)

It armed right after power-on, because stabilisation is already active then.
It held position 0 and fired: Nikon accepted (code 0) and a still record
followed. Nikon's "done" signal was `0x04100038`, which that build did not
wait for, so it stopped after 15 s. The release had replaced Nikon's
stabilisation parameters, so the build did not restore them, and the hold
stayed on until power-off. All three are fixed: arming needs a half-press,
`0x04100038` completes a frame, and the latest parameters are re-sent. The
click is new.

## What I will look for

- whether Nikon accepted each release (code 0) and its completion events;
- whether the hold survived each exposure (telemetry right before and after);
- whether stabilisation came back after the module restored it;
- in the four photos, whether the image moved by about one pixel each time.
  That is the first real calibration of the step scale on the Z7.

## Verified before the camera

- `8dcee0e0`, `5fe15dcc`, `b68284dc` and `e33474d1` all still rebuild byte for byte.
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
- Offline against a simulated stabiliser and release (27 checks):
  - exactly four fires, each only while the commanded corner is held, with
    the exact request and the module's callback;
  - never with the button touched, and never armed without a half-press;
  - `0x04100038` and `0x04100034` both complete a frame;
  - one click per frame: no extra click when the shutter sound already
    clicked, and still a click with the sound OFF;
  - Nikon's latest stabilisation parameters are re-sent after the release
    changed them;
  - stops on a held button, a touched button, a refusal, a failed or missing
    completion, or a busy slot, and always recentres and restores;
  - nothing on a binding mismatch;
  - the callback itself, run for real.
- The display suite (277), playback (22) and folder (22) checks pass.
- Emulator: the module boots and Nikon's menus work (26 checks). The emulator
  cannot take photos.

Credit: design follows JKWTCN's MIT z7ii-extensions pixel shift; original-Z7
bindings are independent work.
