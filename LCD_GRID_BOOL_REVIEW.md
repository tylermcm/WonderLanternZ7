# LCD grid storage policy revision - November 22, 2026

Prepared offline after the owner-tested storage-free LCD menu/toggle trial.
No card mutation, firmware update or new hardware trial has occurred. The
current working module9b076c6d... remains active until this revision is approved.

Owner reported navigating all settings, enabling two initially OFF settings,
normal speed/responsiveness and normal power-off, with no observed detriment.
Custom pages and Battery percentage are inferred from their defaults, not
individually named by the owner. Actual grid-layout selections remain unknown;
do not claim a full feature-by-feature or pixel-accuracy pass.

## Exact candidate

Z7APP.BIN: 18,060 bytes, SHA-256
`8ec66cea22ebf33755944591351d7d7f4c728e361af2b2bd7794323a72ef52ea`.
Private build: `.private/builds/20261122-lcd-volatile-grid-bool-01`.
Requires the current owner-tested host; no new firmware flash.

The existing LCD profile sent layout numbers1..5 to the native0x102d grid
setting. The diagnostic comparison executes the old packet and observes dense
selection's native setter argument5; this is not evidence of a hardware failure
or a physical flash write. The revised storage-free profile instead reuses the
working small-grid policy: selected layout stays in module RAM, while native
selection receives only ordinary Off0/On1. Nikon's normal native setting service
still owns saving that On/Off flag; there are no module settings-file operations.

When the native flag is1, layout starts as3x3 each boot. Older extended values2..5
are read-compatible: the module renders/marks that legacy layout without rewriting
the native value at startup. The next explicit layout selection stores only0/1
and uses its RAM layout. There is no automatic migration or guessed native RAM
address change. Other values follow the existing native fallback. EVF/movie
geometry stays native; golden-ratio geometry is adjusted only on photo LCD.

The four compact DISP presets, information/horizon/battery/focal controls and
settings-reset-on-boot behavior remain. No worker or settings file adapter is
registered. Custom pages and battery percentage initially start OFF. This
revision is limited to the storage-free profile; it does not clear the persistent
LCD candidate's grid storage/persistence contract for hardware use.

## Checks

- Reproducible build and independent exact rebuild.
- 262 grid/storage assertions, including all five choices and Off, actual native
  On/Off setter path, RAM choice, seven-row menu/selection, 450 actual/reference
  geometry calls, EVF/movie fallback and legacy read/next-selection behavior.
- Native setter arguments observed in the revised test are only0 and1.
- 44 storage-free compact menu/default/action/reset/DISP/context checks pass.
- All68 ELF-bounded module functions scanned; no exclusive instruction found.
- 101 root tests pass. Existing A/B, progress and read-only restore packets
  rebuild byte-for-byte unchanged; their refreshed source-fingerprint builds
  are saved separately. Installed host sources remain unchanged.

Native storage/UI/viewport inputs are supplied fixture boundaries. No physical
grid pixels, capture lifecycle, write durability or exact-candidate recovery is
established. The earlier owner-tested LCD packet remains a scoped live baseline.

## Proposed next owner test

After approval, identify/back up the same card. Require active module9b076c6d...
and preserve it under an unused Z7APP.LCD-VOLATILE-WORKING.disabled. Keep all older
working/failed files, seed, journals and updaters intact. Exclusively add this
exact candidate as Z7APP.BIN; flush/full-readback verify, verify unchanged earlier
contents/size/mtime/catalog, then safely eject. No seed/config/updater write.

Start normally, never Update. First confirm the compact menu and normal controls.
Then select3x3, Center cross and6x6 one at a time, observing the rear-LCD grid and
menu selection after each. Check Off, then re-enable one layout. Report actual
behavior and normal power-off. Settings/layout are deliberately volatile; do not
expect custom preferences to survive restart. Keep unsupported modes outside
this first hardware observation.

If a stall occurs, stop, report the trigger and do not repeat. Prior SD/battery
isolation recovered other trials, but this exact candidate's recovery is not
guaranteed. Preserve/disable it on the laptop before another test. No full
persistent profile or automatic settings write is authorized by this review.

Private evidence: `20261122-lcd-volatile-grid-bool-01.json`,
`20261122-lcd-volatile-grid-bool-ui-01.json` and
`20261122-lcd-volatile-grid-bool-instructions-01.json` under `.private/evidence/`.
