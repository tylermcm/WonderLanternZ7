# Original-Z7 battery display research

Independent original Nikon Z7 C 3.80 research, November 19, 2026. The SD-module
framework and first grid module are described in
[Z7_DISPLAY_MODULE_RESEARCH.md](Z7_DISPLAY_MODULE_RESEARCH.md). An automatic
LCD-photo battery module is now implemented and tested in assisted QEMU. Broader
native lifecycle/output validation and physical telemetry remain open. Earlier
text probes use supplied **63%** and are kept separate below. Nothing has been
staged or flashed.

## Automatic LCD photo module

`plugins/battery_percent.c` follows eligible native battery glyphs, samples the
validated getter once per 16 GUI paint passes, updates the owned label, and
restores stock icon layers when disabled or excluded. Invalid samples remain
rate-limited too. No sampling, allocation or label write occurs while disabled.
Its initial setting is part of the SD package; use builder option
`--battery-percent on` or `off`. There is no camera-side setting menu yet.

Admission requires the live GUI pool, LCD/photo context, no active native menu
page, a visible stock foreground battery glyph (`0x1120,22,24,26,28`), its known
HUD painter and unrotated native layout. Plug/adapter pair `0x112A/B`, hidden
icons, foreign painters, alternate layouts, movie/EVF contexts and bar fallback
are excluded. Restore code can repaint both original foreground/background
layers without replacing their callbacks or visibility. Existing native warning
palette descriptors are inherited for the outline and percentage text.

The native compact LCD readout font comes from kind19's entry at `0xA18237E8`,
font100 in the inspected stock data, with 20-pixel height. The old diagnostic's
font0 has 36-pixel height and was unsuitable inside the icon. Runtime font
admission rejects unknown or larger-than-24-pixel records. Borrowed label299 is
checked for both text and font ownership. GUI rebuilds can reclaim an empty,
reset label; foreign text/font data is never overwritten.

Current private module07 is 2,824 bytes, SHA-256
`89358992419867380781bafae7a1624f4d51955b3920127718f6daba9318ea23`.
Disabled counterpart04 is
`a0237b08bad6d23e48e896857d6fb9ba9331aceea29eb43b12e459ba2b15d66c`.
Both reproduce with the pinned compiler. The builder changes only the owned
initialized setting word and reseals the module CRC; firmware is not modified
by this configuration operation.

39 automatic-module instruction checks cover cadence, rejected samples,
disable/re-enable, font invalidation, warning palettes, GUI slot/label rebuild,
stale callbacks, foreign label/font changes, admission exclusions, full native
pool capacity and disabled-package CRC/admission without work. Original pool,
snapshot and initialization code runs; GUI/telemetry instances and selected
font/list/pixel services are supplied.

Assisted-QEMU run04 passes eight checks across five frames: no native icon means
no overlay/sampling; a one-time supplied native bar/icon request enables the
stock renderer and automatic percentage; disabling restores the complete stock
frame exactly; the adapter glyph does not enable sampling or the percentage.
The percentage comes from the virtual native snapshot (0), not from that GUI
request. The supplied bar1 and icon visibility are explicitly modeled inputs,
not observed camera battery state. Frames were inspected: the native low-battery
red palette is retained, the compact percentage is readable, and the stock icon
returns. Earlier run01 passed narrow pixel checks but wrongly admitted the
adapter glyph; visual inspection caught it, and the implementation was tightened.

This remains a standalone SD module, separate from the grid module. Combining
features, native-key menu/playback transitions, AF redraw stress, movie support,
EVF/HDMI/rotation behavior and physical card/telemetry/cache/wake behavior remain
work. The evidence does not clear installation or recovery.

```powershell
.venv\Scripts\python.exe tools/build_z7_display_module.py --variant battery-percent --battery-percent on --output .private/builds/battery-percent-new
.venv\Scripts\python.exe tools/build_z7_display_module.py --variant battery-percent --battery-percent off --output .private/builds/battery-percent-off-new
.venv\Scripts\python.exe tools/audit_z7_battery_percent.py --build .private/builds/20261119-display-host-02 --module .private/builds/battery-percent-new --disabled-module .private/builds/battery-percent-off-new --output .private/evidence/battery-percent-new.json
.venv\Scripts\python.exe tools/probe_z7_display_module.py --build .private/builds/20261119-display-host-02 --module .private/builds/battery-percent-new --view battery-auto --battery-icon-fixture --output .private/evidence/battery-percent-new
```

