# Independent original-Z7 module research

`plugins/portrait_geometry.h` derives its quarter-turn geometry from pinned
upstream `plugins/portrait_menu.c`, copyright (c) 2026 JKWTCN, MIT. Bounded
original-Z7 transforms, read-only orientation sampling and native queue audits
are independent local modifications under the same license. See
`PORTRAIT_RESEARCH.md` for scope; portrait display integration is unfinished.
`plugins/portrait_draw.h` follows the same pinned synchronous local-message and
deferred-completion approach, with independently bound original-Z7 payloads,
native adapter addresses, angle offset and argument layouts under MIT.

This is an independent, modified adaptation for **original Nikon Z7 C 3.80**.
It is not a Nikon, Wonder Lantern, or JKWTCN release. It currently contains a
firmware-independent loading core, not an installed camera module host.

The module format, CRC algorithm, relocation approach, linker layout and LLVM
build command derive from [JKWTCN/z7ii-extensions](https://github.com/JKWTCN/z7ii-extensions),
commit `50a22b24c50619cffa646dac386e8334659f475a`, retrieved November 19, 2026:

- `host/host.c`: header validation, CRC and relocation approach.
- `sdk/z72.h`: model-tagged native module ABI concept.
- `sdk/module.ld`: image/BSS layout.
- `tools/module.py`: ELF extraction and LLVM build approach.

Copyright (c) 2026 JKWTCN. The MIT license is preserved in [LICENSE](LICENSE).
Local modifications are copyright (c) 2026 WonderLanternZ7 contributors and
are also provided under that MIT license, including `tools/build_z7_module.py`.
No upstream font assets, firmware patches, firmware bytes or screenshots are
included in this component. Other repository components retain their own licenses.

Local changes introduce a separate original-Z7 identity and minimal ABI, separate
validation from preparation, validate all relocations before destination writes,
check destination overlap and address overflow, bound ELF reads and allocations,
and add native C and synthetic Thumb execution checks. Z7II packages are rejected.
The new original-Z7 host adapter is independent local MIT code. Its scoped
filesystem/task/cache instruction checks and assisted QEMU no-card startup are
documented in `Z7_MODULE_HOST_RESEARCH.md`. The independent display-hook API and
grid/histogram module are documented in `Z7_DISPLAY_MODULE_RESEARCH.md`, with
native menu/grid emulator observations and an unresolved histogram rendering
gap. Physical card/cache behavior and camera display integration remain unverified.

`examples/battery_display_probe.c` and `plugins/battery_percent.c` adapt the transparent-rectangle preparation
from upstream `sdk/battery_percent.h` under the same preserved MIT license,
copyright (c) 2026 JKWTCN. Its original-Z7 addresses, pool/lifetime checks and
diagnostic phase control are local work. The fixed-text diagnostic displays
supplied text, not battery telemetry. See `Z7_BATTERY_DISPLAY_RESEARCH.md` for native rendering/restoration
evidence and the remaining feature work.

The automatic module uses the independently derived native sample policy rather
than supplied text. Its visibility, ownership, font/palette and bounded-cadence
logic are local modifications. Physical battery telemetry is still unverified.

`plugins/display_settings.c` and its header are independently written MIT code.
The configurable-page/component concepts are informed by pinned upstream
`sdk/disp.h` and `docs/custom-disp.md`, copyright (c)2026 JKWTCN under MIT.
The original-Z7 wire format is separate; no upstream configuration bytes or
native Z7II interfaces are copied. The model itself contains no native UI or
card I/O. Independent native menu adapters are described in `DISPLAY_SETTINGS.md`;
card persistence remains open.

`plugins/settings_storage.c` and its header are independent local MIT work.
Its two-slot Z7J1 journal wraps the unchanged independent Z7C1 settings payload;
it does not copy the pinned Z7II configuration format or native addresses.
The pinned upstream `sdk/config.h` (copyright (c)2026 JKWTCN, MIT) was inspected
for comparison. Its direct-file saving mechanism is not embedded here. The
current transport diagnostic is in-memory; original-Z7 file I/O, shared-state
coordination and physical durability remain separate work.

The subsequent `plugins/settings_files.c` binding and optional
`examples/display_persistence_policy.h` are independent local MIT work. Native
original-Z7 filesystem/cache interfaces, pre-publication loading, menu revision
publication and resident-worker saves are tested separately from the original
in-memory policy. Supplied filesystem/sector/task/UI boundaries and remaining
physical-card/cache/durability limits are recorded in `DISPLAY_SETTINGS.md`.

`examples/settings_menu_policy.h` is independent local MIT native-interface work
based on original-Z7 instruction/GUI observations. Native contracts were also
cross-referenced against this lab's separately licensed sound-menu component;
that component retains its community license. No sound-menu implementation or
firmware bytes are embedded in the new profile. Generated native structures,
frames, traces and binaries remain private.

`examples/display_base_policy.h` independently adapts the native-page ownership
design from pinned upstream `sdk/disp.h`, copyright (c) 2026 JKWTCN, under the
preserved MIT license. Original-Z7 selector/setter interfaces, conditional
snapshot handling, error rollback, foreign-write handling and audits are local
work. This remains an independent modified prototype, not an upstream release.

`sdk/gui.h`, the after-GUI host wrapper, `examples/gui_update_probe.c` and their
audits are independent local MIT interface/validation work. The need for a pass
after the complete native update is informed by pinned upstream
`plugins/histogram_horizon_ram.c`, copyright (c)2026 JKWTCN under MIT. No Z7II
addresses or implementation bytes are embedded in the original-Z7 wrapper.

`examples/display_histogram_policy.h` adapts the guarded extra-pass sequence,
temporary mask placement, scale calculation and synchronous painter restoration
from pinned upstream `plugins/histogram_horizon_ram.c` at
50a22b24c50619cffa646dac386e8334659f475a, copyright (c)2026 JKWTCN, under the
preserved MIT license. Original-Z7 addresses, mask banks, state ownership,
sample clearing/overflow handling, explicit retirement and audits are independent
local modifications. This experimental port is an independent modified work.

`examples/display_groups_probe.c` and the six-group additions to
`examples/display_readouts_policy.h` independently extend the pinned upstream
`sdk/disp.h` information-group concepts under the preserved MIT license.
Original-Z7 widget identities were derived from original updater execution and
private native-icon inspection: shooting5, release51 and focus2. Z7II release3
and focus6 identify different original-Z7 content and are not reused. The native
identity/mask audits and private pixel-check adapter are independent local MIT
validation tools. Firmware resources and decoded native icons remain private.

The six-group custom-page eligibility rule also adapts pinned `sdk/disp.h`'s
per-LCD-bank standard-photo permission seed under the preserved MIT license.
The original-Z7 independently seeded normal/alternate operation bits, nonzero exposure-format preservation, conditional
ownership/restoration and native instruction/pixel validation are independent
local modifications, not an upstream or Nikon release.

`examples/display_other_probe.c`, `display_other_bindings.h` and the associated
identity, policy and pixel audits extend that independently modified MIT adapter.
The Other-information grouping concept comes from the same pinned JKWTCN
`sdk/disp.h`; original-Z7 widget identities, shared-format warning preservation
and 64-bit conditional ownership are local work. Firmware resources, native
icons, screenshots and generated packages remain private. Nikon's public display
reference is used only to cross-check label meanings, never native widget IDs.

The ADL repaint and focal-native audits are independent local MIT instruction
fixtures. They identify original-Z7 native contracts without incorporating
firmware bytes or decoded resources. The focal target is informed by pinned
JKWTCN `sdk/focal_length.h` under the preserved MIT license; no Z7II addresses
are substituted into an original-Z7 implementation.

`plugins/focal_sample.h` and its diagnostic independently bind the original-Z7
native lens producer/property getter. The pinned focal feature's type filtering
concept is adapted under the same preserved MIT license. libgphoto2's public PTP
definitions were consulted only to identify the protocol property and units;
no libgphoto2 implementation is incorporated in these MIT sources.

The optional focal overlay uses independently derived original-Z7 native object,
label, font and GUI bindings. Its transparent-clear/native text-object pattern
builds on this component's existing MIT battery overlay, which preserves JKWTCN's
copyright and license. Independent object ownership, native-state invalidation,
bounded repaint/retry and original-Z7 validation are local modifications. This
is an experimental modified profile, not an upstream or Nikon release.

The native focal-layout audit and horizon frame-stability diagnostics are
independent local MIT validation tools. They incorporate no firmware bytes or
decoded resources; firmware, generated binaries and screenshots remain private.

The original information-app registry/entry/admission audit is independent local
MIT work. Its original-Z7 bindings and failure cases are derived independently;
no Z7II application index, callback address or firmware bytes are substituted.

Photo-highlight parameter conversion and owned-request concepts are informed by
the pinned JKWTCN `sdk/photo_zebra.h` under the preserved MIT copyright/license.
Original-Z7 routing, property/packet/request bindings, API52 filtering and native
update notices, epoch identities, workspace reservation and validation are local
independent modifications. Development profiles are not Nikon or upstream releases.
Firmware, generated images, native dumps and camera screenshots remain private.
