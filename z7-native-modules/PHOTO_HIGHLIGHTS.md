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

## Remaining implementation work

Publish/revalidate a shared settings/context epoch, then integrate the
validated optional host bridges and resident asynchronous owner with the full
profile's worker and Photo highlights preference. Original source-submit
boundary1034866E, frame+34 permission, rear/EVF source routing and mode property's
RAM backing execute in diagnostics. Physical output/timing acceptance and the foreign
context/image chain remains unbound. Do not reuse Z7II callback
addresses or assume its context/image offsets. Then integrate owned
packet interception, cancellation/restoration, preset visibility, and native
LCD/EVF/movie preservation with the full resident profile. Pixels and output/
capture/menu/lens transitions require separate acceptance evidence.

The existing Photo highlights preference is still not connected to a producer.
No visible highlight feature or installation/recovery clearance is claimed.
