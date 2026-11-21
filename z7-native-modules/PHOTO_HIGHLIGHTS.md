# Original-Z7 photo-highlight port research

Independent original-Z7 C3.80 interface research. The feature design is informed
by the pinned MIT JKWTCN Z7II photo_zebra implementation. No foreign addresses
are installed, and no camera, card, firmware staging or flash is involved.

## Verified native transport

The original decoder at `102396E2` reads the command from request+10hex.
With byte `A180A568` set to selector0, command `42060007` normalizes to
(group0, operation6, selector0), while `42062007` is rejected. Selector1 accepts
`42062007` as (group0, operation6, selector1) and rejects `42060007`.
The physical LCD/EVF meaning of these selectors is not established by this test.

Native dispatcher `10239840` reads service state from `A1D68E54 + group`.
Its function table starts at `10629FC8`, with300-byte group stride,
60-byte state stride and4-byte operation stride. For group0/operation6,
states1 through4 select `1023E215` at these original table slots:
`1062A01C`, `1062A058`, `1062A094`, `1062A0D0`.
The audit executes the original decoder, table dispatch and handler for both
commands and all four supported incoming service states.

The handler at `1023E214` consumes a payload pointer at request+14hex and:

- Copies exactly100 bytes to `*A180A588 + 28hex`.
- Sets the state word at offset24hex to1.
- Sets the source acknowledgement word at offset100decimal to1.
- Calls original completion `102396C0(request, 0)` and returns1.

The source packet therefore needs at least104 accessible bytes. A standalone
100-byte scratch buffer is insufficient for this consumer. This agrees with
the pinned design using26-word request payload storage, but it does not prove
that the native parameter meanings or all other offsets match the Z7II.

Four payload cases exercise direct copying, acknowledgement, request identity,
and untouched surrounding bytes. Native decoder/output selection and eight
native state-dispatch cases bring the focused audit to37 passing checks.
Incoming request/state storage, initialized service-state bytes and completion
are supplied fixtures. Original memory copy and native decode/dispatch execute;
no actual display hardware or warning pixels are established.

Run from the root checkout with private inputs/outputs:

```powershell
.venv\Scripts\python.exe tools/audit_z7_display_parameters.py --stock-main .private/builds/20261021-silent-property-01/stock-main.bin --output .private/evidence/display-parameters-new.json
```

The input must match the existing exact C3.80 stock-main fingerprint. The output
must be a new path under `.private`. Firmware/disassembly stay private.
Source-only evidence: `evidence/20261120-display-parameters.json`.

## Verified request converter

Original `1034FE22` accepts `(destination, request, output_flags)` and converts
the36-byte GUI request to sparse fields in the100-byte display packet. The
request shape agrees with the pinned design: enabled word0; reserved bytes4/5;
two groups of four halfwords at6 and14; horizontal/vertical words24/28; pattern
bytes32/33. Addresses and native field behavior were bound on the original Z7.

The converter uses native enumeration-table accessors `10433B1E`, `10433B26`,
`10433B2E` and native palette getter `10435ACA(1,0)`. The latter reads its
pointer from `A1F18FAC`; it is not replaced by a supplied function in the audit.
Palette contents and their initialized pointer are supplied incoming state.
Two distinct palettes verify that converted color bytes follow native lookup.

For enabled requests the first halfword in each group scales by257, and the
threshold byte scales by256. Both groups are tested at255,248,235,224,213,202,
191,180. Pattern values0/1 map through the original enumeration table; the
existing design exposes these as enabled patterns1/2. Output flag1/2/4 encodes
native packet target byte0/1/2 respectively. Physical LCD/EVF/external mapping
and photo/movie eligibility still need caller/context proof.

**Disabled conversion writes only the enable word.** All other destination
bytes remain as supplied. Clear the complete owned100-byte conversion buffer
before use; do not publish uninitialized or stale padding. The consumer still
requires a104-byte source allocation because its acknowledgement is after the
100-byte payload. Enabled conversion also preserves unspecified padding.

The converter audit passes198 checks across99 cases: three output flags, two
enabled patterns, eight thresholds, two supplied palettes, and three disabled
cases. Each case checks exact destination/padding writes, input preservation,
and native palette-getter calls. No graphics submission or producer executes.

```powershell
.venv\Scripts\python.exe tools/audit_z7_highlight_converter.py --stock-main .private/builds/20261021-silent-property-01/stock-main.bin --output .private/evidence/highlight-converter-new.json
```

Original caller `1034FF1E` invokes this converter before the request builder
`1034EFB0` and graphics submission/completion path. Its blocking handoff is executed below; it is not an accepted asynchronous
extension interface.
Source-only evidence: `evidence/20261120-highlight-converter.json`.

## Verified original submission/completion handoff

Native builder `1034EFB0` case16 returns a caller-supplied request descriptor
(or uses a native static fallback, not exercised by this audit). It writes
callback/command/payload/context at offsets0C/10/14/18hex. Logical banks0/1/2
produce `42060007`, `42061007`, `42062007`. The third builder argument is not
used by this case. The audit passes six arguments using the original ARM caller
stack layout and checks that the argument words remain intact.

The original blocking caller `1034FF1E` maps output flags1/2/4 to banks0/1/2.
It converts into a100-byte local stack payload, constructs an adjacent descriptor,
clears its completion bit, queues the request through `10348494`, and waits.
The DisplayService branch executes `1023AAB2`, `101F243C`, and `10112446` before
entering the supplied kernel queue service. The separate bank1 `42061007` path
selects `103490F4`; that submission path is not exercised here.

