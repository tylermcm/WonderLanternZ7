# Pixel shift on the original Nikon Z7 is hardware verified

**November 28, 2026. Source update; no firmware or module binary is
distributed.** Read the [risk notice](RISK_NOTICE.md) before trying anything.

Pixel shift on the original Z7 is now a menu feature in Nikon's own Photo
shooting menu, and it has been verified on the camera. The
[first release note](RELEASE_NOTES_2026-11-27_PIXEL_SHIFT.md) covered a
one-off test build that ran once per power-on. This update is a full feature,
tested on the camera over eight test sessions.

\* *Hardware verified on the project owner's original Z7 (C 3.80, without
the paid RAW-video upgrade), on a tripod. It is still experimental,
source-only research firmware. See [Limits](#limits).*

## Verified on the camera

**MENU → Photo shooting → Pixel shift shooting:**

| Feature | Camera result |
| --- | --- |
| One full press of the shutter starts a group | Works; no freeze, Menu and Play stay usable |
| 4 shots | Frames shifted (-1, 0), (-1, +1) and (0, +1) px, measured on the raw colour planes |
| 8 shots | Works; the 4-position pattern twice, for averaging |
| 16 shots | Works; all 16 planned positions in order, the four corners at four half-pixel offsets |
| AE bracketing | Works; 3F at 1.0 EV gave three groups of four at 1/3 s, 1/6 s and 0.625 s (Nikon's order 0, -1, +1 EV), one exposure per group |
| New folder per group | Works; each group starts a new DCIM folder |
| Cancel with OK | Works; stops after the current frame, then recentres and restores |
| Temporary setup | NEF only, single frame, Silent photography, AF-S/single-point. Exposure is held for the group, and your settings come back afterwards |
| Stabilisation | Sensor recentred and Nikon's normal stabilisation restored after every group |

The four 4-shot frames merge with
[`tools/merge_z7_pixel_shift.py`](tools/merge_z7_pixel_shift.py). Fine
printed halftone resolves with less colour speckle than a single frame.

## How to use it

1. Tripod, a still subject, steady light, manual focus, FX image area, and
   the **mode dial on M**.
2. MENU → Photo shooting → **Pixel shift shooting** → mode On (single photo
   or series), then pick the number of shots, delay, interval and options.
3. Leave the menu and **fully press the shutter once**, then step back. After
   about 7 seconds of settling, the camera takes the group.
4. Press **OK** to cancel.

## What the camera tests fixed

Getting from the test build to a menu feature took eight camera sessions.
Each problem was fixed in source, reproduced in the simulator so it can't
come back unnoticed, and confirmed on the camera:

- **Mode dial.** The Z7's exposure mode follows the physical dial and can't
  be changed by the module, so pixel shift now requires M and says
  **Use M** otherwise.
- **Full-press freeze.** Two of Nikon's shutter-button callbacks were
  swapped, which left Nikon thinking the button was still half-pressed. They
  are now taken from Nikon's own registration code.
- **One frame, then stop.** After each shot, Nikon hands stabilisation back
  to its normal mode, and tripod vibration moves the sensor reading by up to
  about 19 units. The module now re-sends each position, uses the camera-proven
  hold tolerance and retries its last check.
- **OK didn't cancel.** The module now reads the OK button's live switch
  state while a group runs.
- **Menu ignored changes after a group.** The post-group watch now ends as
  soon as stabilisation is back to normal, in about a second.

## Limits

- **One camera.** Verified only on the owner's original Z7 at C 3.80. Other
  bodies, firmware versions and the Z7 II are not supported by these modules.
- **The menu row label is blank** on the camera. The row works, but its
  name doesn't show yet.
- **32 shots** uses the same code as 16 but hasn't been run on the camera.
- **Merge on the computer only.** There is no in-camera merge, and NX Studio
  doesn't recognise the files as a pixel-shift set.
- **Pixel-shift conditions apply**: anything that moves between frames
  spoils the merge, as on every pixel-shift camera.
- If the battery dies mid-group, the automatic restore can't run, so check
  image quality, release mode, Silent photography and AF afterwards.

Full test details and per-session evidence:
[LCD_PIXEL_SHIFT_CAMERA_TEST.md](LCD_PIXEL_SHIFT_CAMERA_TEST.md) and
[`evidence/`](evidence) (files named `20261127-pixel-shift-*` and
`20261128-pixel-shift-*`).

## Credit

Menu labels follow Nikon's public Z8/Z6III pixel-shift manuals. The design
follows [JKWTCN's MIT Z7 II extensions](https://github.com/JKWTCN/z7ii-extensions).
All original-Z7 bindings, the calibration and the merge tool are independent
work. See [CREDITS.md](CREDITS.md).
