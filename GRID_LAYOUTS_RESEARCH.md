# Additional composition grids — October 27, 2026

An independent lab candidate adds three layouts to the original Z7 C 3.80
framing-grid menu. This is separate from the published three-choice preview;
the published image and its default build/report remain byte-for-byte unchanged.
The additional layouts have not been installed on a camera or cleared to flash.

| Menu choice | Stored value | Drawing |
| --- | --- | --- |
| 4x4 grid | 1 | Three evenly spaced lines in each direction |
| 3x3 grid | 2 | Two evenly spaced lines in each direction |
| Golden ratio | 3 | Two lines per axis, near 38.2% and 61.8% |
| Center cross | 4 | One full-length line through each axis midpoint |
| 6x6 grid | 5 | Five evenly spaced lines in each direction |
| Off | 0 | Native grid plane disabled; previous type forgotten |

The golden-ratio option is a phi grid, not a spiral. A spiral, golden triangles
or diagonal guides need a different drawing path: the traced LCD-grid primitive
repeats horizontal and vertical rectangles. A subsequent
[Fibonacci drawing proof](GRID_SPIRAL_RESEARCH.md) uses the native PNG/GPU path
on the UI surface. It is separate from this six-layout candidate, with automatic
redraw/removal and physical-camera behavior still unverified.

## Implementation

The optional build uses Nikon's original 32-bit grid scalar, native setting
service and unchanged 89-record journal. Existing values 0, 1 and 2 retain their
meanings. Only successful reads of property 0x102D with stored values 2 through
5 normalize to native boolean On. Other values, properties, return status and
NZCVQ flags follow the original getter. Menu and geometry code read the stored
scalar directly. There is no timer, custom settings record, flash writer, heap
reservation or save-worker hook.

The center and dense grids select immutable copies of the three native geometry
records with one or five repetitions. Golden ratio first uses the two-line
records so Nikon computes viewport, crop offsets, line extents and style. A
guarded return-path hook then changes only the two first-line origins and the
two repeat intervals. For each span, the first displacement is
`floor(span * 25033 / 65536)`; the second is mirrored, with interval
`span - 2 * first`. The Q16 fraction approximates `1/phi^2`. Tested first-line
positions differ from exact phi by less than one pixel, and the pair is symmetric.
The native geometry notification, when used, sees the completed descriptor.

All six 48-pixel menu rows fit the native 720x480 menu viewport, at 52-pixel
pitch. Labels are dynamic slots 39 through 44; independent IDs 0x7A30 through
0x7A33 are checked against stock menu IDs. Native focus, activation and Off
handlers remain in use. Menu QEMU tests select every entry with native keys,
leave the page and reopen it to check the stored value and focus.

## Reproduce the private lab candidate

Use current working source, not the older preview ZIP. Follow the root laptop
setup and provide your own original stock firmware. From the repository root:

```powershell
.\.venv\Scripts\python.exe tools/build_grid_firmware.py --native-choice --extra-grids --output .private/builds/grid-layouts-local
.\.venv\Scripts\python.exe tools/audit_grid_native_value.py --build .private/builds/grid-layouts-local --stock .private/builds/20261021-silent-property-01/stock-main.bin --container .private/stock/Z_7_0380.bin --output .private/grid-layouts-audit.json
.\.venv\Scripts\python.exe tools/probe_grid_firmware.py --build .private/builds/grid-layouts-local --view menu --output .private/grid-layouts-menu
.\.venv\Scripts\python.exe tools/probe_grid_firmware.py --build .private/builds/grid-layouts-local --view live --output .private/grid-layouts-live
```

The stock MAIN path above is an existing local extraction, not included in the
source repository. On a fresh setup, first extract it using the root setup
instructions and pass that path to `--stock`. Existing output directories are
refused. Generated firmware and screenshots stay private. `--extra-grids`
requires `--native-choice` and produces preset `grid-layouts-emulator-only`.
Independent candidate admission rebuilds the complete image and report.
The existing flash-review presets reject this new candidate.

## Exact tested candidate and evidence

Candidate: `.private/builds/20261027-grid-layouts-02/`.

- MAIN: 33,056,172 bytes, SHA-256
  `6485b0a579eb469701bcb89c442ab6b7faa1cea748dd3716cc524e500595b97f`.
- Full EG: 33,056,174 bytes, SHA-256
  `437e1f8edbb89f1409ad768dcf50e91725280481561fcaa8f0f161cc64e5dccc`.
- Five guarded edits total 44 bytes; 4,084 appended bytes. Heap, original
  journal schema, load/save and default-reset entry windows remain stock.
- Repeated build, complete image/report admission and EG CRC passed.
- 484 instruction checks, including 33,808 original/patched scalar calls,
  756 geometry executions, native journal reloads with fresh CPU/RAM, stock
  selected-consumer fallback, native packed snapshot bytes, supplied write
  failures/cuts and the geometry-notification branch.
- Three viewports, all three native geometry modes, five crop-property values,
  and eight stored values cover the main geometry comparisons. Return PC,
  stack and callee-saved registers are checked during instruction execution.
- Assisted QEMU: 22 menu checks and 13 shooting-view checks. Pixel probes hit
  every horizontal/vertical grid line; Off restores the sampled scene pixels.
  Menu and all three new layout screenshots were also visually inspected.
- Existing three-choice build and report match candidate 02 of the released
  preview exactly, and its 107 instruction checks still pass.
- 12 root tests and 16 patcher tests passed, with private stock input and no
  skipped integration tests. No QEMU C changes; renderer/ISP suites were not
  repeated for this Python/patcher change.

Sanitized evidence: `evidence/20261027-grid-layouts.json`.

Unicorn supplies OS, storage, UI-service/widget, viewport and visibility
boundaries. Its journal tests carry synthetic flash bytes into a fresh CPU/RAM
instance. They do not establish physical durability or complete camera shutdown.
QEMU uses existing startup/peripheral assistance and a functional LCD-grid
model whose physical blend/scanout behavior is still unverified. Shooting-view
tests invoke compiled callbacks and native visibility update diagnostically;
they do not simulate a real sensor or prove capture behavior.

No card writes, physical installation or release publication occurred. Generic
property consumers, presets/import/export, wake behavior, extended use and
camera recovery remain outside this validation. The owner's hardware result
for the earlier three-choice image does not transfer to this candidate. A
separate exact-candidate installation/recovery assessment is required before
considering a hardware trial.
