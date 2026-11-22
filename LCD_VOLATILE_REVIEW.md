# Storage-free LCD checkpoint - November 22, 2026

Prepared offline while owner is AFK. Not staged or hardware-cleared. Use only
after reviewing the next incremental hardware gates with the owner present;
leave the current working B module and installed host unchanged meanwhile.

Exact Z7APP.BIN: 17,868 bytes, SHA-256
`9b076c6db032d6b17884aadda8ec75934be9b9456655e2ef30010870d51c8592`.
Private build: `.private/builds/20261122-lcd-volatile-01`.
Requires the current owner-tested display host; no new firmware update.

## Scope

This reuses the existing compact LCD profile: four DISP presets, supported grid
and native horizon controls, information groups, battery percentage and focal
display settings. It omits persistence entirely. No settings files are loaded,
created or written and no worker is registered. The old journal files are ignored
and preserved; settings reset to supported defaults each boot.

Custom pages and battery percentage start OFF. This may initially look like
stock behavior. The expected configuration entry is Framing grid display →
Display settings. Compact root controls are Custom pages, Standard, Minimal,
Composition, Exposure and Battery percentage. Unsupported histogram/highlight/
custom-Info controls remain filtered out, including after resetting a preset.
Movie, EVF and menu-context native DISP fallbacks remain part of the software
contract; physical output/capture/lifecycle behavior is not established here.

## Future incremental camera observation

After explicit approval, identify/back up the card and preserve whichever
working progress/B module is active under an unused disabled name. Exclusively
create this exact Z7APP.BIN, flush/full-readback verify it, verify other named
contents/file size/mtime/catalog and safely eject. No updater or seed/config
write belongs in this test. Stop on unexpected active contents/name collisions.

First normal start and inspect only: controls/power-off should work; locate the
Display settings row and compact menu, without enabling several features at once.
Record this first result. Later owner-guided steps can toggle battery percentage,
then Custom pages and one preset feature at a time. Preferences intentionally
reset after a power cycle; a reset is expected rather than a failed save.

Do not select any retired EX/LX probe, run Update, activate the persistent LCD
build, or treat offline success as physical readiness. If it stalls, stop and
report the trigger. Prior card/battery isolation recovered other SD-module stalls,
but exact-candidate recovery is not guaranteed. Preserve/disable a failed module
on the laptop before further experiments.

## Evidence

Reproducible build; independent rebuild and all 68 ELF-bounded function ranges
scanned with no exclusive instruction found. 44 supplied-service checks cover
supported defaults, compact controls/actions/reset/filtering, no registered worker,
no settings file operations, unchanged persistent menu-dispatch slot, journal
ignore/fresh reset, native DISP preset cycling/skipping and context fallback.
Module-loader cache maintenance is distinguished from settings-file operations.

The default persistent builds were independently rebuilt afterward and remain
byte-identical to their already-tested versions; this optional mode does not
change their default code. Root tests pass. No complete native visual or shooting
lifecycle, sensor/focal accuracy, cache/durability or camera recovery validation
is claimed. Private evidence: `.private/evidence/20261122-lcd-volatile-01.json`
and `.private/evidence/20261122-lcd-volatile-instructions-01.json`.
