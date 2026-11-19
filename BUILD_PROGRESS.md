# Autonomous original-Z7 module and display work

The owner asked on November 19, 2026 to keep building while they are at work.
Continue autonomously within the selected order: SD-loaded modules, then display
features. The active goal remains open until the software work and relevant
validation are complete. Do not stage or flash a camera without explicit owner
authorization and a concrete exact-candidate installation/recovery assessment.

## Completed

- Original-Z7 package identity, bounded ELF packer and native C relocation core.
- Private pinned ARM/Thumb compiler, actual compiled C probe module.
- Original-Z7 boot/task/filesystem/cache host with guarded stock hooks.
- 99 compiled-Thumb instruction checks, 34 original/root regression tests.
- Native-kernel assisted-QEMU no-file startup, 100 bounded retries, seven checks.
- Successful module loading/initialization in assisted QEMU using an explicit
  read-only filesystem-dispatch fixture; nine checks including the C probe's
  BSS marker in native heap memory. Task scheduling, allocation, cache instructions
  and initializer execution remain native guest code. This is not real-card I/O.
- Five new tests cover fixture ownership, buffer bounds and unrelated-request
  pass-through. Successful run: `.private/evidence/20261119-module-host-qemu-load-04/`.

## Next implementation

1. Add a staged, owned display-hook API. An initializer failure must never publish
   a callback into freed module storage. Absent modules retain stock behavior.
2. Port grids and histogram/horizon as the first display controls, using the
   existing independently mapped Z7 paths, not copied Z7II addresses.
3. Continue the display work in `SD_MODULE_PORT.md`: custom DISP, focal length,
   battery percentage, photo zebras and portrait layout. Independently derive
   native interfaces, test failure/restoration paths, and keep uncertain features
   clearly separate from proven ones. The old spiral's EVF lag remains unresolved.
4. Complete reproducible builds, scoped instruction/QEMU checks, visual inspection
   where relevant, source-only evidence, handoff and ignored graph refresh.

## Current boundaries

No physical camera or card access, staging, flashing or public push is authorized
by this autonomous continuation. Firmware/BINs, dumps, keys, camera frames,
toolchains and raw traces remain ignored/private. Recovery and actual card/cache/
wake behavior are unverified. Capture pre-buffering, AF, Wi-Fi and recording-limit
ports are outside the selected display-first implementation sequence.
