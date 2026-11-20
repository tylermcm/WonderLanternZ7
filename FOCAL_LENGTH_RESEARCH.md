# Original-Z7 focal-length port research

November 20, 2026. Independent original Nikon Z7 C3.80 work informed by the
pinned JKWTCN MIT focal-length feature. The sampler and initial LCD landscape
overlay are implemented. EVF, rotation and broader lifecycle remain open.
Native firmware, generated packages, screenshots and dumps remain private.

The target remains live focal length from an electronically communicating lens,
including manual zoom, independent per-preset selection, missing/invalid-data
suppression and LCD/EVF context handling. Taking a photo or reading EXIF is not
a substitute for that live source. Fractional values must remain representable.
The port must preserve native VR, lens-controller and existing display behavior.

## Initial independent LCD overlay

Optional `display-focal-probe` includes the existing Other-information and
histogram stack and requires GUI API32. Its native text object uses regular
slot1198 and label298, separate from battery1199/299 and VR widget50. The initial
landscape window is110,194..220,218 in the original LCD coordinate space. It
formats both24mm and24.5mm and obeys the independent per-preset Focal switch.
Occupied slots/labels are rejected; detached objects cannot paint through stale
pointers. Native object construction, visibility, dirty and font-cache helpers
remain in use. No native VR control or descriptor is edited by this overlay.

Current module03 is reproducible SHA
bd3c4ccad9a5ec7dbebd4e3075c3119c9bdbde385c688a26a7a089c8e65c3b36,
17420bytes/image17152/BSS5444/API32, unchanged host07. The targeted overlay audit
passes45 checks, including four supplied current preset states, Other/Focal
independence, fractional formatting, missing data, foreign ownership, native
state invalidation and failed-submit retry. Native key cycling has separate
coverage; supplied current preset states do not establish new physical key flows.

Assisted-QEMU live03 passes20 checks/13 frames. It supplies incoming properties
1C14/1C01 explicitly, with no native snapshot, visibility or pixel stores.
Fractional and whole text change real pixels only inside the owned window.
Other OFF retains identical focal pixels. Focal OFF, absent lens with a stale
value, and master OFF restore complete captured native RGB; master OFF restores
all61 native descriptor masks. PNG fingerprints and decoded RGB comparisons
were independently rechecked, and private key-frame crops inspected. This
establishes scoped rendering with supplied lens values, not physical telemetry.

Live01 stopped in baseline setup because a single DISP press reached native
page2 rather than3. The established key-and-wait helper corrected that fixture.
Live02 on module01 exposed a production bug: Other OFF erased focal pixels while
the cached label remained24mm. Module03 requests repaint after native snapshot
delta or custom-mask changes, preserving the100ms cadence and label caching.
These are invalidation inputs, never completed-paint fences. Failed submit keeps
the request pending; successful extra submission must actually invoke the owned
painter before presentation. Earlier failures remain private and are not passes.

The host instruction fixture now allows30s wall time while retaining its10M
instruction cap and all stack/callee-save guards. A diagnostic on the unchanged
module returned load status8 in10.703s, beyond the old10s wall budget. Direct PNG
fixtures retain their10s default. Current regression counts and exact source
identities are recorded in `evidence/20261120-native-focal-overlay.json`.

Focal combined with horizon, EVF, rotated information, AF states, native MENU return, output changes and
same-type lens reconnect still need implementation or broader live validation.
Those contexts are rejected by the initial overlay instead of applying LCD
coordinates to another layout. The full display-port goal remains unfinished.

## Native layout contract after restart

`tools/audit_z7_focal_layout.py` executes original constructor102F17B8 and text
wrapper102F32AE. Its175 checks cover20 text cases and five constructor cases.
VR50/control2 has rectangles40,194..107,218;62,292..129,316;284,16..360,40 for
scenes0/1/2. Other scene values clamp geometry to bank2. Logical font19 maps to
font100 except exactly scene2, which maps to109. Varying snapshot orientation338
does not change this wrapper's selection; this does NOT validate rotated pixels.
The wrapper retains the caller paint argument; the original VR caller supplies1
ordinarily and2F6 for scene2. No pinned Z7II palette number is borrowed.

