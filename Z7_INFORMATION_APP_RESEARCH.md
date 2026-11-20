# Original-Z7 native information page

November20,2026. Independent original Nikon Z7 C3.80 work for the fifth custom
DISP choice. The API40 `display-information-probe` now composes the full
focal/Other/histogram stack with the native information app. Earlier API32
profiles retain their bit16 rejection. Firmware/resources remain private.

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

## Original implementation plan (historical)

The earlier API32 custom profiles reject native-information bit16. The new
API40 profile installs ownership/routing separately; this rejection is retained
in older profiles. The original integration requirements follow. Preserve actual native DISP admission
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
state256 layout. This was the original proposal; the implemented bridges and
register/flag, delegation, cleanup and reentry verification are recorded below.

Source evidence: `evidence/20261120-information-native.json`. These scoped native
contracts do not grant installation or physical-camera recovery clearance.

## Implemented additive host interface

`sdk/information.h` now exposes API40, preserving the complete API32 GUI prefix.
An init-only owned callback runs after original information DISP admission;
return0 delegates native exit, 0x100 consumes the key, and2 is reserved for a
transition already performed. A second owned callback runs before native Info
update. The wrapper skips the stale original updater when application13 changed.
This is not a completed-paint fence. Native key/event pointers remain unchanged.

The host instruction audit passes116 checks, including rejected registration,
failed initialization cleanup, nested calls, context conflicts and exact delegated
register/stack/LR/NZCVQ continuity. Native update is a supplied sink in that audit.
Separately, live compatibility passes21 checks/four frames with unchanged API32
focal module and no information callbacks. Actual native DISP entry and return
execute through the resident updater. All PNG hashes were independently checked;
information RGB exactly matches the previous API32-host control. Vertical mirrored
text remains unresolved and visual acceptance is false. Captured LCD format and
geometry flags remain identical across these states except buffer addresses.
See `evidence/20261120-information-host.json` for scoped regressions. Physical installation remains unverified; later combined-profile work is recorded below.

## Verified transition ledger

`plugins/information_transition.h` implements conditional entry/return ownership.
The caller must release custom component ownership before entry. The ledger
keeps the original user page separately from the native page at entry, verifies
page4 publication before requesting the original native application transition,
and observes asynchronous app state. It records admitted native exit without
replacing the exit handler. Only observed native shooting return/page0 permits
restoration of the original saved page. Failed native setter publication/rollback
retains conditional recovery; different foreign page values remain untouched.
No helper assigns the native application byte or registry.

The reproducible standalone diagnostic passes160 ARM checks, including a saved
page3 with custom applied page0 and native return0. Original setter/getter,
request helper and native information DISP exit execute. Property services,
parent callback and application initialization remain supplied. Actual component
release is an explicit caller precondition, not established by this test. Root55
regressions pass. See `evidence/20261120-information-transition.json`.
The helper is now used by the API40 combined profile below.

## Five-choice combined profile

`display-information-probe` includes the complete focal/Other/histogram stack,
with API40 information callbacks and an explicit transition ledger. An admitted
shooting DISP key selects the next enabled preset or stages information entry.
Custom masks/base and owned painters retire first. The after-GUI callback
rechecks native eligibility before requesting the original native information
transition. Only observation of native app13 commits logical choice4.

An admitted information DISP key either keeps an information-only configuration
or delegates the original native exit to the selected preset. Settings-driven
master-off/disabled-current return uses independently bound ordinary native LCD
exit primitives, verifies page-property publication and waits for native manager
return. No synthetic key or application/registry/snapshot assignment performs a
transition. The original user page remains separate from intermediate return0.
Failure rollback and foreign-state conflicts retain conditional ownership; a
failed entry does not issue another request on every GUI frame.

Current reproducible candidate04 is20748bytes/image20480/BSS5508/API40, SHA
`d49811875af0304f5c18a2f6b182fb2bf79419fe43b7ad6d316ecefabd15ffcd`.
The original API32 focal profile remains byte-identical. Native information
orientation remains unresolved; routing success does not establish visual
acceptance or camera installation/recovery. Scoped evidence accompanies the
checkpoint; highlights, portrait, persistence and broader lifecycle remain open.

Candidate04 validation:54 compiled routing checks,182 transition checks,45 focal
overlay checks and55 root regressions pass. Assisted QEMU passes43 checks across
15 frames. Actual native entry/return, information-only DISP/master-off and saved
page3/all61-mask restoration execute. A later supplied lens1/245 phase verifies
focal painter retirement and text reappearance. All15 PNG hashes and frozen helper
source were independently verified. Fixed focal crop changes against its disabled
control, returns exactly, and master-off restores the original native background
in that window. Raw frames were inspected. No whole-RGB or physical telemetry
claim is made. See `evidence/20261120-display-information.json`. Native information
text remains mirrored; full visual acceptance and broader lifecycle remain open.

## Native MENU lifecycle and graphics observation

On the unchanged full five-choice module, assisted QEMU passes42 lifecycle checks
across10 frames. Native and owned information stay on app13/page4 beneath MENU;
master-off while MENU is open waits for close, then restores native user page3
and all61 masks. Repeated inactive native MENU controls independently reproduce
the remembered focus difference (first page1+19, then page1 alone). The owned MENU
frame exactly matches the second inactive native frame in complete RGB. PNG hashes
and frozen helpers were verified. This does not cover every output/lifecycle path.

A new default-off GPU draw observer captures private registers, path data and
bounded texture bytes only while an optional host gate is present (512 draws,
1MiB per file).330 GPU checks,23 QEMU transport tests,55 root tests and a firmware-free
QMP smoke pass on rebuilt QEMUf76609ae...9b45c98. No rasterization rule changed.
The Info entry and settled-refresh controls pass22/4 and36/9 checks/frames. Traces
are bounded partial histories. Upright A8 glyph samples and a settled RGBA copy
B045F200→B090F200 followed by LCD conversion are observed; both copies submit
negative-Y texture matrices. Their actual native orientation contract remains
unproven. No application-specific flip or edited screenshot is accepted as a fix.
See `evidence/20261120-information-menu-graphics.json`. Firmware, textures and
camera/emulator images remain private. Native information mirroring still blocks
visual acceptance; broader original software scope remains open.
