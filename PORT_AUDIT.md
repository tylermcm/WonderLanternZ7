# Port review hold — October 21, 2026

**Latest camera failure:** the owner reports repeated audio during live view and
Capture audio busy in the menu. [LIVEVIEW_SOUND_REGRESSION.md](LIVEVIEW_SOUND_REGRESSION.md)
records the incorrect photo-specific event assumption and an audit-only probe
against the existing binary. Two notification-only rejection checks fail. Enabled
OFF now stops the loop by owner confirmation. Leave it OFF; this does not clear
the trigger failure or any further flash.

**October 22 trace:** [CAPTURE_EVENT_TRACE.md](CAPTURE_EVENT_TRACE.md) now executes
the original registered callback and exposes native no-scheduling cases that
still cause custom audio admission. It also rejects AutoRelease completion alone
as per-photo evidence using the original zero-count request/worker path. All 24
evidence checks pass; no replacement trigger or firmware candidate is cleared.

The owner raised a specific concern that copied assumptions from another camera
could leave the Z7 unusable. Further flash recommendations and candidate staging
are on hold while the port evidence is reviewed. This is an initial audit and
gap register, not a completed safety assessment. No firmware or card content was
changed during this review. Do not interpret this hold as an instruction to
interrupt an update already running.

The most recently staged candidate is the full silent-property build, SHA-256
`9e636d645281ee9f92cb150b6dcc8d771b21ff95c47e45f538d951a1d932420b`.
It remains a private experimental artifact. Installation is inferred from the
owner's latest test sequence, without readback. It is not cleared for a further hardware
installation by this audit.

## What was actually composed

The laptop builder explicitly selects `model='z7'`, verifies the exact original
Z7 C 3.80 stock fingerprint and uses the Z7 platform's address mapping. It adds
the histogram/level, extended-M and Z7 sound-port patches. The sound builder
selects `shutter_sound_z7`, whose custom routines were adapted from Z30 source.
That Z7 base and exact-byte checks do not establish that the port's interfaces
or copied identifiers are correct.

The port has already exposed multiple bad assumptions: the audio busy-state
address, the exclusive audio-kind bound, a hook window with an interior native
branch target, and the Silent photography property ID. The last was masked by a
test that returned values for the same copied key. Tests now execute the real
native property lookup and Silent photography menu constructor, but other tests
still use controlled interface boundaries. Correcting the known issues does not
close the remaining audit.

The current source inventory finds 23 distinct direct literal native call
targets in the Z7 sound-generation sources and 17 edits in the full candidate.
Dynamic callbacks and addresses inside assembly strings are outside that count.
The legacy `NATIVE`/`GLOBALS` translation dictionaries are not referenced by the
generated-routine sources; actual literals and generated output must be audited,
not only those dictionaries. See
`evidence/20261021-port-audit-inventory.json` for source references, without raw
firmware bytes.

## Evidence and remaining gaps

| Area | Existing evidence | Required before clearing another candidate |
| --- | --- | --- |
| Base/model/version | Exact Z7 stock fingerprint, model selection, bounds and CRC checks | Retain these checks; do not treat them as behavioral proof |
| Silent property | Original Z7 menu constructor and real getter/tables; deliberately conflicting old/new properties | Record this native derivation in the interface register; hardware cue still unverified |
| Audio busy/type/config/data | Native metadata/getter/bounds and selected consumer instructions; owned-callback guards and stock fallback comparisons | Validate remaining driver/DSP contracts, ownership and completion behavior |
| Capture hooks | Three callback paths and dispatcher states tested; owner reports unwanted live-view repetition; offline notifications alone queue/restart audio | Establish independent photo transaction semantics and reject no-photo live view, half press and menu events; review timing/reentrancy, single/burst, exceptions and cancellation |
| Other hook windows and veneers | Stock windows, selected callback/stack/flag comparisons; zero-byte cave assertions | Audit inbound branches/aliases and displaced effects for every hook; establish why cave ranges are unused, beyond their contents |
| Allocation and buffers | Owned allocation bounds, WAV/conversion checks and controlled allocator/memory helpers | Independently identify native API contracts, alignment, cross-task ownership and all failure/cleanup paths |
| File I/O | Native addresses and return conventions ported; owner reports WAV loading/playback | Audit open/read/close structures, descriptor ownership, card removal and error cleanup independently |
| UI/state anchor | Native page metadata and cleanup comparisons; assisted menu tests | Verify anchor lifetime and repeated page entry/exit and allocation failure without relying on unused-slot assumptions alone |
| Histogram/level and M900 | Model-specific sites, stock masks/prologues and offline checks; M900 still shares key 0x11A3 with Z30 | Independently substantiate each Z7 state/property meaning; separate tested behavior from copied semantic assumptions |
| Installation/recovery | Owner-reported earlier installs and operation; preserved stock/prior files | No verified emergency recovery exists; do not describe those files or CRC checks as recovery assurance |

Before resuming installation recommendations, each used native interface needs
an evidence reference, calling convention, structure/enum meaning, ownership and
failure behavior. Tests must be able to reject the wrong-model assumption using
independent Z7 evidence, not just agree with the generated patch. Any controlled
boundary must remain explicit. Expand the inventory to assembly-embedded and
dynamic targets, and review the entire full preset rather than sound alone.

This review must produce a concrete installation/recovery assessment with its
remaining limitations for the owner to review. No finite set of emulator results
should be presented as a guarantee against an unusable body. No automatic stock
reflash or other recovery experiment is proposed.
