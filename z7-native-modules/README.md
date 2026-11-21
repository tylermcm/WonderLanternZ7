# Original-Z7 native module foundation

The owner-selected first-release target is now `--variant lcd-first-release`:
four LCD presets, grids/native horizon, information groups, battery percentage,
supported focal display and settings persistence on the existing API44 host.
Custom Info/histogram, zebras, portrait and unsupported-output extensions are
deferred. Unsupported v1 preferences are filtered on load/edit; compact menus
omit their controls. The candidate still needs native visual/lifecycle checks
and an exact installation/recovery review. See the latest root HANDOFF.md.

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

The opt-in API84 `sdk/graphics.h` adds staged resident graphics dispatch. Its
[scope and checks](PORTRAIT_RESEARCH.md#opt-in-resident-graphics-bridge-api84)
cover registration and stock fallback; the functional portrait module is unfinished.

The opt-in API92 `sdk/touch.h` adds an init-only resident touch transform after
the navigation API prefix. It preserves the original producer and driver slots;
the host synchronously submits a transformed copy or the original packet and
returns the native result. The loaded portrait diagnostic composes graphics,
button navigation and touch mapping for grid/dial/settings pages. See the
[touch scope and checks](PORTRAIT_RESEARCH.md#resident-touch-api92). Native task/
pending-screen exclusion and physical installation/recovery remain unfinished.

The opt-in API88 `sdk/navigation.h` adds a resident central navigation bridge,
preserving all17 native RAM mode slots. `--navigation-hooks` requires the full
API84 graphics profile. Its [scoped navigation checks](PORTRAIT_RESEARCH.md#resident-navigation-api88)
cover committed callback publication, foreign/stock fallback and the loaded menu
layout latch. Touch, rotation preferences and full input task lifetime remain open.

The SDK now exports ABI, API size, target identity and staged display/menu
registration. See [the display module record](../Z7_DISPLAY_MODULE_RESEARCH.md)
for ownership, publication, the additive API size and reproducible audit commands.
The experimental host includes `sdk/gui.h`: one owned init-only callback
after the original shooting GUI update returns. Earlier API prefixes remain
compatible. Consumers must revalidate context; this is not a frame/ISP fence.
The additive API40 `sdk/information.h` provides owned init-only admitted Info-DISP
and before-Info-update callbacks. Its [validation record](../Z7_INFORMATION_APP_RESEARCH.md#implemented-additive-host-interface) separates instruction sinks from native live compatibility.
The additive API44 `sdk/worker.h` supplies one initialization-only resident-task
callback after native delay argument1000. It enables background work without
performing file I/O from paint/menu callbacks. Registration, failed-init cleanup,
code bounds and recursive-dispatch protection are checked independently. This
does not implement settings persistence or establish card/shutdown timing;
see [the worker record](../Z7_MODULE_HOST_RESEARCH.md#resident-worker-callback).
An explicit `--display-hooks --highlight-hooks` host build adds API48
`sdk/highlight.h` for resident source/consumer callbacks and owned request
cancellation. The [highlight record](PHOTO_HIGHLIGHTS.md#optional-api48-source-and-consumer-host-bridges)
documents its77 scoped instruction checks and diagnostic-only context policy.
Default API44 host and full persistent module binaries remain byte-identical.
These hooks do not yet connect the Photo highlights preference or prove warning
pixels, physical output mapping, camera acceptance or recovery.
The optional `display-highlight-context-probe` now connects that preference to
the full persistent profile's shared GUI/source/worker epoch. Its
[validation record](PHOTO_HIGHLIGHTS.md#shared-settingscontext-epoch-in-the-persistent-profile)
distinguishes61 compiled checks from the still-unconnected parameter submission,
restoration and warning pixels. It requires API48; the default profile remains
API44 and byte-identical.
The further opt-in `display-highlight-parameters-probe` requires API52 and
converts eligible native photo-parameter payloads before their original handler.
Its [parameter record](PHOTO_HIGHLIGHTS.md#native-parameter-payload-path-api52)
separates real caller/copy/ack/completion instructions from supplied kernel/UI
boundaries. It does not yet enable frame permissions, submit owned requests,
restore parameters or establish warning pixels. API44/API48 profiles remain
byte-identical when this extension is disabled.
The optional `display-highlight-owned-probe` composes that API52 path with a
resident asynchronous request and parameter lease. It converts at consumption,
conditionally restores the captured native baseline, and cancels stale work
after native updates. See [owned parameter integration](PHOTO_HIGHLIGHTS.md#owned-parameter-integration).
Its source-frame permissions remain native; immediate pending-frame cleanup,
visible warning pixels and camera installation/recovery are still open.
The opt-in `display-highlight-frame-probe` requires API56 and
`--frame-permission-hooks` in addition to the API52 host flags. It filters the
permission consumed by the primary frame gate, including forced deferred replay,
while keeping caller/pending frame data native. See the
[consumption-time gate record](PHOTO_HIGHLIGHTS.md#consumption-time-primary-frame-permission-api56)
for stale replay checks and supplied hardware boundaries. It has no physical
pixel or installation clearance.
The optional `display-highlight-cleanup-probe` uses the same API56 host and adds
qualified no-frame restoration in the native parameter consumer. It retains the
original native frame permission and verifies the native gate's register effects.
See [consumer plane cleanup](PHOTO_HIGHLIGHTS.md#native-consumer-no-frame-cleanup)
for engine admission, cancellation, failure parking and supplied boundaries.
`display-highlight-cached-probe` adds API60 filtering for native cached metadata
and NULL cached-state refreshes. Its host additionally requires
`--cached-frame-permission-hooks`. See the
[cached path record](PHOTO_HIGHLIGHTS.md#cached-primary-metadata-and-state-refresh-api60).
This closes a demonstrated path around the earlier primary-frame filter;
native frame/parameter scheduling and allocation lifetime remain unproven.
The experimental `display-highlight-coordinated-probe` requires API64 and
`--owned-frame-coordination-hooks` in addition to all API60 host flags. It
excludes the two identified native primary-frame bodies from module-owned
parameter consumption through cleanup completion. Busy owned work cancels and
retries; busy frames return native0. Tracking starts after cold-state validity,
before module activation, so an earlier tracked frame prevents activation.
Foreign Nikon parameter requests remain uncoordinated: a separate supplied
schedule reproduces a stale-frame enable after such an update. Generation
exhaustion refuses admission without shutdown handling. This diagnostic is an
intermediate integration step; see [owned/frame exclusion](PHOTO_HIGHLIGHTS.md#owned-frame-exclusion-api64).
The API72 `display-highlight-native-transaction-probe` additionally requires
`--native-warning-transaction-hooks`. It moves permission writes into the
warning gate, coordinates qualified foreign100-copy requests, and retires their
bridge-local tokens before native completion callbacks. The earlier frame
mutex remains outside the warning transaction. Near generation exhaustion the
owned feature drains while native traffic continues through a terminal lane.
Use its exact paired host/module bundle; cross-profile module loading is
unvalidated. See [native warning transactions](PHOTO_HIGHLIGHTS.md#native-warning-transactions-api72)
for the supplied schedules and remaining native/hardware gaps.
`display-highlight-preferences-probe` uses that same API72 host and adds a
highlight submenu: a per-page visibility toggle, global Off/Type1/Type2 pattern,
and eight global thresholds. Its optional version2 settings payload migrates
version1 records to Pattern1/248 and keeps the existing64-byte payload/80-byte
journal sizes. Older variants retain version1 and rebuild byte-identically.
See [highlight preferences](DISPLAY_SETTINGS.md#highlight-preferences-version2).
The optional `display-histogram-probe` combines custom DISP/base/grid/readouts
with a guarded native extra histogram pass. Its [validation record](DISPLAY_SETTINGS.md#native-histogram-component-prototype)
distinguishes compiled native drawing primitives, real sample failures and
the still-open successful pixel/statistics validation.
The API40 `display-information-probe` composes the full focal/Other/histogram
profile with native information-app routing and conditional user-page restoration.
Older API32 focal builds remain byte-identical. Native information orientation,
complete lifecycle and physical acceptance remain open.
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
shutter/aperture/ISO groups. Each LCD bank and native operation state's own
standard-photo eligibility seeds its two custom base pages; only owned photo-LCD bits change. Native
control selection, formatting, warnings and painting stay in the original pipeline.
Other information, focal length and the separate information app remain open.
See [DISPLAY_SETTINGS.md](DISPLAY_SETTINGS.md) for validation scope. Earlier
histogram08 still rebuilds byte-identically with the optional extension disabled.
