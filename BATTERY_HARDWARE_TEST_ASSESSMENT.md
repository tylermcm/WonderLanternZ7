# Battery-only SD hardware test assessment

**Owner-reported PASS for the scoped startup/control test.** Numeric percentage
visible; MENU, touch and normal power-off confirmed working. This demonstrates
module/GUI execution for this exact candidate. It does not clear the full LCD
release, establish battery accuracy, or identify the previous freeze cause.
Current working battery-only card file stays active; no further change authorized.
See evidence/20261121-battery-hardware-result.json. Preapproval material below
and frozen bundle remain historical; this result supersedes pending status.

Owner subsequently approved "yes". Exact candidate is now staged as Z7APP.BIN,
readback/hash verified and safely ejected. All four disabled originals, existing
settings/file metadata and Nikon catalog are preserved. No firmware update.
The owner observation is now recorded above. The frozen
preapproval bundle stays unchanged; this note supersedes its approval status.

November 21, 2026. Prepared for owner review; NOT staged or authorized to run.
Independent WonderLanternZ7 work for original Nikon Z7 C 3.80. Component MIT
licenses/notices retained. This is a diagnostic checkpoint, not the LCD release.

## Exact scope and artifact

Use the already-installed display host. Do not run Firmware version > Update,
copy an EG image, restore the failed full module, or enable any other trial.
The installed host is inferred from the prior owner-reported successful update;
there is no physical installed-image readback.

Candidate: battery percentage only, enabled, `Z7APP.BIN`, 2,824 bytes.
SHA-256: `89358992419867380781bafae7a1624f4d51955b3920127718f6daba9318ea23`.
Image 2,752 bytes, BSS 56 bytes, two relocations, entry offset zero.
Minimum API 16 bytes; tested against the existing API44 display host MAIN hash
`7d7356e7775db90483ed9fe5598f401afb7fb8498a7b42bd71900db849d7f057`.

Only before/after-paint callbacks are registered. There is no custom menu,
grid registration, key interception, settings journal or resident worker.
No code/data from the withdrawn ownership patch is included. Initialization
performs no native GUI RAM stores, battery getter calls or rendering in the
instruction fixture. Native battery sampling/rendering begins on eligible GUI
callbacks, behind the existing host-ready and module context guards.

The percentage requires a supported native battery snapshot and visible battery
HUD in landscape photo mode on the rear LCD. It uses the existing overlay's
native label/pool ownership checks. It does not add a new text or menu marker.

## Evidence and limits

Both enabled and disabled packages were independently built twice with identical
bytes. The disabled control is retained privately and will not be staged.
The existing battery policy audit passes 39 checks, including enabled rendering,
disabled no-op, sample validation, context exclusions, ownership and retirement.
The new exact-host boundary audit verifies no native GUI mutation during load,
no early-host callback effects, no sampling with a missing HUD pool, unchanged
menu/grid/key pointers, and a visible `63%` label for supplied eligible telemetry.
Root test and source-graph results are recorded with the frozen review evidence.

These tests supply kernel/filesystem services, GUI/telemetry/mutex state and
selected rendering services. They do not prove physical cold startup, percentage
accuracy, camera responsiveness, or recovery. Prior full and settings-disabled
modules froze the camera despite passing software checks. This candidate could
also freeze. A percentage appearing is evidence that this module and its GUI
callbacks ran; normal controls without that marker remain inconclusive.
This smaller module also changes card-read timing. A pass would not prove that
menu code caused the earlier freezes or rule out a timing-dependent loader fault.

## Installation plan after fresh explicit approval

With the camera OFF, connect its card to the reader. Verify the same external
card identity and privately back up/hash all named trial/configuration files.
Verify the four preserved payloads:

| Preserved name | SHA-256 |
| --- | --- |
| `Z7APP.BIN.disabled` | `aafb4b392203589e7dabc244d1d1e4b40a2c02023013621d9fc393328eb60e22` |
| `EG161080.BIN.disabled` | `fa709dba7eb7a9addc8bd5b90f839edd578cfb6d4bb0df87a1cd8cb4a7beaa4d` |
| `Z7APP.NOINIT.disabled` | `ecba70f7e93974cda15f7515c2747a06c2ed1c77731cc60fac2cbc8b95c77cdc` |
| `Z7APP.SETTINGS-IO.disabled` | `69921c4efc2b2395c76b969499cdf9f78d77ef675017acc2d5130365fbbf63e0` |

Require no active root `.BIN`, no existing `Z7APP.BIN`, and no preservation-name
collision. Stop on any identity/hash/name mismatch; do not overwrite or delete.
Exclusively add only the exact candidate as `Z7APP.BIN`, flush/fsync, read back
and compare bytes/hash. Verify existing file metadata and Nikon catalog hash,
then safely eject and verify no accessible card media. Preserve photos and all
trial files. No firmware update, format or automatic settings-file changes.

## One owner test

1. Camera OFF: insert the safely ejected card, then turn it on normally.
2. Check controls and rear-LCD photo live view. With the native battery indicator
   visible, look for a numeric percentage. Allow up to 30 seconds; do not loop
   restarts, enable other trial files, or run Update if it does not appear.
3. If responsive, open/close MENU and check touch, return to photo live view,
   then turn the camera off normally. No capture, movie, output switching or
   extended feature/lifecycle test is part of this first check.
4. Report percentage present/absent, responsiveness and whether normal power-off
   worked. A clean result permits discussion of a next test, not release approval.

## Stop and recovery plan

If controls freeze, stop the test. Previously, card removal restored inputs and
the unresponsive power switch required a battery pull. If the switch cannot
shut down this ordinary-startup test, the previously used battery-removal method
can shut it down; remove the card before starting again. Do not perform another
update or repeatedly restart with the active candidate. Recovery for this exact
candidate has NOT been physically verified or guaranteed.

Return the card to the reader for preservation-only quarantine: verify the exact
candidate hash, rename `Z7APP.BIN` to `Z7APP.BATTERY-ONLY.disabled` only if that
destination is absent, verify all bytes/metadata, then safely eject. Keep all
other files disabled. This stops SD-module loading; it does not uninstall the
modified host or restore stock firmware. Same-version firmware rollback and
emergency recovery remain unverified and are not part of this proposal.

The full LCD release and the prior ownership-hardening build remain withdrawn.
No staging or camera test is authorized merely by preparing this assessment.
