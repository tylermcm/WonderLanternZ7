# Original-Z7 display settings model

Independent MIT work for original Z7 C3.80. Page/component concepts follow the
pinned JKWTCN MIT custom-DISP feature; no Z7II addresses, configuration records,
glyphs or implementation bytes are embedded. This is a model and serializer,
not a native menu, card reader/writer or completed custom-page renderer.

`plugins/display_settings.c` supplies four configurable presets and an independent
native information-page enable bit. The enabled-page set must contain at least
one of five pages even while the master switch is off. Cycling skips disabled
pages, wraps, and permits the information page to be the only enabled page.
Preset reset restores that preset's component/information selections while
preserving page enables, master and battery settings. Global battery display
and custom-page master are separate flags; both default off.

| Preset | Components | Information groups |
| --- | --- | --- |
| Standard | Grid | Ordinary groups, excluding independently selected focal length |
| Minimal | None | Shutter, aperture, ISO |
| Composition | Grid, horizon | None |
| Exposure | Histogram, photo highlights | Ordinary groups, excluding focal length |

Eight independent information bits represent shutter, aperture, ISO, shooting
mode, release mode, focus, other status and focal length. Four component bits
represent grid, histogram, horizon and photo highlights. These preferences do
not establish those features' original-Z7 native bindings or render eligibility.
In particular, the new model does not enable a globally disabled grid/highlight
feature or claim that warning/AF controls have been identified.

## Independent 64-byte format

All words are little endian. Length must be exactly64 bytes. This is original-Z7
`Z7C1` version1, not a Z7II `Z72APP.CFG` record; no migration from that format is
attempted. No filename/card persistence is installed yet.

| Offset | Words | Meaning |
| --- | --- | --- |
| 0 | 1 | Magic bytes `Z7C1` |
| 4 | 1 | Version1 |
| 8 | 1 | Exact target `0x03800007` |
| 12 | 1 | IEEE CRC32 over all64 bytes with this word zero |
| 16 | 1 | Flags: custom-page master bit0, battery bit1 |
| 20 | 1 | Enabled pages bits0..4; at least one set |
| 24 | 4 | Per-preset component masks; only low4 bits |
| 40 | 4 | Per-preset information masks; only low8 bits |
| 56 | 2 | Reserved, zero |

Unknown versions, targets, flag bits, component/information bits, nonzero reserved
words, an empty page set, wrong length or damaged CRC are rejected before output
changes. Encode validates the complete model and stages all64 bytes before
writing. Decode stages the complete validated model before publication. Overlap
between model and wire buffers is supported; callers still own their actual
buffer allocation/capacity and model alignment. CRC detects corruption and is
not authentication. A native module is trusted executable code.

## Compiled validation

Private settings-probe02 is1,344 bytes, image1,280, BSS172, SHA
`a8b278b4614741a10a5b90c6614edf93f3436469c8929f768e510d7daa4355f0`.
It is a standalone SD-loaded C diagnostic with no display callback registration.
The compiled ARM model passes1,262 instruction checks against an independent
Python wire-format reference. Coverage includes512 single-bit corruptions,
sealed invalid fields, exact lengths,64 generated valid records, all31 enabled
page sets and five starting pages, last-page protection, isolated settings/reset,
unaligned byte buffers, overlapping model/wire storage, canaries and null pointers.
The module/host loader executes; file/kernel/heap services are supplied by the
existing instruction fixture. No native menu or card I/O is exercised.

```powershell
.venv\Scripts\python.exe tools/build_z7_display_module.py --variant settings-probe --output .private/builds/settings-new
.venv\Scripts\python.exe tools/audit_z7_display_settings.py --build .private/builds/20261119-display-host-02 --module .private/builds/settings-new --output .private/evidence/settings-new.json
```

Next: bind settings to owned native English controls, connect per-page renderer
policies while retaining warnings/AF/output admission, then implement independently
validated configuration loading/saving and lifecycle. The existing grid, battery
and clean-page profiles have not been switched to this model yet. Firmware,
modules and configuration bytes remain private; camera installation remains
outside this software validation.