For flags1/4, original callback functions `10354342`/`10354356` set bits20hex/
80hex on the native event object at `A1F1353C`. The original consumer dispatch,
100-byte copy, acknowledgement, completion `102396C0`, and those original
callback instructions execute. A supplied kernel event service records the bits.
The caller resumes through its original wait wrapper, returns1 and preserves
its original stack/callee-saved registers. The consumer uses a separate emulated
stack while the caller's CPU context and live stack payload remain preserved.
Both enabled and disabled requests are covered for both logical output paths.

**The original wait timeout is `FFFFFFFF`: it is unbounded.** Do not call this
wrapper from extension paint callbacks. An owned asynchronous packet path needs
separate task/lifetime/cancellation/backpressure proof. Successful modeled queue
send and event delivery do not establish kernel failure or physical scheduling
behavior. Native source acknowledgement overlaps the first word of the adjacent
stack descriptor in this original caller; the extension should retain explicit
104-byte payload storage rather than relying on that local stack adjacency.

The focused audit passes38 checks: three logical bank builders and four complete
caller/consumer handoffs with original completion callbacks. Kernel queue/event
services, initialized palette/service state and explicit scheduling are supplied.
No frame producer, graphics hardware or warning pixels execute.

```powershell
.venv\Scripts\python.exe tools/audit_z7_highlight_submission.py --stock-main .private/builds/20261021-silent-property-01/stock-main.bin --output .private/evidence/highlight-submission-new.json
```

Source-only evidence: `evidence/20261120-highlight-submission.json`.

## Original frame permission and deferred copy

The read-only `tools/audit_z7_highlight_frame_gate.py` audit executes original
source application `1034866E`, primary-frame application `1023B9D0`, warning
gate `1023B76E` and parameter transformation `1023B578`. All66 checks pass.
For the primary source kind0, the frame permission is the word at **frame+34hex**,
copied to native state+20hex. The global enable is state+28hex. Both must equal1
to enable the warning plane; permission2 inhibits it. Frame+28 is not this flag.

Selectors0/1 admit logical source outputs0/2. Incoming active service3/4 and
ready state+228 are supplied. Wrong output, not-ready, inactive service and
unsupported source cases do not publish permission or program the plane.
These logical paths do not establish physical LCD/EVF or photo/movie mapping.

In deferred mode, native code copies exactly4B8hex bytes to state+50Chex and
sets byte state+508hex. Restoring the caller's frame+34 does not undo this copy.
Forced native replay consumes the copied permission and can enable the plane.
Therefore a temporary caller-side flag override alone is insufficient cleanup;
the eventual extension must reconcile pending metadata and global parameters.
Clearing the outer lifecycle's pending-ready byte is not established here.

Incoming MMIO/frame/service/palette state, selected surface checks, kernel mutex
success, hardware color lookup and warning-plane programming are supplied.
Native parameter transformation executes, but actual hardware programming and
warning pixels do not. No foreign image+468 offset or producer hook is installed.
Source evidence: `evidence/20261120-highlight-frame-gate.json`.

## Resident asynchronous request owner prototype

`plugins/highlight_request.h` now supplies a single resident28-byte descriptor
and separate104-byte payload. It uses original converter1034FE22,
builder1034EFB0 and submit wrapper10348494 for logical flags1/4. All parameter
words and acknowledgement are cleared before conversion, including disabled
requests whose converter otherwise leaves96 bytes untouched. It does not call
the native infinite-wait wrapper1034FF1E. Kernel queue latency/blocking itself
remains unverified; this helper is intended for the resident worker.

The consumer bridge contract brackets original dispatch with an atomic claim
and retirement after native return. Context epochs are supplied by that bridge:
an owned stale request calls original completion102396C0 without publishing
parameters. Ordinary packet pointers return a delegate decision unchanged.
The owned completion callback alone cannot release storage. Reaping also waits
for the submitter to return, covering consumption before queue-send returns.
An acknowledgement distinguishes native100-byte application from cancellation.
Missing completion, unexpected owned descriptors and lost requests stay parked;
neither a timeout nor a queue error permits reuse. This intentionally lacks a
speculative retry that might overwrite a still-retained packet.

The compiled ARM probe passes59 checks with original native conversion, builder,
queue wrappers, dispatch, copy/ack and completion. Tests cover both logical
outputs, enabled/disabled requests, foreign packets, context cancellation,
duplicate/reentrant consumption, all four owned descriptor field corruptions,
wrong-command completion, missing completion, supplied queue success/error,
late consumption and consumption on a separate stack before submission returns.
Supplied queue errors do not prove physical kernel error ownership semantics.
Explicit test calls supply consumer bracketing and context epochs; no host hook,
coherent context producer, preference connection or warning pixels are claimed.
The accepted API44 full display module and host remain unchanged.

```powershell
.venv\Scripts\python.exe tools/audit_z7_highlight_request.py --stock-main .private/builds/20261021-silent-property-01/stock-main.bin --output .private/evidence/highlight-request-new
```

Source evidence: `evidence/20261120-highlight-request.json`.

## Optional API48 source and consumer host bridges

The explicit `--display-hooks --highlight-hooks` host build now installs
exact-byte-validated bridges at original source1034866E and consumer10239840.
Default builds retain API44 and no highlight patches. `sdk/highlight.h` adds
one initialization-only registration function after the44-byte worker prefix.
The descriptor must be an aligned28-byte range in loading module memory; all
four required callbacks must be Thumb code inside the module image. The host
copies the callback addresses, publishes them only after successful init, and
clears them before freeing a failed initializer. The fixed256-byte host state
uses the previously reserved seven words; guard offsets are unchanged.

