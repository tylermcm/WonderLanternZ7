# Original Z7 rule-of-thirds grid — October 25, 2026

For the newer existing-setting persistence prototype, read
`NATIVE_GRID_SETTINGS.md`. It passes native-worker/fresh-RAM restart and QEMU
checks while preserving Nikon's 89-record format. That candidate is separate
from the owner-tested RAM-only build described below and has not been staged.

**Hardware result:** the owner reports correct grid operation and an approximate
three-second off-time threshold: rapid off/on under that duration retains the
3x3 spacing; longer off periods restore 4x4. This is temporary retention, not
durable saved settings. The workspace initializer defaults to 4x4 when it runs;
equating that event with every physical off/on was not established. No custom
journal hooks are present in the flashed candidate. Retention mechanism and
battery-removal behavior remain unverified. See
`evidence/20261025-grid-owner-hardware.json` and `GRID_FLASH_ASSESSMENT.md`;
the offline-only scope below is historical.

For the subsequent internal-storage investigation and its compatibility limits,
read `SETTINGS_PERSISTENCE_RESEARCH.md`. The grid build described here remains
RAM-only; no persistence hook or replacement candidate was added by that audit.

## Result and scope

Current standalone candidate: `.private/builds/20261025-grid-emulator-03/`.
The native d9 page now offers **4x4 grid / 3x3 grid / Off**, using a separate
RAM-only choice and Nikon's original boolean grid setting. The choice defaults
to 4x4 after a cold startup. Both geometry tables are immutable; a builder
snapshots one pointer, avoiding mixed counts during a selection change.

MAIN is 33,053,800 bytes, SHA-256
`2762ccd5276e1c4720c06e26f636c6c551cafe3772eb6d24400b769c200cd348`.
The build replaces four guarded windows totaling 32 bytes and appends 1,712
bytes. It is reproducible, has a valid EG CRC, and its QEMU loader independently
rebuilds and compares the entire MAIN and report. It is excluded from ordinary
installation presets and cannot be composed with the separate splash experiment:
both reserve state at the same native workspace initialization boundary.
There is no outer Nikon update package, card staging or installation clearance.

`tools/build_grid_firmware.py` builds the candidate.
`tools/audit_grid_firmware.py` executes its choice handlers, page entry and
geometry hook with controlled UI/property/viewport boundaries. The audit also
executes cold-state initialization and checks its native caller stack contract.
`tools/probe_grid_firmware.py` provides separate native-key menu and diagnostic
live-view probes, writing all runtime evidence privately.

The final native-key menu run passes **10 checks** for initial Off, then selecting
and reopening 3x3, 4x4 and Off. Manual review confirms correct native current-value
outlines. The separate assisted live-view run passes **6 checks**, observing both
grids and disabling the plane again. Its final Off PNG is additionally identical
to the initial Off PNG. The final compiled instruction audit passes **190 checks**
over 270 native geometry calls, cold state/ABI, menu focus/current-value marking
and native boolean property writes. Source-only evidence:

- `evidence/20261025-grid-firmware-qemu.json`
- `evidence/20261025-grid-firmware-unit-v3.json`
- `evidence/20261025-grid-display-latch-final.json`

Private final frames/results: `.private/research/grid/20261025-selector-final-02/`
and `.private/research/grid/20261025-live-final-02/`. Live-view choice handlers
are invoked diagnostically; a complete menu-to-live-view transition in one boot
is not claimed. A stock 1024x682 viewport produces thirds at x=342/684 and
y=228/456, retaining native even-pixel alignment. Stock quarters remain at
x=256/512/768 and y=170/340/510.

## Original investigation

The original Z7 C 3.80 grid has a native geometry path suitable for a 3×3
experiment. This is independently derived from the original Z7 firmware.
Changing six line-count fields from three to two makes the original geometry
builder calculate thirds. No instructions, sensor settings or recording path
were modified in the initial experiment. The first investigation changed counts
only in emulator memory; the later standalone candidate is described above.

