# Grid choice in Nikon's existing settings — October 25, 2026

There is now a working lab prototype that stores 3x3 in Nikon's existing grid
setting, using the original save worker and startup loader. It keeps the native
89-record journal format. This is the preferred next grid-persistence experiment;
the earlier 90-record extension remains held.

**October 26 hardware update:** the owner confirmed that the latest build is
installed and retains 3x3 after more than ten seconds switched off on one
original Z7. This is an owner report, not independent observation, complete
functional coverage, long-term durability or emergency-recovery validation.
See `evidence/20261026-grid-saved-owner-hardware.json`. Earlier preparation-only
statements below refer to the lab phase before this report.

The owner requested a fresh firmware build. An exact copy of tested candidate
02 is prepared at `.private/flash-ready/20261025-grid-saved/EG161080.BIN`;
read `GRID_NATIVE_FLASH_ASSESSMENT.md` for that concrete input and rollback scope.
The selected grid is intended to survive shutdowns of any duration. The suggested
ten-second off interval is a regression test, not an expiry timer or reset delay.

## Why the current image resets

The installed image keeps the grid type in a separate RAM word. Its workspace
initializer clears that choice to 4x4. Nikon saves its own grid On/Off setting,
but the separate word is not part of that native payload. The owner measured
temporary retention for off/on under approximately three seconds, and a return
to 4x4 after longer off periods. That is consistent with retained state on quick
restarts; the exact power/shutdown mechanism and threshold are not traced.

The new prototype removes the dependency on that separate RAM word. Fresh CPU
and RAM instances restore the choice from synthetic internal flash alone, so
the test does not depend on simulating a particular number of seconds off.

## Existing-scalar approach

The original Z7 scalar 0x102D is a 32-bit value at `0xA24F182C`, in native main
journal record 49. The original raw setter accepts value 2. More importantly,
the actual original journal loader and post-load validator retain it without
rejecting the journal or resetting the native records. Raw setter acceptance
alone was not used as compatibility evidence.

Stored values are **0 = Off, 1 = 4x4, 2 = 3x3**. The new grid menu and geometry
read that stored value directly. At native scalar-get API `0x10070234`, a
guarded wrapper maps only a successful read of key 0x102D/value 2 to On (1).
Other keys, failure results and other values follow the original getter. The
wrapper also restores the original NZCVQ condition flags. This
keeps audited native boolean visibility consumers working while the stored
payload remains 2. The UI callbacks still use Nikon's setting service; the
normal native worker controls flash writes. No custom flash writer, save hook,
schema descriptor, heap reservation or migration/conversion action is added.

Off stores 0 and forgets the prior grid type. Selecting 3x3 again stores 2.
This differs from the older separate-RAM build's ability to remember the type
while Off. Do not silently describe the two implementations as identical.

Original stock startup accepts the saved 89-record journal and restores every
native payload. Its tested grid menu and visibility predicate interpret 2 as
Off. Thus the experiment avoids the incompatible-journal problem found with
the added record. This is selected stock-consumer compatibility, not a full
camera downgrade/recovery test.

## Exact private candidate

`.private/builds/20261025-grid-native-value-02/`:

- Preset: `grid-native-value-emulator-only`.
- MAIN: 33,054,024 bytes, SHA-256
  `7f29bfda937c90261eff989d5f27dbf71ca2b142308b70879b1a7ef3d46c4075`.
- Full EG: 33,054,026 bytes, SHA-256
  `07d77574bc9fed84d357b4e7c3df808127d361106c10ca26e0b6e2c818f6d0a7`.
- Four guarded windows total 28 bytes; 1,936 appended bytes. The heap-init,
  journal descriptor, load/save and default-reset entry windows remain stock.
- Complete build/report independently reproduced and EG CRC verified.

`features/grid_native_z7.py` implements the optional experiment;
`grid_z7.build(..., native_choice=True)` selects it. `--persistent` and
`--native-choice` cannot be combined. Ordinary presets/builds retain their
previous behavior. The exact owner-installed RAM-only build still passes its
independent rebuild admission after these changes.

