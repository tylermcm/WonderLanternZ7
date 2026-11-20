# Original-Z7 native information page

November20,2026. Independent original Nikon Z7 C3.80 work for the fifth custom
DISP choice. This binds original native contracts; the choice is not yet enabled
in the compiled custom-DISP profiles. Firmware/resources remain private.

`tools/audit_z7_information_native.py` passes47 checks:16 manager-selection cases
and10 original information-key admission cases, plus native registry, callback
registration, getter and entry checks. The exact original stock MAIN is required.

## Original bindings

| Role | Original-Z7 binding |
| --- | --- |
| Native application index | 13 |
| Application registry | A20207BC; entry13 points to A182D16C |
| Information descriptor getter | 102FD528 |
| Information key slot/value | A182D180 / 102FD647 |
| Information update slot/value | A182D188 / 102FDA09 |
| Current application byte | A1829AF4 |
| Separate information snapshot | A20210C0 |
| Information DISP state | snapshot byte2D, low6 bits |
| Parent registration | 10376440 writes parent callback and application index |
| Parent request dispatch | 103764B8 |

The original registry-construction prefix1030CF74 executes up to1030D00A before
registration/initialization. Entry15 instead points to A182CF00; it is a distinct
application. A numeric application identity from the pinned Z7II is not reused.

The original shooting DISP cycle1037061C advances native page3 to4, stores through
103673DE, and requests command4/payload108000 through the original shooting
descriptor getter1030D50C and helper103EB7C4. Return value2 signals the native
app-transition path. The original manager1030D1AA selection executes through
1030D33E, before final app work/initialization. Request108000 selects application13
only for photo LCD; movie/EVF cases select0. Request100000 returns to application0.

The native entry cycle does not validate a failed property write before issuing
its transition request. The audit retains that behavior: snapshot page4 can
coexist with unchanged property3 under a supplied setter failure. A custom
implementation needs explicit property/snapshot verification and conditional
rollback rather than treating a request or return2 as completed initialization.

## Original information-key contract

The original key handler102FD646 takes DISP key29. It retains its first, second
and final native filters, primary/secondary admission gates, fallback admission,
low6-bit snapshot states2/5 and both exclusion helpers. Ten cases execute this
handler with named service results and incoming snapshot state supplied. Blocked
cases issue no return request or page-property store; snapshots remain read-only.

For the admitted ordinary-LCD path it clears native view state, stores property
2F15=0 and requests command4/payload100000 through the information descriptor.
The audit supplies drawing/refresh and parent-request services, so it does not
establish native app initialization, a rendered information page or return pixels.

## Implementation work still required

Current custom profiles reject configurations containing native-information bit16
because ownership/routing is not installed. Remove that rejection only as part of
the complete five-choice implementation. Preserve actual native DISP admission
on both sides; do not replace it with the model's next-index calculation. Preserve
native keys/events, failure cleanup, settings reselection and output/movie gates.

Entry/return must release custom masks/base/overlays, perform the actual app
transition and reacquire the selected preset on native shooting return. Keep the
user's original saved native page across the owned information round trip; an
intermediate native return to0 must not replace that saved value. Master OFF and
foreign property changes still require conditional ownership-aware restoration.
Information only, disabled-current choice, master OFF, native MENU return and output changes
need compiled and live validation. Register guarded callbacks only after all
initializer failures are excluded, or extend the host API with owned native
information admission/update bridges. No information callback is installed yet.

## Live native control and visual limit

The inactive focal profile on host07/current emulator passes21 native routing
checks across four frames: baseline pages0/3 are selected through the original
setter, actual DISP enters application13/native page4, and DISP returns to
application0/page0. The original information key/update callbacks and all61 HUD
masks remain unchanged, and custom base/focal objects remain inactive. All four
PNG fingerprints and manager/page/property sequences were independently checked.
Return pixels differ only inside the native ISO region; full RGB identity was
not an acceptance gate for this routing control.

Inspection of the actual native information panel shows vertical mirroring in
the emulator. That observation blocks visual acceptance; its cause is unproven.
Do not fix it by flipping evidence images or inserting an application-specific
scanout rule. Derive the relevant native display/GPU orientation command and
validate the model against it. The live control does not implement custom DISP.

An owned bridge at native admitted-DISP point102FD7DA and a guarded pre-update
wrapper on initializerA182D188 are implementation leads. Original key/event slots
can remain unchanged. An additive API40 can preserve the current API32 prefix and
state256 layout. These bridges are not implemented yet; register/flag preservation,
original delegation, failure cleanup, reentry and native return need verification.

Source evidence: `evidence/20261120-information-native.json`. These scoped native
contracts do not grant installation or physical-camera recovery clearance.