The initial fixed count experiment replaced the existing 4×4 guide while Nikon's
On/Off setting was On. The later selector preserves both choices. Camera LCD,
EVF, movie mode, magnification, image-area
changes and clean captured files still need end-to-end verification.

## Independently identified native path

- Stock menu navigation in assisted QEMU: Custom Settings → d Shooting/display
  → d9 Framing grid display → On/Off. Page index `0x153`.
- Page constructor `0x104EFA6A` reads property `0x102D` via `0x104065A4`.
  On selects control `0x1901`; Off selects `0x1902`.
- Display eligibility helper `0x1037723E`, update `0x103772F8`, and viewport
  change handler `0x103773D8` also read that property.
- Geometry builder `0x10376DA0` reads the native viewport via `0x10437190`
  and crop property `0x402`. Its three modes use 32-byte records beginning at
  `0x1064FD90`. Unsigned halfwords at offsets `10` and `22` specify the number
  of horizontal and vertical internal lines. All six original values are `3`.
- It divides each viewport span by **line count + 1**, converts through the
  original soft-float routines, and retains native mode/crop offsets.
- `0x10376F92` prepares the descriptor through `0x103FB9A4`, then submits it
  through `0x103FB99C` → `0x10435ADA` to native overlay slot 4. The downstream
  renderer/display behavior still needs visual confirmation.

For a synthetic viewport `(0,0,720,480)`, mode 0 calculates stock spacing
`180` horizontally and `120` vertically. With two internal lines it calculates
`240` and `160`, giving vertical lines at 240/480 and horizontal lines at 160/320.
Other modes retain their existing small alignment offsets; these were not
removed to make synthetic coordinates look exact.

## Verification

`tools/audit_grid_geometry.py` executes the original builder and original
soft-float instructions in Unicorn. Only viewport, crop-property and allocation
boundaries are supplied. Both original and experimental calls check their return
PC, stack and callee-saved registers.

Result: **91 checks passed**, 90 native builder executions over three viewports,
three native modes and five controlled crop values. Checks cover original count
guards, thirds spacing, extents, styles and preservation of native offsets.
The crop values are test inputs, not a claim that every value is a supported
physical image-area selection. Evidence is source-only:
`evidence/20261025-grid-geometry.json`.

```powershell
.\.venv\Scripts\python.exe tools/audit_grid_geometry.py `
  --stock .private/builds/20261021-silent-property-01/stock-main.bin `
  --output evidence/20261025-grid-geometry.json
```

The stock MAIN must match the pinned SHA-256 in the fixture. A different input
is rejected. No firmware or screenshots are included in the public evidence.
Private menu frames and navigation objects are under
`.private/research/grid/menu-20261025-102523/`.

The first QEMU photo-live-view attempt timed out during the existing diagnostic
5000-unit native display wait, before any grid property/table change. It supplies
no evidence for or against 3×3 rendering. Raw logs remain in the private session.

A second stock boot reduced that test-only wait to 100 units. Shooting startup
returned and a QMP frame showed the synthetic color bars with Nikon shooting
controls. After the diagnostic property setter enabled the **stock** grid, the
guest stopped at an explicitly unmodeled device write: address `0x20145620`,
value `1`, PC `0x102422F2`. The debugger connection then closed. No experimental
count-table writes had run. The failing boundary is an emulator device-model
gap; its relationship to enabling the grid has not been isolated. It does not
prove a stock or modified grid rendering failure. The native geometry descriptor
was still zero at the earlier Off snapshot. No stock-grid or 3×3 screenshot was
obtained. Private evidence: `.private/research/grid/live-20261025-103226/` and
the corresponding private QEMU session logs. Source-only probe summary:
`evidence/20261025-grid-qemu.json`.

## Next implementation boundary