Source callbacks bracket native application with an invocation-local token.
Native caller registers/flags are restored before the displaced instructions;
native result/volatile registers/flags are preserved across the after callback.
The original conditional branch in the10-byte source window is relocated
explicitly. Unregistered/invalid state delegates to native. Source reentry
delegates without another module callback, and temporary caller flag restoration
does not erase a deferred native copy. Production eligibility is still unbound.

Only the registered descriptor address reaches consumer callbacks. Every other
packet executes original native dispatch, even while an owned request is pending.
For owned requests,1 dispatches native,2 invokes original cancellation completion,
and other decisions park. Reentry during before/native processing parks without
calling completion a second time. After native returns, the host releases its
consumer claim BEFORE the module publishes retirement. Otherwise an immediate
worker reap/submit could dispatch while the old guard was still set and lose the
new request. The old owner state rejects duplicate consumption before retirement;
after retirement, old callback code must finish without further old-packet access.

`tools/audit_z7_highlight_host.py` passes77 checks on the compiled host/probe:
registration bounds/all required callback fields/duplicate/late/init-failure,
resident guards, source native fallback for both selectors/permissions and three
incoming flag patterns, no-op callback ABI, actual flag override/restoration and
deferred copy, owned dispatch/cancel/reap, recursion and foreign matching/rejected
native packets with exact results/registers/flags/publication. The immediate
retire/reap/submit/consume overlap test fails on private host02 and passes on
host03. This is explicit diagnostic interleaving, not physical scheduling proof.

The native hardware-config transformation leaves padding unwritten. Exact
unregistered hardware-config comparisons therefore supply the stock reference
with the same incoming scratch bytes captured at the native trampoline entry.
No screenshot/pixel normalization is involved. Registered no-op comparisons prove
result/volatile-register/flag ABI; they do not claim identical uninitialized stack
padding or physical warning-plane programming. Kernel/filesystem, initial native
state, selected surface checks and hardware color/plane services are supplied.

Private host03 SHA512f06c17c712b6a4503532098c4f521deef681b6839346a739d3151f361d02c
is reproducible with zero EG CRC. API44 default host and full persistent module
rebuild byte-identically to the accepted profiles; root71 tests pass/no skips.
The API48 probe's epoch/eligibility inputs remain diagnostic. Full preset/worker
integration, coherent photo/output policy, owned baseline restoration and actual
warning pixels are not implemented by these host hooks.

```powershell
.venv\Scripts\python.exe tools/build_z7_module_host.py --display-hooks --highlight-hooks --output .private/builds/highlight-host-new
.venv\Scripts\python.exe tools/audit_z7_highlight_host.py --build .private/builds/highlight-host-new --stock-main .private/builds/20261021-silent-property-01/stock-main.bin --output .private/evidence/highlight-host-new
```

Source evidence: `evidence/20261120-highlight-host.json`.

## Original output routing and property-backed mode

`tools/audit_z7_highlight_output.py` passes131 scoped native checks. Original
source selector103484DC maps logical output0 to the rear-monitor tag selector
1023CC7E and output2 to EVF selector1023CCF4. Original16-byte comparisons and
all five downstream pointer setters execute. A matching secondary source takes
priority over a matching primary source, including distinct addresses with
identical tags. An altered final tag byte does not match. Source selection
does not itself change active selector byteA180A568. A no-match clears the
selected state+8/+C pointer but leaves downstream receiver pointers stale.
The extension must use the primary selected pointer, not those mirrors.

Original getter103FEF80 reads output-kind wordA181C764. With this actual getter
executing, DISP selector103673AC chooses2F15/2F16 for mode0,2F17/2F18 for mode1;
kind1 selects the first key of each pair. Supplied kinds0..5 are covered without
equating every alternate kind to a physically attached EVF.

Native property138D lookup10070204 resolves index467hex to ROM descriptor
114D501C, type7/size4/backing wordA24E1E00. Original104065A4/101D53AE wrappers,
generic getter10070234 and ROM group lookup execute against supplied RAM values
0/1/2/FFFFFFFF. Getter returns are not faked, and this tested path uses direct
ROM/RAM reads rather than property locks or task waits. The original bulk-key
tableA1828E88 contains138D at index135decimal (offset21Chex). Real bulk wrapper
10376414 and1016FEFC loop copy a ONE-KEY slice intoA201F47C, preserving adjacent
bytes. This does not establish the whole270-key snapshot as atomic/current.

`plugins/highlight_context.h` now reads the property backing word, output kind,
active selector, native state/selected source, readiness and service state using
RAM only. It checks the selected source against the original rear/EVF tag,
collects and rereads the fields with at most three attempts, and commits its
caller-owned output only after a matching sample. Source/state pointer bounds,
nulls, alignment, selector and tag are checked before dependent reads. It never
uses stale downstream mirrors or the GUI's cached138D word. The caller still
must reject non-photo/ineligible mode/output/service and apply UI/preset policy;
the reader intentionally returns raw stable values, not an ownership decision.

`tools/audit_z7_highlight_context.py` passes28 compiled ARM/native-routing checks:
both sources, four mode values, invalid pointers/tag/selector, native no-match
with stale mirror, opposite live/cache modes, and explicit between-instruction
mode/output/selector/state/source/readiness/service changes. Continuous mode
changes stop after three attempts without partially publishing output. Late
Unicorn read/code hooks require invalidating the probe's cached translation
blocks; earlier diagnostic hooks had not run until this was corrected. The
final interleavings change RAM after a completed load, not inside that load.

