# Silent shutter sound as an SD module — original-Z7 binding map

Status: **playback works on the camera (November 25, 2026 field test); no photo
trigger and no menu yet.** The test chime played from the SD module. The
provisional still-file trigger is ruled out: its callback never fired for 7
photos ([field result](SHUTTER_SOUND_FIELD_TEST.md#camera-result-november-25-2026)). A second session found
the per-photo event: controller callback `0xA18D1BD8` event `0x0419000B`, once
per photo and per burst frame, first in each exposure
([session 2](SHUTTER_SOUND_FIELD_TEST.md#session-2-result-v5-november-25-2026)).
A camera-test module that plays a synthetic click on that event in Silent
photography **worked on the camera**: on time, on every burst frame, silent
with the mechanical shutter, but too quiet; a louder click is prepared
([result](SHUTTER_SOUND_ON_PHOTO_TEST.md#camera-result-november-25-2026)).
The louder click then played on all 22 Silent-photography exposures. The sound
is now built into the LCD module with a **Shutter sound** volume row (OFF, 1–7)
on its settings page, saved in `Z7SND.DAT`
([test plan](LCD_SHUTTER_SOUND_TEST.md)); not yet staged.

## Why a new approach

The October attempt ([PORT_AUDIT.md](PORT_AUDIT.md)) was a firmware patch derived
from Z30 code. It patched native sound code in flash, got audible Preview on the
owner's Z7, then failed on camera: the chosen trigger (`0x04190001`) also fires in
plain live view, so the sound repeated. That build is on hold and is not reused.

JKWTCN's pinned Z7II feature
([shutter-sound.md](https://github.com/JKWTCN/z7ii-extensions/blob/f298964fdf6b0d20df0d3c6cad48a74aa5f5c339/docs/shutter-sound.md),
MIT) is an SD module. It changes only RAM function pointers: it queues its own job
to Nikon's sound service and intercepts **only that job** in the service's start
handler, then programs PCM through the service's own setters. Every test of an SD
module is a card-file swap, not a firmware update.

## Z7 sound service matches the Z7II design

Derived from the original Z7 C 3.80 MAIN by static disassembly, plus a read-only
dump of the live handler table from a stock boot in isolated assisted QEMU.
Event numbering differs from the Z7II (`0x0418xxxx` here vs `0x0419xxxx`), so no
Z7II address or ID is reused.

| Role | Z7II (upstream) | Original Z7 C 3.80 | Evidence |
| --- | --- | --- | --- |
| Post event + payload to sound service | `0x102B325D` | `0x100A2D79` | Allocates 0x1C message: `+0x10` event, `+0x14` payload, `+0x0C` completion |
| Sound mailbox handle | `0xB18646AC` | `0xA18852AC` | Literal used by the post function |
| Start-request event | `0x0419001E` | `0x0418001E` | Dispatcher accepts `0x0418001E..21` |
| Finished event to record's done callback | `0x04190023` | `0x04180023` | Sent by playing-state stop handler `0x1006BEE3` |
| Message dispatcher | — | `0x1006BB58` | Indexes handler table by state byte and event |
| Start handler (native) | `0x102611CB` | `0x1006BC47` | Live table, state 0 / event `0x0418001E` |
| Start handler RAM slot | `0xB18646C8` | `0xA188D278` | Table base `0xA188D190+0xE8`, `state*16 + index*4` |
| Service state (state, left, right bytes; counters) | `0xB18646B4` | `0xA188D190` | Matches October's corrected busy address |
| Record copy (0x24 bytes) | `0xB21E2630` | `0xA21AB994` | Start handler copies the record here |
| Speaker check / second check | `0x1036F781` / `0x1036F867` | `0x100CF90B` / `0x100CF98D` | Same pass condition (byte 1, result 0) |
| Format setter | `0x10260CB5` | `0x1006B795` | `{u8 2, 05 01 01, u32 bytes}`, same format bytes as upstream |
| Tone setter | `0x10260B4D` | `0x1006B62D` | `{2, play, tone, alt, alt tone, right, right tone}` |
| Data setter | `0x10260E6B` | `0x1006B94B` | `{pcm, bytes, 1, 0, loop}` |
| DMA start + callback | `0x10260CFD`, `0x1026118D` | `0x1006B7DD`, `0x1006BC09` | `{u8 2, callback}` |
| Completion → job release | — | `0x100A2D5F` | Calls `job[1](event, job)`, frees message |
| DMA cache clean / invalidate | `0x1034F9ED` / `0x1034FA29` | `0x101E9F39` / `0x101E9F77` | Already used by the module's settings file adapter |
| Silent photography property | `0x057A` | `0x0576` | [SILENT_PROPERTY_FIX.md](SILENT_PROPERTY_FIX.md) |

Record layout is identical on both bodies: `play, tone, alternate, alternate tone,
right, right tone, repeats, type, done`. The Z7 start handler rejects `type >= 18`
for native requests, consistent with October's finding.

Upstream's job layout also maps directly: the native start handler reads the
record pointer from `job[0]`, the dispatcher writes the result to `job[2]`, and the
completion calls `job[1]` as the release callback.

`tools/audit_z7_sound_service_bindings.py` re-checks these facts against the stock
MAIN: 27 literal, call-target and instruction checks, plus 4 live-table values
from the private stock QEMU dump (31 total, all pass). Static checks confirm what
the code references; they do not execute it. The playback audit below is where
the native post, dispatcher and completion actually run.

## Step 1: playback module

Sources: `z7-native-modules/plugins/shutter_sound_playback.h` (engine),
`shutter_sound_module.c` (install only) and `shutter_sound_boot_preview.c` (same,
plus one preview queued by the host's resident worker on its eighth tick, so the
camera has finished starting before anything plays). Built by
`tools/build_z7_shutter_sound.py`, twice per build to confirm the bytes reproduce.

What the module does at boot:

1. Reads `A:\SHUTTER1.WAV` once, read-only, through the native file functions. It
   accepts 48 kHz 16-bit mono or stereo, at most one second. Any other file means
   nothing is installed.
2. Checks the first instruction words of the nine native functions it calls or
   replaces. If any differ (other firmware), the module returns an error and the
   host frees it. It changes nothing.
3. Stores its handler into the start slot `0xA188D278` with one word write, and
   only if the slot still holds the native `0x1006BC47`.

The handler forwards every request that isn't the module's own job to the native
start handler untouched. For its own job it repeats the native preconditions
(speaker on, second check clear, service idle), then programs the setters with the
same argument shapes the native handler builds. The record is type 18, which the
native handler rejects, so if the intercept were ever missing the job would
release without playing anything. This trial reads one clip and has five volume
levels. The menu and the other four clips come with step 3.

**Offline audit** (`tools/audit_z7_shutter_sound_playback.py`, 80 checks, all
pass). It runs the original host loader, the compiled module, and Nikon's post
function, message dispatcher and completion in Unicorn. It stubs the filesystem
dispatcher, allocator, mailbox send, speaker checks, the four setters and the
native start handler; it records their arguments but doesn't execute them. Covered:
WAV decode edge cases, install and no-install paths, firmware-mismatch refusal,
setter order and arguments, native passthrough, every rejection path releasing the
job, busy and allocation failure, the deferred preview (nothing at load, one
preview on tick 8, never repeated, skipped when busy) and the exact card WAV
decoded sample-for-sample. A mutation test (tone 31→30) fails as expected.

**Assisted QEMU, real guest tasks** (`tools/probe_z7_shutter_sound.py`):

| Run | Result |
| --- | --- |
| Install-only module + WAV | WAV read through the file fixture, slot holds the module handler, nothing queued, no private start in 4 s of running (6/6) |
| Same module, no WAV | Nothing installed, slot keeps `0x1006BC47` (3/3) |
| Boot-preview module + card WAV | Boot completes with nothing queued; the worker queues the preview on tick 8; it then reaches the known codec abort below (6/6) |

**Emulator limit: playback can't be tested in QEMU.** Any sound request, Nikon's
own beep included, crashes the emulated codec task.
`tools/probe_z7_sound_differential.py` queued one request at the GUI checkpoint
and decoded the exception frame:

| Request | Module handler in slot | Outcome |
| --- | --- | --- |
| None | yes | No exception in 8 s |
| Stock type-0 beep, module **not** installed | no (`0x1006BC47`) | Data abort |
| Stock type-0 beep through module passthrough | yes | Same data abort |
| Module's private preview | yes | Same data abort |

All three aborts are identical: data abort at `0x100CBB3E` (`ldrb r2,[r0,#4]`,
r0 = 0) in codec-channel function `0x100CBB3A`, called from `0x100CEA0E` with
channel 0's object pointer, which is null in emulation. Nikon's exception reporter
`0x100545EC` then sends the flash chip its CFI autoselect (ID read) commands
(`AAA←AA, 554←55, AAA←90`), which QEMU refuses as a flash write and stops. The
null object is probably due to the unmodeled audio codec (QEMU logs repeated I2C
NACKs at address `0x1D`); that part is not proven. Because the stock beep fails
identically with the module out of the path, the abort is an emulator gap, not a
module fault. The setters and DMA can only be verified on a camera.

## Trigger: still open

Upstream triggers on two Z7II photo events (`0x041A000F` RAW ready, `0x041B0090`
input ready). **Neither ID exists in the Z7 firmware.** Candidate Z7 signals:

- **Still-file finalization `0x041E0002`** through RAM slot `0xA18D2750`
  (live value `0x104DB211`, confirmed). Per saved record, not per exposure: JPEG+NEF
  gives two events (dedupe by slot/group/number with the native comparator), and it
  fires at save time, so the sound can lag in bursts.
- **Capture controller consumer** slot `0xA18D1BDC` (live `0x1014708D`). Its
  `0x04190001` event also fires in plain live view; rejected alone (October).
- An earlier RAW-pipeline event on the `0x041A` family, which does exist on the Z7,
  is the closest analogue to upstream; not yet identified.

Per-photo cardinality cannot be proven in QEMU, which does not complete a capture.

### Step 2: trigger probe module (built, not on camera)

The family shift seen in the sound service (`0x0419xxxx` on Z7II, `0x0418xxxx` on
Z7) suggests upstream's RAW-ready `0x041A000F` maps to `0x0419000F` here. That ID
doesn't appear as a literal either, and the capture consumer's event switch sends
it to its default case, so the guess isn't confirmed. Registration code
(`0x100752D2`/`0x100752DE`, called from `0x10147BB8`/`0x10147BBE`) fills two
callback words on the capture-controller object `0xA18D1B98`; the other two stay
empty. A read-only QEMU dump (`tools/probe_z7_capture_slots.py`) confirms the live
values:

| Slot | Live handler | Calling convention |
| --- | --- | --- |
| `0xA18D1BD8` | `0x101426A9` | `(event, packet)`, no stack arguments |
| `0xA18D1BDC` | `0x1014708D` | `(event, packet)`, no stack arguments |
| `0xA18D2750` | `0x104DB211` | `(event, packet)`, no stack arguments |

`z7-native-modules/plugins/shutter_trigger_probe.c` wraps all three. Each wrapper
counts the event, keeps the packet's first two words, and calls Nikon's handler
with the same arguments and result. The worker logs counts, the last 128 events
with timestamps, and Silent photography changes to `A:\Z7TRIG.DAT`
(`tools/read_z7_trigger_log.py` decodes it). Offline audit
(`tools/audit_z7_trigger_probe.py`): 25 checks, three mutations caught. In
assisted QEMU (`tools/probe_z7_trigger_probe.py`) the module loads, all three
wrappers install into the live slots and stay there while the guest runs, and no
callback fires in the idle emulated view. One run captured a complete, parseable
`Z7TRIG.DAT` written by the worker through Nikon's file functions; the emulated
worker is slow, so other runs paused before that first write finished.
The camera measurement is in [SHUTTER_TRIGGER_PROBE_TEST.md](SHUTTER_TRIGGER_PROBE_TEST.md).

### Step 3 groundwork: provisional still-file trigger (built, not for the camera yet)

`z7-native-modules/plugins/shutter_sound_trigger.h` holds the policy for the
still-file candidate; `shutter_sound_still_trigger.c` wires it to the playback
module (`tools/build_z7_shutter_sound.py --still-trigger`). On `0x041E0002` it
reads the packet's record and keys on slot, group and number (kind ignored), so a
JPEG+NEF pair sounds once. It plays only in Silent photography, remembers the
last 8 records, skips a frame while a sound is still playing, and always calls
Nikon's handler with the same arguments. Offline audit
(`tools/audit_z7_still_trigger.py`): 20 checks through Nikon's sound service;
two mutations (key mask, silent gate) are caught. It stays off the camera until
the trigger probe shows this event is once per photo and absent in live view.
If the probe picks a different event, only the policy's event and key change.


## Plan

1. **Playback module** and 2. **event counter**: both built and verified offline,
   combined into one field-test module (`shutter_sound_field_test.c`): chime on
   worker tick 8 plus the trigger log, with sound counters in the log header.
   One camera session: [SHUTTER_SOUND_FIELD_TEST.md](SHUTTER_SOUND_FIELD_TEST.md).
   The same module also carries the upside-down photo EXIF fix
   ([EXIF_ORIENTATION_RESEARCH.md](EXIF_ORIENTATION_RESEARCH.md)) so the session
   measures it too.
   Staging waits for the owner's approval.
3. **Trigger:** wire playback to the signal the counts support (still-file policy
   built provisionally, above); Silent photography ON, photo mode only, no
   retrigger while playing; then a menu for clip, volume and Preview.

Credit: design follows JKWTCN's MIT shutter-sound implementation; original-Z7
bindings are independent work.
