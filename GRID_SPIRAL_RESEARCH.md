# Fibonacci curve over the golden grid — October 27, 2026

## Owner trial works; electronic level performance regression

After the gray LCD/EVF candidate was staged, the owner reports "confirmed
working; electric level thing visibly lags". Their comparison narrows the lag
to Golden ratio, conspicuous in EVF and barely noticeable on the monitor. They
recall it was absent before the spiral. This is a report from one original Z7,
not independent observation or a measured latency result. Exact associated
hashes and verbatim feedback are in
`evidence/20261027-grid-spiral-display-owner-hardware.json`.

The current rendering implementation has a concrete expensive path:

- Every eligible dirty-widget paint completion calls the spiral helper. There
  is no check whether the curve itself changed or its pixels were invalidated.
- The helper holds the shared native graphics mutex across the PNG call.
- Original wrapper `0x10431738` reads PNG metadata and calls `0x1043142C` with
  resource ID -1. The explicit asset uses the uncached decode branch: original
  `0x10431544..0x10431574` allocates an aligned image buffer and invokes decode;
  `0x1043170C..0x1043171E` synchronizes and frees that buffer after drawing.
- LCD RGBA image size is 1,382,400 bytes (345,600 pixels), with only 4,195
  opaque curve pixels. EVF is 4,915,200 bytes (1,228,800 pixels), with only
  7,589 opaque curve pixels. EVF decoded image size is about 3.56 times LCD.
  These are exact asset sizes, not measured memory traffic, frame times or
  hardware allocation high-water marks. Metadata/decode scratch adds work.
- The hook clears the original UI pending flag only after the helper returns.
  Repeated decoding therefore adds work to the UI completion path and holds a
  graphics lock needed by other painting. This is the leading explanation for
  the owner comparison; a hardware profiler has not isolated exact costs.

The next renderer experiment should eliminate PNG decode from frequent updates.
Original Z7 graphics primitive `0x1042F066` is a useful native path/paint starting
point: its code creates a path and paint, supplies geometry, draws a stroke,
unbinds and destroys the temporary objects. Candidate path boundaries include
`0x10450852`, `0x10450A3E`, `0x104508A6`; their complete argument and graphics
state contracts still need tracing before an extension can use them. A compact
curve path would avoid full-image decompression. Native API overhead, state
restoration, failures, LCD/EVF geometry and actual camera speed must be verified.
No path renderer has been built or validated yet.

Do not throttle the electronic level, modify its sensor updates, borrow an
unowned native cache ID or assume a spare RAM slot. Drawing only once without
tracking native erasure would leave holes as widgets repaint and break MENU/
display transitions. Avoid a speculative new flash until a renderer experiment
has its own checks. Existing installed image and build hashes remain unchanged;
no camera/card access or new staging occurred during this performance triage.

## Gray spiral and native LCD/EVF routing

The owner reports that the installed yellow curve appears on the rear monitor
and clears/returns through MENU, but is absent from EVF while straight custom
grids remain visible there. The installed helper explicitly accepts only LCD
ID 1 and a fixed 720x480 bitmap, which explains that limitation. The owner wants
the curve to match the normal grid color.

A separate `--follow-display` experiment uses RGBA `(216,216,216,255)`, matching
the normal grid's gray. It calls the original Z7 descriptor getter
`0x10433B80(1, active_display_id, 0)`: component 1 has LCD 720x480 and EVF
1280x960 UI bitmaps. The framebuffer pointer comes from `+0x24` and the packed
shape from `+8`. It accepts IDs 1 and 4, excludes external/unknown IDs, and
requires one existing active registry entry with exactly that address and size.
Null, unregistered, ambiguous and mismatched surfaces refuse drawing. Immutable
gray PNG assets match each native size. The native lock, target save/restore and
original paint-return behavior remain in place. No other camera's code, custom
bitmap allocation or display-switch hook is introduced.

Candidate `.private/builds/20261027-spiral-display-02/`:

- Preset `grid-spiral-display-lifecycle-emulator-only`.
- MAIN 33,074,644 bytes, SHA-256
  `7049b2120a9f88e3859a5d8ec335bb4858e6642ba9a278e5cd95474edf597543`.
- EG 33,074,646 bytes, SHA-256
  `c3cbb8fd4aaa932fc74cfd662cbfaac3f5471ea6ab81edb6148766d5a93449b6`.
- Full independent rebuild and CRC pass. All 132 supplied-boundary checks pass
  for LCD/EVF asset/descriptor selection, value/display/enable gates, refusal
  cases, original walker/return/pending flag, stack/registers and NZCVQ.