Repeated values do not detect ABA, pin native source allocations or establish a
native transaction/frame fence. A module-owned shared epoch/settings publisher,
UI ownership policy, parameter baseline restoration and full profile connection
are still required. Physical output, warning pixels and transition timing are
not accepted by these supplied-RAM instruction checks. Existing host/full-module
bytes are unchanged by these isolated helpers/audits.

```powershell
.venv\Scripts\python.exe tools/audit_z7_highlight_output.py --stock-main .private/builds/20261021-silent-property-01/stock-main.bin --output .private/evidence/highlight-output-new.json
.venv\Scripts\python.exe tools/audit_z7_highlight_context.py --stock-main .private/builds/20261021-silent-property-01/stock-main.bin --output .private/evidence/highlight-context-new
```

Source evidence: `evidence/20261120-highlight-context.json`.

## Shared settings/context epoch in the persistent profile

The optional `display-highlight-context-probe` now composes the full persistent
focal/Other/histogram/information profile with API48 source observation and a
shared GUI publication. It is a development stage of the highlight port, not a
visible warning feature. No frame permission or native parameter writes occur.
The accepted API44 persistent profile still rebuilds byte-identically.

`plugins/highlight_epoch.h` publishes twelve words: seven native context fields,
settings revision, preset, wanted/eligible flags and native DISP cycle generation.
Only the GUI callback writes; source/worker readers make at most three attempts.
All shared payload words use atomic word accesses. A writer marks the sequence
odd before copying and publishes the new epoch/even sequence with release
ordering. Readers check both sequence and epoch after collecting the view, so a
repeated32-bit sequence value cannot pair an old epoch with a partially new view.
Unchanged GUI ticks keep the epoch stable. Epoch exhaustion parks publication
permanently for this boot rather than recycling an old queued identity.

The existing composed after-GUI callback publishes only after its focal,
histogram and information work. It uses the persistence layer's even-revision
settings snapshot and current native RAM context. Source/worker validation
rechecks live mode, output, source/readiness/service, settings revision, preset,
DISP generation and current UI ownership. The current full profile owns LCD DISP;
its EVF/movie/information/menu contexts remain delegated. This is not a replacement
for the remaining EVF port or broader native lifecycle acceptance.

The source callback returns an observation epoch and its after callback records
it without modifying the frame. The worker records the currently eligible epoch
then runs the existing persistence worker. The registered descriptor submits no
requests yet and its consumer callback parks. All four callbacks and the worker
are registered before startup settings I/O, with host readiness/menu publication
still delayed until successful init. API44 hosts reject before settings/menu I/O.
The Photo highlights switch now drives the wanted epoch bit, not warning pixels.

`tools/audit_z7_highlight_epoch.py` passes61 checks using compiled ARM publication
and the actual full-profile GUI/source/menu/DISP/worker callbacks. It tests every
view field, unchanged ticks, odd writer, sequence wrap, exhausted epochs, and a
reader paused after one payload load while the compiled GUI publisher runs on a
separate stack. Supplying a repeated sequence value forces epoch validation to
retry to one whole new view. Full-profile tests cover startup ordering, live
context invalidation before GUI republishing, actual menu checkbox revision,
four native DISP cycles back to the original preset and API44 early rejection.
The round trip cannot reuse its prior epoch because the native cycle generation
changed. Filesystem/UI/after-GUI delta synchronization, frame-apply boundary and
explicit task interleavings are supplied. No physical scheduling/fence is claimed.

Private context03 module SHA
`d429674d261aeea3685906ef166159691634724e489833312dc8fc0cb1470409`,
25412 file/25088 image/5740 BSS bytes, minimum API48, reproducible. Root71 tests
pass/no skips. Default persistent module remains SHA719c1db3ca5cf1c78d82ebedcdbbb4cc7b67312b34b7982d11a718e4b39af85c.
The existing full persistence/status audit passes84 checks on this exact context03
module/API48 host, including startup failures, menu edits, retry and save-state
handling. Its API40 legacy rejection uses host bundle20261120-display-host-08.
The persistence audit now validates its legacy-host bundle path before expensive
emulation; passing a module-only directory is rejected immediately.

```powershell
.venv\Scripts\python.exe tools/build_z7_display_module.py --variant display-highlight-context-probe --output .private/builds/highlight-context-profile-new
.venv\Scripts\python.exe tools/audit_z7_highlight_epoch.py --build .private/builds/20261120-highlight-host-03 --module .private/builds/highlight-context-profile-new --legacy-build .private/builds/20261120-highlight-compat-host-02 --stock-main .private/builds/20261021-silent-property-01/stock-main.bin --output .private/evidence/highlight-epoch-new
```

Source evidence: `evidence/20261120-highlight-epoch.json`.

## Native parameter payload path (API52)

The explicit host flags `--display-hooks --highlight-hooks --parameter-hooks`
add `sdk/parameters.h` after the API48 prefix. Init-only registration requires
the highlight hooks first and validates a resident Thumb callback. Failed init
clears the callback before freeing module memory. API44/API48 host and module
binaries remain byte-identical with the new extension disabled.

Before original consumer10239840 dispatch, the host recognizes only foreign
42060007/42062007 descriptors, matching active selector, service1..4, aligned
native RAM descriptor and104-byte source range, and enabled word0/1. Only photo
mode0/service3..4 exposes the writable100-byte payload. Other modes or phases1/2
produce a callback with NULL payload: an update notice, with no writable caller
memory exposed. Invalid/unrelated packets delegate without callback; the owned
registered descriptor stays on its existing separate consumer path. Reentry
delegates without another parameter callback. Every path still runs the original
native dispatcher; this interface cannot cancel or replace native completion.