The constructor inserts the SAME object into listsA201E3B4/A201E47C/A201E544 when
their corresponding source rectangles are nonempty; parent comes fromA201E394.
The audit supplies allocation/list insertion, pool/parent context, text setup
and draw sinks. Original geometry, font selection, font-attribute query and style
setter execute. The query103FBC32 returns1 for both mapped fonts; it is not a
height query. Font-table heights are20/24 for fonts100/109. Source controls
remain unchanged except the constructor's object
pointer; snapshot bytes remain unchanged. This identifies native contracts and
does not implement or establish an EVF overlay, output switching or rotation.

Earlier handoff names were wrong:10369214 propagates control dirty state and
102F27A8 selects permission/visibility masks. Actual text geometry copy begins
at102F333E. Neither of the earlier leads is a placement service or paint fence.

The first focal/horizon live run is FAILED:16 checks pass and the owned-window
comparison fails after native24.5mm is painted. Differences outside that window
are confined to the earlier ADL edge area,64/65/84 pixels against same-ISO-phase
references. ADL controls/masks match, but its pixels also vary between captured
focal-disabled references. These observations do not clear the failure or prove
its cause. The revised fixture additionally requires whole-native RGB to repeat
within every observed ISO phase before enabling focal. References remain complete
captured frames; no compositing, pixel exclusions or tolerance is introduced.

Revised live02 is also FAILED:61/62 checks,33 frames. Whole-native frames repeat
in both ISO phases by reference23. Fractional and whole focal text then match
settled references exactly outside the owned window; Other OFF retains the
identical focal crop. After Other ON/Focal OFF, full RGB matches transient
reference1. Reenabling focal differs on40 ADL edge pixels against every
same-ISO-phase reference. Missing-lens/return/master-OFF checks were not reached.
All33 PNG fingerprints and recorded memberships were independently verified.
No production C or package was changed, and neither failed run is cleared.

Next control must exercise Other OFF/ON on the horizon with focal NEVER enabled,
to distinguish background reconstruction from the focal object's contribution.
The existing GPU model's approximate YUV/alpha handling is only a possible lead.
Another long combined run needs evidence from that control or the actual repaint
path first; increasing sample caps or excluding edge pixels does not resolve it.

## Live source independently bound

