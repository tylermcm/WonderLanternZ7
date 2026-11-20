# Independent original-Z7 module research

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