Native-menu and rendered stock/thirds/Off comparisons are complete for the final
standalone emulator candidate. Physical LCD/EVF, crop/zoom/wake combinations,
recorded files and concurrency remain unverified. Emulator success cannot
establish camera installation acceptance or recovery. Persistent grid-choice
storage and composition with other experimental features remain separate work.

To reproduce, choose fresh private output directories; the tools preserve prior
builds and probe evidence rather than overwriting them:

```powershell
.\.venv\Scripts\python.exe tools/build_grid_firmware.py --output .private/builds/grid-next
.\.venv\Scripts\python.exe tools/audit_grid_firmware.py --build .private/builds/grid-next --stock .private/builds/20261021-silent-property-01/stock-main.bin --container .private/stock/Z_7_0380.bin --output .private/grid-next-unit.json
.\.venv\Scripts\python.exe tools/probe_grid_firmware.py --build .private/builds/grid-next --view menu --output .private/research/grid/menu-next
.\.venv\Scripts\python.exe tools/probe_grid_firmware.py --build .private/builds/grid-next --view live --output .private/research/grid/live-next
```

Run guests sequentially. Instruction fixtures collect Unicorn callback cycles
between cases to avoid retaining many separate ROM mappings during a large audit.

## Display-plane discovery and emulator extension

The stock grid became runnable after adding the independently traced boolean
write contract at display offset `0x1620`. A stock run then changed its native
descriptor between three and two internal lines, but no grid appeared in QMP
frames. That result was not a rendered-grid pass.

The grid is a separate display plane, not an OpenVG drawing primitive.
Original functions `0x1023C4B0` / `0x1034B364` prepare repeated rectangles;
`0x10242186` packs their positions, spans, thickness, spacing, counts minus one
and style into offsets `0x1600..0x1618`; `0x102422E8` writes the enable bit.
The LCD instance uses `0x20145600..0x20145620`. Offset `0x161C` is unmodeled;
the enable bit is write-only in this hypothesis. Debugger bulk reads across
either boundary were rejected and diagnostic scripts were corrected.

The QEMU LCD compositor now draws the observed black-initialization style
`0x01000000` and gray-active style `0x03D8D8D8` from these registers underneath
the existing native UI plane. Geometry derives from the firmware's register
writes; the low 24 color bits are approximated as opaque RGB. Color/blending,
half-open edges and plane priority
are functional hypotheses; physical colors/blending, edge inclusion and EVF
scanout are unverified. Unsupported styles are not silently approximated.
This extension neither edits RAW buffers nor invents device completions.

Firmware-free ARM register-contract probes pass 14 checks. The production
renderer suite passes 292 synthetic checks, including stock quarters, thirds,
Off, spans, thickness, zero spacing and unsupported styles. Existing firmware
patch/container/Thumb suites pass 14 checks with two optional integration tests
skipped; the RAW-input Python suites pass all 11 checks using workspace-local
temporary storage. The first sandbox-default temporary path was inaccessible,
so that run failed on host file permissions rather than input parsing.

Two early selector candidates exposed test/UI issues: native menu startup was
not ready before blind key counts, and dynamic labels needed control flag
`0x1209` rather than stock translated-resource flag `0x1000`. The first working
selector also focused 3x3 while leaving the stock current-value mark on 4x4.
The final constructor follows the native focus/current-value helper contract
with the chosen control ID. Earlier failed runs and frames remain private.

The first final-candidate live probe passed native count/enable checks but failed
pixel checks because it submitted the gray-active style, which the first display
model did not support. That failed run is preserved at
`.private/research/grid/20261025-live-final/`. Supporting the observed gray style
changes QEMU only; the firmware remains the exact candidate 03 identified above.

The first final menu run reached correct 3x3 and 4x4 selections but hit its
420-second test watchdog at the last Off/reopen step. It is preserved at
`.private/research/grid/20261025-selector-final/` as an incomplete run. The final
repeat with a bounded 900-second watchdog passes all 10 menu checks.