The original native PTP property5008 description10341856 and current-value
handler103418B6 call1034231A. That getter reads property1C01 through103FE85E and
multiplies it by10. [libgphoto2's primary protocol definitions](https://github.com/gphoto/libgphoto2/blob/master/camlibs/ptp2/ptp.h)
identify5008 as FocalLength; its [native value rendering table](https://github.com/gphoto/libgphoto2/blob/master/camlibs/ptp2/ptp.c)
uses0.01mm per wire unit. Combined with the original scaling instructions, this
establishes the original1C01 value's tenths-of-mm representation. The new module
reads the native property directly; it makes no PTP transaction or EXIF read.

Original producer1016342E updates that property from live lens queries. Type1
uses309E/309D and original fractional conversion1015BE8C; supplied24/32768
publishes245. Type3 uses601D and original encoded-value table10204FCC. Stable
values avoid repeated publication. Original1C14 is the lens type property;
native property descriptors bind1C01 toA24E25A8 and1C14 toA24E2600. This is an
independent original-Z7 binding, not a shifted-address port.

`plugins/focal_sample.h` reads1C14, accepts types1/3, reads1C01, rejects zero and
FFFFFFFF, and rechecks the type before returning the value. Invalid type states
can leave a previously valid native focal property unchanged, so value alone is
insufficient. The type recheck rejects an observed transition; it is not an
atomic lens-identity or same-type reconnect guarantee. GUI lifecycle must still
invalidate cached presentation across menu/output/lens changes.

Reproducible diagnostic `focal-sample` is256bytes/image192/BSS4/API12, SHA
de0b258fcd6554cc8633c4f6d095404217f1b472c0c96fac6a8d649d2e314398.
`tools/audit_z7_focal_source.py` passes147 checks: actual native property lookup
and reads, compiled sampler, five observed type transitions, original PTP
scaling, three fractional and14 encoded producer cases, stable-value suppression
and stale-value rejection. Incoming lens-query data, native property publication
and loader/kernel services are supplied. Actual lens hardware is unverified.
The first audit attempt incorrectly assumed the native PTP gate rejected type4;
the original gate accepts it. The feature's type1/3 policy remains explicit and
separate from that broader native PTP admission. No production correction was
needed. Existing Other01 rebuilds byte-identically; root55/no-skips pass.

## Native shared text identified

The original Z7 updater table binds widget50 to102F6BF7 and preparation to
1036F2B1. It contains three controls: VR imagery in0/1 and mm text in2.
The native updater reads snapshot+AC and+B0, clamps the latter to60..40000,
divides by10 and calls the original101709A8 formatter with `%dmm`. Supplied245
therefore produces24mm. This existing formatter alone cannot implement24.5mm.
With supplied text-control visibility, zero formats as6mm; hiding zero depends
on the preceding native preparation rather than on the formatter.

The preparation prefix through1036F35C enables text only when the supplied AC
field and B0 value are nonzero and context135 is0 or2. The remaining native
context/layout services are outside this prefix audit. The original collector
copies source offsetsE4/E8 to snapshotAC/B0; its key table atA1828E88 associates
those source offsets with153D/1548. These facts identify the VR-associated
snapshot path. They do not establish live electronic-lens focal telemetry or
the meaning of every lens/context value.

`tools/audit_z7_focal_native.py` passes106 checks, covering18 native formatting
cases across supplied output values0/2 and32 preparation-prefix cases. Original
updater, formatter and prefix instructions execute; incoming state, dirty
predicate and drawing sinks are supplied. Neither pixels nor hardware telemetry
are established. The original raw property lookup rejects2014; that namespace
result is not evidence about equivalence to the pinned Z7II getter.

## Binding and ownership consequences

The pinned Z7II feature uses a dedicated widget60 and live getter10634177 with
keys2014/2001. Original-Z7 widget60 instead belongs to flash-focus status. Neither
its descriptor nor its source getter can be borrowed by address or numeric ID.
Original widget50 is already included in Other information; routing independent
focal text through that parent without separating ownership would couple the
Focal switch to the Other/VR switch. That would violate the intended behavior.

The live property source above is now identified and instruction-validated with
supplied lens inputs. Next use a separately owned native text object
or derive rigorously separate child ownership, preserving the existing VR field.
The battery overlay's native container allocation is an existing local lead, but
its pool slot1199 and text label299 are already reserved. An independent focal
object must verify available capacity, avoid occupied slots, follow native
teardown and update/erase only on the correct GUI/output lifecycle.

## ADL restoration investigation

Other-information horizon live01 remains failed. A new15-check audit,
`tools/audit_z7_adl_repaint.py`, replays the two immutable captured incoming
states through the original ADL updater, dual-image selector, output-style query
and object-reset instructions. Both select native resources2968/2969 and the
same reset/drawing arguments. Captured snapshots, masks and control records are
also identical. The full captured RGB still differs by65 pixels; this audit
explicitly records `pixel_mismatch_cleared=false` and the failed input-run status.
Dirty eligibility, owned substitute object storage and drawing sinks are
supplied. It does not execute the later GPU composition or prove a paint fence.

The next ADL diagnostic should distinguish object bitmap state, native dirty
clear/repaint and final overlay composition. Repeating the unchanged live test
without additional observations is not a useful diagnostic. Do not drop edge
pixels, combine reference frames or reinterpret this request audit as pixel
restoration acceptance.