## Native settings-menu prototype

Optional `--variant settings-menu-probe` now combines the existing display
profile with an owned native page-zero object at `0xA1833548`. The original
page getter resolves that slot. Preparation rejects any occupied page-zero
object, validates the original page42 layout and builds owned metadata,
callbacks, seven controls, geometry and event maps. Publication follows successful
component registration with the page tag stored last. The ordinary combined
grid/battery package still rebuilds byte-identically.

The root contains custom-page master, four presets, independent information-page
enable and battery setting. Preset subviews expose page enable, information,
four components and reset. Information is split into six groups plus a further
view for Other/Focal. Virtual subviews retain one native object; native Back
returns through the virtual parents and then the original native page history.
Control IDs7B10..7B16 are absent from the3,893 IDs found in the stock menu table.
Dynamic slots230..244 are borrowed only while empty or still holding this
prototype's exact prior strings/font. Detached callbacks check page identity,
metadata and callback-table ownership before changing model state.

Private candidate09 is9,348 bytes, image9,088, BSS3,160,49 relocations, SHA
`31e94a9c59853f6e412c77aba9330d85af0bc23cf848735a796af1823adb1283`.
Twenty-eight compiled instruction cases pass, including native page lookup,
model edits/reset/last-page protection, foreign labels, stale callbacks and
failed initialization. Native label/focus/header/queue services are supplied
in those policy cases; six additional cases execute the original text setter
to verify its font-kind restrictions and the supported bridge through kind0.

Assisted-QEMU live09 passes15 checks across seven frames using native direction
keys for master/preset/component/information/global edits and Back navigation.
The final model is flags3, enabled-pages31, Standard grid off and shutter group
off, with other preset defaults retained. All seven frames were inspected.
Titles, information labels and final ON/OFF states now render correctly. Some
intermediate root captures omit submenu `--` indicators until a later repaint;
font/present timing remains under investigation. This is not complete visual
validation of every preset, subview or lifecycle.

Earlier failures remain private: live01 assumed event callbacks receive the
page inR0, but the original router's BLX does not promise that argument. Explicit
event adapters now supply the owned page address. Live02 changed the current
Back event's destination while that event was executing, causing an extra native
exit; Back maps now stay neutral and root exit invokes native history explicitly.
Later green model checks still produced stale text. Native component painting
after edits consumes the dirty objects. Header ID203 comes from the original
layout/observed native object, rather than a foreign menu's header ID. Original
setter104BCBDA rejects direct font-kind1->2; a native1->0->2 transition fixes the
resource-text title. Binding runs after header construction on the native GUI
paint path. No host pixel buffer writes are used.

The menu is opened by an explicitly supplied native diagnostic call, not by a
normal camera menu entry. Its edits currently change only the settings model;
they do not enable the actual renderer or card persistence. Next work must add
the user-facing entry, complete rendering/setting bindings, investigate remaining
indicator repaint timing and cover MENU/playback/GUI rebuild/re-entry/foreign
ownership. The current optional profile is not installation-ready.

```powershell
.venv\Scripts\python.exe tools/build_z7_display_module.py --variant settings-menu-probe --output .private/builds/settings-menu-new
.venv\Scripts\python.exe tools/audit_z7_settings_menu.py --build .private/builds/20261119-display-host-02 --module .private/builds/settings-menu-new --output .private/evidence/settings-menu-new.json
.venv\Scripts\python.exe tools/probe_z7_display_module.py --build .private/builds/20261119-display-host-02 --module .private/builds/settings-menu-new --view settings-menu --output .private/evidence/settings-menu-live-new
```

## Native menu entry and battery binding

