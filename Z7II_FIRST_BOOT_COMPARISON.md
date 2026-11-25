# Upstream first-boot fix comparison — November 24, 2026

Inspected JKWTCN's [hardware-verified first-boot host patch](https://github.com/JKWTCN/z7ii-extensions/commit/e9879e077028b20fc799b9bc13f7e585b71e9f32).
Upstream reports missing extension menus and incorrect framing grids after
battery reinsertion. That hardware claim applies to its Z7II target.

The patch addresses two mechanisms:

- Its master reset path bypasses scatter loading. The direct initialized-data
  copy must also cover eight alignment bytes used by the upstream host. The
  patch adjusts the direct copy and scatter/BSS handling together.
- A successfully opened module may still have an incomplete or failed read
  during startup. The loader worker retries that failure after a successful
  close, within its existing attempt limit. A failed close stays terminal.

## Original-Z7 assessment

Our fixed-address host has no BSS: its linker asserts that explicitly. The
workspace hook clears its reserved state before native allocations. The module
preparer separately zeroes each loaded module's BSS. The host does not reserve
the upstream's eight alignment bytes or modify its startup-copy records.
The upstream padding edit therefore cannot simply be applied to this memory
layout or to original-Z7 addresses.

Our worker did share the stop-on-read-failure policy. An optional
`Z7_HOST_RETRY_READ_FAILURES` implementation adapts the upstream retry rule using
the existing original-Z7 loader, status values, native wrappers and close guard.
It retains the 100-attempt limit and 100 ms backoff. Invalid modules, failed
initializers, invalid sizes and uncertain closes are not retried.

Build it privately with:

```powershell
.venv\Scripts\python.exe tools/build_z7_module_host.py --display-hooks --retry-read-failures --output .private/builds/NEW-read-retry
```

This generates emulator research files only. **No update container, installation
clearance or camera flash is provided.** The installed host remains unchanged.

## Evidence and the current name-label bug

The [scoped report](evidence/20261124-upstream-host-read-retry.json) records 41
compiled checks over eight worker scenarios: transient errors, transient short
reads, permanent errors, read plus close failure, missing file, invalid size,
invalid module and initializer failure. Counts, bounded delays, closes, allocation
cleanup and terminal uncertain-close handling pass. Native loader/wrapper code
executes with supplied filesystem, task and allocator boundaries. All 103 root
tests also pass. Rebuilding the default profile remains byte-identical to the
installed-equivalent MAIN hash `24b2074559ca6089432011d98a72193f81e112c2621aee2aa0ed1359febfa7ce`.

A visible **h** shows that the module itself loaded; a missing name after that
is not explained merely by failure to read the module. The latest read-only
card identification found the older e377 category module, not the newer 5e62
[GUI label/cache repair](LCD_SETTINGS_LABEL_REVIEW.md). Thus the reported symptom
does not yet establish failure of that newer repair. It requires a separate
owner cold-start check. No host update is needed to test that SD-only repair.

The retry adaptation remains an independent offline improvement. These checks
do not establish actual cold-start behavior, card durability, safe firmware
installation or emergency recovery on the original Z7.
