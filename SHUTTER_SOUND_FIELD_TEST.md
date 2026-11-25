# Shutter-sound field test: one card swap, one session

Status: **prepared, not staged.** This replaces running the
[smoke test](SHUTTER_SOUND_CAMERA_SMOKE_TEST.md) and the
[trigger probe](SHUTTER_TRIGGER_PROBE_TEST.md) as two separate sessions. No firmware
update; the installed module host stays as is.

## What the module does

One module (`z7-native-modules/plugins/shutter_sound_field_test.c`, 4,184 bytes)
answers four open questions:

1. **Can an SD module play sound on a real Z7?** About 8 host worker ticks after
   power-on it plays the test chime once (rising two notes, 0.45 s).
2. **Which Nikon event marks one photo?** It counts the three capture callbacks
   and logs every event with timestamps to `A:\Z7TRIG.DAT`, as the trigger probe
   does. It never plays a sound on a photo.
3. **Does an upside-down photo get the right EXIF orientation?** The module
   writes Orientation 3 when Nikon's capture pose is 3, and logs every pose
   Nikon's Orientation writer sees ([EXIF_ORIENTATION_RESEARCH.md](EXIF_ORIENTATION_RESEARCH.md)).
4. **Does the AF-area shortcut work on the camera?** In photo mode the movie
   record button (None by default) switches AF-area to Wide-area AF (L); each
   switch is logged ([AF_SHORTCUT_RESEARCH.md](AF_SHORTCUT_RESEARCH.md)). It only
   acts while the movie button's f2 assignment is None, and is meant for photo mode.

The log also records the sound path: chime queued, started, rejected, finished,
and Nikon beeps that passed through. If no chime is heard, the card shows where
it stopped.

| Card file | What it is |
| --- | --- |
| `Z7APP.BIN` | Field-test module, SHA-256 `22d99be1…` |
| `SHUTTER1.WAV` | Test chime, SHA-256 `469f08a6…` |
| `Z7APP.LCD-LABEL-5E62.disabled` | Your current LCD module, parked, unchanged |
| `Z7TRIG.DAT` | Created by the module while it runs |

The custom LCD display features are off during the test.

## Steps (about 5 minutes)

Pause about 5 seconds between steps.

1. Power on. Wait in photo-mode live view for 20 seconds. **Listen for one chime**
   in the first 5 to 15 seconds.
2. Half-press the shutter twice (focus only).
3. Take **one** photo (single frame).
4. Turn Silent photography ON, take **one** photo, turn it OFF.
5. Continuous low: take a burst of about **three** frames.
6. Single frame again: hold the camera **upside down** and take **one** photo.
7. In photo mode, set AF-area to Single-point, then press the **movie record
   button** once. AF-area should change to Wide-area AF (L).
8. Open the menu, then play back one photo.
9. Power off and bring the card back.

## What to report

- Chime: heard or not, and roughly when.
- Image quality setting (JPEG, NEF, or both).
- Whether the upside-down photo opens upright on a computer.
- Whether the movie button switched AF-area to Wide-area AF (L).
- Anything unusual: freeze, error, slow start, repeated sound.

After the session, one command turns the card log into answers (chime, trigger
event, EXIF pose, AF shortcut), with 6 photos for steps 3 to 6 if the burst was 3
frames:

```powershell
.venv\Scripts\python.exe tools/analyze_z7_field_test.py Z7TRIG.DAT --photos 6
```

If the camera freezes, take the battery out and put it back. Removing the card
returns the camera to stock behavior.

## Verified before the camera

- Offline (Unicorn), 29 checks: all four parts install; only `SHUTTER1.WAV` is read
  and only `Z7TRIG.DAT` is written; the first log shows the sound state; the
  chime is queued on tick 8, programs Nikon's setters, finishes, and never
  repeats; a still-file event is logged and passed to Nikon with no sound; Nikon
  beeps are counted; a missing WAV, a busy service and a speaker rejection each
  show up in the log; pose 3 writes Orientation 3 while other poses use Nikon's
  writer, and every pose is logged; a firmware mismatch in the sound or probe
  part touches nothing; the analyzer reads logs written by the compiled module
  and reports the right verdicts for a good session and a failing one; the
  movie button sets Wide-area AF (L) once per press through the validated setter,
  is logged, and does nothing in an unmeasured focus mode or on a button with a
  native function.
- The component audits still apply: playback 80 checks, trigger probe 25, EXIF
  orientation 12, AF shortcut runtime 34 (and an emulator demo where a press
  changed AF-area end to end).
- Assisted QEMU with the exact WAV (10 checks): all four parts install in the
  real guest (the EXIF getter in Nikon's live IFD descriptor, the AF trial's
  update hook), nothing is queued
  at boot, the worker writes a log carrying the sound
  state, queues the chime on tick 8, and the request then reaches the emulator's
  known codec abort (Nikon's own beep hits the same one). The wrappers stay
  installed throughout.
