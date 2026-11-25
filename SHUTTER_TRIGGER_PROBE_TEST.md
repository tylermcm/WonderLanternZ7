# Shutter-sound trigger probe: camera measurement

Status: **prepared, not staged.** Run after the playback smoke test
([SHUTTER_SOUND_CAMERA_SMOKE_TEST.md](SHUTTER_SOUND_CAMERA_SMOKE_TEST.md)) and its
restore. No firmware update; the installed module host stays as is.

## Why

A shutter sound must play once per photo and never in plain live view. The
October firmware patch failed on exactly that: its event also fired in live view.
Upstream's Z7II trigger events don't exist on the Z7, and QEMU can't take a
photo, so the Z7 event has to be measured on the camera.

## What the module does

It plays no sound. It wraps three Nikon callbacks found in a stock boot:

| Callback slot | Native handler | Role (static analysis) |
| --- | --- | --- |
| `0xA18D1BD8` | `0x101426A9` | Capture-controller notification consumer |
| `0xA18D1BDC` | `0x1014708D` | Capture consumer (October's live-view trigger) |
| `0xA18D2750` | `0x104DB211` | Still-file finalization (`0x041E0002`) |

Each wrapper counts the event, keeps the first two words of its packet, then
calls Nikon's handler with the same arguments and returns its result. Every few
seconds the module's worker writes the counts and the last 128 events, with
timestamps and Silent photography changes, to `A:\Z7TRIG.DAT` (3,264 bytes,
at most 400 writes per power-on). It refuses to load on any other firmware and
leaves any slot alone that doesn't hold the expected Nikon function.

## Steps (about 3 minutes)

Pause about 5 seconds between steps so they separate in the log.

1. Power on. Leave the camera in photo mode, live view, for 20 seconds.
2. Half-press the shutter twice (focus only).
3. Take **one** photo (single-frame release).
4. Take **one** photo with Silent photography ON, then turn it back OFF.
5. Switch to continuous low and take a burst of about **three** frames.
6. Open the menu, then play back one photo.
7. Power off. Bring the card back, or copy `Z7TRIG.DAT` off it.

Note your image quality (JPEG, NEF, or both): it changes how many still-file
events a photo makes.

## What the log answers

- Which event arrives exactly once per photo, in steps 3 to 5.
- Which events also fire in steps 1, 2 and 6 (those can't be the trigger).
- Whether Silent photography changes the sequence.

`tools/read_z7_trigger_log.py` decodes the file. Then the sound trigger is wired to
the event the counts support.

## Verified before the camera

- Offline (Unicorn): 25 checks covering install, exact argument and return
  pass-through, per-slot counts, ring order and packet words, Silent photography
  markers, the write schedule and 400-write cap, foreign-slot and
  firmware-mismatch refusal, file failures, and candidate ranking. Three
  mutations (write timing, argument forwarding, write cap) are each caught.
- Assisted QEMU: the wrappers install into the live slots and stay there while
  the guest runs; no callback fires in the idle emulated view; one run captured a
  complete, parseable log written through Nikon's file functions.

`tools/read_z7_trigger_log.py Z7TRIG.DAT --photos 5` ranks each callback and event
by how many distinct photo records it saw (5 = steps 3 to 5 if the burst was 3).