The optional `--variant display-settings` profile adds a seventh **Display
settings** row to Custom Settings d9, Framing grid display. It retains the six
grid choices and their stored values. The new row opens the owned settings page
through the original native page API; Back returns to the grid page. Off now
uses an owned event map and a wrapper around the original Off callback, since
the host permits its native-map exemption only on the final row. Ordinary
combined builds remain byte-identical; this profile does not change the host.

Private entry01 (SHA
`567528756b145881a0d3fb05edcaf2673dda0f032368e0734d0d73b35d65b825`)
passes20 assisted-QEMU native-key checks/8frames from native menu tabs through
d9 into settings and back. Entry/root/back frames were inspected. A separate
19-check/7frame native-key run covers all six grid selections with the seventh
row present. These results apply to entry01, before the battery binding below.

Entry02 is9,612 bytes, image9,344 and BSS3,760, SHA
`9a086f58748b34beaa9e45c823ad585ef45983b64ab756c4566115592a2a46e9`.
It starts the actual battery renderer OFF to match the model and publishes its
enabled state after native settings actions. Forty-six compiled menu checks
pass; another38 automatic-battery checks enable it through the compiled settings
callback with supplied GUI queue boundaries. This verifies the actual included
renderer, not just the model flag. The remaining preset/master settings still
edit the model only, and configuration persistence is not connected.

The first entry02 native battery integration run is retained as a failure.
Native menu keys enable the actual percentage in shooting and disable the owned
overlay, but the stock battery ROI does not match the initial baseline after
MENU return: the native icon is absent. All three shooting frames were inspected.
The emulator supplies bar/icon visibility requests, never a percentage or the
setting word. The longer integration02 adds a disabled-only native-menu control
round trip and native object diagnostics. It passes25 checks/6frames: the
disabled control preserves the stock icon, native keys enable the actual
renderer, and disable restores the complete RGB frame byte-identically. Its
virtual native battery sample is0%; this is not physical telemetry. All frames
were inspected or matched byte-identically to the inspected restored frame.

This second run does not resolve the first run's restoration failure: no
production code changed, and the preceding disabled control changes the boot/
menu sequence. Visual review also catches stale battery status text: the ON
capture still reads OFF and the OFF capture reads ON, despite the correct
renderer flag and shooting behavior. This extends the earlier indicator timing
gap to actual status values. Reproduce the immediate-after-boot restoration
failure and correct native value repaint/cache timing before treating this
profile as complete. Green state checks do not establish a correct menu image.
This supersedes the earlier prototype's model-only battery limitation; it does
not complete custom DISP, every menu indicator, lifecycle or physical telemetry.

```powershell
.venv\Scripts\python.exe tools/build_z7_display_module.py --variant display-settings --output .private/builds/display-settings-new
.venv\Scripts\python.exe tools/audit_z7_settings_menu.py --build .private/builds/20261119-display-host-02 --module .private/builds/display-settings-new --output .private/evidence/display-settings-new.json
.venv\Scripts\python.exe tools/probe_z7_display_module.py --build .private/builds/20261119-display-host-02 --module .private/builds/display-settings-new --view settings-entry --output .private/evidence/display-settings-entry-new
.venv\Scripts\python.exe tools/probe_z7_display_module.py --build .private/builds/20261119-display-host-02 --module .private/builds/display-settings-new --view settings-battery --battery-icon-fixture --output .private/evidence/display-settings-battery-new
```

## Immediate native text and virtual-view focus

Entry06 is9,804 bytes, image9,536, BSS3,760, SHA
`3ae795ed00a9ae165852ddc5d2a6d34f1ab830a9350047552aaa28d6f850298a`.
The builder reproduces it byte-identically.51 compiled menu checks and38
automatic-battery policy checks pass for this exact module.

The stale ON/OFF text came from refreshing the native display before painting
the changed component. The helper now paints first and refreshes second. The
original103FAC5A calls103FA770 synchronously as a refresh predicate; earlier
descriptions of it as a queued callback were inaccurate. Deferring rebinding
to pre-paint alone did not fix the stale pixels; that private experiment remains.
The instruction audit checks component-paint/refresh ordering explicitly.