The optional `display-highlight-parameters-probe` composes the full persistent
profile and its epoch with this callback. Eligible current LCD photo packets
are converted with original1034FE22 into a cleared100-byte temporary, then
copied into the caller's live converted payload before original dispatch. The
typed36-byte request has asserted field offsets and preserves the original
caller's36-byte GUI request. Current development defaults are pattern1 and
threshold248; style/threshold menu configuration remains open. Context/epoch and
palette pointer are checked again before writing. Descriptor/source/callback/
context and source acknowledgement are untouched by the callback. No caller
pointer is retained or restored after completion wakes its owner.

Every valid native update advances a separate monotonic generation and clears
the prepared epoch, including notices and ineligible packets left unchanged.
This detects native ownership changes even when native bytes equal the last
converted payload. Exhaustion parks conversion instead of recycling identity.
Owned requests will not advance this native generation. The recorded conversion
epoch is PREPARED, not proof of native application; ownership/restoration and
source flag enablement must still require actual copy/ack/current parameters.

API52 host state is272 bytes, retaining the256-byte prefix/guards and adding
callback/running/two guards. The workspace reservation is320 bytes. The original
allocator101E3DAC rounds sizes to64 but does not realign its cursor, so reserving
only272 would misalign every subsequent allocation. The corrected cold path
preserves native continuation registers/flags and tested guards/neighbors;
original allocator arithmetic returns64-aligned starts for sizes1/63/64/65.
Workspace lock operations are supplied in this allocator fixture.

`tools/audit_z7_parameters.py` passes59 checks on final host03/profile03:
registration/code bounds/prerequisite/duplicate/late/failed-init cleanup, cold
reservation/native allocator, both selectors/service3/4, descriptor/source guards,
read-only notices, ordinary packet filtering and reentry. The full-profile test
executes original blocking caller1034FF1E for BOTH originally disabled and enabled
requests, pausing at its actual infinite kernel wait. A separate consumer stack
runs the real hook/converter/dispatch/copy/ack/completion/native event callback.
The caller resumes with its original stack/callee registers and GUI request.
Descriptor changes are limited to the original source+100 acknowledgement that
overlaps descriptor word0; its callback/source/context remain unchanged. Mode,
menu, palette, odd settings and actual checkbox-Off preserve original payloads
and native completion. Same-byte native updates invalidate prior ownership.

Private final host03 MAIN SHA
`da7cfc45631e9545f7d8da6def184d2007496ef9ae2f26757b7b25df52c7e6f9`;
profile03 SHA`33a159a188e2a51dbbfadde2a5614073ba04ba25e9e0676dbdb851e8b5555f9e`,
25732file/25408image/5804BSS, minimum API52. Builds are reproducible/host EGCRCzero.
Root71 tests pass/no skips. Persistence84 and epoch61 regressions pass with this
exact module on host02. Final host03 has identical C runtime/symbols/all non-cold
bytes to host02; the ONLY changed MAIN byte is the separately tested cold cursor
reservation at11FA6C9A. The59-check audit verifies that equivalence explicitly.
This composes scoped evidence; it is not a claim of a new full camera boot.

Kernel queue/events, filesystem/UI, palette contents and task handoff are supplied.
Native event wrappers execute; the full-profile fixture's unrelated histogram
event model is bypassed only for this original highlight event object. Frame
permissions remain native. Owned submission/restoration, pending-frame cleanup,
EVF feature integration, warning pixels and physical lifecycle remain incomplete.

```powershell
.venv\Scripts\python.exe tools/build_z7_module_host.py --display-hooks --highlight-hooks --parameter-hooks --output .private/builds/parameter-host-new
.venv\Scripts\python.exe tools/build_z7_display_module.py --variant display-highlight-parameters-probe --output .private/builds/parameter-profile-new
.venv\Scripts\python.exe tools/audit_z7_parameters.py --build .private/builds/parameter-host-new --module .private/builds/parameter-profile-new --legacy-build .private/builds/20261120-highlight-host-03 --stock-main .private/builds/20261021-silent-property-01/stock-main.bin --output .private/evidence/parameters-new
```

Source evidence: `evidence/20261120-native-highlight-parameters.json`.

## Deferred owned-packet conversion

The resident request helper now offers `submit_deferred` and `convert_deferred`.
Submission clears and queues its separate104-byte payload without touching the
converter/palette. Only a current claimed consumer may fill its100 parameters
before original dispatch. Descriptor/callback/context integrity, epoch, state,
completion and acknowledgement are checked first. Consumed/completed payloads
cannot be converted again. Stale claims enter an explicit CANCELLING state;
passing their old epoch cannot revive conversion. Original cancellation completion
still retires them without a false application acknowledgement. The earlier
preconverted research entry remains compatible, but is not the intended worker path.

The focused owner audit now passes107 checks, retaining its previous59 lifetime
checks and adding deferred enabled/disabled requests for both logical outputs,
palette changes AFTER queueing, zero padding/ack, pre-claim/post-completion guards,
stale cancellation and attempted revival. Original conversion/native dispatch/
copy/ack/completion execute; kernel queue, palette state and explicit consumer
bracketing are supplied. This helper is not yet wired into the full profile's
worker/consumer, and does not implement parameter lease/restoration or frame gates.
Existing full profile/host bytes are unaffected; only isolated diagnostic users
currently include this header. Private final result:
`.private/evidence/20261120-highlight-request-deferred-02/result.json`.
Source evidence: `evidence/20261120-owned-highlight-deferred.json`.

## Owned parameter integration

