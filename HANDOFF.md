# Laptop handoff — October 20, 2026

## Original text descriptors and full font-context fixture - November 21, 2026

Previouseb5d8c7 exercised native glyph layout with a descriptor stub. This is
PROGRESS: original34/37/38 descriptor functions now execute, with operational
font context from original10476904 and all4 native provider registrations.
No persistent graphics hook/page integration, no camera/card/stage/flash/push.
Full original goal ACTIVE.

Native options104774AC, setters1047762A/10477526, alignment1044F85E and
destructors10477502/10476A70 execute. Text setter takes{pointer,count,encoding};
factory establishes measurement-cache flags. Native maximum glyph size and
graphics state are initialized by constructor rather than manually guessed.
The parent fixture's preliminary supplied context is discarded before this path.

native-descriptor-01/result.json PASS240 across48 stock/portrait pairs:34/37/38,
both directions,A/ABC,unit/.75 scale,alignment0/2. Queries preserve native entry
matrix/origin; draws get exact reference matrix; widget metrics match stock;
message/payload preserved except result0; native cleanup precedes acknowledgement;
native destruction releases all tracked allocations.34 reaches supplied bitmap
emitter104AA7FE,37/38 native contours with final sink. Font face/cache, metrics/
outline/shaping, allocator and GPU APIs still supplied. No Nikon font-file load,
bitmap rasterization/inline symbols/GPU pixels/live task lifetime or boot proof.

Probe byte-identical to portrait-text-03/native-glyph-09:1216file/1152image/28BSS/
0relocs/reproducible, SHA82fbd88cfa691acd3d65f022e8bb5dcaa306d82b186bd95dfc3508c8a9d10fa8.
Prior four supplied-NULL native allocator counterexamples remain unresolved.
Early private traces corrected fixture option flags, structured text input,
identity flag1 and missing context invariants; no failed trace is acceptance proof.

See PORTRAIT_RESEARCH.md and evidence/20261121-native-text-descriptor.json.
Next: native font files/bitmap symbols and live graphics output/target/page/task
admission, then portrait reflow/input/settings. Original accepted highlight
host/module unchanged. Native lifecycle/writer/bank/engine closure, Info mirror,
real histogram source and integrated release/install/recovery remain unfinished.

Final root71/no skips:20261121-native-descriptor-root-tests.log. All direct
fingerprints current and probe bytes identical to the accepted text adapter.
Ignored Graphify refreshed3379nodes/9147edges; existing parser warnings retained.
Source-only checkpoint, no integrated firmware release rebuild or flash clearance.

## Native glyph contours and incomplete-font admission - November 21, 2026

Previouse0bc399 added text interception against supplied glyph renderer. This
checkpoint is PROGRESS: original native glyph renderer and contour transform
execute; portrait_text.h now rejects basic incomplete native font state. Full
original goal ACTIVE. No camera/card/stage/flash/push. No installed graphics hook.

New admission requires context+45D8 state span1BC and native-RAM buffers at
state1AC/18C/19C/178. Stock provider publishes its table before initialization
finishes; the prior table-only guard was insufficient. These bounded readiness
checks do NOT pin allocations or establish capacity/task/lifetime closure.
portrait-text-03 PASS273; probe1216file/1152image/28BSS/0relocs/reproducible,
SHA82fbd88cfa691acd3d65f022e8bb5dcaa306d82b186bd95dfc3508c8a9d10fa8.

native-glyph-09/result.json PASS192 exact-behavior checks with36 native paired
layouts (34/37/38, both rotations, A/ABC, unit/.75/half-height scales). Actual
provider initializer10477C30, glyph renderer10539574, metrics/face selection,
contour transform104A9416 and destruction10477B9C execute. Font face metrics/
triangle outline, shaping, descriptor processing, allocator and final contour
emission remain supplied. Native UTF16->UTF32 buffer checked independently.
Normal buffers all freed; native metric error2 restores matrix/provider and
acknowledges through stock completion. No Nikon font-file shaping or GPU pixels.

IMPORTANT native10539EB0..CE ceilings glyph translations after rotation. Audit
checks pre-round affine mapping, exact native ceiling phase and final vertices
without tolerance.01/02 used a post-scaled contour reference;03/04 shaper fixture
used wrong UTF16 width;05 exposed the ceiling phase;06 reached allocation fault;
07 recorded it;08 readiness/native-RAM allocator;09 adds separate partial-state
rejection calls. Failed runs remain failed, not silently cleared evidence.

UNRESOLVED: supplied allocator NULL1 returns error1/no publication; NULL2..5
fault at104A9C4A (zero-before-null-check) retaining1..4 supplied allocations.
Four expected counterexamples are included in192 behavior checks, NOT recovery
passes. Actual camera allocator contract unproved. Separate adapter calls reject
the resulting partial states without ack/publication; no native fault recovery
claimed. Carry this gap into exact installation/recovery assessment.

See PORTRAIT_RESEARCH.md and evidence/20261121-native-glyph.json. Next: native
font-file/live descriptor behavior, inline bitmap symbols, live LCD target/page/
task admission, portrait reflow/input/settings integration. Prior highlight
host/module unchanged. Native lifecycle/writer/bank/engine closure, Info mirror,
real histogram source and integrated release/install/recovery remain open.

Final root71/no skips:20261121-native-glyph-root-tests.log. Both final audit
fingerprints and identical probe packets verified current. Ignored Graphify
refreshed3367nodes/9091edges; existing parser warnings retained. Source-only
checkpoint, no new integrated firmware release or flash clearance.

## Caller-admitted portrait text matrix interception - November 21, 2026

Previous686929a is the fixed-image/font-binding checkpoint. This is PROGRESS:
portrait_text.h now implements synchronous temporary provider interception for
original-Z7 text commands34/37/38. No persistent graphics hook or full portrait
page/input integration. Full original goal ACTIVE; no camera/card/stage/flash/push.

Native font context slotA180AD98/getter104BA37C; text completion104BA383 signals
eventA1D75E48/2 through original wrapper. Descriptor spanC8 (original34 reads past
pinnedB0), descriptor+94 must match context4604, provider+45B4 must be11B6E120,
glyph slot+1C must be10539575. Caller owns graphics execution and LCD/page policy.
Positive bounded scales/translations compose portrait glyph matrices with int64
intermediates. Queries/null origins retain stock matrices. Unsupported matrices,
rounded-zero scales and translation overflow fall back to stock renderer. Seven
matrix words restored after renderer return, including failed returns.

Local provider table and deferred callback live through original dispatch. Busy
owner rejected. Normal provider/state restored before original acknowledgement;
foreign provider replacement preserved. Reentrancy/task/lifetime closure remains
unproved. Bitmap-symbol provider interception and descriptor reflow unfinished.

Private portrait-text-02/result.json PASS261:216 draw combinations,7 query cases,
foreign provider replacement,18 rejection+18 owner-preservation cases, native
context getter. Original dispatcher/completion/event wrapper execute; native
descriptor processing and glyph renderer are supplied Thumb-stub/sink boundaries.
No glyph shaping/native metrics/live font state/pixels proof. Probe1088file/
1024image/28BSS/0relocs/reproducible, SHA
9ee393c727b0a817880dc88e9cc4d4702b74e343b59da95d4305f9875535db59.
Flat loading does not exercise module-loader admission.01 PASS170;02 broadens
boundary/argument-mapping and cleanup-before-ack coverage. Direct fingerprints
verified current; see evidence/20261121-portrait-text.json and PORTRAIT_RESEARCH.md.

Next: actual native text/glyph and inline symbols, live LCD output/target/page
admission and graphics-task ownership, then portrait reflow/input/settings.
Original highlight host/module unchanged. Native startup/writer/bank/engine
closure, Info mirror, real histogram producer, integrated release and exact
installation/recovery assessment remain unfinished.

Final root71/no skips:20261121-portrait-text-root-tests.log. Probe identity and
all direct audit fingerprints verified; ignored Graphify refreshed3354nodes/
9036edges with new code present, existing parser warnings retained. Source-only
checkpoint; no full functional host/module release rebuild implied.

## Fixed-point portrait images and font-provider binding - November 20, 2026

Previous67450bd added caller-admitted portrait rectangles/images. This checkpoint
is PROGRESS: native1C fixed-point image conversion to rotatable1A now compiled
and checked. No graphics hook, live LCD admission or text rotation installed.
Full original goal ACTIVE. No camera/card/stage/flash/push.

Z7 fixed1C is18 source words with NO Z7II clear word: first6 copied, white tint,
zero clear fields, blend10->1A11, flags11/12->16/17, extra13..15->19..21.
Original source16/17 trailing controls rejected; their meaning is unestablished. Caller portrait box replaces fixed
destination; original native1C and converted1A normalization execute. Producer
completion remains deferred until dispatch return and acknowledged exactly once.

Private portrait-draw-08/result.json PASS186:150 draw cases+12 native fixed-image
normalizations+18 rejected inputs+6 font-binding checks. Probe768file/704image/
0BSS/0relocs/reproducible, SHAa1e21d1a8957ab1282d9d5a3917facf45b7fc29484dfe4245c8b93acea29381c.
Backend renderers/kernel event/caller LCD admission supplied; no pixels, live
task concurrency, full renderer lifetime or module-loader admission proof.

Font initializer10477C30 binds table11B6E120 at context+45B4; table+1C is
dedicated glyph renderer10539575. DO NOT use10476CFC as five-arg renderer:
actual provider0 trampoline uses context+454C and clobbersr2 selecting a two-arg
callback.03 PASS180;04 failed that five-argument assumption;05/06 PASS185 after
correcting fixture/model.07 adds original initialized-provider branch: supplied
context+45D8 nonzero, returns0 and changes only table pointer45B4. No allocation/
boot initialization or dedicated renderer execution is proved by this audit.
08 uses neutral labels for the unestablished trailing-control meaning.
Native text descriptor paths34/37/38 reach104BAA5E/104BB130/104BB248.

See PORTRAIT_RESEARCH.md and evidence/20261120-portrait-fixed-image.json.
Next bind live text descriptor/context/provider, implement bounded matrix
interception/restoration; then real LCD target/page/task admission and portrait
reflow/input/settings integration. Original highlight host/module unchanged.
Native startup/writer/bank/engine closure, Info mirror, real histogram source,
integrated release and installation/recovery assessment remain unfinished.

Final root71/no skips:20261120-portrait-fixed-root-tests.log. Current audit source
fingerprints verified; ignored Graphify refreshed after code edits. Firmware,
probes and generated graphs remain private/ignored. Functional full-module host
pair remains the previously accepted highlight build; no new release implied.

## Synchronous portrait rectangle/image adapter - November 20, 2026

Previous94c65c4 is the geometry/queue foundation. This checkpoint is PROGRESS:
compiled caller-admitted portrait_draw.h now executes original Z7 dispatch for
rectangle13/16/17 and image19/1A with transformed destination and image angle.
No graphics hook is installed; caller LCD/page/task admission remains required.
Full original goal ACTIVE; no camera/card/stage/flash/push.

CRITICAL original-Z7 format difference: image angle is source word15 (Z7II16),
flags16/17;1A ignores word18 and copies19..23 to extra backend fields. Source
word counts13/16/17/19/1A are8/7/6/18/24. Local copies preserve source payload;
native dispatcher runs synchronously with deferred callback, then original
producer acknowledged once with42010062/0. Invalid spans/callbacks/commands,
angles/modes/orientations/boxes return unchanged without acknowledgement.
Fixed-point image1C, text reflow, navigation and real LCD admission unfinished.

Private portrait-draw-02/result.json PASS155 (138 draws+17 rejection cases),
probe640file/576image/0BSS/0relocs/reproducible,
SHAfea18c4dd08683f85e4a26e9403b64536c2ce17f0294b89d15b49195631013f8.
Original dispatcher/image normalization/completion execute; backend renderer,
event service and admitted layout supplied. No pixels or renderer lifetime proof.
Draw01 failed unused static helper under-Werror; geometry header now inline.
Orientation-02 PASS13405 refreshes header/audit fingerprints and384-byte probe,
SHA31af1709d71ec6d97e9fd99c59496c9bb7ebfd3e3f40a51edccc59bb6cf2f970.
Orientation timeout-thread overhead removed; instruction bound remains in force.

See PORTRAIT_RESEARCH.md and evidence/20261120-portrait-draw.json. Original
highlight host/module unchanged. Next: fixed-point image1C, text adapter,
LCD output/target/page admission and graphics-task ownership, then reflow/input/
settings integration. Native lifecycle/writer/bank/engine closure, Info mirror,
real histogram producer and exact release/install/recovery assessment remain.

Final checks: root71/no skips (20261120-portrait-draw-root-tests.log), both final
audit fingerprints current. Ignored Graphify refreshed3327nodes/8966edges with
new code present; existing parser warnings retained. No full functional module
rebuild implied: these are diagnostic probe and standalone adapter changes.

## Orientation foundation and original graphics queue - November 20, 2026

Previous a753620 is the accepted logical LCD/EVF highlight pair. This checkpoint
is PROGRESS only: bounded read-only native orientation sampling, compiled
portrait box math and an original-Z7 graphics queue binding. No portrait drawing
hook is installed; full original goal remains ACTIVE. No camera/card/stage/flash/push.

New orientation_sample.h preserves unknown native state; portrait_geometry.h
provides bounded exclusive-edge720x480/480x720 transforms for orientations1/2,
including output nonmutation and exact aliasing. A reproducible384-byte flat
diagnostic executes those helpers. Private orientation-01/result.json PASS13405:
9216 raw getter/normalizing-wrapper/sampler combinations,504 override/notification
cases and2604 valid compiled geometry round trips plus invalid/null cases.
Gate exactly1 selects supplied sensor; otherwise selectors1/2/3/4 map0/3/1/2,
selector0 is UNKNOWN4. Normalizing native wrapper maps4 to0 but is not established
as the graphics orientation getter. Physical IMU and live drawing remain unproved.

Original rectangle producer1042F5F6 reaches queued dispatcher10372390 through
103726B8. Graphics taskA1D75D34 has queue+20 and dispatch+2C, NOT Z7II+24.
Native101F2414 registration executes in graphics-queue-05/PASS27. Original
producer/enqueue/dispatcher/completion execute with supplied renderer/kernel and
serialized two-CPU schedule. Command42010017 is synchronous at the backend,
copies x/y/w/h plus two flag bytes and acknowledges42010062/0. Mode0 renders
directly. Failed01/02 expected the wrong completion event;03 bytearray transfer
fixture error;04 PASS26;05 adds registration and enqueue-self-link coverage.

See z7-native-modules/PORTRAIT_RESEARCH.md for exact bindings, scope and next work.
Need LCD target/output admission, image/text adapters, graphics task ownership,
reflow/navigation/settings and cleanup before portrait integration. Accepted
highlight host/module remain byte-identical to the previous checkpoint. Full
startup/writer/index/bank/engine lifetime, native Info mirror, real histogram
producer, integrated release and installation/recovery assessment remain open.

Validation: root71/no skips (20261120-orientation-root-tests.log); both final
audit source fingerprints match disk. Ignored Graphify updated3308nodes/8915edges
with new code present; existing preprocessor parser warnings retained. Source-only
summary: evidence/20261120-orientation-foundation.json. Probe SHA
cd8266b1e24f75aa06ebdb8098461a4a0a615e9330b74d05da25e0df3a826578.

## Cache-driven logical LCD/EVF handoff - November 20, 2026

Previous0fe3f8b was PROGRESS (API80 cache-copy host). This checkpoint is PROGRESS:
new display-highlight-handoff-probe uses actual API80 snapshots for baseline
acquisition and logical LCD/EVF round trips WITHOUT foreign display-parameter
packets. Full original goal ACTIVE. Native boot/pre-cold writer ordering, full
writer/index/bank/engine lifetime closure, physical pixels and installation remain
unproved. No camera/card/staging/flash/push. This is not a finished camera release.

Module20261120-display-highlight-handoff-03:
SHAea5ef0a4704897ebff6ca2baa447e842982c1baf6ae7597f4404cf300f49cd59,
32972file/32576image/7376BSS/minAPI80/reproducible;65 source inputs.
Paired photo-source host20261120-native-cache-host-05,
MAIN11933df6daf28d1f1988e72d070e84e2a958a229c36d47214b0c1af8bf999ca3,
33065600main/8453host/360state/384reserve/cold224slot/API80/reproducible/EGCRCzero.
Earlier EVF flag-OFF rebuild20261120-handoff-compat-evf-01 remains byte-identical
1fb3afc1f389c636d4bb681ce19cccc571593bd6b64747dc4a6191124b071c21.
New full API80 module rejects API72 before publication(status7/image0), verified
in20261120-handoff-api72-rejection-final.json. No generic cross-profile clearance.

Handoff macro ONLY appends cache_bound/baseline_foreign and44-byte snapshot to
lease record: record300/publication312 bytes, old baseline/params offsets60/160
unchanged. Two bounded consumer-written origin publications retain each output's
native baseline/context/cache binding. Older-output native baselines survive a
new native generation on the other output when their native request is unchanged.
Actual foreign native100 preserved exactly; cache-derived baselines convert the
native36-byte request at consumption. Changed native request supersedes old
cache binding. Palette changes reconvert cache-derived baselines, preserve exact
foreign payloads when raw request unchanged. Disabled cache ignores undefined
request tail and restores normalized zero100. Config/journal formats unchanged.

Worker still only queues/reaps, no conversion or native gate. It disables old
owned plane first, waits for acknowledgement, then applies target or restores its
native baseline if Off. Consumer confirms old disabled state/engine/register0
before retiring old frame-policy record. New actual frame supplies native policy;
no cross-output permission/frame pointer reuse. Global Off can restore an enabled
Nikon baseline under its native permission; it does not blindly force native Off.

Cache generation participates in owned frame permission. Cache-only update
inhibits old ownership before worker refresh. Busy cache queues owned disable
even if GUI still wants highlights, then waits without repeated requests. Cache
completion permits retry/restoration without GUI or native parameter update.
Queued apply with partial source cancels before100-copy; completed newer source
is reacquired at consumer. Cache observation exhaustion disables cache-bound owner
without stale restoration. A genuine native update can return native ownership.
Preflight rejects exhausted lease/origin publication identities before owned copy.
Snapshot validity still does NOT make later application atomic with cache writers.

.private/evidence/20261120-highlight-handoff-08.json PASS68: actual native cache
constructors before module load(supplied ordering), no-foreign-packet round trip,
all16 EVF choices, native source/frame/gate/driver enable effects, cache-only
baseline refresh, per-output exact foreign preservation, Off destination/native
permission, real partial memcpy with owned disable/retry, queued cancel/latest
source, Off during busy copy, counter exhaustion/native recovery, palette-derived
vs foreign distinction, undefined disabled request tail, movie-cache exclusion
and fresh-photo recovery. Engine/context/UI/FS/
kernel/palette/MMIO storage and schedules supplied. No physical mapping/pixels.

Audit01 fixture missed an already queued second-stage request; explicit pending
state consumption fixed02/PASS11. Module01's current-GUI disable condition would
reject cache-busy shutdown; corrected new-profile branch in accepted02. Audit03
PASS35;04 PASS51 adds all16 EVF choices;05 PASS59 adds pending-Off/exhaustion;
06 PASS63 adds palette and disabled-tail cases. Mode review found that raw
cache readiness lacked producer-mode tracking: host05 now stamps whether copy
begins/ends in photo0, clears bank readiness otherwise and requires currentphoto0
for capture/validation. API80/44-byte snapshot/state360 unchanged. Native cache
host audit08 PASS102, including mode rejection and copies spanning both mode
directions. Handoff07/08 PASS68 add photo/movie/photo native cache recovery.
Mode/index ABA and original producer semantic context remain unproved; stamps
sample boundaries, not task/allocation pins. Earlier host04 is NOT accepted for
this handoff pairing. The module packet stays identical;03 refreshes source
fingerprints for the updated SDK contract. Failed runs remain failed.

FINAL accepted pairing checks: native-cache-host-08/result.json PASS102;
highlight-handoff-08.json PASS68;handoff-transactions-02.json PASS41;
handoff-cleanup-02.json PASS28 +36owned;handoff-preferences-02/result.json
PASS609 codec +95native preferences. Root71/no skips:handoff-root-tests-final.log.
Host independent exact payload/report rebuild PASS:handoff-host-independent.json.
API72 flag-OFF host rebuildhandoff-compat72-host-02 remainsEF6F payload identical.
All final audit fingerprints,20 host and65 module inputs verified current; source
frozen during live runs. Ignored Graphify refreshed3273nodes/8820edges;
all3 new code files present. Source-only evidence:evidence/20261120-highlight-handoff.json.

NEXT: validate native pre-cold constructor/boot ordering and other writers/index
ABA/bank lifetime; broaden native lifecycle/pixel evidence and finish remaining
orientation/portrait, native Info mirror and real histogram producer. Final
integrated release and exact installation/recovery assessment remain required.
Do not redefine the full goal around the admitted logical shared-engine fixture.

## Native request cache bridges and SDK API80 - November 20, 2026

Previouse5114eb was PROGRESS (unwired observation core). This checkpoint is
PROGRESS: opt-in native copy bridges, API80 snapshots and actual loaded SDK probe.
Full original goal ACTIVE. Automatic no-native-update display handoff is NOT yet
wired into the functional display module. No camera/card/staging/flash/push.

NEW --native-cache-copy-hooks requires all API72 native warning transaction flags.
API80 extends72 with native_cache_snapshot(output,out44) and snapshot_valid.
Only output1/LCD and4/EVF, fixed native indices0/2. Requests remain36 bytes;
snapshot adds serial/bank. Capture uses staged local result, actual native getter
and volatile word copies, then generation validation. Failure never changes caller
output. Caller keeps snapshot unchanged. Validation is not payload authentication,
writer exclusion, allocation pin or atomic later parameter application.

State360: observation active336/serial340/halted344, completed-bank mask348,
guards352/356. Existing336 prefix preserved. Cold bridge224-byte slot; same384
reservation. Only TRACKED completed kind0 request copies make a bank ready; raw
unobserved initial cache data is rejected. Bridge spans constructor10433CEE and
setter10434910/1043494A/1043497E. Aligned LCD window8 bytes; others10 bytes,
reconstructing native loads/branches and extra constructor load/peaking stores.
Input registers/flags survive helper calls. Actual ARM memcpy executes even if
observation token0, halted or state invalid. Retire token then original post-copy
instructions; native caller request buffers stay immutable until copy returns.

Accepted host20261120-native-cache-host-04:
MAINe694ad92067a9c9d1233f2a71418c6093500d28d0586afede9840c97a8cee3b6,
33065480main/8333host/360state/384reserve/cold224slot/API80/reproducible/EGCRCzero.
20 current host source inputs. SDK probe192file/128image/16BSS, actual loader,
header/CRC/BSS/cache-maintenance and z7_main execute. API function pointers and
min80 gate verified. API80 probe rejects API72 cleanly with host status7/image0.
Flag-OFF API72 rebuild20261120-cache-compat72-host-01 byte-identical previous
MAINef6f1f703b87978336465452ee572f0b464fedfc37b90d4afb36c1ede6aaec1a.

.private/evidence/20261120-native-cache-host-06/result.json PASS97. All24 native
mask/pattern combinations match original full-bank bytes, return, NZCVQ andr1/r2/r3/r12;
normal callee-save/stack guards retained. Constructors include nonzero first/
zero second field to exercise displaced-load branch. Tests actual bridge busy
count across partial copy and overlapping HDMI writer, completed snapshots,
stale/tampered metadata, unsupported mapping/output/alignment, a complete writer
running between snapshot copy and validation, immutable failure output, exhausted
active/serial counters, halted/bad-state native fallback and actual cold hook
reservation/continuation. Kernel/FS/bank indices/task schedules supplied.

Build01 missing nested API base fixed;02 jump8 unaligned error fixed with native
10-byte windows;03 wrong saved begin destination (APSR inr0) found by snapshot
readiness, corrected explicit [sp+8]/[sp+16] reload in04. Audit01 overbroad write
logger affected loader stack observation; restricted to cache address range.
Audit02 exposed begin argument bug;03 overlap fixture overwrote paused source
buffer, corrected distinct immutable caller buffers;04 PASS91;05 PASS97 with
snapshot-in-progress and exhaustion additions;06 PASS97 also compares all caller-
scratch registers. No failed candidate is accepted.

FINAL new host + unchanged EVF module regressions:
20261120-cache-host-transactions-01.json PASS41;cache-host-evf-01.json PASS37;
cache-host-cleanup-01.json PASS28 +36owned;cache-host-preferences-01/result.json
PASS609 codec +95native preferences. This tests that exact supplied pair, not
arbitrary cross-profile compatibility. Root71/no skips:cache-host-root-tests.log.
Independent exact payload/report rebuild PASS:cache-host-independent-rebuild.json.
All audit fingerprints and20 host source inputs current, code frozen during runs.
Ignored Graphify refreshed 3244nodes/8711edges; new3 code files present.
Source-only evidence:evidence/20261120-native-cache-host.json. All jobs terminal.

NEXT: close pre-cold constructor/writer ordering, other writers and index ABA/
bank lifetime; integrate snapshots into native baseline acquisition and automatic
LCD/EVF handoff, including invalidation on cache-only updates and observation halt.
Do not treat snapshot validation as atomic commit. Existing native-update-driven
EVF module remains unchanged. Preserve all native baseline restoration and lane
contracts. Orientation/portrait, native Info mirror, real histogram producer,
full lifecycle and integrated installation/recovery assessment still required.

## Compiled cache write observation core - November 20, 2026

Previousac58cb1 was PROGRESS (native cache/torn-read proof). This checkpoint is
PROGRESS toward original full automatic LCD/EVF handoff: bounded atomic cache
observation core plus actual native setter AND constructor copy tests. Existing
firmware host, SDK/API72 and display module bytes unchanged. Full goal ACTIVE;
no camera/card/staging/flash/push. This core is NOT a finished producer binding.

NEW plugins/cache_observation.h keeps active/serial/halted in12 bytes. Every
covered writer begins before its complete request write, returns token1, and
retires it once afterward. Active counts overlapping/nested writers; serial
advances on begin/end. Reader obtains ticket, copies data, then validates ticket
with active0 and matching non-exhausted serial. Bounded3-CAS retries; exhaustion,
unbalanced/invalid retirement or retry failure halt observation without counter
reuse. Token0 never denies the original native write. There is NO reader lock,
writer exclusion, native bank/allocation pin or later-application atomicity.
Integration must drain owned features when observation halts and cover every
writer; copying still needs the proper volatile/native ordering contract.

New original-Z7 constructor10433C78 also copies request36 at10433CEE, besides
regular writer104348E4 at10434910/1043494A/1043497E. It initializes header/other
fields separately. A regular-setter-only hook would miss request initialization.
Direct-BL scan and PC-relative literal scans are research leads, not full writer/
indirect caller closure. INDEX initialized bytes observed0000010002020000;
index immutability and all transitions remain unproved. Future host must close
constructor/init, normal writers, index lifetime and activation before snapshots.
Existing early cold-state reservation precedes native workspace allocation;
validate its ordering against all cache initialization before using it to seed
observation. Avoid synchronous producer queue waits inside native consumer.

.private/evidence/20261120-cache-observation-03/result.json PASS48 checks.
Probe576file/512image/0BSS/0relocations/reproducible. Compiled ARM atomics plus
original native setter and constructor/memcpy execute. At output1 and4 both
writers pause before request memcpy and after16/36 stores. Two equal raw reads
are torn; compiled observer rejects ticket and stale generation; resumed writer
keeps stack/callee-saves, completion admits fresh generation. Covers overlapping
writers (even serial still busy), balanced retirement, inactive/no-token behavior,
invalid/unbalanced token halt, active overflow, serial exhaustion/nonreuse and
native writes continuing after observation halt. Observation begin/end boundaries
are supplied by audit, NOT installed firmware hooks; flat zero-relocation probe
load is NOT module loader validation.01 missing fixture memory helper corrected;
02 PASS48;03 adds complete direct build-input fingerprints/PASS48.10s/10M guards.
All source hashes verified current. Root71/no skips:
20261120-cache-observation-root-tests.log. Ignored Graphify refreshed
3225nodes/8635edges; all3 new code files present.

Details:z7-native-modules/Z7_HIGHLIGHT_CACHE_RESEARCH.md; source-only evidence
`evidence/20261120-cache-observation.json`. NEXT: wire complete request-copy spans
into opt-in host bridges, establish early activation and bank/index/writer closure,
then expose coherent native requests for automatic baseline/handoff integration.
Native-update-driven EVF remains the latest functional module. All other original
ports/lifecycle and integrated installation/recovery requirements remain open.

## Native highlight cache binding and torn-read proof - November 20, 2026

Previous3362f4f was PROGRESS (native-update-driven EVF). This is PROGRESS toward
full automatic output handoff, not a new narrowed goal. No firmware/module/host/
SDK change this checkpoint. No camera/card/staging/flash/push.

Original getter10434CEE(kind0,output1/2/4) returns native request36 at bank+58.
Helper10433B80 uses INDEXA180F274[output], CACHEA1F18FC0, strideE84. Writer
104348E4(outputmask,kind0,request,submit0) performs native36-byte memcpy for
selected bits1/2/4 and clears bank+40 only if request enabled. All masks0..7,
patterns0/1/2, nonzero-kind rejection, mutable indices and aliasing checked.
Getter(output0,kind0) returns58 rather thanNULL: restrict supported outputs.
Physical bank count/index writers/allocation bounds/lifetime remain unproved.

CRITICAL: actual native memcpy paused after16/36 stores yields TWO EQUAL reads
that are neither complete old nor complete new request. Writer resumes in its
saved ARM state and returns with original stack/callee-saves. Thus repeated
stable byte reads are NOT a coherent baseline snapshot. Cache-only writes also
occur without display-queue submission. Do not implement automatic handoff by
merely polling the getter or double-reading its returned pointer.

.private/evidence/20261120-highlight-native-cache-03.json PASS60 native checks;
source hashes verified current.01 reached resumable native memcpy but the test
incorrectly forced Thumb on ARM resume;02 fixed saved-state resume/PASS40;03
adds all output masks/nonzero kind/output0 boundary/PASS60. Guards remain10s/10M.
Kernel queue/mutex boundaries must NOT be reached for submit0. Native getter,
writer and memcpy instructions execute; incoming indices/requests/palette and
explicit task schedule supplied. No physical coherence/caller closure claim.

Root71/no skips:20261120-native-cache-root-tests.log. Ignored Graphify refreshed
3199nodes/8560edges; new audit present.
Details:z7-native-modules/Z7_HIGHLIGHT_CACHE_RESEARCH.md. Sanitized source-only
summary:evidence/20261120-highlight-native-cache.json. Existing EVF/API72 pair
and baseline-restoration behavior remain unchanged. Next: close native cache
writers and bank-index transitions, then establish writer exclusion or complete
producer publication before consuming per-output requests for automatic handoff.
Avoid synchronous native queue waits in the parameter consumer. Full original
remaining ports, native lifecycle and installation/recovery requirements ACTIVE.

## Native-update-driven EVF highlight path - November 20, 2026

Previous e47e58e was PROGRESS (persistent LCD highlight preferences). This
checkpoint is PROGRESS toward the SAME full display-port goal: new opt-in
`display-highlight-evf-probe` admits logical EVF native/owned photo requests after
an observed matching native parameter update. This is NOT the complete EVF port.
Automatic handoff without a new native update, native producer binding,
orientation/portrait, Info mirror, real histogram producer, full caller/task/
engine lifetime closure and final integrated installation/recovery remain open.
No camera/card/staging/flash/push. Emulator results do not prove camera pixels,
physical output mapping, updater acceptance or recovery.

Original routing distinguishes rear-monitor and EVF16-byte source tags. Logical
EVF uses kind2/selector1/source output2/converter output4/command42062007; LCD
kind1/selector0/source output0/converter output1/command42060007. New EVF UI
admission requires photo mode, scene2, no movie/menu/playback/transient UI and
valid native context. EVF follows global pattern/threshold and Custom enable;
it ignores the LCD page checkbox. First EVF color is13, other group15; LCD15/15.
No foreign firmware addresses were copied into this independent Z7 port.

A bounded copied native-origin publication records context/generation/baseline
before optional conversion. Native updates in mismatched modes/outputs or NULL
notices retire origin. New owned claims require a matching observed origin and
current baseline (disabled tail is undefined and normalized). This also means
initial LCD ownership waits for a native update in THIS experimental profile.
Switching away disables the old owned plane, keeps its lease and waits rather
than interpreting the other display's shared parameters as a new native baseline.
Matching native updates replace the old lease; observed native updates before GUI
eligibility can support later owned work. Preferences still use asynchronous
worker requests and consumer-only conversion/cleanup. Native producer binding
is needed to finish immediate/no-packet output transitions; do not silently
substitute this narrower event-driven path for the full EVF requirement.

Module .private/builds/20261120-display-highlight-evf-01,
SHA1fb3afc1f389c636d4bb681ce19cccc571593bd6b64747dc4a6191124b071c21,
31692file/31296image/6936BSS/minAPI72/reproducible,62 source inputs.
Host remains20261120-native-transaction-host-04,
MAINef6f1f703b87978336465452ee572f0b464fedfc37b90d4afb36c1ede6aaec1a.
Previous preference profile rebuild20261120-evf-compat-preferences-01 is byte
identical99d5f7357a1fd5c4b369837ddccd304d9b6a22ee0da1a00829d1cd5739c2a795.

EVF audit04 passes37 checks: all16 enabled choices match independent output4
requests, actual source/frame/gate/driver/register effects, output-switch disable
and waiting, native baseline restoration, update-before-GUI, global EVF/page-mask
separation, movie exclusion, disabled-tail normalization and busy-publication
parking. First audit used incorrect raw lease selector offset48; corrected to40
before accepted evidence. Cleanup01 exposed an older fixture assumption that
movie parameters could be reused as a photo baseline. The new-profile branch
explicitly checks waiting for a fresh photo native update (same bytes allowed)
then retains original frame-capture/cleanup assertions. Older profile unchanged.
Cleanup02 completed behavior checks but the separate ownership fixture hit its
30s pure-C module CRC observation timeout. AdmittedOwnedFixture now uses the
same validator-only Python-dispatch fast path as CleanupFixture; all ARM CRC/
header/relocation instructions and original30s/10M guards still execute.
Supplied boundaries remain kernel/FS/UI/colors/surfaces/context/source schedule,
same shared engine/MMIO storage. No engine lifetime or physical EVF claim.

FINAL evidence: .private/evidence/20261120-highlight-evf-04.json PASS37;
20261120-evf-preferences-02/result.json PASS609 codec +95 native preferences;
20261120-evf-transactions-02.json PASS41;20261120-evf-cleanup-03.json PASS28
cleanup +36 owned. Root71/no skips:20261120-evf-root-tests.log. All result source
hashes and62 module inputs verified current; fingerprinted inputs stayed fixed
during live audits.
Ignored Graphify refreshed:3180nodes/8505edges; new EVF
files verified present. Source-only summary:evidence/20261120-highlight-evf.json.

NEXT: native parameter-producer/output-transition binding. Preliminary direct-BL
scan found caller1034FF1E at1035183C/1035189E/10351900/103542E6. Nearby native
output4 path fetches request via10434CEE before submission; investigate that
getter, ownership/locking and producer lifetime before any baseline acquisition.
This scan includes data and is NOT indirect-caller closure. Preserve previous
profiles, native baseline restoration and the native transaction contract.

## Highlight preferences and settings version2 - November 20, 2026

Previousa9e7b86 was PROGRESS (native warning transaction API72). This turn is
PROGRESS: global pattern/threshold menu, captured native requests and persistence
migration implemented in a NEW opt-in display-highlight-preferences-probe. Full
original goal ACTIVE; no camera/card/staging/flash/push. Physical menu/overlay
raster, card durability, native lifecycle and installation/recovery remain open.

Pinned private z7ii-50a22b2/sdk/photo_zebra.h confirms global patterns0 Off/1/2,
threshold indices0..7 ->255,248,235,224,213,202,191,180; native request pattern
bytes0/1. Independently constructed original-Z7 requests retain LCD palette15,
groups255/threshold/15/5 and4x4. No foreign Nikon addresses installed. Current
fixed defaults1/248 preserved (index1). Global pattern0 makes wanted=false;
owned worker restores latest Nikon baseline rather than submitting an override.

Z7_HIGHLIGHT_PREFERENCES only in new variant. Settings model adds2 words48bytes;
wire stays64. Optional Z7C1 version2 reuses reserved words56/60 for pattern and
threshold index. Strict range/CRC/schema validation, staged decode/output and
legacy version1 zero-reserved acceptance defaults1/1. All existing flags, masks
and4 page selections preserved. Journal Z7J1 envelope remains80/version1 with
same native I/O, two slots, CRC, verification and worker. Startup does NOT write
migration. A later real settings edit saves canonicalv2 into the other slot.
Older variants stillv1 and CANNOT decodev2; do not mix journal/module versions
without a reviewed rollback/configuration plan. No actual card migration done.

Preset Highlight row5 now opens view4 only in new variant. Row0 Show on this
page toggles that preset's component bit; row1 Pattern (all pages) cyclesOFF/
Type1/Type2; row2 Threshold (all pages) cycles8 values; row6 Back and native Back
return to owning preset row5. Existing7-row layout/label pool reused; blank rows
stay blank. Global style/threshold survive page toggles/preset reset. Menu is
sole settings writer; GUI actions do no file I/O. Native label slots/focus tested,
new text raster NOT yet inspected. Existing variants unchanged when macro OFF.

GUI publication captures validated pattern/threshold (or safe invalid-view
values) in its bounded snapshot. Epoch includes new fields and settings revision.
Owned and foreign conversion build request from CAPTURED snapshot, not mutable
menu globals. Current-state recheck precedes native payload copy. Style changes
before GUI publication invalidate pending work; worker reaps/retries latest epoch.
Lease continues retaining original/latest native baseline across preference edits.

FINAL module .private/builds/20261120-display-highlight-preferences-01,
SHA99d5f7357a1fd5c4b369837ddccd304d9b6a22ee0da1a00829d1cd5739c2a795,
30988file/30592image/6680BSS/minAPI72/reproducible;61 source inputs current.
Host UNCHANGED20261120-native-transaction-host-04,
MAINef6f1f703b87978336465452ee572f0b464fedfc37b90d4afb36c1ede6aaec1a.
Old72 module rebuilt20261120-preferences-compat72-module-01 exact
b918362c22da8b1b2d92fe6337e3e12e4680a22e39924b7a6a30e28692236fc0.

.private/evidence/20261120-highlight-preferences-03/result.json PASS609 codec +
95 preference integration on final pair. Model probe1536bytes/image1472 executes
compiled C; independent Python CRC/wire checks cover24 valid pairs, v1 forward
migration preserving existing fields, canonicalv2, sealed invalid schema/ranges,
all512 single-bit damage cases, invalid lengths/nonmutation and global prefs
across preset reset. Native profile exercises submenu enter/Back/focus/text slots,
16 enabled pattern/threshold choices ->actual converter/consumer/driver/MMIO
field checks, current preferences on foreign native update, globalOff restoration
of latest native baseline, per-page toggle/global-choice separation, queuedold
preference cancellation BEFOREcopy after a menu edit, retry newer captured choice,
worker v2 save in80B record, first migration save preserving legacy slot and
restart reload. UI/FS/kernel/colors/surfaces/engine/context/MMIO supplied.
01 failed test bytearray input type for Unicorn;02 PASS609+91;03 adds4 stale-
queued/retry cases, bounded menu-cycle helper and probe fingerprint/metadata.
Production bytes unaffected by those test corrections.

20261120-preferences-transactions-01.json PASS41 native transaction regressions
on THIS preference module.20261120-preferences-cleanup-regression-01.json PASS27
cleanup/publication +36 owned. OwnedFixture.toggle now selects the preference
variant's actual view4/row0 via report metadata; old variant stillview1/row5.
Cleanup CLI admits explicit preference kind with same API72 host requirements.
Original30s/10M guards retained; all jobs terminal. Source hashes in all results
and final module inputs verified current. Root71/no skips:
20261120-preferences-root-tests.log. Ignored Graphify refreshed3160nodes/
8443edges; all3 new code files present. Source-only evidence:
evidence/20261120-highlight-preferences.json.

NEXT: continue full remaining display ports, especially EVF/native preservation
and orientation/portrait paths, native Info mirror and real histogram producer.
Inspect new preference UI raster in assisted native rendering when applicable;
physical camera appearance remains a separately authorized hardware test. Retain
API72 caller/writer/math-task/lifetime and fixed consumer-only borrowed-gate
contracts. Do not have GUI/style controls directly call native gate; they use
asynchronous owned requests. Final integrated release candidate and exact
installation/recovery assessment still required; no flash clearance or push.

## Native warning transactions API72 - November 20, 2026

Previous0c49637 was PROGRESS (owned-only API64, foreign race reproduced). This
checkpoint is PROGRESS: identified warning gate plus qualified foreign100-copy
transactions integrated. Full original software/display-port goal ACTIVE. No
camera/card/staging/flash/push; no pixel, installation or recovery clearance.
Physical native caller/writer/task/allocation closure remains unproved.

NEW sdk/native_warning_transaction.h API72 extends64 with init-only activation
and owned_warning_available(). Host --native-warning-transaction-hooks requires
all64 flags; new display-highlight-native-transaction-probe opts in after prior
registrations. State336: Native flag324/guards328,332; preserves324 prefix;
reserve384/cold192. New fields/lane reads use acquire/release atomics.
Exact paired bundle only: old64 host+module rebuild unchanged with new flag OFF;
old64 module on new72 host is UNVALIDATED. Prefix layout alone is not a claim
of cross-profile behavior. New72 frame admission spans the warning gate, not
API64's whole frame bodies. Native frame entries themselves remain original.

New primary/cached bridges elide their state+20 permission stores; fresh input
is re-read/filter-stored under native GATE1023B76E ownership immediately before
original gate body. Cached NULL uses existing state and retained original policy.
Native LR1023BABD/1023D895 identifies primary/cached frame and original r5/r4
inputs; all input registers/flags preserved through C helpers. Gate body original
10-byte prologue reconstructed with format4 branch. Module gate calls under
PARAM role borrow that transaction (caller must be resident module executable).
This assumes the FIXED module calls original gate only from consumer callbacks;
module text bounds are NOT per-task authorization for arbitrary new callers.
Keep future GUI/worker code on the asynchronous request path, not direct gate.

Consumer bridge now owns an8-byte LOCAL stack slot {token,packet}, pointer r8.
Registered owned descriptor remains nonblocking cancel/retry. Qualified foreign
aligned camera-RAM descriptors, commands42060007/42062007 with matching sampled
selector/service1..4, yield delay1 until gate releases BEFORE module callback.
Other requests keep original native dispatch. Original dispatcher checks service
<5; group0/op6 table0 NULL and1..4 all1023E215. No unidentified service handler
is admitted deliberately. Native service/context state is sampled, not pinned.
Completion102396C0 shim saves all regs/flags, RELOADS original packet [sp+8],
passes slot to helper, restores native prologue. Foreign slot token is zeroed
BEFORE release and original callback. Late consumer return checks local zero,
not stale r7. Owned retains token through native completion and module after-
consumer cleanup. New bridge code never accesses foreign caller payload/
descriptor memory after the original completion callback.
Native completion reentry can run frame or foreign consumer with a new slot.
Before-consumer callbacks still MUST NOT dispatch recursively/wait (API52 rule).

Near generation0xfffffff0 query returnsfalse, highlight_current becomesfalse,
owned frame policy inhibits and worker restores captured native baseline. At
idle0xfffffffc native traffic AND owned restoration use a terminal lane with
phase3/owner publication; tokensfffffffd/frame,fffffffe/parameters can REPEAT.
Counter never wraps/resets. Terminal correctness depends on closed native bridge
lifetimes (slot retirement before release, one final gate leave), not globally
unique generations. Core generic lane remains unchanged and refuses exhaustion.
Injected terminal cycles and delayed original return are tested; physical timing
and arbitrary external token misuse are not proved.

FINAL host .private/builds/20261120-native-transaction-host-04,
MAINef6f1f703b87978336465452ee572f0b464fedfc37b90d4afb36c1ede6aaec1a,
C7521/API72/state336/reserve384/reproducible/EGCRCzero.
Module20261120-display-highlight-native-transaction-02,
SHAb918362c22da8b1b2d92fe6337e3e12e4680a22e39924b7a6a30e28692236fc0,
30404file/30080image/6616BSS/minAPI72;60 current source inputs verified.
Module01 is same bytes,02 refreshes SDK comment/source hashes. Host01 had broken
completion packet handoff (R0 contained saved APSR), exposed by actual native
callback reentry;02 fixes [sp+8] reload;03 adds atomic shared reads;04 limits
foreign admission to identified matching selector/service handlers. Only04 is
accepted for this checkpoint. Prior64 compat host02 MAIN8c12dc12...cef438e6 and
compat64-module01 SHA4d83e278...eab0380c match prior exact accepted payloads.

.private/evidence/20261120-native-warning-transaction-05.json PASS41 FINAL pair:
SOURCE/cached fresh/NULL old frame pauses at real enable, foreign request yields
without copy/ack/lease invalidation, frame completes, native consumer quiesces,
copies/acks/retires, settled frame staysOff. Owned busy cancellation retained.
Reverse foreign copy pause: all three frame gates reject without permission
store or warning programming. Actual supplied ARM completion thunk reenters
frame+consumer. First consumer paused after token retirement, second owns lane,
first late return cannot release second. Native earlier mutex boundary pause
holds no warning token and foreign consumer completes; post-gate old frame tail
cannot resurrect disabled plane. Injected near-exhaustion inhibits owned plane,
worker restores baseline;3 terminal native frame/completion/reentry cycles run
without wrap. Kernel/FS/UI/surface/color/engine/context/MMIO/schedules supplied.

20261120-native-warning-host-04/result.json PASS22 FINAL host: cold336/reserve384/
guards/allocator; activation prerequisites/single/init-only; module PARAM gate
borrow versus native frame rejection; unrelated completion cannot release;
retired slot protects later gate; sampled out-of-service/wrong-selector passes
native; terminal slots/counter/old-return; failed init clears flags/callbacks;
preactivation gate token blocks init and survives failed load; retry after leave.
Host audit03 attempted to remap parent's existing service RAM; corrected test
setup in04. Fresh-open offset0 is explicitly supplied for loader retry.
20261120-native-transaction-cleanup-regression-03.json PASS27 cleanup/publication
plus36 owned on FINAL pair. Existing30s/10M guards retained. CLI admits72 only
with native transaction flag. 20261120-native-transaction-api64-rejection.json:
module72 rejects host64 before feature publication. Root71/no skips:
20261120-native-transaction-final2-root-tests.log.

Native audit01/04 and cleanup regression02 hit ORIGINAL30s CRC wall cap during
layered fixture dispatch/concurrent work; known sessions exited, no blind restart.
Final CleanupFixture bypasses ONLY Python model dispatch inside the pure compiled
z7_module_validate..prepare code span, where no modeled service boundaries exist.
ALL CRC/header/relocation ARM instructions still execute; no validation shortcut,
instruction budget change or wall limit increase. Transaction bootstrap invokes
this lean Cleanup hook before load. Final05 and cleanup03 ran serially. Earlier
transaction02 found actual completion reentry bug; intermediate03 passed41 on
host02. Those results are NOT final04 evidence. Final source/build hashes checked.

Source record:evidence/20261120-native-warning-transactions.json. All jobs terminal;
ignored Graphify refreshed3137nodes/8359edges, all5 new code files present.
Preliminary private CFG gate scan unresolved tables/math/returns is NOT closure
proof. Native math/task wait graph, indirect callers/writers, pre-cold sequencing,
engine allocation/lifetime and physical pixel/update/recovery gaps remain.

NEXT software: finish API72 cached original-policy/unsupported-context regression
coverage as needed, then highlight style/threshold settings from pinned Z7II
source, EVF/orientation handling, native Info mirror and real histogram producer.
Keep original full display-port scope. Continue native lifecycle/caller research
where required for safe bindings; distinguish software proof from hardware gaps.
Actual camera pixels/update acceptance/recovery require later separately authorized
hardware work and an exact-candidate installation/recovery assessment. No flash
clearance follows these emulator results; no push authorization.

## Owned/frame exclusion API64 - November 20, 2026

Previous6afdbd2 was PROGRESS (counterexample/core primitive). This checkpoint is
PROGRESS: native owned/frame exclusion integrated and tested; FOREIGN ordering
still unsafe under a supplied schedule. Full original goal ACTIVE. This is an
intermediate diagnostic, NOT a deployable/flash-ready profile. No camera/card/
staging/flash/push. All jobs terminal when saving checkpoint.

NEW sdk/owned_frame_coordination.h API64 adds init-only enable after all cached/
primary/parameter/highlight callbacks. Host --owned-frame-coordination-hooks
requires all API60 flags. State324: enabled304/lane.state308/lane.owner312/
guards316,320; reserve384/cold192. Cold and seeded fixtures support both guards.
Init activation must acquire idle lane, so an older tracked native frame blocks
activation. Native frame tracking starts after cold-state validity even before
opt-in. Failed initialization clears flag/callbacks but NEVER resets lane state;
old frames retain/release exact generation-qualified token. Pre-cold boot caller
closure is unproved. Existing API60 host payload/module rebuild byte-identical.

Whole-frame entry wrappers1023B9D0 and1023D794 save AAPCS state, use outer SP as
owner, acquire frame role before original bodies, retain token through EVERY
native return and release after original native work. Busy returns native0
without original body. Original8-byte prologues reconstructed with verified
literal values and flags (cached MOVS r4,r0). Consumer bridge acquires parameter
role ONLY for registered owned descriptor before module before-consumer; holds
through original copy/ack/completion and module after-consumer cleanup. Busy
owned work still enters helper/claims request, changes accepted decision1 to
cancel2, calls original completion with ack0 and normal module after/cancel.
Worker reaps/retries. Park/reentry/fallback release only acquired tokens; busy
UINT32_MAX is never a release token. Module after-consumer ends request accesses
before worker reuse; host final leave reads only immutable packet identity.
No owned path waits for earlier native frame mutex. FOREIGN descriptors retain
original path and remain uncoordinated. No indirect native gate closure proof.
Generation exhaustion returns busy forever to frame/owned admission; core never
wraps, but shutdown handling is UNFINISHED. Must resolve before deployability.

Final host .private/builds/20261120-owned-coordination-host-02,
MAIN8c12dc12d2466fdb5677e580bea2e28a32a8fb9fa6905d6b7b8f8d46cef438e6,
C6341/API64/state324/reserve384/reproducible/EGCRCzero.
Module20261120-display-highlight-coordinated-01,
SHA4d83e278e41d40f7d2f174c3bd18a1379006919c8782823574b79161eab0380c,
30340file/30016image/6616BSS/minAPI64;58 source inputs verified current.
Initial host01 compile failure missing nested api.cached prefix corrected in02;
no failed artifact was accepted. Existing API60 compatibility host
20261120-owned-coordination-compat60-host-01 MAINa905e50c63b6c9de8922cd27a8b09ab29b8012f0ae5dce1c228af7d6233f0eb6;
compat60-module-01 SHA6a5b066b1aa6f9212b01b30e63f44ed715f79d9f297bff298e02cb00d9af4cd4. Payloads checked against prior accepted fingerprints.

.private/evidence/20261120-owned-frame-coordination-02.json PASS34 exact pair:
cold/all guards/neighbor bounds; SOURCE, cached fresh and cached NULL pause at
real enable driver with frame lane held; Off cancel/ack0 without copy/lease
release/cleanup-success; resume native frame/correct SP+callee regs; worker retry
restores baseline and disables actual register, settled frames stay Off. Reverse:
owned cleanup paused at real100-copy, all three frame entries return native0
without input/state/register mutation for three flag patterns; resumed consumer
copies/restores/disables/retires correctly. Kernel/FS/UI/surfaces/colors/engine/
context/MMIO/explicit two-stack scheduling supplied. No physical schedule proof.
Native audit01 reused a cold-reset fixture without boot loader field init; this
TEST setup was corrected to separate cold reservation from initialized loader.

20261120-owned-coordination-host-03/result.json PASS12: prerequisite/single/init-
only activation, frame reentry, stale/wrong identity, new guards, foreign helper
pass-through, generation exhaustion refusal, failed init after activation frees
and clears, preactivation frame blocks init without token reset, retry succeeds
after frame returns. Fresh-open file offset0 explicitly supplied for retry.
01 failed due fixture file position not reset between fresh opens;02 PASS12;
03 removes assertion of unspecified return value from void leave helper.
20261120-owned-coordination-cleanup-regression-01.json PASS27 cleanup/publication
plus36 owned on exact API64 pair. CLI now admits this compatible diagnostic kind
and requires its explicit host flag. Original30s/10M guards retained.
20261120-owned-coordination-api60-rejection.json verifies API64 module rejected
by API60 before feature publication. Root71/no skips:
20261120-owned-coordination-final-root-tests.log.

CRITICAL .private/evidence/20261120-foreign-frame-interleaving-01.json reproduces
FOREIGN gap in4 checks on exact new pair. Pause SOURCE at real enable with frame
token held, turn feature Off, execute original foreign parameter request to
native copy/ack/completion. Old lease released, parameters disabled and real
control0; frame token unchanged. Resume old frame: actual enable1/active1 with
disabled params and invalid lease, correct native SP/callee and token release.
passed=true means COUNTEREXAMPLE, foreign ordering safe=false. This cannot be
counted as a completed full native concurrency fix. Source inputs/results hashes
verified current. Source record:evidence/20261120-owned-frame-coordination.json.

NEXT: coordinate foreign parameters while preserving native ordering, packet
lifetime, completion and callback reentry. Do NOT merely block consumer behind
the entire frame before proving its waits cannot require that consumer: native
frame1023A3DE takes A1D6AB80 via infinite-timeout10170944/kernel100361E8; gate/
parameter core itself has no observed wait, but complete transitive closure is
unproved. Consider a safely admitted narrower warning transaction or prove the
whole wait graph. Parameter handler copies100 at1023E226, sets dirty/ack at
E22A..E232, calls potentially reentrant completion atE236; any early release
must retire its token to avoid late release of another owner. Also implement
lane exhaustion feature shutdown, indirect/native gate caller closure and boot/
failed-init concurrency coverage before treating the profile as complete.
Then actual warning rendering/pixels, style/threshold preferences, EVF,
portrait/rotation, native Info mirror, real histogram producer, full lifecycle/
engine lifetime and exact-candidate installation/recovery. Full scope unchanged.

Ignored Graphify refreshed3111nodes/8272edges; all6 new code files present.

## In-flight ordering counterexample and lane primitive - November 20, 2026

Previous3096ba8 was PROGRESS (cached primary API60). This turn is PROGRESS:
concrete supplied concurrency counterexample and a compiled ownership primitive.
Full goal ACTIVE. NO native fence integration or flash readiness claimed.
No camera/card/staging/flash/push. Accepted API60 binaries have not been changed.

.private/evidence/20261120-gate-interleaving-01.json reproduces the API60 gap in
5 checks on exact cached-host-02/display-highlight-cached-03. Pause SOURCE frame
on CALLER_STACK at actual DRIVER10241A0E immediately before enabled1 write;
run Off GUI/worker/consumer on separate default STACK. Cleanup reports done1,
restores baseline100, invalidates lease and leaves hardware enable0. Resume old
native frame: callee regs/SP return correctly, but enable register and active
state become1 again, with baseline still restored and lease invalid. Native
gate/consumer/driver/register instructions execute; explicit two-stack schedule,
kernel/services/context/engine/MMIO supplied. Physical reachability/shared lock
closure NOT proven. Result passed=true means counterexample reproduced, NOT
ordering-safe. Source hashes verified current at this checkpoint.

NEW host/highlight_lane.h is NOT included by z7_380.c and NO native hook uses it.
8-byte {state,owner}, low state bits0 idle/1 frame/2 parameters/3 transition,
nonrecycled generation in upper bits. CAS admission first claims transition,
publishes owner then release-publishes token. Release validates owner/token,
CAS-claims transition, clears owner then release-publishes next idle generation.
Same owner address cannot let an old token release a new operation (ABA).
Busy/reentrant entry returns0; final idle0xfffffffc refuses admission forever,
never wraps/resets. Future integration MUST handle exhaustion via feature
shutdown and retain tokens through LAST native accesses. CAS uses compiler
strong-exclusive retry, no wait/yield on another lane owner. No allocation pin,
callback authorization, task lock order or native correctness claim from core.

Diagnostic examples/highlight_lane_probe.c + tools/audit_z7_highlight_lane.py
compile original C to Thumb and execute in NativePNG; no native hook registers.
Final .private/evidence/20261120-highlight-lane-03/result.json PASS56: role/owner
validation, frame/parameter exclusion/reentry, wrong/stale release rejection,
reused-owner address token generation, interrupted admission/release both after
transition claim AND after owner publish/clear, independent-stack ABI, final
generation/exhaustion. Kernel scheduling/interruptions supplied. 01 exposed a
TEST expected-generation count error (expected20 vs actual16 after 4 releases);
fixed test arithmetic; 02 PASS34; final03 adds owner-store interruptions PASS56.
Ignored Graphify refreshed3079nodes/8155edges; all four new code files present.
Root71/no skips:20261120-lane-root-tests.log. No accepted feature suite rerun or
native stale-frame fix claimed. Source record:evidence/20261120-highlight-ordering-lane.json.

Native review constraint: frame1023A3DE takes mutexA1D6AB80 via10170944;
wrapper calls kernel100361E8 with timeoutFFFFFFFF. Original frame releases this
mutex before permission capture/gate. A whole-frame lane acquired BEFORE that
wait needs a proven wait graph before foreign consumer waiting can be safe.
Gate1023B76E and color getter10243D82 contain no observed blocking in their
reviewed bodies, but complete transitive closure is still unproved. A narrower
warning-permission-through-gate span may avoid the earlier mutex; this is a
candidate design, NOT implemented or a completed closure proof. Parameter
handler1023E214 does 100-copy atE226, dirty+ack atE22A..E232, completionE236.
Foreign completion can be an arbitrary callback: release must precede callbacks
that could reenter rendering, and no old leave may release a later transaction.

NEXT: wire correct native frame/parameter coordination using this primitive or
a better design. Preserve foreign native requests, owned cancellation/retry,
original ABI/flags, startup/failure and exhaustion behavior; rerun the actual
stale-frame schedule against the integrated build plus reversed/interrupted
schedules. Primitive checks are NOT a replacement for these native tests.
Then actual warning pixels, style/threshold preferences, EVF, portrait/rotation,
native Info mirror, real histogram producer, full lifecycle/engine lifetime and
exact-candidate installation/recovery. Full original software goal unchanged.

## Cached primary path API60 - November 20, 2026

Previousc32dcff was PROGRESS (no-frame consumer cleanup). This turn investigated
caller/lane assumptions and found/fixed another native path around API56 gating.
Full goal ACTIVE. Native source/parameter shared lane or locks STILL UNPROVEN.
No camera/card/staging/flash/push; no physical pixels/installation clearance.

Native cached primary1023D794 stores metadata+30 into state+20 at1023D82E, then
calls warning gate at1023D890. NULL input bypasses metadata and uses cached state.
This NEVER passes original primary1023B9D0/permission hook1023BAB0. Focused audit
reproduces accepted API56 module re-enabling old owned params after primary Off
filter cleared the real MMIO enable. Original direct gate-call candidates are
1023BAB8 and1023D890, both now filtered in new opted-in profile. Indirect/native
caller closure not proved. Private branch refs:highlight-lane-xrefs.json.

New sdk/cached_frame_permission.h API60: frame56 prefix +init-only resident cached
callback. Fresh fields pointer is native frame+4 metadata (format+1/permission+30),
NULL provides NO new original input. Decision0 preserve/1 enable/2 inhibit. Host
--cached-frame-permission-hooks requires all prior flags; state304 preserves288
prefix, cachedCB288/running292/guards296,300; reserve320. Native cold/allocator and
all prefix/tail guards tested. Invalid field range, callback/guards, reentry and
nonboolean native permission delegate. Failure clears all callback state beforefree.

Exact10-byte bridges1023D82A and1023D88A: fresh metadata filters before store;
NULL recheck filters immediately before native gate. Native gate veneer uses BL
local tail stub, preserving R12 input, resets LR to original1023D895 on return.
Native result/volatile+callee regs/SP/NZCVQ fallback compared for NULL/nonNULL,
three flag patterns. Earlier API56 host/module remain byte-identical when disabled.

NEW display-highlight-cached-probe includes full cleanup API56 stack +registration
before startup I/O. Fresh fields feed common permission policy, reading only
format atfields+1 (no preceding bytes/no retained pointer); NULL skips capture.
NULL cannot overwrite original native0/1 with filtered1/0. Same engine/context
native parameter handoff retains original frame policy, including native inhibit2.
A NULL-only refresh without known original policy inhibits rather than creating
untracked owned plane. Fresh cached metadata can establish original policy without
primary-frame input. Off cleanup restores latest baseline/native permission even
following cached-only presentation. Menu/movie changes rechecked before GUI/worker.

Final host .private/builds/20261120-cached-host-02,
MAINa905e50c63b6c9de8922cd27a8b09ab29b8012f0ae5dce1c228af7d6233f0eb6,
C5777bytes/API60/state304/reserve320/reproducible/EGCRCzero.
Final module20261120-display-highlight-cached-03,
SHA6a5b066b1aa6f9212b01b30e63f44ed715f79d9f297bff298e02cb00d9af4cd4,
30340file/30016image/6616BSS/minAPI60;56 source inputs verified current.

.private/evidence/20261120-cached-frame-03/result.json PASS61 exact final pair:
cold/allocator, registration/ranges/guards/reentry/cleanup, delegated cached native
ABI, API56 rejection, OLD bypass reproduced, native cached fresh/NULL path actual
register effects, original policy across fresh+NULL and native updates, explicit
inhibit2 retention, first cached presentation and no-frame cleanup, menu/movie.
Kernel/FS/UI/surface/colors/engine/MMIO/context/task scheduling supplied. Focused
01 PASS51 intermediate;02 PASS59 added policy-retention cases;03 final61 adds
explicit native inhibit handoff. Earlier macro nesting compile error confined to
diagnostic probe; fixed by including original parameter initializer once.

Cleanup regression20261120-cached-cleanup-regression-01.json PASS27 +owned36 on
FINAL pair. Cleanup audit CLI now admits compatible API56/60 cleanup kinds, keeps
all original30s/10M guards. Root71/no skips:20261120-cached-root-tests.log.
Compatibility host20261120-cached-compat56-host-01 exact
bbda6819e395fce90fa6f4a4f67d307ffddb8d1539c3ac0794274e5e12468968.
API56 cleanup module20261120-cached-compat56-module-01 exact5d570653...d2ad3.
Source evidence:evidence/20261120-highlight-cached-primary.json. All jobs terminal;
ignored graph refreshed3052nodes/8057edges (new cached files confirmed present);
source manifest refreshed at checkpoint. No broad previous45/24/107
rerun claimed on API60. Known native engine lifetime and concurrency gaps remain.

NEXT: resolve native upstream frame/parameter concurrency. Direct source branch
candidates at10208800/102089AE/1023A0C4/1023A120/1034EF60/10353030/103530E4.
Param dispatcher10239840 registered at102398D4 through101F2414; executor101F240C
loads callback+2C and calls it after queue receive. This boundary has no shared
source lock in its visible body, but upstream/task/lock closure is NOT complete.
Cached1023D794 callers1023D926/1023E0E6 are parameter-side handlers; forced replay
1023DDCC also in that family. Source10352E68 callers10434E28/3A/50 enter direct
application; trace upstream10434E10/1034EB8A/Image display synchronization. Need
prove existing coordination or add correct native coordination; do not assume
a global seqlock or callback-only reentry flag fences whole native gate/copy.
Then rendering/pixels, style/threshold prefs, EVF/portrait, Info mirror, real
histogram producer, lifecycle, exact installation/recovery. No flash clearance.

## Native-consumer no-frame plane cleanup - November 20, 2026

Previous0db4314 was PROGRESS (native driver/register binding). This turn connects
qualified no-frame restoration/disable and native update quiescence in a NEW
opt-in API56 display-highlight-cleanup-probe. Full goal ACTIVE. No camera/card/
staging/flash/push. Host bytes unchanged. No physical pixels or installation claim.

examples/display_highlight_cleanup_policy.h records original consumed native
permission/meaningful format, context and engine pointer/id/bank; NO frame pointer
retained. Publication bounded3, sequence+nonwrapping serial, halt on exhaustion.
Format4 leaves prior meaningful format. Unknown engine delegates frame permission;
owned/native application admits cameraRAM8 descriptor/id141or142/bank0or4000 only.
These descriptors/banks remain supplied, not physical engine construction proof.

Worker queues/reaps only; cleanup runs in serialized native consumer callbacks.
Before dispatcher, cleanup_prepare snapshots original native input and checks
engine/context. After native100copy+ack, finish restores raw native permission and
calls original gate with meaningful format. Disabled native baseline/raw0 closes
plane; enabled baseline/raw0 remains hidden; enabled baseline/raw1 reprograms
native baseline WITHOUT a new frame. Mode/output disable inhibits owned plane,
retains baseline, returns/restores in original context. Native update release
quiesces old owned plane BEFORE foreign handler/copy and resets frame record;
old queued cleanup cannot clobber newer native parameters.

Checks actual parameters/nativegen/context/service/engine/id/bank before and
after gate; verifies active/dirty and actual register enable. If a qualified
DISABLE still reads enabled due stale active bookkeeping, calls original driver
bit-preserving disable directly. No success on failed register readback; parks
and retains diagnostic ownership rather than falsely publishing released lease.
Unknown/changed engine or busy frame record cancels BEFORE parameter copy.
Native conversion with unknown engine delegates input unchanged and advances gen.
No allocation pin/physical scheduler proof: context/native parameter writer lane
serialization is assumed. Unsupported engine lifetime changes require native
handoff/restart; hardware that rejects writes is not software-recovered here.

Reproducible final .private/builds/20261120-display-highlight-cleanup-04,
SHA5d57065372ce66e013176842653f3d68dd868478f75f01f07fdc236dec9d2ad3,
30148file/29824image/6616BSS/minAPI56. Final54 source inputs verified current.
Host frame-host-01 unchanged MAINbbda6819e395fce90fa6f4a4f67d307ffddb8d1539c3ac0794274e5e12468968.

.private/evidence/20261120-highlight-cleanup-05.json PASS27 cleanup/publication
plus36 owned regression on exact FINAL pair. Actual native converter/consumer/
source/gate/driver/MMIO. Cases: disabled/enabled native baselines/raw0/raw1, no
frame calls during worker/native cleanup, meaningful-format retention after
isolated format4 callback/gate (remaining native format4 render path NOT tested),
mode/menu/output departure, native movie precedence, stale bookkeeping fallback,
unknown initial engine/changed engine cancellation, busy snapshot, interrupted
compiled reader/separate publisher stack/repeated seq/serialMAX halt and injected
stuck MMIO enable failure (no successful-release claim). Kernel/FS/UI/surface/
colors/engine descriptors/MMIO storage/faults/interleavings supplied. Frame cache
layout64 bytes (12 prefix +52 record); permission offset52/format56/valid60.

04 audit reached owned regression but hit original30s/10M CRC/init wall cap at
later fixture.05 retains SAME limits; bootstrap uses original OwnedFixture hooks
(no frame/plane hooks needed during init). Owned36 uses original OwnedFixture +
admitted engine constructor ONLY; full cleanup cases enable plane hooks after
load. Prior01 format4 full native render hit unrelated mutex model; final scope
explicitly isolates callback/gate4. No production workaround or timeout increase.
Root71/no skips:20261120-cleanup-root-tests.log. Old frame profile rebuild
20261120-cleanup-compat56-01 exact3536d86...d476; owned profile
20261120-cleanup-compat52-01 exactf1f39562...2189. Prior45/24/84/107 results remain
previous-profile scopes, not reruns on this cleanup build. Source record:
evidence/20261120-highlight-consumer-cleanup.json. All jobs terminal; refresh
ignored code graph refreshed3046nodes/8017edges; source manifest refreshed
when saving source-only checkpoint.

NEXT: bind native source/frame callers to the parameter-consumer lane or add
concurrency-safe coordination before treating cleanup as camera-ready. Current
checks supply serialization; no physical frame/parameter fencing proof.
Full remaining: actual warning rendering/pixels, style/threshold preferences,
EVF feature/preservation, portrait/rotation, native Info mirror, real histogram
producer, full lifecycle/engine allocation/unsupported context handoff, exact
installation/recovery assessment. No flash clearance; no push authorization.

## Native warning-plane programming and teardown binding - November 20, 2026

Previous644d9c8 was PROGRESS (API56 consumption gate). This turn moves validation
below the supplied plane-programming sink: original driver/validator/readback
execute against emulated MMIO. Full goal ACTIVE. No production host/module edits,
no camera/card/staging/flash/push. This is register evidence, NOT visible pixels.

NEW tools/audit_z7_highlight_plane.py composes FrameProfileFixture and bypasses
ONLY driver10241A0E sink, executing NativePNG native instructions instead. Maps
emulated MMIO20140000..20145FFF, records actual writes. Converter/owned consumer/
source/frame/gate execute. Surface checks, hardware colors, kernel/FS/UI/context
and task handoffs still supplied. Engine identities141/142 with bank offsets0/
4000 are supplied descriptors, NOT live engine construction/output mapping proof.

.private/evidence/20261120-highlight-plane-02.json PASS24, exact unchanged final
API56 pair: frame-host-01 MAINbbda6819e395fce90fa6f4a4f67d307ffddb8d1539c3ac0794274e5e12468968;
display-highlight-frame-02 SHA3536d86c7adac1ab21b5fa63662ec2322a5fb7c39819cffa30f757653c40d476.
Full profile enables actual native register bit, native transformed60B config
passes validator10258EF8, selected mode/threshold/color/control fields match
actual registers, and original readback10241C2E observes enable/mode. Deferred
copy stays native; Off before GUI/worker forced replay clears real enable bit.

NO-FRAME PRIMITIVE: original GATE1023B76E withstate+20=0/active1 invokes driver
10241A0E(engine,NULL,0). Driver disable reads engine+4 bank offset, clears ONLY
bit0 of20140000+offset+430, returns0. Gate clears active1C and dirty24. Both
banks, preservation of all other register bits/banks and repeated-call no-op
verified. Module asynchronous cleanup NOT CONNECTED by this binding audit.
Native pending-ready508 and original frame metadata remain unchanged.

IMPORTANT: format4 bypasses gate and returns1 without teardown. Driver enable
returns0 EVEN when validator rejects configuration, without MMIO programming.
Diagnostic reversed native group upper0/lower256 makes upper gate return1 and
setactive1/dirty0 while hardware enable remains0. Do not treat gate status or
bookkeeping as proof of actual register programming/plane ownership.

NEXT: qualify no-frame cleanup using matched current parameter ownership/native
update generation/context AND native engine. Capture/preserve ORIGINAL consumed
native permission separately from filtered1; enabled native baseline restoration
must not mistake filtered permission for native policy. Gate cleanup belongs in
the serialized native consumer lane; do not call driver/paint from worker/source
observation. Verify no-frame Off, native update precedence, enabled/disabled
baseline, mode/output/menu departure, format4, engine changes and register effects.
Then actual warning rendering/ISP pixels, style/threshold prefs, EVF/portrait,
Info mirror, real histogram producer, full lifecycle, installation/recovery.

Source evidence:evidence/20261120-highlight-plane-registers.json. Audit01 was
intermediate23-check pass;02 final24 adds upper-gate false-positive bookkeeping.
Current sources/exact binary fingerprints verified. No broad suite rerun because
production unchanged; prior45/36/71 remain previous checkpoint scopes. All jobs
terminal; ignored graph refreshed3015nodes/7905edges; source manifest refreshed
at source-only checkpoint.

## Consumption-time primary permission API56 - November 20, 2026

Previous6f6963b was PROGRESS (owned parameter integration). This turn adds an
opt-in native primary-frame consumption filter and full-profile wiring. Full
goal ACTIVE. No camera/card/staging/flash/push. Warning-plane calls execute to
supplied hardware sinks; no actual pixels or physical timing clearance.

NEW sdk/frame_permission.h API56 embeds52-prefix plus init-only resident Thumb
callback registration. Requires existing parameter/highlight/display host flags
and --frame-permission-hooks. Host state288 preserves entire272prefix; callback
272/running276/guards280,284; workspace remains320 (64aligned). Cold clears288,
sets both older/new tail guards and reserves320. Original allocator arithmetic
and continuation registers/NZCVQ execute. Failure clears pointer/claim beforefree.
Missing/invalid callback, guard corruption, reentry, invalid/unaligned/noncamera/
short frame pointer, unsupported kind and native permission>1 delegate unchanged.
Callback decisions0/native,1/enable,2/inhibit; other decisions delegate native.

Exact8-byte hook1023BAB0 in1023B9D0 replaces permission load/store before native
warning gate1023B76E. All live registers/SP/NZCVQ preserved except native r0/r1
outputs. Callback sees actual frame and native permission. Both immediate apply
and forced pending replay traverse hook. Native caller/pending frames and508ready
stay UNCHANGED: module never copies a forced1 into pending metadata. No need to
clear native ready byte or restore a producer's copied flag after the fact.

NEW display-highlight-frame-probe composes full API52 owned/native path and
filters consumed permission only. Matched actual params/nativegen/context/epoch/
palette/current UI ->enable. Owned but stale ->inhibit, including native1 while
owned params await restore. Busy/halted lease ->inhibit unverified params; halted
lease requires restart. Restored/replaced native lease ->delegate. Native writer/
context serialization remains assumed, not a native allocation pin/frame fence.
NEXT: actual warning-plane rendering/pixels and lifecycle teardown when NO next
frame/gate arrives, then style/threshold preferences/EVF/portrait/Info/histogram.

Reproducible host .private/builds/20261120-frame-host-01,
MAIN bbda6819e395fce90fa6f4a4f67d307ffddb8d1539c3ac0794274e5e12468968,
hostC5513bytes/API56/state288/reserve320/EGCRCzero.
Final module .private/builds/20261120-display-highlight-frame-02,
SHA3536d86c7adac1ab21b5fa63662ec2322a5fb7c39819cffa30f757653c40d476,
28612file/28288image/6484BSS/minAPI56. Host/module source inputs verified current.

.private/evidence/20261120-frame-permission-04/result.json PASS45 exact final pair:
cold/allocator, registration/integrity/guards/reentry/cleanup, bridge native entry
and live regs/flags, native source/immediate/pending4B8copy/forced replay, checkbox
Off BEFORE GUI/worker, restoration/delegation, menu/movie/output/preset/palette
changes, busy/halted lease and API52 early rejection. Source/pending memory is
unchanged. Original native highlight mutex wrappers execute; bypass unrelated
histogram fixture's mutex model only for A1D6AB80; kernel mutex/plane/color/surface
boundaries supplied. Initial01 failed because cold test omitted normal boot's
retained_fd initialization before direct load; fixed independent fixture (same
as older audits).02 hit unrelated histogram mutex model; no production workaround.
03 was an intermediate41-check run;04 is final45/current source/bytes evidence.

Owned regression36: .private/evidence/20261120-frame-owned-01.json on FINAL pair.
Root71/no skips:20261120-frame-root-tests.log. API52 host rebuilt WITHOUT frame
option:20261120-frame-compat52-host-01 exact old da7cfc45...7e6f9; old owned module
20261120-frame-compat52-module-01 exact f1f39562...2189. No old52 behavior change.
Older107 request/9 lease/84 persistence reports remain scoped prior-checkpoint
evidence, not a rerun of those suites against API56. Source record:
evidence/20261120-highlight-frame-permission.json. All audit/build jobs terminal;
final ignored Graphify graph refreshed3004nodes/7865edges; source manifest
refreshed when saving checkpoint.

Full goal incomplete: physical warning pixels, lifecycle/asynchronous teardown,
style/threshold menu preferences, EVF feature/preservation, portrait/rotation,
native Info mirror, real histogram producer and exact installation/recovery.
No flash clearance. Keep source-only; no remote push authorized.

## Full-profile owned highlight parameter lease - November 20, 2026

Previous70ec7ad was PROGRESS (deferred helper). Latest status-only turn made no
source changes; this continuation completes owned parameter integration and adds
focused lease tests. Full goal ACTIVE. No camera/card/staging/flash/push.
Source permissions remain native; no immediate pending-frame cleanup or pixels.

NEW display-highlight-owned-probe composes both eligible incoming API52 native
conversion and deferred worker submission with a consumer-written parameter lease.
Worker operation/context/native-generation metadata precedes queue publication.
Current consumer converts with the current palette, native dispatcher copies100,
acks/completes, and after-consumer checks actual parameters before publishing the
lease. Request reuse still requires BOTH dispatcher and submitter return. New
cancel_claim handles policy failures after claim; old preconverted submit inline.

Lease records original baseline/expected100, context, epoch, palette, nativegen,
and disabled state. All valid native updates invalidate old ownership, including
same-byte/ineligible notices. Eligible rewrite captures the ORIGINAL incoming
native baseline first. Disabled input defines ONLY word0; normalize other96 to0.
Off restores only matched nativegen/currentdata/context. Mode/output exit disables
owned params and retains baseline; return to original identity reapply/restore.
Newer native updates cancel pending restore/disable. Settled work does not queue
again. Menu entry rechecks live UI even before a new GUI publication.

Lease reader bounded3, sequence+monotonic serial, no partial failed output; serial
MAX parks. Native parameter writers ASSUMED SERIALIZED in DisplayService consumer
lane; no native allocation pin, physical frame fence, or concurrent-writer proof.
Do not enable frame+34 yet. Deferred4B8 frame copy needs immediate cleanup; worker
cleanup alone leaves a replay interval. Next implement/test pending cleanup and
source gate using matched applied ownership, then broader lifecycle/pixels.

Reproducible private module:20261120-display-highlight-owned-02,
SHA f1f39562292a2cd5a112aa397862db4dd96ae417dfd5d1190ea4b3610ae42189,
28356file/28032image/6484BSS/minAPI52. Final50 source inputs verified current.
Host unchanged:20261120-parameter-host-03,
MAIN da7cfc45631e9545f7d8da6def184d2007496ef9ae2f26757b7b25df52c7e6f9.
Owned01 and02 are identical bytes;02 updates reviewed input fingerprints.

.private/evidence/20261120-highlight-owned-03.json PASS36 on exact final bytes:
worker send/current palette/actual native dispatch/copy/ack/completion, enabled
and normalized-disabled baseline restoration, stale cleanup cancellation, same-byte
native update, native movie precedence, early consumer while submit paused on
separate stack, new eligible native baseline replacement, menu changes before GUI,
LCD/EVF selector round-trip disable/reapply/restore. Kernel/FS/UI/palette and
explicit task handoffs supplied. Owned02 audit attempt TERMINAL wall-time failure
at module init while other heavy jobs ran;03 ran alone with SAME30s/10M guards.
No relaxed timeout or failed-run evidence substituted for success.
Lease:20261120-highlight-lease-01/result.json PASS9 compiled Thumb; interrupted
reader/independent writer stack/repeated sequence/serialMAX halt/unchanged failed
output. Request:20261120-highlight-request-owned-01/result.json PASS107; same
probe SHAa95e400a31877a1921f40c0b693c1b464178534beeaf4431989c75ca34e26b9a.
Persistence:20261120-owned-persistence-01.json PASS84 on final host/owned bytes
(module01 bundle byte-identical02), including actual menu/worker interleavings.
Root:20261120-owned-root-tests.log PASS71/no skips. Default API44 module rebuild
20261120-owned-compat44-01 byte-identical SHA719c1db3ca5cf1c78d82ebedcdbbb4cc7b67312b34b7982d11a718e4b39af85c.
Source evidence:evidence/20261120-owned-highlight-integration.json.

Remaining full goal: immediate frame cleanup/gating and pixels, style/threshold
preferences, EVF feature/preservation, portrait/rotation, native Info mirror,
real histogram producer, full lifecycle and exact installation/recovery assessment.
No flash clearance. All jobs terminal. Final graph refreshed2985nodes/7827edges;
source manifest refreshed when saving checkpoint. Generated/private files stay ignored.

## Deferred owned request helper - November 20, 2026

Previousc9242e5 was PROGRESS (API52 incoming parameter path). This turn adapts
the resident owner for consumer-time conversion. Full goal ACTIVE. User asked
status: native parameter conversion is implemented/tested, but owned submission,
restoration, frame gating/pixels and broader lifecycle remain; no flash advised.
No camera/card/stage/flash/push. Existing full profile/host bytes unchanged.

highlight_request.h adds submit_deferred (queue zero104-byte source, no palette
access/conversion) and convert_deferred (only current claimed consumer, intact
descriptor/callback/source/context, uncompleted/ack0). Original native converter
runs at consumption with then-current palette. Legacy preconverted research
entry retained. Only examples/highlight_request_probe.c and highlight_host_probe.c
include helper currently; full parameter profile still DOES NOT submit owned work.

Added Z7_HR_CANCELLING=5 (old enum values unchanged). A stale begin() transitions
to cancellation, and convert cannot revive it even when passed its OLD epoch.
Native completion/end accept cancellation and retire it with ack0. Completion
still does not permit reuse before native dispatcher AND submitter return; lost
requests remain parked. All old59 lifetime checks retained.

.private/evidence/20261120-highlight-request-deferred-02/result.json PASS107.
Probe SHAa95e400a31877a1921f40c0b693c1b464178534beeaf4431989c75ca34e26b9a.
Enabled/disabled both outputs1/4, changed palette AFTER queueing, zero source,
before-claim/after-completion guards, wrong epoch and cancellation revival,
native copy/ack/completion/reap tested. Kernel queue/palette input/explicit
consumer scheduling supplied. Final current header/probe/audit hashes recorded.
Source evidence:evidence/20261120-owned-highlight-deferred.json. Isolated helper
change, not a full profile/persistence regression rerun. No warning pixels.
Final probe/source hashes verified current; graph refreshed2931nodes/7648edges,
generated output ignored. All jobs terminal; source-only manifest refreshed.

NEXT: wire deferred helper into full API52 profile with parameter lease/baseline,
native generation+settings/context epoch; convert after owned claim at dispatch.
Capture baseline before incoming eligible native rewrite (disabled input only
defines enableword), preserve newer native updates even if bytes match, conditional
restore/disable and cancellation. Source/frame permission remains native until
matched applied ownership AND immediate pending-frame cleanup are implemented.
See prior chapter for final API52host03/profile03 fingerprints, read-only native
notices, workspace320 reservation, regression scopes and deferred-copy danger.
Remaining full goal unchanged: style/threshold prefs, EVF, portrait/rotation,
Info mirror, real histogram producer, lifecycle, installation/recovery. No flash.

## Native photo-parameter payload conversion API52 - November 20, 2026

Previous60c5041 was PROGRESS (full-profile epoch). This turn implements incoming
native parameter conversion. Full goal ACTIVE. No camera/card/stage/flash/push.
No frame flag override, owned submits, restoration, pending cleanup or warning
pixels yet; this remains a development profile, not a completed feature build.

Host flags --display-hooks --highlight-hooks --parameter-hooks add API52
sdk/parameters.h. Init-only resident Thumb callback registration follows API48
hooks and precedes settings I/O. Foreign42060007/42062007 only, matching selector,
service1..4, aligned RAM descriptor28/source104, enable0/1. Writable100 source
ONLY mode property138D==0/service3..4. Other modes or phases1/2 notify via NULL,
never expose writable caller memory. Invalid/unrelated packets and registered
owned descriptor excluded; reentry delegates; ORIGINAL dispatcher/completion
always continue. Callback code/pointer bounds, failed-init clearing tested.

--variant display-highlight-parameters-probe composes full persistent profile
and epoch with current eligible LCD photo conversion. Original1034FE22 executes
with a cleared100-byte temporary and asserted typed36-byte request. Initial
pattern1/threshold248; style/threshold menu configuration and EVF feature remain
open. Recheck epoch/context/palette pointer before copy, enableword last. Preserve
descriptor/source/callback/context/ack and GUI36. No retained caller pointer or
post-wake scratch restoration. Native generation advances on ALL valid updates,
including ineligible and same-byte notices; exhaustion parks, no wrap. Prepared
parameter_epoch is NOT confirmed application. Need actual copy/ack/currentdata.

Final host .private/builds/20261120-parameter-host-03,
MAIN da7cfc45631e9545f7d8da6def184d2007496ef9ae2f26757b7b25df52c7e6f9.
Profile .private/builds/20261120-display-highlight-parameters-03,
SHA33a159a188e2a51dbbfadde2a5614073ba04ba25e9e0676dbdb851e8b5555f9e,
25732file/25408image/5804BSS, minAPI52, reproducible/hostEGCRCzero.
State272 preserves256prefix; callback256/running260/guards264,268. RESERVE320!
Actual101E3DAC rounds sizes64 but DOES NOT realign cursor; initial272 reservation
was wrong. Cold now clears272, advances toSTATE+320. Original allocator1/63/64/65
returnsSTATE+320/384/448/512, cursor+640, all64aligned. Workspace lock wrappers
supplied; original arithmetic/cold continuationregs/NZCVQ/guards/bounds execute.
Generic HostFixture now initializes report.state_bytes and API52tailguards;
words() intentionally still inspects the64-word prefix for old APIs.

.private/evidence/20261120-parameters-07/result.json PASS59 on FINALhost/profile.
Both selectors/service3/4, filter/notice/reentry/registration/lifetime cleanup,
native cold/allocator and original1034FF1E callers initiallydisabled ANDenabled.
Pause original at actual10036504 wait timeoutFFFFFFFF, savecontext, consumer on
SEPARATEstack. Original converter/dispatcher100copy/ack/completion/native event
callback execute. Caller resumes with original SP/callee regs/GUI36. Descriptor
+4..27 preserved; original source+100 ack overlapsdescriptorword0. Actual checkbox
Off/menu/movie/palette/oddrevision delegate unchanged. Same-byte native update
clears prepared identity and increments generation. Highlight event object
A1F1353C must bypass unrelated HISTOGRAM event model at10170BEE/10170BE8/10170C72,
executing ORIGINAL wrappers down to supplied kernels. No production workaround.

Root71/no skips:.private/evidence/20261120-parameters-root-tests.log.
Persistence84:.private/evidence/20261120-parameters-persistence-01.json;
epoch61:.private/evidence/20261120-parameters-epoch-01/result.json. Those ran exact
profile03 on host02 MAIN6cba9195b520755caeefadadfe3ef6d5eef6d942d18b641ecace9b5d7c5e0fe3.
Finalhost03 has IDENTICAL C image/symbols/all noncold bytes; only byte11FA6C9A
changes cold cursor272->320. Final59 --runtime-reference host02 verifies this
and separately tests correctedcold. Do not claim84/61 report finalhost03 hash or
physical boot. Kernel/FS/UI/palette/task scheduling supplied. Source evidence:
evidence/20261120-native-highlight-parameters.json. All jobs terminal atcheckpoint.
Final59 audit/host/module source fingerprints verified current. Graph refreshed
after code edits:2924nodes/7636edges; generated graph ignored. Source manifest
refreshed; no private firmware, binaries, dumps or graphs indexed.
Old API44/48 hosts/modules rebuilt BYTE-IDENTICAL:7d7356e.../512f06c... hosts and
719c1db.../d429674... profiles; parameter-compat-host44/48-02 and
parameter-compat-module44/48-01 private bundles. Default profile unchanged.

NEXT: parameter lease with native generation ANDepoch (not byte equality alone),
baseline capture before eligible native overwrite and conditional restoration.
Disabled native input defines only enableword: do not interpret stale96 bytes.
Adapt highlight_request.h (old59check scope) to convert OWNED requests at consumer
with current epoch/context/palette, not earlier worker conversion. Retain104-byte
source/28-byte descriptor until submit+consume return; after_consumer must finish
old-packet access BEFORE end publishes reuse. Existing consumer callback PARKS;
current profile submits NO owned request. Keep caller GUI36/descriptor/callback/
ack contract, never restore caller memory after original completion wake.
Only enable frame+34 after matching actual applied params/ack/generation/epoch.
OFF/mode/output/menu must handle deferred4B8 copy state+50C/ready+508: restoring
caller flag does not cancel pending1. Do NOT enable flag before immediate cleanup
policy; worker-only cleanup can leave pending replay active between ticks. Gate
1023B76E/state+20 permission/state+28 enable proved66; hardware pixels stillopen.
Then style/threshold prefs, EVF feature/preservation, portrait/rotation, Info mirror,
real histogram data, full lifecycle and installation/recovery. No flash clearance.

## Full persistent profile settings/context epoch - November 20, 2026

Previousf2d4767 was PROGRESS (mode/output/context reader). This turn connects a
shared epoch to the actual full persistent profile's GUI/source/worker callbacks
and native menu/DISP behavior. Full goal ACTIVE, no camera/card/stage/flash/push.
This remains a DEVELOPMENT CONTEXT PROFILE, not a visible highlight feature.
No native warning parameters or per-frame permission writes, no request submits.

NEW --variant display-highlight-context-probe requires API48; composes unchanged
focal/Other/histogram/information/persistence functions plus epoch observation.
.private/builds/20261120-display-highlight-context-03 is reproducible,
SHA d429674d261aeea3685906ef166159691634724e489833312dc8fc0cb1470409,
25412file/25088image/5740BSS. Host remains accepted optional API48
.private/builds/20261120-highlight-host-03, SHA512f06c17c712b6a4503532098c4f521deef681b6839346a739d3151f361d02c.

plugins/highlight_epoch.h: one GUI writer, twelve atomic payload words: seven
native context fields +settings revision/preset/wanted/eligible/DISP generation.
Odd/even sequence and monotonic epoch, reader bounded3 attempts, no partial out.
Unchanged GUI ticks keep epoch. Readers recheck BOTH sequence and epoch; repeated
sequence cannot pair old epoch/new partial view. EpochMAX change parks untilboot,
never recycles queued identity. No native transaction/fence/physical timing claim.

examples/display_highlight_context_policy.h publishes at end of existing composed
after-GUI callback. Uses even-revision persistence_snapshot and RAM contextreader,
current LCD DISP ownership; EVF/movie/menu/Info remain delegated. Source callback
returns observation epoch, after records it WITHOUT changing frame. Worker
records currently eligible epoch then runs existing persistence worker. Descriptor
is registered but NEVER queued; before_consumer parks. Allfour callbacks/worker
registered BEFORE persistence_prepare I/O. API44 rejects before settings/menu I/O.
Actual Photo highlights checkbox now feeds wanted epoch bit, NOT warning pixels.
Capture native z7_preset_cycles: four cycles away/back cannot reuse prior epoch
even if preset number matches. Recheck revision/preset/generation/UI/live context
and publication epoch before source/worker accepts. Existing fullprofile is LCD;
this does not redefine full EVF/native preservation goal as completed.

.private/evidence/20261120-highlight-epoch-05/result.json PASS61 on EXACT03.
Compiled ledger +actual full GUI/source/menu/DISP/worker callbacks execute.
Every field/unchanged tick/odd writer/wrap/exhaustion; reader paused after first
payload word while compiled writer executes on separate stack. Supply repeated
sequence to require monotonic epoch retry. Full preset round-trip, menu revision,
live mode/output/selector/service/menu/app invalidation and API44earlyreject pass.
FS/UI/after-GUI delta sync/frame-apply and explicit interleavings supplied. Native
source route executes, frame-apply itself supplied in this combined fixture
(separate original frame/gate audit remains66). Caller frame4B8 bytes unchanged.

Existing persistence/status acceptance PASS84 on EXACT03:
.private/evidence/20261120-highlight-context-persistence-02.json.
Root71/no skips:.private/evidence/20261120-highlight-epoch-root-tests.log.
Default API44 persistent profile rebuilt BYTE-IDENTICAL
.private/builds/20261120-highlight-epoch-compat-01,
SHA719c1db3ca5cf1c78d82ebedcdbbb4cc7b67312b34b7982d11a718e4b39af85c.
First regression reached last check then failed because a MODULE directory was
passed as legacy HOST. Correct API40host is20261120-display-host-08 (SHA6ea33985de7c0d35c2f6b026157595b56fdd9167aa79df53cded25e2f25c87ac),
NOT20261120-menu-status-compat-01. Audit now preflights host report/main presence;
wrong module-only directory verified fails immediately/no output artifact.
Source evidence:evidence/20261120-highlight-epoch.json; details/commands:
z7-native-modules/PHOTO_HIGHLIGHTS.md. All jobs terminal at checkpoint.
Final module input hashes/epoch audit sources verified current. Graph refreshed
after code edits:2896nodes/7545edges; generated graph ignored. Root source-only
manifest refreshed; no firmware/private artifacts or generated graphs indexed.

NEXT ACTUAL FEATURE IMPLEMENTATION: connect epoch to native parameter ownership
and both pinned paths. Re-read .private/research/z7ii-50a22b2/sdk/photo_zebra.h:
zebra_packet_update/apply change eligible100-byte native payload BEFORE original
dispatch, preserve descriptor/callback; zebra_evf_request submits owned packet
for output switches that need not produce native packets. Owned-only async queue
is NOT a substitute for incoming native parameter conversion. Current API48
always delegates foreign descriptor addresses; add explicit opted-in narrow
parameter-packet hook (likely API52) while keeping default API44/API48 unchanged.
Filter exact original42060007/42062007, correct active/photo/UI/epoch; ordinary
non-highlight/ineligible/native movie packets stay byte-identical. Original GUI
payload100 remains live until callback; mutate converted100 before native handler,
keep descriptor/source pointer/callback/ack contract (do not restore after wake
and risk returned caller stack). Native36-byte GUI request remains unchanged.
Convert owned requests at consumer boundary with current context/palette rather
than relying on earlier worker conversion. Restore/cancel owned state only with
validated ownership, preserve foreign changes, account for deferred frame copies.
Only enable per-frame+34 after matching current applied epoch/parameters. Existing
resident owner helper's59check scope still separate; adapt and retest lifetime.
Then actual warning pixels/EVF/movie preservation. Portrait/rotation, Info mirror,
real histogram data, full lifecycle and exact installation/recovery still open.

## Highlight native mode/output and bounded RAM context - November 20, 2026

Previousae19d3e was PROGRESS (optional API48 host bridges). This turn binds
original rear/EVF routing, property-backed mode and compiled RAM context reads.
Full goal remains ACTIVE. No camera/card/stage/flash/push. Host/full persistent
module/QEMU bytes unchanged; no highlight preference connection/pixels claimed.

.private/evidence/20261120-highlight-output-03.json PASS131. Original103484DC
logical source0 ->rear-monitor tag selector1023CC7E; source2 ->EVF1023CCF4.
Real16-byte comparison and all five pointer setters execute. Matching secondary
source wins; distinct identical tag pointers and trailing-byte mismatch tested.
No match clears native state+8/+C but LEAVES DOWNSTREAM MIRRORS STALE. Source
selection does not set active selectorA180A568. Use primary selected source.

Original output-kind getter103FEF80 reads WORD A181C764 (not a supplied return).
Original DISP selector103673AC executes for kinds0..5/modes0/1. Kind1 selects
2F15/2F17; others2F16/2F18. Do not equate all alternate kinds to physical EVF.
CRITICAL newly bound mode property138D: original lookup10070204 resolves467hex
to ROM descriptor114D501C, type7/size4/backing WORD A24E1E00. Original getter
104065A4/101D53AE/1016FEF2/101706EE/10070234 and group lookup execute directly
against supplied RAM, no mode getter return faked and no property lock/wait on
this path. Values0/1/2/FFFFFFFF tested. Original GUI bulk key tableA1828E88
contains138D at index135decimal/+21Chex. Real10376414/1016FEFC loop copies a
ONE-KEY slice into cachedA201F47C with adjacent bytes intact. The whole270-key
cache is NOT proved atomic/current; production should use property backing word.

NEW plugins/highlight_context.h and examples/highlight_context_probe.c use
RAM-only seven-field stable reads:mode/output-kind/active-selector/native-state/
primary-selected-source/ready/service. Validate state/source alignment/range,
selector0/1 and source's original rear/EVF tag, then reread fields with bounded
three attempts. Output is caller-owned and untouched on failure. Reader returns
raw mode/ready/service, NOT a photo eligibility or UI/preset ownership decision.
Repeated equal values do not detect ABA, pin allocations or make a native fence.

.private/evidence/20261120-highlight-context-06/result.json PASS28. CompiledARM
reader plus original source selection execute. Both selectors/four mode values,
pointer/tag/range/selector failures, stale mirrors after native no-match, live vs
stale GUI-cache values and between-instruction mode/output/selector/state/source/
ready/service changes tested. Continuous changes stop after three attempts,
output unchanged. Diagnostic gotcha: adding Unicorn read/code hooks after prior
translated execution required ctl_remove_cache(CODE,CODE+len(image)); previously
hooks did not run (mode read count0), not a C reader failure. Final mutations
occur on NEXT instruction after first completed load, never in observed load.
Native source allocations/frame timing and physical cross-task behavior unproved.

Scopes131 native output +28 compiled reader are separate; isolated helpers/audits,
no broad root/full-profile regression rerun. Details/commands:
z7-native-modules/PHOTO_HIGHLIGHTS.md; source-only evidence:
evidence/20261120-highlight-context.json. All audit jobs terminal at checkpoint.
Final native audit/compiled reader source fingerprints and private probe hash
verified current. Graph refreshed:2856nodes/7429edges; generated graph ignored.

NEXT IMPLEMENTATION: integrate into full persistent profile (new opted-in
display-highlights-probe/API48), register hooks before persistence_prepare I/O.
Publish odd/even shared settings+preset/context epoch from existing GUI path;
source/consumer callbacks re-read property WORD A24E1E00 and primary routing
through helper, reject mode!=0 and ineligible service/output/UI/preset. Apply
per-frame+34 only for owned eligible primary frames, restore caller token without
assuming deferred copy cancellation. Worker owns asynchronous submission/reaping.
Capture100-byte native baseline at owned consumer boundary; conditionally restore
only if current parameters still match owned application, preserve foreign native
changes. Cancel stale descriptors with original completion. Native mode transition
timing/source allocation lifetime still need explicit interleavings/acceptance.
No native wait in paint/producer. Actual warning pixels, EVF/movie preservation,
portrait/rotation, Info mirror, real histogram data, full lifecycle and exact
installation/recovery assessment remain incomplete. No flash authorization.

## Optional API48 highlight host bridges - November 20, 2026

Previous100a830 was PROGRESS (resident request owner/frame gate). This turn
implements exact-byte-validated native source1034866E and consumer10239840
bridges in an explicitly opted-in API48 host. Full goal remains ACTIVE.
No camera/card, stage/flash/push. User asked whether close to flashing: explained
that full features/lifecycle and exact-candidate recovery assessment remain;
no flash authorization, continue software work as previously requested.

Private .private/builds/20261120-highlight-host-03 is reproducible/EGCRCzero,
main SHA512f06c17c712b6a4503532098c4f521deef681b6839346a739d3151f361d02c.
Use build_z7_module_host.py --display-hooks --highlight-hooks. Default remains
API44 with no highlight patches. Fixed256-byte host state uses reserved words
53..59 for descriptor/four callbacks/two atomic running flags; guards unchanged.
sdk/highlight.h defines init-only registration, aligned loading descriptor28,
four required Thumb image callbacks, fail-init cleanup before free and resident
lifetime checks. No foreign Z7II callback/structure offsets assumed.

.private/evidence/20261120-highlight-host-07/result.json PASS77. Actual compiled
host/probe plus original converter/builder/queue wrappers/source/gate/consumer/
copy/ack/completion execute. Kernel/filesystem, incoming state/diagnostic epoch,
surface checks, hardware color/plane programming are supplied. Source callbacks
use local token; caller frame restored while deferred native copy keeps flag.
Native result/volatile registers/flags preserved across callbacks. Foreign native
packets (matching/rejected logical families) delegate unchanged while owned
request is pending. Owned stale request cancels via original completion without
copy. Duplicate/reentrant owned consumption parks. Init/late/duplicate/bad ranges,
all four required callbacks and damaged resident state guards tested.

Audit first caught wrapper argument corruption: saving APSR had clobbered R0
before helper calls. Both bridges now explicitly restore callback arguments.
Native hardware config has unwritten padding; byte-exact UNREGISTERED fallback
comparisons seed original reference scratch from captured native-entry scratch.
Registered no-op tests prove result/volatile-register/flag ABI, not undefined
padding equality. Actual screenshots/pixels are not normalized or claimed.

Important retirement race fixed: release host consumer guard BEFORE module
after_consumer publishes reusable state. Otherwise an immediate reap/submit/
consume could be dropped as old-call reentry. Diagnostic explicitly nests a
new request after retirement before old host leave returns. It FAILS on host02
(.private/evidence/20261120-highlight-host-retirement-before-fix.log), PASSES on
host03 with original native completion. Explicit interleaving is not hardware
scheduling proof. After retirement module code must not access old packet data.

Root tests71/no skips: .private/evidence/20261120-highlight-host-root-tests.log.
Default API44 host and persistent display module rebuilt byte-identically to
accepted7d7356e7775db90483ed9fe5598f401afb7fb8498a7b42bd71900db849d7f057
and719c1db3ca5cf1c78d82ebedcdbbb4cc7b67312b34b7982d11a718e4b39af85c.
The new API48 diagnostic is NOT the accepted full resident feature profile.
Details/commands:z7-native-modules/PHOTO_HIGHLIGHTS.md. Source evidence:
evidence/20261120-highlight-host.json. All jobs must be terminal at checkpoint.
Final77-check audit and both host reports match current source fingerprints.
Graph refreshed after code edits:2823nodes/7335edges; generated files ignored.

NEXT: bind coherent original photo/output context and epoch changes, integrate
the optional host hooks/owner into full persistent profile before startup I/O,
and submit from its worker. Capture/conditionally restore owned100-byte native
baseline, cancel stale owned packets and account for deferred frame copies.
Then prove actual warning pixels and native LCD/EVF/movie preservation. Photo
highlights preference remains UNCONNECTED. Portrait/rotation, native Info mirror,
real histogram data, broader lifecycle and installation/recovery remain active.

## Highlight frame gate and resident async owner - November 20, 2026

Previous status-only goal turn was NO PROGRESS. This turn adds compiled ARM
request ownership code and59 scoped native checks, and records the previously
uncommitted66-check frame permission audit. Full goal remains ACTIVE. No
camera/card, stage/flash/push; accepted API44 display module/host/QEMU unchanged.

Frame audit: .private/evidence/20261120-highlight-frame-gate-03.json PASS66.
Original1034866E source submit ->1023B9D0 primary frame ->1023B76E gate executes,
including1023B578 parameter transformation. Primary frame+34hex permission is
copied to state+20hex; both it and global state+28hex must equal1. Do NOT use
frame+28 as warning permission. Native selector0/1 admit logical outputs0/2;
physical output/photo-movie binding is still open. Deferred native source copy
is4B8hex bytes at state+50Chex, ready byte+508hex. Restoring caller metadata
does not cancel that copy; forced replay can still enable the plane. Incoming
service/frame/MMIO/palette state, surface checks, mutex success, hardware color
and plane programming are supplied. No actual warning pixels/hardware accepted.

NEW plugins/highlight_request.h and examples/highlight_request_probe.c supply
resident28-byte descriptor plus separate104-byte payload. Original converter,
builder and submit wrappers execute; no native infinite-wait caller. Atomic
single-owner states prevent overwrite/reentry. Consumer bridge must claim the
owned packet, execute original dispatcher (or original completion for stale
context), then retire only AFTER native return. Completion alone cannot release
storage. Reaping also waits for submitter return, including early consumption
while submitter is paused at kernel queue on a separate stack. Native ack1
means100-byte copy; ack0 completed means cancelled/not applied. No completion
means parked, regardless of time/queue return. No speculative timeout reuse.

.private/evidence/20261120-highlight-request-02/result.json PASS59. Private
probe SHA51f1df142dab6db2637b1d05bf0ba3b1e3d0edd559fceed6050ad1ccbe4f3aaa.
Both logical outputs/enabled+disabled, zero padding/ack, busy nonmutation,
foreign pointer delegation, stale context cancellation, duplicate/reentrant
consumption, wrong-command/missing completion, four descriptor corruptions,
supplied queue success/error with late consumption, and early consumer tested.
Kernel queue latency/error ownership are NOT proved. Consumer bracketing and
epochs are explicit test inputs, NOT installed host/context hooks. All audits
terminal; separate scopes66 and59, not a broad full-profile regression rerun.
Graph refreshed after code edits:2786nodes/7228edges, generated graph ignored.
Current owner/probe/audit source hashes and private probe binary match the59
check report. Source-only manifest refreshed; no private/binary files indexed.

Source evidence:evidence/20261120-highlight-frame-gate.json and
evidence/20261120-highlight-request.json. Details/commands:
z7-native-modules/PHOTO_HIGHLIGHTS.md. Existing accepted persistent native full
profile remains .private/builds/20261120-display-save-status-05, API44,
SHA719c1db3ca5cf1c78d82ebedcdbbb4cc7b67312b34b7982d11a718e4b39af85c.

NEXT: implement exact-byte-validated native source/consumer host bridges,
resident callback registration/lifetime checks and coherent photo/output epoch
producer, then integrate async owner into full Photo highlights preference.
Account for deferred copied metadata and restore/cancel owned parameters on
context/preset exit. Ordinary native movie/EVF packets must delegate unchanged.
No foreign image+468 chain bound. Actual warning pixels, portrait/rotation,
native Info mirror, real histogram data, full lifecycle and exact-candidate
installation/recovery assessment remain incomplete. No flash authorization.

## Native highlight request submission/completion handoff - November 20, 2026

Previous95a16b5 was PROGRESS (original converter). New isolated research audit
executes original builder1034EFB0, blocking caller1034FF1E, submission wrappers,
consumer dispatcher, native completion and native event callbacks. Native
module/host/QEMU bytes UNCHANGED; no hook installed, camera/card, stage/flash/push.

.private/evidence/20261120-highlight-submission-02.json TERMINALPASS38.
Buildercase16 logicalbanks0/1/2 ->42060007/42061007/42062007 with exact native
callback/data/context fields and ARM stack argument preservation. Original
caller flags1/4 ->banks0/2 converter+queue+wait. Flags2/bank1 builder is checked,
but its separate103490F4 submission path is NOT forced through DisplayService.
Physical output mapping/photo-movie eligibility are not established here.

Native wrappers10348494 ->1023AAB2 ->101F243C ->10112446 execute before supplied
kernel queue send100363CC. Native event clear10170BEE enters supplied kernel
10035E94. Caller stops at actual kernel wait10036504 with timeoutFFFFFFFF and
bits20/80hex. Preserve callerCPUcontext, run native10239840 consumer on a
SEPARATE emulated stack, including100-byte copy/ack and original102396C0
completion; original callbacks10354342/10354356 ->10170BE8 ->kernel10036334
set the matching flag. Restore caller context; original wait completes, result1,
stack and all callee-saved registers intact. Both enabled anddisabled paths tested.

Original payload stays on caller stack until completion. Its100-byte payload
ends exactly where adjacent descriptor starts; source+100 acknowledgement writes
descriptorword0. Use explicit104-byte payload storage in extension code instead
of copying this adjacency assumption. Builderdescriptor size at least28bytes.

CRITICAL: native caller wait is INFINITE (FFFFFFFF). Do not call from extension
paint callbacks. We need owned asynchronous packet lifetime, context-cancellation
and queue/backpressure assessment before integrating. Kernel queue/event delivery
and initial palette/service state are supplied, explicit task handoff is not
physical scheduling proof. No frame producer or actual warning pixels verified.
Detailed source:z7-native-modules/PHOTO_HIGHLIGHTS.md. Newaudit:
tools/audit_z7_highlight_submission.py. Source evidence:
evidence/20261120-highlight-submission.json. This turn's38checks are separate
from prior198converter/37transport/71root scopes; no broad regression rerun for
an isolated read-only audit. All jobs terminal. Graph refreshed after code edits:
2747nodes/7116edges; generated outputs ignored.

NEXT: bind the original source/frame producer and photo/output context, then
integrate owned async packets and existing Photo highlights preference. New
private leads:1023B76E applies state+28 parameters via1023B578 ->10241A0E;
1023B9D0 gates native service states3/4 and state+228. These are disassembly leads,
NOT executed bindings. Raw+468 field scan has many unrelated false positives;
do not copy Z7II image+468 offset based on occurrence alone. Private scans:
.private/research/z7-highlight-state28-candidates.txt andframe468-candidates.json.
Original highlights/portrait/rotation/nativeInfo/lifecycle/statistics and
physical installation/recovery scope remain active, not complete.

## Original highlight request converter bound - November 20, 2026

Previousbb689d1 was PROGRESS (native packet transport). New independent
read-only research audit binds original-Z7 converter1034FE22, not Z7II10578920.
.private/evidence/20261120-highlight-converter-01.json TERMINALPASS198 in99cases.
Native converter, enum-table helpers10433B1E/26/2E and raw palette getter10435ACA
execute. Incoming36byte request and palette state/content are supplied. Palette
pointer is nativeA1F18FAC; no getter return is faked. Two different palettes
verify lookup-dependent output bytes. No native module/host/QEMU code changed.

Cases coverflags1/2/4, enabledpatterns1/2, all8thresholds255/248/235/224/213/202/
191/180, two palettes anddisabled mode. Exact100byte destination+padding,
input36bytes+padding and original getter calls checked. Thresholds scale256,
first halfword255 scales257 toFFFF; output flags1/2/4 give targetbyte0/1/2.
Original enum tables determine pattern/color interpretation. Do not equate
logical target flags with physical LCD/EVF/movie until original caller proof.

CRITICAL: disabled conversion writes ONLY word0=0. The remaining
96bytes are untouched; enabled conversion also leaves padding untouched. Clear
all25 owned words before conversion. Do not send uninitialized padding. Consumer
acknowledgement still needs104source bytes as proved previously. This agrees
with the pinned caller's zeroed25-word converted scratch and26-word queue payload.

Sourceaudit:tools/audit_z7_highlight_converter.py. Detailed source research:
z7-native-modules/PHOTO_HIGHLIGHTS.md. Source evidence:
evidence/20261120-highlight-converter.json. Newtool is isolated; relevant check
is198native checks, not a rerun or replacement of prior37transport or71root tests.
Graph refreshed after code edits: 2733nodes/7067edges;
generated outputs ignored. All jobs terminal.
No graphics submission, frame producer, warning pixels or physical camera/card
access established. No installed hook, stage, flash or push.

NEXT: execute original1034FF1E caller /1034EFB0 request builder, then bind frame
producer and photo/output context. Caller disassembly shows converter before
submission/completion; do not call it from GUI hooks and inherit its native wait
without proving task safety. Existing Photo highlights preference still unbound.
Full original scope remains active: highlights, portrait/rotation, native Info
mirror, lifecycle, real statistics producer and physical installation/recovery.

## Photo-highlight native packet transport research - November 20, 2026

Previous638470e was PROGRESS (startup-blocked menus). This turn starts the
original photo-highlight port; no native module/host/QEMU changes, camera/card
access, staging, flash or push. All prior feature gaps remain in the full goal.

New tools/audit_z7_display_parameters.py executes exact stock C3.80 instructions.
.private/evidence/20261120-display-parameters-03.json TERMINALPASS37. Native
102396E2 decoder admits42060007 only for selector0 atA180A568 and42062007 only
for selector1; both normalizegroup0/op6. Original10239840 dispatcher uses
10629FC8 table withgroup300/state60/op4byte strides. Service states1..4 at
A1D68E54 route to1023E214 via four original slots1062A01C/058/094/0D0.

Handler copies100bytes fromrequest+14hex payload to* A180A588+28hex, sets
state+24hex=1 and source+100decimal=1, then completion102396C0(request,0),
return1. SOURCE NEEDS104accessible bytes, not a100byte scratch buffer. Four
opaque payload tests prove exact copy, source acknowledgement and surrounding
buffer/request preservation; eight native routing cases cover both families/
four service states. Incoming packets/state/service bytes and completion are
supplied; original decode/table/copy/stores execute. First extension attempt
missed mapping the service-state RAM page; fixed fixture, not expectations.

Early family literal scan had float/data false positives and no62000 base
literal. Native execution now proves62007 support despite that search absence.
Do not interpret search hits or lack thereof as command acceptance. Selector
physical LCD/EVF mapping, parameter threshold/pattern meanings, converter,
producer, runtime cancellation and warning pixels remain UNVERIFIED. No
highlight implementation or hook is installed. Native module stays unchanged.

Detailed source-only research:z7-native-modules/PHOTO_HIGHLIGHTS.md;
evidence:evidence/20261120-display-parameters.json. Private scans/disassemblies
under.private/research/z7-photo-zebra-* andz7-display-parameters-table-refs.json.
NEXT: bind original converter and frame producer before connecting the existing
Photo highlights preference. Preserve native movie/EVF warning preferences,
photo context exclusions and ownership/restoration. Portrait/rotation, native
Info mirror, broader lifecycle, real statistics and physical installation/
recovery gaps remain. No required broad regression rerun for a new isolated
read-only research audit; this turn's relevant check is the37 native checks.
Code graph refreshed after code edits: 2718nodes/7030edges; ignored.
All jobs terminal.

## Startup-blocked menus and native header readiness - November 20, 2026

Previous8d7cebd was PROGRESS: queued save/retry refresh accepted. Native module,
host and QEMU are UNCHANGED this turn. Current native profile remains private
save-status-05/SHA719c1db3...39af85c, API44. No flash/staging/card/camera/push.

SettingsFileFixture now supports explicit owned read-open error80000002,
distinct from missing80000010. Root71/no skips PASS, including unread-slot/
handle preservation and recovery when the supplied open error is cleared.
Probe --startup-error --seed-directory uses two prior valid journal files and
runs ONE fresh guest inspection, not a new two-boot acceptance result.

.private/evidence/20261120-save-blocked-live-01 TERMINALPASS9 /4PNG. Startup
read-open errors keep module resident with volatile defaults and saves blocked.
Clearing modeled error after init does NOT load late or permit save: a real
native menu edit remains dirty/temporary, no subsequent file events or attempts,
and both original journal hashes stay unchanged. Root, edited root, Composition
and Information native screens all show Restart to save. All4 PNG hashes and
both seed/final file hashes independently verified; frozen3 helper sources match.

Capture now walks the native component child list (component+9C, first/count;
list node payload+8, next+4) using the original102958BA lookup semantics to find
header child203. In addition to all14 row nodes, header+44 must be clear before
accepting a frame. Raw header words/readiness retained privately. This is native
paint readiness, not a physical presentation fence. Actual raw root-edited,
Composition and Information PNGs were visually inspected. Both longest28char
Composition/Information titles are fully visible, with tight spacing before the
back button. No font scaling, screenshot cropping/editing or injected model/
revision/title/pixel stores used. All jobs terminal; guest closed.

Source evidence:evidence/20261120-save-startup-blocked.json. Graph refreshed
after code edits: 2709nodes/7001edges; generated graph ignored. No native build or broad instruction
rerun needed: production bytes untouched; prior84/15/54 +live39 scopes remain
separate. Current new result is startup-error inspection only.

NEXT: continue photo highlights from pinned Z7II source, preserving original-Z7
bindings and native movie/EVF warning preferences. First private literal scan
finds6 original-Z7 occurrences of42060000 and1 of4206001F; no42062000/1E literals.
This is a search lead only, NOT a binding or implementation. Results private at
.private/research/z7-photo-zebra-command-literals.json. Uncertain-close status
pixels, native Info mirror, portrait/rotation, EVF/AF/lens lifecycle, actual
statistics producer and physical SD/cache/shutdown/recovery gaps remain open.

## Queued menu save-status refresh and live retry - November 20, 2026

Previousad4f3d0 was PROGRESS (status publication, idle-refresh failure). This
milestone implements a guarded native menu event wrapper and worker wake-up.
NO camera/card access, staging, flash or push. Full goal remains active.

Current private profile: .private/builds/20261120-display-save-status-05;
reproducible24048bytes/image23744/BSS5648/API44/SHA
719c1db3ca5cf1c78d82ebedcdbbb4cc7b67312b34b7982d11a718e4b39af85c.
Final05 differs from tested04 in a source comment only, and builds EXACT same
native bytes; all39 current input hashes verified. Host09/QEMU remain unchanged.
Old nonpersistent API40 compat01 still d4981187...15ffcd exactly.

The native menu application atA182ECB8 uses state1 callback slotA182ED34,
original1048BFFD. sm_prepare rejects foreign ownership BEFORE settings I/O;
sm_publish installs the wrapper only after all init failures are past. The
wrapper always delegates the complete original event first, preserves its
result, then verifies installed-slot ownership, menu state1, owned page identity,
focused native page, component existence and label ownership. Only a changed
save status causes native menu text and paint. The worker publishes atomic state
and calls original104064CC on the original event-flag handleA181F910, mask0x2.
Original1048B324 wait/clear loop dispatches mask0x2 as event3, whose original handler
polls the existing input queue; no key is injected and no timer slot borrowed.
Worker notification additionally checks bounded native menu stack/top-page and
its handle. It never writes native labels or performs paint.

Menu dispatch audit05 TERMINALPASS15: original event-flag wrapper, state
callback dispatcher and empty-queue handler execute; kernel event delivery,
empty input queue, incoming GUI state and text/paint services supplied. Guards
cover other focused page, inactive state, foreign slot, empty stack and absent
handle. Foreign callback rejects init before settings files and frees allocation.
Early audit fixtures omitted host status publication, then counted loader cache
operations as settings I/O; corrected observation/setup, not production guards.

Live .private/evidence/20261120-save-status-live-05 TERMINALPASS39, two fresh
QEMU processes/16PNG. Explicit owned create error80000002 preserves prior valid
record and dirty revision; native menu shows Save retry without another key.
Clearing the supplied error permits worker retry and Saved title. Fresh process
restores exact settings without rewriting files. Root/Standard/information final
comparisons match complete720x480 RGB across restart. All16 PNG hashes, four
closed-journal hashes, both journal CRCs and all14 captured row paint flags
independently verified. Saved/retry and restart information PNGs visually viewed.
Frozen helper code retained; final probe removes one trailing space only (exact
normalized-line identity verified), other two helpers match exactly.

Keep failed live02/03/04 as failures. Live02 remained stale. Live03 hit stock
Setup focus skipping unavailable rows; row navigation now follows native stock
focus movement while owned page0 still asserts exact adjacent rows. Live04
caught Saving after worker completed: two event-flag wakes may coalesce during
paint. Worker retries notification on its next normal tick. Capture now retains
ALL ready raw candidates and waits within the original bounded30-attempt paint
window for BOTH clean rows and current header; it never navigates or rewrites
text to settle. Final current-header check stays mandatory. This is bounded
asynchronous status observation, not a hardware/display fence.

Full persistence/status instruction05 PASS84 and root70/no skips PASS. Routing04
TERMINALPASS54 on current native bytes at
.private/evidence/20261120-save-status-routing-04.json. It adds native-call
elapsed/timeout diagnostics and gc.collect before each independent fixture load
to release unreachable old emulator/hook cycles. All54 original checks,30s wall,
10M instruction and ABI guards remain unchanged. This pass does not by itself
isolate why prior runs stopped in CRC loading. All jobs terminal; guests closed.
Earlier full/routing attempts stopped at the unchanged native-call guard in CRC
loading (11FA57xx); earlier output did not separate wall vs instruction limit.
No guard or timeout was enlarged.
Final code graph refreshed: 2705nodes/6988edges (ignored). Serialized retry
of full audit passed84. Do not attribute candidate02's84 to current source.

NEXT: visually validate startup-blocked/close-error states and longest title
fit (Composition/Information plus Restart to save), then continue original
highlights, portrait/rotation, EVF/AF/lens lifecycle and real statistics producer.
Current live scope covers saved/retry titles and three menus, not every status
pixel or all camera lifecycle states. Header dirty-node readiness is not yet
sampled separately from14 row nodes. Native Info mirror remains unresolved;
physical SD/controller/cache/shutdown/recovery gaps remain. No flash clearance.

## Save-state presentation implementation, idle-refresh gap - November 20, 2026

Previous01b6668 is PROGRESS: accepted two-boot persistence harness checkpoint.
This follow-up adds atomic worker-state publication and native menu title states:
Defaults, Saved, Unsaved, Saving, Save retry, Restart to save. Startup failures
and retained-descriptor failures block saves; transient save errors remain dirty
and show retry. Worker never updates native labels or performs menu paint.
Menu-only rendering observes current/saved revision without falsely marking a
new edit saved when an older worker snapshot completes.

PRIVATE CANDIDATE ONLY, NOT live accepted:
.private/builds/20261120-display-save-status-01, reproducible23408bytes,
image23104/BSS5648/API44/SHA
66411f9d8aed7c3491bc4cf9ee0cceb74d3969b1e2492f0699a486de2402f508.
Host09/QEMU unchanged. Full persistence/status instruction audit02 TERMINAL
PASS84; root69/no skips and routing01 PASS54. Instruction checks execute actual
menu titles for defaults/loaded/dirty/saved/retry/startup-blocked/close-latch,
including actual separate-stack menu edits during snapshot/write. Worker ticks
are asserted never to modify native labels. First audit attempt failed because
the parent fixture does not log menu labels; added explicit observation before
its unchanged native label-service fixture. No production workaround for that.
Old nonpersistent API40 full build compat01 remains byte-identicald4981187...15ffcd.

Live status01 TERMINAL FAILED at first-master-saved-native-header-status-current:
worker completed save, but the open menu title remained Unsaved. Root-initial
Defaults screenshot was visually inspected and fits. This is a REAL idle-refresh
gap in new presentation; do not relabel as pass or replace accepted persistent01.
The existing sm_before is a BEFORE-PAINT hook, not a continuous menu heartbeat;
its status check alone cannot schedule an idle repaint. No new worker-thread UI
calls or speculative event callbacks have been added. Native event2F2 is a map
sentinel, not an established timer. Do not reuse it as an invented heartbeat.
Longer title suffixes also need width validation/shorter page titles.
Final graph refreshed after code edits: 2685nodes/6922edges; ignored.

NEXT: establish a native queued menu-refresh mechanism with task/ownership
proof, or an appropriately guarded host/menu callback. Then show success/retry/
blocked states in live UI and rerun restart acceptance on the updated candidate.
Do not weaken the automatic-current-header check or settle for stale text that
updates only after navigation. Native API44 persistent01 remains the last
accepted live persistence profile. All jobs terminal; guests closed. No card,
camera, staging, flash or push. Full original feature scope remains active.

## Two-boot native menu persistence acceptance - November 20, 2026

Previous b6e91a1 remains the production module implementation. This milestone
changes the assisted-QEMU filesystem/stop harness only; native module/host/QEMU
bytes remain unchanged. No card/camera access, staging, flash or push.

Private evidence 20261120-persistence-live-04 is TERMINAL PASS: 22 checks,
two fresh guest processes, 15 PNGs. Native MENU edits enable master/battery and
disable Standard grid/shutter information. The resident worker saves through
original native wrappers into two explicitly modeled Z7J1 files. Their bytes,
not RAM, seed the second process. Startup restores exact settings without
rewriting either file. Three final menu comparisons (root, Standard, information)
are pixel-identical across restart, including complete 720x480 RGB frames.
Independent verification checks all15 PNG hashes, four closed journal hashes,
frozen helper source identity and all captured row paint flags clear.

SettingsFileFixture owns only A:\Z7CFG0.DAT/A:\Z7CFG1.DAT, with bounded reads,
80byte writes and nonreused owned handles. The immutable module fixture stays
separate. ModuleFileRemote serializes Ctrl-C with complete filesystem RPCs and
retains requested stops instead of silently resuming. The harness now lets the
native menu task run freely while servicing filesystem calls: calling native
delay on that task had starved its own queued repaint work. Captures require
all14 label/value dirty flags clear and matching native highlight pulse phase;
every ready candidate is preserved. No pixel edits, masks or tolerance.

Failed live01/02/03 remain private failures. An experimental unconditional text
rebind firmware change did not fix starvation and was REJECTED and reverted;
archive .private/research/menu-repaint-experiment is not production. Widget
inspection established native pool+4 is label-array offset1200, not row count.
Free-run-control01 passes as single seeded inspection only; live04 is the
accepted two-boot result. All associated jobs terminal, no guest left running.

Root regression: 69 tests, no skips; new8 filesystem and6 remote protocol tests.
Graph refreshed after code edits:2664nodes/6892edges (ignored). Source evidence:
evidence/20261120-persistence-menu-restart.json. This proves scoped modeled-file
startup/menu/worker/restart behavior, not physical SD/controller/cache durability,
shutdown flush, actual parallel scheduling or complete display/lifecycle parity.

NEXT: show unsaved/save-failure state in the menu, validate retries visibly,
then continue highlights, portrait/rotation, EVF/AF/lens lifecycle and real
histogram statistics. Native information mirror remains unresolved. No new
installation/recovery clearance; the full goal stays active.

## Native settings files + full background-save profile - November20,2026

Previous39a6dca turn was PROGRESS (journal policy). This turn implements native
file adapter AND startup/menu/worker integration in FULL profile, not only a
standalone policy. No physical card/camera access, staging, flash or push.

plugins/settings_files.c/.h owns A:\Z7CFG0.DAT and A:\Z7CFG1.DAT. Raw native
open1027BFA2 flags0/mode0; read1027C018 capacity81, require80. Native create
1027C0DA mode0 ->original1023F146 forces0301 ->descriptor mode026 and truncates
existing writable file. Write1027C048 requires80; close1027BFCC. Failed close
retains descriptor (including0), parks ALL I/O and prevents reinit/stale close.
Native absence80000010 bound by original10255D16 FAT root zero/exhaustion paths
and read-open propagation; sector/path services supplied, other card/driver
states remain unverified. Do not call every unavailable error 'missing'.
Owned192byte/aligned64staging, native clean101E9F38 beforewrite, invalidate
101E9F76 before/afterread. All3touched lines insideowned array; physicalcache/
durability NOT proved. Native1027BFEE is seek, NOT flush.

Native files01 builds reproducibly2764bytes/image2688/BSS156/API12/SHA
0d724be9f907954787894a5148e04b4f7403327dd5127784b1b89c5ea7da422b.
Files audit03 TERMINALPASS215 at.private/evidence/20261120-settings-files-03.json
on current harness:bothslots/lengths/all81 short-write prefixes/missing vs errors/
close-latch/caches/order/reloadjournal. Audit01/02 also215 historical; firstattempt
expected descriptor24 incorrectly, direct original execution showed26 (write bit
02), fixed fixture expectation. Adapter code was correct. No weakened ABI guards.

New examples/display_persistence_probe.c defines Z7_SETTINGS_PERSISTENCE and
includes FULL information/focal/Other/histogram stack. API44 checked before menu
preparation. All callback registrations including worker happen BEFORE config
I/O; then persistence_prepare loads on original loader task while native menu
tag and hostready remain0. No later init failure can free uncertain descriptor
state. Startup applies valid newest settings + batteryflag; missing/invalid uses
defaults without writing. Failed/ambiguous startup loading stays volatile for
that boot and BLOCKS saves until restart (no late worker model replacement).

Actual menu edits stage local model and atomically publish words between odd/
even revisions. Only changes dirty revision, not navigation/rejected no-ops.
Worker takes bounded3-attempt atomic snapshot, observes revision, waits2quiet
checks and saves on fourthtick. No paint/menu I/O. Save failures backoff5ticks;
close-latch parks foreverforboot. An edit during I/O remains dirty while the
older snapshot acknowledgement is saved; next cycle saves newer model.

Persistent01 reproducible22936bytes/image22656/BSS5584/API44/SHA
6ba9f4cfa6c247d3b6d8ce5023084dc16b83e516712bec97ea81769823a85bb6.
.private/builds/20261120-display-persistence-01 is current optional FULL candidate.
Current39 source hashes verified; host09 unchanged7d7356e7...d7f057/API44/state256.
Integration02 job50176 TERMINALPASS48 at
.private/evidence/20261120-display-persistence-02.json. Original menu activation
adapter, native files/cache wrappers and worker execute with supplied FS/kernel/
UI services. Actual menu callback runs on SEPARATE emulated stack while worker
is stopped mid-snapshot, then mid-file-write; workerCPUcontext restored. Tests
prove complete two-field reset snapshot, newer edit not falsely saved, later
save, old record retention and ABI/running-guard preservation. NOT actual native
scheduler/hardware timing proof. Initial integration01 job97924 PASS36 before
preemption extension. Earlier fixture missed loader stat op16 fallback, then
looked for optimized-away sm_action/sm_back symbols; fixed to actual sm_activate/
sm_back_event adapters. No production failure in these harness attempts.

Existing five-choice routing01 job89016 TERMINALPASS54 on SAME persistent01,
using --persistence-transport. Audit now accepts fixture_class so separate journal
files are supplied, not accidentally read from module-file bytes. API32host
rejects44early. Native adapter215 +integration48 +routing54 =317scoped newchecks.
Root55/no-skips PASS; py_compile PASS. Old API40full rebuildcompat06 EXACT
same d4981187...15ffcd (32currentinputs); old API32focalcompat06 EXACTsame
bd3c4cca...65c3b36 (28currentinputs). Modulehost/QEMU renderer unchanged.
Graph34528 TERMINAL2595nodes/6691edges after final code edits; generated ignored.
All jobs terminal. Source evidence:evidence/20261120-display-persistence.json.

NEXT: assisted-QEMU native menu save/restart/pixels on persistent01 with explicit
TWO writable synthetic journal files. Existing ModuleFileFixture retires after
module close BEFORE config startup reads, so it MUST be extended carefully to
keep settings service alive without reusing retired module handles or breaking
unrelated filesystem calls. Do not treat current instruction checks as live UI
or real-card proof. Also add clear unsaved-state presentation; model/status fields
exist but menu currently doesn't show save failure. Failed startup loading is
latched for thisboot intentionally. Lifecycle/card/cache/shutdown assessment stays
open. Broader EVF/rotation/AF/lens, highlights, portrait and real statistics remain
in original scope. Native Info mirror unresolved, visual acceptanceFALSE. Do not
return to rejected global texture flip. No new installation/recovery clearance.

## Two-slot settings journal policy - November20,2026

Previous5a71983 turn was PROGRESS (resident worker). New independent MIT
plugins/settings_storage.c/.h implements a two-slot journal behind an explicit
read/write transport. No native file adapter, filenames, worker registration or
menu synchronization added yet. Existing full display module05/host09 unchanged.
Z7J1 records are80bytes: magic/version/generation/outerCRC plus EXACT64byteZ7C1.
Both CRCs and all original model/target validation apply. Loader picks newest
modular generation; identical ties okay, conflicting ties/half-range ambiguous
and block publication/save. Missing/bad-length/invalid records differ from I/O
errors. Both known unusable slots -> defaults without writes. A valid peer may
load despite another I/O error, but any I/O error blocks save. No valid peer +
I/O error preserves caller settings. Save stages coherent payload before any I/O,
rescans both slots, skips unchanged, writes ONLY other slot, readback checks80
exact bytes before success. Old valid slot retained under one-slot transport
contract. An uncertain failed close may have committed full newer record; next
scan recognizes it. No assumed rename/replace atomicity or power-loss guarantee.

Storage01 compiled reproducibly SHAab1f6986...c94f944 and PASSED1680 checks.
Extended interface distinguishes known bad length IO_INVALID3 from I/O error2
and unknown statuses. Current02 PASS2020 on actual compiled ARM, no boundary
weakening. Added previous-valid-target torn replacements and pointer guards.
Current03 header-comment rebuild EXACT SAME BYTES as tested02; current8 input
source hashes verified.2440bytes/image2368/BSS376/API12; SHA
2b6daaa17daf46fe1a3eb79e62fd631c8ae6be9f14f67f398c390611f7cc779a.
.private/builds/20261120-settings-storage-03 is current diagnostic ONLY; it
registers NO callbacks and has supplied in-memory files, not native card I/O.
Audit02 at.private/evidence/20261120-settings-storage-02.json (job34071 terminal)
checks640 single-bit corruptions, sealed fields/lengths, generation ambiguity/
wrap, all81 cut points with either slot active, reported success/error, partial
replacement of older valid slot, uncertain commit/rescan, readback failures,
unknown statuses, no-op saves, mutation during I/O and null/overlap arguments.
All caller stack/callee-saved guards checked by fixture. Root55/no skips PASS;
py_compile PASS. Source evidence20261120-settings-storage.json. Job93206 was
old01 terminalPASS1680; graph41970 terminal2550nodes/6556edges. Final graph79560
TERMINAL2551nodes/6557edges after final code/comment edits; generated ignored.
All jobs terminal. No camera/QEMU job is live.

Pinned upstream sdk/config.h was retrieved successfully using GitHub fetch at
commit50a22b24c50619cffa646dac386e8334659f475a, now saved PRIVATE beneath
.private/research/z7ii-50a22b2/sdk/config.h with MIT notice intact. It directly
rewrites its file (no two-slot journal); no code/format/Z7II addresses copied.
Earlier web raw/blob requests failed but connector succeeded, so do not treat
this file as still unavailable. No network source execution.

NEXT: bind original-Z7 native IO to the four-state transport and coordinate
startup load/menu snapshots/worker debounce; no storage I/O from paint/menu.
Require confirmed missing-file status, not generic open-unavailable. IO_OK means
exact80 bytes, IO_INVALID3 means known wrong-length record, ABSENT1 means confirmed
absence, ERROR2/unknown means read unavailable. Short writes and close failures
must fail and retain unknown descriptor state; no stale-handle retry. Proposed
slot filenames not bound in code yet. Inspect native filesystem/cache contracts
below, then implement native adapter+instruction failure audit before live model.

STATIC ORIGINAL leads (NOT yet executed write/rename/cache audits):
1027C0DA create(path,mode) ->request0D ->handler1027BBE8 ->1023F146 ->10277F78
with flags0301;1027C048 write(fd,buffer,count,actual) ->request09 ->1027BB96
->1023F0CC ->1027817A.1027BFCC close(fd)->request06->1027BB4C->1023F086.
1027C018 read()->request08->1027BB7C->1023F09A.1027BFA2 open(path,flags,mode)
->request05->1027BB46->1027C616. Native task callback1027BAC0 uses jump table
1027BADA+2*table[opcode].1027C102 two-path request0E ->1027BC0E ->1023F150
->10278A98 rename lead; atomicity unproven and two-slot journal doesn't need it.
1027BFEE request07 is SEEK (64-bit offset in R2/R3), NOT flush; don't use as flush.
1027C4B8 request21 goes1027BDC8->1027B964.1027B964 is a conditional volume
maintenance path, NOT established durable flush. Original native cache-clean
101E9F38 loops MCRc7,c10,1 and adds extra64bytes (pad aligned DMA arrays!),
invalidate101E9F76 as existing loader. Original write input/output and real card
cache effects remain unverified. Keep native contracts separate from policy.

Mirror remains unresolved; highlights/portrait/lifecycle/realstats stay in full
scope. No camera/card/staging/flash/push. Full goal remains active.

## Resident task callback for persistence - November20,2026

Saved prior native-texture work source-only in58639ac. Continued building beyond
that investigation. New API44 sdk/worker.h appends init-only register_worker to
unchanged API40prefix. Existing loader task now delays1000 then dispatches an
owned callback after successful initialization. No paint/menu I/O. State remains
256bytes/old offsets; reserved words49..52 now callback/registered/running/code
length. Registration rejects null/foreign/even/BSS/duplicate/late pointers;
failed init clears before free; dispatch checks guards/status/residency/code
bounds and atomic non-reentry. Callback owns its work bounds/shared-state locking.
No card readiness, shutdown flushing or hardware delay units are claimed.

Private host09 MAIN33058860/resident4593, reproducibleSHA
7d7356e7775db90483ed9fe5598f401afb7fb8498a7b42bd71900db849d7f057.
Host08 remains preserved; do not substitute prior host08 visual evidence as
host09 full-profile validation. Existing module05d4981187...15ffcd unchanged.
Worker-probe01 384bytes/image320/BSS24/SHA
428a947e16a756a659a0a88df6dbed67f8ca06d3378ea41baae3efd4aa5db83e.
worker-diagnostics01/probes contains reproducible success/failure builds.

Worker instruction01 PASS55 (actual loop success/failure/missing retries included).
Loader99/display316/GUI122/information116 PASS on host09. API40host rejects44
probe. Information audit now checks minimum40prefix instead of exact hostcapacity,
reports actual44. Root55/no-skips PASS. One harness attempt initially read a
nonexistent diagnostic SHA metadata key; fixed to record packet SHA. Another
misread calls as0 when deliberately clearing image pointer; stable probe address
now verifies actual memory, not missing-state-derived count. Neither was a host
callback failure. First compile missed nested api.information field; corrected
before any candidate was produced.

Live worker job51734 TERMINAL PASS11 at
.private/evidence/20261120-worker-live-01. Counter2->5 under free running after
module FS fixture retired, guard clear and native MENU still works. No supplied
counter stores/paint triggers. MENU PNG hash verified; helpers frozen beside run.
QEMU unchangedf76609ae...9b45c98, all5source+binary hashes verified. Host11source
and worker9source hashes verified. Live worker is not full-feature display/pixel
acceptance. Full routing host09 audit6162 TERMINAL PASS54 on unchanged full module05.
Total scoped instruction checks762; these are not complete pixels/lifecycle.
Final graph73545 TERMINAL:2514nodes/6451edges; generated graph ignored.
All jobs terminal. Source evidence:evidence/20261120-resident-worker.json.

NEXT: settings persistence now has a worker execution path, but NO file load/save
implementation. Establish original-Z7 write/flush/replace contracts before wiring
I/O; no config.h was saved in pinned-source snapshot, do not assume it exists.
Read-only loader contracts are in Z7_MODULE_HOST_RESEARCH.md. First native leads
from exact stock:102D86B0 is the file-object wrapper via function pointer1027C048
(write request opcode9);102D86A0 is its read sibling via1027C018. These are STATIC
LEADS ONLY, not yet independently executed write/flush semantics. Do not infer
flush/rename contracts from neighboring functions or copy Z7II addresses. Preserve
last known valid configuration on failure and keep I/O off paint/menu callbacks.
Native Info mirror remains recorded, visual acceptancefalse; do not resume global
flip experiment. Highlights/portrait/lifecycle/realstats remain in full scope.
No camera/card/staging/flash/push. Full goal remains active.

## Native texture contracts; global flip REJECTED — November20,2026

Previousd3a932a turn was PROGRESS. This turn does NOT fix native Info mirroring.
Production GPU header is BYTE-IDENTICAL tod3a932a (and original QEMU manifest);
no experimental shader was built/run in QEMU. Emulator remainsf76609ae...9b45c98,
all5 source/binary fingerprints verified. Module05 d4981187...15ffcd and host08
unchanged. Never add app13 flips, flip evidence images or relabel failed runs.

A global V reversal + GUI-preview reversal experiment was tested ONLY in standalone
C. Initial 'negative-Y copy is identity' expectation was INVALID. The added
native HUD registration control REJECTED the candidate (line172 in private saved
candidate), because it moved the registered output window. Production code was
restored. Accepted tests now explicitly cover reflected vs positive transforms,
two reflections composing to identity, A8/YUV rows, native HUD registration and
lower-left GUI-only preview.351renderer checks PASS; all prior330 expectations
retained. Larger console test adapter permits actual720x480 preview checks.
Private `.private/research/texture-origin-experiment/README.txt` marks candidate
REJECTED; do not apply its .h. Root55 and QEMU Python23/no-skips PASS.

New tools/graphics_api_observer.py installs bounded hardware breakpoints and
single-steps ORIGINAL native prologues, without rewriting guest code/arguments/
returns. Native public entry map derived from ORIGINAL RAM export names/pointers.
Failed live01 job66985 retained: capture pause timed out while hooks remained
active (64valid native prefix observations do not make that run a pass).
Fix: api_stop BEFORE free-running capture. Live02 job57164 TERMINAL PASS24checks/
5frames at `.private/evidence/20261120-information-api-live-02` with same f766/
module05/host08.9observed vgDrawImage calls, ALL LR10430A9B, original push executed
nextPC10450C88; no count cap reached. All5PNG hashes verified. Timing is diagnostic,
NOT hardware timing.63supported read-only LCD parameters per frame include BOTH
overlays and region/bank controls; horizon→Info differs ONLY four buffer addresses
(2440/24C0/210/220). No interrupt/W1C reads. No live jobs remain.

New audit_z7_texture_controls.py PASSES104checks:12named exports,28initializer
prefix cases,64sampler prefix cases. Exact original stock required. Native
1047E814..E844 copies allowed-quality→descriptor24 and kind→48; supplied args only,
not complete image creation. Native104B92EA..9318 sets sampler bit0 for kind4,
mask06 only when descriptor quality mask0x4 and context value4, and20 for formatC.
Thus flags1 versus7 are QUALITY-dependent; don't treat them as orientation flags.
Hardware row origin remains UNPROVEN. Source evidence native-texture-contracts.json.
OpenVG1.1 spec10.1/10.8 distinguishes image coordinates and applied transforms;
it does NOT specify this chip's raw-memory/register interpretation.

Useful next native leads: DMP image extensions vgCreateImageStandardDataDMP
104514E8 (kind4 initializer path10483BD4), vgCreateImageBufferPointerDMPX104516C6
(wrapper→10483D7C), constructor calls10483B7C/10483D16→1047E814. Standard vgCreateImage
10450B36→1047EAC4 passes kind1. Inspect external-image/backing-store and path-state
contracts before another shader change. Public sampler0x153 header01531004 is
loaded104B9436/104B99E2, not full-mask0153F004. Naming/quality do not prove origin.

Keep the Info mismatch recorded as an independent emulator-model gap (it occurs
with custom routing OFF); it must not monopolize progress on the remaining real
feature ports: persistence, highlights/portrait and broader EVF/rotation/AF/lens
lifecycle/real statistics. Full scope stays active, visual acceptance remains false.
Graph refreshed:2494 nodes/6396 edges; generated graph remains ignored. No camera/card/staging/flash/push.

## Native Info MENU preserved; gated GPU capture — November20,2026

Previousc688d4d turn was PROGRESS (full five-choice routing). This turn makes NO
host/module C change: current information05 remains d4981187...15ffcd, API40,
20748bytes/image20480/BSS5508. New generic GPU observer is explicit opt-in, host
file gate,512draw cap/1MiB per-file cap; captures exact draw/path registers,
segments/coordinates and bounded textures to PRIVATE files. No guest-state or
rendering alteration. Default disabled and inherited env cleared in interactive.py.
330production GPU checks PASS including gate/bounds/nonmutation; QEMU Python23
and root55/no-skips PASS. QEMU rebuilt with root Windows setup; binarySHA
f76609ae4cb96060ca1593a352a7ec3fc6af7e29473db756b4bbebf699b45c98,
all5 source/binary hashes verified. Firmware-free QMP smoke PASS with manifest
native_runtime_path in PATH. First bare-path smoke failed with no QMP (DLL path
missing); corrected runtime, not a rendering change. Jobs71119/89478 terminal.

MENU lifecycle live01 job82706 TERMINAL PASS42checks/10frames:
`.private/evidence/20261120-information-lifecycle-live-01`.
Original/custom information stay app13/page4 under MENU and on return. Master OFF
while MENU open defers until close, then returns app0/user page3/all61 masks.
All10 PNG hashes and frozen lifecycle helper verified; raw native/owned MENU viewed.
First native MENU enters page1+19 row0, owned later MENU enters only page1 row0;
this is NATIVE remembered focus, confirmed by repeated inactive control below.
No app/snapshot/mask/pixel/lens input stores supplied.

Graphics live01 job50290 TERMINAL PASS22/4frames, early native Info entry capture.
Graphics live02 job84803 TERMINAL PASS36/9frames, settled refresh + TWO original
inactive MENU roundtrips. Both use same full module with custom inactive.
Both original MENU paths match lifecycle: first1+19 then1 alone. Owned MENU frame
is EXACT COMPLETE RGB match to second inactive native MENU. All9+4PNG hashes
verified. Helpers frozen per run; live02 frozen helper matched source before final
metadata clarification. Old custom_information_implemented:false marker described
inactive CONTROL, not module capability; source now separates implemented/active.
No live jobs remain. Main-frame RGB identity is NOT asserted beyond matched MENU.

Each capture has512draws; early lifecycle cap spent487onhorizon/25Info (not useful
for Info glyphs). Info-only early capture includes upright A8 glyph source samples
(raw source-glyphs.png viewed). Settled capture records repeated RGBA
B045F200→B090F200 copy (source flags1, negative-Y texture matrix), then
B090F200→LCD YUV copy (flags7, negative-Y matrix). Cause of mirror NOT PROVEN.
Do not flip images or add app-specific scanout rules. Inspect original copy/image
contracts and complete display controls; same primitive/register patterns alone do
not prove orientation semantics. Large >1MiB textures are intentionally omitted.
Private capture-manifest.json files verify all bounded dumps; source evidence
20261120-information-menu-graphics.json. Original nativeInfo glyph mirroring remains,
visual acceptance FALSE. No new GPU rasterization fix claimed.

NEXT: use captured settled copy0031/0032 and native builders to establish why Info
copy differs, without blindly rerunning MENU or earlier successful routing tests.
Original10452B24 emits graphics command words;1048587C/10485Dxx are image/paint
builder leads. Broader EVF/rotation/AF/lens lifecycle, highlights/portrait/persistence/
real histogram statistics remain in full scope. Graph37256 refreshed2477nodes/6348edges; generated graph ignored.
No camera/card/staging/flash/push. Full goal active.

## Full five-choice routing validated — November20,2026

Previous5159f8b turn was PROGRESS. New API40 `display-information-probe` includes
FULL focal/Other/histogram stack. Current04 is20748bytes/image20480/BSS5508,
reproducible SHAd49811875af0304f5c18a2f6b182fb2bf79419fe43b7ad6d316ecefabd15ffcd.
Comment-only rebuild05 has EXACT same package bytes and current32 source-input
hashes verified. Host08 unchanged. Deferred native Info entry waits for masks/base/painters,
rechecks native eligibility and preserves user baseline. Native admitted exit,
information-only, master-off and disabled-current routing implemented. No fake
keys or app/registry/snapshot/pixel stores implement transitions. Ordinary native
settings-exit primitives retain delayed-property0/app13 as pending and handle
partial publication/retry. Failed entry parks until master OFF; foreign state
preserved. API40 checked BEFORE native menu preparation. Old API32 focal rebuilt
compat05 exact bd3c4cca...65c3b36. Current04 module source-input hashes verified.

Current04 audit06 PASSED54 routing checks; helper03 audit05 PASSED182transition;
current04 focal audit04 PASSED45; current04 root55/no-skips PASS. Native setter,
key admission, request primitives and native exit execute in instruction tests;
manager/app initialization, property services/rendering remain supplied there.
Earlier first-audit disabled-Info reselection bug fixed to next enabled preset0.
Deferred secondary-gate test initially failed because inherited histogram fixture
supplied gate2/2A as0; dedicated native DISP gates fixed fixture, not weakened test.
Superseded candidates01/02/03 remain historical, not current accepted artifacts.

Live02 job21326 TERMINAL PASS43checks/15frames at
`.private/evidence/20261120-information-routing-live-02` on CURRENT04/host08.
Actual apps0→13→0; four presets, all61 masks, saved native page3,
information-only DISP consume and master-off restore. Later explicitly supplied
lens1/245 phase paints24.5mm, native painter retires before Info entry, then focal
reappears on return and master-off restores native horizon/page3. No native app,
snapshot, mask or pixel stores supplied. All15PNG hashes/frozen helper verified;
fixed focal crop[156,275,313,310] changes from pre-focal control, returned crop is
EXACT, master-off window matches original native background. Raw visible/returned/
retired/master-off frames VIEWED. No whole-RGB identity claim. Private independent-
verification.json retained. Source evidence20261120-display-information.json.
Native Info text is still vertically mirrored; visual acceptance FALSE.

Live01 job7745 terminalPASS35/11 on superseded02, all11PNG hashes verified. Main
jobs43556/44078/62588 terminalPASS54/45/182; previous87837 handle expired but
its audit05 result independently verifiedPASS51. No live jobs remain. Graphs84241/62426
terminal2462nodes/6309edges after final code/comment edits; generated graph ignored.
Host99/316/122/116 are existing scoped HOST checks, not a broad five-choice claim.

NEXT: native-information orientation investigation and MENU/output/lifecycle
integration on the current full profile. Do not flip screenshots or hardcode an
app13 flip. Prior readonly LCD geometry/format flags match across states except
buffers; GPU texture/orientation semantics need native contracts. Preserve strict
focal retirement/return pixels; do not blindly rerun or relax earlier failures.
Broader EVF/rotation/AF/lens lifecycle, highlights/portrait/persistence/real histogram
statistics remain in full scope. No camera/card/staging/flash/push. Goal active.

## Information transition ledger — November20,2026

Resumed after Windows update. Host API40 is saved in local source-only7c3be7d;
all388 indexed source hashes verified. New production helper
`plugins/information_transition.h` and instruction diagnostic compile
reproducibly: transition01 SHA8b946c864bfaba71208d6423305339990c1700f226cf56653c7760b165f0f2be,
1088bytes/image1024/BSS20, API12 (no callbacks registered by this diagnostic).
The helper is NOT yet connected to the combined custom-DISP module.

Transition audit02 PASSES160checks; root55/no-skips and py_compile pass. Actual
original setter/getter/native request helper and admitted native exit execute;
property services, parent request sink and manager/application publication are
supplied. Preserves saved user page separately from applied page and intermediate
return0; checks asynchronous entry, original-key exit, four saved baselines,
failed setter partial publication/rollback/retry, foreign bindings/pages, deferred
output return and non-authoritative parent return. No app/registry changes across
helper calls. Caller must FIRST verify overlay/mask/base release; boolean precondition
is tested, actual component release/pixels remain unverified. New source evidence
20261120-information-transition.json. Does NOT establish five-choice routing.
No live jobs remain. Sessions14147/7478 terminalPASS137/160 respectively; graph43593
terminalPASS2418nodes/6164edges; generated graph remains ignored. First loader experiment with a global Unicorn
write hook failed inside native filesystem; removing that observer restored the
unchanged loader. Final audit compares app/registry before/after each operation;
it does not claim temporal memory-write instrumentation.

NEXT: wire ledger into new API40 five-choice diagnostic, preserving old profiles'
bit16 rejection until complete. Integration needs native admission on both sides,
component retirement/cleanup, asynchronous pending state, menu disabled-current
reselection and master-off Info exit; use original native exit contracts, not fake
DISP keys or direct app writes. Do not mistake isolated transition success for
actual app initialization/pixels. Full combined focal/histogram profile, orientation,
EVF/rotation/lifecycle/persistence/highlights/portrait/real stats remain open.
No camera/card/staging/flash/push. Full goal active.

## API40 information host completed — November20,2026

Restart recovery: job67221 TERMINAL PASSED21checks/4frames at
`.private/evidence/20261120-information-host-native-live-01`. Host08/API40 with
UNCHANGED focal03/API32. Native apps0,0,13,0/pages0,3,4,0; original key/event
unchanged, resident information-update wrapper11FA59E1 executes original updater.
All4 PNG hashes independently verified. Information RGB is EXACTLY identical to
previous host07 control; mirrored text remains an emulator issue, NOT accepted
visuals. Read-only LCD geometry/format flags are identical across four states
except buffer addresses; these registers do not yet explain orientation.

API40 now IMPLEMENTED: sdk/information.h retains complete32-byte GUI prefix.
Owned init-only admitted Info-DISP and before-Info-update callbacks; native key/
event slots untouched, wrapper skips stale updater if callback changes app.
Full register/LR/NZCVQ delegated-prefix continuity, guarded context, reentry,
failure cleanup and old API32 compatibility. Host08 MAIN SHA
6ea33985de7c0d35c2f6b026157595b56fdd9167aa79df53cded25e2f25c87ac,
33058548bytes/resident4281/state256. Reproducible build passed.
New host audit02 PASSES116checks. Existing loader99/display316/GUI122/native47/
focal45/root55 PASS. Original updater is an explicit instruction-fixture sink;
live compatibility separately executes native updater with custom callbacks absent.
Source evidence20261120-information-host.json records limits. No active live jobs.

NEXT: actual five-choice module ownership/routing, preserve saved native page
across Info entry/return, failure rollback, menu reselection and master-off. Current
profiles still reject bit16. Orientation investigation remains open; no hardcoded
app flip or edited evidence. No camera/card/staging/flash/push. Full goal active.

## Focal horizon accepted; information app bound — November20,2026

Previous goal turn progressed0a78afd (native control/GPU correction). Current
worktree resumed clean. Job14000 is now TERMINAL PASSED88checks/54frames:
`.private/evidence/20261120-focal-horizon-live-03`.
Unchanged focal03/host07, rebuilt QEMU91652e21...84c6. Initial whole-native
reference qualification takes23frames; after Other ON/Focal OFF,18frames restore
the ORIGINAL settled native RGB twice per ISO phase. Both histories retain
24reference cap. Fractional/whole, Other OFF, component OFF, reenable, absent
lens with stale245, return and master OFF pass exact comparisons. All61masks and
saved page0 restore. Source1C14/1C01 inputs are explicitly supplied, not hardware
telemetry. No native snapshot/visibility/pixel stores, ADL exclusions, tolerance
or composed references. All54 PNG fingerprints,7 memberships and18 post-Other
qualification records independently verified; verified-focal-horizon-crops.png
viewed. Earlier failures remain failed. New source evidence focal-horizon.json.

Native information control43430 is TERMINAL PASSED21checks/4frames at
`.private/evidence/20261120-information-native-live-01`, unchanged host07/focal03,
custom inactive/QEMU91652e21...84c6. Native setter establishes baseline0/3;
actual DISP enters13/returns0. Native page/property0,3,4,0; all61 masks/key/update
callbacks unchanged, Focal/base inactive. All4 PNG hashes independently verified.
Return RGB differs only within native ISO box; full RGB identity was NOT a gate.
IMPORTANT: inspected information panel is vertically mirrored in emulator.
Routing21 pass is NOT visual acceptance; cause unproven. Do not flip captured
images or hardcode an app13 flip. Derive actual display/GPU orientation flags.
No live jobs remain. Frozen sources/private independent-verification.json kept.

Native information page independently binds application13 (NOT15), descriptor
A182D16C, key-slotA182D180=102FD647, update-slotA182D188=102FDA09; separate snapshot
A20210C0/state2Dlow6; current-app byteA1829AF4; registryA20207BC. Native audit01
PASSES47checks:16 manager-selection cases/10 native key-admission cases plus
registry/getters/parent registration/entry. Registry construction executes before
initialization; manager selection stops1030D33E before final app work. This is
NOT a custom native-information implementation or completed app-transition proof.
Read Z7_INFORMATION_APP_RESEARCH.md and evidence/20261120-information-native.json.

Actual entry:1037061C page3→4 calls original setter then getter1030D50C/helper
103EB7C4, emits parent command4/payload108000, returns2. Native selector admits
photoLCD app13, rejects movie/EVF to0. Native info DISP key29 preserves filters,
gates, snapshot states2/5 and exclusions, then stores2F15=0 and requests100000
return. The original entry still requests transition if property write fails;
a new adapter must verify property/snapshot and retain conditional rollback.
Adjacent original app15=A182CF00 is distinct; do not borrow Z7II's numeric15.

NEXT actual feature work: implement owned native-information admission/update
bridges and additive host API, then finish all5-choice module routing, replacing
bit16 configuration rejection only when complete. Preserve actual native input
admission, initialization failure cleanup, native return/parameter-display state,
conditional base/mask/overlay ownership and current variant regressions. Entry/
return needs live verification. Preserve the ORIGINAL user native page across
the owned information round trip; do not resave intermediate native return0 as
the user's baseline. Information-only, disabled-current reselection,
master-off/MENU/output gates remain. EVF/rotation/AF/focal broader lifecycle,
highlights/portrait/persistence/real stats remain in full scope. No camera/card,
staging, flashing or push; full goal stays active.

Implementation lead: native Info DISP has completed original filters/gates/
state2/5/exclusions at102FD7DA, before native exit work. An additive API40 can
register an admitted-information-cycle callback and before-information-update
callback while preserving API32/state256 prefixes. Preserve original R0-R12,
LR/NZCVQ and native post-key flow; delegated displaced prefix calls1040A4AE,
conditionally103FEC18, compares3, then resumes102FD7E6 or102FD7E8. Delegated paths
must restore the original displaced-call LR (102FD7E5 or102FD7DF respectively).
Consumed path can resume original post-key102FD9B4. Wrapper on initializerA182D188 can run an
owned pre-update callback then call original102FDA09 if app remains13, always
delegating unchanged when absent. This is a PROPOSAL, not implemented. Keep
original Info key/event slots unchanged and test absent/invalid/reentrant/failure
paths before implementing five-choice ownership. The orientation issue can be
investigated via read-only LCD/GPU register capture alongside that compatibility
control; native drivers10241706/10242A2C are leads, not proven flip semantics.

Graph refreshed2367nodes/6032edges after native information tools, ignored;
graphs12011/16203 TERMINAL. Production C unchanged this turn; no blanket regression
rerun. Scoped native audit47 and py_compile pass; source manifest refreshed at
checkpoint. Full software scope is not complete.

## Native Other control and GPU no-op correction — November20, 2026

Previous goal turn progressed: local checkpoint30ec5d0. This turn's focused
control01 `.private/evidence/20261120-horizon-other-control-01` PASSES156checks/
50frames on UNCHANGED pre-fix QEMU1a651c1b...d4def and focal03/host07. Focal was
NEVER enabled: object/samples/paints/presents all0 in every frame; no incoming
lens property writes. Native ADL pixels drift65pixels with IDENTICAL284byte
ADL objects. Complete RGB qualifies after22before/24after references; settled
Other OFF/ON returns EXACT native RGB in BOTH ISO phases. All61masks and saved
native page0 restore. All50PNG/100object fingerprints and2whole-RGB comparisons
independently verified. This excludes focal as the cause of that baseline drift;
it does not reclassify old combined failed runs as passes or certify hardware.

Separate REAL emulator bug: alpha0 SRC_OVER round-tripped untouched YUV through
lossy RGB conversion and changed storage. New production test first FAILED on
unchanged rasterizer. Skip this no-op BEFORE destination conversion; SRC alpha0
still clears.316GPU checks now pass, covering solid/texture/modulated texture,
105/106/107 alpha8/alpha4;398ISP checks pass(total714). Root55/no-skips and QEMU
Python23 pass; original restricted Python run failed WinError10013 sockets and
is retained, allowed-localhost rerun passed. QEMU rebuilt through root Windows
instructions: SHA91652e21c8a75ff923e26feb8111e456003a5baeeb58efbdbf5241160cbe84c6;
firmware-free localhost QMP smoke passes. No native firmware/module C changed.
ADL PNGs2968/2969 are opaque; this fix is NOT a proven ADL cause or hardware GPU
accuracy claim. Source-only GPU/control evidence files dated20261120 record scope.

LIVE JOB14000: `.private/evidence/20261120-focal-horizon-live-03`, unchanged
focal03/host07 on rebuilt QEMU. Poll SAME14000; do not restart on observation
timeout. Combined helper now keeps Focal OFF after Other ON until complete RGB
matches the ORIGINAL settled native frames twice per ISO phase. SAME24reference
cap, no edge exclusions/tolerance/composites; based on successful no-focal control.
It then tests reenable, absent/return and master-OFF. Not yet a passing run.
Control28754, build58217, Python32617/14593, renderer5924 and graph70371/84365
TERMINAL. Graph refreshed2344nodes/5977edges after latest helper edit, ignored.

Reconnect lead: native1015E508 compares current lens-context6 with published
type-cache18 atA18D3E90, publishes1C14 only on change, leaves1C01 untouched.
Seven private native-call cases pass with supplied context/publication; this is
NOT actual same-type reconnect proof. Trace native attach/cache reset/order
before claiming freshness. No sampler change. Broader EVF/rotation/AF/menu/output,
information app/highlights/portrait/persistence/real-stats/software scope remains.
Full goal active. No camera/card, staging, flashing or push.

## Restart recovery and native layout — November 20, 2026

Resumed after Windows update from93a20a2; source and current private module
fingerprints verified. No production C or package change. New native-layout
audit PASSES175 checks/20 text cases/five constructor cases. See
FOCAL_LENGTH_RESEARCH.md and evidence/20261120-native-focal-layout.json.
Original text/constructor geometry and font selection execute; allocation,
list insertion and drawing boundaries remain supplied. EVF/rotation
pixels are not established. Corrected misleading native function names below.

Focal/horizon live01 is TERMINAL FAILED16/17checks,10frames. Native24.5mm
paints, then whole-frame membership outside the owned window fails on the ADL
edge:64/65/84 pixels against same-ISO-phase references. ADL masks/controls match;
the focal-disabled reference frames already vary in that area. Failed run and
private inspected crops retained. No exclusions, composites or relaxed checks.
Revised fixture requires whole-native RGB to repeat within each ISO phase.
Live02 is TERMINAL FAILED61/62checks,33frames on UNCHANGED focal03/host07.
Baseline converged at23references; fractional/whole text match settled complete
native RGB outside the owned window. Other OFF retains identical focal crop.
After Other ON/Focal OFF, RGB matches TRANSIENT reference1, not the settled
baseline. Focal reenable then differs on40 ADL pixels at626,6..649,50 against
ALL same-ISO-phase references. No absence/return/master-OFF checks were reached.
All33 immutable PNG fingerprints and every recorded full-frame membership were
independently rechecked; failure remains failed. BOTH97949/29488 and Graphify
jobs34833/22645 are terminal. Do not poll/restart them. No live jobs remain.
Graph refreshed2337nodes/5956edges and remains ignored. Full goal stays active.

NEXT: focused Other OFF/ON horizon control with Focal NEVER enabled, to isolate
background reconstruction from the owned focal object. Capture complete native
RGB before/after that SAME history, qualify phases/repetition, preserve strict
comparisons. Then inspect original ADL clear/draw/GPU commands as needed. Do not
blindly rerun the long combined probe, extend sample caps, exclude edges or call
the failed runs passes. Existing GPU model uses approximate YUV/alpha; this is
a lead, NOT a proven cause. Native layout bindings above prepare EVF work, but
base/readout/focal policies still admit LCD only. Remaining full software scope
continues below. No camera/card, staging, flashing or push.

## Independent focal overlay — November 20, 2026

Previous turn made progress: live sampler5fc3ff6. This checkpoint adds a separate
native focal object1198/label298, LCD landscape window110,194..220,218, decimal
text and100ms bounded source/repaint cadence. Battery1199/299 and native VR50
controls remain separate; Other OFF retains focal text. Optional after-GUI
wrapper retains the histogram callback. Full goal stays active. No camera/card,
staging, flash or push. ALL jobs TERMINAL; do not poll/restart old handles.

Current module03 `.private/builds/20261120-display-focal-03` is reproducible SHA
bd3c4ccad9a5ec7dbebd4e3075c3119c9bdbde385c688a26a7a089c8e65c3b36,
17420bytes/image17152/BSS5444/API32, host07 unchanged. Source inputs verified.
Module01 e532e7b4...390c5 was17292/image17024; transient02 b26ca512...31e2b is
superseded. Existing Other rebuilt on current source remains byte-identical
cbadda7a...6ae8d. Root55/no-skips pass after final C/timing edits.

Current03 policy focal-overlay-04 PASSES45checks: native allocation/initialization
and source reads, fractional/integer text, independent Focal/Other, all4 supplied
current preset states, foreign labels/slots, detached objects, missing data,
RAM-only painter guards, native HUD delta and failed-submit retry. Actual native
key cycling is separate prior coverage, not inferred from supplied preset states.
Current03 base02 PASSES68/histogram02 PASSES170/grid02 PASSES282(nativegeometry109)
and Other01 PASSES1627. Private files have prefix20261120-focal-current-.

Live03 `.private/evidence/20261120-focal-live-03` PASSES20checks/13frames on03.
Properties1C14/1C01 are explicitly SUPPLIED lens inputs, not hardware telemetry;
no native snapshot, visibility or pixel stores. Native24.5mm/24mm differ only
inside the owned window. Other OFF keeps the SAME focal crop. Focal OFF, absent
lens with stale245, and master OFF restore complete captured-native RGB. All61
masks restore; saved native page0 returns with base ownership inactive. All PNG
fingerprints and7 whole-native-reference membership comparisons independently
rechecked; exact Other-OFF crop equality verified. Private verified-focal-crops.png
inspected. No composed references/excluded pixels. Independent-verification.json
preserves the checks. Standard base covered; focal/horizon combination still open.

Retain failed live01 (baseline raw DISP reached2 rather than3; fixed with existing
key-and-wait helper). Retain live02/module01 REAL repaint failure: Other OFF
erased focal pixels with cached24mm, paints/presents stayed2; private crop viewed.
03 fix: mask changes OR actual current/previous native HUD snapshot delta request
repaint even when label unchanged. This is INVALIDATION INPUT, NEVER a completed-
paint fence. After GUI revalidates context/ownership/busy, maintains100ms cadence,
requires own painter invocation before extra present and retains failed-submit
requests. Labels/objects are reused. No legacy VR controls edited by focal.

Earlier current base/histogram/grid01 calls did not return under10s wall bound.
An unchanged-module load diagnostic with SAME10M cap/APCS guards returned8 in
10.703s under30s. Shared HostFixture now allows30s; direct NativePNG still defaults
10s. All original instruction caps/stack/callee-save checks remain. Current02
regressions above pass; module C was not changed for the harness timing issue.

NEXT: focal/horizon live combination, EVF/rotated layout and AF/alternate states;
then native MENU/output/lens reconnect lifecycle. Current focal path rejects
EVF/rotation/AF rather than applying old LCD coordinates. Original VR widget50
has separate whole-mm text2 and is already under Other masks; do not hijack it.
CORRECTION:10369214 propagates control dirty state;102F27A8 selects native
permission/visibility masks. Neither identifies text rectangle placement.
Actual constructor102F17B8 and text wrapper102F32AE copy per-scene rectangles;
see the175check focal-layout audit and FOCAL_LENGTH_RESEARCH.md. Current old ADL
horizon65edge-pixel mismatch remains unresolved;15check updater equivalence only
narrows it. Native information app, highlights, portrait, persistence and broader
combined lifecycle remain. Read FOCAL_LENGTH_RESEARCH.md / DISPLAY_SETTINGS.md.

Source-only evidence `evidence/20261120-native-focal-overlay.json`. Graph used and
refreshed2324nodes/5914edges, ignored; manifest refreshed at local source-only
checkpoint. No hardware lens/card/cache/installation/recovery claim is made.

## Live focal source and compiled sampler — November 20, 2026

Previous goal turn made progress (native mm text and ADL request isolation,
f98fd35). This turn independently binds the original live focal source and adds
a compiled sampler. All jobs TERMINAL. No QEMU run, camera/card access, staging,
flash or push. Full goal stays active; display overlay is still to implement.

Original PTP property5008 descriptor10341856/get-value103418B6 call1034231A.
That native function uses103FE85E to read1C01 and multiplies by10. Primary
libgphoto2 ptp.h identifies5008 as FocalLength; ptp.c's rendering table uses0.01mm
per wire unit. Thus original1C01 is tenths of mm. These sources were consulted
only for protocol semantics; no gphoto implementation copied. Original keys,
not upstream Z7II20xx:1C14 type @A24E2600,1C01 focal @A24E25A8. Raw bank20 has
only6entries; LensInfo selector2001 returns0/2014 reads one packet flag. Those
alternate namespaces are NOT this live source. Private query-xrefs JSON records
exploration only, not semantic proof.

Live producer1016342E (LensInfo.c) reads type fromA18D3E90+6. Type1 uses native
queries309E/309D then1015BE8C; supplied24/32768 publishes245. Type3 uses601D then
original encoded LUT10204FCC. Native setter101645EC publishes1C01 only on change.
Types0/2/4 may retain a previous valid property when cached value is already
valid: module MUST gate on type, never solely value. PTP's native admission also
accepts4; the new electronic-lens feature deliberately accepts only1/3 as pinned.
Initial audit01 had the wrong PTP-type4 expectation; corrected fixture02 passes,
no production fix. No successful hardware telemetry or lens reconnect claimed.

New `plugins/focal_sample.h`: original getter103FE85F, reads1C14, accepts1/3,
reads1C01, rejects0/FFFFFFFF, rechecks type before publishing. Type recheck is
NOT atomic lens identity or same-type detach/reattach proof. Diagnostic profile
`focal-sample` exposes z7_focal_resample/valid/tenths; API12/no GUI mutation.
Private reproducible `.private/builds/20261120-focal-sample-01`:
SHAde0b258fcd6554cc8633c4f6d095404217f1b472c0c96fac6a8d649d2e314398,
256bytes/image192/BSS4. `tools/audit_z7_focal_source.py` PASSES147checks/17native
producer cases; native lookup/read/PTP scaling, fractional/encoded conversions,
stable suppression and compiled sampler execute. Incoming lens queries, native
property publication and loader services supplied. Private focal-source-02.json.
Root55/no-skips pass. Existing Other profile rebuild is BYTE IDENTICAL cbadda7a...
6ae8d. Host07 unchanged. Source evidence `evidence/20261120-native-focal-source.json`.

NEXT: implement independent focal text overlay using owned native container slot
and dynamic label (battery uses1199/299; do not collide). Preserve native VR and
independent Other/Focal selection, decimal text, missing/invalid values and
menu/output/teardown/reconnect behavior. Existing battery_percent.c allocation/
label/paint code is a local lead; current Other stack registers
histogram_after_gui in display_histogram_policy.h:191 via GUI API32, so optional
focal integration must retain that callback and existing histogram/combined
behavior. Original VR widget50/control2 is whole-mm and shares Other masks;
widget60 is flash-focus. Do not hijack either as a dedicated focal control.
ADL horizon live01 still fails65edge pixels; prior15check request equivalence
only narrowed it. Continue object/dirty/overlay diagnostics with new observations.
Remaining information app/highlights/portrait/persistence and broader lifecycle
remain in scope. Read FOCAL_LENGTH_RESEARCH.md. Graph used/refreshed2286nodes/
5792edges ignored; manifest refreshed at local source-only checkpoint.

## Native focal-text and ADL request contracts — November 20, 2026

Previous goal turn made progress: Other01 committed cd32b05, with a retained
horizon ADL pixel failure. This turn narrows that failure and identifies the
original native mm text. No production C or module binary changed; Other01
source input hashes still match. All jobs TERMINAL; no QEMU restart this turn.
Full goal remains active; no camera/card access, staging, flash or push.

`tools/audit_z7_adl_repaint.py` PASSES15 targeted checks using immutable captured
all-on4 and Other ON states from failed horizon live01. Original102F354E updater,
dual-image selector102F309A, native output-style query102F3006 and object reset
102F2B8C execute; dirty predicate, owned substitute objects and drawing sinks are
supplied. Both paths select2968/2969 with identical draw requests/reset words.
Snapshot, control records and all masks agree. RGB STILL differs65pixels; result
explicitly says input_live_run_passed=false, full_rgb_equal=false and
pixel_mismatch_cleared=false. This does not establish later paint/composition.
Private result `.private/evidence/20261120-adl-repaint-02.json`.

`tools/audit_z7_focal_native.py` PASSES106checks/18formatting/32prefix cases.
Original widget50 (VR) has image controls0/1 and mm text2; updater102F6BF7,
prep1036F2B1, formatter101709A8. Native B0 clamp60..40000 then/10 +%dmm turns245
into24mm; zero formats6mm if visibility is supplied. Prefix1036F2B0 stops before
1036F35C context/layout: text visible iff AC!=0/B0!=0/context135 in0,2. Collector
sourceE4/E8 keys153D/1548 map to snapshotAC/B0. Live electronic-lens provenance
is NOT established. Raw propertylookup10070204 rejects2014; this namespace is not
assumed equivalent to pinned Z7II10634177. Widget60 on this Z7 is flash-focus,
not the Z7II dedicated focal widget. Private focal result native01.

Read `FOCAL_LENGTH_RESEARCH.md` for contracts and implementation constraints.
NEXT focal: independently identify original live lens-controller getter and
communication/units/invalid-data rules. Use a separate native text object (or
prove separate child ownership); reusing VR widget50 parent would couple Focal
and Other/VR selection. Battery pool1199 and label299 are already reserved;
never collide or replace a native slot. Native container allocation/teardown in
battery_percent.c is an existing local lead. No focal implementation claimed.
NEXT ADL: distinguish native object bitmap state, dirty erase/repaint and final
overlay composition with NEW observations before another horizon run. Avoid
blind retries, excluded edge pixels and composed references. Full remaining
information app/highlights/portrait/persistence and broader lifecycle stay open.

Source-only evidence `evidence/20261120-native-focal-and-adl.json`. Existing graph
used for exploration, refreshed2267nodes/5745edges, ignored. Source manifest
refreshed at this local source-only checkpoint. No root suite repeat: production
code unchanged; both added instruction audits executed on exact stock MAIN.

## Other information and wide ownership — November 20, 2026

Previous turn made progress (cross-page native information). This checkpoint adds
18 independently identified Other widgets:3,6,7,8,9,13,14,16,17,26,27,34,38,41,
44,46,50,53. Total24 widgets/48 LCD words; uint64_t pending ownership only in
new display-other-probe. Original groups03 rebuilds byte-identical a951a257...487b83.
Other01 `.private/builds/20261120-display-other-01` is reproducible SHA
cbadda7a7dfbc27a9c9ca2f955c96dd3c5ae767bc0880178ca8402267c26ae8d,
14860bytes/image14592/BSS5380/API32, unchanged host07. Source inputs verified.
All jobs TERMINAL; old handles60474/69236/87016/57082 must not be polled/restarted.
No camera/card access, staging, flash or push. Full software goal stays active.

Identity02 PASSES75checks/18normal widgets; full policy02 PASSES1627checks;
phase22/base68/histogram170/grid282(native geometry109)/root55-no-skips pass.
Shared formats2(capacity16),3(flash17),4(meter7) preserve complete native groups
for EVERY nonzero value. Prefix audit stops at original format-helper entry;
full preparation bodies are not claimed. Picture Control26 has normal4035 and
N-Log child4734; old all-visible atlas was insufficient. Microphone/wind34=1321.
White balance37, battery20, AF frame, flash-ready48 and temperature stay native.
Manual label cross-check (not widget IDs):
https://onlinemanual.nikonimglib.com/z7_z6/en/14_technical_notes_01.html

Standard Other live01 PASSES11checks/eight frames, private evidence
`.private/evidence/20261120-other-information-live-01`. Other OFF protects current
capacity warning16; Other ON/master OFF restore complete captured native RGB
and all61 masks. Independent `verify_z7_other_pixels.py` PASSES standard01:
`.private/evidence/20261120-other-core-pixels-01.json`. It additionally requires
all six core readout regions and warning to equal the SAME complete native
reference, including overlap between Other14 and ISO15. No composed reference.
Settings setters are diagnostic calls; operation193=0 only in live coverage.

Horizon Other live01 TERMINAL FAILED48/49checks/11frames, private evidence
`.private/evidence/20261120-other-horizon-live-01`. Four unchanged-settings
references qualify both ISO phases. Page3 ownership, selected core glyphs,
non-information pixels, Other OFF scope/warning16, and Other ON mask restoration
PASS. Final Other ON full-RGB restoration FAILS: compared with ISO-matched all-on4,
65 differing pixels confined to ADL widget6 edges, scanout626,3..660,51. Current
snapshot and all control6 records match exactly between all-on4 and Other ON;
RGB differs. Other references1/3 have same65edge differences plus ISO phase;
reference2 differs84 ADL pixels. Underlying RGB transitions vary in antialiased
edge colors. Do NOT assume cause, invent paint completion, exclude those pixels,
compose reference frames or call horizon acceptance passed. Master OFF was not
reached. Private `adl-crop-comparison.png` / `adl-difference-large.png` inspected.
Full-frame thumbnails may omit HUD layers; trust decoded RGB and private crops.

NEXT: trace native ADL erase/repaint and exact same-settings native reference
behavior before another horizon run. A new run needs a concrete diagnostic change,
not merely restarting this failure. Then finish focal length/native information
app, highlights, portrait, persistence and broader menu/AF/output lifecycle.
Real histogram statistics and physical card/cache/wake remain unverified.
User wants software finished first; no camera staging/flash without explicit
owner authorization and exact installation/recovery review. Source evidence:
`evidence/20261120-native-other-information.json`. Graph refreshed2248nodes/
5681edges, ignored; source manifest refreshed at local source-only checkpoint.
Failed identity01 (missing supplied warning-row8 visibility) and policy01
(retained supplied page3 accidentally triggered foreign-page release) are retained;
fixture corrections needed no production C change.

## Custom information across native states — November 20, 2026

Previous goal turn made progress; this turn fixes cross-page information ON.
All current jobs are TERMINAL. Latest groups03
`.private/builds/20261120-display-groups-03` is reproducible SHA
a951a2574b80a41114f4dde62d012506b35388a7d2c9fa45eceb5ead9f487b83,
14604bytes/image14336/BSS5060/API32, unchanged host07. No camera/card access,
staging, flash or push. Full software goal stays active.

Each LCD bank AND native operation state retains its own original standard-page
eligibility: saved bit0 seeds0/3, saved bit8 independently seeds8/11. Only0x909
changes; movie/other-output/third-bank bits remain native. Nonzero exposure
formats keep their complete saved native mask. Original shooting bank1=0x110
permits only the alternate operation; focus/release bank0 have bit0 but no bit8.
Do not seed both states from bit0 or copy the Z7II0x99 mask. Earlier groups02's
single-seed prototype is superseded. Native control-level eligibility still runs;
there are no direct visibility stores or changed current shooting snapshots.

Information-pages02 PASSES2753 compiled cases across4presets/all64combinations,
warnings/ownership and all16photo-bit patterns with independently seeded native
operation0/1 and pages0/3 in both banks. Phase02 PASSES22checks/4cases: actual
compiled Shooting masks change, but at fixed supplied native phase the original
ISO preparation10369C06, selector102F2586 and visibility helper102F2656 produce
identical controls. It supplies incoming state and three native context-service
returns; no pixels or temporal producer semantics are established by that audit.
Current03 also passes base68/histogram170/grid282(native geometry109)/root55
no-skips. Old histogram08 rebuild remains byte-identical29155d33...dc91b2.

Current groups03 live04 `.private/evidence/20261120-information-horizon-live-04`
PASSES60checks/16frames. Actual native DISP1/3/0 references precede custom enable.
Selected Shooting5, Release51 and Focus2 glyphs appear on native horizon3 and
match standard-native crops. Every pixel outside the six information-control
rectangles matches the original horizon reference, including the level graphic.
Each isolated OFF changes only its own control pixels; each ON restores an exact
captured all-on horizon frame. Master-off restores saved native0, all61 native
descriptor masks and complete captured-native standard RGB. Key horizon and
master-off crop inspected; exact decoded full-frame membership verified.
Settings setters are diagnostic calls, not native-menu editing/lifecycle proof.
Live operation193 remains0; alternate operation visibility is native-instruction
coverage with supplied snapshots, not physical AF behavior.

Retain failed live01/02 on groups02. Initial all-on references lacked the later
native ISO AUTO pixel phase; a settings OFF/ON cycle did not qualify it. Live03
on unchanged groups02 then PASSED60checks/16frames by sampling unchanged settings
at varied native125/250 intervals; four all-on samples captured both actual ISO
RGB phases. Current03 live04 repeats that success. Source/control values can
precede pixels: never call them a paint fence or invent phase completion. No ISO
pixel exclusions, composited reference images or production phase overrides.
This proves complete captured-native-frame membership, not temporal coherence.

Source evidence `evidence/20261120-native-information-pages.json` identifies the
current03 and prior02 packages separately. Ignored graph refreshed2213nodes/
5575edges; source manifest refreshed at this source-only local checkpoint.

NEXT: bind Other information using original-Z7 updater/icon identity, then focal
length and the native information app; highlights, portrait, persistence and
native menu-return/broader lifecycle remain. Original60 is flash-focus, not the
Z7II focal widget. Private prior native icon inventory is a lead, not complete
binding proof. Current pending/release ownership uses two bits per group in a
32-bit word; expand that representation before exceeding15 groups. Successful
real histogram statistics and physical card/cache/
wake remain unverified. User wants software finished first. No camera staging
or flash without explicit authorization and exact installation/recovery review.

## Six ordinary information groups — November 19, 2026

Previous goal turn completed histogram pixels. This turn implements three more
ordinary groups, retaining the full goal. New private groups01 is reproducible
SHA063d91a6c8231f0d6124ad4ebff5fbfc1692596441e0aa86ce459683ca206fcf,
14604bytes/image14336/BSS5060/API32, unchanged host07. Variant
display-groups-probe includes histogram08 plus Z7_INFORMATION_GROUPS_PROBE.
Old histogram08 rebuild in groups-histogram-regression-01 remains byte-identical.
No camera/card access, staging, flash or push.

Native updater execution and private decoded-icon inspection independently
identify shooting5 (102F346E, snapshot+8), release51 (102F6D00,+5B), and focus2
(102F31A6,+1F7). Do not reuse Z7II release3/focus6: original3 is AF-area and6 is
Active D-Lighting. Original60 is flash-focus, not a derived focal-text binding.
38 identity cases pass; private icons retained, never published. The six-group
adapter covers10/11/15/5/51/2, two owned LCD bank words each,0x909 suppression
only. ON preserves original permissions. Exposure nonzero formats remain native;
other native status/warning/AF-area layers are untouched. Conditional restoration,
foreign-write latch and pending abandoned descriptors extend to all12 words.
641 compiled cases pass across4presets/all64combinations, native mask interpreter,
exposure formats and per-new-group ownership failures. Histogram170 passes.
Root55/no-skips pass, including4 ordinary HUD geometry regressions.

Live01 terminal failed the checker's wrong bottom-up transform, after actual
native shooting-mode suppression. Correct actual difference vs initial native
refs is3,3,54,54 within top-left0,0,57,57. Ordinary image/text control layout is
TOP-DOWN; histogram low-level fill uses a separate BOTTOM-UP convention. New
display_pixel_geometry.py encodes ordinary720x480/exclusive-endpoint scaling;
do not reuse the histogram helper. Live02 uses frozen probe/geometry source.

Live02 PASSES18checks/12frames. Actual native DISP cycles1/3/0 before filtering.
Each of shooting/release/focus OFF changes only pixels within its original HUD
control rectangles. Difference bounds respectively3,3,54,54 /304,6,356,51 /
410,6,467,51. Every outside pixel matches a captured native reference. Each ON
and final master-off restores the complete captured native RGB exactly, with
native format matching and no outside pixel exclusions. All61 descriptor masks
are compared; only the target's two LCD words change. Native mode/visibility/
snapshot stores are NOT supplied. Compiled settings setters are invoked by the
diagnostic; this is not native menu editing coverage. Focus-off and master-off
frames visually inspected. Source evidence:
`evidence/20261119-native-information-groups.json`.

Base68 and grid282/native geometry109 regressions also pass on groups01. All
current jobs are TERMINAL. Parallel heavy Unicorn fixture loads hit the existing
10-second per-call watchdog; serial native-load diagnostic completed status8 in
6.97s with original stack preserved. Do not run multiple heavy audits concurrently
with QEMU. Graph refreshed2200nodes/5539edges; generated graph stays ignored.
Source manifest refreshed at this local source-only checkpoint. Goal stays active.

NEXT: Other information, focal length, information app, highlights, portrait,
persistence, native menu-return and broader lifecycle. Review cross-page ON
semantics against pinned sdk/disp.h before finalizing custom DISP: current ON
preserves native eligibility, so ordinary groups whose native masks omit horizon
page3 do not become visible there merely by selecting ON. The new live test
covers standard page0 only; suppression/native interpreter tests cover0/3. Do
not claim all enabled information/horizon combinations complete. Successful real
histogram statistics and physical card/cache/wake remain unverified. No camera
staging/flashing until explicit authorization plus exact installation/recovery
assessment; user wants software finished first.

## Native histogram pixels and active-output guards — November 19, 2026

Current histogram08 supersedes06 below: reproducible SHA
29155d3343a98ffa9f9edc126fa68b027d9b715699eba4093a3ec3ce39dc91b2,
14540bytes/image14272/BSS5060/API32, unchanged host07. No camera/card access,
staging, flash or push. Full software goal remains active.

Original103FBCCA confirms active outputs at A1821370+0x24. Require sole-active
LCD, including in the RAM-only painter guard. Reject output/page/ownership
changes before native painting. Failure cleanup avoids layout against a changed
output/scene, while native hide/dirty still retires the owned object. Never
re-enter native property services or display waits from the painter guard.
170 compiled component checks,52 original-painter/output cases,68 base ownership
and282 grid cases pass on08. Root51 tests/no skips pass, including12 new fixture
ownership/RSP/register/pause/coordinate cases.

Positive private run `.private/evidence/20261119-histogram-pixels-live-05` passes
12checks/9frames. Supplies immutable bins ONLY at104070AC for the exact cleared
owned BSS buffer and in-module Thumb caller. Foreign callers execute original
getter. No statistics event completion or framebuffer pixels supplied. Actual
native layout/updater/painter/submit/present execute. Active and same-page
re-enabled histogram each change37360 RGB pixels, all inside the exact native
rectangle; every other pixel matches a captured native reference. Component-off
and master-off restore complete native RGB exactly. Key active frame inspected.
Native720x480 bitmap rows are bottom-up (existing spiral research); original
fill endpoints are exclusive. Rect475,269,675,370 maps to675,156,960,300 at
1024x682. Raw ISO control snapshots are diagnostic, never a completed-paint fence.

Retain pixels-live01 native readiness failure;02 fixture swallowed an explicit
pause at a queued getter stop (fixed/tested);03 wrong top-down coordinate test;
04 invalid requirement that raw ISO visibility fence actual painting. None
required a renderer patch or pixel exclusions.05 uses actual captured RGB and
native format membership, retaining control snapshots diagnostically. Real
statistics production remains UNVERIFIED; prior real-getter failure run remains
separate evidence. Source summary `evidence/20261119-native-histogram-pixels.json`.

NEXT: remaining display components (highlights/information app/groups), native
menu-return coherence, persistence and broader lifecycle. Preserve the explicit
sample boundary; do not call supplied bins real statistics success. Physical
card/cache/wake and exact installation/recovery assessment remain hardware gaps.
User wants software finished before flashing. Never flash without explicit
authorization and a concrete exact-candidate installation/recovery assessment.
Graph/source manifest refreshed at this checkpoint; all jobs terminal.

## Native histogram extra pass and real getter failure — November 19, 2026

Previous goal turn made progress; this turn implements the histogram component.
ALL CURRENT JOBS ARE TERMINAL after graph refresh. Keep full goal active.
Current experimental module `.private/builds/20261119-display-histogram-06` is
reproducible SHA9f26f9d690e21c9258e1f555813ae598d766c25fd062a396a07559e2b18ec790,
14220bytes/image13952/BSS5060, additive32-byte API, unchanged host07. Accepted
base-grid04 rebuild `.private/builds/20261119-histogram-base-regression-01` remains
30399ca0... byte-identical. No camera/card access, staging, flash or push.

Variant display-histogram-probe includes the base/grid/readout/GUI stack, defaults
custom display off, keeps original masks six444/three440 and native page2 gate.
Owned LCD page0/3 extra pass checks previous page, base/property/context, key/event
bindings, pending work, widget/control/canvas/painter identity, dirty/visible
flags, photo eligibility and readiness. Clear aligned256-word samples before
real104070AC. Failed/empty/overflowed/changed data stops before native publication.
Success copies1024bytes toA201DF88; native min(peak,4*nonzero mean) scale goes
toA201D33C (actual getter103EA09E key3 verified). Temporary masks only LCD banks0/3
add bits0/8 or3/11 during native layout10369248,10369214,102F27A8. Restore masks,
dispatch102F2ADA/102F5540, submit102F2042, conditionally request present102F11B6.
Native updater installs102F1545; original rectangle initializer1043396A proves
default10433913. Temporary module observer restores default after synchronous
submit, including old-object cleanup if the control pointer changes. Native hide/
dirty services explicitly clean failures and retire owned widgets before native
invalidation on component/master-off. Never overwrite foreign object/painters.

Final audit `.private/evidence/20261119-histogram-component-07.json` passes146
compiled checks. Native layout/updater execute, plus one whole positive chain
through original painter/scale getter to supplied rectangle/barrier services.
Sample producer, synchronous submit and present are supplied. Failure injection
supplies painter returns. Another case executes real getter/driver/zeroing with
unavailable event0; no invented successful event. Painter audit01 passes28 checks/
five cases for native scale lookup, bar heights/clipping, empty and hidden states;
primitive geometry only. Base68/grid282(native geometry109)/root39 no-skips pass.

Live `.private/evidence/20261119-histogram-component-live-05` PASSES9checks/8frames.
Native RAW/ISP readiness and a complete native DISP cycle precede comparison.
Five actual getter attempts fail without optional paint/present. Active RGB
matches both initial disabled standard frames with identical native format/ISO
visibility. Active/component-off/master-off all match those full RGB frames;
attempt count stays5 after disable. Native HUD reference inspected; RGB equality
independently confirmed. This is native failure-path frame membership only,
not successful histogram pixels, actual statistics success or a paint fence.
Source evidence: `evidence/20261119-native-histogram-component.json`.

Retain failed live01/02: A1829AF8 word0 is a message callback pointer, not a zero
context byte (original103764B8 loads/calls it). Correct guards use known native
key/event bindings; do not map foreign context globals by nearby struct offsets.
Live03 reaches getter failures but ISO AUTO differs from its initial reference;
live04 shows invalidation alone is insufficient. Live05 records native cycling
and matches phase-qualified complete native RGB with no pixel exceptions.

NEXT: validate actual active output bits W(A1821370+0x24), as original103FBCCA
reads that word; current context checks requested output103FEF80 and LCD scene0
but not yet this active-output word. Add ownership/transition protection before
successful pixel validation. Then run native submit/present with explicitly
supplied bins at the getter boundary if QEMU has no statistics backend, without
inventing event completion or calling that hardware statistics success. Verify
visible histogram, same-page toggle/master-off retirement and protected pixels.
Native present102F11B6 routes outputs via103FBCCA,10435318,103FAC5A; original
submit102F2042 uses LCD prep102F1E3C, dirty-list102F1DC0 and render103FAEC6.
No supplied-sample pixel fixture is implemented yet. Real producer success,
highlights, information app/groups, menu-return coherence, persistence/lifecycle,
physical card/cache/wake and exact installation/recovery remain open. Graph and
source manifest refreshed at this source-only checkpoint. Never flash until
explicit authorization plus concrete exact-candidate installation/recovery review.

## After-native-GUI prerequisite — November 19, 2026

Previous goal turn made progress; this turn adds the after-GUI host API.
ALL CURRENT JOBS ARE TERMINAL after graph refresh. Host07 is reproducible MAIN
SHA9326b595fd4f47719aaa9bcdb157ce35aa9f3cbd812a62f990585a4e2e52db66,
33057580bytes/host3569bytes, additive32-byte API/state256/hooks32. Private build
`.private/builds/20261119-display-host-07`; GUI diagnostic01 package384bytes,
image320/BSS24, SHAdc7443a8d2500171cf379ceaafe1c437cd6e78255e210bb2d24d0749aba32a99.
Combined regression13 remainsf7dbdf87... byte-identical. No camera/card access,
staging, flash or push. User explicitly wants software finished before flashing.

Only native shooting-update initializer A1829B14 changes to resident bridge;
original1030DB42..1030DD1D body and key/event slots1030DA57/1030DD1F remain native.
The callback runs after original return, including early app transitions. It
preserves original post-call registers/result/NZCVQ. Nested native updates still
execute but nested module callbacks are suppressed. Init-only registration
accepts owned Thumb image code; failure clears publication before image release.
Three reserved state words40/41/42 hold callback/registered/running. Older API
prefixes remain compatible. This is NOT a frame/ISP fence or statistics producer.
Existing after-paint callbacks run inside native rendering: never submit a
recursive extra pass there. Use sdk/gui.h and revalidate context/render busy.

122 instruction checks pass, including20 differentials/five original paths/four
NZCVQ states, callback ordering, nested suppression, guard/publication failures,
foreign-slot rejection and old28-byte-host rejection. Original callback body
executes; direct native service returns are supplied. Existing host99/display316/
update24/DISP137/base68/grid282 +root39/no-skips pass on host07. Grid includes109
native geometry calls. Source evidence `evidence/20261119-native-gui-update.json`.

QEMU `.private/evidence/20261119-gui-update-live-01` passes11 checks/two frames.
Native pipeline readiness is observed, callback counts52->70 with actual DISP
page0->1, zero observed render-busy callbacks. Both native frames inspected.
No extra paint/statistics fixture. Original full widget/statistics success is
not covered by the instruction audit. All test/build/QEMU jobs terminal.

Next bind native histogram extra layout/submit/present with real getter failures
and cleanup preserved. Pinned upstream histogram_horizon_ram.c remains private
at50a22b24... . Original sampler/service chain in prior section remains valid.
Further research this turn: regular GUI103240AA invokes10324502(control prep),
102F2AC8(each102F27A8),102F2042(render submit), then102F2AE8(dispatch updater only
for dirty descriptor),102F2EE8(output/gate postprocessing),1036DD72. Candidate
single-widget layout chain is10369248/10369214/102F27A8; derive and audit before
using it. Native updater102F5540 sets painter102F1545 via104BCB3C and visibility
via103FB32E. Do not mistake102F2F1E(visibility aggregate) for layout. Native
present102F11B6 has output-routing/service dependencies and needs full audit.
Clear owned sample buffer before getter; nominal lower-level success may still
leave empty samples if statistics backend fails. Do not invent event completion.
Histogram/highlights, information app/groups, native menu-return coherence,
persistence/lifecycle and physical installation/recovery remain open. Keep the
full software goal active. Graph/manifest refreshed at this source checkpoint.

## Native grid component and histogram failure contracts — November 19, 2026

Previous goal turn made progress; this turn binds native grid visibility.
ALL CURRENT JOBS ARE TERMINAL. Base-grid04 is reproducible SHA
30399ca0300985666221c962dce9ee77ee2952eae1dfda15b1a6d0ba4f66742c,
12044bytes/image11776/BSS3884, unchanged host06/28-byte API. Only scalar key102D
reports Off during eligible owned custom grid-Off state. Original1037723E keeps
its native availability/exclusion gates. Native geometry, saved style and style
tables stay unchanged. Scalar callbacks are RAM-only; never re-enter property
services inside a scalar read. Ownership/foreign-property validation is on GUI
updates. Same-page component edits/master-off invalidate native layout.

282 grid contracts pass (109 original geometry calls,96 native visibility
combinations,49 scalar key/value/no-service-reentry cases and context checks).
Native scalar inputs, eligibility/exclusion and viewport/GUI/kernel services are
supplied. Corrected04 ownership audit05 passes68 cases including older-host
rejection. Root39/no-skips pass. Accepted disp03 rebuilds byte-identically.

Private grid-live02 PASSES30checks/16frames: native golden ON/OFF references,
positive line-pixel qualification, native DISP cycling, correct native plane
writes with saved style3 unchanged, horizon+grid+composition protected pixels,
exact native OFF/ON/OFF same-page edits, master-off from hidden grid restoring
exact native grid-ON RGB/base release, then resumed native cycling. Key frames
visually inspected, including restored top-HUD crop. This is finite captured
native RGB membership for the expected base/grid state, not a paint fence,
warning-pixel, physical-output or durability proof. No pixel exceptions.

Retain failed grid-live01/count-only03: six checks then preset1 has descriptor
counts0 but visible lines (3169pixels from native Off). Native repeat encoding
and plane enable are different contracts. Count-only policy is removed. Neither
its121 instruction cases nor its zero-count records prove hidden pixels.

Histogram getter audit01 passes224 original wrapper/driver/zeroing cases. Getter
chain104070AC->10203C5E->10148DA0->101F8F20 requires driverA188D70C+1==2 and an
aligned destination, then100A7382 uses driver+2 and native event waiting. Supplied
unavailable event0 returns0, clears busy/pending and zeroes exactly1024bytes;
early state/alignment rejection leaves the destination untouched. Original mutex
ordering/zeroing execute; mutex/event returns are supplied. Successful statistics
production/conversion and histogram pixels remain UNVERIFIED. Do not invent event
completion or treat zeroed failure data as valid bins. Source evidence files:
evidence/20261119-native-grid-component.json and20261119-native-histogram-getter.json.

Next implement native histogram/highlights component bindings, information-app
ownership, remaining groups, actual native-menu/update coherence and persistence.
Pinned upstream histogram/portrait files remain private at50a22b24...; hashes in
the prior base-page evidence. Upstream histogram uses a guarded extra statistics/
layout/paint pass. Original Z7 data getter/event path must remain authoritative.
Broader lifecycle, physical card/cache/wake and exact installation/recovery stay
open. Graph refreshed2050nodes/5173edges. No camera/card access, staging, flash or
push. Keep full software goal active.

## Native base-page ownership checkpoint — November 19, 2026

Previous goal turn made progress; this turn adds native base-page ownership.
All current jobs are TERMINAL. Optional display-base-probe/base02 package SHA
17448f7f58b0f3efcd19be59438a15a67b3c0a351bbaffa48f1921db7ca98dd7,
11660bytes/image11392/BSS3876, uses unchanged host06/28-byte API. It selects
native standard0 or horizon3 from the preset's horizon flag, after original
selector103673AC confirms photo-LCD property2F15. It calls original103673DE,
saves the native selection and conditionally restores it on disable/context exit.
Foreign property/snapshot writes suspend custom policy until master-off.
Setter failures roll the snapshot back through the same native API; failed
restores retain conditional ownership/retry. Other-output cleanup changes only
the saved photo-LCD property, never the shared current-output snapshot.

New audit_z7_display_base.py passes68 actual compiled-ARM checks with original
selector/setter instructions; storage/GUI/kernel inputs remain supplied. Covers
all four native starting pages, all16 component sets, no redundant stores,
foreign changes, rollback/retry, other-output pending cleanup and older24-byte
host rejection before native stores. Root39/no-skips pass. Accepted disp03
rebuilds byte-identically (71c07800...), so earlier scoped evidence is retained.

Private disp-base-live01 passes22checks/11frames. Readiness rejects RAW22/ISP22/
LCD0 and accepts RAW21/ISP21/LCD30. Actual native keys select bases0/3; horizon+
composition preserves all pixels outside the readout strip versus the disabled
native horizon reference. Return presets/master-off exactly match complete
captured native standard frames. Disable releases native base ownership and
subsequent DISP resumes original cycling. Horizon/composition/restored frames
were inspected. Not warning pixels, physical orientation/EVF or a coherent native
update/paint fence. No camera/card access, staging, flash or push.

Next implement grid/histogram/highlights component bindings, information-app
ownership, remaining groups and persistence. Pinned upstream missing grid and
histogram files are now fetched privately at the SAME50a22b24... commit; hashes
in evidence/20261119-native-base-pages.json. Upstream custom histogram uses a
guarded extra statistics/layout/paint pass, NOT only page masks. Derive original
Z7 callbacks and failure cleanup before porting it. Original Z7 grid LCD descriptor
count fields are offsets10/22 (not upstream18/30); existing geometry hook sees
only0xA2020C2C. Suppression needs native recomputation/retirement when component
choices change even if native base stays0. Do not silently leave existing pixels.
Native menu-return reselection, warning pixels and broader lifecycle remain open.
Hardware card/cache/wake and exact installation/recovery are still unverified.
Graph refreshed2020nodes/5092edges. Keep goal active; software scope unfinished.

## Completed DISP-cycle checkpoint — November 19, 2026

All current jobs are TERMINAL. Latest display-disp03 is reproducible:
SHA71c0780063ebe2466f8e14b4f1860657b0eee22dddf227342276a60e7f7a414b,
10956bytes/image10688/BSS3844, same28-byte host06 API. New automatic reselection
moves a disabled active preset to the next enabled one on eligible update,
without changing native snapshot/page/property or counting a key press. Menu,
movie, alternate output, master-off and unbound information configuration defer
it until return. Cycle audit03 passes137 cases (60 enabled/current combinations
and10 defer/return cases added).119 readout checks and root39/no-skips pass.
Readout-only package rebuilds byte-identically to the old0aa8f050... package.

New read-only pipeline qualification requires RAW/ISP/LCD progress, processed
scanout and native ready/stage. It records at most6 original1000ms task delays,
with no readiness stores or invented device responses. Full preset live09 passes
21checks/11frames; the first sample advances22RAW/23ISP/30LCD. Native keys select
all four presets; composition preserves all protected pixels; presets1/3/0 and
master-off exactly match complete captured disabled native references. Disabled
mode resumes native cycling. Composition/restored frames visually inspected.
This is finite-native-image equivalence, not a coherent native paint fence or
warning-transition pixel proof. Actual menu-return reselection remains open.

Dedicated admission-live01 passes6checks/2frames/22trace events: original key29
passes the four outer gates, reaches the original inner handler and cycle,
page0->1. Gate returns are observed, not supplied. This100ms startup is NOT the
same as the prior5000ms failure and does not explain that failure. Its trace
records native progress121RAW/115ISP by the after frame. Raw trace stays private.

Next: native base-page/component ownership, information app, remaining groups,
actual menu/update coherence and persistence. Broader output/lifecycle, hardware
card/cache/wake and exact installation/recovery assessment remain unfinished.
Do not repeat the old phase-wait loop. Read the latest DISPLAY_SETTINGS.md and
evidence/20261119-preset-coherence.json. Graph refreshed1997nodes/5031edges.
No physical camera/card access, staging, flash or push.

## Resume after stale running status — November 19, 2026

The former live04 job is TERMINAL, not running. Its saved result fails with
`Native ISO phase did not match the qualified baseline`: 11 checks passed,
then all24 samples stayed at snapshot+4==0 versus the baseline1. No native
timer transition back to1 was observed. Do not relaunch that waiting loop.

Native103681BA..103681D0 copies producer packet A201F260+44/+48/+4C to
snapshot+3C/+4/+24C. Eight original-instruction copy cases now pass, including
unchanged neighboring bytes, alongside8 formatter and96 visibility cases.
Producer packet inputs are supplied; actual producer behavior remains open.
The two saved disabled standard-page references in live04 differ by exactly
the2,206 ISO AUTO pixels only. This does not establish periodic blinking.

Live07 stopped after11 passing checks because it required matching all ISO
source fields, including unselected sources. Offline RGB comparison then showed
preset1 AND preset3 match the complete disabled native baseline exactly, despite
preset3 controls reporting source0/hidden ISO while that frame contains the label.
The snapshot/control record therefore is not a completed-native-paint fence.
Do not infer frame identity from that record or call these signals periodic.

The revised probe accepts only exact full RGB membership in the finite captured
disabled native standard-page reference set. It records source/control identity
separately, with no state/pixel writes, pixel exceptions or waiting loop. This
proves captured-image equivalence only; coherent update/paint timing stays open.
Live08 is TERMINAL: three startup checks pass, then the disabled native DISP
control fails after three bounded injections. Startup reports137 RAW batches
and only1 ISP batch. Custom presets were never enabled in that run. No owned
guest remains. Do not repeat on elapsed delays; investigate native input
admission and sensor/ISP readiness before another full rendering probe.
Live05 failed local socket access. Live06 was explicitly interrupted during
startup to narrow format qualification to readout groups0/1/5. Live07 is terminal.
Root39 tests pass, no skips. Identity audit03 passes112 cases total.
Only validation source changed; host06 and display-disp02 binaries are unchanged.
No camera/card access, staging, flash or push.

## Historical DISP prototype run status — superseded above

LIVE JOB: exec_command session89208, private evidence20261119-disp-presets-live-04.
Poll the SAME handle with write_stdin; observation timeout is not termination.
It boots host06 + display-disp02 and records an explicit disabled native cycle
before the qualified baseline. Wait for its actual result; do not start another
guest based on elapsed time. All earlier jobs are terminal. User asked whether
we were frozen; answered that work/audits progress while native QEMU steps are slow.
Continue meaningful work and give concise updates at least every60seconds.

Current optional display-disp02 SHA f57a1b106b201468dda5178bc4d94f5c545dc79dafd12f892ab7350b50a1bbff,
10892bytes/image10624/BSS3840, needs additive28-byte API. Host06 MAIN SHA
28633855e1daa1ffcf1f2213dfa2b0a41395f65c6a60af7b44a8f02442631958,
33057312bytes/host3301. Read latest DISPLAY_SETTINGS.md and source evidence
20261119-native-disp-cycle.json. Ordinary combined/settings/readout packages
rebuild byte-identically; no physical card/camera access, staging, flash or push.

New host cycle bridge1037061C preserves original key callback slot and original
outer/inner admission.67checks pass: native blocked/other keys, disabled-choice
skip, native fallback, registration/failure/publication, owned-code bounds,
stock delegated-prefix register/flags/stack differential and old24-byte host
rejection before native stores. Update API24, base20, hooks32 and state256 retain
layout; cycle uses two reserved words. Other host checks24+99+316 andreadout120
pass. Root39 pass no skips. Native warning-order16cases pass with selector and
selected predicates executing; ISO preparation executes, other6helper returns
and named status/context boundaries supplied. Warning pixels remain open.

Host05 (prior intermediate MAIN c5491649...) put update before1036B10C, which
follows control-preparation1036AE44. Host06 instead hooks1036AE44 after current
format selection, before preparation/layout; original prefix calls use literal
thunks, native differential passes. This was an ordering improvement, NOT a
proven fix for the ISO-label mismatch: host06 live03 still fails that comparison.

Retain live01/02/03. Native DISP selects1/2/3 and hides readouts, then full RGB
fails by2206pixels in(626,618)-(680,672), the ISO AUTO label. Instrumented02/03
show baseline snapshot+4=1 and return+4=0, ISO250=2 throughout. Original native
102F2586 selects+4 for250==2/default, +3C for1 and+24C for3; native102F2656
sets ISO controls1/2 visibility from that value. New independent identity audit02
passes8formatter +96visibility cases. This is native blinking/visibility phase,
not a proven restoration defect; source/probe now wait for matching native phase
AND all4ISO control visibilities, then capture paused with settle=0. No visibility/
phase stores or pixel exceptions were added; exact full RGB remains required.
Every phase sample is retained. Live04 is the pending repeat of this stricter test.

Raw native-control records and screenshots remain private. Full precompute
instruction experiment (private only) hit unmapped kernel data A208685C; no
kernel data invented. The scoped warning audit supplies six preparation helpers
and three context returns, executes original ISO preparation/computation and
stops at native widget-loop continuation.

After live04: inspect frames/phase records, update pending evidence/docs, refresh
graph and source manifest before checkpoint if needed. Graph refreshed1991nodes/5019edges after the latest audit/probe edits;
generated graph stays ignored. Source manifest covers326 source files. Next software requirements include native
base-page/component binding, information app input/update ownership, remaining
information groups, coherent active-preset changes and persistence. Hardware
card/cache/wake and exact installation/recovery assessment remain. Keep goal active.

## Native readout computation hook — November 19, 2026

Read the final DISPLAY_SETTINGS.md section and evidence/20261119-native-readout-update.json.
Optional display-readouts-probe05 SHA0aa8f050419560d030e907fc1dc14aa72893b4ccda8a2e28e6a9aa9935aa6846,
10828bytes/image10560/BSS3832, requires additive24-byte API. New display-host04
MAIN SHAf5b991a726a2f3e732b98488b66db14996a84fd460dc245c1dbf3c696fbd1858,
33056916bytes/host3129. BaseAPI20, display-hooks32 and state256 retain layouts.

New original1036B10C prefix callback runs before snapshot comparison/computation.
Readout policy changes only six owned LCD mask words for shutter/aperture/ISO;
original10367C5A invalidation then lets native computation/layout/painting run.
Do NOT move it back to sm_before paint or directly dispatch groups/blanket-dirty
HUD: retained private late-phase experiments lost HUD/restoration or drew stale
text and unrelated OK/Exit footer. First new bridge clobberedr12; prefix differential
caught it and corrected local literal thunk preserves native input/flags/stack.

Independent original mask audit30240matrix+7invariants derives0x909, not upstream
0x99 (which touches Z7 movie bits). Original formatter/string-copy8cases identify
widgets10/11/15 and shared shutter warnings. Policy leaves every already-present
nonzero format native; same-update warning transitions/pixels remain OPEN.

120readout checks including old20-byte-host rejection before native stores;
24update registration/prefix,99loader,316existing display-host checks pass.
Root39tests pass none skipped. Ordinary settings regression02 remains identical
SHA3ae795ed... New QEMU readouts-live05 on corrected host04 passes13checks/3frames:
all3normalgroups qualified, hide via masks, outside strip unchanged, disable exact
full RGB/mask restoration. Frames inspected; diff only(193,611)-(838,679) at1024x682.
Explicit native standard-page setter and diagnostic preset2/compiled model setter;
no raw mask/visibility fixture writes. Earlier host03 live04 also passed13/3.
No actual DISP routing, warning-transition, every-output/lifecycle or hardware proof.

Graph refreshed1953nodes/4914edges. All current guests/jobs terminal, no QEMU
process remains. Next: validate warning transition timing before broader integration,
then wire validated native DISP/preset selection and remaining information groups.
Persistence, battery real-telemetry/lifecycle readiness and physical-card/cache/wake
plus exact-candidate installation/recovery remain unfinished. No card/camera access,
staging, flash or push occurred. Keep goal active; this is a scoped milestone.

## Immediate native menu paint/focus — November 19, 2026

Latest optional display-settings entry06 SHA
3ae795ed00a9ae165852ddc5d2a6d34f1ab830a9350047552aaa28d6f850298a,
9804bytes/image9536/BSS3760.51 compiled menu and38 battery policy checks pass.
Private settings-focus-paint-live03 passes28 native-entry checks/11frames:
immediate OFF/ON/OFF glyph changes/restoration, correct native selected-row
highlight in both subviews, identical pixels for all five normal information ON
values, model edits and Back to d9. Entry/root/preset/info/global/back inspected;
additional pixel checks show428 white pixels per normal ON and64 per preset `--`.

Fixes: component paint must precede native display refresh.103FAC5A calls
103FA770 synchronously as a predicate; the old queued-callback description was
wrong. Deferred prepaint alone failed.10402BC2 changes only row indices; focus
also needs native text palettes and compound selection flags. Original
10405D48/10405A92 helpers and103FB30A setters now handle those. Palette-only
entry05 failed the selected-background pixel check.51-case audit includes
native selection setter execution/parent dirty propagation and paint ordering.

Read DISPLAY_SETTINGS.md's latest section and new source-only evidence. Shooting
validation remains open: integration06/07 compared an initial adapter112B to a
final battery1120, so failed ROI comparisons do not prove retirement failure.
Integration10 shows1120 immediately after native GUI requests, then112B after
drawing, and rejects all three baselines. Same paused request/call checkpoint
avoids an input gap but does not suppress native updates. Probe source+SHA are
saved in new private runs. Baseline qualification checks visible native battery,
font, geometry, parent and painter; final glyph must match before pixel compare.

Integration11 uses an explicit disabled-only menu control BEFORE qualification,
but stops on native unmodeled flash write at10000AAA before the first MENU
returns. Startup reports132 RAW/1 ISP batches even with the base5000ms native
StartLV wait. The earlier100ms shortcut was insufficient, but5000ms alone is
also not a reliable readiness gate. Do not keep rerunning on elapsed delay or
invent a flash response; inspect actual pipeline readiness/update sources.
Entry02's earlier first-sequence failure lacks equivalent diagnostics and stays
private/unresolved. No entry06 shooting restoration success is claimed.

Root39 regressions pass, no skips; ignored graph1895nodes/4745edges refreshed.
No owned guest remains live. Other preset/master renderer binding, persistence,
warning/AF/output/lifecycle, real card/cache/wake and installation/recovery are
unfinished. No camera/card access, staging, flash or push occurred.

## Native entry and actual battery switch — November 19, 2026

Optional `--variant display-settings` adds a seventh Display settings row under
native d9 Framing grid display. Original six choices/values remain. Entry01
SHA567528756b145881a0d3fb05edcaf2673dda0f032368e0734d0d73b35d65b825
passes20 native-key checks/8frames for full entry/model/back, and a separate19
checks/7frames for all six grid selections. Entry/root/back were inspected.
The ordinary combined regression05 remains byte-identical to its prior package.

Entry02 SHA9a086f58748b34beaa9e45c823ad585ef45983b64ab756c4566115592a2a46e9
binds model battery setting to the actual renderer, initially OFF.46 compiled
menu checks and38 automatic-battery checks pass. Battery audit enables through
the actual compiled settings adapter, with supplied GUI queue services.
Private settings-battery-integration01 fails stock ROI restoration after MENU:
percentage enables/disables but native icon is absent afterward. Keep this run.
Integration02 adds a disabled-only menu control first;25 checks/6frames pass,
including that control and exact complete RGB restoration after enable/disable.
No production change separates those two runs, so sequence/timing remains open.
Both use labeled GUI bar/icon requests, no supplied percent or setting word.

Visual inspection catches stale battery menu status in integration02: enabled
reads OFF, disabled reads ON. Actual flags and shooting behavior are correct.
Fix native value cache/repaint timing and reproduce the initial no-control
sequence before claiming a completed integration. Other preset/master settings
still change only the model. Persistence, warning/AF policy and broader output/
lifecycle remain. Read DISPLAY_SETTINGS.md's latest section and source evidence.
Root39 tests pass, none skipped; graph refresh1889nodes/4731edges. No owned guest
remains from these completed runs. No camera/card access, staging or flashing.
The SD architecture is one installed firmware host plus resident Z7APP.BIN at
startup; later compatible feature packages replace the card file after power-off.
Actual physical card loading and exact-candidate installation/recovery are open.

## Native settings-menu prototype — November 19, 2026

Read the final section of `z7-native-modules/DISPLAY_SETTINGS.md`. Optional
settings-menu-probe now publishes an owned native page-zero object after all
registrations succeed. Its root/preset/information virtual subviews edit the
validated settings model through native keys. Ordinary combined bytes are unchanged.
Private candidate09 SHA31e94a9c59853f6e412c77aba9330d85af0bc23cf848735a796af1823adb1283
passes28 instruction cases; live09 passes15 checks/7frames. Frames were inspected:
titles, information rows and final ON/OFF values are correct. Intermediate root
captures can omit submenu `--` indicators until another repaint; this is open.

Earlier failures/green-but-visually-stale runs remain private. Original event
router does not supply page inR0, so no-argument adapters supply the guarded page.
Back destinations stay neutral during callbacks; root exit uses native history.
Actual dirty-object painting uses original103FAEC6 on the GUI path. Header ID203
is from the original layout. Native font setter rejects1->2; bridge1->0->2 is
instruction-tested. Active-page prepaint binds the header after construction.

The menu still opens through an explicit native diagnostic call. Add a real
entry, connect settings to renderers/persistence, finish indicator timing and
cover re-entry/MENU/playback/foreign-state lifecycle. Do not mistake model/UI
edits for actual renderer settings yet. No guest remains live from these runs.
No camera or physical card access occurred. Existing earlier entries are historical.

## Configurable display settings model — November 19, 2026

Read `z7-native-modules/DISPLAY_SETTINGS.md`. New independent C model represents
four presets, eight per-preset information groups, four components, separate
information-page enable, custom master and global battery setting. Defaults,
enabled-page skipping, last-page protection and reset isolation are implemented.
Its strict independent64-byte Z7C1 format validates model/CRC/target/version and
preserves output on rejection. No card I/O or native menu is installed yet.
Private settings-probe02 SHAa8b278b4614741a10a5b90c6614edf93f3436469c8929f768e510d7daa4355f0
passes1,262 actual compiled-ARM cases against an independent wire reference,
including all512 single-bit corruptions, sealed invalid fields, all31 page-enable
sets, isolation/reset, overlapping buffers, canaries and null pointers.
File/kernel/heap for the loader remain supplied. This is model progress, not
native settings UI/persistence or completion of the full custom-DISP feature.
No owned guest remains running from the completed prior probes.

## Native-button clean-page prototype — November 19, 2026

New `examples/disp_key_probe.c` is a default-off optional SD profile. It checks
the original native callback binding, publishes an owned wrapper only after all
registrations succeed, forwards arguments/result through the original callback,
and counts only native-admitted DISP page changes. Enabled GUI pre-paint primes
the clean diagnostic masks before native input. This is not the full configurable
DISP port or warning-policy validation. No camera-side setting UI exists yet.
Private key-probe02 SHA622096e10293df185d4ab20da2d82511e5b024b43de551911184bcfe89af7b45
passes22 instruction policy/ownership cases with supplied native callback outcomes.
Original input admission has separate20-case+QEMU evidence. Key-live01 passes8
checks/3frames: native DISP enters clean mode1, counts one accepted transition,
and disable/native cycling restores the complete RGB baseline byte-identically.
Clean/restored frames were inspected. No guest remains live from completed runs.
Only the prototype master switch is explicitly supplied. Existing combined and clean
diagnostic packages both rebuild byte-identically. Artifacts stay private.

## Native PLAY lifetime and clean-DISP investigation — November 19, 2026

Combined playback03 passes17 assisted-QEMU checks/13frames. Native PLAY shows
the no-card error page43, tears down the shooting GUI and clears the owned HUD
reference; no percentage remains or sampling occurs there. PLAY return rebuilds
and recovers after a fourth labeled icon/bar GUI request. Both error and recovered
frames were inspected. This is the native no-card path, not image playback or
real-card evidence. Playback02 is retained as a probe failure: it read object+40
after the object correctly became zero. The probe now handles that teardown.

Card-bracket audit02 passes18 original instruction cases. Widget16 updater
102F3F8A tails into102F7E24 even when its normal control-visibility result is zero;
the original glyph wrapper makes four LCD bracket objects visible again. See
`CLEAN_DISPLAY_RESEARCH.md`. New clean-probe is disabled by default and still a
diagnostic, not a completed custom-DISP feature. Its13 instruction checks pass
mask/visibility restoration, menu/EVF/movie exclusion and foreign-mask protection.
Private live01 passes6 checks/3frames: clean scene+golden grid, all549 mask words
restored and a separate full RGB comparison byte-identical to baseline. Clean
and restored frames were inspected. No owned guest remains live. Camera-side
DISP key/settings, other outputs and broader lifecycle are next. Generated
packages and frames remain private.

Original DISP selector103673AC/setter103673DE now have24 instruction checks in
`tools/audit_z7_disp_selector.py`, private selector01. Photo LCD property2F15,
photo alternate2F16, movie LCD2F17/alternate2F18 follow supplied138D/display-kind.
Setter changes only snapshot+18A then calls original property storage. The
native key callback and admission remain unresolved; do not install a guessed
Z7II callback-slot translation. This is the next custom-DISP integration lead.

Later independent tracing identifies original slotA1829B0C->1030DA57, internal
dispatcher1030D7AC and key29->103673F6 admission->1037061C page cycle. Input audit01
passes14 cases with supplied service results. Selector audit02 now passes104
cases including80 native page-cycle/skip combinations. A live observation first
stopped on a background0 event; input-live01 is retained as a failed trace.
Input-live02 was explicitly stopped after its late observation proved inadequate;
the failure is retained. Input-live03 traces during native AO injection and native
task delays and passes7 checks/2frames: key29, original admission/cycle, mode0->1
and callback unchanged. The real key was handled inside the injection call;
background0 followed during delay. No guest from these runs remains live. Input audit02 now
passes20 cases including six outer-callback admission/filter cases. No native
callback has been replaced. See the clean-display record.

## Combined grid/battery SD module — November 19, 2026

`plugins/combined_display.c` joins the native six-choice grid menu and automatic
LCD-photo battery percentage in one package. It stages both component bindings
locally, registers one unified display table/menu, and commits histogram masks
last. Component/menu failures leave native pointers and masks unchanged.
The standalone grid package remains byte-identical after the deferred-mask edit.

Private combined-display-01 and combined-display-off-01 use existing display
host02. The enabled package is5,140 bytes, SHA
`f7dbdf87c9280edf65d5ff495e2079152221740c27009ac0bd316cddf7ff395f`.
Grid audit02 passes954 checks; battery audit01 passes39. Combined live01 passes
10 checks/6frames, with golden grid and percentage together and exact full-frame
stock restoration. Menu01 passes19 checks/all six choices. Lifecycle01 passes14
checks/10frames: native MENU hides the percentage, stops sampling, then returns
to an eligible icon and recovers. The menu and recovered frames were inspected.
Lifecycle uses three labeled bar/icon GUI requests; percent0 comes from the
assisted virtual snapshot. No physical battery telemetry is established.

See `Z7_DISPLAY_MODULE_RESEARCH.md` and source-only combined evidence. Native
playback/AF stress, other outputs, custom DISP, focal length, photo zebras,
portrait layout and histogram statistics production remain open. No staging or
camera flash is authorized. No guest remains live from the completed runs.
Older entries below record earlier, separate-component milestones.

## Automatic LCD-photo battery module — November 19, 2026

New `plugins/battery_percent.c` is automatic, replacing diagnostic phase control
for this profile. Read the top of `Z7_BATTERY_DISPLAY_RESEARCH.md`. It samples once
per16 GUI passes, rejects bar fallback and invalid telemetry, follows known
native foreground battery glyphs, and restores the stock icon on exclusion/off.
Builder `--variant battery-percent --battery-percent on|off` sets an owned data
word and reseals module CRC. There is not yet a camera-side settings menu.

Private module07 and off04 are current. Source fingerprints are in their reports.
Audit06 passes39 instruction checks including the off package. QEMU04 passes8
checks/5frames, including exact full-frame restoration and adapter exclusion.
GUI request supplies bar1/icon visibility once; native getter supplies percent0
from the assisted virtual controller. No physical battery telemetry follows.
All current frames were inspected: native warning red is retained, compact
percentage fits, the stock icon returns, and no percentage overlays the adapter.

Visual review of earlier QEMU01 caught a semantic gap despite green checks: it
had admitted adapter glyph112A. The new gate accepts only even foreground glyphs
1120..1128 with native class4/HUD painter, excluding adapter112A/B and background
glyphs. Font0 (36px) was too large; the feature uses original LCD readout font100
(20px), selected through native kind19. Frame/text inherit stock warning palette.
The name `native_power_kind` in old private inspection output was an unproven
interpretation of function1030D3CA; current tooling labels it as unknown UI state.

Next: native-key menu/playback/AF stress and repeated GUI lifetime; combine the
standalone battery module with the grid module. Other display ports, histogram
statistics production and physical card/cache/telemetry/wake/output behavior
remain open. No staging or camera flash is authorized. No owned QEMU run remains
live from these completed tests. Earlier handoff entries describe prior stages.

## Native battery sample-to-HUD integration — November 19, 2026

The last turn made code/validation progress, not completion. New reusable sample
policy `z7-native-modules/plugins/battery_sample.h` rejects uninitialized/unknown
data, percent >100 and native bar fallback before/after a getter query. Failure
preserves output. Its 192-byte compiled probe passes 23 cases, including a
fallback transition during the native locked copy. Private result sample-01.

Builder variants `battery-sample` and `battery-native` were added. The latter
includes the shared HUD diagnostic with actual getter/formatter integration.
Private bundle `.private/builds/20261119-battery-native-probe-01/` passes 23
instruction checks (`battery-native-audit-02.json`) and seven assisted-QEMU
checks (`battery-native-display-01/`). It displays the emulator snapshot's 0%,
then retires with the complete frame byte-identical to the starting frame.
No percent value is written by this display probe; virtual controller/power boot
inputs remain assisted. This is still diagnostic one-shot phase control, not an
automatic visibility/cadence/owner-setting feature. Continue that implementation.
Final bundle02 records current included-source hashes and is byte-identical to
QEMU-tested bundle01. The fixed-text bundle03 also matches its previously tested
bundle02 byte-for-byte. Source-only evidence is
`evidence/20261119-battery-native-integration.json`.

The native-sample QEMU run passively reports histogram viewport flag0, native
driver bytes `01 02 02` (driver state2), maximum0. Driver admission is already
valid; the statistics service/data-production path still needs investigation.
No owned emulator process is still running from these completed runs.

## Native HUD lifetime milestone — November 19, 2026

Read `Z7_BATTERY_DISPLAY_RESEARCH.md`. The battery text diagnostic is now an
actual SD-loaded module, separate from the grid module. Candidate probe 02
passes seven assisted-QEMU checks with supplied text 63%, then retires on the
native GUI path. The complete inactive/retired PNGs are byte-identical (SHA in
the research record). Earlier hide-only/generic-constructor/direct-clear trials
and probe 01's insufficient clearing bounds all remain private failures.

New private outputs: `.private/builds/20261119-battery-display-probe-02/`,
`.private/evidence/20261119-battery-module-trial-02/`, battery-display-audit-02
(14 checks), battery-snapshot-03 (44 checks), display-module-05 (951 checks).
The instruction display audit executes original native pool/zeroing/HUD init;
font/label/list/paint and loader services remain supplied. The QEMU visual run
executes native font and painter code. Neither establishes hardware telemetry.

Native GUI getter `0x102F2B84` returns context `0xA201E388`; its object pool is
at +0x24, not directly the returned value. Native regular pool capacity is 1200,
object size 284. Diagnostic slot1199/label299 were empty in the inspected session.
HUD constructor `0x10384D82`, measure request `0x10384E02`, painter `0x10384968`,
destructor `0x10384954`. Native RGBA rectangle painter `0x10433912`. The supplied
text's outlined glyph exceeds its layout box: retiring `(2,392)-(78,436)` around
layout `(10,400)-(70,424)` restores the entire observed frame exactly.

The battery producer `0x101F9888` normally copies input +0x18, but native flag
`0xA18B4DE8 != 0` can replace it through bar conversion `0x101F9844`. A precise
percentage feature must reject that fallback. Next: extract the validated GUI
ownership/painter path into the feature; add sample validity/cadence, native
battery visibility, label ownership, GUI rebuild/teardown and owner controls.
The probe's fixed63% and diagnostic phase writes are not the finished feature.

Histogram context watch run07 finds native producer `0x10370696` clearing at
`0x10370716`. It requires its native eligibility, snapshot +0x28 == 0 and a
successful statistics fetch `0x104070AC`; the latter reaches `0x101F8F20`, requiring
driver state2. The 951-check audit includes real context production and bin copy
with supplied statistics. No histogram completion flag was forced in QEMU.
The probe now records viewport/driver source state passively on future boots.
No guest process from these completed probes remains owned/running.

## Native SD display module — November 19, 2026

Read `Z7_DISPLAY_MODULE_RESEARCH.md` for the current display implementation.
Branch `codex/z7-sd-display-ports` preserves the initial host checkpoint in
`6d4d8c9`. Display host candidate 02 and module bundle 02 are private, reproducible
emulator-only outputs. The module adds six native grid choices through staged,
owned display/menu registrations. Menu pointers commit on the GUI path while
the grid page is inactive. Failed initializers cannot leave callbacks into freed
storage. The native menu passes all six selections; five grid layouts and Off
pass native geometry/pixel/restoration observations in assisted QEMU.

The host audit passes 316 checks; module audit passes 933 checks with 756 geometry
calls, plus 39 root tests without skips. The ordinary live histogram check still
fails: the assisted fixture has native context byte `0xA201D318 == 0`, which the
original visibility code excludes. Another run reaches context 1 and immediate
native visibility, then a later pass hides it again. Its other eligibility checks
pass; the complete hiding path is still being traced. Preserve the native gates.
An explicit context-1 diagnostic flag is separate from default
observations and is not evidence of physical camera histogram behavior.
Live run 05's bounded watch sees context reset to zero on resumed native update;
a one-time context fixture does not supply a valid live context producer. Its
watchpoint was before a store and repeated without stepping; the tool now removes
the watchpoint, steps the observed instruction and reinstalls it. Do not hold
the context at 1.
Update: revised live run 06 succeeds as an observer: on the selected stopped CPU
it steps native hiding store `0x1036D5D4`, reads `01 00`, context 0 and DISP 3.
The ordinary histogram visibility check correctly remains failed. Trace the
context producer next; there is no reason to remove this native exclusion.

Current private records: display module menu 01, live 03, display-host audit 03
and display-module audit 04 under `.private/evidence/20261119-*`. All failed
histogram diagnostics are retained. Continue with native shooting-context
derivation and the remaining independent display ports. Z7 widget 60 has two
power-zoom controls and cannot be replaced using Z7II's focal-widget assumption.
The active autonomous goal remains open; no physical staging or flash is
authorized by this continuation. The older entries below record earlier stages.

Battery-data lead: original percent formatter `0x104C4AA2` calls `0x10437684` /
`0x101F9ECE` for a locked 56-byte snapshot, then formats word +0x18 as `%d%%`.
Snapshot source `0xA235AEE4`, mutex `0xA235AE4C`. This is not Z7II's 80-byte
contract. Validate producer/sentinels and owned text-object lifetime next; the
percentage overlay is not implemented yet.
The new `tools/audit_z7_battery_snapshot.py` passes 32 checks (private result
`20261119-battery-snapshot-02.json`): actual wrapper/getter/ARM memcpy, bounded
56-byte copy, mutex order and original menu-constructor prefix reaching percent
formatting with exactly snapshot word +0x18. Mutex, producer and object lookup
boundaries are supplied. No hardware battery telemetry or overlay is proven.

## Autonomous continuation and native-kernel module load — November 19, 2026

The owner asked to keep building until finished while they are at work. Follow
`BUILD_PROGRESS.md` and the active goal: module framework then display ports,
with no physical card/camera staging or flash. The existing source-only/privacy,
licensing and exact-candidate assessment rules remain in force.

The unchanged host candidate 02 now passes nine assisted-QEMU load checks using
`tools/module_file_fixture.py`, an explicit read-only filesystem-dispatch HLE.
Task scheduling, heap allocation, cache instructions, host relocation and the
actual compiled C initializer run in the guest. Its BSS marker is read from
native allocated memory. This is not a physical card test. Successful private
result: `.private/evidence/20261119-module-host-qemu-load-04/`.

Initial file-fixture observation points were installed before RSP negotiation
and did not remain active. The corrected client refreshes the observation after
negotiation and before bounded guest calls, and retires it after native close/
stat completion. All failed diagnostics are preserved. Five fixture unit tests
cover exact writes, owned handles, read-only flags, pass-through and bounds.

Next: stage module-owned display callbacks until initializer success, preserving
stock fallbacks without a module. Start with grids and histogram/horizon using
the existing independently mapped original-Z7 geometry and visibility paths.

## Original-Z7 module host probe — November 19, 2026

Owner authorized continuing the SD-module foundation. Read
`Z7_MODULE_HOST_RESEARCH.md`. Private Zig 0.15.2 (official archive hash pinned)
now compiles both the actual C initialization module and the complete host as
Thumb. `tools/Setup-Z7ModuleToolchain.ps1` reproduces the private compiler setup;
the system toolchain and WSL are unchanged. Builder temporaries/caches are private.

Final candidate: `.private/builds/20261119-module-host-02/`, MAIN SHA-256
`b2cde95401214c3115c55e3bd378dab836ae2f7e635612202dbd3e6e0a0fea1e`,
33,053,812 bytes. Two independent builds match, with valid full EG CRC. It is
stock-based and includes no display, sound or installed grid/spiral features.
Guarded workspace initialization reserves 256 bytes and preserves native
continuation registers/NZCVQ; one AUTOOP binding forwards the original initializer
before scheduling a native low-priority loader task. No preset is added to the
ordinary firmware builder or installation-review admission.

99 instruction checks execute the compiled Thumb host and C module plus original
Z7 filesystem/task/cache wrappers. Kernel, FS-dispatch and allocator boundaries
are modeled. They cover cleanup/errors, model/CRC/bounds, cache ordering and
owned 640-byte staging bounds, full-width task IDs, boot/retries and actual C
initialization. Native Z7 file objects are 40 bytes; the sound routine's 48-byte
stack reservation includes its read-count storage, correcting the earlier
object-size inference. Z7's direct-buffer read ABI and success 0x04390080 differ
from Z7II and are independently traced.

The final candidate passes seven assisted-QEMU checks for native task creation/
start, 100 unavailable-file attempts, intact guards, no active image and MENU
input in one guest. Private result: `.private/evidence/20261119-module-host-qemu-03/`.
Its predecessor's Playback menu frame was visually inspected. Initial probe 01
incorrectly rejected kernel task ID 0x01000102 with a 16-bit assertion and had a
cleanup attribute error; that guest was identified/stopped, the harness was fixed,
and the failed evidence is preserved. Do not report those harness failures as a
firmware crash. All 34 root tests pass, including exclusion from flash review.

This does not establish successful real-card loading, card removal/EOF/error
semantics, physical cache coherence, wake, display features or emergency recovery.
No physical camera/card access, staging or flash, commit or public push occurred.
Preserve installed/prior candidates. A future hardware step requires a concrete
exact-candidate installation/recovery assessment and explicit owner authorization.

## SD-loaded module foundation — November 19, 2026

The owner linked `JKWTCN/z7ii-extensions` and selected SD-loaded modules first,
then display features. Read `SD_MODULE_PORT.md` and `z7-native-modules/README.md`.
Inspected/pinned source commit: `50a22b24c50619cffa646dac386e8334659f475a`, Z7II
C 1.70 preview.21. Its 15 feature groups are upstream reports, not original-Z7
hardware validation. Selected public text references remain ignored under
`.private/research/z7ii-50a22b2/`; no release binaries or screenshots were fetched.

New MIT-derived independent component adds Z7M1/0x03800007 identity, minimal
z7_main API, C validation/preparation core, linker layout, example and bounded
ELF module packer. No Z7II camera addresses are bound into this component.
Ten new tests pass: native-host C core plus synthetic relocated Thumb init at
three bases, API rejection, BSS/ABI preservation, malformed inputs and buffer
bounds. All 33 root tests pass without skips. LLVM is absent from inspected PATH;
the example C probe and actual LLVM compilation/linking remain untested.

This is not a completed SD loader: original-Z7 boot/task/card/file/cache/heap
integration still needs independent contracts and failure/lifecycle tests, then
an isolated no-feature firmware probe. Existing sound-port filesystem addresses
are leads only; upstream's descriptor/read/cache contract differs. Native C core
execution on the host is distinct from the synthetic module's Thumb execution.
No original-Z7 firmware or QEMU binary source changed, no new firmware candidate
was generated, and no card/camera access, staging, flash, commit or push occurred.
Existing sound-trigger hold and spiral EVF lag remain. Preserve installed/prior
builds and require a fresh exact-candidate assessment before future flashing.

## Source push preparation — October 27, 2026

The owner requested pushing the code. Scope includes automatic spiral lifecycle,
gray native LCD/EVF routing, exact-candidate review and compatibility tools,
source-only evidence, clean-display research and the unresolved level-lag report.
The pending QEMU smoke helper change permits EOF/reset after a successful quit
request only, while retaining mandatory capabilities/status replies, zero exit
and bounded termination; its 12 synthetic process/TCP regressions are included.
No renderer performance fix or new firmware release is claimed.

Fresh checks: all 23 root tests and all 23 QEMU component Python tests pass.
The first restricted component run hit local file/socket access failures; the
properly permitted repeat passes. The QEMU publication inventory passes with
46 source-only files. The actual native QEMU executable also passes the updated
firmware-free QMP smoke check. No C renderer/ISP source changed, so those contract tests
were not redundantly rerun. Previous exact-candidate instruction/emulator results
remain scoped as documented above. Private firmware, dumps, binaries, media,
camera captures, keys and ignored graphs are excluded from this source push.

## Gray/EVF trial works; Golden ratio level lag — October 27, 2026

Owner reports the installed gray/EVF trial works, but electronic level motion
lags conspicuously in EVF and barely noticeably on the monitor, only on Golden
ratio. They recall no lag before the spiral. Exact report is recorded in
`evidence/20261027-grid-spiral-display-owner-hardware.json`. Associated EG remains
`c3cbb8fd4aaa932fc74cfd662cbfaac3f5471ea6ab81edb6148766d5a93449b6`.
This is owner-reported post-update function/performance, not firmware readback
or independently timed observation. Do not keep claiming EVF is wholly untested;
the owner now reports the trial works, with this regression.

Read the new performance section of `GRID_SPIRAL_RESEARCH.md`. Each eligible UI
paint completion currently calls uncached PNG drawing under the shared native
graphics mutex. Native wrapper forces resource ID -1 and allocates/decodes/
synchronizes/frees a full image each call. EVF decodes 4,915,200 RGBA bytes for
7,589 curve pixels; LCD 1,382,400 bytes for 4,195 curve pixels. This is the leading
cause, not a measured hardware latency diagnosis. Candidate native path/paint
primitive `0x1042F066` and boundaries `0x10450852/0x10450A3E/0x104508A6` provide a
starting point for an allocation/decode-light curve renderer, but full argument,
state restoration and failure contracts remain unverified. No replacement
renderer, new firmware or lag fix was built in this triage. Preserve all current
builds. No new card access or staging occurred. No physical rollback or emergency
recovery is verified. Source manifest refreshed; firmware code unchanged.

## Gray LCD/EVF spiral staged for owner trial — October 27, 2026

Owner explicitly authorized staging/flash: "card is mounted lets flash it".
Read `GRID_SPIRAL_DISPLAY_FLASH_ASSESSMENT.md`. Fresh independent build at
`.private/builds/20261027-spiral-display-flash-01/` exactly matches tested candidate
02: full EG 33,074,646 bytes, SHA-256
`c3cbb8fd4aaa932fc74cfd662cbfaac3f5471ea6ab81edb6148766d5a93449b6`;
MAIN `7049b2120a9f88e3859a5d8ec335bb4858e6642ba9a278e5cd95474edf597543`.
New explicit `grid-spiral-display` review identity reconstructs all EG/MAIN/report
bytes separately from legacy yellow and rejects mixed/modified/legacy/explicit
artifacts. Twelve native updater header/name checks, 18 fresh previous-loader
compatibility checks and 23 root tests pass. Exact prior 132 instruction, 18 LCD
lifecycle and nine native EVF-bitmap results plus their frame/bitmap hashes verify;
QEMU was not redundantly rerun for byte-identical artifacts. Ignored code graph
refreshed. Review bundle retains stock and three prior rollback inputs separately.

Sony QD-G240F was freshly identified on E: by serial, size, volume and partition.
Its yellow EG exactly matched and is backed up at
`.private/card-backups/20261027-spiral-display-4d73d3a5/EG161080.BIN`.
New full EG is staged and fully hash-verified as the only root BIN. Other root
file sizes/hashes remain unchanged; photo directories were not edited. No
formatting, automatic ejection or camera operation occurred. Receipt is in that
backup folder; sanitized evidence is `evidence/20261027-grid-spiral-display-flash-review.json`.

Owner instructions: charged power, select 3x3 before update, safely eject, use
normal firmware updater (version stays 3.80), do not interrupt programming, follow
completion/restart instructions. Confirm normal rear-monitor use first, then
Golden ratio gray curve and MENU/3x3 removal, then EVF/monitor switching. No
physical EVF success, camera update completion, rollback or emergency recovery
is claimed. The camera has not been operated by the agent.

## Gray spiral and native EVF bitmap correction — October 27, 2026

Latest owner feedback: yellow spiral is visible only on the monitor; straight
custom grids work in EVF. The owner requests normal-grid gray and EVF support.
The installed legacy helper explicitly excluded EVF. Read the new top section
of `GRID_SPIRAL_RESEARCH.md` and `CLEAN_DISPLAY_RESEARCH.md`.

New private build `.private/builds/20261027-spiral-display-02/` uses original Z7
component-1 descriptors for LCD 720x480 and EVF 1280x960, exact registered
surface/shape checks, separate immutable gray assets and active IDs 1/4.
MAIN SHA-256 `7049b2120a9f88e3859a5d8ec335bb4858e6642ba9a278e5cd95474edf597543`.
Independent rebuild/CRC, 132 supplied-boundary instruction checks, 18 assisted
LCD lifecycle checks and 22 root tests pass; nine frame hashes verify. The gray
detector's first run falsely counted native grid/gradient pixels; the failed
run is preserved and a regression plus narrower upper-arc detector resolves it.
The complete gray spiral and Off frames were visually inspected.

Native EVF bitmap/decoder test is separate from eye-sensor/scanout validation.
Attempt 01 sampled two-byte instead of four-byte pixels; attempts 02/03 used
top-down coordinates against a bottom-up RGBA bitmap. These failed results
remain preserved. Attempt-03 full raw capture exactly matches all 7,589 source
curve pixels after vertical reflection, including 6,621 beyond LCD-sized bounds.
Corrected repeat 04 passes all nine checks, including native registration,
full-size gray pixels and previous target restoration. Its result is in
`.private/research/grid/20261027-spiral-native-evf-04/`. No physical EVF success
is claimed. Sanitized evidence: `evidence/20261027-grid-spiral-display.json`.
Default legacy build exactly reproduces installed yellow MAIN hash `06b89e2a...`.
The new identity is not admitted by the existing yellow flash assessment/review.
No new candidate was copied to the card; it is in the camera after the owner's
earlier trial. Fresh card identification and a new exact-candidate assessment
are required before a later staging request.

Clean-display emulator RAM masking hides most shooting widgets but leaves two
card-count brackets even after MENU clear/return. Original background/secondary
bitmap fills did not remove them. All original masks were restored, normal
simplified readouts returned, and that isolated guest was closed. No clean UI
firmware patch is included. Private research outputs remain under
`.private/research/display/20261027-clean-mask-03/`.

## Owner confirms spiral grid switching — October 27, 2026

After the reported update initiation below, the owner reports: "yep it appears
only when using golden ratio, and will disappear when swapping to another
gridtype". This is the first physical-camera report for the automatic spiral
image staged with EG SHA-256
`52c593aff9895e31b4cfaf15ceb0335bdf4f26671d346dcb499080ea11c0f316`.
It supports post-update display operation and expected layout selection/removal
on one original Z7. It is not independent observation or firmware readback.
The owner also answered "Yes, clears and returns" for opening MENU and returning
to Golden ratio. Exact completion text, EVF/crop/DISP/wake, capture/performance
and recovery remain unverified. The core selection and MENU lifecycle now have
both scoped emulator evidence and one owner's physical-camera report.
Evidence: `evidence/20261027-grid-spiral-owner-hardware.json`.

## Spiral trial staged; owner reports programming — October 27, 2026

The owner accepts the curve in front of status icons and explicitly requested a
camera trial. The owner confirmed charged power and a backed-up card connected
through its reader. Read `GRID_SPIRAL_FLASH_ASSESSMENT.md`. Clean-display research
is a separate task and is not in this BIN.

Fresh `.private/builds/20261027-spiral-flash-01/` exactly reproduces the tested
automatic-paint image: full EG 33,062,334 bytes, SHA-256
`52c593aff9895e31b4cfaf15ceb0335bdf4f26671d346dcb499080ea11c0f316`;
MAIN SHA-256 `06b89e2a4eb864a96599eea504dd1d2f8aba05c8f072243c3a7d51c999fbd136`.
The dedicated `grid-spiral` review rebuilds/completely compares EG, MAIN and report,
retains the CRC, rejects mixed/modified/explicit-only inputs and links the new
assessment. Other review modes remain separate. All 20 root tests pass.

Fresh 95 instruction, 12 selected original updater header/name and 18 previous
loader compatibility checks pass. The identical MAIN's existing 18 assisted-QEMU
checks and nine frame hashes verify; QEMU was not redundantly rerun for the copy.
Stock, prior six-grid and owner-tested three-grid inputs are kept separately in
`.private/flash-review/20261027-spiral-01/`. No emergency recovery or physical
rollback is verified. Foreground acceptance does not resolve LCD/EVF/crop/DISP,
allocation/concurrency or real timing limits.

The expected Sony QD-G240F was freshly re-identified as E: and its six-grid EG
fully hash-matched. Backup: `.private/card-backups/20261027-spiral-b20cb240/EG161080.BIN`.
The spiral was staged as the only root BIN using a flushed/verified temporary copy
and final readback. Settings/WAV/root inventory remain unchanged. No photo-folder
edits, formatting, automatic ejection or camera operation by the agent occurred.
Sanitized evidence: `evidence/20261027-grid-spiral-flash-review.json`.

The owner was instructed to begin with 3x3 selected and use the rear LCD, then
choose Golden ratio after update/startup. Golden ratio now includes the curve;
no separate spiral row exists. While asked for the current/new screen, the owner
reported "flashing now. ill report back". Programming is owner-reported in progress,
not observed complete. Do not interrupt an active update. Await completion and
test Golden ratio, MENU return, and 3x3/Off following the camera's instructions.

## Automatic spiral paint proof and upstream merge — October 27, 2026

The owner asked to investigate automatic spiral drawing/removal. Read the new
automatic section of `GRID_SPIRAL_RESEARCH.md`. Separate private candidate
`.private/builds/20261027-spiral-lifecycle-01/` hooks the original Z7 dirty-widget
paint completion, retaining the original walker/return/pending-flag behavior.
No custom workspace, timer, capture hook, settings record or flash writer is
added. It combines the spiral with existing Golden ratio value 3; there is no
separate spiral menu choice yet.

MAIN SHA-256 `06b89e2a4eb864a96599eea504dd1d2f8aba05c8f072243c3a7d51c999fbd136`,
33,062,332 bytes. The explicit-draw parent has one additional guarded 12-byte
window (11 changed bytes), plus 352 appended bytes. Full independent rebuild
and CRC pass. Preset `grid-spiral-lifecycle-emulator-only` is rejected by ordinary
grid and flash-review admission. The earlier six-grid card file is untouched.

95 supplied-boundary instruction checks, 19 root tests and 18 assisted-QEMU
checks pass. Native MENU clears the curve and both tested returns automatically
restore it, without host draw calls or asset uploads. Choosing 3x3/Off through
exact compiled handlers while MENU owns the screen removes it on return;
Golden ratio restores it. Nine saved PNG hashes verify. The first visual run's
second MENU check falsely counted Nikon's yellow sidebar highlight; that failed
run remains preserved. Narrower observed-color classification has two new
regressions, and the full repeat passes. Sanitized evidence:
`evidence/20261027-grid-spiral-lifecycle.json`.

This is a feasibility proof, not a flash-ready implementation. The curve draws
over some status icons; layer ordering/owned UI integration is the next concrete
problem. Direct live-view erase, DISP/playback, EVF/crop/rotation, allocation
failure, concurrent painting and hardware performance remain unverified. No
camera/card access, new staging, flash clearance, publication or push occurred.

The owner also reported the WonderLantern PR merge. GitHub metadata confirms
`WonderLantern/z7-qemu#3`, "Support native Windows builds and controller
execution", is merged. Head `109671a14bd48729d6a7ed92402b2d7b229789d6` merged as
`110c8ab93278e32870ae136533b5ee8b17db19b3`, timestamp
`2026-10-28T02:12:21Z` (October 27 in Denver).
https://github.com/WonderLantern/z7-qemu/pull/3 . No additional upstream comment,
repository update or vendored-snapshot rebase was performed for this observation.

## Six-choice grid prepared and staged — October 27, 2026

The owner requested preparing a camera flash with the new grids, then confirmed
the card was mounted in response to the staging request. Only 4x4 / 3x3 /
Golden ratio (phi lines) / Center cross / 6x6 / Off are included. The Fibonacci
curve, sound and splash remain excluded. Read `GRID_LAYOUTS_FLASH_ASSESSMENT.md`.

Fresh `.private/builds/20261027-grid-layouts-flash-01/` exactly reproduces tested
candidate 02. Full EG is 33,056,174 bytes, SHA-256
`437e1f8edbb89f1409ad768dcf50e91725280481561fcaa8f0f161cc64e5dccc`;
MAIN SHA-256 `6485b0a579eb469701bcb89c442ab6b7faa1cea748dd3716cc524e500595b97f`.
Review bundle: `.private/flash-review/20261027-grid-layouts-01/`.
Convenient copy: `.private/flash-ready/20261027-grid-layouts/EG161080.BIN`.

Fresh 484 instruction checks and 12 updater header/filename probes pass. Eighteen
new previous-build compatibility checks show native journal loading retains all
89 payloads, old visibility/menu treat new values as Off, and old 3x3 can be
selected/saved/reloaded. These are supplied-boundary tests, not physical rollback.
The identical MAIN's earlier 35 QEMU checks and frame hashes were verified;
QEMU was not rerun for a byte-identical copy. All 17 root tests pass. The new
explicit `grid-layouts` review mode rejects old-mode/spiral report substitution.

The Sony QD-G240F was re-identified by model, serial, physical capacity, USB
bus and volume identity as E:. Its old EG matched the owner-tested saved-grid
build and was backed up/read back at
`.private/card-backups/20261027-grid-layouts-951c3dab/EG161080.BIN`.
The new EG was staged through a verified temporary copy, then renamed into
place. Final full hash matches, it is the only root `.BIN`, and settings/WAV
hashes plus the non-firmware root inventory are unchanged. No photo-folder
write, formatting, ejection or camera programming was performed.

Next checkpoint: safely eject, insert into the original Z7 C 3.80/no paid RAW
upgrade with fully charged supported power, and inspect the actual current/new
version screen before starting an update. There is no verified emergency
recovery if the camera becomes unbootable. Stock and prior EGs are preserved
normal-updater rollback inputs only, not a full flash/calibration backup.
Sanitized evidence: `evidence/20261027-grid-layouts-flash-review.json`.

## QEMU PR fix and reply published — October 27, 2026

The owner approved responding, requested no dash punctuation, and asked that
the public reply focus on Windows without mentioning other host testing.
The five-file smoke-test fix was committed and pushed to the existing fork
branch `tylermcm/z7-qemu:codex/windows-native-support` as
`109671a14bd48729d6a7ed92402b2d7b229789d6`. PR #3 now reports that head SHA.

Posted and read back the revised reply as `tylermcm`:
https://github.com/WonderLantern/z7-qemu/pull/3#issuecomment-6458021615 .
It acknowledges the overly strict quit-reply check, links the fix, and reports
23 passing Python tests on Windows plus three passing firmware-free smoke runs
against the existing QEMU 10.2.4 build. Its wording was verified against the
approved revision, including the requested punctuation and host scope.

The GitHub connector's comment action returned 403 (integration permission),
so the explicitly authorized comment was posted with the authenticated GitHub
CLI instead. The PR branch checkout is clean. The lab's vendored copy remains
updated locally; no additional lab main-branch push or release was made here.
No firmware, screenshots, dumps or runtime artifacts were published.

## QEMU PR response and prepared quit fix — October 27, 2026

The owner asked to look into answering the response on
https://github.com/WonderLantern/z7-qemu/pull/3 . R3tr0ooo reported that the
smoke helper falsely fails when QEMU exits cleanly before its quit reply;
their Python and sanitized GPU/ISP tests passed. Original pinned QEMU 10.2.4
`qapi/control.json` explicitly permits EOF before the quit acknowledgement.
The firmware-extension PR #1 had no returned comments at this check.

Prepared locally in the vendored component and the existing isolated PR
checkout `.private/pr-review/z7-qemu` on `codex/windows-native-support`:
require capability/status replies, send quit separately, and require process
exit 0 within ten seconds without reading a mandatory quit reply. Twelve new
synthetic TCP/process regressions cover EOF/reset, ordinary replies, errors,
nonzero exit and timeout. The synthetic server tolerates abandoned connection
attempts before the first command, after observed Windows loopback setup aborts;
it does not retry an actual protocol scenario.

All 23 Python tests passed on the isolated PR source. Three firmware-free runs
against the existing lab-built QEMU 10.2.4 executable passed. No Linux build,
ASan/UBSan run, firmware/UI run or camera test was repeated for this helper
change. QEMU C sources are unchanged. Publication inventories and code graph
were refreshed after review. This is a prepared patch and reply draft only:
no PR comment, PR push or main-branch push has been performed for this response.
The owner's request did not explicitly authorize posting the drafted message.

## Source push requested — October 27, 2026

The owner authorized pushing the additional grids, Fibonacci drawing prototype,
research notes, tests and sanitized evidence to `tylermcm/WonderLanternZ7` on
`origin/main`. This source update does not change the published preview tag or
assets. Nikon firmware, generated BINs/PNGs, screenshots, raw traces, local
runtime and Graphify output remain private and excluded from the commit.

The new straight-grid mode has 484 instruction and 35 assisted-QEMU checks;
the spiral drawing entry has 15 instruction and nine assisted-QEMU checks.
The 16 root tests pass. The earlier three-choice image/report still reproduce
exactly. These are scoped lab results, not new camera installation clearance;
automatic spiral redraw/removal is still pending. Exact evidence and remaining
work are in the two research documents below.

## Fibonacci overlay drawing proof — October 27, 2026

The owner asked to draw a Fibonacci curve on the golden-ratio grid. The
compiled UI-surface diagnostic now shows both over a live test image in QEMU.
Read `GRID_SPIRAL_RESEARCH.md` and `evidence/20261027-grid-spiral.json`.
Private successful frames: `.private/research/grid/20261027-spiral-native-ui-01/`.

`tools/build_spiral_probe.py` appends an immutable RGBA PNG and explicit drawing
entry, preserving every MAIN byte of the six-layout parent. New preset
`grid-spiral-draw-emulator-only`; MAIN SHA-256
`e76f8678add993cd0a665557c09bf081e675eb470937212761d108b0a8f1f5aa`.
The helper guards Golden ratio value 3, locks the native graphics mutex, selects
the registered 720x480 UI surface at 0xB045F200, draws through the original Z7
PNG path, restores the prior target and unlocks. No new lifecycle hook exists.
Use `tools/probe_grid_spiral.py --compiled` with this private build.

16 root tests, 15 supplied-boundary instruction checks and nine assisted QEMU
checks pass. The combined scene/grid/curve frame remains identical after two
seconds resumed. Direct-call experiment 01 had weak startup readiness; stricter
experiment 02 failed because its draw targeted a rotating live-image buffer.
Do not claim those earlier probes proved a usable combined overlay.

Automatic redraw/removal, grid-Off and MENU transitions, dynamic crop/EVF state,
memory/performance and concurrency still need integration/validation. Do not
blindly call PNG drawing from the geometry worker. No camera/card write, flash
clearance, push or publication occurred during that experiment. The source push
is authorized separately above. Existing grid and flash-review admission
reject the new image identity, and published default build outputs are unchanged.

## Additional grid layouts — October 27, 2026

The owner requested golden ratio and other photographic grids. A separate
optional lab mode now provides 4x4 / 3x3 / Golden ratio / Center cross / 6x6 /
Off, retaining existing scalar values 0..2 and adding 3..5. No card or camera
was accessed, and no new flash/release was authorized or performed.

Read `GRID_LAYOUTS_RESEARCH.md` and `evidence/20261027-grid-layouts.json`.
Build with `--native-choice --extra-grids`; preset is
`grid-layouts-emulator-only`. Tested private candidate 02 MAIN SHA-256:
`6485b0a579eb469701bcb89c442ab6b7faa1cea748dd3716cc524e500595b97f`.
Candidate 01 is superseded: its native geometry notification ran before the
golden adjustment. Candidate 02 adjusts before notification and passes both
native tail branches. Neither was staged.

484 instruction checks and assisted QEMU's 22 menu / 13 live-view checks pass.
All three new layouts were visually inspected, and each choice restores from
synthetic native flash into fresh CPU/RAM. Native journal schema/save policy
remain unchanged. The original three-choice image and report reproduce exactly
and its 107 checks pass; 12 root and 16 patcher tests pass with no skips.
Existing flash-review presets deliberately reject the additional-layout image.
Physical shutdown/durability/recovery and generic consumers remain unverified.

The default `--native-choice` output, published tag/assets and source-only
redistribution decision remain unchanged. Curves and diagonals require a
separate drawing path; the subsequent Fibonacci drawing proof is described
above. Diagonal guides remain unimplemented.

## Published source-only preview — October 26, 2026

Source commit `3a441180f80e6be26abff46d41d9210b53b7087c` was pushed to the
owner's `origin/main`. Public prerelease:
https://github.com/tylermcm/WonderLanternZ7/releases/tag/v0.1.0-grid-preview.1
The annotated tag resolves to that exact source commit. The release is
published, marked prerelease, and includes only the source ZIP, SHA256SUMS.txt
and RISK_NOTICE.md. **No Nikon BIN, dump, key or camera screenshot was uploaded.**

The source ZIP contains 208 reviewed source/text files, matching every hash in
its source manifest. It was extracted and used to reproduce the exact private
EG with SHA-256
`07d77574bc9fed84d357b4e7c3df808127d361106c10ca26e0b6e2c818f6d0a7`.
All three published assets were downloaded and verified byte-for-byte against
their local originals. Source ZIP SHA-256:
`2b9b8837a9e2b8d3320cc2c2c318c1428912133b04356a50627bf5140a9ba106`.
The private publication receipt is under `.private/releases/v0.1.0-grid-preview.1/`.

Release-time checks passed 16 patcher tests with private input/no skips, 11 root
and 11 QEMU Python tests, 292 renderer checks, 398 ISP checks, a firmware-free
QEMU smoke test, and the 45-file QEMU publication audit. Sanitizers were not
run. Scoped summary: `evidence/20261026-grid-release-validation.json`.
Prominent risk/no-warranty/liability notices are in README, RISK_NOTICE.md and
the release body, preserving component licenses and independent-work credits.
Reddit recommendations/draft are in REDDIT_POST_DRAFT.md; nothing was posted
or sent to Reddit/moderators by the agent. The release tag/source archive are
immutable to this follow-up bookkeeping update on main.

## Owner persistence confirmation and public preview — October 26, 2026

The owner confirmed that the latest existing-setting build was installed and
keeps the selected 3x3 grid after more than ten seconds off: "Yes, installed
and it stays 3x3". Associated staged EG SHA-256 is
`07d77574bc9fed84d357b4e7c3df808127d361106c10ca26e0b6e2c818f6d0a7`.
This is one owner's report on one original Z7, without independent observation
or camera readback. Broader behavior/durability/recovery are not established.
Evidence: `evidence/20261026-grid-saved-owner-hardware.json`.

The owner requested pushing all code, an experimental release, a Reddit draft,
and very prominent camera-damage/no-liability wording. After reviewing Nikon's
official page (Reproduction: Not permitted), the owner chose **source/patcher
only**, keeping the full BIN private. Do not upload Nikon firmware as an asset.
`RISK_NOTICE.md` and `RELEASE_GRID_PREVIEW.md` contain explicit brick/data-loss,
repair/replacement, no-warranty and liability-disclaimer language, subject to
applicable law. Do not promise that this wording guarantees legal protection.
The release remains an independent modified preview, preserving all licenses
and credits; not official Nikon or Wonder Lantern work.

Planned preview tag: `v0.1.0-grid-preview.1` on the source-only lab repository
`tylermcm/WonderLanternZ7`. The user authorized publishing a prerelease, but
not posting on Reddit; `REDDIT_POST_DRAFT.md` is for their manual use. Check
GitHub for the actual tag/release/commit before reporting publication as done.

## Existing-setting grid staged for owner flash — October 25, 2026

The owner explicitly requested "lets copy it. im gonna flash it" after the
exact-candidate assessment was prepared. The Sony QD-G240F was identified again
as USB disk 2, E:, exFAT `NIKON Z 7_2`, with the same partition/volume identity;
the identity was rechecked immediately before copying.

`E:\EG161080.BIN` now contains the reviewed existing-setting candidate, 33,054,026
bytes, SHA-256 `07d77574bc9fed84d357b4e7c3df808127d361106c10ca26e0b6e2c818f6d0a7`.
It matches tested native-value candidate 02, and is the only root `.BIN`.
Temporary copy was flushed and verified, followed by final-name readback.
The previous working RAM-only file (SHA-256
`ae46a48d52f4a89dac7c54bf63fc4b6d40b6c7d5adc49f67335e8b50fe97973b`)
is verified in
`.private/card-backups/20261025-grid-saved-050104-05d1f496/EG161080.BIN`.
Its private `staging.json` records the operation at 2026-10-26 05:01 UTC
(October 25 local Denver time). No formatting or photo edits occurred;
NIKON001.DSC and SHUTTER.WAV root-file hashes were checked unchanged.

Card was not automatically ejected. The agent did not operate the camera or
observe programming. Owner intends to flash; installation/completion and actual
persistence are not yet reported. Use supported fully charged power and normal
on-screen update completion; select 3x3 once afterward, then check after at
least ten seconds off and a longer off period. Those intervals are persistence
tests, not expiry delays. Read `GRID_NATIVE_FLASH_ASSESSMENT.md`; physical
durability, other consumers and emergency recovery remain unverified.

## Existing-setting grid binary prepared — October 25, 2026

The owner requested the firmware build. Fresh
`.private/builds/20261025-grid-native-flash-01/` reproduces tested native-value
candidate 02 exactly (EG, MAIN and report). The convenient full component file
is `.private/flash-ready/20261025-grid-saved/EG161080.BIN`, 33,054,026 bytes,
SHA-256 `07d77574bc9fed84d357b4e7c3df808127d361106c10ca26e0b6e2c818f6d0a7`.
Read `GRID_NATIVE_FLASH_ASSESSMENT.md`, not the older RAM-only assessment.
No card access, staging, ejection or camera programming occurred in this build.

The owner clarified the requirement: the selected grid should remain across
shutdowns of any duration until manually changed. Ten seconds off is only a
regression-test interval beyond the old retention cutoff, not a reset delay or
time-to-live. The new implementation has no timed expiry. Its intended durable
behavior still needs physical validation. Select 3x3 once after installation;
the old RAM-only type was not in native storage and cannot be migrated from it.

Review bundle `.private/flash-review/20261025-grid-native-01/` keeps this exact
candidate, untouched stock EG and official container separately. The helper now
admits `--preset grid-native` for offline review only, flags the changed value
encoding separately from the unchanged journal format, and links the correct
assessment. Six tests pass, including rejecting RAM-only files as native-value
artifacts and vice versa. All 12 exact-EG header/filename probes pass and three
bundle copies verify. Full CRCs/capacity/private-path checks pass. Prior 107
instruction and 16 QEMU checks apply to the identical MAIN; they are not a
physical persistence or emergency recovery result. Public scoped review summary:
`evidence/20261025-grid-native-flash-review.json`.

Before any future card staging, identify the actual card/drive again. Do not
replace the earlier working file merely because E: was used previously. Shared
reader consumers, presets/import/export, complete power lifecycle and recovery
limits are explicitly listed in the new assessment. The 90-record build remains
held and must not be substituted for this existing-setting candidate.

## Existing-setting grid persistence solution in the lab — October 25, 2026

Read `NATIVE_GRID_SETTINGS.md`. After the owner requested a solution for the
approximately three-second retention cutoff, a separate existing-scalar
prototype was implemented and tested. It stores Off/4x4/3x3 as 0/1/2 in Nikon's
existing grid scalar, normalizing only successful 0x102D/value-2 scalar reads
to boolean On. Owned menu/geometry code reads raw 2. Nikon's original worker
saves its original 89-record journal and original startup restores the choice
in fresh CPU/RAM instances. No added record, custom flash writer, journal hook,
heap reservation or conversion is used. This is the preferred next experiment;
the older 90-record prototype remains held.

Private candidate `.private/builds/20261025-grid-native-value-02/`, MAIN
33,054,024 bytes, SHA-256
`7f29bfda937c90261eff989d5f27dbf71ca2b142308b70879b1a7ef3d46c4075`.
Full EG 33,054,026 bytes, SHA-256
`07d77574bc9fed84d357b4e7c3df808127d361106c10ca26e0b6e2c818f6d0a7`.
Four guarded windows total 28 bytes, with 1,936 appended bytes. Independently
reproduced, valid CRC; preset `grid-native-value-emulator-only`.

107 instruction checks pass: 21,130 differential reads covering all 2,111
indexed properties plus invalid keys, native getter/visibility/menu/packed
snapshot, actual native request/worker/completion, fresh-RAM 3x3/4x4/Off reload,
original-stock startup preserving all 89 records with selected grid consumers
falling back to Off, sampled program cuts 1/269 and failed programming, plus
90 geometry calls. Candidate 02 also preserves original NZCVQ flags across the
shared reader and compares them across all indexed reads; candidate 01 is
superseded. Supplied OS/events/flash/UI/viewport/secondary datasets are
explicit boundaries; this is not a complete camera shutdown or physical flash
test. The optimized scalar differential helper avoids per-call Windows host
timers while enforcing instruction and ABI bounds; both full-key runs passed.

QEMU passes 10 native-key menu and 6 assisted live-view checks. Real native UI
service writes stored 2; both grid planes and Off work. These do not implement
persistent flash between QEMU processes. Scoped public summaries:
`evidence/20261025-grid-native-value.json` and
`evidence/20261025-grid-native-value-qemu.json`.
Patch/container/Thumb tests pass 14 with 2 optional stock-location skips; five
review path/admission tests pass. The previously installed RAM-only candidate
still independently rebuilds unchanged.

No new card/camera access or firmware staging occurred. At the initial prototype
stage the experiment was excluded from the review helper; the newer build
preparation above adds offline review admission. It changes a shared scalar-get
API for one key/value; generic consumers, U1/U2/U3, settings-file import/export,
toggles, wake, complete shutdown and physical durability remain review items.
Off stores 0 and forgets the prior type, unlike the older RAM-only last-type
behavior. Do not use the older RAM-only assessment to clear this new image.

## Owner-reported grid hardware success — October 25, 2026

The owner reports that the grid build works and measured its retention behavior:
selecting 3x3 survives switch-off/on when off for less than approximately three
seconds; longer off periods return to 4x4. This concerns the selected spacing,
not merely visibility. It resolves the earlier ambiguous delayed-reset report:
the observed threshold relates to time switched off. Exact boundary/repeat
counts were not supplied. Reliable persistence is not established.

The associated staged full EG SHA-256 is
`ae46a48d52f4a89dac7c54bf63fc4b6d40b6c7d5adc49f67335e8b50fe97973b`.
Laptop hash/report were rechecked: only `grid`, 64-byte workspace, no journal
hooks. The initializer writes choice 0 when executed; equating it with every
physical off/on was an unverified assumption. The observed quick-restart
retention is consistent with temporary retained state, but that mechanism and
the actual shutdown/init paths have not been traced. No evidence of an on-state
spontaneous reset was reported. No new firmware changes or flashes were made
while recording these findings. The optional journal prototype remains held.

Next lifecycle regression should distinguish a rapid off/on from at least ten
seconds switched off; battery-removal retention remains untested. The threshold
is approximate owner timing, not a measured electronic cutoff. There is no
camera firmware readback or independent hardware observation. LCD plus EVF,
all choices, standby/wake, recorded-image checks, rollback and recovery remain
outside this report. The earlier staging entry describes laptop operations
before the owner's physical test. Evidence: `evidence/20261025-grid-owner-hardware.json`.

## Grid binary rebuilt and staged — October 25, 2026

The owner requested the binary for flashing and connected the XQD. E: was
identified afresh as the Sony QD-G240F, USB disk 2, 217,701,154,816 bytes,
exFAT volume `NIKON Z 7_2`; its partition/volume identity was checked again
immediately before staging. The card contains DCIM/NIKON directories and user
files; no formatting or photo/audio/settings-file edits occurred.

A fresh normal grid build at `.private/builds/20261025-grid-flash-01/` reproduced
the previously tested exact MAIN/full EG and report. The convenient local binary
is `.private/flash-ready/20261025-grid-only/EG161080.BIN`. The same full EG is
now the only root `.BIN` at `E:\EG161080.BIN`, 33,053,802 bytes, SHA-256
`ae46a48d52f4a89dac7c54bf63fc4b6d40b6c7d5adc49f67335e8b50fe97973b`.
Source rebuild, CRC, laptop copy, temporary card copy and final card filename
readback matched. Temporary card writes were explicitly flushed before readback.

The older root EG (SHA-256
`9e636d645281ee9f92cb150b6dcc8d771b21ff95c47e45f538d951a1d932420b`)
was copied to `.private/card-backups/20261025-grid-035528-be76f89e/EG161080.BIN`
and its backup hash checked before replacement. `staging.json` there records
the private operation at 2026-10-26 03:55 UTC (October 25 local Denver time).
It is the previous experimental sound file, not stock recovery firmware.

No camera flash occurred and the card was not automatically ejected. Next:
safely eject, insert into the original Z7 with supported fully charged power,
inspect Setup → Firmware version and obtain its actual current/new versions
before proceeding. Physical acceptance and emergency recovery remain unverified;
read `GRID_FLASH_ASSESSMENT.md`. Internal persistence remains held.

## Grid-only hardware-test preparation — October 25, 2026

The owner explicitly selected the simpler RAM-only grid build for the first
hardware test, holding internal persistence. Read `GRID_FLASH_ASSESSMENT.md`.
Preparation is complete at `.private/flash-review/20261025-grid-01/`.
Its full `candidate/EG161080.BIN` is 33,053,802 bytes, SHA-256
`ae46a48d52f4a89dac7c54bf63fc4b6d40b6c7d5adc49f67335e8b50fe97973b`.
It matches the complete independent rebuild of grid-emulator-03; MAIN hash
`2762ccd5276e1c4720c06e26f636c6c551cafe3772eb6d24400b769c200cd348`.
Only the grid feature is included: stock-based 4x4 / 3x3 / Off, with 4x4 as
cold-start choice. This replaces earlier custom sound/splash/M900/dual-display
features. No internal settings-schema change, outer-container repacking, version
spoofing, card access, staging or physical flash occurred.

Current checks: 192 grid instruction checks/270 geometry calls, including actual
native workspace allocator non-overlap; 12 exact-EG native filename/header
probes; 5 preparation path/admission tests; 14 patch/container/Thumb tests with
2 optional stock-location tests skipped. The same MAIN already passed 10 QEMU
native-key menu checks and 6 diagnostic live-view checks; current QEMU binary
and all five input source hashes match that evidence. Full EG/container CRCs,
capacity and three bundle file hashes verified. Scoped summaries are
`evidence/20261025-grid-preflash-instructions.json` and
`evidence/20261025-grid-flash-review.json`.

Next hardware step: identify the actual card/drive again, confirm current body
and power, stage the exact EG with readback hash, then inspect recognition.
Programming needs explicit owner authorization for this concrete reviewed
candidate. No verified emergency recovery exists. The assessment explains
normal-updater stock rollback limits and the post-install grid/wake/LCD/EVF
checks. Do not reuse historical E: identity or the old sound assessment as
clearance for this candidate. Do not select a persistent candidate for staging.

Separately hardened persistent prototype: `.private/builds/20261025-grid-persistent-05/`,
MAIN 33,058,292 bytes, SHA-256
`e230338d7d513a54b44cea6e0f2073e3b8f22aee15f0aa848f552d293ce1d8e7`.
It passes 74 persistence checks. Missing/damaged workspace or destination/length
tables now reject load/save without falling through to original journal writes.
Nikon-format conversion survives modified-firmware restarts and normal saves;
only an explicit grid choice reenables the extension. Important native contract:
the third word of each schema triple is a mutable flash-source cache, not a
dirty flag. An initial overly strict guard rejected those native cache updates;
candidate 04 is superseded, candidate 05 validates immutable pairs instead.
The rollback function is still diagnostic, with no camera-accessible action.
It and full lifecycle/concurrency/physical durability remain on hold. Candidate
02 separately passed 10 native-key QEMU menu checks this turn; that does not
validate later candidate 05 or persistence across QEMU restarts.

## Compiled persistent-grid prototype — October 25, 2026

The owner authorized implementing internal persistence and building/testing it
in the lab. Current private candidate:
`.private/builds/20261025-grid-persistent-02/`, MAIN 33,057,940 bytes, SHA-256
`a0cda3a3c4acac326cfbc56ac9aca48b075f09c3a5742f8470a5f7da79bd508c`.
It is reproducible with valid EG CRC and independent full rebuild validation.
No outer update package, staging, camera/card access or installation clearance.

`features/settings_z7.py` adds guarded native journal descriptor/load/save/reset
hooks to the optional `grid_z7.build(..., persistent=True)` path. Ordinary grid
builds remain unchanged. `tools/build_grid_firmware.py --persistent` explicitly
selects the new emulator-only preset. It reserves 0x500 bytes at A9700000,
including an owned 90-record table. Record 89 is 16 bytes: magic WLS1, version 1,
grid choice 0/1, IEEE CRC32 of the first 12 bytes. Native property 0x102D stays
0/1; the live choice remains one aligned word at STATE+4.

Load tries extended format, retries original format before Nikon's reset path,
and defaults only extension data when its CRC/version/value is invalid. Saves
hook the normal main-journal routine, capture all native payloads plus extension
state into an immutable snapshot, and read back into separate buffers. The
176,744-byte temporary allocation is checked/freed; all payloads are compared,
native descriptor/logical-view pointers restored, and dirty state retained on
failure or generation changes. No UI/geometry hook writes flash directly.

`tools/audit_grid_persistence.py` passes 53 checks: compiled CRC, cold ABI,
fresh-instance 3x3/4x4 reloads, actual native startup caller, native reset,
old-format migration, CRC corruption, failed readback, allocation/program
failure, busy saves, generation changes, original-format conversion and six
program-boundary interruptions during first migration. All 89 native records
survive the sampled interruptions. These execute native instructions in
Unicorn with supplied OS/allocation/flash-controller boundaries; they do not
establish physical durability or a full QEMU persistence/reboot cycle.

The updated grid instruction audit passes 190 checks/270 geometry calls on
candidate 02. It also passes all 190 on the unchanged earlier RAM-only build.
Patch/container/Thumb tests pass 14; two optional integrations remain skipped.
Assisted QEMU live view passes all six checks at
`.private/research/grid/20261025-persistent-live-01/`, session
`20261025-141908-5174`; compiled handlers select native grid planes and Off
restores the scene. This QEMU probe does not persist flash across restarts.
The native-key menu probe has not been rerun on this persistent candidate.

Public scoped summaries are `evidence/20261025-grid-persistence.json`,
`evidence/20261025-grid-persistent-geometry.json`, and
`evidence/20261025-grid-persistent-live.json`. Read the implementation section
in `SETTINGS_PERSISTENCE_RESEARCH.md` before continuing. A diagnostic rollback
function is compiled and verified against a fresh unmodified stock loader,
but has no camera menu/updater integration. Its mode is RAM-only: do not power
cycle the modified firmware between conversion and a future stock update.
Wake/concurrency, repeated compaction/endurance, complete shutdown policy,
updater ordering, user-visible failure reporting and physical recovery remain
open. Invalid/missing workspace state currently falls through to original
storage APIs; audit fail-closed behavior before considering any installation.
The splash experiment still cannot compose with this workspace reservation.

## Internal settings persistence investigation — October 25, 2026

Read `SETTINGS_PERSISTENCE_RESEARCH.md`. The owner wants extension settings
inside the camera, independent of card swaps. `tools/trace_settings_storage.py`
passes 45 checks against pinned original instructions in isolated Unicorn.
The main settings journal is logical `0x0F`, with 89 native records and two
`0x40000`-byte regions at `0x12E00000` / `0x131E0000`. A supplied 90th record
survives fresh-instance save/load while preserving all native payloads. Explicit
old-schema retry/migration and original-format rollback conversion also work
with supplied descriptors. Bare schema replacement fails in both directions.
No migration, rollback or persistence hook has been installed in firmware.

Correction: the raw `0x102D` scalar writer accepts 32-bit values, including 2;
it does not enforce boolean semantics. Native menu/display code supplies or
compares 0/1. Raw setter acceptance is not compatibility. The main journal
wrapper also returns success after injected program failure; read-back is
required. Public scope/results: `evidence/20261025-settings-storage.json`.
No firmware build, camera/card access or full QEMU cold boot occurred. The
existing grid candidate remains RAM-only.

## Native 3×3 grid investigation — October 25, 2026

Read `GRID_3X3_RESEARCH.md`. The original investigation now has a standalone
emulator-only firmware candidate with native d9 choices **4x4 grid / 3x3 grid /
Off**. Keep the existing 4x4 choice. Grid choice is separate RAM state, defaulting
to 4x4 at workspace initialization; Nikon's native property 0x102D stays boolean.
The choice is not saved persistently. No card access, physical flash or outer
Nikon update package was involved; camera installation remains on hold.

Current private build: `.private/builds/20261025-grid-emulator-03/`.
MAIN is 33,053,800 bytes, SHA-256
`2762ccd5276e1c4720c06e26f636c6c551cafe3772eb6d24400b769c200cd348`.
Four guarded windows total 32 bytes, with 1,712 appended bytes. Builds/reports
are reproducible with valid EG CRC; the probe independently rebuilds the entire
MAIN/report. Normal installation presets exclude this feature. Do not compose
it with the splash experiment: both own the same workspace-init reservation.

`features/grid_z7.py` derives its geometry/table/property/UI contracts from
original Z7 C 3.80. The builder 0x10376DA0 uses three immutable 32-byte records
at 0x1064FD90; an atomic RAM choice selects the stock table or an appended
copy with two internal lines per axis. Dynamic-label flag 0x1209 and both native
focus/current-value helpers are required; earlier candidates exposed these UI
details and were superseded.

`tools/build_grid_firmware.py`, `tools/audit_grid_firmware.py`, and
`tools/probe_grid_firmware.py` provide build, instruction audit and isolated
menu/live probes. Final instruction audit passes 190 checks/270 geometry calls,
including cold reservation/ABI, invalid-state fallback and current-value marking.
The earlier pure geometry audit passes 91 checks. The QEMU production renderer
suite passes 292 checks; strict firmware-free register contracts pass 14.
Existing patch/container/Thumb suites pass 14, with 2 optional integrations
skipped; RAW-input suites pass 11 with workspace-local temporary storage.

The grid is a separate hardware display plane. The stock 0x20145620=1 stop
was resolved by the traced boolean write contract, then a functional LCD-grid
model was added from native registers 0x1600..0x1618. Observed black/gray styles, half-open
edges and plane priority remain explicit hypotheses. No invented completions
or host drawing injection is used. EVF and physical bit accuracy remain open.

Final native-key menu probe passes all 10 checks: initial Off plus 3x3, 4x4 and
Off selection/reopen, with correct labels, focus and current-value outlines.
Private evidence: `.private/research/grid/20261025-selector-final-02/`.
The earlier `20261025-selector-final/` run hit its 420-second watchdog; it is
superseded, preserved, and not a full pass. The runner now allows 900 seconds.

Final assisted live-view probe passes all 6 checks: compiled choice handlers
and the native visibility update produce visible thirds/quarters through the
emulated hardware plane, then Off disables the plane and restores the sampled
scene pixels. The entire final Off PNG additionally matches the initial PNG
byte-for-byte. Private frames: `.private/research/grid/20261025-live-final-02/`.
Native 1024x682 alignment yields thirds x=342/684, y=228/456; quarters
x=256/512/768, y=170/340/510. Color/priority remain emulator hypotheses.

Public source-only evidence: `evidence/20261025-grid-firmware-qemu.json`,
`evidence/20261025-grid-firmware-unit-v3.json`, and
`evidence/20261025-grid-display-latch-final.json`. Camera LCD/EVF behavior,
recorded files, wake/concurrency, persistent choice storage, composition,
installation acceptance and recovery remain unverified. Do not stage or flash.

## Image-creation feature shortlist — October 25, 2026

The owner wants useful shooting features inspired by newer Nikon bodies with
similar hardware. Read `IMAGE_CREATION_FEATURES.md` for the official-manual
comparison, current Z7 baseline, ranked candidates and evidence gaps.
Suggested first investigations: native 3×3 grid/framing guides, still-photo
highlight stripes using the existing movie path, independent M900 property/timer
audit, then a recipe selector based on compatible native Picture Controls.
The D780 provides an EXPEED 6/900-second precedent; Z7II/Z6II are dual EXPEED 6
and cannot be treated as throughput-equivalent to the original body.

The source review confirms that existing M900 still overrides property 0x11A3;
the port audit requires independent Z7 meaning and physical timing verification.
Do not turn that experiment into a newly completed feature claim. Existing
Creative Picture Controls, focus shift/peaking-stack preview, bracketing and
supported-lens focus recall are part of the stock baseline, not new unlocks.
Newer display/AF examples are design references; port feasibility is estimated.
No new firmware build, staging or camera access occurred for this research.

## Firmware-owned splash experiment — October 24, 2026

The owner explicitly authorized building a firmware and running it in QEMU.
That is a narrow exception to the earlier no-build hold for this emulator
experiment. Camera installation, staging and flash recommendations remain on
hold; no card/camera access or outer Nikon update package was involved.

`tools/build_splash_firmware.py` builds independent Z7 C 3.80 MAIN/EG images
from the pinned original container, twice reproducibly with valid EG CRC.
Every QEMU input is independently rebuilt and compared in full, including its
report. The feature is excluded from ordinary installation presets.

Current private build: `.private/builds/20261024-splash-emulator-02/`.
MAIN is 33,067,836 bytes, SHA-256
`dc6ec38c9b427374afd80be53d31d14edb4914e89f06abc73099a9e12f021f24`.
EG SHA-256 is
`a60b0c9db5003db532ffe596848e8ea8ae9e390b3b4928ab3c1066316ede2fd3`.
Three guarded instruction windows totaling 32 bytes are replaced; 15,748 bytes
of independent code/padding/PNG assets are appended.

`features/splash_z7.py` reserves 64 bytes at 0xA9700000 through the original
monotonic workspace initializer (cursor starts at 0xA9700040), arms after
original UI resource setup, and atomically consumes its own latch at the first
native full-screen clear. The 0x1042F152 hook accepts caller 0x104FFB19 only
with `[0,0,720,480,255]`; it runs before any visible menu paint. Both PNGs
are embedded in ROM. Native 0x10431738 performs splash/black cleanup drawing;
native delay 0x1017081E receives argument 2000. That argument is not a physical
two-second timing claim. The displaced original prologue then resumes.

`tools/audit_splash_firmware.py` passes 40 instruction/ABI checks, using mocked
OS/GPU boundaries. Evidence: `evidence/20261024-splash-firmware-unit-v2.json`.
The existing patch/container suites pass 11 + 3 tests. Physical low-memory,
concurrency, wake/LCD-EVF behavior, updater acceptance and recovery remain unverified.
Read the current section in `SPLASH_SCREEN_FEASIBILITY.md` for reproduction.

Two fresh assisted QEMU cold boots pass 27 checks each, with the exact embedded
splash as the first observed nonblack frame, native timed handoff, intact state
guards, complete native menu redraw/navigation and one presentation through
menu exit/re-entry. No host splash controller or drawing injection is involved.
The base boot still supplies synthetic power/system/MENU fixtures. Public
source-only evidence: `evidence/20261024-splash-firmware-qemu.json`; private
frames/state and logs: `.private/research/splash/20261024-firmware-03/`.
This proves the firmware lifecycle in assisted QEMU, not physical instant-on,
unassisted boot, live-view startup or readiness to flash.

Rejected first build and test runs remain private. Continuous QMP observation
caught an earlier 64-pixel gray sidebar before the PNG-builder hook; the earlier
host prototype's sampled "first-visible" claim did not test that interval.
Original queue tracing identified the earlier clear hook used now. Test-only
redraw waits were also corrected after exact comparisons caught text still being
painted. Keep these failures in the record; do not turn their partial successes
into installation clearance.

## First visible screen corrected — October 24, 2026

Historical host prototype, superseded by continuous firmware observations above.

The owner correctly rejected the previous preview's menu -> splash ordering.
The startup probe now intercepts the first native drawing call at 0x10430256
while the QEMU surface is still black. It draws the splash in that native
rendering task, holds that task with native OS delays while other guest tasks
run, restores a black backing through native PNG/GPU drawing, and resumes the
original first draw. The menu is only visible after the splash.

Two cold boots pass 41 checks each; source-only evidence is
`evidence/20261024-splash-first-frame.json`. Private artifacts are in
`.private/research/splash/20261024-first-frame-startup-02/`. The first normal
scene and later navigation are verified, including exact scene comparison at
the same established focus state. A native help-icon backing changes on its
first focus cycle; preserve the initial screenshot rather than masking that
difference in an exact-pixel comparison.

The original MENU fixture still schedules the first native scene internally;
the splash runs before that scene paints visible pixels. Removing MENU setup
and drawing from the idle application task produced a splash but no usable
handoff. Those unsuccessful runs remain private and are not cleared methods.
The new method is still a host-assisted rendering-boundary experiment, not a
firmware patch, physical instant-on result or live-view startup implementation.
The local replay viewer uses this corrected sequence. No camera/card access,
new firmware image or flash occurred; the port/installation hold remains.

## Automatic splash lifecycle experiment — October 24, 2026

Historical overlay experiment: this version waited for the menu, so its passing
checks did not establish the owner's required first-screen startup order.

The owner asked to investigate automatic startup. `tools/probe_splash_startup.py`
observes original UI initialization and automatically schedules the existing
native PNG draw after the first stable native display. Two fresh assisted cold
boots pass 30 checks each: one presentation, exact pixels, approximately two
host seconds of visible hold, exact scene restoration, MENU exit/re-entry and
navigation without re-showing. Results are source-only in
`evidence/20261024-splash-startup.json`; frames/traces remain private in
`.private/research/splash/20261024-auto-startup-02/`.

Important: the outer UI initializer 0x102697F4 runs again on MENU re-entry. It
is not a boot-only trigger. Its resource-setup block checks initialized guard
0xA1822D68, calls 0x103F9C0A, then clears the guard at 0x1026984A. Both cold
traces observe guard 1 in this block and guard 0 afterward; subsequent menu
initialization does not rerun resource setup. The host prototype arms at the
post-resource-return observation, consumes its own one-shot before drawing and
never modifies the native guard. This does not prove physical wake semantics.

Readiness detection, the one-shot state and timed synthetic focus redraw are
host policy, not installed firmware hooks. Production work still needs a native
graphics-ready/render-task event, an independent cold-reset latch and verified
timer/dismissal/wake/LCD-EVF behavior. Do not hook the outer initializer
unconditionally or repurpose its guard. The original display probe shares the
heap-backed drawing helper; its regression evidence is kept privately alongside
the new runs. All 14 original display checks pass after that refactor in
`.private/research/splash/20261024-display-probe-07/`. No firmware build,
card staging or camera access occurred; the
port/flash hold remains active.

## Splash takes priority — October 24, 2026

The owner wants splash loading investigated before film-roll work. Read the
new section in [SPLASH_SCREEN_FEASIBILITY.md](SPLASH_SCREEN_FEASIBILITY.md).
`tools/probe_splash_display.py` now presents an original 720x480 RGB PNG through
stock Z7 code in an isolated assisted QEMU guest. All 14 presentation checks
pass: exact full-screen pixels, native decoder/GPU trace, encoded-image heap
guards, caller register/scratch restoration, exact native menu restoration and
subsequent menu navigation. The PNG uses original heap allocation; only an
80-byte descriptor is staged on the diagnostic caller's stack. A fresh run and
private screenshots are in `.private/research/splash/20261024-display-probe-06/`;
sanitized results are `evidence/20261024-splash-native-display.json`.

This is host-assisted native presentation, not an automatic startup hook or
flashable splash feature. Earlier oversized stack-data and cross-task graphics
lock probes stalled or left the guest unresponsive; do not reuse those methods.
The successful probe supplies encoded PNG data only, with no host framebuffer
pixel writes. It closes its own guest and leaves existing app sessions alone.
Next: establish the correct startup/render-task transition, once-per-boot state,
bounded dismissal, wake suppression and LCD/EVF behavior. No firmware build,
card staging or camera access occurred; the port/flash hold remains in force.

Earlier offline milestone:
`tools/audit_splash_image.py` executes the stock resource getter, image wrapper,
libpng/zlib and original memory helpers with a controlled bounded allocator.
All 43 checks pass, including exact RGB/RGBA pixel output, buffer guards,
callee-saved registers/stack and selected allocation-failure cleanup. The
320x120 synthetic PNG decodes to 153,600 RGBA bytes. Evidence is source-only.
These unit checks alone do not verify GPU/LCD presentation. Startup event
semantics, production dismissal and wake suppression remain unverified.

## Film-roll feasibility — October 24, 2026

The owner asked whether a Canon Ritual-style experience could be built for Z7.
Read [FILM_ROLL_FEASIBILITY.md](FILM_ROLL_FEASIBILITY.md). Native custom Picture
Controls provide the initial recipe path. Nikon's original-model manual already
documents 20 Creative controls, contradicting the inherited report's dormant-
feature premise. A correction banner preserves that report while marking its
unsupported conclusions. Three narrow stock-image checks are recorded in
`evidence/20261024-picture-control-baseline.json`; no complete parser or new
rendering was validated. Photo counting, persistence and a hard shutter limit
remain research tasks. No firmware build, staging or camera/card access occurred.

## Source publication checkpoint — October 24, 2026

The owner requested a source push and review of possible contributions to both
vendored upstream projects. The root README now reflects the hardware reports:
WAV Preview works, automatic capture sound repeats during live view, and Enabled
OFF contains the loop. Historical preparation and test instructions below are
not current installation clearance. The port audit and flash hold remain active.

The latest stock assisted-emulator observation collected three distinct
0x041F0001 -> 0x04190001 callback deliveries without a shutter action. Controller
mode was 0 and the native capture-service state byte was 9 in each observation.
Read the new section in [CAPTURE_EVENT_TRACE.md](CAPTURE_EVENT_TRACE.md) and the
sanitized summary `evidence/20261024-stock-liveview-observation.json`. This is
negative evidence against the current trigger, not a physical-camera trace.

A separate stock capture-request probe timed out before recording any action;
it establishes no positive capture signal. No firmware source was changed for
these observations and no new candidate was built, staged or installed. Private
RAM, disassembly, emulator sessions and probe logs stay excluded from publication.

Publication checks were rerun on October 24: 8 root host tests, 11 QEMU Python
tests, 270 renderer contracts, 398 ISP contracts, firmware-free QMP realization,
and 14 synthetic patch/container tests passed. Existing-image probes passed 24
native-callback, 14 still-file and 60 selected callback/property checks. The
retrigger audit still fails both required no-photo rejection checks; its two
OFF checks pass. These results do not clear automatic shutter sound. No new
firmware build, camera update or sanitizer run was included. See
`evidence/20261024-source-validation.json` for scope and exclusions.

## Backward tracing anchor: still-file record — October 22, 2026

The owner asked how to obtain a verified per-photo signal. Read
[STILL_FILE_TRACE.md](STILL_FILE_TRACE.md). Original still-file finalization wrapper
0x1026FADC sends 0x041E0002 with a record ID through a separately registered
callback. Native record helpers expose slot/group/number/kind fields and compare
records while ignoring kind. Fourteen offline evidence checks execute that
wrapper, registration/dispatch and ID helpers with controlled file operations.

This is a new backward-tracing anchor, not a chosen shutter hook. File completion
can lag exposure, repeat or occur multiple times per photo; physical timing and
per-photo cardinality remain unverified. Follow upstream exposure/record creation
before connecting audio. No firmware source, image or camera/card content changed;
Enabled OFF and the flash hold remain in force.

## Native callback trace — October 22, 2026

The owner asked to keep tracing. Read [CAPTURE_EVENT_TRACE.md](CAPTURE_EVENT_TRACE.md).
The new audit executes the original registered Z7 callback instead of stubbing
its return. Two supplied classification cases schedule no native work, but the
existing sound hook still queues audio. Six stock/patched cases retain native
scheduling while exposing that unconditional custom admission. A separate native
zero-count AutoRelease probe also emits its request notification without invoking
release control, ruling that notification out as sufficient per-photo evidence.

All 24 trace evidence checks pass; this confirms the defect, not a replacement
trigger or candidate clearance. Real per-photo signal semantics remain unresolved.
Enabled OFF is owner-confirmed to stop repetition. Firmware source and existing
images were untouched; no rebuild, staging or camera write. The flash hold remains.

## Latest hardware failure: repeated live-view audio — October 21, 2026

The owner reports repeated sound during live view and Capture audio busy on
opening the menu. Read [LIVEVIEW_SOUND_REGRESSION.md](LIVEVIEW_SOUND_REGRESSION.md).
The owner confirms Enabled OFF stops the repeating sound on the camera. Leave it
OFF. This confirms containment, not correct shutter triggering. The latest
silent-property candidate is associated by sequence, without firmware readback.
It fails the shutter-cue behavior requirement; audible repetition is not success.

An audit-only probe of the existing binary queues three requests from three
notifications without an independently identified photo transaction, and confirms
the pending/finished restart path. Two required rejection checks fail; two compiled
OFF checks pass with controlled device boundaries. The callback's photo-specific
meaning was never established. Earlier passing callback tests missed this case.
No firmware source change, rebuild, staging, camera write or rollback occurred.
The port audit and flash hold below remain in force.

## Current owner caution and port audit hold — October 21, 2026

The owner raised the risk of ported camera code leaving the Z7 unusable and asked
for more care. Further flash recommendations and candidate staging are on hold
pending an independent Z7 port audit. Read [PORT_AUDIT.md](PORT_AUDIT.md) before
continuing. The most recently staged silent-property image remains experimental;
the earlier preparation/testing notes below are not clearance to install it.
Do not interrupt a camera update already running. Do not automatically roll back,
reflash stock, or prepare another candidate as a response to this concern.

Initial review confirms a Z7 stock base with Z30-derived custom feature code, not
proof that all copied interfaces are correct. The inventory identifies 23 direct
literal native sound call targets and 17 full-image edits; dynamic/assembly-embedded
targets and lifecycle/recovery gaps remain. The native translation dictionaries
are not used by the generated routines, so reviewing them alone is insufficient.
No camera/card/firmware mutation occurred in this audit turn. No complete port
audit or verified emergency recovery is claimed.

## Current Silent photography property correction — October 21, 2026

The owner followed the capture-start candidate's installation/test instructions:
still no audio, now with heading Silent mode required after a silent photo.
This supports trigger reachability; the remaining mode gate queries the wrong
property. The Z7's own Silent photography page 0xB2 constructor reads 0x576;
the port retained Z30 key 0x57B. Read [SILENT_PROPERTY_FIX.md](SILENT_PROPERTY_FIX.md).

New private build/review suffix: `20261021-silent-property-01`, full EG SHA-256
`9e636d645281ee9f92cb150b6dcc8d771b21ff95c47e45f538d951a1d932420b`.
Exactly one appended instruction byte plus two CRC bytes differ from the previous
candidate; length and menu/Preview code are unchanged. Both sound presets pass
60 capture checks and 18 playback checks using the original native property
getter/tables. Contradictory Z7/legacy values also execute the original Silent
photography menu constructor, exposing the previous mocked-getter test gap.
Sixteen firmware tests and reproducible/CRC checks for all four presets pass.
The candidate was staged on the re-verified E: Sony QD-G240F card at
2026-10-22 04:38 UTC (October 21 locally). Full SHA-256 readback matched the
candidate above. The previous card EG was backed up privately; SHUTTER.WAV and
other card files were preserved. The review bundle's card-staging.json records
the copy. The subsequent live-view regression above supersedes this pending
status: installation is inferred, and correct physical capture audio has failed.

## Current normal-capture callback correction — October 21, 2026

The owner now reports Waiting for capture after silent shooting, and Silent mode
required after one mechanical photo with the feature still enabled. This supports
the installed diagnostic build and late-hook mode gating, with no late-hook
notification observed for silent capture. Installation is inferred from the unique
headings; no readback or explicit updater-completion report was supplied.

Read [CAPTURE_START_FIX.md](CAPTURE_START_FIX.md). A separate normal native
callback at 0x100726AC was outside the previous diagnostic's coverage. The new
hook queues sound from its normal notification and retains the late hook for
diagnostics only, avoiding duplicate cues. All three callback paths and the full
native dispatcher now pass 48 capture checks for each sound preset; the existing
18 playback checks and 16 firmware tests also pass. Hardware triggering remains
unresolved until a camera retest.

New private build/review suffix: `20261021-capture-start-02`, full EG SHA-256
`efcfbda40439354e8707a2c1e8c0b16b5e47a27c0fe8999110ca98eb9f15dc1c`.
It was staged on the re-verified E: Sony QD-G240F card at 2026-10-22 04:10 UTC
(October 21 locally). Full SHA-256 readback matched the candidate above. The
previous card EG was backed up privately; SHUTTER.WAV and other card files were
preserved. The private review bundle's card-staging.json records the copy.
The owner subsequently followed the installation/test instructions and reported
Silent mode required after the silent photo, with no audio. Installation is
inferred from that sequence without readback; the property fix above supersedes
this candidate. The first offline relocation attempt failed
null-callback branch checks and was corrected before producing this candidate.
The candidate passes 13 admission checks, 12 private review checks and all 17
assisted-QEMU sound-menu checks with 30 native key events and return to live view.
No abort was observed in that run. The source graph has been refreshed locally.

## Startup splash investigation — October 21, 2026

The owner asked whether a custom splash could be installed. Read
[SPLASH_SCREEN_FEASIBILITY.md](SPLASH_SCREEN_FEASIBILITY.md). Private stock scans
confirm PNG resources and libpng strings, with 198 of the first 200 signature
hits verified by Pillow and 16 large resources verified by chunk CRC. An original
compact embedded image plus a one-time native UI hook is promising; no startup
logo replacement, callable decoder interface or power-on-only hook is yet proven.
The current EG has 489,334 bytes of room under the existing patcher limit. This
was read-only firmware investigation; no splash build or card/camera write occurred.

## Current capture-trigger investigation — October 21, 2026

The owner clarified that WAV playback works but shutter replacement does not,
with Enabled ON, SHUTTER.WAV selected and Nikon Silent photography ON. Read
[SHUTTER_TRIGGER_FIX.md](SHUTTER_TRIGGER_FIX.md). A native branch bypasses the
old hook entry and lands inside its patched literal; this is reproduced offline.
The new shared-callback hook preserves both native paths and passes 24 capture/
diagnostic checks for both sound presets. Diagnostic titles distinguish callback
reachability from mode/busy gating. The role of this defect in the failed camera
test remains unknown; actual shutter-triggered sound still fails by owner report.

After diagnostic staging, the owner again reported no shutter sound and initially
could not identify the expected heading (described as a "tile"). The later
Waiting for capture / Silent mode required comparison is recorded above. The diagnostic
is the page title above Enabled/Sound file/Preview/Reload, not a new menu row.
With Enabled ON and no error it should initially read Waiting for capture;
after a photo read that heading without power-cycling or selecting ON again,
which resets the capture status.

New private build/review suffix: `20261021-shot-fix-01`, full EG SHA-256
`51dd7feb01e991d0cbce93e952ac42be98981dca510187e2767141ec8974dd9b`.
The diagnostic candidate was staged on the re-verified E: Sony QD-G240F card at
2026-10-22 03:39 UTC (October 21 locally), with full SHA-256 readback matching
the candidate above. The previous card firmware was backed up privately;
SHUTTER.WAV and other card files were preserved. The private review bundle's
card-staging.json records the copy. The later unique diagnostic headings above
support this build running on the camera, inferred without firmware readback.
The new build also passes 13 candidate checks, 12 private review checks and all
17 assisted-QEMU sound-menu checks on an isolated retry. The first QEMU attempt
stopped during assisted menu entry; both outcomes are preserved in the sanitized
capture evidence. Card staging and the later inferred installation are recorded
above; shutter-triggered audio has not passed.

## Current audio correction — October 21, 2026

**Latest owner result: "the wav actually works now!"** This follows staging the
corrected candidate below and the installation/Preview instructions. Record this
as owner-reported audible WAV playback; the subsequent capture failure above
separates that result from shutter-triggered playback.
Corrected installation is inferred from that sequence, without firmware readback.
Shutter-triggered playback, repeated-use stability and recovery are not established.

Read [AUDIO_PLAYBACK_FIX.md](AUDIO_PLAYBACK_FIX.md). The owner tested the stronger
WAV: still no audible output; Sound busy appears when moving the selector after
activation. The file matches every documented 8 kHz/mono/16-bit/canonical-header
requirement. The installed code reads the format table instead of the native busy
byte, and requests a type outside the native exclusive range. Both blockers are
corrected in source, with five failing checks reproduced against the installed
image and all 18 request-path checks passing for corrected full and sound-only.

New private build/review directory suffix: `20261021-audio-fix-01`. Full EG SHA-256
is `770408b99ff547dd972486656285307b17e4ff2674937dbb50f144200233b7be`.
The corrected firmware was staged on the re-verified E: Sony QD-G240F card at
2026-10-22 03:08 UTC (October 21 locally). Full SHA-256 readback matched the
candidate above; the previous card firmware was backed up privately, and the
stronger SHUTTER.WAV and other card files were preserved. The private review
bundle's card-staging.json records the copy. The owner subsequently reported
working WAV playback as recorded above. Earlier silent-playback reports below
describe the previous build, before this correction.

The corrected full image passed 17 isolated QEMU menu checks with 30 native key
events. All four builds are reproducible with valid CRCs; 16 existing firmware
tests, 13 candidate checks and 12 private review/header checks passed. Both sound
presets passed 18 playback-admission contracts. Results are recorded in
`evidence/20261021-audio-playback-fix.json`. Root default/native app configuration
still names the earlier private build; launch the corrected build explicitly
when inspecting it. Restart validation of an older payload against the changed
patcher source will intentionally reject it; the previous binaries are preserved.

## Latest hardware result — October 21, 2026

The owner reports **the flash worked and the sound setting is present** on the
original Z7 C 3.80, no paid RAW-video upgrade. This follows the camera's
`Current A3.80 → New A3.80` confirmation and an updating warning/progress report
at about 30%. The verified card candidate was the full EG with SHA-256
`9e98eae9b726d1ced0e9cef60c89b6ef25eff369430673e753b5c3054be4f6b4`.

This establishes an owner-reported same-version installation, subsequent camera
operation and visible sound-menu entry. The exact completion message, firmware
readback, submenu operation, WAV loading/playback, capture, video and recovery
have not been independently observed. Do not expand this result to full hardware
validation or a proven rollback path. Earlier preparation notes below describe
the state before this first installation.

A private canonical test sound is prepared at
`.private/sound-test/20261021-01/SHUTTER.WAV`: 0.18 seconds, 660 Hz, 8 kHz,
mono signed 16-bit PCM, with fades and approximately 6% full-scale peak. Its
44-byte header, sample count and exact normalization roundtrip passed. At the
owner's request it was copied to the verified E: Sony QD-G240F card root as
`SHUTTER.WAV`; complete readback matched SHA-256
`e8bc84dc82c53e36c5ec8fc8a28556272b367a7e93ed0e0c91782797ea7ea5cb`.
Existing card files were preserved. The private sound-test `card-staging.json`
records the copy. The owner then reported **Sound file shows SHUTTER.WAV;
Preview produces no error but nothing audible**. Loaded-file/menu behavior is
owner-reported; audible output has not passed. Preview is designed to work with
Enabled OFF. Ordinary photo/playback has not been explicitly reported.

On resuming October 21, a stronger test WAV was staged on the re-verified E:
Sony QD-G240F card: `.private/sound-test/20261021-02/SHUTTER.WAV`, 14,444 bytes,
SHA-256 `d9b38aae45fbe7cb6ccbe79e64bafc40c2d69d987beb6608f00d8c0fc1145ac0`.
It contains three faded notes at 1, 2 and 3 kHz, 0.9 seconds total, 50% peak
amplitude. The earlier 0.18-second/6% tone is preserved locally, including a
verified copy of the old card file. Both WAVs passed the exact installed full
image's native validator and converter; every converted stereo PCM byte matched
the independent interpolation reference, output was nonzero and buffer guards
held. This checks parsing/conversion, not audio scheduling or speaker output.

The new card file passed complete SHA-256 readback. Firmware and other card
files were not changed; another flash is not needed for this test. Next safely
eject, insert into the camera, select Sound file → SHUTTER.WAV again and use
Preview with Enabled OFF. Audible output from this stronger file is pending.
If still silent, investigate native audio routing/gain and use normal Nikon
beeps as a separate control; do not infer a volume-only cause from the first test.

## Native Windows continuation — October 21, 2026

The app now runs on this laptop without WSL. Double-click `Start-Z7.cmd` or open
<http://127.0.0.1:8787/> while the prepared server is running. It was left paused
after verification to save CPU; click **Resume**. English browser controls and
keyboard/menu instructions are included. The selected private build is
`.private/builds/20261021-laptop-01`; the earlier laptop build is preserved.

QEMU 10.2.4 was compiled from the pinned archive with a separate MSYS2/UCRT64
toolchain under `.private/`. The existing system MSYS2 was not updated. A private
CPython 3.12.14 core and the local virtual environment keep the prepared app
independent of the Codex runtime cache. Firmware, binaries, guest diagnostics,
screenshots and Graphify output remain ignored. No camera/card writes occurred.

Current native validation: 16 firmware tests with no skips; all four payloads
match the accepted emulator baseline; 13 candidate admission/corruption checks;
5 launcher tests; 11 Python RAW/input tests; 270 renderer and 398 ISP contracts;
firmware-free QMP/TCP realization; 21 general UI checks; 17 sound-menu checks
each for full and sound-only. ASan/UBSan were not run on this Windows host.
See [the sanitized native results](evidence/20261021-windows-validation.json).

Cold assisted boot took about 140 seconds. The old fixed 12-second menu-return
verification window expired on this host despite subsequent scene recovery.
The verifier now records per-cycle timing with a configurable bounded deadline;
the three successful returns took 16.890, 16.985 and 18.453 seconds, each with
zero scene-region pixel RMS difference, continued ISP batches and the same guest
session. Native Windows stdio corrupted batched QMP smoke requests; the smoke
check now uses sequential commands over localhost TCP, matching the controller.

Fresh setup/rebuild commands are in [WINDOWS_BUILD.md](WINDOWS_BUILD.md).
`Setup-Z7.ps1` builds privately and runs native host/candidate checks;
`tools/check_windows.ps1` repeats firmware-free host checks. Linux setup now
also adds the vendored patcher to the new venv's import path, which is required
for candidate validation outside the firmware builder. WSL command construction
was unit-tested; an actual Linux/WSL run was not repeated on this laptop.

No complete modified Nikon container, complete camera updater acceptance,
recovery route or actual WAV playback was validated by the emulator work.

## Hardware preparation continuation — October 21, 2026

The owner authorized an experimental flash attempt and confirmed original Z7,
C 3.80, **no paid RAW-video upgrade**. Read [FLASH_ASSESSMENT.md](FLASH_ASSESSMENT.md)
before continuing. A separate native EG path was found in the Z7 stock code;
a complete outer container is not the only route worth investigating. Twelve
bounded native header/filename checks and all stock container/module CRC checks
passed. The private bundle `.private/flash-review/20261021-01/` contains the
reproducibly rebuilt full candidate as `candidate/EG161080.BIN` and separate
untouched stock inputs. This is an offline review, not hardware acceptance.

The candidate retains its CRC and entire appended tail. The native filename
pattern is `EG1610??.BIN`; the longer literal filename used in upstream build
examples does not match the tested loop (FAT aliases are untested). The storage
descriptor accommodates the candidate, but the complete updater and flash writer
remain untested. Same-version acceptance is unresolved. No verified emergency
recovery is available; stock files are not a full flash/calibration backup.

The owner then identified E:. It was verified as a removable, writable Sony
QD-G240F XQD/exFAT card, with no root user/firmware files. At 10:47 UTC the
candidate was copied as `E:\EG161080.BIN` and its complete SHA-256 read back as
`9e98eae9b726d1ced0e9cef60c89b6ef25eff369430673e753b5c3054be4f6b4`.
No formatting/deletion or camera flashing occurred. The private bundle's
`card-staging.json` records the copy. Battery charge and the real firmware screen
are still unconfirmed. Eject normally and stop at the camera's firmware version
screen, before selecting Update or Yes, for the proposed recognition check.

The owner subsequently reported the actual camera page shows **C 3.80** with
**Done, Update, Delete firmware files**. This is a user-reported recognition
observation; update execution, same-version installation and post-boot behavior
are still untested. Next inspect the separate confirmation dialog after choosing
Update, before choosing Yes, and confirm a fully charged battery.

The owner then reported the separate warning/confirmation dialog: **Update?
Current A3.80 → New A3.80**, Yes/No. This confirms the same-version choice is
offered, not that programming or post-boot operation succeeded. No Yes selection
or completed flash has been reported. The battery prerequisite remains necessary.

## Current state

The local firmware build and assisted QEMU run work. We corrected the sound
port's live-view failure and custom-menu crashes. Build `20261020-09` is the
accepted emulator baseline. All source and local fixes are included in the two
component directories as regular files; cloning this repository needs no submodule
initialization. Upstream origins/commits are recorded in `UPSTREAMS.json`.

The owner's physical camera is an original **Z7, C 3.80**, without the paid
RAW-video upgrade (confirmed October 21). The first same-version full-EG flash
and visible sound-menu entry are now owner-reported successful; see the latest
hardware result above. Audio, capture and recovery still need physical tests.

## Verified results

| Gate | Result |
| --- | --- |
| Upstream patcher tests with real private input | 16 pass, none skipped |
| Repeated builds and module CRC | All four presets pass |
| Histogram/level gate executions | 1,024 pass per applicable preset |
| Config hook calling convention | 3 cases pass per sound preset |
| Route fallback versus native instructions | 6 cases pass per sound preset |
| Data fallback versus native instructions | 4 cases pass per sound preset |
| Menu layout/callback/native hierarchy contracts | 20 checks pass per sound preset |
| Candidate admission and corruption rejection | 13 checks pass |
| Full image general UI, pause/resume, three MENU roundtrips | 21 checks pass |
| Full and sound-only submenus, independently | 17 checks each, 30 native key events each |
| Earlier QEMU synthetic tests | 11 Python, 270 renderer, 398 ISP checks; ASan/UBSan clean |

The submenu checks include the actual active page and RAM state, visible titles,
OFF, ON without a WAV, failed file selection, Preview/Reload without a file,
back/reopen with native selection retention, and return to the reference processed
live-view scene with continued ISP batches. Real WAV loading/playback is untested.
Read `SOUND_MENU_FIX.md` for the exact bug mechanisms and `LAB_REPORT.md` for history.

## Fresh laptop setup

Use Python 3.12+ in Linux or an explicitly selected WSL distribution. The desktop
used **Ubuntu**, not the unrelated `ubuntu-noble` coursework distro. Do not reset
or replace an existing distro. The upstream component docs mention older paths and
`ubuntu-noble-nikon`; the root instructions below govern this workspace.

1. Clone this repository and open a Linux/WSL shell in the checkout.
2. Install the OS dependencies and run setup:

```sh
sudo apt-get update
sudo apt-get install build-essential ninja-build pkg-config python3-venv \
  libglib2.0-dev libpixman-1-dev zlib1g-dev libfdt-dev
python3 tools/setup_lab.py --jobs 4
```

The helper creates `~/.local/share/wonderlantern-z7/venv`, installs the tested
dependencies, builds checked QEMU 10.2.4 and generates synthetic CMOS inputs.
The QEMU archive hash is checked by `z7-qemu/tools/build.py`. Allow several GB;
use `--jobs 2` on a smaller laptop. Generated build files live on the Linux
filesystem. The local interpreter/distro configuration is stored in ignored
`.private/lab-environment.json`; no desktop username is required.

3. Obtain your own official input from
   <https://downloadcenter.nikonimglib.com/en/download/fw/558.html> and place it at
   `.private/stock/Z_7_0380.bin`.

| Input | Size | SHA-256 |
| --- | --- | --- |
| Original container `Z_7_0380.bin` | 34,472,614 | `07cf19513ada5b770caec4cfc3531a6734c48aede28dcec037f0f8374ef441a2` |
| Extracted stock MAIN | 33,052,088 | `e6df1764323fb1c287159dd3ce1c84ac93c72b96ba6eb09c070295c093fecbff` |

The patcher validates the original container and extracted module automatically.
Keep original firmware and all generated candidates private.

4. Build and validate locally:

```sh
LAB_PY="$HOME/.local/share/wonderlantern-z7/venv/bin/python"
"$LAB_PY" tools/build_firmware.py --output .private/builds/20261020-09
"$LAB_PY" tools/check_candidate_inputs.py --build .private/builds/20261020-09
"$LAB_PY" tools/probe_sound_menu.py --build .private/builds/20261020-09 \
  --output .private/evidence/laptop-full-menu-01 --exercise
"$LAB_PY" tools/probe_sound_menu.py --build .private/builds/20261020-09 \
  --preset shutter-sound --output .private/evidence/laptop-sound-menu-01 --exercise
```

Output directories must be new. After the first build use a new suffix and pass
that directory to the launcher. Expected MAIN outputs for unchanged firmware source:

| Preset | Size | SHA-256 |
| --- | --- | --- |
| full | 33,064,940 | `1d456c84709650e90cc6decd0877a9a51d4692bacc5477fa21ea28fba67cfb76` |
| shutter-sound | 33,064,840 | `0fe02a264926fe215484fd233b994d26fbdf9e6e4b2358df30027b8d82a93c0d` |
| liveview-dual | 33,052,156 | `b15532154d9bff9aea4649b8977f2c9ed737aba4256a7cc5e40880024761b9ff` |
| m900 | 33,052,120 | `806c026b3c1aed197326ad8cc7e78692016b488d863264b6ce3a7f24d28038db` |

5. Start the browser demo:

```sh
"$LAB_PY" tools/launch_z7.py
# Another local terminal, while the server runs:
"$LAB_PY" z7-qemu/tools/verify_ui.py --menu \
  --output .private/evidence/laptop-general-ui-01
```

On Windows use `Run-Z7.ps1 -WslDistro Ubuntu` after completing Linux setup/build.
`--linux-python` and `--wsl-distro` on `tools/launch_z7.py` support custom setups.
Open <http://127.0.0.1:8787/>. MENU/arrows/OK/DISP are native guest inputs. From
fresh shooting: MENU, left twice, down four times, right, up, OK opens Shutter sound.
Stop an existing owned server before reusing its port. The browser Stop control
stops the guest but leaves the HTTP server available for inspection.

## Next investigation

1. Continue the dedicated EG updater investigation from `FLASH_ASSESSMENT.md`.
   Stock container/module layout and CRCs are mapped; the complete outer digest
   remains unsolved for Z7. Our `.main.bin` is a QEMU payload; `.eg.bin` is an EG
   module. Neither is a validated camera update container.
2. Establish complete updater version/compatibility checks. The owner's camera
   already has 3.80; Nikon's official page lists 1.00–3.70 as the supported starting
   versions. Modified same-version acceptance is unknown. No paid RAW upgrade.
3. Find a concrete, model-specific boot recovery/rollback route and what still works
   after a bad boot. Reinstalling stock requires a functioning installation path;
   do not assume a saved stock file alone provides recovery.
4. Investigate actual WAV/card/audio and capture behavior. Current tests only prove
   missing-file handling and selected assisted-emulator paths. No verified real
   sensor, AF, shutter timing, recording or update acceptance follows from them.

Preserve all original inputs and earlier candidates. Card staging is complete;
the reviewed camera recognition step is next. This handoff does not authorize posting firmware, private dumps or
screenshots to the public repository.

## Source orientation and troubleshooting

- Sound fixes: `z7-firmware-extensions/src/z30_extensions/features/` files
  `shutter_sound_z7.py`, `sound_layout_z7.py`, `sound_ui_z7.py`.
- Root `tools/verify_sound_*.py`: native instruction/layout regressions.
- `tools/probe_sound_menu.py`: owns an isolated guest and captures abort context.
- `z7-qemu/tools/firmware_input.py`: re-creates the candidate from private stock
  and compares every payload byte before launch/restart.
- `z7-qemu/tools/interactive.py`: native-key browser controller and assistance.
- `z7-qemu/qemu/nikon-z7-lab.c`: emulated peripherals and diagnostics.
- Use Graphify when available: `graphify .`, then `graphify query "question"`.
  Generated graphs are excluded and can be recreated from this source.

Do not trim appended patch code back to the stock MAIN length. Only the final two
EG CRC bytes are omitted for QEMU. Keep calibration/startup assistance explicit;
do not conceal unknown device accesses by supplying invented completion values.
Capture the abort reporter at Thumb `0x100545EC`; R0 identifies exception kind,
R1 points to saved context. Copied exception strings on its stack are insufficient
to identify the fault. See the probe for checked offsets.

Some desktop command-runner contexts could not start WSL/network worker threads;
the existing Ubuntu environment worked through the desktop process runtime. That
was a host tool issue, not a reason to reset the distro. A normal laptop shell
should use the ordinary commands above. Do not copy desktop `.local` manifests:
they contain absolute host paths and QEMU fingerprints; regenerate them.

## Included and excluded

All component source, local fixes, root helpers, license notices, reports and a
sanitized validation summary are included. Original Nikon input, generated firmware,
QEMU executable/source downloads, RAM/disassembly traces, camera UI PNGs, local
tokens, virtual environments and runtime logs remain only on the desktop. Rebuild
them from your own input. The public source is sufficient to reconstruct the lab;
it is not a backup of the ignored private artifacts.
