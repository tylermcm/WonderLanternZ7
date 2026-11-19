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