`display-highlight-owned-probe` is a further opt-in API52 development profile.
It includes both eligible incoming native conversion and worker-submitted owned
requests. The worker publishes operation/context/native-generation metadata
before queueing a resident descriptor and a zero104-byte source. Only the claimed
consumer converts using the current palette. The original dispatcher copies100
bytes and acknowledges/completes before the lease is considered applied. The
request remains unavailable for reuse until both dispatch and submission return.

The lease records the native baseline, expected applied parameters, context,
settings epoch, palette and monotonic native generation. Off restores a baseline
only when the context, generation and current parameters still match. A mode or
output departure disables owned parameters while retaining the original baseline;
returning to its context can reapply or restore. Eligible incoming native updates
capture their original baseline before conversion. Every valid native update,
including an ineligible notice or same-byte update, invalidates the previous
lease. Pending old restore/disable requests therefore cannot overwrite newer
native settings merely because the bytes happen to match.

Disabled native input defines only its enable word. Its remaining96 bytes are
normalized to zero rather than treated as meaningful baseline fields. Enabled
baselines retain all100 bytes. Module publication uses bounded reads and a
monotonic serial; serial exhaustion parks instead of recycling ownership.

This policy assumes native parameter writers are serialized through the
DisplayService consumer lane. It does not establish a physical frame fence,
allocation lifetime, concurrent foreign-writer safety, or a native scheduling
guarantee. Source/frame permissions remain untouched. Worker cleanup alone is
insufficient for pending frame replay: immediate cleanup is required before
enabling the source flag override. No warning pixels or camera readiness are
claimed. Reproducible module SHA:
`f1f39562292a2cd5a112aa397862db4dd96ae417dfd5d1190ea4b3610ae42189`.

The final integration audit passes36 checks, including native baseline replacement,
same-byte invalidation, stale cleanup, early consumption on a separate stack,
menu changes before GUI publication, and logical LCD/EVF round-trip restoration.
The focused compiled lease audit passes9 checks; the request lifetime audit
passes107; persistence passes84 on these same host/module bytes; root tests pass71
with no skips. Kernel/filesystem/UI/palette inputs and explicit interleavings are
supplied. Source evidence: `evidence/20261120-owned-highlight-integration.json`.

```powershell
.venv\Scripts\python.exe tools/build_z7_display_module.py --variant display-highlight-owned-probe --output .private/builds/owned-profile-new
.venv\Scripts\python.exe tools/audit_z7_highlight_owned.py --build .private/builds/20261120-parameter-host-03 --module .private/builds/owned-profile-new --stock-main .private/builds/20261021-silent-property-01/stock-main.bin --output .private/evidence/owned-profile-new.json
.venv\Scripts\python.exe tools/audit_z7_highlight_lease.py --stock-main .private/builds/20261021-silent-property-01/stock-main.bin --output .private/evidence/lease-new
```

## Consumption-time primary frame permission API56

The optional `--frame-permission-hooks` host build adds
`sdk/frame_permission.h` with an init-only resident Thumb callback. It requires
the existing display/highlight/parameter host flags. The exact eight-byte window
at1023BAB0 in original primary-frame application1023B9D0 now calls a guarded
filter immediately before publishing state+20 and calling warning gate1023B76E.
Native instructions and the surrounding stack/register/NZCVQ contract are
preserved. The callback returns preserve/enable/inhibit; unsupported kinds,
nonboolean native permission, invalid frame ranges, missing/corrupt callback,
host guard failure and recursive entry delegate native behavior.

`display-highlight-frame-probe` composes the full owned/native parameter profile
with this callback. A matched settled lease with current context/epoch/palette
enables the consumed permission. Stale owned parameters inhibit it until
restoration or replacement. A busy/halted lease publication also inhibits because
ownership cannot be established; a halted publication requires restart. Native
behavior resumes once restoration relinquishes the lease. No caller frame flag
is overridden, so no module-enabled1 is copied into the deferred4B8 buffer.
Every primary forced replay reaches this filter and rechecks live settings/UI.
The native pending-ready byte and all stored frame metadata stay unchanged.

This addresses stale pending replay at its consumption boundary. It does not
provide asynchronous plane teardown in the absence of a native frame/gate call,
pin native allocations, or establish a physical frame fence. Native context/
parameter writer serialization remains an explicit precondition. Whole lifecycle
acceptance, successful hardware programming and actual warning pixels remain open.

Final private host: `20261120-frame-host-01`, API56/state288/reservation320,
MAIN `bbda6819e395fce90fa6f4a4f67d307ffddb8d1539c3ac0794274e5e12468968`.
Final reproducible profile: `20261120-display-highlight-frame-02`,
28612file/28288image/6484BSS bytes,
SHA `3536d86c7adac1ab21b5fa63662ec2322a5fb7c39819cffa30f757653c40d476`.
The original API52 host and owned profile rebuild byte-identically with the new
option disabled. The final45-check audit executes native source, primary apply,
deferred copy/replay and warning gate instructions. It covers cold reservation/
guards/allocator, registration/reentry/cleanup, live bridge registers/NZCVQ,
active application, Off before GUI/worker, native baseline restoration, menu/
movie/output/preset/palette changes, unreadable leases, and API52 rejection.
Kernel/FS/UI/context/surface/color and warning-plane programming remain supplied.

```powershell
.venv\Scripts\python.exe tools/build_z7_module_host.py --display-hooks --highlight-hooks --parameter-hooks --frame-permission-hooks --output .private/builds/frame-host-new
.venv\Scripts\python.exe tools/build_z7_display_module.py --variant display-highlight-frame-probe --output .private/builds/frame-profile-new
.venv\Scripts\python.exe tools/audit_z7_frame_permission.py --build .private/builds/frame-host-new --module .private/builds/frame-profile-new --legacy-build .private/builds/20261120-parameter-host-03 --stock-main .private/builds/20261021-silent-property-01/stock-main.bin --output .private/evidence/frame-permission-new
```

