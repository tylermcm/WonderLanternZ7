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

`examples/battery_display_probe.c` adapts the transparent-rectangle preparation
from upstream `sdk/battery_percent.h` under the same preserved MIT license,
copyright (c) 2026 JKWTCN. Its original-Z7 addresses, pool/lifetime checks and
diagnostic phase control are local work. It displays supplied text, not battery
telemetry. See `Z7_BATTERY_DISPLAY_RESEARCH.md` for native rendering/restoration
evidence and the remaining feature work.