Virtual-view focus also needs three distinct native changes.10402BC2 changes
row indices but neither the text palettes nor the compound selected-background
flag. The prototype now uses original unfocus/highlight routines around the
position change and original103FB30A setters to clear/select the old/new row
background. Palette-only entry05 still displayed the old highlighted row and
failed the new rendered check. Original selection setters execute in the
instruction audit, including propagation of dirty state to the parent.

Entry06 native-menu live03 passes28 checks/11frames. Battery OFF/ON/OFF glyphs
change and restore immediately; both subviews highlight their actual native
selected row, and all five unselected ON fields in the information view render
with identical pixels. Frames and native object/label records are retained.
Selection backgrounds pulse between bright/dark gold, so the status regression
compares black glyph cores and retains RGB hashes rather than demanding an
unchanged selection background. Root/preset/information/Back navigation and
the original grid setting remain covered. This is not every preset or extra
information subview, every lifecycle or a custom-DISP renderer binding.

Shooting validation is separate. The probe restores the base fixture's native
5,000ms StartLV display wait; its earlier100ms shortcut could enter MENU before
the initial live-view draw settled. Early unmodeled-flash stops remain private;
no emulated flash response was invented. Entry05 integration06 reaches menu
enable/disable with correct status glyphs, but its initial baseline is native
adapter112B while its final icon is battery1120. Its failed ROI comparison
therefore does not establish a battery-restoration defect. The original entry02
failure lacks that diagnostic and remains unresolved. The current probe must
qualify the visible native battery glyph/layout/painter before accepting a
baseline, retain all bounded request attempts and require the restored glyph
to match before comparing pixels. A disabled-only control remains opt-in via
`--settings-battery-control`; it must not silently replace the original sequence.

Integration10 records battery1120 immediately after each native call and
adapter112B after the subsequent native drawing passes. All three attempts are
correctly rejected as unqualified baselines. Dispatch now uses the same paused
checkpoint as the supplied request, and each future run saves its exact probe
source and SHA. This removes a scheduler gap but does not suppress later native
updates or create persistent simulated battery telemetry.

Integration11 explicitly requests the disabled-menu control before qualifying
the baseline, but exits on an unmodeled flash write during the first MENU. Its
startup reports132 RAW batches and only1 ISP batch despite the5,000ms wait.
Therefore elapsed settling time alone is not a reliable readiness gate, and no
new shooting-restoration success is claimed for entry06. Retain all failures;
next shooting work must inspect actual pipeline readiness/native update sources,
without inventing flash responses or treating an adapter frame as a battery
baseline. The independent native-menu28 checks and compiled51+38 checks remain
successful. No guest remains from these completed runs.

## Readout filtering through the native update pipeline

The optional `display-readouts-probe` now binds the first three information
settings to independently identified original-Z7 shutter, aperture and ISO
widgets (10,11,15). It is an independent diagnostic, not the completed custom
DISP implementation. Preset selection is still a supplied diagnostic word;
the master setting uses the compiled validated model setter. Normal
`display-settings` still builds byte-identically to entry06 (SHA3ae795ed...).

The original mask interpreter102F2690 was executed over30,240 cases, with7
additional invariants. Original-Z7 photo pages0/3 use bits0/3, or8/11 in the
alternate operation state, so suppression uses0x909. Copying the Z7II0x99 mask
would also edit original-Z7 movie bits. Only LCD words in the first two banks
are changed; alternate outputs, movie permissions, the third bank and other
widgets retain their native values. ON preserves the native baseline rather
than synthesizing permission. Foreign bindings/writes cause conditional owned
restoration and a latch until the master is turned off; abandoned owned words
remain pending until their original descriptor returns.

Independent original updater/formatter execution identifies the three groups
and shared shutter warning formats in8 cases. Every nonzero native format is
left fully native. This covers already-present special states, not warning
transitions arriving in the same update: transition timing and actual warning
pixels remain unverified. Broader output/menu/reentry/AF lifetimes remain open.

