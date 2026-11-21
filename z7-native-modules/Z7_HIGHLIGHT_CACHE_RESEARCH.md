# Original-Z7 highlight request cache

Independent research for the unfinished automatic LCD/EVF highlight handoff.
No producer hook or new firmware/module profile is installed by this work.
Keep stock MAIN and generated evidence private. Source audit: MIT.

## Native paths

The original native getter at `0x10434CEE` returns a pointer to a 36-byte request.
For its supported use, R0 is output1,2,4; R1 is kind0. It calls the bank helper
at `0x10433B80` and adds `0x58` to the returned block pointer. Nonzero kind returns
zero. Output0 with kind0 returns `0x58`, so this is not a validating API for
arbitrary callers.

The helper reads the byte at `0xA180F274 + output`, multiplies that bank index by
`0xE84` and adds `0xA1F18FC0`. These constants are checked against the native
literal pool. The audit supplies bank indices0,1,2; it does not prove the physical
bank count, native index writers, allocation bounds or lifetime. Different output
indices can select the same bank. Changing an index changes subsequent getter
results; retaining the old pointer across transitions is unjustified.

The writer at `0x104348E4` accepts an output bitmask in R0, kind0 in R1, a request
pointer in R2 and a submission flag in R3. With submission disabled, its native
memcpy writes exactly36 bytes at each selected bank's `+0x58`. An enabled request
also clears the word at `+0x40` in that bank. A disabled request preserves that
word. Other bank bytes remain unchanged. Output bits1,2,4 are handled separately;
all masks0..7 and enabled/disabled requests are exercised. Nonzero kind does not
modify the cache. Mutex/queue submission boundaries are asserted unreachable in
this update-only audit; no native writer or memcpy instruction is replaced.

Nearby native submission paths call getter10434CEE then caller1034FF1E, including
the output4 path around103518EC..10351900. This makes the cache a candidate
baseline source, not an established coherent baseline API.

## Counterexample to equal double reads

The audit starts the actual native writer on a separate supplied stack. It pauses
after16 of the36 request bytes have been stored, preserves that task's register
context, and executes the original getter on the reader stack. Two identical
36-byte reads contain a mixture of the old and new requests. Both differ from
the complete old and complete new records. Resuming the writer in its saved ARM
instruction state finishes the copy and preserves stack/callee-save guards.

Therefore equality of two reads is insufficient to establish request coherence.
A preempted writer can remain stopped across both reads. Pointer/index rechecks
alone do not solve this partial-copy case. The update-only path also demonstrates
that the cache can change without submitting a display-parameter packet.

## Validation and next implementation

`tools/audit_z7_highlight_native_cache.py` passes60 checks against the exact private
original-Z7 C3.80 MAIN. Native bank arithmetic, getter, writer and memcpy execute.
Bank indices, incoming requests, palette memory and task scheduling are supplied.
This does not establish all direct/indirect writers, task ownership, physical
memory lifetime, output pixels or installation/recovery.

Before using this cache for automatic handoff, identify all writers and bank
index transitions, then provide writer exclusion or a publication protocol that
covers the complete write. Preserve the distinction between genuine native
per-output requests and the currently shared module-owned100-byte parameter
block. Do not move native synchronous queue waits into consumer callbacks.
The native-update-driven EVF profile remains unchanged while this binding is
unfinished; it continues to wait for matching native updates.

## Compiled write observation core

`plugins/cache_observation.h` supplies a12-byte active/serial/halted record. Every
covered complete write increments active and serial before the write, then serial
and decrements active after it. Counts support overlapping writers; serial parity
alone is not used for admission. A reader obtains a ticket, performs its copy,
then checks that serial still matches and active is zero. Three-attempt bounded
CAS operations halt observation on exhaustion/contention failure instead of
recycling identities. Invalid/unbalanced retirements halt observation. Halting
observation does not block the original native writer; integration must stop or
drain owned features that require trustworthy snapshots.

The core does not perform the payload copy, exclude writers, pin pointers or make
later parameter application atomic. All relevant writers and bank/index changes
must participate. Caller owns aligned observation state and a separate exclusive
ticket output; native payload reads need the appropriate volatile/order contract.
State initialization/activation must precede all writes relevant to an admitted
snapshot. A writer that began before observation activation is not covered merely
by reading an idle counter afterward.

The constructor at10433C78 also writes the request via memcpy10433CEE. Normal
writer copy sites are10434910/1043494A/1043497E. These are candidates for native
bridges, not an exhaustive writer inventory. Constructor header and neighboring
fields are written separately; the current test brackets only request-copy spans.

`tools/audit_z7_cache_observation.py` compiles a reproducible576-byte flat probe
and passes48 checks. Real setter and constructor copies at LCD/EVF logical outputs
pause after16 bytes: raw equal reads are torn and compiled observation rejects
both current and stale tickets. Native completion preserves original guards and
admits a new ticket. Overlapping writers, balanced/invalid retirements, counter
exhaustion and continued native writes after observation halt are checked.
Probe execution includes compiled atomic instructions; begin/end boundaries and
task scheduling remain supplied by the test. There are no installed firmware
bridges, module-host loader checks, physical lifetime or automatic handoff claims.

