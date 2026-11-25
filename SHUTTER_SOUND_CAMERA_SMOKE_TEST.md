# Shutter-sound camera smoke test

Status: **superseded by the one-session [field test](SHUTTER_SOUND_FIELD_TEST.md);** kept as a
fallback. Prepared, not staged. Nothing is on the card until the owner approves
staging. No firmware update is involved: the installed module host stays as is.

## What this tests

One question: does the SD-module playback path produce sound on a real Z7? The
emulator can't answer it (see [SHUTTER_SOUND_SD_PORT.md](SHUTTER_SOUND_SD_PORT.md)):
it crashes on every sound request, Nikon's own beep included.

The test module plays one short chime a few seconds after power-on and does
nothing else. It has no photo trigger, no menu and never writes to the card.

| Card file | What it is |
| --- | --- |
| `Z7APP.BIN` | Boot-preview test module, 2060 bytes, SHA-256 `b87e8a5a…` |
| `SHUTTER1.WAV` | Rising two-note chime (C6 then G6), 0.45 s, 48 kHz mono |
| `Z7APP.LCD-LABEL-5E62.disabled` | Your current LCD module, parked, unchanged |

While the test module is active, the custom LCD display features are off; the
camera shows Nikon's standard screens. Putting the LCD module back is a rename.

## Steps

1. Power the camera on. Wait about 15 seconds without touching anything.
2. Listen for one rising two-note chime, roughly 5 to 10 seconds after power-on.
   It should play once, not repeat.
3. Use the camera for a minute: take two photos, open the menu, play back a photo.
4. Power off and on again. The chime should play once more.

## What to report

- Chime heard: yes or no. If yes, about how many seconds after power-on.
- Anything unusual: freeze, error message, slow start, repeated sound.

If the camera freezes or won't respond, take the battery out and put it back,
then tell me. Removing the card returns the camera to stock behavior.

## Why a delay

The chime waits for the module host's eighth resident-worker tick instead of
playing while the module loads, so the camera has finished starting its display
and audio. If the sound service is busy at that moment, the module skips the
preview and doesn't retry.

## Verified before the camera

- Offline (Unicorn): 80 checks, including the exact `SHUTTER1.WAV` decoded
  sample-for-sample, nothing queued at load, one preview on worker tick 8, never
  repeated, skipped when the service is busy, silent without the WAV.
- Assisted QEMU with the exact WAV: boot completes with nothing queued; the
  worker queues the preview on tick 8; it then reaches the emulator's known
  codec abort, the same one Nikon's own beep hits.

Afterwards the restore script parks the test module as
`Z7APP.SHUTTER-SOUND-PREVIEW.disabled` and puts `5e62` back as `Z7APP.BIN`.
