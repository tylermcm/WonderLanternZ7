# Exclusive-free settings publication - November 22, 2026

Additional gate: the later LCD grid review found the generic full profile still
passes extended layout IDs to the native grid property. Only the new storage-free
revision currently opts into the RAM-layout/native-bool policy. The persistent
candidate below remains unapproved until its grid storage contract is resolved;
the publication tests alone do not clear that separate behavior.

Offline implementation/regression checkpoint, not a camera candidate clearance.
The working host/card were unchanged while the owner was away. Hardware progress
and read-only I/O gates remain ahead of any settings-write or full LCD trial.

## Changes and ownership

The full persistence policy had two fetch-add operations on its revision word.
They are replaced with an ordinary aligned atomic revision load, odd store,
ordering fence, payload stores, and final even release store. The writer is
the existing GUI menu path, or loader initialization before GUI publication;
the worker only reads bounded snapshots. An already odd revision refuses a
nested commit. This is not a lock for concurrent writers.

The fence after publishing odd prevents payload publication from preceding the
in-progress marker; final release publishes the completed revision. The worker
still attempts at most three snapshots and returns if the writer is in progress.
It does not spin until the writer resumes. The settings model, v1 journal, paths,
debounce/retry policy and serialized bytes are unchanged. Existing wraparound
semantics are retained; this is not a new persistence format or durability claim.

The [GCC atomic built-in documentation](https://gcc.gnu.org/onlinedocs/gcc/_005f_005fatomic-Builtins.html)
defines the requested load/store/fence orders; the actual ARM build was separately
checked for emitted instructions. [Linux sequence-counter documentation](https://docs.kernel.org/locking/seqlock.html)
explains the even/odd consistency pattern and the need to serialize writers.
Our bounded reader avoids an indefinite retry while a GUI writer is preempted;
the explicit single-writer assumption still requires native lifecycle validation.
These references do not validate Nikon scheduling or physical memory attributes.

## Exact private builds and results

| Build | Bytes | SHA-256 |
| --- | ---: | --- |
| Persistence diagnostic | 24,048 | b4f4be274e4249587bacf5a252b9508e7ed7ff0ab30123275325c29db903161d |
| LCD candidate | 21,104 | 3e8854834417bb29e0b4ea9ea3c5a7be5b37fcb941826e1099adc43be3f5d954 |

Both built reproducibly and were independently rebuilt for exact ELF-function
scans. All 91 diagnostic functions and 83 LCD functions contain zero exclusive
instructions. Each retains 19 DMB instructions across its functions; ordering
was not removed along with read/modify/write operations. Called native firmware
functions are outside these scans.

- 84 full persistence checks pass: real compiled menu edits, journal/file
  wrappers, missing/read/close/write faults, dirty/retry states, worker saving,
  restart, and menu preemption during snapshot and write paths.
- A new targeted test pauses the actual GUI writer immediately after its odd
  store, runs four worker reads on a separate emulated stack, verifies no I/O or
  busy wait, resumes the writer with ABI preserved, then verifies the complete
  even revision is saved. Observed revision stores are exactly1 then2, with the
  payload between them.
- 48 LCD scope checks pass: compact menu/defaults, legacy filtering, supported
  battery/focal switches/reset, save/restart and native DISP/page/context behavior.
- 101 root tests pass, including optional ELF function-bound export checks.

Current source-fingerprint builds are `.private/builds/20261122-persistence-no-rmw-02`
and `.private/builds/20261122-lcd-no-rmw-02`. They match the already-tested `-01`
packets byte-for-byte after adding the optional volatile profile. Persistence
evidence and function scans use the identical packet hashes from `-01`; the LCD
audit was rerun as `20261122-lcd-no-rmw-02.json`. Evidence is under `.private/evidence/`
with those prefixes plus `20261122-persistence-writer-preemption-01.json`.

The explicit emulator interleavings do not establish physical ordering,
filesystem durability, shutdown flushing, native menu lifecycle, output/capture
safety or recovery. Remaining RMW sites in deferred highlight/cache/portrait and
advanced host profiles were inventoried but not mechanically rewritten: they
have different ownership contracts and remain outside this LCD hardware trial.
No settings write or full LCD activation is authorized by this offline work.
