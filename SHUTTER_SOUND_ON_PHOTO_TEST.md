# Shutter sound on every photo: camera test

Status: **works on the camera, November 25, 2026, but too quiet.**

## Camera result (November 25, 2026)

Staged with the owner's approval; LCD module restored afterwards
([evidence](evidence/20261125-shutter-sound-on-photo-hardware-result.json)).

- **Timing: right on time.** The click came at the press.
- **Burst: a click on every frame** (many frames, not counted).
- **Silent photography off: no extra click** heard over the mechanical
  shutter. The card log agrees for the last power cycle: 7 exposures, none in
  Silent photography, none queued.
- **Volume: very low, hardly audible.** The click's RMS is about half the
  boot chime's. `tools/make_z7_shutter_click.py` now makes a louder click by
  default (`ccf0d0f1`, about 4x the RMS, +12 dB, peak just under full scale);
  the first click stays available as `--level soft` and rebuilds byte for
  byte. The module is unchanged and passes its 19 checks with the louder clip.
- The log is recreated at every power-on, so it only kept the last power cycle
  (Silent photography off). A later build should keep one log per boot.

Builds on the two
[field-test sessions](SHUTTER_SOUND_FIELD_TEST.md) of November 25, 2026, which
showed that an SD module can play sound on the camera and that the capture
controller event `0x0419000B` arrives once per photo and once per burst frame.
No firmware update; the installed module host stays as is.

## What the module does

`z7-native-modules/plugins/shutter_sound_capture_test.c` (3,416 bytes):

- Plays `A:\SHUTTER1.WAV` on each `0x0419000B` while **Silent photography is
  on**, as upstream does. With the mechanical shutter the camera already makes
  its own sound, so the module stays quiet.
- The sound is a new synthetic click (two short curtain-like ticks, 0.12 s), so
  a burst frame finds the sound service free again. If the previous sound is
  still playing, that frame is skipped and counted, never queued late.
- Nikon's own handler always runs, with the same arguments and result.
- No boot chime. It keeps the version-2 diagnostic log in `Z7TRIG.DAT`, with
  the trigger counters (exposures seen, in Silent photography, queued, busy)
  in its header.

| Card file | What it is |
| --- | --- |
| `Z7APP.BIN` | Test module, SHA-256 `2c176587…` |
| `SHUTTER1.WAV` | Synthetic click, SHA-256 `a0712773…` |
| `SHUTTER1-CHIME.WAV` | The field-test chime, renamed |
| `Z7APP.LCD-LABEL-5E62.disabled` | Your LCD module, parked, unchanged |
| `Z7TRIG-SESSION2.DAT` | The session-2 log, renamed |

## Steps (about 2 minutes)

1. Power on and wait about 10 seconds in photo-mode live view. There is **no
   chime** this time.
2. Turn **Silent photography on**. Take **3 single photos**, a few seconds
   apart. Expect one click per photo.
3. Still silent, continuous low: take a burst of about **4** frames.
4. Turn **Silent photography off**. Take **2 single photos**. Expect only the
   normal mechanical shutter, no extra click.
5. Power off and bring the card back.

## What to report

- Step 2: did each photo click, and did it sound at the press or late?
- Step 3: how many frames, and roughly how many clicks?
- Step 4: any extra click? (There should be none.)
- Is the volume right? Anything unusual?

If the camera freezes, take the battery out and put it back. Removing the card
returns the camera to stock behavior.

## Verified before the camera

- Offline (Unicorn), 19 checks with the exact click: the module loads, installs
  the playback intercept and the three probe wrappers, reads only
  `SHUTTER1.WAV`, plays nothing at boot, queues one sound on `0x0419000B` in
  Silent photography and none with the mechanical shutter, ignores every other
  event and callback, runs Nikon's handler with the same arguments and result,
  counts a busy service without retrying, sounds each of four burst frames once
  the previous click finished, programs Nikon's sound setters, writes the
  counters to the log, stays silent without a WAV, and touches nothing on a
  firmware mismatch.
- The field-test (42 checks) and trigger-probe (25 checks) audits still pass
  with the shared code, and the v5 field-test module rebuilds byte for byte.
- Assisted QEMU, 7 checks: the module loads in the real guest, installs the
  intercept and wrappers, queues nothing for 60 seconds without a photo, and
  writes its log. The emulator cannot play sound or take a photo.

Credit: design follows JKWTCN's MIT `shutter_sound.c` (silent-mode only);
original-Z7 bindings are independent work.
