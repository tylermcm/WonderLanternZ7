# Original-Z7 display module research

Independent original Nikon Z7 C 3.80 software, November 19, 2026. This extends
the [SD host](Z7_MODULE_HOST_RESEARCH.md) using original-Z7 native interfaces.
The framework format derives from the pinned MIT JKWTCN source identified in
[SD_MODULE_PORT.md](SD_MODULE_PORT.md); the Z7 adapters and display module are
independently written. Generated firmware, modules, frames and raw traces stay
private. No camera installation or physical card test has occurred.

## Combined SD module

`plugins/combined_display.c` now combines the six-choice native grid menu,
histogram/horizon mode hooks and automatic LCD-photo battery percentage in a
single `Z7APP.BIN`. It retains the same host ABI and exact stock binding. Battery
admission, compact font, warning palette and hardware gaps are documented in
[the battery record](Z7_BATTERY_DISPLAY_RESEARCH.md).

Both component initializers prepare owned data against a local staging API.
Grid histogram-mask stores are deferred in this profile. Only after both
components prepare successfully does the entrypoint register one unified display
table and one menu with the real host. The scalar masks commit last, with no
subsequent failure path. Host readiness/menu-pointer publication remains staged
until successful return and an inactive grid page. Failed component preflight
or menu ownership leaves the native pointers and masks unchanged.

Private combined bundle01 is reproducible: 5,140 bytes, image4,992, BSS2,216,
21 relocations, SHA-256
`f7dbdf87c9280edf65d5ff495e2079152221740c27009ac0bd316cddf7ff395f`.
The battery-disabled combined packet is
`fdbd54528580bbabab029c8bffde68206246dcc76fe67a7cd48efe76e104b93c`.
The standalone grid packet rebuilds byte-identically to its previously tested
package after introducing deferred mask publication.

The combined packet passes954 grid/registration/rollback instruction checks,
including756 native geometry calls and both component-preflight failures, plus
39 automatic-battery checks. Assisted QEMU passes ten live checks across six
frames, including simultaneous golden-grid pixels and percentage, exact full-frame
stock restoration, and adapter exclusion. A separate native-key run passes all
19 menu checks and all six selections. A further native MENU-entry/return run
passes14 checks across10 frames: an active percentage retires in the menu,
performs no sampling there, and recovers when the native icon becomes eligible
after return. The menu and returned percentage frames were visually inspected.
No real-card or camera result follows.

```powershell
.venv\Scripts\python.exe tools/build_z7_display_module.py --variant combined --diagnostics --battery-percent on --output .private/builds/combined-new
.venv\Scripts\python.exe tools/build_z7_display_module.py --variant combined --battery-percent off --output .private/builds/combined-off-new
.venv\Scripts\python.exe tools/audit_z7_display_module.py --build .private/builds/20261119-display-host-02 --module .private/builds/combined-new --failures .private/builds/combined-new/failures --output .private/evidence/combined-grid-new.json
.venv\Scripts\python.exe tools/audit_z7_battery_percent.py --build .private/builds/20261119-display-host-02 --module .private/builds/combined-new --disabled-module .private/builds/combined-off-new --output .private/evidence/combined-battery-new.json
.venv\Scripts\python.exe tools/probe_z7_display_module.py --build .private/builds/20261119-display-host-02 --module .private/builds/combined-new --view battery-auto --battery-icon-fixture --output .private/evidence/combined-live-new
.venv\Scripts\python.exe tools/probe_z7_display_module.py --build .private/builds/20261119-display-host-02 --module .private/builds/combined-new --view menu --output .private/evidence/combined-menu-new
.venv\Scripts\python.exe tools/probe_z7_display_module.py --build .private/builds/20261119-display-host-02 --module .private/builds/combined-new --view battery-auto --battery-icon-fixture --battery-lifecycle --output .private/evidence/combined-lifecycle-new
```

These remain private emulator-only builds. The live GUI request supplies native
bar/icon visibility once; the percentage is read from the assisted virtual
snapshot. The lifecycle run supplies two additional labeled bar/visibility
requests, before MENU and after return; it does not supply a percentage.
Histogram statistics production remains unverified in QEMU; this
combination does not bypass its original data/eligibility checks.

## Implemented behavior

