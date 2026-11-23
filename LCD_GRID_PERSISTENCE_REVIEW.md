# LCD grid-shape save/restore checkpoint - November 22, 2026

The owner confirms the startup 4x4-to-3x3 swap is absent on the current eae52b49
module. The reported reset to 3x3 happens only after a shutdown of about ten
seconds, while a short off/on can retain the shape. This matches the existing
RAM-only grid design; it is not a reported same-session selection regression.
The camera's exact short-shutdown retention mechanism remains unverified.

This independent original-Z7 C 3.80 checkpoint adds grid shape to saved display
preferences and retains the owner-tested startup invalidation change. The card
and installed firmware were not accessed or changed during this offline work.

## Exact candidate

Z7APP.BIN: **21,560 bytes**, SHA-256
`f848e62de232776a27fef9f481452d590901ff5fb95de2c564fe6e46611cc00e`.
Source: `plugins/lcd_grid_persistence_checkpoint.c`.
Private source-fingerprint build: `.private/builds/20261122-lcd-grid-persistence-02`.
It matches the tested `-01` packet byte-for-byte after a codec comment update.
Frozen review: `.private/review/20261122-lcd-grid-persistence-01`.

Preserve the current 21,360-byte owner-tested startup module, SHA-256
`eae52b4946ad375c3eacbe98cd61054a8eb9d94a402764fac85958f01aa3eda2`.
The old profile independently rebuilds to the identical packet; grid persistence
is opt-in. No host changes or new firmware update are required. Required host
MAIN SHA-256 is `24b2074559ca6089432011d98a72193f81e112c2621aee2aa0ed1359febfa7ce`,
inferred from the earlier approved successful update rather than camera readback.

## Storage and ownership contract

The selected shape, values 1..5, is appended to the coherent GUI-owned settings
model. Payload version 3 uses word56 of the existing 64-byte Z7C1 packet and
requires word60 zero. It is separate from the deferred version2 highlight
profile. The unchanged 80-byte Z7J1 generation/CRC wrapper alternates two files.

**New writes target only `A:\Z7DSP0.DAT` and `A:\Z7DSP1.DAT`.** Neither legacy
`Z7CFG` file is written. If both new paths are confirmed absent, startup reads
the older slots as a read-only fallback, preserving their preferences with a
default 3x3 shape. Startup itself does not migrate compatible legacy settings.
After a shape/menu edit, the worker saves the new model into the new slots.
When a valid new record exists, it owns the complete display preference model;
legacy files are no longer opened or synchronized during that startup.

Grid selection publishes the shape without file I/O. The existing bounded
revision reader and worker debounce save it. The loader restores module RAM
before host readiness. Native grid storage continues receiving ordinary Off/On
only, with no native settings schema extension. Off retains the last shape;
native visibility remains separately owned by the normal Nikon service.
Existing native legacy values2..5 retain read compatibility until an explicit
shape choice normalizes native storage to boolean On, as in the working module.

Existing invalid/unknown new records with no valid selected record block saving
instead of falling back to defaults/legacy and overwriting them. Read errors,
ambiguous serials and uncertain-close behavior retain the existing safeguards.
The temporary legacy path selector is loader-only and cleared before native
GUI publication and worker availability. This is not a concurrent path switch.

## Offline validation

- 152 actual-module checks: all five shapes save and cold-reload, independent
  v3 byte/CRC/generation comparisons, alternating slots, no automatic migration,
  old-file preservation, battery/menu edits retaining shape, invalid codec
  inputs with unchanged output, corrupt/unknown new records, read/create/short
  write/close errors and retry behavior. Every observed write targets a new slot.
- 262 grid/storage assertions and 450 geometry comparisons still observe only
  native setter values0/1, including menu selection and EVF/movie fallback.
- 15 native menu-status checks; actual odd-store publisher interruption with
  four bounded separate-stack worker reads and later completed save.
- Reproducible build and independent exact scan of 84 ELF-bounded functions:
  zero exclusive instructions and 19 DMB instructions. Native callees excluded.
- 101 root regression tests pass. Graphify refreshed; conditional-C extraction
  gaps remain. Source fingerprints and complete report hashes are frozen.

These fixtures supply filesystem, GUI, property and scheduling boundaries.
They do not establish physical shutdown durability, pixels, all capture/output
lifecycles or camera recovery. The new profile has not been hardware tested.

## Installation, preservation and rollback assessment

After owner approval, identify the same card and require active eae52b49. Require
both `Z7DSP` paths absent for this first test; preserve and review them if either
already exists. Privately back up all named modules, updaters, seed and both
legacy journals. Verify a valid unambiguous LCD-compatible selected legacy record
so startup need not filter older unsupported settings. Preserve every file.

Rename the working module to unused `Z7APP.LCD-STARTUP-WORKING.disabled` and
exclusively create the candidate at `Z7APP.BIN`. Flush/full-readback verify it,
check unchanged prior contents/size/mtime/catalog through that rename, and safely
eject. Keep all update files disabled. No seed, legacy journal or updater write.

If the candidate fails, stop. Privately back up any new records, disable/preserve
the trial module and restore the exact working eae52b49 module with full readback
and safe eject. Keep the new `Z7DSP` files intact; the older working module ignores
them and uses its unchanged legacy `Z7CFG` preferences. Those older preferences
may differ from edits made in the new profile. Reenabling the new profile prefers
its new records; the two profiles do not synchronize settings automatically.
Earlier card/battery isolation recovered prior trials, but exact-candidate
recovery and physical abrupt power-loss durability have not been established.

## Proposed first owner test

Start normally, **never Update**. Select only Center cross in Framing grid
display. Open Display settings and wait for Saved. Leave other preferences
unchanged. Power off normally and leave it off at least20seconds, then restart.
Check that Center cross returns, observe startup for any brief wrong-grid swap,
and check controls and normal power-off. Stop/report a stall or save error.
Return the card for read-only backup/CRC/generation inspection before another
shape or preference change. Do not intentionally interrupt a save or pull power.