Changing masks during paint was too late. A global invalidation there lost
unrelated HUD content and failed readout restoration. Targeted permission/update
dispatch plus a blanket HUD dirty request produced stale pixels and unrelated
OK/Exit footer content. Those failed private runs are retained. The current
policy calls neither direct dispatch nor drawing helpers. It changes masks on
the native widget-computation path before103690C0, then calls the independently
audited original snapshot invalidator10367C5A. The subsequent original pipeline
computes permissions, layout, strings and pixels normally.

`sdk/update.h` adds an optional24-byte host API tail while preserving the20-byte
base and32-byte display-hook layout. Registration is init-only, accepts owned
Thumb image code, rejects duplicates and publishes only after initializer
success. Failed init clears the callback before freeing memory. Two reserved
state words are used without moving existing fields or guards. The displaced
1036B10C prefix preserves native register inputs, stack and flags; a differential
check caught and corrected an r12 clobber in the first long-call bridge.
Older20-byte hosts reject this diagnostic before native stores and free its image.

Current reproducible private host04 MAIN SHA
`f5b991a726a2f3e732b98488b66db14996a84fd460dc245c1dbf3c696fbd1858`
is33,056,916 bytes with3,129 host bytes. Readouts05 module SHA
`0aa8f050419560d030e907fc1dc14aa72893b4ccda8a2e28e6a9aa9935aa6846`
is10,828 bytes, image10,560, BSS3,832. Instruction audits pass120 readout
cases,24 update-registration/prefix cases,99 loader cases and316 existing
display-host cases (2,114 native indexed scalar reads per image). Root39 tests
pass without skips. Incoming control snapshots and GUI/loader boundaries are
supplied in the instruction fixtures; they do not establish physical operation.

Assisted QEMU live04 on the earlier host03 passes13 checks/3frames: Composition
suppresses ordinary readouts, all pixels outside the native bottom strip
(116,420)-(590,480) remain identical, and disable restores every RGB pixel and
all mask words. The fixture explicitly calls the original standard-page setter,
selects diagnostic preset2 and invokes the compiled model setter; it supplies no
mask/visibility stores. It uses the modeled read-only module file and existing
assisted sensor/ISP startup. These are not physical card or DISP-key results.
The corrected host04 repeat live05 also passes13 checks/3frames with all three
ordinary groups qualified and exact complete RGB restoration; its source-only
record is evidence/20261119-native-readout-update.json.

```powershell
.venv\Scripts\python.exe tools/build_z7_module_host.py --display-hooks --output .private/builds/update-host-new
.venv\Scripts\python.exe tools/build_z7_display_module.py --variant display-readouts-probe --output .private/builds/readouts-new
.venv\Scripts\python.exe tools/audit_z7_display_readouts.py --build .private/builds/update-host-new --module .private/builds/readouts-new --legacy-build .private/builds/20261119-display-host-02 --output .private/evidence/readouts-new.json
.venv\Scripts\python.exe tools/probe_z7_display_module.py --build .private/builds/update-host-new --module .private/builds/readouts-new --view readouts --output .private/evidence/readouts-live-new
```

No camera/card operation, installation clearance, staging, flash or push is
implied. The host remains one installed firmware component plus a resident
startup-loaded `Z7APP.BIN`; new hook requirements need a compatible host.

## Native admitted-DISP preset prototype and warning order

The optional `display-disp-probe` adds native input routing for the four logical
presets and their three mapped readout groups. It does not yet bind component
selection, native base-page selection or the separate information app. A model
that enables the unbound information choice delegates the whole diagnostic to
native behavior instead of silently skipping that enabled choice. These remain
implementation requirements, not completed features.

