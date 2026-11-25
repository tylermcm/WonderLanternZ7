# Original Z7 development update — November 25, 2026

This update covers new SD-module features built and checked **offline and in an
emulator** on November 24–25, and the first camera field test of them (end of
this page). The
hardware-verified scope is unchanged from the
[November 23 update](DEVELOPMENT_UPDATE_2026-11-23.md). Read
[RISK_NOTICE.md](RISK_NOTICE.md) before trying any build.

## New work, all on the SD module (no firmware patch)

| Feature | Where it stands | Details |
| --- | --- | --- |
| Shutter sound playback | The module reads `SHUTTER1.WAV` and plays it through Nikon's own sound service, intercepting only its own job. 80 offline checks. The emulator can't play sound: Nikon's own beep crashes it the same way. | [SHUTTER_SOUND_SD_PORT.md](SHUTTER_SOUND_SD_PORT.md) |
| Shutter sound trigger | Upstream's Z7II photo events don't exist on the Z7. A silent probe logs three Nikon capture callbacks to the card so one camera session can pick the per-photo event. A provisional still-file trigger (JPEG+NEF sounds once) is built. | [SHUTTER_SOUND_SD_PORT.md](SHUTTER_SOUND_SD_PORT.md) |
| Upside-down photo EXIF | Nikon's Orientation writer drops pose 3, so upside-down photos are saved as Orientation 1. The module swaps only that writer to write 3. Whether the Z7 records pose 3 is measured on the camera. | [EXIF_ORIENTATION_RESEARCH.md](EXIF_ORIENTATION_RESEARCH.md) |
| Upside-down photo playback | Traced, not built; a read-only observer is in the field test. Nikon's playback lookup and rotation table have no half turn, so upside-down photos play back unrotated even with Orientation 3. 42 offline checks run Nikon's own code. The live RAM handler table that a port would redirect was found in the emulator. | [EXIF_ORIENTATION_RESEARCH.md](EXIF_ORIENTATION_RESEARCH.md#in-camera-playback-traced-not-built) |
| AF-area shortcut | AF-area values, the setter, all five button inputs and the f2 assignments were measured by driving Nikon's own menus in the emulator. A validating runtime switched AF-area end to end in the emulator when a button was pressed. No target-picker menu or saved settings yet. | [AF_SHORTCUT_RESEARCH.md](AF_SHORTCUT_RESEARCH.md) |

## One camera session for all of it

[SHUTTER_SOUND_FIELD_TEST.md](SHUTTER_SOUND_FIELD_TEST.md) describes a single
field-test module and a ~6-minute session: hear one chime after power-on, take a
few photos (single, silent, burst, one upside down, one vertical), press the
movie button once in photo mode, view the vertical and upside-down photos in
playback, then bring the card back. The module logs everything to
`Z7TRIG.DAT`, and `tools/analyze_z7_field_test.py` turns that log into five
answers. The fifth comes from a read-only playback observer that records the
rotation Nikon's playback requests for each photo shown, the value an
upside-down playback module would change. It temporarily replaces the LCD module on the card, has no firmware
update, and has not been staged.

## Emulator method used

Most new bindings were measured by pressing keys through Nikon's own
AutoOperation path in assisted QEMU and watching which word changed
(`tools/probe_z7_menu_walk.py`, `tools/probe_z7_switch_watch.py`), then confirming
the property key with Nikon's getter offline. Each audit re-checks the recorded
runs, including screenshot hashes.

## Credits

Feature designs follow JKWTCN's MIT
[z7ii-extensions](https://github.com/JKWTCN/z7ii-extensions); original-Z7
bindings are independent work. See [CREDITS.md](CREDITS.md).

## Camera field test result (November 25, evening)

The owner ran field test v4 on the camera ([results](SHUTTER_SOUND_FIELD_TEST.md#camera-result-november-25-2026)):

- **SD-module sound works**: the test chime played from the card.
- **Upside-down EXIF works**: the upside-down photo was saved with Orientation 3.
- **AF-area shortcut trial works**: the movie button switched to Wide-area AF (L).
- **Photo trigger unsolved**: the still-file callback never fired, so the
  provisional trigger is ruled out.
- **Playback observer: no data**, lost to a log overflow from live-view events.
  In-camera upside-down playback is still not built.

Nothing unusual happened; the LCD module was restored afterwards.

A second session with a fixed log (v5) found the per-photo event for the shutter
sound (`0x0419000B` on the capture controller callback, once per photo and
burst frame) and confirmed on the camera that the playback request holds the
photo being shown ([session 2](SHUTTER_SOUND_FIELD_TEST.md#session-2-result-v5-november-25-2026)).