## Native data contract

Original menu constructor `0x104C4AA2` calls wrapper `0x10437684` and formats
snapshot word `+0x18` with `%d%%`. Wrapper `0x101F9ECE` locks `0xA235AE4C`, copies
**56 bytes** from `0xA235AEE4`, then unlocks. This is not the Z7II's 80-byte ABI.

Producer `0x101F9888` normally copies input word `+0x18` into that snapshot.
When `0xA18B4DE8` is nonzero, it can instead replace the word using the bar-level
conversion at `0x101F9844`. A percentage overlay must reject that fallback path
instead of presenting bar estimates as precise telemetry. Producer validity,
identity, sentinel and transition behavior still need review before connecting
the display to real battery readings.

`tools/audit_z7_battery_snapshot.py` passes 44 checks: exact bounded native copy,
canaries, unchanged input and lock ordering; original menu-constructor prefix
reaching the percentage formatter; and direct versus fallback producer paths.
The getter, wrapper, ARM memcpy and converter execute original instructions.
Mutex, incoming snapshot and menu-object services are supplied. A formatter
prefix is not a completed menu constructor or hardware observation.

## Native GUI ownership

The native live-GUI getter `0x102F2B84` returns the context, not its object pool.
The observed context is `0xA201E388`; its pool pointer is at `+0x24`.
The initial mistaken direct-pool interpretation was rejected by shape checks;
that failed diagnostic is retained privately.

The original pool constructor `0x103FCE98` declares 1,340 slots, of which 1,200
are regular and 140 are compound. Regular pool metadata at `0xA181C770` describes
284-byte objects. `0x103FCF0E(pool, kind, slot)` returns an existing object or
allocates one through `0x103FCE10`. The native allocator can loop when full, so
the diagnostic checks for free global capacity before calling it. It also
requires regular slot 1199 and dynamic label 299 to be unused. Those slots are
unused in the observed session; that does not establish availability in every
camera state. Future feature code must revalidate ownership after GUI rebuilds
and protect label ownership, rather than relying on this one inspection.

The regular HUD text initializer is `0x10384D82`, with native painter
`0x10384968` and destructor `0x10384954`. `0x10384E02(object, 1)` requests native
layout measurement. The generic text initializer `0x103837AC` is a different
class and was investigated separately. Native text-label storage is the existing
300-entry registry at `0xA2019E78`, updated through `0x103FBB5C`.

The LCD paint list is `0xA201E3B4`. Native list append is `0x103FAEBA`.
The probe creates its object from the GUI callback after module publication,
retains the native destructor, and installs its own painter only in that owned
object. There is no hot unload. A successful module remains resident while the
native object points into its code.

## Text probe and retirement work

`z7-native-modules/examples/battery_display_probe.c` is an SD-loaded diagnostic,
separate from the grid module. Its phases are inactive, display supplied text,
retire, and retired. Private tools change these diagnostic phase words.
It is not a user setting or an automatic battery feature.

The native label renders in QEMU. The first generic/HUD hide-only trials leave
black glyph pixels. A direct rectangle call outside the GUI painter also fails
restoration; that experiment was removed from the tool and its evidence retained.
The SD-loaded probe instead performs retirement in its native GUI callback.
Its first retirement rectangle missed the outlined glyph's padding. The revised
probe reserves native LCD rectangle `(2,392)-(78,436)` around the text layout
`(10,400)-(70,424)` and clears that complete area through native RGBA painter
`0x10433912`. Revised probe 02 passes all seven QEMU checks across three frames.
The inactive and retired complete frames have the same SHA-256
`b3f9f2701de0a5ae1010e14338da83b3bd561c106a1abf9159fcda53dd94013f`.
Both were visually inspected alongside the supplied-text frame. The first failed
module trial remains private and is not counted as a passing rendering test.

