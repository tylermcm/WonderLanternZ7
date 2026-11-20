# Original-Z7 native module foundation

This component implements [the SD-module port](../SD_MODULE_PORT.md).
The intended installation has two parts: an installed original-Z7 firmware
host, followed by `Z7APP.BIN` on the SD card. The host reads and initializes the
module during startup; later compatible module updates replace the card file
after full power-down. This is a startup loader with one resident combined
module, with no hot unloading. Changing the host or its native hook contracts
can still require another firmware update. Actual card loading and camera
installation/recovery remain unverified; the successful emulator runs supply
the read-only filesystem boundary.

`host/module.c` validates and prepares a module in a caller-owned buffer. It does
not read a card, allocate camera memory, modify firmware, register callbacks,
publish executable caches, or call an initializer. A future Z7 host must supply
those operations using independently verified original-Z7 contracts. The new
experimental `host/z7_380.c` supplies those bindings for an isolated stock-based
probe; its [research and validation record](../Z7_MODULE_HOST_RESEARCH.md)
separates successful instruction-fixture loading from actual QEMU no-card boot.

The SDK now exports ABI, API size, target identity and staged display/menu
registration. See [the display module record](../Z7_DISPLAY_MODULE_RESEARCH.md)
for ownership, publication, the additive API size and reproducible audit commands.
The latest experimental host adds `sdk/gui.h`: one owned init-only callback
after the original shooting GUI update returns. Earlier API prefixes remain
compatible. Consumers must revalidate context; this is not a frame/ISP fence.
The optional `display-histogram-probe` combines custom DISP/base/grid/readouts
with a guarded native extra histogram pass. Its [validation record](DISPLAY_SETTINGS.md#native-histogram-component-prototype)
distinguishes compiled native drawing primitives, real sample failures and
the still-open successful pixel/statistics validation.
No Z7II native addresses are exported. Native modules are
trusted code, not sandboxed. CRC detects corruption; it does not authenticate a
module or make arbitrary code safe.

## Package format

The independent [display settings model](DISPLAY_SETTINGS.md) now supplies
configurable preset/page semantics and a strict64-byte original-Z7 wire format.
Its compiled diagnostic has no native menu binding or card I/O yet.

All integers are little-endian 32-bit words. Image bytes immediately follow the
64-byte header; a sorted table of image-relative relocation offsets follows the
image. BSS is described by the header and occupies no bytes in the package.

| Offset | Meaning |
| --- | --- |
| 0 | Magic `Z7M1` |
| 4 | ABI version 1 |
| 8 | Experimental original Z7 C 3.80 target `0x03800007` |
| 12 | Exact total file length, at most 1 MiB |
| 16 | Nonzero image length, multiple of 64 |
| 20 | BSS length; image plus BSS at most 4 MiB |
| 24 | Even Thumb entry offset, within image |
| 28 | Number of 32-bit absolute pointer relocations |
| 32 | IEEE CRC-32 over complete package with this word treated as zero |
| 36–63 | Reserved, must be zero |

Each relocation points to an aligned image word whose initial value is an offset
within image+BSS. Preparation adds the runtime base, preserving a Thumb pointer's
low bit. Offsets must be strictly increasing. The runtime base must be nonzero,
64-byte aligned, and leave room for the complete memory region without 32-bit
address wrap. Destination capacity is explicit and source/destination cannot
overlap. All rejection paths preserve the destination and output metadata.

The caller must keep source bytes immutable throughout validation/preparation
and keep output metadata separate from the buffers. On actual ARM hardware,
the destination must correspond to the supplied execution address. Cache
publication and synchronization must finish before any native call or callback
registration. A successful module's image/BSS must remain resident while any
task, callback or pointer can reference it; no hot-unload interface exists.

## Offline verification

Use the root laptop environment:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -p test_native_modules.py -v
```

The test compiles the C core using the prepared private UCRT64 GCC (or
`Z7_MODULE_CC`/GCC on PATH), with strict warnings, into an ignored temporary
directory. It checks malformed headers, CRC, relocation bounds/order, rejection
of Z7II identity, buffer canaries, overlap/address overflow, exact file/memory
limits and zeroed BSS. It then executes a synthetic relocated Thumb initializer
under Unicorn at three bases, including API rejection and ABI register/stack
preservation. The loader C itself executes on the native host, not on ARM.

Keystone and Unicorn come from the existing private lab environment. When no GCC
is available the C test class is explicitly skipped; such a run does not establish
loader validation. The recorded November 19 run has no skips.

## Optional C module build

With LLVM clang and ld.lld available, use a new private output path:

```powershell
.venv\Scripts\python.exe tools/build_z7_module.py z7-native-modules/examples/probe.c --output .private/Z7APP.BIN
```

Use `--clang` and `--linker` for explicit executable paths. The packer rejects
unresolved symbols, unsupported relocations, malformed ELF ranges, invalid image
bounds and existing output files. All generated files must remain private.

An optional private compiler is now available through the root laptop workflow:

```powershell
.\tools\Setup-Z7ModuleToolchain.ps1
.venv\Scripts\python.exe tools/build_z7_module.py z7-native-modules/examples/probe.c --zig .private/toolchain/zig-x86_64-windows-0.15.2/zig.exe --output .private/Z7APP-new.BIN
```

Zig 0.15.2 supplies Clang and embedded LLD. The actual C example now compiles,
links and initializes through the compiled Thumb host under the instruction
fixture. The host additionally boots in assisted QEMU with no module card.
Neither result establishes real-card loading or physical cache coherence.
This module command produces no camera-installable firmware; the separate host
builder produces private emulator-only EG/MAIN artifacts. See
[NOTICE.md](NOTICE.md) for provenance and licensing.

## Automatic battery profile

The separate `plugins/battery_percent.c` profile is now available through
`tools/build_z7_display_module.py --variant battery-percent --battery-percent on`
(or `off`). It uses the bounded native sample policy and a GUI-owned native text
object. Read [the exact scope and checks](../Z7_BATTERY_DISPLAY_RESEARCH.md).
It follows known LCD-photo battery glyphs and preserves their warning palette;
adapter glyphs, foreign objects/labels/fonts and unsupported layouts are excluded.
`--variant combined` now joins this with the grid/histogram profile through a
single staged registration; `--battery-percent on|off` also applies there. The
combined package has separate instruction, live-pixel and native MENU lifecycle
checks in the display record. This remains emulator-only software. Keep
generated packages private and do not treat the builder setting as a native
camera menu or installation clearance.

## Native preset base-page diagnostic

`tools/build_z7_display_module.py --variant display-base-probe --output .private/builds/NEW`
adds guarded original-Z7 standard/horizon selection and native grid visibility
to the admitted-DISP prototype. Grid edits preserve the saved native style and
retire through native layout/plane controls, including same-page edits. It uses the existing28-byte host API and preserves the earlier
`display-disp-probe` bytes. See [DISPLAY_SETTINGS.md](DISPLAY_SETTINGS.md) for
conditional property ownership, failure rollback, compiled checks, actual native
key/pixel observations and unfinished component/persistence work. This remains
private emulator research, not an installation-cleared camera update.

## Ordinary information-group diagnostic

`tools/build_z7_display_module.py --variant display-groups-probe --output .private/builds/NEW`
extends the32-byte histogram/base stack with independently identified original-Z7
Shooting mode, Release mode and Focus mode widgets, in addition to the existing
shutter/aperture/ISO groups. It changes only owned photo-LCD mask bits and leaves
native selection, formatting, warnings and painting to the original pipeline.
Other information, focal length and the separate information app remain open.
See [DISPLAY_SETTINGS.md](DISPLAY_SETTINGS.md) for validation scope. Earlier
histogram08 still rebuilds byte-identically with the optional extension disabled.
