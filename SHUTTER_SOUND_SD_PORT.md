# Silent shutter sound as an SD module — original-Z7 binding map

Status: **playback module built and verified offline, November 24, 2026.** It has
not run on a camera, has no photo trigger and no menu yet. Nothing is staged.

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
plus one preview queued at module init). Built by
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

**Offline audit** (`tools/audit_z7_shutter_sound_playback.py`, 74 checks, all
pass). It runs the original host loader, the compiled module, and Nikon's post
function, message dispatcher and completion in Unicorn. It stubs the filesystem
dispatcher, allocator, mailbox send, speaker checks, the four setters and the
native start handler; it records their arguments but doesn't execute them. Covered:
WAV decode edge cases, install and no-install paths, firmware-mismatch refusal,
setter order and arguments, native passthrough, every rejection path releasing the
job, busy and allocation failure. A mutation test (tone 31→30) fails as expected.

**Assisted QEMU, real guest tasks** (`tools/probe_z7_shutter_sound.py`):

| Run | Result |
| --- | --- |
| Install-only module + WAV | WAV read through the file fixture, slot holds the module handler, nothing queued, no private start in 4 s of running (6/6) |
| Same module, no WAV | Nothing installed, slot keeps `0x1006BC47` (3/3) |

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
It needs a camera measurement, which an SD module can do safely: count candidate
events without playing sound or writing files, and show the counts.

## Plan

1. **Playback module:** built and verified offline (above). Next is a camera smoke
   test of the boot-preview build: one clip at power-on, then normal camera use.
   This needs the owner's approval and swaps the module file on the card.
2. **Event counter (camera, no sound):** count trigger candidates per photo, single
   and burst, and in idle live view, half-press, menus and playback.
3. **Trigger:** wire playback to the signal the counts support; Silent photography
   ON, photo mode only, no retrigger while playing; menu for clip, volume, Preview.

Credit: design follows JKWTCN's MIT shutter-sound implementation; original-Z7
bindings are independent work.
