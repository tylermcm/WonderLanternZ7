# Combined LCD photo highlights integration

This independent original-Z7 lab profile combines photo highlight stripes with
the saved LCD display release: grids, histogram, horizon, information groups,
focal length, battery and optional native Information display. It builds on the
credited MIT JKWTCN photo-zebra design and the existing original-Z7 API72 native
warning transaction implementation. This is an offline integration checkpoint.

## Exact build and host boundary

- Build: `tools/build_z7_lcd_volatile.py --photo-highlights`.
- Private `Z7APP.BIN`: 33,364 bytes, SHA256
  `aa56f2b87aedeeafbc74f57a0285d3a753ae123773908cac6a53d4a6aea6c959`.
- Requires API72 with native warning, frame and parameter transaction hooks.
- **Incompatible with the installed API44 host. Do not stage this module on the
  camera.** The audit verifies rejection before GUI publication on that host.
- Offline host MAIN SHA256:
  `f77f0ced784403ffe99bd413c1ce71c07ecbd6a94e25c19919cb55a80c175b7c`.
  This host has not been cleared for installation by this checkpoint.
- The prior Information-page profile remains byte-identical at `cec4c39b...`.

Each preset now exposes Photo highlights. Its submenu has Show on this page,
Pattern (all pages), Threshold (all pages) and Back. The global pattern defaults
OFF; choices are OFF, Type 1 and Type 2. Threshold choices are 255, 248, 235, 224,
213, 202, 191 and 180, default 248. Global OFF retains page choices and threshold.
This integrated profile enables the existing LCD path; EVF and portrait parity
remain separate work.

## Combined settings and preservation

The wire payload remains 64 bytes inside the existing 80-byte journal envelope.
Version 4 stores grid shape at payload offset 56 and packs pattern in bits 0..1
and threshold index in bits 2..4 of offset 60. Other bits are reserved and must
be zero. Pattern 3 and out-of-range grids are invalid. The in-memory model has
13 words. A damaged or unsupported payload is rejected before output changes.

Version-1 migration uses 3x3 and highlights OFF/248. Version 2 retains its explicit
highlight pattern/threshold and uses 3x3. Version 3 retains its grid shape and
defaults highlights OFF/248. Existing display and information selections remain.

New writes go only to `Z7EXT0.DAT` / `Z7EXT1.DAT`. With both absent, the loader
tries `Z7DSP0.DAT` / `Z7DSP1.DAT`, then legacy `Z7CFG` if both DSP slots are absent.
Existing invalid or unknown records block silent fallback and saving over them.
I/O failure also blocks saving. The loader resets its path selector before GUI
publication; GUI edits never write files. Merely loading a legacy record does
not write a migrated copy. A later edit saves only to the new namespace.

Rollback modules continue reading their prior DSP/CFG journals and therefore
retain their previous preferences; newer choices are separate. All namespaces
still need a private backup before any future owner-authorized installation.

## Verification

The reproducible candidate passes 828 combined checks: all 120 grid/pattern/
threshold combinations against an independent wire encoder, 512 single-bit
corruptions, reserved-field and legacy migration cases, exact submenu labels and
row count, all 16 enabled native pattern/threshold paths, plane programming,
global-OFF restoration, v4 reload, v3 migration and older-namespace preservation,
unknown-record protection and installed-host rejection. The root suite passes
103 tests. The preceding API44 Information candidate rebuilds identically.

The actual native converter, consumer, warning gate and driver execute with
supplied GUI state, filesystem, palette, surfaces, engines, MMIO storage and task
handoff. These checks do not establish physical stripes, complete scheduling,
native task wait graphs, camera cold startup, long-term stability or recovery.
No new native-key QEMU raster or hardware image is claimed for this profile.

## Remaining installation work

There is no installation approval or recovery clearance for this host/module
pair. A future assessment must independently rebuild and inspect the exact host
and update container, compare its hooks against the installed host, preserve
camera/card files and identify an exact rollback plan before requesting a flash.
Earlier card/battery removal recovered prior failures; that does not establish
recovery from an API72 host update. Emergency recovery remains unverified.
