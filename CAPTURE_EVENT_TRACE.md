# Native Z7 sound-trigger trace — October 22, 2026

Follow-up [STILL_FILE_TRACE.md](STILL_FILE_TRACE.md) identifies a record-bearing
still-file notification and native record comparison as a backward-tracing
anchor. Its 14 checks do not establish per-photo timing/cardinality or clear a
replacement hook.

The owner asked to continue tracing the bug after confirming that Enabled OFF
stops the live-view audio loop. This investigation executes more original Z7 code
and identifies two insufficient trigger candidates. It does not produce a fixed
firmware image or clear another installation. Keep Enabled OFF; the
[port audit hold](PORT_AUDIT.md) remains open.

## Current hook loses Nikon's classification result

The original initialization at `0x10147BBE` registers callback `0x1014708D` via
`0x100752DE`, which writes the controller object's callback slot at
`0xA18D1B98 + 0x44` when empty. The dispatcher at `0x100725A0` receives
`0x041F0001`, copies three input words into a zero-filled stack packet and calls
that registered consumer with event `0x04190001` on its normal path.

The original consumer at `0x1014708C` does not unconditionally schedule the same
work for this notification. Its path reads classification bytes at
`0xA18B7B90 + 0x1A` and `+0x1F`, plus other context:

| Supplied +0x1A | Supplied +0x1F | Original consumer scheduling in this fixture | Existing patch audio requests |
| --- | --- | --- | --- |
| 0 | 0 | Worker `0x10146233`, 16-byte copied packet | 1 |
| 1 | 0 | None | 1 |
| 3 | 0 | None | 1 |
| 0 | 2 | Worker `0x1014644B`, no packet | 1 |
| 1 | 2 | Worker `0x1014644B`, no packet | 1 |
| 3 | 2 | Worker `0x1014644B`, no packet | 1 |

These numeric scenarios are controlled RAM inputs, **not identified real idle,
photo or movie states**. In particular +0x1A overlaps the word accessed at +0x18;
its ownership/packed representation and runtime transitions require further work.
Reading that byte as a new custom gate would repeat the earlier semantic mistake.

The existing custom veneer at `0x100726A8` preserves the native callback, but calls
the audio trigger afterward solely because event `0x04190001` was delivered.
It has no independent photo transaction or native admission outcome. Thus the
two native no-scheduling cases still queue audio. This strengthens the earlier
[retrigger reproduction](LIVEVIEW_SOUND_REGRESSION.md): the callback body is now
executed rather than replaced by a return stub. The owner report, rather than
these synthetic states, establishes that background live view can cause playback
on the camera.

Repeated notifications can start new requests after idle or set PENDING while
busy. The compiled completion handler can then schedule a restart. The earlier
audit reproduces the Capture audio busy heading and verifies compiled OFF clears
pending/new admission; the owner independently confirms OFF stops the loop.

## The release-request completion is also insufficient

The stock AutoOperation code at `0x10521060` calls `0x10203D40`. Its error path
references Nikon's `CCaptureStateControlService_ExecuteAutoRelease` diagnostic.
This API registers notification `0x34` and schedules worker `0x10202A79` with a
12-byte request. That worker branches to `0x102029BC`.

With controlled validation helpers and a zero-count request, executing the original
API and worker produces event `0x04100034` with two zero result words, without
calling release-control entry `0x10061FAA`. Consequently, request acceptance or
this notification alone cannot establish that an individual exposure happened.
This is not a complete model of AutoRelease, nor a claim about all physical
shutter paths or failure codes.

The nonzero branch is statically traced through request-context setup
`0x10203F2C`, release-control admission `0x10061FAA` and timer scheduling. A direct
branch-encoding scan found other call candidates for `0x10061FAA`; those still
need caller-context review. No new hook is proposed on that entry: it is a
request/control boundary and burst/cancellation behavior remains unresolved.

## Reproducible evidence and boundaries

Run against the existing private build, without building firmware:

```powershell
.\.venv\Scripts\python.exe tools/trace_sound_native_callback.py `
  --stock .private/builds/20261021-silent-property-01/stock-main.bin `
  --image .private/builds/20261021-silent-property-01/full.main.bin `
  --report .private/builds/20261021-silent-property-01/full.json `
  --output .private/research/shutter-trigger/native-consumer-trace-20261022.json
```

All **24 evidence checks pass**: stock fingerprint, registration/setter derivation,
six stock-versus-patched consumer scenarios, native scheduling preservation,
unconditional custom admission, the two no-scheduling counterexamples and the
zero-count release-request probe. Passing means the traced defect is reproduced;
`candidate_cleared` is explicitly false. Public summary:
`evidence/20261022-native-capture-trace.json`. Raw disassembly stays private.

The original dispatcher, callback consumer, callback setter, property getter,
release request API and selected worker path execute in Unicorn. Notification
packets, classification RAM, allocator, worker/audio scheduling, synchronization,
controller helper/semaphore and selected release validation/context helpers remain
controlled. Scheduled native workers are recorded, not asynchronously executed.
There is no real sensor exposure, hardware event trace, measured cadence/timing,
concurrency proof, installation acceptance or recovery evidence here.

The next unresolved boundary is a per-photo exposure/image-record signal, with
independent native derivation separating it from preview frames, half press,
request acceptance, cancellation and burst grouping. Candidate record-allocation
paths are under investigation; their photo-specific semantics are not established.
No firmware source was changed and no image was rebuilt, staged or flashed in
this trace. The existing EG/MAIN hashes remain unchanged.

## Stock live-view observation, reviewed October 24

A private harness booted the hash-checked original Z7 MAIN in the existing
assisted emulator and observed three distinct controller `0x041F0001` deliveries
becoming consumer `0x04190001` callbacks without supplying a shutter action.
The controller mode register was 0 and the capture-service state byte at
`0xA18B7B90 + 1` was 9 in all three observations. Distinct packet timestamps and
stepping past each breakpoint before rearming distinguish deliveries from a
repeated stop at the same instruction. The callback was the original registered
consumer `0x1014708D`.

This supports rejection of `0x04190001` alone as a photo signal. It does not
establish a replacement state gate: mode 0 or state 9 has not been compared with
independently verified successful exposures. The assisted model reported 24 RAW
batches and 18 ISP batches, but processed-buffer scanout was false. The harness
skipped a display-settling wait and makes no display-ready or sensor-accuracy
claim. Existing startup/calibration assistance remained explicit.

A separate stock capture-request run timed out before recording an action.
Native inhibits were not bypassed and sensor completions were not fabricated;
that unsuccessful probe supplies no positive capture evidence. Both runs used
isolated local guests, with no camera or card access. Public observations are
limited to `evidence/20261024-stock-liveview-observation.json`; raw packets, RAM,
disassembly and harness logs remain private. No firmware candidate is cleared.
