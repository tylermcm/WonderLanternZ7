# Original-Z7 display settings model

**Current status — November 23, 2026:** selected LCD checkpoints now have
[owner hardware observations and saved-file checks](../DEVELOPMENT_UPDATE_2026-11-23.md).
Photo/video proof is pending. The earlier milestones and broader experimental
profiles below are historical or separate; they do not expand that hardware scope.

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

## Five-choice native application diagnostic

The API40 `display-information-probe` now combines all four configurable presets
with native information application13, including the focal/Other/histogram stack.
Entry waits for custom mask/base release and owned painter retirement; return
preserves the original user native page across intermediate native page0.
Information-only, master-off and disabled-current reselection are implemented.
Older API32 profiles keep their bit16 rejection and remain independently usable.
See [the information-app record](../Z7_INFORMATION_APP_RESEARCH.md#five-choice-combined-profile)
for exact candidate and scoped evidence. Native information text remains vertically
mirrored in the emulator, so routing tests do not establish visual acceptance.
No card persistence or physical installation/recovery clearance is added.

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

## Two-slot storage transaction

November20,2026: `plugins/settings_storage.c` now implements the independent
storage policy behind a caller-supplied transport. It does not call a native
camera filesystem or register the resident-worker callback yet. The caller must
serialize slot operations and supply a coherent menu-settings snapshot. Native
file/cache bindings, startup loading and shared-state coordination remain open.

Two slots each hold an80-byte little-endian `Z7J1` record. Offsets0/4 are magic
`Z7J1` and version1; offset8 is a wrapping32-bit generation; offset12 is IEEE
CRC32 of all80 bytes with that word zero. Offset16 contains the EXACT unchanged
64-byte `Z7C1` payload above, including its own target and checksum. The outer
checksum protects the generation as well as the settings. This is not a Z7II
record or a change to the standalone64-byte serializer. Filenames are not bound.

Loading checks both records and chooses the newer valid generation by modular
serial order. Identical tied records are accepted; conflicting tied records or
an exact half-range generation difference are ambiguous and block publication
and saves. Invalid checksums/fields and confirmed bad lengths are unusable slots.
Two confirmed absent/unusable slots yield defaults without writing. A read error
is distinct from confirmed absence: a readable valid peer can still load, but
any slot I/O error blocks saving. Without a valid peer, I/O errors preserve the
caller's current output rather than publishing defaults.

Saving stages the64-byte settings snapshot BEFORE transport callbacks, rescans
both slots and skips an unchanged record. It writes only the other slot, then
reads the complete record back and checks byte identity before reporting saved.
The previous valid slot is never the write target. Failed writes, short writes,
close failures and failed verification leave the prior valid slot available
under the transport's one-slot ownership contract. A fully written record with
an uncertain close result may be selected at restart; the next save rescans and
recognizes it without rewriting. This provides a bounded recovery policy, not
physical power-loss durability: real filesystems/cards can fail beyond these
modeled slot operations. No rename/replace semantics are assumed by the policy.

Private `settings-storage02` builds reproducibly:2440bytes, image2368/BSS376,
SHA `2b6daaa17daf46fe1a3eb79e62fd631c8ae6be9f14f67f398c390611f7cc779a`.
Its ARM diagnostic passes2020 checks against independent Python bytes/CRC/serial
expectations. Coverage includes640 single-bit corruptions, resealed invalid
fields, record lengths, overlaps/null arguments, generation wrap/ambiguity,
all81 write cut points with either slot active and success/error returns,
partially replacing an older valid slot, read/verification failures, uncertain
commits, unknown I/O statuses, write-free unchanged settings and a snapshot
changed by a supplied transport callback. Loader/kernel/filesystem services are
supplied to load this diagnostic; journal transport itself is in-memory.
These are not real-card or menu/worker integration checks. A header-comment-only
rebuild03 has the EXACT same package bytes and verifies all8 current source-input
hashes; existing display/worker profiles were not changed.

```powershell
.venv\Scripts\python.exe tools/build_z7_display_module.py --variant settings-storage-probe --output .private/builds/settings-storage-new
.venv\Scripts\python.exe tools/audit_z7_settings_storage.py --build .private/builds/20261120-display-host-09 --module .private/builds/settings-storage-new --output .private/evidence/settings-storage-new.json
```

## Queued save-status presentation

The API44 persistent profile now publishes atomic save state and displays
Defaults, Saved, Unsaved, Saving, Save retry or Restart to save in its header.
A guarded wrapper around the original menu state1 callback delegates the native
event first, then refreshes only the owned focused settings page. Worker
notifications use the original event-flag service and mask0x2 input-queue poll;
they do not inject keys, borrow timers, update labels or paint on the worker.
Foreign callback ownership rejects initialization before settings I/O.

The menu dispatcher audit passes15 checks and the full persistence/status audit
passes84; the extended routing audit passes54 on the same native bytes.
Live save-status05 passes39 checks across two fresh guests/16 PNGs:
an explicitly modeled create error preserves the old record and shows Save
retry, clearing it permits Saved, and restart restores settings without writes.
All three final menu comparisons match complete720x480 RGB across restart.
All16 PNG and four closed-journal hashes were independently verified. Status
publication and menu paint are asynchronous: every ready candidate is retained,
and the bounded capture waits for current title text as well as clean row nodes.
This does not establish a hardware presentation fence or SD durability.

Final private source build05 is byte-identical to tested04:
`719c1db3ca5cf1c78d82ebedcdbbb4cc7b67312b34b7982d11a718e4b39af85c`.
Root70 tests pass without skips. The previous live failures remain failures.
Source evidence: `evidence/20261120-menu-status-refresh.json`.

Startup-blocked live inspection now passes9 checks/4 native frames: clearing a
modeled startup read-open error does not reload late or overwrite the original
journals, and native menu edits stay temporary with Restart to save displayed.
Composition and Information longest titles are fully visible in inspected native
720x480 frames, with tight spacing before the back button. Header child203 paint
readiness is now checked alongside all14 row nodes. Root71 tests pass without
skips; source evidence is `evidence/20261120-save-startup-blocked.json`.

Uncertain-close status pixels and broader menu/lifecycle behavior remain open. The native information mirror,
physical card/cache/shutdown and installation/recovery assessments remain open.

## Native files and persistent full display profile

November20,2026: the optional `display-persistence-probe` now combines the FULL
focal/Other/histogram/information profile with startup loading and background
saves. It requires API44. The older API40 full profile and API32 focal profile
remain byte-identical when this option is disabled. This is software instruction
validation with supplied files, not a physical-card or flash-ready release.

`plugins/settings_files.c` owns only `A:\Z7CFG0.DAT` and `A:\Z7CFG1.DAT`.
Read-only open uses original1027BFA2 with flags0/mode0. Read1027C018 requests81
bytes to establish the exact80-byte record boundary; a successful short/long
read is a known unusable record, not confirmed absence. Only native status
`0x80000010` is classified as absence. Its meaning is bound to original FAT
root end/exhaustion and read-open propagation, with sector/path services
supplied. Other driver/card states remain a physical validation gap.

Create1027C0DA passes mode0; original1023F146 forces open flags0301. Executed
original open instructions select descriptor mode026 and truncate an existing
writable file, while read mode1 does not truncate. Write1027C048 requires all80
bytes. Both read and write close via original1027BFCC. Any nonzero close result
retains the descriptor and parks ALL adapter I/O for that boot. Initialization
cannot discard that unknown handle, including descriptor0. No raw-close retry
is used. The journal verifies read-back before reporting saved.

Owned192-byte,64-byte-aligned staging buffers contain every line touched by the
native helpers. Writes clean with101E9F38 before filesystem submission. Reads
invalidate with101E9F76 before and after submission. Each80/81-byte request
covers three64-byte lines in the instruction tests. This is an address/order
check; physical coherence and durable media flush are unverified. Native
1027BFEE is a64-bit seek interface, not a flush function.

The combined initializer checks API44 before menu preparation and registers all
callbacks before starting settings I/O. Loading runs on the existing loader task
while host readiness and native menu publication remain clear. No failing init
operation follows that I/O, so uncertain descriptor state remains resident.
Valid stored settings determine the initial model/battery flag. Confirmed missing
or invalid records use defaults without auto-writing. Failed/ambiguous startup
loading keeps volatile defaults and blocks saves for that boot; restart retries
loading. A worker never publishes a late replacement into active menu state.

Menu edits stage a complete model, then publish changed words atomically between
odd/even revisions. Menu navigation and rejected edits do not dirty settings.
The resident worker takes a bounded revision-checked atomic snapshot. It observes
an edit, waits two further quiet ticks, then attempts a save on the fourth tick.
Native delay units are not assumed to be milliseconds. Unchanged revisions do
not write. Failed saves retry after five worker ticks, except an uncertain close
parks the adapter. An edit arriving during I/O remains dirty after the older
snapshot is acknowledged, and a later cycle saves the newer edit.

Private files-probe01 is2764bytes, image2688/BSS156, API12, SHA
`0d724be9f907954787894a5148e04b4f7403327dd5127784b1b89c5ea7da422b`.
Its215 checks execute original directory/open/cache/wrapper instructions with
supplied dispatcher/sector/path services. Coverage includes both slots, native
mode/truncation, lengths, every short-write cut point, read/write/close failures,
retained descriptor0, cache line/order bounds and journal reload after a short file.

Persistent profile01 is22936bytes, image22656/BSS5584, API44, SHA
`6ba9f4cfa6c247d3b6d8ce5023084dc16b83e516712bec97ea81769823a85bb6`.
Forty-eight integration checks execute startup loading, actual native menu
adapters, publication, quiet ticks/retries and fresh-module reloads. Two supplied
task-preemption cases run the actual menu callback on a separate emulated stack,
then restore worker registers/stack/PC: one interrupts a snapshot before a
multi-field reset, another interrupts filesystem submission before a newer menu
edit. Complete snapshots and revision acknowledgements are verified. This is
not a complete native scheduler or physical timing proof. Another54 existing
five-choice routing checks pass on the persistent profile with separate settings
files supplied. Root55/no-skips pass. Current10/39 source-input hashes verified
for the files diagnostic/full profile, respectively.

Assisted-QEMU persistence live04 now passes22 checks across two fresh guests.
Native MENU edits are saved by the resident worker to two explicitly modeled
journal files, whose bytes seed the restart. Startup restores settings without
rewriting the files. Root, Standard and information menu comparisons match
complete720x480 RGB frames after all14 row paint flags clear and the native
highlight pulse phase matches. All15 PNGs and four closed-file hashes were
independently checked. Firmware/module/host/QEMU bytes stayed unchanged; the
harness now services file calls while the menu task runs freely. Earlier
native-delay waits starved queued repaint work; an experimental firmware rebind
change was rejected and reverted. See source evidence
`evidence/20261120-persistence-menu-restart.json` and root HANDOFF.md.

Basic unsaved/save-retry presentation is implemented and scoped above; broader
current-profile pixel/lifecycle validation and all blocked-state visuals remain open. No physical card,
shutdown flush or installation/recovery acceptance is established. The separate
native information mirroring gap, highlights/portrait and broader lifecycle/real
statistics work remain open. Firmware, modules and configuration bytes stay private.

```powershell
.venv\Scripts\python.exe tools/build_z7_display_module.py --variant display-persistence-probe --output .private/builds/display-persistence-new
.venv\Scripts\python.exe tools/audit_z7_display_persistence.py --build .private/builds/20261120-display-host-09 --module .private/builds/display-persistence-new --legacy-build .private/builds/20261120-display-host-08 --output .private/evidence/display-persistence-new.json
.venv\Scripts\python.exe tools/audit_z7_display_information.py --build .private/builds/20261120-display-host-09 --module .private/builds/display-persistence-new --persistence-transport --output .private/evidence/display-persistence-routing-new.json
```

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

## Native base-page ownership prototype

Optional `--variant display-base-probe` extends the admitted-DISP package with
native standard/horizon selection. Preset horizon OFF requests native page0;
ON requests page3. The independently derived original selector must identify
photo-LCD property2F15 before ownership is acquired. The saved property and
snapshot must agree. Calls use the original103673DE snapshot/property setter,
not raw snapshot stores or a borrowed Z7II callback.

Disable or context exit conditionally restores the saved native property only
if it still equals our applied value. An inactive output's property is restored
without changing the shared current-output snapshot. Foreign property/snapshot
changes suspend custom rendering until master-off; those foreign snapshot
values remain untouched. Setter failures roll back through the same native API,
retain conditional cleanup and retry failed restoration on later updates. A
failed acquisition cannot apply readout masks. Native invalidation follows an
accepted page change so preparation and layout use the new native page.

Current base02 package is11,660bytes/image11,392/BSS3,876, SHA
17448f7f58b0f3efcd19be59438a15a67b3c0a351bbaffa48f1921db7ca98dd7.
It requires the unchanged28-byte host06 API.68 compiled-ARM checks pass with
original selector/setter instructions executing and explicit property storage,
GUI and loader boundaries supplied. These cover all saved native pages, all16
component combinations, foreign changes, rollback/retry, other-output cleanup
and older24-byte-host rejection before native stores. Root39 tests pass without
skips. The accepted disp03 package rebuilds byte-identically.

The assisted QEMU native-key/full-RGB repeat passes22 checks/11frames. Its
readiness gate rejects an initial sample with22RAW/22ISP/0LCD progress and accepts
the following21RAW/21ISP/30LCD sample. Native keys select standard or horizon
according to each preset. Composition on native horizon page3 preserves all
pixels outside the readout strip relative to the disabled native horizon frame.
Return presets and master-off exactly match captured disabled native standard
frames. Master-off releases base ownership; subsequent DISP resumes the native
cycle. Horizon/composition and restored frames were visually inspected.
These are synthetic assisted-emulator pixels, not physical orientation/EVF,
warning-transition or coherent native update-to-paint boundary validation.
Grid, histogram and highlights switches remain unbound in this prototype;
information app, remaining groups, persistence and broader lifecycle remain.

Pinned reference research now includes the original grid/histogram glue and
implementation files listed by hash in evidence/20261119-native-base-pages.json.
The upstream custom histogram uses a guarded extra GUI pass with real statistics,
not merely native page masks. Original-Z7 statistics/getter and native-control
leads already exist, but the extra pass still needs independent derivation.
Grid suppression must use original-Z7 LCD descriptor count offsets10/22; upstream
uses different offsets. No foreign geometry offsets or histogram addresses may
be copied by analogy. Fetched upstream source remains private under MIT.

## Native LCD grid component binding

The base-page diagnostic now binds the grid component through the existing
scalar-value callback. Only native key102D reports Off during eligible owned
custom grid-Off state. Original1037723E then follows its unchanged availability
and exclusion gates and drives the native grid plane. Grid ON permits the saved
native selection. The component does not write the saved grid setting, geometry
or style tables. Menu, movie, other output, invalid model, unbound information
and foreign native ownership retain native behavior. Foreign property ownership
is validated on GUI updates; scalar callbacks use RAM-only context and never
re-enter property services while inside a native property read.

The base policy tracks the grid component separately from native page selection.
Same-page edits and master-off invalidate native layout, so an already visible
or hidden grid is recomputed by native code. No scratch geometry is restored over
a changed native viewport. Current base-grid04 is12,044bytes/image11,776/BSS3,884,
SHA30399ca0300985666221c962dce9ee77ee2952eae1dfda15b1a6d0ba4f66742c,
using unchanged28-byte host06 API.

282 contract checks pass:109 original geometry calls with identical component
ON/OFF descriptors,96 original visibility combinations,49 scalar key/value cases
trapping property-service reentry, and context/retirement cases. Native scalar
input, availability/exclusion, viewport/GUI and loader services are supplied
boundaries.68 base ownership checks (including older-host rejection) and39 root
regressions/no-skips pass. Accepted disp03 rebuilds byte-identically.

Assisted QEMU grid-live02 passes30 checks/16frames. Setup explicitly selects a
native Golden ratio style and uses native grid enable/Off controls to collect
complete native ON/OFF references. Four visible native line pixels qualify the
positive reference. Actual DISP selects the four logical presets; grid-Off
frames and native plane0 agree while the saved style remains3. Horizon+grid+
composition preserves protected pixels relative to the native horizon reference.
OFF/ON/OFF component edits on the same native page exactly match the appropriate
native frames without changing style3 or counting extra DISP presses. Master-off
from a hidden grid restores a complete native grid-ON frame and releases native
base ownership; the next DISP resumes native cycling. Horizon/composition,
hidden, re-enabled and retired frames were visually inspected, including the
restored top-HUD crop. Reference membership requires both the correct native
base page and grid state, with no fallback image or pixel exceptions.

This is captured-frame equivalence in synthetic assisted QEMU, not a coherent
native update/paint fence, warning-transition, real-card, EVF or durability proof.
Actual native-menu edits/return and broader lifecycle remain open.

### Retained count-only failure

The earlier base-grid03/grid-live01 fails at preset1 after six passing checks:
both geometry counts are0, but lines remain and differ from native Off by3,169
pixels. The native drawing path has encoded repeat fields and a separate plane
gate. Zeroing descriptor counts is not an Off contract. Its121 instruction cases
proved the edits only; that policy was removed. The failed package, source and
frames remain private. The corrected policy changes the native read response,
not the emulator or verifier pixels.

### Native histogram getter rejection contract

For the next histogram binding, the original getter chain104070AC->10203C5E->
10148DA0->101F8F20 gates on driver A188D70C+1==2 and passes driver+2 into100A7382.
That path checks destination alignment and uses native event waiting; it is not
a simple battery-style locked memcpy. The pinned upstream extra histogram pass
must retain real data-service failure behavior.

`tools/audit_z7_histogram_getter.py` executes the original wrapper/driver/zeroing
instructions in224 cases. Only driver-state2 and a four-byte-aligned destination
reach the native wait. Other states/alignment return0 without touching the
buffer. A supplied unavailable event result0 returns0, clears native busy and
pending-destination fields, and zeroes exactly1,024 destination bytes with
canaries preserved. The native wait argument is100; no physical timing guarantee
follows. Fast modes lock/unlock around the pending destination and clear it;
ordinary mode2 retains its own native path. Driver input bytes remain unchanged.
Mutex/event services are supplied; no successful statistics producer/conversion
or histogram pixels are claimed. The port must check the return flag and must
not interpret a zeroed failed sample as valid data. Histogram/highlights,
information app, remaining groups, persistence and broader lifecycle remain.

## After-native-GUI callback for the histogram pass

Host07 adds the32-byte additive `sdk/gui.h` API. Its init-only registration
accepts one callback in the loading module's owned Thumb image. Null, ROM,
non-Thumb, BSS, duplicate and late registrations are rejected. Failed init
clears publication before releasing memory. The existing20/24/28-byte prefixes,
32-byte display hooks and256-byte resident state retain their layouts. Three
previously reserved state words hold the callback, registration and running flag.

The native shooting-app update initializer at A1829B14 now points to the resident
wrapper. Original key/event bindings remain1030DA57/1030DD1F; the entire original
update body1030DB42..1030DD1D is byte-identical. The wrapper calls that original
body first, then the optional module callback, preserving its result, caller
registers and NZCVQ flags. Nested updates still execute the original body but
suppress the nested module callback. This includes early native app-transition
returns; consumers must recheck ownership and rendering state. It is not a frame
or ISP fence. Existing after-paint callbacks remain inside native rendering and
must not recursively submit another drawing pass.

Reproducible host07 MAIN SHA9326b595fd4f47719aaa9bcdb157ce35aa9f3cbd812a62f990585a4e2e52db66,
33,057,580bytes, resident C host3,569bytes. GUI diagnostic01 package SHA
dc7443a8d2500171cf379ceaafe1c437cd6e78255e210bb2d24d0749aba32a99,
384bytes/image320/BSS24. Combined package remains byte-identical atf7dbdf87... .

`audit_z7_gui_host.py` passes122 cases, including20 differentials across five
native paths and four incoming NZCVQ states, original-entry register equality,
callback ordering, nested suppression, failure cleanup, foreign-slot rejection
and older28-byte-host rejection. Original callback instructions execute, while
its direct native service returns are supplied. This does not exercise complete
widget layout or sampling. Existing host99/display316/update24/DISP137/base68
audits and39 root tests/no-skips pass on host07.

Assisted QEMU gui-update-live01 passes11 checks/two inspected frames. Native
RAW/ISP/scanout readiness is observed before the test. Callback count advances
52 to70 while native DISP changes page0 to1; no callback reports render-busy.
No extra paint or histogram sample is injected. Private result/frames preserve
the scope; source summary is `evidence/20261119-native-gui-update.json`.

Next derive the original-Z7 extra histogram layout/submit/present contracts and
bind real sample availability with fail-closed cleanup. Successful statistics,
histogram pixels, remaining components/information groups, information app,
menu-return coherence, persistence, lifecycle and physical installation/recovery
remain open. No camera/card access, staging, flash or push.

## Native histogram component prototype

`display-histogram-probe` extends the base/grid/readout prototype through the
32-byte after-GUI API. It keeps the original histogram masks (six0x444 and
three0x440 words) and native page2 sampling gate. Earlier standalone/combined
grid modules remain compatible; the accepted base-grid04 rebuild is byte-identical.
The new component defaults to custom display disabled and does not create a
new camera installation candidate or bind persistence.

For an owned photo-LCD custom page0/3 with the histogram component enabled,
the optional after-GUI pass checks current/previous page agreement, saved base
property ownership, native key/event bindings, menu/update/exclusion state,
pending display work, descriptor/control identity, native canvas/painter identity,
dirty/visible control flags, photo eligibility and native viewport readiness.
An aligned owned256-word buffer is cleared before original104070AC is called.
Failure, empty nominal success, overflowing totals or a changed context stop
before publishing native bins/scale or submitting a draw. Native event completion
is never invented. Retry cadence uses100 native clock units from completion,
including slow or failed getters; physical timing is not established.

Successful samples use the native min(peak, four times nonzero-bin mean) scale,
with overflow handled before multiplication. The pass copies exactly1,024bytes
into native bins A201DF88 and publishes scale A201D33C, which original getter
103EA09E key3 reads. During layout only the two photo LCD banks temporarily add
bits0/8 or3/11. Original10369248,10369214 and102F27A8 run; all masks restore before
native updater102F2ADA/102F5540 and submit102F2042. The updater installs original
painter102F1545. A temporary owned observer calls that painter synchronously,
then conditionally restores the native default10433913. Only a successful visible
paint in the same eligible context requests native present102F11B6. Present
requests are not proof of physical presentation.

Layout recomputation alone did not hide the native object in failure injection.
The corrected cleanup explicitly uses native hide/dirty services after layout;
component-off/master-off retirement does the same before native invalidation.
Foreign object/painter replacements are preserved. The optional painter is
conditionally removed even from an old object if its control slot changes
during submission. No hot-unload or new object allocation is introduced.

Current private histogram06 is reproducible SHA
9f26f9d690e21c9258e1f555813ae598d766c25fd062a396a07559e2b18ec790,
14,220bytes/image13,952/BSS5,060, using unchanged host07.146 compiled component
checks pass, covering native layout/updater instructions, normalization bounds,
failure cleanup, retirement, native unavailable-event getter rejection,
foreign-write handling, completion-based cadence and old28-byte-host rejection.
One positive chain executes the original histogram painter and scale getter
with supplied bins/render-submit/rectangle/present services. Separate original
painter audit passes28 checks/five cases for scale lookup, native bin geometry,
clipping, empty samples and hidden-object behavior. These prove primitive
geometry, not actual scanout or successful real statistics production.

Retain failed live01/02: the first prototype misidentified shooting-object
A1829AF8 word0 as a zero context flag. Original message dispatcher103764B8
loads that word and calls it as a function. It is now guarded through known
key/event bindings instead. Corrected live03 reaches the real getter and
records failed samples with no paint/present calls, but whole-frame comparison
fails on the native ISO AUTO redraw phase. Live04 confirms native invalidation
alone does not establish that visibility phase. Live05 completes native DISP
cycling before enabling custom display, then passes9 checks/eight frames.
Five real getter attempts produce no optional paint/present requests. The active
frame matches the complete disabled standard-page RGB reference with matching
native formats/ISO visibility. The two disabled initial references, active,
component-off and master-off frames are byte-identical after RGB decoding.
Sampling remains at five attempts after component-off/master-off. The native
reference HUD was inspected and exact pixel equality independently checked.
No pixel exclusions, supplied sample data or invented event completions are used.
This is captured native failure-path RGB membership, not successful histogram
pixels, full submit/present integration or an update/paint fence.

Base68/grid282 (including109 native geometry calls) and39 root regressions/no-skips
pass on the new module. Source summary is
`evidence/20261119-native-histogram-component.json`. Next validate active output
bits at A1821370+0x24 (original103FBCCA reads them), then the successful native
submit/present pixel path and visible-widget retirement with explicit supplied
bins if the emulator has no real statistics producer. Keep that boundary labeled;
real successful statistics production remains unverified. Other display scope,
physical card/cache/wake and exact installation/recovery remain open.

### Successful native histogram pixels with explicit test bins

Histogram08 adds sole-active-LCD checks using original103FBCCA's output word
A1821370+0x24. A RAM-only paint guard checks current bindings, base ownership,
settings/page and output before calling the original painter. It never invokes
property services or native waits. Cleanup skips layout if output/scene changes,
then uses output-independent native hide/dirty retirement.170 compiled component
checks and52 original painter/output checks pass; base68/grid282 also pass.

Private pixels-live05 passes12 checks/nine frames using immutable sample bins
at the exact owned getter boundary. Only the cleared aligned module BSS buffer
and an owned Thumb return address qualify. Other native getter callers pass
through unchanged. No event completion, framebuffer pixels or native display
service returns are supplied by this fixture. Actual native histogram painting
changes37360 pixels entirely inside its original rectangle, with every outside
pixel equal to a captured native reference. Same-page re-enable repeats this;
component-off and master-off restore complete captured native RGB exactly.

Native bitmap rows are bottom-up and fill endpoints exclusive: native rectangle
475,269,675,370 maps to675,156,960,300 on1024x682 scanout. The checker derives
this box, requires visible changes inside, and excludes no outside pixels.
Native format must match the reference. Raw ISO flags remain diagnostic because
they can precede painting; actual captured RGB establishes membership. Failed
readiness, queued-pause, wrong-coordinate and ISO-state-filter runs are retained
privately. The pause fix and coordinate/ownership/register boundary have12 tests;
all51 root tests pass without skips. Fixture/helper sources are frozen with
private evidence. See `evidence/20261119-native-histogram-pixels.json`.

Current package14540bytes/image14272/BSS5060/API32 has reproducible SHA
29155d3343a98ffa9f9edc126fa68b027d9b715699eba4093a3ec3ce39dc91b2.
Host07 is unchanged. Successful real statistics production, physical output
transitions and hardware presentation remain unverified. This advances renderer
integration and retirement, while remaining display/software scope stays open.

### Six ordinary information groups

The optional `display-groups-probe` adds original-Z7 Shooting mode, Release mode
and Focus mode to the existing shutter/aperture/ISO selections. Its native widget
IDs are10/11/15/5/51/2, independently derived from original updater execution and
decoded native icons. In particular, original3 is AF-area,6 is Active D-Lighting,
and51 selects single/continuous/self-timer icons. The Z7II3/6 assignments cannot
be copied. Focus here controls the native MF/AF-S/AF-C/AF-F information widget;
the AF-area status and AF frame layer remain unchanged.

All six groups share the existing conditional mask-ownership protocol: only
photo-LCD words0/3 and bits0x909 can be suppressed; ON retains the native mask.
All other outputs, movie bits, third bank, controls, snapshot values and native
updater bindings stay native. Exposure nonzero formats retain their complete
native group. Native invalidation prepares the following original update/layout
pipeline; the policy never draws or dispatches widgets directly. Twelve-word
restoration preserves foreign writes, latches ownership loss, and defers cleanup
when a descriptor is replaced.

Private status-identity01 passes38 original-updater/icon cases. Private
information-groups-04 passes641 compiled cases across four presets and all64
six-group combinations, exposure formats, native mask selection and each new
group's foreign-word/descriptor/updater handling. Snapshot preservation is tested
with horizon disabled so the independent native base-page setter is isolated.
Groups01 package14604bytes/image14336/BSS5060/API32 is reproducible SHA
063d91a6c8231f0d6124ad4ebff5fbfc1692596441e0aa86ce459683ca206fcf.
The earlier histogram08 package remains byte-identical with the extension off.

Ordinary HUD controls use top-down native720x480 layout coordinates; the
histogram low-level fill has a different bottom-up convention. Four geometry
regressions protect that distinction. Failed live01 records actual shooting
suppression at scanout3,3,54,54 but rejects it using the wrong bottom-up box.
The corrected geometry helper is separate and frozen with subsequent live
evidence. Root55 tests/no-skips pass. Histogram170, base68 and grid282/native
geometry109 regressions also pass on this package.

Corrected live02 passes18 checks/twelve frames. A full native DISP1/3/0 baseline
cycle precedes filtering. Shooting/release/focus OFF each changes pixels only
inside its original top-down HUD control rectangles. Every outside pixel matches
a captured native reference; each ON and final master-off restores complete
captured native RGB exactly. All61 descriptor masks are compared, with only the
target's two LCD words changed. Native snapshot/mode/visibility stores are not
supplied. The diagnostic invokes compiled settings setters, so these results do
not establish native settings-menu editing/lifecycle. Native formats must match;
raw control snapshots are never treated as a completed-paint fence. Key focus-off
and master-off frames were inspected. Source evidence:
`evidence/20261119-native-information-groups.json`.

ON still retains native page eligibility. Some ordinary native masks omit the
horizon page; selecting ON does not currently extend those masks. Review this
against pinned upstream custom-DISP semantics before finalizing the feature.
The new live sequence covers standard page0; contract suppression covers0/3.
Other information, focal length, information app, highlights, portrait,
persistence and broader lifecycle remain open. This is an independent modified
experimental package, not a completed or installation-cleared release.

### Standard and horizon information eligibility

Groups02 corrects the cross-page ON limitation above. Pinned upstream
`sdk/disp.h` uses each LCD bank's original standard-photo bit to seed information
on both custom base pages. The original-Z7 mask interpreter uses bits0/3 for
standard/horizon and8/11 in operation193 states. For ordinary selected groups,
the adapter therefore normalizes only0x909 from that bank's saved bit0. OFF
clears those bits; a bank lacking native standard eligibility stays excluded.
Movie bits, other outputs, the third bank and following native control-level
eligibility remain unchanged. Nonzero exposure formats retain the complete
saved mask, including native warning permissions. Disable restores the original
page-specific masks rather than retaining their expanded custom-page form.

This rule applies only to the optional six-group adapter. Earlier three-group
and histogram08 variants rebuild unchanged. Groups02 is reproducible SHA
a76b0884ecc5f94ed3ab6419159dc8b74af285051152fd9a23ba0b8c9aa8e825,
14604bytes/image14336/BSS5060/API32, using unchanged host07. Information-pages01
passes2753 compiled cases: the prior group/ownership/warning cases plus every
four-photo-bit pattern for every group, opposite patterns in the two LCD banks,
ON/OFF native interpreter results on pages0/3 and operations0/1, snapshot
preservation and exact original-mask restoration. Root55/no-skips pass.

Live horizon validation and remaining regressions are recorded in the current
handoff while they run. Other information, focal length, information app,
highlights, portrait, persistence and broader lifecycle remain open; no physical
camera behavior or installation clearance is established by these checks.

The first two live horizon probes pass selected-glyph and non-information-pixel
checks, but their first isolated Shooting OFF check fails on the native ISO AUTO
region. A native settings OFF/ON reference cycle does not qualify the missing
all-on phase. Those failures remain private; no isolated-toggle success is
claimed from them. The original ISO preparation10369C06, selector102F2586 and
visibility helper102F2656 now execute with the compiled policy in an independent
18-check/four-case audit. At fixed supplied phase0 or1, Shooting ON/OFF produces
identical native ISO controls and preserves the current snapshot. This proves
the covered native path's phase dependence, not the temporal source or a paint
fence. The subsequent live probe records full snapshot/source diagnostics and
samples bounded varied native intervals with settings unchanged to qualify
complete captured-native RGB phases before testing isolated toggles.

Groups03 further separates the original Z7's operation states. Saved bit0 seeds
only0/3; saved bit8 independently seeds8/11. Original shooting-mode bank1 is0x110:
it permits the alternate operation's standard page but lacks ordinary bit0.
Focus/release have the converse pattern in bank0. One bit0 seed for both states
would lose the former permission and invent the latter. The current adapter
preserves both original standard-page eligibility decisions while extending each
eligible state to its own horizon bit. Movie permissions and warnings stay native.

Current groups03 is reproducible SHA
a951a2574b80a41114f4dde62d012506b35388a7d2c9fa45eceb5ead9f487b83,
14604bytes/image14336/BSS5060/API32, unchanged host07. The updated2753-case matrix
passes with independent operation-state seeds. The strengthened phase audit now
passes22 checks, including actual compiled Shooting mask-change assertions.
Root55/no-skips pass and histogram08 still rebuilds byte-identically.

Prior groups02 live03 passes60checks/16frames after four unchanged-settings
samples qualify both complete native ISO pixel states. It proves all three
selected horizon glyphs, protected native horizon/non-information pixels,
isolated toggles and complete captured-native horizon/standard restoration for
that package. Current groups03 live04 also passes60checks/16frames, with the
same exact native glyph/protected-pixel/toggle/restoration requirements. All61
descriptor masks restore and the saved standard page0 returns on master-off.
Live operation193 is0; alternate-operation results remain original-instruction
tests with supplied snapshots, not physical AF proof. Current03 base68/
histogram170/grid282(native geometry109) regressions pass. Key horizon and
master-off crop were inspected, with exact decoded full-frame equality verified
independently. Source evidence `evidence/20261120-native-information-pages.json`
distinguishes both packages. All jobs are terminal; full software goal stays open.

### Other information and shared warnings

The optional `display-other-probe` extends the six-group profile with 18 original
Z7 widgets under the Other switch: AF-area status3, Active D-Lighting6,
metering7, AE lock8, FV lock9, flash compensation13, exposure compensation14,
capacity16, flash mode17, Picture Control26, image area27, microphone/wind34,
multiple exposure38, touch shooting41, image quality/size44, silent shutter46,
VR50 and flicker53. Widget numbers are independently derived native bindings.
[Nikon's display reference](https://onlinemanual.nikonimglib.com/z7_z6/en/14_technical_notes_01.html)
cross-checks label meanings only. White balance37, battery20, AF frame,
flash-ready48, temperature and unidentified controls remain native.

Native updater execution identifies all18 ordinary widgets, including separate
normal Picture Control and N-Log child content. Native preparation prefixes
identify shared formats2 for capacity,3 for flash and4 for metering; prefix
execution stops at the original format helper rather than claiming full
preparation-path coverage. Every nonzero shared format keeps the complete native
group, so Other OFF preserves warning content. Two LCD words per widget now
require48 ownership bits; only this profile uses uint64_t pending ownership.
The existing six-group package rebuilds byte-identically.

Other01 is reproducible SHA
cbadda7a7dfbc27a9c9ca2f955c96dd3c5ae767bc0880178ca8402267c26ae8d,
14860bytes/image14592/BSS5380/API32, unchanged host07. Identity75,
compiled-policy1627, native phase22, base68, histogram170 and grid282 checks pass;
root55 tests/no-skips pass. Policy coverage includes all128 information masks,
four presets, native interpreter results, nonzero warning selectors, all18
abandoned descriptors, pending bits above31 and foreign writes to the last slot.

Standard-page QEMU passes11 checks/eight frames. Other OFF changes only filtered
Other-control pixels; the active capacity warning stays native. An independent
immutable-capture check additionally requires all six separate readouts and the
warning to match the same complete native reference, including regions where
Other-control boxes overlap ISO. Other ON and master OFF restore captured native
RGB; all61 descriptor masks restore. Settings setters remain diagnostic calls,
not native settings-menu/lifecycle proof. See
`evidence/20261120-native-other-information.json` for current horizon results and
the precise evidence boundaries. Focal length, native information app,
highlights, portrait, persistence and broader lifecycle remain open.

Horizon live01 is retained as a failed run:48 of49 checks pass across11 frames.
Other OFF scope and warning preservation pass; Other ON restores mask words but
fails complete native RGB restoration. Against the ISO-matched all-on reference,
65 pixels differ inside ADL widget6 antialiased edges, despite identical current
snapshot and control6 records. The cause remains under investigation. Master OFF
was not reached. No pixels are excluded and no synthetic references are used to
turn that failure into a pass; Other horizon acceptance remains open.

### Independent focal text on LCD landscape

Optional `display-focal-probe` adds native text in its own object1198/label298,
keeping battery1199/299 and VR widget50 separate. The existing Focal information
bit controls it independently in each preset. Original properties1C14/1C01
provide type and tenths-of-mm data;24mm and24.5mm are supported. Missing/invalid
values hide the object. Foreign slots/labels are rejected, native teardown
detaches ownership, and the painter uses RAM-only guards before native drawing.

Native HUD snapshot delta or mask changes request a repaint even when the label
is unchanged. This fixes the first candidate's disappearing text after Other OFF.
Requests remain pending after failed submit, with100ms bounded sampling and
extra-pass cadence. Delta/control flags are invalidation inputs, not completed
pixel fences. The composed after-GUI callback retains the histogram pass.

Current03 passes45 overlay checks,68 base,170 histogram,282 grid(native geometry
109),1627 Other checks and55 root tests/no-skips. QEMU live03 passes20checks/
13frames using explicitly supplied lens properties: visible whole/fractional
text, protected outside pixels, independence from Other and complete native RGB
restoration on Focal OFF, missing lens and master OFF. All61 masks restore.
Private crops and immutable PNG/RGB comparisons were independently inspected.
Earlier failed runs remain recorded. See `FOCAL_LENGTH_RESEARCH.md` and source
evidence `evidence/20261120-native-focal-overlay.json` for hashes and boundaries.

The standard sequence is now supplemented by horizon live03:88checks/54frames
pass on unchanged focal03/host07. Native background must repeat exactly in both
ISO phases before focal entry and after Other ON; both histories retain their
24reference cap. No ADL edges are excluded. Focal reenable, absence/return and
master OFF preserve full native RGB outside the owned window; all61masks and
saved page0 restore. All54PNG fingerprints, seven memberships and18 post-Other
frames were independently checked and private crops inspected. Old failed runs
remain failed. See `evidence/20261120-focal-horizon.json`.

This initial path rejects EVF, rotation and AF/alternate operation states. Those
paths, native MENU return, broader output/lens reconnect lifecycle and physical
telemetry remain open. This is an independent modified experimental profile;
the full display port remains unfinished and no installation clearance follows.

Native information contracts are now bound to original application13, descriptor
A182D16C, key102FD647 and update102FDA09.47 native checks cover registry/requests,
movie/EVF selection rejection and original key admission. This is not a custom
information-page implementation; the bit16 configuration guard remains until
actual owned entry/return/update routing is installed and tested. See
`Z7_INFORMATION_APP_RESEARCH.md` and `evidence/20261120-information-native.json`.

## Highlight preferences version2

The optional `display-highlight-preferences-probe` composes the API72 native
warning transaction profile with the pinned photo-zebra preference semantics.
Its Highlight entry in each preset opens a submenu with these controls:

| Control | Scope | Values |
| --- | --- | --- |
| Show on this page | Selected DISP preset | ON/OFF |
| Pattern (all pages) | Global | OFF, Type1, Type2 |
| Threshold (all pages) | Global | 255,248,235,224,213,202,191,180 |

Pattern1/248 preserve the earlier fixed behavior. Pattern names identify the
native enumeration; physical appearance is not established by these tests.
Back returns to the Highlight row of the owning preset. Per-preset reset keeps
the global pattern/threshold choices. Turning a page or global pattern off
restores the latest captured native baseline rather than erasing Nikon settings.

This variant and its EVF derivative define `Z7_HIGHLIGHT_PREFERENCES`. The model adds
two words (48 bytes total); the wire payload stays64 bytes. `Z7C1` payload
version2 uses former reserved words56/60 for pattern0..2 and threshold index0..7.
The existing `Z7J1` envelope remains80 bytes and keeps the same two-slot transport.
The new decoder accepts valid version1 payloads with zero reserved words and
supplies pattern1/threshold index1. All existing flags, page masks and component/
information selections are preserved. Migration does not write during startup;
a later actual edit is saved canonically as version2 by the existing worker.
Older modules cannot read version2 payloads. Earlier variants still emit version1.

The menu is the settings writer. GUI publication captures pattern/threshold in
its bounded snapshot and epoch; conversion uses that captured choice at native
consumption. A preference edit before consumption cancels old queued work before
parameter copying. A fresh publication retries the new choice. GUI actions
perform no file I/O. Saving, verification and restart loading use the existing
worker/journal path.

The scoped audit passes609 codec/migration checks and95 native menu/parameter/
register/persistence checks. All16 enabled pattern/threshold combinations reach
original-Z7 conversion and register programming; global Off, latest native
baseline restoration, page visibility, stale queued edits, first migration save
and restart loading are exercised. The settings controller emits the expected
native label slots; menu raster and physical camera pixels remain unverified.
Native transaction41 and cleanup27/ownership36 regressions also pass with this
variant. See `evidence/20261120-highlight-preferences.json` and root HANDOFF.md.

## Native-update-driven EVF highlight diagnostic

`display-highlight-evf-probe` extends the preferences profile with photo EVF
conversion and ownership using original-Z7 bindings. It follows the global
pattern/threshold and Custom enable, independently of the LCD page checkbox.
Logical EVF routing uses converter output4, command42062007 and first color13;
LCD keeps output1, command42060007 and first color15.

A copied native-origin record prevents the shared parameter block from being
mistaken for the newly selected output's original settings. First ownership in
both outputs requires an observed matching photo native update. Switching outputs
disables the old owned plane, retaining its baseline, and waits for the new
output's update. Movie updates cannot become photo baselines on a mode change.
A native update observed before GUI eligibility can support later owned work.
Returning to the same unmodified owned context can reuse its retained baseline.
Global Off restores the latest native baseline for that context. Disabled native
parameter tails remain undefined and are normalized when retained/restored.

This is an intermediate experimental port. Automatic output transitions without
a new native update still require producer binding; physical output mapping,
engine lifetime, EVF pixels and orientation remain unverified. Existing preference
profile bytes remain unchanged when the EVF option is absent. See root HANDOFF.md
and `evidence/20261120-highlight-evf.json` for exact validation scope.

## Cache-driven LCD/EVF highlight handoff

`display-highlight-handoff-probe` requires the paired API80 cache-copy host and
extends the EVF profile. It can acquire each output's native baseline from a
tracked native request-cache copy without a foreign display-parameter packet.
Only tracked copies that begin and end in photo mode are admitted, while current
mode is photo. Movie cache writes and copies crossing a mode boundary retire that
bank readiness; returning to photo waits for a fresh photo cache copy or native
photo parameter source. An unobserved cache is rejected. Per-output origins keep LCD and EVF
baselines separate, including exact foreign native parameter updates.

On an output change, the worker first queues a native-consumer disable. Only after
that completes does it queue the target output's application or native restoration.
The consumer confirms the old plane is disabled before retiring its frame-policy
record. A new actual frame supplies the target's native permission; no old frame
pointer or other output's permission is reused. Global Off on the destination
restores that destination's native baseline and relinquishes module ownership.
An enabled Nikon baseline may still render under its original native permission.

A cache-only change invalidates cache-bound frame ownership immediately at the
permission callback. The worker refreshes the baseline and captured generation.
If a native cache copy is incomplete, it disables the owned override and waits;
completion permits retry without a new GUI or foreign parameter update. Queued
application cannot consume a partial cache snapshot. Cache-counter exhaustion
also disables cache-bound ownership without guessing a restoration baseline;
a subsequent genuine native update can reestablish native ownership.

Cache-derived baselines are converted using the current palette. Exact foreign
native parameters remain byte-preserved when their bound raw native cache request
has not changed, including across palette and other-output updates. A newer changed
raw request becomes the restoration baseline. Disabled requests define no useful
tail and restore a normalized zero parameter block. Configuration and journal
formats remain the existing preference version2 /envelope version1.

This is an independent experimental logical-output port. Tracking covers the
host's four audited copy spans; complete native boot/pre-cold writer ordering,
other writers, index ABA, engine allocation lifetime and physical pixels remain
open. Snapshot validation does not make later application atomic with writers.
The full display-port goal also retains orientation/portrait, native Info mirror,
real histogram producer, lifecycle and final installation/recovery assessment.
See root HANDOFF.md and `evidence/20261120-highlight-handoff.json` for validation.
