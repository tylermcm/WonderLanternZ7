# Upside-down photo playback: camera test

Status: **experimental, prepared, not staged.** Your everyday module (the
sound-folder build `8b2b30b1`: display features, shutter sound page with volume
and sound choice, upside-down EXIF fix, all working on the camera) plus playback
that shows upside-down photos the right way up. Combined build `8cbb9b46`
(the earlier `7702d094` was the same playback on the module before the sound
folder).
Design follows JKWTCN's MIT Z7II inverted playback; original-Z7 bindings are
independent work ([EXIF_ORIENTATION_RESEARCH.md](EXIF_ORIENTATION_RESEARCH.md)).

## Camera result, first try (November 25, 2026): not turned

With `8cbb9b46` the upside-down photo (DSC_8496) was remembered correctly
(`Z7INV.DAT` held its number and the file carries Orientation 3), but playback
did not turn it. Nikon builds display requests into **two** blocks with the
same layout: `0xA289A264` (message `0x04160009`), which the hook handled, and
`0xA289A2D4` (message `0x04160004`, built by `0x103D1D54`), which it did not.
The fixed build `8dcee0e0` turns the photo in either block and writes
`A:\Z7IPDBG.DAT` with what the hook saw (message ids and counts, which block,
image ids, rotations, how many were turned), so the next run can be diagnosed
from the card even if it still does not turn. If Nikon's renderer ignores a half
turn, that file will show the rotation was set.

## How it works

- Every photo Nikon shows in playback goes through one display request
  (`0xA289A264`, rotation at `+0x28`), handled by the playback service whose
  handler pointer is in RAM (`0xA289C1D8`, found in the emulator). The module
  wraps that handler and, for an upside-down photo, sets the rotation to a half
  turn just before Nikon draws it. Nikon's own code accepts that value but never
  produces it.
- Nikon's playback cannot tell that a photo is upside down (its index treats
  EXIF Orientation 3 as "no rotation"), so the module remembers them itself:
  when its EXIF fix sees the upside-down pose, it pairs that with the next new
  photo number on the still-file event and saves the list in `A:\Z7INV.DAT`.
- **Only photos taken upside down with this module** are turned. Older photos,
  and photos from other cameras, play back as before.
- JPEG was the format measured; JPEG+NEF pairing is not yet verified.

| Card file | What it is |
| --- | --- |
| `Z7APP.BIN` | Sound folder + playback, SHA-256 `8cbb9b46…` |
| `Z7APP.LCD-SOUND-FOLDER.disabled` | Your current module, kept unchanged |
| `Z7INV.DAT` | Created after your first upside-down photo |

## Steps (about 2 minutes)

1. Power on. Take one photo **upside down**, then one held normally.
2. Wait about 10 seconds in live view.
3. Press **Play**: the upside-down photo should show the right way up; the
   normal one unchanged. Try zooming in on the upside-down photo.
4. Power off and on, press Play again: still the right way up.

## What to report

- Was the upside-down photo turned, and the normal one left alone?
- Any stray lines or pixels along an edge (upstream needed a fix for that on the
  Z7II), or a wrong picture in zoom or the thumbnail grid?
- Anything slow or unusual in playback.

If anything goes wrong, ask me to restore: your current module returns as it was.

## Verified before the camera

- `5e62ce53`, `92602a4a`, `fc9b315e` and `751954d4` still rebuild byte for
  byte; the playback code is behind its own build switch.
- Offline: the 277-check display suite unchanged, the sound and EXIF checks,
  and the playback checks: both wrappers install only over Nikon's stock
  handlers (late install from the worker if the playback service starts after
  the module; a foreign handler is left alone); only the upside-down photo of a
  normal/upside-down/normal sequence is remembered, a JPEG+NEF repeat of the
  same number counts once, and bursts pair in order; a display request for it
  gets the half turn while normal photos, a native tall rotation and other
  messages are untouched; Nikon's handlers always run with the same arguments;
  the list is saved, reloaded after a restart, and a damaged list is ignored.
- Emulator: the module loads and Nikon's menus work. The emulator has no card,
  so playback itself cannot be shown there.