- All 18 assisted LCD lifecycle checks pass; nine PNG hashes verify. The gray
  curve appears automatically, remains after resumed execution, clears through
  two MENU roundtrips, returns, and disappears for 3x3/Off. The screenshot
  detector measures the upper arc in the color bars, excluding straight grid
  intersections and gray gradient bands; the complete curve was visually
  inspected. The first run's detector counted gray background/grid pixels as
  a stale curve and is preserved as a failed run. A regression covers that case.
- The default build still exactly reproduces the installed yellow MAIN hash
  `06b89e2a4eb864a96599eea504dd1d2f8aba05c8f072243c3a7d51c999fbd136`.
  Existing yellow assessment/review identities are unchanged.

Private LCD results: `.private/research/grid/20261027-spiral-display-gray-03/`.
Instruction results: `.private/research/grid/20261027-spiral-display-instructions-02.json`.
An additional diagnostic uses original `0x10434378(1,4,0)` to register/select
the native EVF-sized bitmap, supplies grid display ID 4 in emulator RAM, then
calls the compiled drawing entry explicitly. This is a supplied route, not an
eye-sensor transition. The direct raw bitmap capture from attempt 03 contains
all 7,589 expected opaque gray curve pixels, with 6,621 beyond LCD-sized bounds.
Every one exactly matches `(216,216,216,255)` at the vertically reflected source
coordinates. The native RGBA bitmap has bottom-up rows; the LCD presentation
transform normally hides that difference. No pixel is added by the host.

The initial offscreen checks failed: attempt 01 read two-byte samples instead
of four-byte RGBA; attempts 02/03 sampled top-down source coordinates. These
failed results are preserved. The full attempt-03 raw capture independently
resolves the orientation and establishes native EVF-sized drawing. A corrected
end-to-end repeat 04 passes all nine checks, including native registration,
gray pixels beyond LCD bounds and current-target restoration. Its result is in
`.private/research/grid/20261027-spiral-native-evf-04/`. Raw bitmap previews are not EVF
scanout screenshots and may include LCD widgets reinterpreted at the larger
stride because the diagnostic has not switched the whole shooting pipeline.

The EVF descriptor and supplied instruction fixtures do not establish physical
EVF scanout or switching. Camera MENU/DISP/crop/wake transitions, timing,
allocation and concurrency still need hardware validation. No new card staging
or camera flash occurred for this variant. Existing `grid-spiral` installation
review admits the earlier yellow image only, not this new identity. The
clean-display investigation is documented in `CLEAN_DISPLAY_RESEARCH.md` and
is not included in either spiral build.
All 22 root tests pass. Sanitized evidence is in
`evidence/20261027-grid-spiral-display.json`. The ignored Graphify code graph was
refreshed after source edits.

Reproduce the new experiment privately:

```powershell
.\.venv\Scripts\python.exe tools/build_spiral_lifecycle.py --follow-display --output .private/builds/spiral-display-local
.\.venv\Scripts\python.exe tools/audit_spiral_display.py --build .private/builds/spiral-display-local --stock .private/stock/Z_7_0380.bin --output .private/spiral-display-instructions.json
.\.venv\Scripts\python.exe tools/probe_spiral_gray.py --build .private/builds/spiral-display-local --output .private/spiral-gray-qemu
.\.venv\Scripts\python.exe tools/probe_spiral_display_surface.py --build .private/builds/spiral-display-local --output .private/spiral-evf-bitmap-qemu
```

## Automatic paint integration experiment

**Hardware-trial update:** the owner accepts foreground placement and explicitly
requested a trial. The identical rebuilt image has now passed a separate
[candidate assessment](GRID_SPIRAL_FLASH_ASSESSMENT.md), instruction/header checks
and verified card staging. The owner subsequently reports that Golden ratio
shows the spiral and changing grid type removes it. See
`evidence/20261027-grid-spiral-owner-hardware.json` for that limited hardware report.
This authorization applies to that exact
assessed candidate, not to the other diagnostic probes or clean-display research.

The owner requested investigating the missing automatic lifecycle. A separate
private candidate now attaches the existing draw entry to the original Z7
dirty-widget paint completion. The explicit-draw proof described below remains
unchanged. Ordinary grid review modes remain separate. The later explicit
`grid-spiral` offline review mode independently rebuilds the full automatic image;
it is not general installation or emergency-recovery certification.

The pinned original function at `0x103FCC44` waits through `0x103FA97C`, then
walks the native dirty-widget list with `0x10295822`. A guarded 12-byte window
at `0x103FCC54` preserves that original walk before invoking the extension.
It then preserves the original return value, clears the original pending flag
at `0xA18213A4`, and returns through the original epilogue. No new workspace,
timer, capture hook, journal record or flash writer is introduced.

