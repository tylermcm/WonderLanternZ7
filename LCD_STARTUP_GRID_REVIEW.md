# LCD startup redraw comparison - November 22, 2026

This independent original-Z7 C 3.80 module is an offline comparison candidate.
The owner reports a brief 4x4-to-3x3 grid transition only at startup with Custom
pages ON; persistence and ordinary DISP cycling work. The visible transition
has not been reproduced offline or established fixed by this change.

## Exact change

When Custom pages first acquires native page ownership, the existing code
invalidates the native display snapshot even if grid visibility is already ON
and the native base page is unchanged. The instruction fixture observes one
invalidation with master ON and zero with master OFF in that unchanged case.
The earlier stable grid-source fixture always selects thirds once ready.
Neither observation alone proves which frame the physical display presents.

The optional `Z7_BASE_INITIAL_GRID_DELTA_ONLY` branch removes only that initial
grid-ON invalidation. Initial grid suppression and later visibility changes
still invalidate; actual native base-page and readout-mask changes independently
request invalidation. It adds no delay, file operation, worker operation, native
setting write, early callback publication or renderer hook. It leaves the
host's readiness and native first-frame scheduling unchanged.

Important boundary from the broader test: with initially unmodified native
information masks, those masks also change and both baseline and candidate
still request one initial redraw. With masks already matching the preset,
fresh grid ownership requests one redraw in the baseline and none in the
candidate. This isolates the redundant contribution; it does not demonstrate
that eliminating it removes the owner's cold-start transition. The hardware
comparison may show no visible difference.

The change is enabled only by `plugins/lcd_startup_grid_checkpoint.c`.
The owner-working persistence module remains byte-identical at 21,296 bytes,
SHA-256 `88b53ce46ae816b634c249cfe011f05a501f2619447d9c156e2828c2cf82a71e`.
Its refreshed source-fingerprint build is
`.private/builds/20261122-lcd-persistence-baseline-rebuild-01`.
Older frozen reviews retain their original source fingerprints and history.

Candidate: **21,360 bytes**, SHA-256
`eae52b4946ad375c3eacbe98cd61054a8eb9d94a402764fac85958f01aa3eda2`.
Private build: `.private/builds/20261122-lcd-startup-grid-01`.
Frozen review: `.private/review/20261122-lcd-startup-grid-01`.
Requires the existing owner-tested task-worker host, MAIN SHA-256
`24b2074559ca6089432011d98a72193f81e112c2621aee2aa0ed1359febfa7ce`.
No firmware update or installed-image readback is part of this comparison.

## Validation scope

The exact-candidate evidence and final counts are listed in the frozen package
manifest and current HANDOFF. Checks exercise native invalidation, actual page
setters, grid geometry, LCD menu/persistence paths, native status dispatch and
exclusive-instruction absence. Native property/GUI/filesystem boundaries are
supplied. These do not model physical cached grid presentation or scanout.
The new profile retains the unchanged v1 two-slot preference journal and the
RAM-only grid-shape contract; grid shape defaults to 3x3 when native grid is ON.
The candidate passes 48 LCD menu/save/restart checks, 262 grid/storage assertions
with 450 geometry comparisons, 69 preference fault/restart checks and an exact
rebuild/83-function scan with no exclusive instructions and 19 DMB instructions.
The targeted A/B audit passes 65 checks, including initial suppression,
horizon-page changes, subsequent grid toggles and the separate already-matching
information-mask boundary. All 15 native menu-status checks also pass.
The owner-working baseline independently rebuilds to its original hash. All
101 root tests pass. Initial concurrent emulation attempts reached their 30s
wall limit in loader CRC execution; completed lower-concurrency reruns, rather
than those timed-out runs, provide the evidence in the frozen manifest.

## Preservation and recovery assessment

This candidate has not been staged or hardware tested. After owner authorization,
identify the same Sony card, verify the active module is the working 88b53ce4
packet, and privately back up all named module/updater/seed/journal files.
Record file sizes/timestamps and catalog hash. Preserve every existing file.

Read both journals without changing them. Require a valid unambiguous selected
v1 record whose settings already satisfy the LCD release filter; otherwise stop
for review, since loading an older unsupported profile can normalize and autosave.
Existing compatible saved preferences are deliberately retained for this test.
The previous absent-journal prerequisite applied to the first persistence test;
it does not apply to this comparison after verified physical journal writes.

Rename the working active module to unused
`Z7APP.LCD-PERSISTENCE-WORKING.disabled`; do not overwrite a collision. Exclusively
create only the exact candidate at `Z7APP.BIN`, flush/full-readback verify it,
check all prior file contents/metadata/catalog through the intended rename, and
safely eject. Keep the firmware updater disabled. No journal or seed rewrite.

If a stall or regression occurs, stop the trial and preserve the candidate and
any journal records on the laptop. Disable the trial module and restore the
verified working 88b53ce4 module, with full readback and safe eject. Earlier card
removal/battery isolation restored controls in other trials; exact-candidate
recovery remains unverified. Neither this module swap nor rollback changes the
installed host. Physical abrupt power-loss durability remains outside the test.

## Proposed owner comparison

Use the rear LCD and the ordinary grid ON/3x3 default. Leave other preferences
unchanged. With Custom pages ON and its title Saved, power off normally, then
start normally and observe whether 4x4 appears before 3x3. Do not run Update.
If Custom pages was left OFF, enable only it and wait Saved before shutdown.
Check MENU/touch/responsiveness, DISP cycling and normal power-off. Stop/report
any stall or save error rather than repeatedly toggling or reflashing.

Report the startup appearance even if it is unchanged. A normal boot alone does
not demonstrate the visual issue fixed. If the transition persists, retain the
bounded offline finding and investigate geometry/presentation timing separately;
do not expand into host readiness changes without new evidence and review.