## Experimental native-copy host and API80

The opt-in host flag `--native-cache-copy-hooks` requires the full API72 warning
transaction profile. Its API80 prefix appends two functions: capture a44-byte
snapshot (36-byte request, serial and bank), and validate that snapshot's serial
and bank. Output1/LCD and output4/EVF are supported. Callers retain snapshots
unchanged; validation checks identity/generation rather than authenticating the
payload bytes. It does not exclude a writer that starts after validation.

Four native copy sites are patched: constructor10433CEE and setter10434910,
1043494A,1043497E. Each bridge preserves original registers/flags around helper
calls, executes the actual ARM memcpy, retires observation and reconstructs the
displaced load/conditional branch. Unaligned sites need ten-byte jump windows;
constructor also reconstructs a second load, HDMI/EVF the peaking-clear store.
The aligned LCD site uses eight bytes. Native copy and original post-copy effects
run even when observation is unavailable, halted or state guards are invalid.

Cold host state grows from336 to360 bytes, within the same384-byte reservation.
Observation active/serial/halted occupy336/340/344; completed-bank ready bits348;
guards352/356. The224-byte cold bridge slot initializes them before publishing magic.
Only tracked complete kind0 copies set ready bits. Unobserved initial cache bytes
are not accepted as baselines. Snapshot captures a ticket, calls the native getter,
copies volatile words into a local record, validates, then publishes the output.
Failure leaves caller output unchanged. Fixed native indices0/LCD and2/EVF are
required; unexpected mappings fail. Global generation conservatively invalidates
snapshots even after a write to another bank.

The loaded SDK probe and installed bridges pass97 checks. All24 mask/pattern
combinations match original full-bank bytes, return, flags andr1/r2/r3/r12
effects. Native constructor paths, tracked readiness, stale/tampered metadata,
partial and overlapping copies, a writer completing during snapshot capture,
exhaustion, native fallback on halt/bad guards and actual cold reservation execute.
Input request buffers remain caller-owned and immutable until native copy return.
The write observer is restricted to cache addresses; loader/filesystem execution
retains the ordinary HostFixture path. SDK probe is independently loaded by the
host; it is not a full display-feature module.

These hooks establish the four scoped copy spans. They do not prove all writers,
index ABA exclusion, physical bank lifetime, native initialization ordering before
cold activation or atomic later parameter application. In particular, a write
started before cold state initialization cannot be assumed covered by idle
counters afterward. Close that ordering before using this as an automatic
handoff baseline source. Earlier API72 host bytes remain identical with the new
flag disabled. No camera/card/update/recovery clearance follows.

## Display-module snapshot consumer

The API80 `display-highlight-handoff-probe` now consumes snapshots for logical
LCD/EVF baseline acquisition. Two312-byte bounded native-origin publications
retain context, baseline, optional raw cache binding and whether the baseline
came from an exact foreign native packet. Lease records append these fields only
under `Z7_HIGHLIGHT_HANDOFF_PROBE`; the old baseline/parameter prefix is preserved.
Native consumer callbacks are their sole writer; GUI/worker code does not convert
or program the native gate. Worker work remains resident asynchronous requests.

Changed output ownership requires an acknowledged old-plane disable before new
application/restoration. A readable disabled lease and actual engine/state/register
checks precede retiring the old frame-policy record. Cache validity participates
in the frame permission decision, while the worker handles refresh, busy disable,
retry and restoration. Per-output native records survive updates on the other
output. Cache-derived colors follow palette changes; exact native packet baselines
are retained when the bound raw request is unchanged.

These mechanisms use the existing warning-parameter lane for module application,
while native cache writers remain observed rather than excluded. A writer can
start after validation; this is not an atomic cache-to-plane commit. A completed
tracked cache source is required for initial cache-driven ownership. Full native
startup/writer/index/allocation closure is still needed before claiming a complete
camera lifecycle or installation-ready release.

## Photo-mode source stamp

The paired handoff host also stamps whether each observed copy began and ended
with native property138D/MODE at0. Only such completions set photo-ready bits;
a movie/unknown-mode completion or a copy crossing a mode boundary clears that
bank's readiness. Snapshot and validation also require current mode0. This prevents
a request written in movie mode from becoming a photo baseline just because the
mode word later returns to0. A new complete photo-mode copy readmits the bank.
Tokens carry bank+1 in their low byte and the sampled photo-start flag in bit8.
State and SDK snapshot sizes remain360/44 bytes; API prefix remains80. This is a
correction within the experimental exact-pair contract, not compatibility clearance
for earlier API80 host binaries. Audit admission requires the photo-source flag.

The source stamp samples mode at copy boundaries; it is not a mode-transition
allocation pin or proof of all native producer contexts. Mode/index ABA, writes
before cold activation, indirect writers and lifetime still need closure. Five
additional native host checks cover current movie rejection, movie-copy readiness,
fresh-photo recovery and copies spanning each direction of the mode transition.
The functional handoff audit also exercises photo/movie/photo with movie-cache
writes, waiting, fresh-photo recovery and exact photo restoration without a foreign
display packet. Earlier mode-agnostic host04 is not the accepted handoff pairing.