`z7-native-modules/plugins/grids_histogram.c` supplies the native d9 framing-grid
page with **4x4, 3x3, golden ratio, center cross, 6x6 and Off**. It retains the
existing Z7 property `0x102D`, storing values 1 through 5 for those layouts and
zero for Off. The extended values are normalized only when the native grid
scalar consumer reads that property. The raw stored value remains unchanged;
the unrelated indexed properties retain their original behavior. Actual camera
persistence, import/export and all indirect consumers remain unverified.

The module owns four immutable 96-byte copies of the native grid template.
Golden-ratio coordinates use Q16 value 25033 after native viewport/crop geometry
has run. Both axes validate before either is changed. Native drawing, clipping,
color and the Off path remain in use. There is no per-frame image decoding.
This does not fix the separate installed spiral overlay's reported EVF lag.

The histogram descriptor's nine masks expand from native `0x444`/`0x440` to
`0xCCC`, and its two mode checks admit DISP states 2 and 3. Native exposure,
output, shooting-context and other exclusion checks remain. The assisted
shooting fixture currently supplies a zero context byte at `0xA201D318`; native
code suppresses the histogram in that context even when its other checks pass.
The ordinary live probe preserves this failure. Context 1 also occurs in another
run: an explicit native refresh makes the control visible momentarily, but a
later native pass hides it again. Context zero is one exclusion, not a complete
explanation of the missing rendering. An optional, explicitly labeled context-1
fixture tests that branch; it is not an observed camera state. The failed
supplied-context run is retained and does not establish histogram drawing.
The bounded watch experiment observes the normal updater with context back at
zero after resuming; a one-time diagnostic write is not a valid live context
producer. Do not freeze that field or bypass the native exclusion to force a
successful result.
The corrected observer in private live run 06 stops at native store
`0x1036D5D4`, single-steps on the stopped CPU, and reads control bytes `01 00`
with context zero and DISP state 3. It identifies the native hiding instruction;
the producer of the transient context still needs to be traced.
Later context-write run 07 identifies `0x10370716` in native producer
`0x10370696`. It permits a context only when its original eligibility check,
snapshot `+0x28` and histogram-data service succeed. Service `0x104070AC` reaches
`0x101F8F20`, which requires its driver state to be 2 before fetching bins.
The expanded instruction audit now passes **951 checks**, including original
context production and 1,024-byte bin copying/normalization with supplied
statistics availability. This does not supply statistics to the QEMU camera
pipeline or establish histogram rendering there.

## Callback and menu lifetime

The ABI-1 API grows additively from the original 12-byte identity table to a
20-byte table with `register_display` and `register_grid_menu`. Older modules
can check their smaller size requirement. New display modules require all 20
bytes. This is an experimental interface, without hot unload or chaining.

Registration is accepted only during initialization and only once per kind.
Tables must belong to the loading image/BSS. Functions must be Thumb pointers
inside the image, never BSS, the stack, native ROM or foreign allocations.
The host validates menu layout, row count, owned arrays and activation functions.
Failed initialization clears staged registrations before freeing the image.
Successful modules retain their allocation; a release barrier publishes ready.
These checks prevent accidental dangling pointers; trusted native code can still
write arbitrary memory and is not sandboxed by this interface.

The menu metadata/callback pointers publish from the GUI paint bridge, with a
barrier between metadata and callbacks, only while the grid page is inactive.
An invalid native page list defers publication. Module initialization builds all
owned menu structures before registration, then changes only the scalar histogram
masks after both registrations succeed. No failure return follows those stores.

Thin guarded bridges cover native grid template/geometry, indexed scalar reads,
both histogram mode checks, and before/after native GUI paint. Without a ready
module they preserve stock geometry, scalar values and histogram mode behavior.
The host validates the exact stock fingerprint and original bytes at each hook.

## Scoped validation

- 316 display-host instruction checks cover pointer admission, late/duplicate
  registration, initialization failure, publication and native fallback paths.
  Both images read all 2,114 tested indexed keys; flags are compared too.
- 933 display-module checks include 756 native geometry calls over three
  viewports, photo/movie geometry modes, crops and invalid stored values.
  They test six native setters/labels/selection, failed initialization and bad
  menu ownership, immutable templates, and histogram exclusions across 256
  supplied context combinations. Native histogram visibility instructions run;
  individual property/output gates and UI refresh boundaries are supplied.