Candidate 01 passed its initial value/ABI checks but did not explicitly preserve
return flags. Candidate 02 supersedes it with flag preservation and five added
differential checks. No intermediate image was staged.

The review helper now supports `--preset grid-native` for a separate offline
review with exact-mode admission. It does not stage a card or clear physical
installation. The earlier exclusion applied before this new review path.

## Evidence

`tools/audit_grid_native_value.py` passes **107 instruction checks**:

- Differential reads of all 2,111 indexed native properties, plus invalid
  keys, with five stored grid values: **21,130 original/patched scalar calls**.
  Each checks return PC, stack and callee-saved registers within a bounded
  instruction count; all original NZCVQ flags are compared too. Only the intended
  grid output differs.
- The compiled callbacks, native raw writer, full native getter chain, grid
  visibility predicate, menu current-value markers and packed-byte updater.
- Original request `0x10117860` posts event 0x1000; the original worker
  `0x1011774C` invokes its normal main save path and completion callback.
  Its default save-enable flag and explicit disable API are respected.
- Fresh CPU/RAM instances run original startup `0x10117594`, loading all 89
  native records. 3x3, 4x4 and Off survive the supplied-flash restart tests.
- Fresh unmodified stock startup accepts the same journal and preserves all
  native records; its selected menu/display fallback is Off.
- Supplied program failure preserves the previous valid store. Sampled cuts
  after program operations 1 and 269 load a valid old/new grid value and
  preserve unrelated records. These are whole-program-call boundaries, not
  partial physical flash writes or exhaustive power-failure coverage.
- 90 original/patched geometry calls across three viewport inputs and three
  modes, including invalid-value fallback.

The fixture supplies OS/event and flash-controller boundaries, UI service
dispatch to the original raw setter, widget/viewport inputs and secondary
dataset handling. It does not execute the complete camera power controller.
Public summary: `evidence/20261025-grid-native-value.json`.

QEMU passes **10 native-key menu checks** and **6 assisted live-view checks**.
The actual native UI service stores 2 when selecting 3x3. Both grid sizes render
and Off restores scene pixels. These runs do not persist flash between QEMU
processes; the fresh-flash restart evidence is the instruction fixture above.
Public summary: `evidence/20261025-grid-native-value-qemu.json`; frames stay
private. The 3x3 menu frame was visually inspected.

Patch/container/Thumb tests pass 14 with two optional stock-location tests
skipped; private-source independent admission is exercised separately. The five
review output/admission tests also pass.

## Remaining review and hardware scope

The scalar-get hook is shared native infrastructure, even though its changed
behavior is restricted to one key/value. The full indexed read differential
does not prove every indirect consumer, user setting mode or settings-file
export/import path. U1/U2/U3 interactions, native toggles, standby/wake, complete
shutdown ordering, long-session behavior and physical flash durability need
further validation. No exact electronic explanation of the owner's three-second
threshold has been established.

Before any installation, prepare an assessment for this exact candidate rather
than reusing the RAM-only clearance. Preserve the previously working build,
stock inputs and the source-only evidence. There is still no verified emergency
recovery route. A future physical persistence test must include at least ten
seconds switched off, with normal capture/display checks, and distinguish that
from a quick off/on sequence.

## Reproduce

```powershell
.venv/Scripts/python.exe tools/build_grid_firmware.py --native-choice `
  --output .private/builds/NEW-UNUSED-NAME
.venv/Scripts/python.exe tools/audit_grid_native_value.py `
  --build .private/builds/20261025-grid-native-value-02 `
  --stock .private/builds/20261021-silent-property-01/stock-main.bin `
  --container .private/stock/Z_7_0380.bin `
  --output .private/research/grid/NEW-AUDIT.json
```

Use `tools/probe_grid_firmware.py --view menu` or `--view live` with the same
build and a fresh private output directory for the assisted QEMU checks.
