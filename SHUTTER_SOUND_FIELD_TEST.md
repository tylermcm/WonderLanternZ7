# Shutter-sound field test: one card swap, one session

Status: **ran on the camera twice, November 25, 2026** (session 2 result first below; session 1 v4 `b76d6c4b`, staged with the
owner's approval, LCD module restored afterwards). Results are under
[Camera result](#camera-result-november-25-2026) and in [the evidence file](evidence/20261125-field-test-hardware-result.json).

## Session 2 result (v5, November 25, 2026)

Staged with the owner's approval, LCD module restored afterwards
([evidence](evidence/20261125-field-test-session-2-hardware-result.json)).
8 photos (3 single, a burst of 4, 1 vertical); the log v2 kept everything.

- **Per-photo trigger found.** Controller callback `0xA18D1BD8` event
  `0x0419000B` fired exactly 8 times, first in each exposure's sequence
  (`0x0419000B`, `0x0419000D`, consumer `0x04190004`/`0x04190005`, `0x0419000E`,
  `0x04190003`), once per burst frame, and never outside photos. The photo
  file is written about 12–17 display updates later. `0x0419000B` is the
  candidate shutter-sound trigger.
- The still-file callback fired once per photo this time but never in session
  1, so it is not relied on.
- **Playback request confirmed live.** The request block and turn cache held the
  id of the photo on screen (DSC_8312 vertical: turn 1, request rotation 0;
  DSC_8311: turn 0, rotation 0). Rotation 0 for the tall photo matches the
  unrotated full-screen view the owner saw, which is what Nikon does with Rotate
  tall OFF. The worker kept running in playback.
- Chime played again; nothing unusual.

## Session 2 (v5): plan as staged

Session 1 left two questions open, the per-photo trigger and the playback
rotation values, because live-view events overflowed the log. Field test v5
(`73ec9f0f…`, 4,696 bytes) fixes the
log, version 2:

- Each capture-callback event is logged for its first 24 occurrences only, then
  just counted, so live-view events (about 180 per worker tick) cannot push out
  rare ones. Counts stay exact.
- The log never wraps: it holds 512 entries and counts any further ones.
- Every entry carries a display-update stamp, a finer clock than worker ticks,
  so a candidate photo event can be lined up with the EXIF writer, which runs
  once per saved photo.

The chime, EXIF fix, AF trial and playback observer are unchanged. The card
keeps `SHUTTER1.WAV`; the session-1 log is renamed `Z7TRIG-SESSION1.DAT`.

### Session 2 steps (about 3 minutes)

1. Power on and wait 15 seconds in photo-mode live view (the chime plays again).
2. Take **3 single photos**, about 5 seconds apart.
3. Continuous low: take a burst of about **3** frames.
4. Back on single frame, hold the camera **vertically** and take **one** photo.
5. Press **Play** (it shows the vertical photo). After 5 seconds, half-press the
   shutter to go back to live view and wait **10 seconds**.
6. Press **Play**, press **left** once, wait 5 seconds, half-press, and wait
   **10 seconds** in live view.
7. Power off and bring the card back.

The module only runs while live view is up, which is why steps 5 and 6 return
to live view: it then reads the rotation Nikon kept for the last photo shown.
Report the burst length; the analysis uses `--photos` 3 + burst + 1.

### Verified before the camera (v5)

- Offline, 42 checks: the 35 v4 checks plus a recreated session-1 flood (1,200
  live-view events), after which the rare capture event, the EXIF pose, the AF
  switch and the playback entry are all still in the log with correct stamps;
  exact counts; the EXIF writer counted in the header; the analyzer ranking the
  rare event that falls just before the photo; and a full log that stops at
  512 entries instead of wrapping. The trigger-probe audit (25 checks) passes
  with the shared v2 log.
- Assisted QEMU, 10 checks, and the v2 log the real guest wrote parses.

## Camera result (November 25, 2026)

| Question | Result |
| --- | --- |
| SD-module sound | **Works.** The chime played 7–10 s after power-on; the log shows it queued, started once and finished. |
| Upside-down EXIF | **Works.** The upside-down photo was saved with Orientation 3 (the vertical one with 8, the others with 1), so the Z7 does record pose 3. |
| AF-area shortcut trial | **Works.** The movie button switched AF-area to Wide-area AF (L). |
| Per-photo trigger | **Unsolved.** The still-file callback `0xA18D2750` never fired for 7 JPEG Fine* photos, so the provisional still-file trigger would not work. No event on the other two callbacks counted 7. |
| Playback rotation values | **No data.** Live-view events on the capture callbacks (about 180 per worker tick) overwrote the 128-entry log ring, taking the EXIF, AF and playback entries with them. The owner saw the vertical photo upright and the upside-down photo upside down, as expected. |
| Stability | Nothing unusual. |

The ring overflow is a probe design fault: high-rate callbacks should be
counted, not logged one by one. The next probe keeps them out of the ring.

This replaces running the
[smoke test](SHUTTER_SOUND_CAMERA_SMOKE_TEST.md) and the
[trigger probe](SHUTTER_TRIGGER_PROBE_TEST.md) as two separate sessions. No firmware
update; the installed module host stays as is.

## What the module does

One module (`z7-native-modules/plugins/shutter_sound_field_test.c`, 4,376 bytes)
answers five open questions:

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
5. **Where does playback decide a photo's rotation?** A read-only observer
   logs Nikon's playback display request (rotation code) and turn cache each
   time they change, so viewing a tall photo and the upside-down photo shows
   the values an upside-down playback module would change
   ([EXIF_ORIENTATION_RESEARCH.md](EXIF_ORIENTATION_RESEARCH.md#in-camera-playback-traced-not-built)).
   It writes nothing in camera memory.

The log also records the sound path: chime queued, started, rejected, finished,
and Nikon beeps that passed through. If no chime is heard, the card shows where
it stopped.

| Card file | What it is |
| --- | --- |
| `Z7APP.BIN` | Field-test module, SHA-256 `b76d6c4b…` |
| `SHUTTER1.WAV` | Test chime, SHA-256 `469f08a6…` |
| `Z7APP.LCD-LABEL-5E62.disabled` | Your current LCD module, parked, unchanged |
| `Z7TRIG.DAT` | Created by the module while it runs |

The custom LCD display features are off during the test.

## Steps (about 6 minutes)

Pause about 5 seconds between steps.

1. Power on. Wait in photo-mode live view for 20 seconds. **Listen for one chime**
   in the first 5 to 15 seconds.
2. Half-press the shutter twice (focus only).
3. Take **one** photo (single frame).
4. Turn Silent photography ON, take **one** photo, turn it OFF.
5. Continuous low: take a burst of about **three** frames.
6. Single frame again: hold the camera **upside down** and take **one** photo.
7. Hold the camera **vertically** (grip up) and take **one** photo.
8. In photo mode, set AF-area to Single-point, then press the **movie record
   button** once. AF-area should change to Wide-area AF (L).
9. Press **Play**. Show the vertical photo for about 5 seconds, then the
   upside-down photo for about 5 seconds. Leave Rotate tall at its default (ON).
10. Power off and bring the card back.

## What to report

- Chime: heard or not, and roughly when.
- Image quality setting (JPEG, NEF, or both).
- Whether the upside-down photo opens upright on a computer.
- Whether the movie button switched AF-area to Wide-area AF (L).
- In playback: did the vertical photo show upright, and was the upside-down
  photo shown upside down (expected today)?
- Anything unusual: freeze, error, slow start, repeated sound.

After the session, one command turns the card log into answers (chime, trigger
event, EXIF pose, AF shortcut, playback rotation), with 7 photos for steps 3 to 7
if the burst was 3 frames:

```powershell
.venv\Scripts\python.exe tools/analyze_z7_field_test.py Z7TRIG.DAT --photos 7
```

If the camera freezes, take the battery out and put it back. Removing the card
returns the camera to stock behavior.

## Verified before the camera

- Offline (Unicorn), 35 checks: all five parts install; only `SHUTTER1.WAV` is read
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
  native function; the playback observer logs each change of the request and
  turn cache once, stays quiet otherwise, writes no camera memory, stops after
  48 reports, and the analyzer reads its entries back.
- The component audits still apply: playback 80 checks, trigger probe 25, EXIF
  orientation 12, AF shortcut runtime 34 (and an emulator demo where a press
  changed AF-area end to end).
- Assisted QEMU with the exact WAV (10 checks): all four parts install in the
  real guest (the EXIF getter in Nikon's live IFD descriptor, the AF trial's
  update hook), nothing is queued
  at boot, the worker writes a log carrying the sound
  state, queues the chime on tick 8, and the request then reaches the emulator's
  known codec abort (Nikon's own beep hits the same one). The wrappers stay
  installed throughout. The playback observer read the real guest's request and
  cache (empty, since the emulator has no card or playback) without fault.