- Assisted QEMU runs the native kernel, allocation, host and module with an
  explicit read-only filesystem-dispatch fixture. A menu run passes 19 checks:
  all six choices work through native keys and reopen with the expected focus.
- The ordinary live run passes 14 grid checks: all five layouts produce native
  counts and expected pixels; Off restores the sampled original scene pixels.
  Its histogram visibility check fails with the fixture's zero context. This
  result is retained, not counted as an all-pass live test.
- 39 root regression tests pass with no skips. Their scope includes package
  admission, loading, fixture ownership and installation-review exclusions.

Instruction fixtures model file/kernel/heap/viewport/UI/storage boundaries.
QEMU uses synthetic sensor/calibration inputs. These checks do not establish
physical card/cache behavior, EVF switching, hardware histogram data, settings
durability, sleep/wake, updater acceptance or recovery.

## Reproduction on the root Windows setup

Use new private directory names; builders and evidence writers reject overwrite.

```powershell
.venv\Scripts\python.exe tools/build_z7_module_host.py --display-hooks --output .private/builds/display-host-new
.venv\Scripts\python.exe tools/build_z7_display_module.py --diagnostics --output .private/builds/display-module-new
.venv\Scripts\python.exe tools/audit_z7_display_host.py --build .private/builds/display-host-new --modules .private/builds/display-module-new/probes --output .private/evidence/display-host-new.json
.venv\Scripts\python.exe tools/audit_z7_display_module.py --build .private/builds/display-host-new --module .private/builds/display-module-new --failures .private/builds/display-module-new/failures --output .private/evidence/display-module-new.json
.venv\Scripts\python.exe tools/probe_z7_display_module.py --build .private/builds/display-host-new --module .private/builds/display-module-new --view menu --output .private/evidence/display-menu-new
.venv\Scripts\python.exe tools/probe_z7_display_module.py --build .private/builds/display-host-new --module .private/builds/display-module-new --view live --output .private/evidence/display-live-new
```

The last command intentionally exposes the current histogram fixture gap.
Use `--histogram-context-fixture` only for the separately labeled supplied-context
experiment; it writes no firmware or persistent settings. Builders use the pinned
private Zig toolchain and build each module twice, comparing the complete result.

Private candidate `20261119-display-host-02` has MAIN SHA-256
`1d9a09a4d2d26569dba5852de2b60c9a1bcbe9a9efb94483a9e4215939c1a410`.
Display bundle `20261119-display-module-02` contains a 2,028-byte package with
1,920 image bytes, 2,148 BSS bytes and 11 relocations, SHA-256
`3f698f03db054e144218793428dc47ae91d558399ac33d7f81f59a8f1b987e62`.
It matches bundle 01 byte-for-byte after adding diagnostic build variants.

Custom DISP, battery percentage, live focal length, photo zebras and portrait
layout still require independently verified Z7 data sources and lifetimes.
In particular, Z7 widget 60 has two native power-zoom controls; the Z7II focal
overlay's single-control slot cannot safely be reused by analogy. Z7 widget 50
has a native `%dmm` renderer, but the meaning of its source fields is not proven.
The existing clean-DISP experiment also retains two card-count brackets.

An independent battery-data lead is the native percent formatter at
`0x104C4AA2`: it requests a 56-byte snapshot through `0x10437684`, then formats
the word at `+0x18` as `%d%%`. That wrapper reaches `0x101F9ECE`, which locks
`0xA235AE4C`, copies 56 bytes from `0xA235AEE4`, then unlocks. This differs from
the Z7II's 80-byte contract. Snapshot producers, invalid/sentinel semantics,
sampling cadence and a suitably owned Z7 text object still require validation.

`tools/audit_z7_battery_snapshot.py` now passes 44 instruction checks. It executes
the original getter, wrapper and ARM memcpy with supplied mutex/producer
boundaries, verifying exactly 56 copied bytes, guards, lock ordering and unchanged
source. A prefix trace of the original menu constructor reaches `%d%%` formatting
with the exact +0x18 word for eight values, including out-of-range diagnostics.
Object lookup/hide calls are supplied and the trace stops before formatting;
this does not establish GUI lifetime or real battery telemetry.
The producer audit additionally distinguishes copied telemetry from the native
bar-based fallback. See [battery display research](Z7_BATTERY_DISPLAY_RESEARCH.md)
for the owned HUD-text module and its exact full-frame restoration observation.