The original shooting-key callback remains1030DA57 in its original RAM slot.
A guarded host bridge at1037061C runs only when native shooting DISP admission
reaches the page-cycle call. A complete Thumb BL scan finds one direct caller,
10367468, after the original outer filters and inner exclusions; no literal
function-pointer references to this cycle entry were found in the stock MAIN.
The callback returns0 to delegate,100hex for a consumed normal update, or2 for
an already-performed native app transition. Other return values delegate. The
native caller still issues its own GUI update request after a consumed cycle.

`sdk/disp.h` is an additive28-byte API, embedding the unchanged24-byte update
extension and20-byte base. Its init-only owned-code registration stages one
callback, rejects duplicates and clears it before freeing a failed initializer.
Existing fields,32-byte display hooks and256-byte host state retain offsets.
The previous settings and readout packages rebuild byte-identically. The newer
preset package rejects the older24-byte host before native stores.

Current preset02 package SHA
`f57a1b106b201468dda5178bc4d94f5c545dc79dafd12f892ab7350b50a1bbff`
is10,892bytes/image10,624/BSS3,840. Reproducible host06 MAIN SHA
`28633855e1daa1ffcf1f2213dfa2b0a41395f65c6a60af7b44a8f02442631958`
is33,057,312bytes with3,301 host bytes. Native instruction checks cover admitted
cycling, disabled-choice skipping, native fallback, original admission/filter
blocks, output/movie/menu/configuration exclusions, registration failures and
differential native register/stack/flag preservation on delegated cycles.

The warning audit now executes original selector10369192 and native Card/Err/
Full predicates with supplied status properties/error-list snapshots. Sixteen
appearance, clearance and priority cases pass. The original caller instructions
run the selector before the module callback, so the policy sees the current
warning format in that iteration. Native ISO preparation10369C06 and its
computation execute in the latest audit. Six other preparation-helper results,
unrelated warning predicates and three context services remain supplied. This
is mask/control-order evidence; actual warning pixels and real producers remain
unverified.

Full QEMU preset runs on host05 exposed an unmatched native visibility phase. Presets1/2/3
advance through injected native DISP events and hide the readout strip correctly,
but exact restoration fails at the native ISO AUTO label. The difference is
2,206pixels in(626,618)-(680,672) at1024x682 in the first run. A disabled-only
native cycle in the second run also changes the ISO label relative to startup;
its qualified baseline then loses that label on the custom return. The three
native ISO control records distinguish this from an unrelated HUD change.
Do not treat either run as a completed rendering-cycle result.

The hook-order review also found that1036B10C runs after native control
preparation1036AE44.
Host06 moves the callback to the start of1036AE44, after warning selection and
before both preparation and layout. The displaced original preparation calls
use local literal thunks to preserve native input registers. Its24-case prefix/
registration audit passes; the exact-pixel repeat is separate and its result
must be read in the latest source evidence. Historical readout-only full-frame
results above retain their original scope and do not prove this full DISP cycle.

```powershell
.venv\Scripts\python.exe tools/build_z7_display_module.py --variant display-disp-probe --output .private/builds/disp-presets-new
.venv\Scripts\python.exe tools/audit_z7_disp_cycle.py --build .private/builds/20261119-display-host-06 --module .private/builds/disp-presets-new --diagnostics .private/builds/20261119-combined-regression-07/probes --legacy-build .private/builds/20261119-display-host-04 --output .private/evidence/disp-cycle-new.json
.venv\Scripts\python.exe tools/probe_z7_display_module.py --build .private/builds/20261119-display-host-06 --module .private/builds/disp-presets-new --view disp-presets --output .private/evidence/disp-presets-live-new
```

Native ISO visibility is now independently audited: original102F2586 selects
snapshot+4 for ISO mode+250==2 (also the default), +3C for mode1 and +24C for
mode3. Original102F2656 applies that selected value to each ISO subcontrol.
All96 cases pass with supplied binary source fields and original selector/
visibility instructions executing. In both instrumented QEMU failures, the
baseline had+4==1 and the return frame+4==0, with ISO controls1/2 following that
phase exactly. The2,206pixel difference is confined to the ISO AUTO label.
It must not be classified as a proven restoration defect or silently ignored.

