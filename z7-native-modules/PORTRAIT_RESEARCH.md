# Original Z7 portrait port

Independent work against original Z7 C3.80, following the MIT-licensed
[pinned JKWTCN implementation](https://github.com/JKWTCN/z7ii-extensions/blob/50a22b24c50619cffa646dac386e8334659f475a/plugins/portrait_menu.c).
This is an incomplete port. No orientation drawing hook is installed by the
current display module. The accepted LCD/EVF highlight pair is unchanged.

## Opt-in resident graphics bridge (API84)

The independent host now offers `sdk/graphics.h`, preserving the API80 prefix.
`--graphics-queue-hooks` requires the native-cache profile. It reserves 384 bytes
of state, including two new guards, and a 256-byte cold hook. Registration is
init-only; module failure clears staged registration before freeing its image.
After successful publication, the resident worker waits for native task slot
`A1D75D60` to contain stock dispatcher `10372391`, then atomically installs a
permanent host bridge. It never places unloadable module code directly in that
slot. A foreign slot value or later replacement makes takeover sticky-disabled.

The bridge validates committed state, callback bounds, the current slot and
message span, then uses a recursion guard. Callback return1 means synchronous
handling and completion finished; return0 must preserve the message and leave
completion to stock. Other results fall back to stock. This is a trusted native
callback contract, not a sandbox. LCD/page/command admission belongs to the
callback and is not yet implemented in the functional portrait module. Native
task caller closure, renderer lifetime, full boot and camera pixels remain open.

Private `20261121-graphics-host-02/result.json` passed29 checks using actual loader,
SDK registration, dispatch, completion and cold initialization instructions.
Filesystem, allocator, kernel, rectangle renderer and task scheduling are supplied.
The reproducible 320-byte probe tests stock/owned completion, invalid-result
fallback, reentrancy, late-registration rejection, guard corruption, foreign
ownership and failed-init rollback. It does not rotate any UI.

The API84 host independently rebuilt exactly; cache regression passed102 and
existing display/highlight handoff passed68. Graphics disabled reproduces the
accepted API80 MAIN exactly. Root71 passed with no skips. Source-only evidence:
[evidence record](../evidence/20261121-graphics-host.json). These results do not
clear an installation candidate or establish camera update acceptance/recovery.

## Native orientation and bounded geometry

`plugins/portrait_target.h` now supplies a read-only predicate for the original
logical2, 720x480 target with exclusive LCD output. Original `10414756` searches
33 registry records (20 bytes each) for the selected hardware ID at `A180AD84`;
the table pointer is at +4. Record +0 is the buffer, +4 the hardware ID byte,
+6/+8 width/height. A hardware ID of12 can therefore resolve to logical2.
This differs from treating the raw selected byte as a logical target index.

The helper bounds the table, rejects inactive255, requires a nonzero buffer,
720x480 dimensions and exactly one matching hardware ID, executes the original
getter and requires result2. It rechecks output, registry identity and all five
descriptor words afterward. These are observed consistency checks, not a lock,
allocation pin, ABA exclusion, physical LCD mapping proof or page policy. Other
portrait layers may use other targets; this predicate is not their final policy.

Private `20261121-portrait-target-01/result.json` passed44 compiled checks. Hardware
IDs0/1/2/12/32/254 resolve through the actual native getter; non-LCD output,
other logical targets, invalid registry spans, inactive/duplicate IDs, wrong
dimensions and changes observed across the getter are rejected. Input memory is
unchanged except explicitly supplied race mutations. The 384-byte probe rebuilds
identically. Registry/output states are supplied; no renderer, live task, native
surface allocation, camera or card is exercised. The functional display module
still does not register a portrait callback.

`plugins/orientation_sample.h` calls the original read-only Thumb API
`101B331B`. It accepts native values0..3 and leaves the caller's output unchanged
for unknown4 or any larger value. It never changes the native override.

Observed native behavior, executing stock instructions:

| Gate word at A1809074 | Selector at A1D49784 | Raw return |
| --- | --- | --- |
| Exactly1 | Any | Sensor byte at A1D495DC |
| Other | 1 | 0, landscape |
| Other | 2 | 3, inverted landscape |
| Other | 3 | 1, portrait A |
| Other | 4 | 2, portrait B |
| Other | 0 or greater than4 | 4, unavailable |

The native wrapper at10532FD6 maps only unknown4 to landscape0. It passes other
values through, including invalid sensor bytes. Its connection to the graphics
task has not been established. It is not used by the bounded sampler.

The original override setter101B4224 stores its full selector, compares raw
orientation before/after and conditionally dispatches notification42051201 with
the new value through the callback at A1809088. A missing callback is allowed.
These are observed branches with supplied gate/sensor inputs, not physical IMU
validation or an explanation of the gate's real startup lifecycle.

`plugins/portrait_geometry.h` provides exclusive-edge box transforms between
LCD720x480 and portrait480x720. Portrait1 and2 select opposite quarter turns;
landscape0 and inverted3 are left to caller policy. Coordinates and dimensions
are bounded before subtraction. Failure preserves the output, and exact
input/output aliasing is supported. This is abstract geometry, not a native
payload layout or complete HUD reflow.

Private audit `20261120-orientation-02/result.json` passes13405 checks:9216 native
gate/selector/sensor combinations,504 original override/notification cases,
2604 valid compiled geometry cases, invalid/extreme coordinates, null pointers,
nonmutation and in-place round trips. The flat compiled probe is reproducible,
384 bytes including its header,320 image,0 BSS and0 relocations. Its manual
fixture loading does not exercise the module loader admission path.
Run02 refreshes the current header fingerprint after changing reusable geometry
helpers to `static inline`. The probe remains384 bytes, with a changed image
layout; run01 remains historical evidence for the previous source checkpoint.

## Native rectangle queue and dispatcher

The original rectangle painter10433912 reaches104FFED0 for clearing and
104FFD54 for shape rendering. The clear path reaches producer1042F5F6.

| Binding | Original Z7 address |
| --- | --- |
| Graphics task structure | A1D75D34 |
| Queue member | Task+20 |
| Registered dispatch slot | Task+2C, A1D75D60 |
| Dispatcher | 10372391, Thumb |
| Producer enqueue wrapper | 103726B9, Thumb |
| Queue-mode halfword | A180AD70 |
| Rectangle producer | 1042F5F7, Thumb |
| Rectangle backend adapter | 1042F5A9, Thumb |
| Producer completion callback | 1042EADF, Thumb |
| Completion event storage | A1D75E3C |

The original registration routine101F2414 writes the callback to task+2C,
initializes task+20 and starts the task. This slot differs from the pinned
Z7II task+24 layout. Do not copy its address or structure offsets.

For a nonzero signed queue-mode halfword,1042F5F6 builds command42010017 with
six payload words: x,y,w,h and two widened flag bytes. Its seven-word message
contains a queue self-link at+8, completion at+C, command at+10, payload pointer
at+14 and result at+18. The real enqueue wrapper writes the self-link. The
original dispatcher converts the payload back to a28-byte shape, zeroes unused
fields, calls1042F5A8 synchronously, writes result0 and invokes the original
completion with42010062/0. That callback signals the producer's event. With
queue-mode0, the producer calls the backend directly with the input shape.

Private `20261120-graphics-queue-05.json` passes27 checks covering original
registration, direct and queued paths, original enqueue wrapper, all message
fields used here, three boxes, modes0/1/2/FFFF, input preservation and completion.
Two Unicorn CPUs use an explicitly serialized schedule; queue/lock/event kernel
services and the renderer are supplied. This proves marshalling and dispatch,
not real task concurrency, installed-hook lifetime or pixels. Early fixture runs
01/02 expected the wrong completion code;03 failed a Python bytearray transfer;
04 passed26 before registration coverage was added in05. Failed runs are not
accepted evidence.

## Caller-admitted synchronous portrait drawing

`plugins/portrait_draw.h` now connects a caller-selected portrait box to original
Z7 message dispatch. It supports native rectangle commands13/16/17 and image
commands19/1A plus fixed-point1C conversion. This is callable software, not an installed graphics hook: the
caller must own the graphics task and admit the intended LCD output/page.

The Z7 payloads differ from the pinned Z7II layouts:

| Command | Source words | Original Z7 backend |
| --- | --- | --- |
| 13 | 8 | 1042F066,28-byte normalized shape |
| 16 | 7 | 1042F426,seven arguments |
| 17 | 6 | 1042F5A8,28-byte normalized shape |
| 19 | 18 | 104303E6,68-byte normalized image |
| 1A | 24 | 1042F894,88-byte normalized image |
| 1C | 18 | 10430BCA,68-byte fixed-point image; converted to1A for portrait |

Image angles are the low half of source word15. Source words16/17 become
two flag bytes, while1A skips source word18 and copies words19..23 into its
extra backend fields. Using the pinned angle word16 would alter a flag instead.
The adapter preserves other source fields, converts destination corners and
adds the intended quarter turn to angles0/90/180/270/360. Mode0/1 input becomes
explicit-destination mode0. Rectangles convert top-origin portrait geometry into
the native bottom-origin payload. Original source bytes are never changed.

The local message defers completion until original dispatch returns, then copies
its result and invokes the original producer completion exactly once. Admission
checks reject foreign callbacks, unknown commands, malformed RAM spans, invalid
angles/modes, unsupported orientations and invalid boxes without dispatch or
acknowledgement. Page policy and full text integration are unfinished.

Private `20261120-portrait-draw-02/result.json` passes155 checks:138 draw cases
covering all five commands, both portrait directions, three boxes, both image
modes and five angles;17 rejected-input cases preserve message/payload state.
The original dispatcher, image normalization adapters and completion execute.
Only backend renderers and the kernel event boundary are supplied. Comparison
excludes backend padding bytes that native adapters leave undefined. Render,
deferred completion, original acknowledgement and event order are checked.
The probe builds reproducibly:640 file/576 image/0 BSS/0 relocations. Flat fixture
loading does not prove module-loader admission or actual renderer lifetime.
Draw01 failed compilation because the original shared header emitted an unused
direction helper under `-Werror`; reusable inline helpers corrected02.

## Fixed-point images and dedicated font provider

The current compiled adapter converts1C to the rotatable1A format. Original
Z7 fixed-point1C has no clear-field word, unlike the pinned Z7II format. It
copies source0..5, sets an untinted white color, leaves clear fields zero and
maps source10 to1A blend11, source11/12 to1A flags16/17 and source13..15 to
1A extra fields19..21. Its original fractional destination is replaced by the
caller-selected integer portrait box. Nonzero trailing source16/17 controls are
rejected, matching the pinned exclusion. Source bytes are preserved; message
command and payload remain unchanged except the final result word.

`20261120-portrait-draw-08/result.json` passes186 checks:150 compiled draw cases,
12 independent original1C normalizations,18 rejected inputs and6 font-binding
checks. Fixed-image cases supply a24x32 crop with positive pitch/height. Both
the original fixed adapter and converted image adapter execute, but their GPU
backends remain supplied sinks. No physical image equivalence is established.
Probe768 file/704 image/0 BSS/0 relocations, reproducible, SHA256
`a1e21d1a8957ab1282d9d5a3917facf45b7fc29484dfe4245c8b93acea29381c`.
Run03 passed180 before font tracing;04 failed an incorrect five-argument font
trampoline assumption;05 passed185;06 removes unused stack-argument tracing;
07 adds the original initialized font-provider path;08 uses neutral names for
the rejected trailing controls, whose native meaning remains unestablished.

Original font provider initializer10477C30 stores table11B6E120 at
context+45B4; the native literal at10477F74 identifies that table. Its slot+1C
contains the dedicated renderer10539575 (Thumb). This agrees with the pinned
provider offset45B4, while the actual addresses differ. Renderer entry copies
the context matrix at+34. Original text descriptor functions104BAA5E,
104BB130 and104BB248 are the34/37/38 dispatcher branches. Live descriptor,
context, provider initialization and interception lifetime still need binding.
The initializer's already-initialized branch executes with a supplied nonzero
context+45D8 state: it returns0 and changes only the provider pointer at45B4.
This does not prove its allocation path or real boot-time font state.

Do not substitute10476CFC: that trampoline reads provider0 at context+454C,
overwrites r2 with its callback and forwards two meaningful arguments. Three
supplied option values and the null-provider return execute in the audit, with
matrix/provider preservation. This test distinguishes the wrong layer; it does
not exercise the dedicated glyph renderer or establish a live font context.

## Synchronous text-provider interception

`plugins/portrait_text.h` is a callable adapter for commands34/37/38 with the
original Z7 text completion104BA383. It uses the original context slotA180AD98,
also read by native getter104BA37C, and requires descriptor+94 to match that
context. Descriptors must spanC8 bytes; the original34 path accesses fields
past the pinned B0-byte admission range. It requires context4604 bytes, stock
provider11B6E120 at+45B4 and dedicated glyph slot10539575. Caller graphics-task
ownership and LCD/page admission are still required.

A bounded caller transform specifies orientation1/2, positive16.16 x/y scales
at most2 and fixed-point translation within +/-720 pixels. Ordinary eligible
glyph draws receive composed portrait matrices. Measurement/bounds queries and
null origins retain their matrix. Zero/negative/large/rotated source scales,
rounded-zero products and overflowing destination translations use the stock
renderer unchanged. Int64 intermediate arithmetic prevents signed overflow;
all seven matrix words are restored after the glyph call, including failure
return values. Caller scale and placement do not implement descriptor reflow.

The adapter copies the eight-word provider table, replaces only its glyph slot
for one synchronous dispatch, and defers the producer acknowledgement. A busy
owner is rejected. Normal completion unpublishes the local table and releases
the state before acknowledging42010063/0 through the original text callback.
If another owner replaces the provider during rendering, its replacement is
preserved. This does not prove general task exclusion or renderer reentrancy.
Inline bitmap-symbol provider rotation is not yet implemented.

Private `20261120-portrait-text-02/result.json` passes261 checks:216 command/
orientation/scale/matrix combinations, seven query/null-origin cases, a foreign
provider replacement,18 admission rejections with18 busy-owner preservation
checks, and the original context getter. An independent affine composition
reference checks transformed values. Tests inspect actual34/37/38 dispatch
argument mapping, glyph return propagation, source payload/message preservation,
provider publication, matrix restoration and cleanup-before-acknowledgement.

The original dispatcher, text completion and event wrapper execute. Descriptor
functions104BAA5E/104BB130/104BB248 are redirected to a supplied Thumb stub that
calls the published provider; renderer10539574 is a supplied glyph sink. Native
glyph shaping, metrics, bitmap symbols, context initialization and pixels are
not exercised. The probe is reproducible:1088 file/1024 image/28 BSS/0 relocations,
SHA256 `9ee393c727b0a817880dc88e9cc4d4702b74e343b59da95d4305f9875535db59`.
Flat fixture loading does not establish module-loader admission. Run01 passed170
before extreme-boundary, argument mapping and cleanup coverage expanded in02.

## Native glyph contours and font readiness

The adapter now also requires a bounded1BC-byte glyph state at context+45D8
and four nonnull, aligned native-RAM buffer pointers at state+1AC/+18C/+19C/+178.
Original provider initialization publishes its table before allocating those
buffers, so the earlier table-only check admitted an incomplete context. These
are basic readiness checks, not allocation pins, capacity validation or task
exclusion. `20261121-portrait-text-03/result.json` passes273 checks including six
new partial-state rejection cases and preservation of a busy owner's state.
The updated probe is1216 file/1152 image/28 BSS/0 relocations, reproducible, SHA256
`82fbd88cfa691acd3d65f022e8bb5dcaa306d82b186bd95dfc3508c8a9d10fa8`.

`tools/audit_z7_native_glyph.py` executes the original provider initializer10477C30,
renderer10539574, metrics aggregation10476E28, face selection10476846, contour
transformation104A9416 and provider destruction10477B9C. Descriptor processing
remains a supplied Thumb stub. A supplied font face provides metrics and a
three-vertex outline; a supplied shaper maps ASCII input to one glyph per code.
The final contour emitter10478AD2 is a sink. Native UTF-16 conversion into the
provider's UTF-32 buffer is independently checked. This does not establish Nikon
font-file loading/shaping, bitmap symbols or actual GPU pixels.

Private `20261121-native-glyph-09/result.json` passes192 exact-behavior checks
across36 paired native layouts: commands34/37/38, orientations1/2, A/ABC input,
unit/three-quarter/half-height scale and translation. Native provider allocation,
buffer setup and destruction run with supplied bounded native-RAM allocators.
Every normal pair frees all its owned buffers. Native metric failure2 also
restores provider/matrix before stock acknowledgement and permits destruction.

Native translation quantization matters. Instructions10539EB0..CE ceiling each
glyph translation to an integer pixel AFTER rotation. Reflecting an already
ceiled translation differs by one pixel at fractional positions. The audit
captures each pre/post-round native origin, proves the pre-round affine mapping,
checks the exact ceiling rule and compares all final vertices with that phase.
There is no comparison tolerance. Earlier01/02 incorrectly post-scaled an
already laid-out contour;03/04 exposed a supplied shaper reading UTF-16 as32-bit;
05 exposed the post-rotation ceiling phase.06 completed contour cases but failed
the assumed allocation unwind.07 recorded counterexamples;08 adds readiness
guards/native-RAM allocations;09 separately verifies rejection of partial states.

**Unresolved allocator contract:** returning NULL from supplied allocation1
produces native error1 without state publication. Supplied NULL at allocations
2..5 instead reaches an unmapped write at104A9C4A: native buffer helpers zero
the returned pointer before checking it. Those four faults retain1..4 supplied
allocations and are explicit counterexamples, not successful recovery. The
actual camera allocator's failure contract remains unproved. A separate emulator
call shows the portrait adapter rejects each resulting incomplete state without
publication or acknowledgement; it does not unwind or recover the native fault.
Do not claim camera OOM safety from this audit.

## Original descriptor and font-context integration

`tools/audit_z7_native_text_descriptor.py` removes the descriptor stub for
commands34/37/38. The operational font context now comes from original
constructor10476904 with maximum-glyph-size and identity-matrix invariants,
followed by four original provider registrations through10476ACA. The allocator
descriptor and memory addresses remain supplied; camera allocator behavior is
not modeled. The parent fixture's earlier supplied context is discarded first.

Original option constructor104774AC establishes measurement-cache flags and
ownership. Geometry setter1047762A and text setter10477526 run; the latter accepts
a pointer/count/encoding descriptor, not a raw string pointer. UTF-16 input is
copied into owned option storage. The audit also executes native alignment
wrapper1044F85E, context/option destruction10476A70/10477502 and text completion.

Private `20261121-native-descriptor-01/result.json` passes240 checks over48 paired
native paths: three commands, both orientations, A/ABC input, unit/three-quarter
portrait scale and alignment modes0/2. The same native descriptor processing runs
with stock and intercepted providers. Measurement/bounds queries retain their
stock entry matrix and origin values; actual drawing entries receive the exact
reference portrait matrix. Widget metric fields remain equal, source messages/
payloads are preserved except native result0, provider/state cleanup precedes
acknowledgement, and native destructors release every tracked allocation.

Command34 selects the native bitmap target and reaches the supplied bitmap
emitter104AA7FE once per glyph. Commands37/38 reach the native contour path and
the supplied final contour sink. Per-glyph bounds, font metrics/outlines, an
already cached synthetic font face, shaping, allocator callbacks and selected
GPU APIs remain explicit supplied boundaries. The fixture uses a matching
synthetic outline/advance unit and does not load Nikon font files. It does not
establish final bitmap rasterization, inline symbols, GPU pixels or camera boot.

Early private traces exposed missing measurement-cache flags, the setter's
structured input ABI, native identity flag1 after reset and the required native
maximum-glyph-size/graphics state. These were fixture deficiencies corrected by
using original constructors rather than weakening the matrix or cleanup checks.
The admitted probe remains byte-identical to portrait-text-03/native-glyph-09:
1216 file/1152 image/28 BSS, SHA256
`82fbd88cfa691acd3d65f022e8bb5dcaa306d82b186bd95dfc3508c8a9d10fa8`.
The previously documented supplied-NULL allocator counterexamples remain open.

## Remaining integration

### Original i-menu classification

The original app registration prefix `1030CF74..1030D00A` binds index3 to
`A1829970`. Original indices4/5 bind `A1829B1C`/`A1829B40`, not the same i-menu
root. Native getters `10385B6A`/`10385B72` read mode/variant at `A18298B8`/+1.
The actual variant branch at `10386B18` selects the grid-style descriptor path
for0 and `0x29`, unlike pinned Z7II's `0x31`. The original entry at `10386C72`
sets mode3 before selecting a variant. These original bindings must replace
upstream constants rather than applying an address offset.

`plugins/portrait_page.h` classifies that original i-menu root into grid
(mode3, or mode0/variant0-or29), dial (mode2/variant0-or29), setting (remaining
modes0..2) or other. It queries the original getters and rechecks app/root and
mode/variant afterward. It does not admit drawing, exclude physical MENU or
playback task takeover, classify live/external pages, or establish task lifetime.
The caller must supply those final policies before the portrait callback uses it.

Private `20261121-portrait-page-01/result.json` passed2552 checks: actual native
registration prefix, all256 variants through the original routing branch,
2032 compiled classification cases, other app IDs, foreign roots and observed
changes during the getter calls. The reproducible probe is256 bytes. Inputs and
race mutations are supplied; no complete app startup, native transition lifecycle,
rendering or pixels are proved. The first audit attempt stopped on an uninitialized
fixture field; after initialization order was corrected the audit completed.
See [source-only evidence](../evidence/20261121-portrait-page.json).

Bind actual LCD output/target admission, native font-file/bitmap emission and symbols,
draw-task lifetime and callback ownership before installing a rotation hook.
Preserve producer completion and payload lifetime: never redirect asynchronous
native work to a temporary stack copy. Then port portrait reflow, navigation and
touch mapping, settings/persistence and cleanup across mode transitions. Physical
MENU, playback, magnified view and other upstream exclusions need their intended
policies preserved. Native startup, Info mirror, real histogram source and exact
installation/recovery assessment remain separate unfinished requirements.

The previously missing pinned `portrait_probe.c` was fetched read-only into
private research:7717 bytes, SHA256
`119c24c6846abb6df80969a4c56ee33ffcca9bd878555c0e55ac1db8723411ac`.
Its SPDX MIT notice is preserved. Firmware, probes and emulator output stay
private. No camera/card access, staging, flashing or push occurred.