The helper requires stored grid value 3, native LCD grid ID 1 and its original
plane-enable query (`0x103FB7DC`, flag 4). That enable query is a native
permission flag, not proof that a menu does not cover the plane. MENU behavior
must therefore be measured through actual native transitions. The existing
guarded draw helper still locks/selects the registered LCD UI surface, draws
the immutable PNG and restores the prior target.

Candidate `.private/builds/20261027-spiral-lifecycle-01/`:

- Preset `grid-spiral-lifecycle-emulator-only`.
- MAIN 33,062,332 bytes, SHA-256
  `06b89e2a4eb864a96599eea504dd1d2f8aba05c8f072243c3a7d51c999fbd136`.
- EG 33,062,334 bytes, SHA-256
  `52c593aff9895e31b4cfaf15ceb0335bdf4f26671d346dcb499080ea11c0f316`.
- Compared with the explicit-draw parent, 11 changed bytes all lie inside the
  guarded 12-byte window; 352 bytes are appended. Every other parent byte and
  its immutable asset are preserved. Complete independent rebuild and EG CRC
  pass.
- 95 supplied-boundary instruction checks pass, including the existing 15
  drawing checks, value/display/enable rejection, original walker ordering,
  original return value, pending-flag clear, return PC, stack and callee-saved
  registers. They do not establish native scheduling, allocation or display
  timing. Private result:
  `.private/research/grid/20261027-spiral-lifecycle-instructions-01.json`.

The first visual run proves automatic appearance, persistence through five
seconds resumed, native MENU clearing, and one automatic return to the live
scene, without a host draw call or asset upload. Its second MENU assertion was
a false positive: the broad gold-color detector counted Nikon's yellow sidebar
highlight as a spiral. The stored frame has no curve. The observation helper
now distinguishes the curve's observed `(255,208,65)` from the highlight's
`(252,215,37)`, with two regression tests. This first run remains recorded as
failed, not silently rewritten.

The corrected full repeat passes all 18 assisted-QEMU checks. Both native MENU
roundtrips remove the curve and restore it automatically on return. Changing
through the native choice handlers while MENU owns the screen, then leaving
normally, removes it for 3x3 and Off and restores it for Golden ratio. Nine
recorded PNG hashes were verified, and the frames were visually inspected.
The curve occupies 6,906 classified pixels in the live frames, zero in MENU,
3x3 and Off frames. The host makes zero calls to the spiral draw entry and
uploads no image. Startup/calibration/RAW assistance and diagnostic choice/
visibility inputs remain explicit. Result:
`.private/research/grid/20261027-spiral-lifecycle-native-02/result.json`.
All 19 root Python tests pass. Sanitized source-only evidence is in
`evidence/20261027-grid-spiral-lifecycle.json`.

The visual proof also exposes an unresolved layer-order problem: the curve
can cross status icons because the hook draws after native widgets. A proper
owned layer/widget, or a verified native operation that places it behind the
status display, needs investigation. No separate spiral menu row is added:
this prototype combines it with Golden ratio value 3. Direct live-view erase,
DISP, playback, crop/rotation, EVF, low memory, concurrent painting and physical
performance remain unverified. Hardware trials require the separate exact-candidate
assessment above; the drawing proof alone does not authorize staging.

Reproduce the separate experiment privately:

```powershell
.\.venv\Scripts\python.exe tools/build_spiral_lifecycle.py --output .private/builds/spiral-automatic-local
.\.venv\Scripts\python.exe tools/audit_spiral_lifecycle.py --build .private/builds/spiral-automatic-local --stock .private/stock/Z_7_0380.bin --output .private/spiral-automatic-instructions.json
.\.venv\Scripts\python.exe tools/probe_spiral_lifecycle.py --build .private/builds/spiral-automatic-local --output .private/spiral-automatic-qemu
```

## Original explicit drawing proof

The compiled diagnostic now draws a transparent Fibonacci spiral over the
golden-ratio grid and live image in assisted QEMU. This demonstrates native
rendering, not a complete automatically managed camera overlay. No camera or
card was accessed, and no new image was cleared for installation or published.

## Geometry and drawing

`tools/spiral_geometry.py` constructs eleven tangent quarter-circle arcs in
89, 55, 34, 21, 13, 8, 5, 3, 2, 1 and 1-sized squares. They tile a 144x89
Fibonacci rectangle. Uniform scaling fits it inside a 720x480 transparent
RGBA image with margins; circles are not distorted to fill a 3:2 frame. This
is the quarter-circle Fibonacci approximation, not an exact logarithmic golden
spiral. Horizontal and vertical mirroring are available in the generator,
but are not exposed in a camera menu yet.

The current diagnostic uses a two-pixel gold curve. Existing gray phi-grid
lines remain visible. The asset is generated from mathematics, with no camera
image or third-party artwork, and stored as an immutable appended PNG. The
original Z7 PNG decoder and graphics instructions draw it; the host never
composites the screenshot or writes pixels into display buffers.