## Native warning-plane registers and no-frame control

`tools/audit_z7_highlight_plane.py` now executes original driver10241A0E,
validator10258EF8 and readback10241C2E below the API56 gate. The prior plane
programming sink is bypassed; real native instructions write emulated MMIO.
All24 checks pass on the unchanged final API56 host/profile pair above.
Both supplied engine-bank offsets0/4000 are checked; these supplied descriptors
do not establish a physical LCD/EVF mapping or live native engine allocation.

The default full-profile converter/consumer/source/gate path reaches the real
driver, and its transformed60-byte configuration passes native validation.
Selected mode/threshold/color/control fields match the actual register values;
native readback observes the programmed enable/mode. Deferred source storage
remains native, and Off before GUI/worker inhibits forced replay down to the
actual register enable bit. MMIO storage, surface checks, hardware color values,
kernel/FS/UI/context and task scheduling are supplied. This does not execute ISP
image processing or prove warning pixels/physical register application.

Calling original gate1023B76E with permission0 and an active plane, without any
source/frame call, invokes the real driver disable path. It clears only bit0
of engine-bank register+430, preserves every other register/bank bit, and clears
the native active flag. Repeated disabled calls perform no driver writes.
This is a verified no-frame teardown primitive, not yet connected module cleanup.

Two important admission limits are now explicit. Format4 returns success while
bypassing teardown. Also the driver returns its ordinary status0 when native
configuration validation rejects an input, without programming any registers.
The upper gate can consequently return1 and mark active1/dirty0 while the actual
register remains disabled. Gate status or bookkeeping alone cannot establish
that a requested plane was programmed. Later ownership/cleanup must qualify the
native engine/context and account for real register effects and original frame
permission; a filtered1 must not be mistaken for native baseline permission.

Private final result: `.private/evidence/20261120-highlight-plane-02.json`.
Source evidence: `evidence/20261120-highlight-plane-registers.json`.

```powershell
.venv\Scripts\python.exe tools/audit_z7_highlight_plane.py --build .private/builds/20261120-frame-host-01 --module .private/builds/20261120-display-highlight-frame-02 --stock-main .private/builds/20261021-silent-property-01/stock-main.bin --output .private/evidence/highlight-plane-new.json
```

## Native-consumer no-frame cleanup

The new `display-highlight-cleanup-probe` is an opt-in API56 profile, using the
unchanged frame-host-01. It adds `display_highlight_cleanup_policy.h` to both the
incoming native conversion and owned consumer paths. The worker only queues and
reaps; source observation performs no cleanup. Register control runs in the
serialized native consumer lane, before a foreign native update takes over or
after an owned restore/disable has actually copied and acknowledged its payload.

The primary permission callback records original native permission and meaningful
format, context, engine pointer/identity and register bank. It retains no caller
or pending frame pointer. Bounded snapshots check sequence and monotonic serial;
exhaustion halts instead of reusing identity. A format4 bypass retains the previous
meaningful format. An enabled native baseline with original permission0 stays
hidden on restoration; original permission1 permits native baseline reprogramming.
The module's filtered1 is never used as evidence of original native policy.

Both initial application and native conversion require an admitted current engine
(camera-RAM descriptor, identity141/142, bank0/4000). These are currently admitted
supplied engine cases, not proven physical output mappings. An engine change or
unreadable snapshot cancels pending cleanup before parameter copy and parks further
owned work. An unknown engine delegates incoming native data without conversion
or plane control. No-frame restore checks context, native generation, actual100
parameters, engine identity/bank and native gate/register results before releasing
the lease. Mode/output disable inhibits the old owned plane and retains its native
baseline. A valid incoming native update quiesces the prior owned plane before its
original handler copies new parameters; old queued restoration cannot overwrite it.

Gate status and active bookkeeping alone remain insufficient. A qualified disable
whose register still reads enabled uses the original driver's bit-preserving
disable directly. Register mismatch or failed verification parks without recording
successful cleanup. This does not promise recovery from hardware that rejects
writes. Unsupported engine allocation/context changes still require native
handoff/restart; no allocation pin or physical scheduling fence is established.

Final reproducible module: `20261120-display-highlight-cleanup-04`,
30148file/29824image/6616BSS/minAPI56,
SHA `5d57065372ce66e013176842653f3d68dd868478f75f01f07fdc236dec9d2ad3`.
Physical warning pixels, hardware application, complete lifecycle and installation
acceptance remain unverified.

Final private audit `.private/evidence/20261120-highlight-cleanup-05.json` passes
27 cleanup/publication checks plus all36 existing owned checks, using an admitted
engine in the ownership fixture. Native source/gate/driver execute against
emulated MMIO for cleanup cases; publication tests include an interrupted reader,
independent publisher stack, repeated sequence and serial exhaustion. A supplied
stuck register bit verifies that failed readback parks without claiming success.
Root tests pass71/no skips. Earlier API52 owned and API56 frame profiles rebuild
byte-identically with cleanup disabled. Source evidence:
`evidence/20261120-highlight-consumer-cleanup.json`.

```powershell
.venv\Scripts\python.exe tools/build_z7_display_module.py --variant display-highlight-cleanup-probe --output .private/builds/cleanup-profile-new
.venv\Scripts\python.exe tools/audit_z7_highlight_cleanup.py --build .private/builds/20261120-frame-host-01 --module .private/builds/cleanup-profile-new --stock-main .private/builds/20261021-silent-property-01/stock-main.bin --owned-regression --output .private/evidence/highlight-cleanup-new.json
```

