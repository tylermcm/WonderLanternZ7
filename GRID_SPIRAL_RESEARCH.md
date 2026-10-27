# Fibonacci curve over the golden grid — October 27, 2026

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
