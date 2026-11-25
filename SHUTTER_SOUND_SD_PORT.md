# Silent shutter sound as an SD module — original-Z7 binding map

Status: **research checkpoint, November 24, 2026.** No module, hook or card file
exists yet. Nothing here has run on a camera.

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
the code references; they do not execute it. The playback audit in step 1 below is
where the native dispatcher and setters will actually run.

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

1. **Playback module:** load `SHUTTER1..5.WAV` from the card at boot, queue a job
   with event `0x0418001E`, intercept only that job in slot `0xA188D278`, program
   PCM with the setters above, and leave all native requests on the original
   handler. Offline audit executes the native dispatcher, setters and completion.
2. **Event counter (camera, no sound):** count trigger candidates per photo, single
   and burst, and in idle live view, half-press, menus and playback.
3. **Trigger:** wire playback to the signal the counts support; Silent photography
   ON, photo mode only, no retrigger while playing; menu for clip, volume, Preview.

Credit: design follows JKWTCN's MIT shutter-sound implementation; original-Z7
bindings are independent work.