## Cached primary metadata and state refresh API60

Native cached primary application1023D794 can write state+20 from metadata+30
and call warning gate1023B76E at1023D890, without traversing primary-frame
application1023B9D0. It also accepts NULL metadata and refreshes the gate using
cached state. The earlier API56 hook at1023BAB0 therefore did not cover this path.
The audit reproduces the old profile re-enabling an owned plane through cached
metadata after its primary Off filter had cleared the enable register.

The optional API60 host adds `sdk/cached_frame_permission.h`, an init-only
resident callback, and exact-window bridges at1023D82A and1023D88A. The first
filters fresh metadata before permission publication; the second rechecks cached
state immediately before the gate, including NULL refreshes. Metadata begins at
the native frame+4 substructure; NULL supplies no new original frame policy.
Native result/register/stack/NZCVQ behavior is retained when the callback delegates.
Native nonboolean inhibition, invalid field ranges, failed guards, callback
corruption and recursive entry delegate. API56 profiles do not register this
interface and keep their earlier behavior.

`display-highlight-cached-probe` composes the full cleanup profile with this new
interface. Fresh cached metadata records its original permission; a second NULL
recheck cannot replace that value with the module's filtered permission. A known
original frame policy is retained across same-context/engine native parameter
updates, including explicit native inhibit2. A NULL-only refresh cannot create
an owned plane without known original policy; fresh cached metadata can establish
that policy without a primary-frame submission. No-frame Off then restores the
latest native baseline with its original permission. Menu/movie/context changes
are checked at cached consumption even before another GUI or worker tick.

Reproducible private host `20261120-cached-host-02`:
MAIN `a905e50c63b6c9de8922cd27a8b09ab29b8012f0ae5dce1c228af7d6233f0eb6`,
API60/state304/reservation320/hostC5777bytes. The288-byte prefix is preserved;
cached callback288/running292/guards296,300 are appended. Cold initialization,
native allocator alignment, registration/reentry/cleanup and API56 rejection
execute in the focused audit. Final reproducible profile
`20261120-display-highlight-cached-03`,30340file/30016image/6616BSS/minAPI60,
SHA `6a5b066b1aa6f9212b01b30e63f44ed715f79d9f297bff298e02cb00d9af4cd4`.
The61-check audit compares native delegated results/registers/NZCVQ for fresh
metadata and NULL refreshes, reproduces the old bypass and verifies actual
native driver register effects on the new path. Both input lifetime and task
scheduling are supplied; no physical pixel result is claimed.

This is not a native frame/parameter coordination fence. Static inspection found
seven direct source-call candidates, a separate queued dispatcher registration at
102398D4/101F2414, and the queue executor's callback dispatch at101F240C. Those
boundaries do not establish a common task or shared lock with every source
caller. Upstream caller/lock closure and actual scheduling remain unproven.
The identified stock direct gate callers are1023BAB8 and1023D890; indirect calls,
native engine allocation lifetime and whole lifecycle need further validation.

Final private focused result: `20261120-cached-frame-03/result.json` PASS61.
`20261120-cached-cleanup-regression-01.json` passes the27 cleanup/publication and36
owned checks on this exact API60 pair. The ownership fixture adds only admitted
engine setup; native control cases use actual driver writes to emulated MMIO.
Root tests pass71/no skips. API56 host and cleanup profile rebuild byte-identically
with cached hooks disabled. Source evidence:
`evidence/20261120-highlight-cached-primary.json`.

```powershell
.venv\Scripts\python.exe tools/build_z7_module_host.py --display-hooks --highlight-hooks --parameter-hooks --frame-permission-hooks --cached-frame-permission-hooks --output .private/builds/cached-host-new
.venv\Scripts\python.exe tools/build_z7_display_module.py --variant display-highlight-cached-probe --output .private/builds/cached-profile-new
.venv\Scripts\python.exe tools/audit_z7_cached_frame.py --build .private/builds/cached-host-new --module .private/builds/cached-profile-new --legacy-build .private/builds/20261120-frame-host-01 --legacy-module .private/builds/20261120-display-highlight-cleanup-04 --stock-main .private/builds/20261021-silent-property-01/stock-main.bin --output .private/evidence/cached-frame-new
```

## Remaining implementation work

Complete visible rendering and broader ownership/restoration lifecycle
acceptance, including native engine allocation and unsupported context handoff.
Native packet conversion, owned asynchronous requests and consumption-time
primary permission filtering are connected in the opt-in API56 full profile.
The pinned photo_zebra implementation changes eligible native100-byte parameter
payloads before dispatch, preserving the descriptor/callback, and also submits
owned requests for output switches that generate no native packet. Both paths
must be ported; owned-only submission is not a substitute for native packet
conversion. Convert owned work at the consumer boundary with current context,
retain lifetime through completion/dispatch return, and conditionally restore
native state. Ordinary non-highlight/ineligible packets must remain native.
Original source-submit
boundary1034866E, frame+34 permission, rear/EVF source routing and mode property's
RAM backing execute in diagnostics. Physical output/timing acceptance and the foreign
context/image chain remains unbound. Do not reuse Z7II callback
addresses or assume its context/image offsets. Extend the current parameter
interception and cancellation/restoration with frame cleanup, preset visibility,
and native LCD/EVF/movie preservation across the full resident lifecycle. Pixels and output/
capture/menu/lens transitions require separate acceptance evidence.

The Photo highlights preference drives native/owned parameter conversion and
the API56 consumption-time primary permission filter. Broader teardown and
physical rendering acceptance remain open.
No visible highlight feature or installation/recovery clearance is claimed.
