# Everyday LCD module: shutter sound 1–9 plus the upside-down photo fix

Status: **works on the camera, November 25, 2026; installed.** The upside-down
photo taken with this module (DSC_8481, JPEG) carries Orientation 3
([evidence](evidence/20261125-lcd-sound-exif-hardware-result.json)).

Original status: prepared, not staged. This is your installed module (`fc9b315e`,
shutter sound with volume OFF/1–9, which works on the camera) with the
upside-down photo EXIF fix added. That fix already worked on your camera in the
[field test](SHUTTER_SOUND_FIELD_TEST.md#camera-result-november-25-2026): the
upside-down photo was saved with Orientation 3, so computers show it upright.
No firmware update; the installed module host stays as is.

## What changes

- **Photos taken upside down** are saved with EXIF Orientation 3 instead of 1.
  Nothing else in the photo changes; landscape (1) and vertical (8 or 6) photos
  are written by Nikon's own code as before. Only JPEG was checked on the camera.
- **Everything else is unchanged**: display features, the Shutter sound row and
  your saved level. The previous module stays on the card as
  `Z7APP.LCD-SHUTTER-SOUND-9.disabled`.
- In-camera playback still shows upside-down photos upside down (separate work).

| Card file | What it is |
| --- | --- |
| `Z7APP.BIN` | Module with sound and EXIF fix, SHA-256 `751954d4…` |
| `Z7APP.LCD-SHUTTER-SOUND-9.disabled` | Your current module, kept unchanged |

## Steps (about 1 minute)

1. Power on and take one photo with the camera **upside down**, and one normal.
2. Bring the card back (or open the photo on a computer): the upside-down photo
   should open the right way up. I can also read the tag for you.

## Verified before the camera

- `5e62ce53`, `92602a4a` and `fc9b315e` still rebuild byte for byte; the fix is
  behind its own build switch.
- Offline: the 277-check display suite passes unchanged plus the sound checks
  for all nine levels and the EXIF checks: the getter is installed in Nikon's
  live IFD0 descriptor, the table is a copy with only the Orientation writer
  swapped, poses 0/1/2/3/4 write 1/8/6/3/1, and a foreign descriptor is left
  alone while the module still loads.
- The same EXIF component ran on the camera in the field test (session 1).

Credit: design follows JKWTCN's MIT `photo_rotation.h`; original-Z7 bindings are
independent work ([EXIF_ORIENTATION_RESEARCH.md](EXIF_ORIENTATION_RESEARCH.md)).