The passing 1,096-byte probe package has SHA-256
`83d5ce5c623ba5918dcc4ed6941361e0a0f4e306f24f444714e70ea65da77683`,
1,024 image bytes and 20 BSS bytes. Its independent instruction audit passes
14 checks; the complete packet and metadata reproduce on a second compile.

The transparent-rectangle preparation follows JKWTCN's MIT battery-painter
approach; the original-Z7 addresses and object contracts were derived separately.
Per-component MIT attribution is retained. No firmware bytes, font assets or
camera images are included in source.

`tools/audit_z7_battery_display.py` passes 14 instruction checks covering the
actual pool allocator/zeroing/HUD initializer, one-time list registration,
owned painter ordering, retirement, detached objects, foreign slots/labels,
missing label buffers, full global capacity and an unready GUI. Font measurement,
label/list/paint services, the GUI instance and loader service boundaries are
supplied. This audit does not prove pixels, cleanup on camera, or telemetry.

## Native sample integration milestone

`plugins/battery_sample.h` now implements a bounded direct-sample policy. It
requires initialized snapshot word0 equal to 1, a native converted kind in 1..6,
percent 0..100, and zero bar-fallback flag both before and after the native getter.
Rejected reads preserve the caller's output. The before/after check is conservative;
controller transitions and physical sampling validity are still unverified.

The compiled 192-byte sampler probe passes 23 instruction cases, including both
percentage boundaries, unknown/uninitialized data, fallback before a query and a
supplied fallback transition during the original locked copy. The original
getter/ARM copy run; telemetry, mutex and loader boundaries are supplied.

`examples/battery_native_display_probe.c` connects that sampler to the validated
HUD lifecycle. Its independent audit passes 23 cases covering object ownership,
formatting 0,1,9,10,63,99,100 percent, and rejection without object creation.
The native-sample QEMU run passes seven checks across three frames. It reads the
emulator's native snapshot value0, renders `0%`, and removes it with a complete
frame byte-identical to baseline. The virtual power/controller boot inputs are
assisted; this is not physical battery telemetry. Diagnostic phase control still
triggers one sample, rather than a finished automatic display feature.

Private native-sample package 01 is 1,224 bytes, SHA-256
`fb0feb156df8d50b8dd84e0f2e0fcc45fa370c955f7d1656f058eec975d07523`.
Build reports now hash included source/SDK/linker inputs, including the shared
sampler header, in addition to comparing complete repeat-build packets.
Final bundle02 records current include hashes with the same complete packet;
the fixed-text variant also rebuilds byte-identically to its prior tested packet.

The same run passively observes histogram viewport flag0 and driver bytes
`01 02 02`, with normalized maximum0. Thus the histogram driver is already in
its native required state2 in this fixture; driver admission alone does not
provide statistics. Do not force the context or a hardware completion flag.

Use `--variant battery-sample` for its instruction diagnostic and
`--variant battery-native` for snapshot-to-HUD integration. Both use new private
output directories and the same host, audit and QEMU commands below.

## Reproduction

Use the root private Windows toolchain and new private output names:

```powershell
.venv\Scripts\python.exe tools/audit_z7_battery_snapshot.py --output .private/evidence/battery-snapshot-new.json
.venv\Scripts\python.exe tools/build_z7_display_module.py --variant battery-probe --output .private/builds/battery-probe-new
.venv\Scripts\python.exe tools/audit_z7_battery_display.py --build .private/builds/20261119-display-host-02 --module .private/builds/battery-probe-new --output .private/evidence/battery-display-new.json
.venv\Scripts\python.exe tools/probe_z7_display_module.py --build .private/builds/20261119-display-host-02 --module .private/builds/battery-probe-new --view battery --output .private/evidence/battery-display-new
```

The last command must prove both changed pixels while shown and exact restoration
of the complete reserved region after retirement. Keep any failure explicit.
Native-key mode changes, warning/menu/playback exclusions, EVF/HDMI transitions,
AF redraw, real telemetry, GUI teardown/rebuild, sampling cadence and an owner
setting remain required before treating this as a usable battery-display port.
