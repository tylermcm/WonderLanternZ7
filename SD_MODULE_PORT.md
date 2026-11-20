# Z7II extension port into the original Z7

November 19, 2026. The owner selected **SD-loaded modules first, then display
features**. Work targets the original Z7 C 3.80 without the paid RAW-video upgrade,
matching this lab's existing scope. This is independent work; source and notices
are preserved, and generated artifacts remain private.

## Inspected upstream

[JKWTCN/z7ii-extensions](https://github.com/JKWTCN/z7ii-extensions/tree/50a22b24c50619cffa646dac386e8334659f475a)
was inspected at commit `50a22b24c50619cffa646dac386e8334659f475a`.
Its README identifies `v0.1.0-preview.21`, targeting **Z7II C 1.70**, and lists
15 feature groups with author-reported hardware verification. These reports are
evidence about their tested Z7II, not validation on the original Z7. Known issues
include missing/incorrect grid or extension startup, pre-capture live-view stutter,
and temporarily unreadable photos while writes are pending. Long-term and
sleep/wake behavior remain unconfirmed in the README.

The reusable architectural change is a small installed host that starts a task,
waits for card readiness, reads `Z72APP.BIN`, validates its header/CRC, allocates
image+BSS, applies pointer relocations, publishes executable caches and calls its
Thumb initializer. Successful modules remain resident until power-off. Later
module updates replace the card file after full power-down. Removing the file
does not unload an already-running module, and does not restore the installed
host firmware or establish emergency recovery.

The combined module validates native bindings and installs RAM callback changes
for many features. The tiny public API is not an abstraction of the whole camera:
plugins still contain many Z7II function addresses, state addresses, widget IDs,
property IDs, file structures and callback assumptions. Rebuilding their plugin
for ARM or changing only the model ID would not create an original-Z7 port.

Relevant sources are [host/host.c](https://github.com/JKWTCN/z7ii-extensions/blob/50a22b24c50619cffa646dac386e8334659f475a/host/host.c),
[tools/module.py](https://github.com/JKWTCN/z7ii-extensions/blob/50a22b24c50619cffa646dac386e8334659f475a/tools/module.py),
[sdk/z72.h](https://github.com/JKWTCN/z7ii-extensions/blob/50a22b24c50619cffa646dac386e8334659f475a/sdk/z72.h)
and [plugins/combined.c](https://github.com/JKWTCN/z7ii-extensions/blob/50a22b24c50619cffa646dac386e8334659f475a/plugins/combined.c).
Only selected public text sources were saved under ignored
`.private/research/z7ii-50a22b2/` for reproducible comparison; no release BIN,
installer, firmware or camera screenshots were downloaded.

## First implemented stage

**Latest display milestone:** [Z7_DISPLAY_MODULE_RESEARCH.md](Z7_DISPLAY_MODULE_RESEARCH.md)
records the staged callback/menu API, native six-choice grid module, compiled
instruction audits and assisted-QEMU menu/pixel checks. The SDK exports display
registration now; the initial offline-stage limits below are historical. Latest
custom-DISP/base/grid/information and guarded histogram work is recorded in
[DISPLAY_SETTINGS.md](z7-native-modules/DISPLAY_SETTINGS.md). Native histogram
pixels pass with explicitly supplied bins; real statistics production is unverified.

**Continuation:** the [original-Z7 host probe](Z7_MODULE_HOST_RESEARCH.md) now adds
boot/task, filesystem and cache bindings. The actual C module and host compile
as Thumb; 99 instruction checks and seven assisted-QEMU startup checks pass.
Successful module loading uses the instruction fixture's modeled filesystem,
not a physical card. The initial offline-stage description below records the
starting point, not the latest limit.

The new [native module component](z7-native-modules/README.md) adapts the format,
CRC, relocation algorithm, linker layout and module packer under upstream's MIT
license. It uses its own `Z7M1` magic, `0x03800007` target and minimal `z7_main` ABI,
so Z7II modules cannot be admitted accidentally. The C core validates every
relocation before copying, clears BSS, rebases pointers and rejects overlap or
address wrap. It does not execute native camera functions.

Ten new tests compile/run the C core on Windows and execute a synthetic Thumb
module at three addresses under Unicorn. All 33 root tests pass, none skipped.
ELF packing is tested with a synthetic linked ELF. LLVM clang/ld.lld are absent
from the inspected PATH; compiling/linking the example C module remains untested.
This is a loading-core proof, not an SD reader, firmware integration, camera
update, display port or completed SD-loaded module system. No firmware preset,
existing candidate, card contents or physical camera was changed.

## Port order and original-Z7 work

| Feature group | Source mechanism / current Z7 position | Next step |
| --- | --- | --- |
| SD module host | Original-Z7 host probe implemented; native wrappers audited and no-card boot tested in QEMU | Validate physical card/cache behavior; retain the no-feature probe before display modules |
| Framing grids | Six native module styles, combined registration and native visibility component implemented; scoped instruction/QEMU menu/pixel checks | Preserve saved encoding and complete broader combined/physical lifecycle validation |
| Histogram + horizon | Native base-page ownership and guarded histogram pass implemented; real getter failures and supplied-bin native pixels validated separately | Validate successful real statistics production and broader combined/physical lifecycle; preserve photo/video/output gates |
| Custom DISP pages | Native four-preset cycle, base/grid selection, six separate information groups plus18 Other widgets and guarded histogram integration; scoped native policy/pixel restoration checks | Resolve Other horizon ADL repaint mismatch; finish focal length, native information app, highlights, portrait, persistence and broader native lifecycle; see z7-native-modules/DISPLAY_SETTINGS.md |
| Focal length | Original live producer/getter bound to keys1C14/1C01; standalone compiled sampler passes147 scoped native checks; existing VR mm field identified separately | Add independent text ownership and GUI/output lifecycle, preserving VR/Other selection; physical lens telemetry remains unverified; see FOCAL_LENGTH_RESEARCH.md |
| Battery percentage | Automatic LCD-photo module and combined grid/battery package implemented; rejects bar fallback, retains compact native text/warning colors; stock restoration and MENU lifecycle tested in assisted QEMU | Validate playback/AF, other outputs and physical telemetry before installation review |
| Photo highlights / zebras | Producer/display callbacks and photo-specific parameters | Trace Z7 native movie highlights path, ownership and LCD/EVF routing; keep movie settings separate |
| Portrait display | Native objects, orientation and layout callbacks | Map Z7 orientation/rotation policy and object geometry; test each affected photo/movie/menu path |
| Extended movie recording | RAM callbacks propagate longer native capacity-limited duration | Trace Z7 duration, writer/encoder budgets and UI messages; retain native thermal/error/storage handling |
| Silent shutter sound | Per-photo owner+sequence identity and RAW/image notifications, with burst/input state | Compare to our failing notification-only trigger; prove Z7 photo transaction semantics before enabling |
| JPEG pre-capture | Silent H+ capture, RAM ring, queued JPEG retention/promotion and writes | Map Z7 JPEG/RAW ownership, capture scheduling, file registration, cancellation and single-card pipeline |
| Filtered playback | Native enumeration/navigation and full-frame/thumbnail filtering | Validate Z7 file identity, deletion/navigation and card changes before altering lists |
| AF-area shortcuts | Native control assignment and AF selection callbacks | Map Z7 button and AF enums independently |
| Custom wide-area AF C1/C2 | Native AF geometry, subject selection, i-menu and command-dial handlers | Establish what the original Z7 AF pipeline supports; no Z7II geometry/capability assumption |
| Wi-Fi settings | Region tables, Wi-Fi task callbacks and auxiliary controller code | Inventory original-Z7 radio/controller support before considering any port |
| Menu localization | Native menu layouts and supplemental glyphs | Use Z7 native English menus first; preserve separate font license if glyphs are later reused |

Display order after the host: existing grids and histogram/horizon as integration
controls, then custom DISP, focal length, battery percentage and photo zebras.
The spiral's existing EVF level lag remains unresolved; moving PNG decoding into
a module alone will not remove it.

## Host interface gates

The next implementation must record original-Z7 derivation, argument/result
contracts, ownership, failure behavior and instruction tests for these services:

1. **Boot and task lifecycle:** original call/return behavior, descriptor size,
   worker stack, initialization exactly once, failed task creation and wake/reset.
   Do not reuse the Z7II anchor `0xb18aedb8` or task descriptor by analogy.
2. **Card and filesystem:** readiness, actual original-Z7 volume/path, metadata
   size, partial reads, close/read errors, card removal and bounded retries.
   Our sound port references original-Z7 file routines at `0x102d8562`,
   `0x102d8566`, `0x102d86d8` and `0x102d85f2` and reserves 48 stack bytes.
   These were leads for the independent inspection now recorded in
   `Z7_MODULE_HOST_RESEARCH.md`. The native Z7 object is also 40 bytes; the
   extra stack space holds read-count storage and alignment.
   Upstream's loader uses a 40-byte descriptor and an explicitly cache-invalidated
   64-byte-aligned staging buffer; its final read requests one extra byte of
   capacity. The Z7 read convention and status code were verified separately.
3. **Memory and execution:** allocator alignment/capacity, lifetime, zeroed BSS,
   executable mapping, D-cache clean / I-cache invalidation, synchronization,
   allocation/read/validation/init failures and retaining the owning allocation.
4. **Publication:** stage callback registration until initialization succeeds;
   never free code/BSS while a callback or task can still reference it. Native
   modules are trusted code; returning failure cannot undo arbitrary writes.
5. **Firmware admission:** bind the host patch to the exact stock Z7 C 3.80
   fingerprint and checked hook bytes; no Z7II package digests or fixed patches.
   Build new private candidates, preserving the installed grid trial and all
   prior rollback inputs. Emulator results do not establish camera installation
   acceptance or recovery. A separate concrete installation/recovery assessment
   and explicit owner authorization are required before camera staging/flashing.

The existing Graphify graph was used to locate the grid, live-view and sound
paths and is refreshed locally after these code edits. Generated graphs remain
ignored. [PORT_AUDIT.md](PORT_AUDIT.md) still applies to the unresolved sound port;
this work does not clear it.