Composition background: [Fujifilm's golden-ratio guide](https://www.fujifilm-x.com/en-gb/learning-centre/the-golden-ratio/)
describes a golden spiral as a photographic composition aid. The formulas and
quarter-circle construction above define this implementation independently.

## Why a direct draw was insufficient

The native repeated-rectangle grid plane cannot express a curve. An initial
direct PNG call could display a curve during startup, but its loose readiness
checks did not establish simultaneous live view and golden grid. The stricter
second experiment waited for actual scene and grid pixels, then failed to find
the curve. Its trace showed the PNG drawing into a rotating 1024x688 live-image
surface; later frames replaced that surface. These runs are not successful
combined-overlay evidence.

The compiled helper instead uses original Z7 interfaces:

1. Require stored grid value 3 (Golden ratio).
2. Acquire the native bitmap/context mutex at 0x10413FF4.
3. Save the selected surface with 0x10414756.
4. Find exactly one active 720x480 UI surface at 0xB045F200 in the 33-entry
   registry at 0xA180AD84. Missing, duplicate, inactive and differently sized
   surfaces are refused.
5. Select that surface through 0x104146A8, then call 0x10431738 with a zeroed
   stack descriptor pointing to the immutable PNG.
6. Restore the previous surface and release the mutex at 0x10413FFA.

Addresses and guard bytes come from the pinned original Z7 C 3.80 image.
No other camera's routine is transplanted. The UI surface address is explicitly
a guarded lab assumption; display switching and alternate surfaces need tracing
before any production implementation. No startup, shutdown or redraw hook has
been installed. The draw entry is called diagnostically from the host.

## Exact private diagnostic image

`.private/builds/20261027-spiral-ui-probe-01/`:

- Preset `grid-spiral-draw-emulator-only`.
- MAIN 33,061,980 bytes, SHA-256
  `e76f8678add993cd0a665557c09bf081e675eb470937212761d108b0a8f1f5aa`.
- The first 33,056,172 MAIN bytes exactly match the six-layout parent
  `6485b0a579eb469701bcb89c442ab6b7faa1cea748dd3716cc524e500595b97f`.
- A 5,293-byte RGBA PNG and 512-byte code slot are appended, with alignment.
  There are no additional edits to stock code or the parent's patch windows.
- Full image/report independent rebuild and EG CRC passed. Existing grid
  candidate validation and flash-review presets do not admit this new identity.

Reproduce privately from the root laptop environment:

```powershell
.\.venv\Scripts\python.exe tools/build_spiral_probe.py --output .private/builds/spiral-local
.\.venv\Scripts\python.exe tools/audit_spiral_probe.py --build .private/builds/spiral-local --stock .private/stock/Z_7_0380.bin --output .private/spiral-instructions.json
.\.venv\Scripts\python.exe tools/probe_grid_spiral.py --compiled --build .private/builds/spiral-local --output .private/spiral-qemu
```

The build requires your own original stock firmware. Generated firmware, assets,
register traces and camera UI screenshots remain private. Existing output paths
are refused. The ordinary grid/preview build outputs remain unchanged.

## Validation and limits

- All 16 root tests pass, including four new geometry/asset tests for tiling,
  tangent continuity, bounds, mirror geometry, alpha and invalid dimensions.
- 15 helper instruction checks pass with supplied graphics API boundaries.
  They check grid-value gating, lock/select/draw/restore ordering, the exact
  asset descriptor, refusal paths, return PC, stack and callee-saved registers.
- The compiled QEMU probe passes nine checks. It first verifies visible scene
  pixels and golden lines, then executes the appended helper and original
  native APIs. The previous target is restored. The curve occupies 6,304
  classified pixels, and 10,081 pixels change across the complete 1024x682
  screenshot, including ordinary UI updates. Sampled grid lines remain visible.
- The completed overlay frame remains byte-for-byte identical after another
  two seconds of guest execution. This is a short stationary observation, not
  evidence of continuous redraw under changing camera state.
- The final combined frame was visually inspected. Public source-only evidence:
  `evidence/20261027-grid-spiral.json`. Private successful screenshots are in
  `.private/research/grid/20261027-spiral-native-ui-01/`.

This is still an explicit drawing entry. Automatic repaint, cleanup when Off or
another grid is selected, MENU/live-view transitions, crop/rotation/EVF handling,
per-frame allocation cost, concurrency and hardware timing remain unresolved.
Do not add the PNG call to an arbitrary grid or capture callback: those may run
outside the appropriate UI rendering context. The next integration step is to
trace the UI paint lifecycle and own both the drawing and removal behavior.
The existing straight-grid hardware report does not establish any of these
properties for this diagnostic image. Camera update acceptance and emergency
recovery remain unverified for this candidate.
