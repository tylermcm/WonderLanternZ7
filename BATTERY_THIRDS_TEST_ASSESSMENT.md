# Battery plus 3x3 grid: next SD test assessment

November 21, 2026. Independent WonderLanternZ7 checkpoint for original Z7 C 3.80.
Prepared for owner review; no card staging or camera test authorized yet.
Component MIT licenses and battery attribution remain intact.

## Exact candidate and behavior

`Z7APP.BIN`, 3,160 bytes, SHA-256:
`78af00b6fb9dd2cb29c2d391e1ce36412a25bd771a9f56ce02fdcd1e8ebadc91`.
Image 3,072 bytes, BSS 156 bytes, six relocations. Built twice identically.
Runs on the already-installed API44 host; no firmware image/update required.
Reviewed host MAIN hash:
`7d7356e7775db90483ed9fe5598f401afb7fb8498a7b42bd71900db849d7f057`.
Installed-image identity is inferred from prior installation, not camera readback.

Keep the hardware-tested battery overlay unchanged. Add only a grid-table hook:
when Nikon's existing Framing grid display is On (native value1), rear-LCD photo
view uses two lines per axis, a 3x3 grid. Off retains the stock off path. EVF,
movie mode, and other stored grid values use the stock table. No new grid choice
or settings menu is installed. Native On/Off can be changed normally by the owner;
the module does not write that setting or add any persistence service.

Only grid-source and battery before/after-paint callbacks are registered. There
are no custom grid-menu pointers, event-dispatch replacements, key intercepts,
histogram-mask edits, settings journals, resident workers, or DISP/readout hooks.
This does not contain the withdrawn ownership patch or the failed full module.

## Validation and limits

The exact installed-host instruction fixture passes 110 boundary/geometry checks:
no native GUI/settings stores during initialization; unchanged native menus,
dispatcher, keys and histogram masks; no pre-ready battery work; native On/Off
and other scalar values unchanged; stock fallback for Off/EVF/movie; owned table
differs only in six line-count fields; foreign table schema fails initialization.
The actual native geometry builder gives thirds spacing and preserves viewport
extents/style/offset relationships across 3 viewports, 3 modes and 5 crop inputs.
The existing battery policy audit passes 38 checks for this exact combined build.
Root suite and graph results accompany the frozen review.

Kernel/filesystem, incoming GUI/telemetry, viewport/crop and selected rendering
services remain supplied. No physical grid pixels or new-camera startup/recovery
are proven. The battery-only module passed one owner startup/control/power-off
check; the full module and settings-disabled diagnostic froze. A different module
changes load timing; success here would not identify the earlier freeze cause.
This candidate could still freeze. Full LCD release remains withdrawn.

## Proposed staging after fresh explicit approval

Camera OFF; connect card to reader. Reidentify the same external card. Privately
back up/hash the active working battery file, four disabled trials and named
configuration files. Require active `Z7APP.BIN` to match the known working
2,824-byte battery hash:
`89358992419867380781bafae7a1624f4d51955b3920127718f6daba9318ea23`.
Verify the four disabled hashes recorded in the battery-only assessment.
Require EG161080.BIN absent and no unexpected active root `.BIN` files.

Require `Z7APP.BATTERY-WORKING.disabled` and `Z7APP.BATTERY-THIRDS.disabled` absent.
Stop on any collision, changed hash or identity mismatch; do not overwrite.
Rename the working `Z7APP.BIN` to `Z7APP.BATTERY-WORKING.disabled`, preserving its
bytes. Exclusively add only the new exact candidate as `Z7APP.BIN`, flush/fsync,
read back and hash. Verify all existing metadata/catalog except authorized rename,
then safely eject and verify inaccessible card media. No deletions, format, EG
reenable, or firmware flash. Preserve the working baseline and all previous files.

## One owner check

1. Camera OFF: insert card, turn on normally. Do NOT run Update.
2. Rear-LCD photo live view: confirm percentage remains visible and controls work.
3. Open the native Framing grid display setting. Choose On: expect two horizontal
   and two vertical grid lines (3x3). Choose Off: expect no grid. Do not look for
   a new menu item. Report the original setting if it used a different value.
4. Check MENU/touch and normal power-off. Stop this first trial here: no capture,
   movie, EVF/output switching or extended lifecycle test is included.

Report percentage, grid On/Off behavior, responsiveness and normal shutdown.
No grid with normal controls is inconclusive; do not repeatedly restart or enable
other payloads. A pass is scoped to this test, not full-release acceptance.

## Stop/recovery and file preservation

If frozen, stop the test. Card removal previously restored controls; an unresponsive
power switch previously required battery removal. If normal power-off is impossible
in this ordinary-startup test, use the previously used battery-removal method to
shut down, remove the card before restarting, and report symptoms. Recovery for
this exact candidate remains physically unverified; no guarantee is claimed.

Return card to reader. Verify and rename the failed candidate to
`Z7APP.BATTERY-THIRDS.disabled` only if destination is absent, preserve all bytes,
verify metadata/catalog and safely eject. Do not automatically restore another
active module or run a firmware rollback. The working battery-only file stays
preserved for an explicitly agreed restoration. Disabling the module does not
remove the installed modified host. Emergency firmware recovery remains unverified.

This assessment alone does not authorize staging or a hardware trial.
