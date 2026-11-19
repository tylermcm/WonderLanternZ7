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
