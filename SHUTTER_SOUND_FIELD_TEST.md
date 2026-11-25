# Shutter-sound field test: one card swap, one session

Status: **prepared, not staged.** This replaces running the
[smoke test](SHUTTER_SOUND_CAMERA_SMOKE_TEST.md) and the
[trigger probe](SHUTTER_TRIGGER_PROBE_TEST.md) as two separate sessions. No firmware
update; the installed module host stays as is.

## What the module does

One module (`z7-native-modules/plugins/shutter_sound_field_test.c`, 3,160 bytes)
answers both open questions:

1. **Can an SD module play sound on a real Z7?** About 8 host worker ticks after
   power-on it plays the test chime once (rising two notes, 0.45 s).
2. **Which Nikon event marks one photo?** It counts the three capture callbacks
   and logs every event with timestamps to `A:\Z7TRIG.DAT`, as the trigger probe
   does. It never plays a sound on a photo.

The log also records the sound path: chime queued, started, rejected, finished,
and Nikon beeps that passed through. If no chime is heard, the card shows where
it stopped.

| Card file | What it is |
| --- | --- |
| `Z7APP.BIN` | Field-test module, SHA-256 `843e480f…` |
| `SHUTTER1.WAV` | Test chime, SHA-256 `469f08a6…` |
| `Z7APP.LCD-LABEL-5E62.disabled` | Your current LCD module, parked, unchanged |
| `Z7TRIG.DAT` | Created by the module while it runs |

The custom LCD display features are off during the test.

## Steps (about 3 minutes)

Pause about 5 seconds between steps.

1. Power on. Wait in photo-mode live view for 20 seconds. **Listen for one chime**
   in the first 5 to 15 seconds.
2. Half-press the shutter twice (focus only).
3. Take **one** photo (single frame).
4. Turn Silent photography ON, take **one** photo, turn it OFF.
5. Continuous low: take a burst of about **three** frames.
6. Open the menu, then play back one photo.
7. Power off and bring the card back.

## What to report

- Chime: heard or not, and roughly when.
- Image quality setting (JPEG, NEF, or both).
- Anything unusual: freeze, error, slow start, repeated sound.

If the camera freezes, take the battery out and put it back. Removing the card
returns the camera to stock behavior.

## Verified before the camera

- Offline (Unicorn), 17 checks: both parts install; only `SHUTTER1.WAV` is read
  and only `Z7TRIG.DAT` is written; the first log shows the sound state; the
  chime is queued on tick 8, programs Nikon's setters, finishes, and never
  repeats; a still-file event is logged and passed to Nikon with no sound; Nikon
  beeps are counted; a missing WAV, a busy service and a speaker rejection each
  show up in the log; a firmware mismatch in either part touches nothing.
- The component audits still apply: playback 80 checks, trigger probe 25.
- Assisted QEMU with the exact WAV (8 checks): both parts install in the real
  guest, nothing is queued at boot, the worker writes a log carrying the sound
  state, queues the chime on tick 8, and the request then reaches the emulator's
  known codec abort (Nikon's own beep hits the same one). The wrappers stay
  installed throughout.