The current probe waits for the same native phase and ISO visibility as its
qualified baseline, then captures the paused frame without another settling
advance. It retains every sampled phase/visibility value, changes no native
visibility/phase word and still requires exact full RGB equality. The older
failed runs stay intact. That live04 run has now terminated: eleven checks pass,
then all24 observations retain native source0 instead of baseline1. Waiting
does not establish that this state is periodic or will return to1.

The original snapshot-copy instructions103681BA..103681D0 copy producer packet
A201F260+44/+48/+4C to snapshot+3C/+4/+24C respectively. Eight binary-input
cases execute this block and verify neighboring snapshot bytes remain unchanged.
The producer packet is supplied; the real producer remains unverified. Combined
with8 formatter and96 visibility cases, identity audit03 passes112 cases.

Live07 then showed why the control record cannot qualify a completed frame:
preset3 reports source0/hidden ISO, but its captured RGB exactly matches the
native reference with the ISO label present. Both preset1 and preset3 match that
complete disabled native frame. Source/control sampling is ahead of painting.
A reliable native paint-completion boundary remains unverified.

The revised probe compares each restored frame to the finite set of captured
disabled native standard-page images. It requires exact full RGB membership,
without pixel exceptions or state stores, and records source/control matches
separately as diagnostics. It fails immediately on an unmatched image and does
not wait for a state transition. Live08 is the pending repeat; host/module
binaries remain unchanged. This validates captured-image equivalence only,
not coherent native update/paint timing or warning-transition pixels.

## Active preset coherence and measured native readiness

The DISP diagnostic now resolves an active preset disabled through the model
setters on the next eligible shooting update. It selects the next enabled preset
without changing the original native page/property or counting a DISP press.
Menu, movie, alternate output, master-off and unbound information-app states
defer this change until eligible return. Sixty enabled-set/current-preset
combinations and ten defer/return cases extend the cycle audit to137 checks.
These are compiled-ARM checks with supplied GUI/kernel boundaries; an actual
native menu roundtrip exercising this reselection is still open.

New disp03 package is10,956bytes/image10,688/BSS3,844, SHA
71c0780063ebe2466f8e14b4f1860657b0eee22dddf227342276a60e7f7a414b.
Host06 and its28-byte API are unchanged. The existing readout-only package
rebuilds byte-identically. The new package passes119 readout checks, and all39
root tests pass without skips.

A dedicated disp-admission observation runs original gates during native AO
injection and task delays, supplying no gate-return values. Its first run passes
six checks/two frames, with22 trace events: original key29 passes all four outer
filters, reaches the inner handler and original cycle entry, and changes native
page0 to1. The100ms startup fixture reports27RAW/21ISP initially; after observation
it has121RAW/115ISP and processed scanout. It does not reproduce the earlier
5000ms-startup input failure. The after frame was visually inspected.

The rendering probe now requires observed RAW, ISP and LCD-counter progress,
processed-buffer scanout and native ready/stage state before exercising custom
DISP. Up to six named1000ms native task delays are recorded with full health
snapshots. No readiness flags are written and no device completion responses are
invented. This is an emulator test precondition, not physical readiness proof.
The first full run using that gate (live09) passes21 checks/11frames. Its first
readiness sample advances22RAW batches,23ISP batches and30LCD frames. Actual
native keys select all four logical presets. Composition changes the readout
strip while every protected pixel remains identical. Presets1/3/0 and master-off
match complete captured disabled native frames exactly; disabled mode resumes
the original page cycle. Composition/restored frames were visually inspected.
This remains a three-readout logical-preset diagnostic: component/base-page and
information-app bindings, remaining groups, persistence, warning pixels and
broader lifecycle are unfinished. Captured native equivalence does not prove
coherent update-to-paint timing. No camera/card operations occurred.
