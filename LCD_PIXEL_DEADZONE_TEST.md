# Pixel shift step 3e: vertical dead-zone run

Status: **prepared, not staged.** This is your everyday module (`8dcee0e0`)
plus a 20-photo measurement run. The first real series (`f4e46989`) held
every position, but its raw data showed that an 18-step vertical move
(1 pixel) barely moved the image (about 0.06 px). The 36- and 72-step
vertical moves and all horizontal moves were proportional. This run
measures exactly how small vertical moves behave. See
[PIXEL_SHIFT_RESEARCH.md](PIXEL_SHIFT_RESEARCH.md).

## What it does

Arming, clicks and safety are as before. It waits 2 seconds after you let go
(touching the button then cancels), and 0.5 s before each photo. Then **20
photos**, one click each:

| Photos | Steps (x, y) | Purpose |
| --- | --- | --- |
| 1 | (0, 0) | discarded: the first photo catches the camera moving |
| 2-8 | ref, (0,+18), ref, (0,+36), ref, (0,+54), ref | upward moves of 1, 2, 3 px, each between references |
| 9-12 | (0,−18), ref, (0,−36), ref | downward moves of 1, 2 px |
| 13-14 | (20, 0), ref | x control (1 px, known to work) |
| 15-16 | (0,+54) then (0,+18) | +1 px reached **from above** |
| 17-20 | ref, (0,−54), (0,−18), ref | −1 px reached **from below** |

Every target stays within ±216 counts. Afterwards it recentres and turns
stabilisation back on (the method that worked on the last three runs).

| Card file | What it is |
| --- | --- |
| `Z7APP.BIN` | Everyday module + dead-zone run, SHA-256 `615cf144…` |
| `Z7APP.LCD-EVERYDAY-8DCE.disabled` | Your current module, kept unchanged |
| `Z7VRMOV.DAT` | The log (rewritten on every power-on) |

## Steps (about 2 minutes)

1. **Set up** as before: sturdy tripod, still subject, M mode with fixed
   settings, Silent photography On, Single frame, RAW, manual focus.
   - **More texture and more light help most**: printed text, fabric or a
     bookshelf filling the frame, as bright as you can make it, so a fast
     shutter speed works.
2. Power on and wait about 5 seconds. Half-press for about 3 seconds, then
   **let go and step back**.
3. After about 2.5 seconds you should hear **20 clicks**, roughly one a
   second.
4. Wait a minute, then power off and bring the card back. Please keep all
   the photos. They are only for measurement, and you can delete them
   afterwards.

**If anything seems wrong** (a noise, an error, a frozen screen, more than 20
clicks), power off at once, and take the battery out if needed.

## What I will look for

On the raw colour planes, each move against the references either side of
it:
- whether the vertical image shift is proportional to the step (0.055 px
  per step), and if not, how many steps are lost (a dead zone);
- whether the loss depends on direction (up/down, or approached from above
  or below).

That decides the fix. Examples: a fixed offset added to y, always approaching
from one side, or using 3-pixel steps that land on the same colour-filter
phase.

## Verified before the camera

- Every earlier build still rebuilds byte for byte.
- Offline, 10 checks:
  - the 20 payloads in order, each released only while held at target
    (within ±216);
  - the 2 s start settle, cancelled by a touch;
  - the 0.5 s settle before every photo;
  - one click each;
  - recentre and the apply restore.
- The display suite (277), playback (22) and folder (22) checks pass.
- Emulator: boots and Nikon's menus work (26 checks).

Credit: design follows JKWTCN's MIT z7ii-extensions pixel shift; original-Z7
bindings and measurements are independent work.
