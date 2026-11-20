# Original-Z7 focal-length port research

November 20, 2026. Independent original Nikon Z7 C3.80 work informed by the
pinned JKWTCN MIT focal-length feature. No focal-length display module is implemented
yet. A standalone native sampler is now implemented; the text overlay remains
open. Native firmware, generated packages, screenshots and dumps remain private.

The target remains live focal length from an electronically communicating lens,
including manual zoom, independent per-preset selection, missing/invalid-data
suppression and LCD/EVF context handling. Taking a photo or reading EXIF is not
a substitute for that live source. Fractional values must remain representable.
The port must preserve native VR, lens-controller and existing display behavior.

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
